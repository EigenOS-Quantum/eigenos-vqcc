"""Compact difference banks for an exact, arbitrary-target ANGLES XOR oracle.

SPDX-License-Identifier: Apache-2.0

Banked QROM construction adapted from Kozykorpesh / Sumit Chongder:
https://www.kaggle.com/code/kozykappa/quantum-ai-compact-arithmetic-banked-qrom?scriptVersionId=361433617
https://www.kaggle.com/code/sumitchongder/notebook2f196e646b?scriptVersionId=361357149
Read through Kirill Tym's public quantum-circuits-qrom-tower42 v10 source.

Our change: allocate only nonzero difference columns. Optionally conjugate the
target by a reversible CNOT change of basis, reducing the difference bank to
its GF(2) column rank. The same change is applied to BOTH lookup tables. Thus
the input target can be arbitrary: T^-1(T z XOR T f(a)) = z XOR f(a).
No coefficient, angle word, address, or measurement branch is approximated.

Numeric/profile operations work without kickmix. Circuit building/testing
requires the competition's Linux kickmix package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import ceil
from pathlib import Path

import numpy as np


def batch_deltas(words, J=5):
    words = np.asarray(words, dtype=np.int64)
    nv, na = words.shape
    padded = np.zeros((nv, ceil(na / J) * J), dtype=np.int64)
    padded[:, :na] = words
    batches = padded.reshape(nv, -1, J).transpose(1, 0, 2)
    result = batches.copy()
    result[1:] ^= batches[:-1]
    return result


def pack(row, brot):
    return sum(int(value) << (j * brot) for j, value in enumerate(row))


def _change_basis(values, operations):
    result = list(values)
    for source, target in operations:
        result = [value ^ (((value >> source) & 1) << target)
                  for value in result]
    return result


def difference_tables(delta, brot=10, mode="zero"):
    """Return packed d0, compact dd, and exact reversible output transforms."""
    if mode not in {"baseline", "zero", "linear"}:
        raise ValueError("mode must be baseline, zero, or linear")
    delta = np.asarray(delta, dtype=np.int64)
    if delta.ndim != 2 or len(delta) < 4:
        raise ValueError("expected at least four address rows")
    if np.any(delta < 0) or np.any(delta >= (1 << brot)):
        raise ValueError("angle word out of range")
    A, J = delta.shape
    width = J * brot
    d0 = [pack(row, brot) for row in delta[::2]]
    d1 = [pack(delta[2 * h + 1], brot) if 2 * h + 1 < A else value
          for h, value in enumerate(d0)]
    dd = [a ^ b for a, b in zip(d0, d1)]
    paired = delta[::2].copy()
    paired[:len(delta[1::2])] ^= delta[1::2]
    if A & 1:
        paired[-1] = 0
    bit_columns = ((paired[:, :, None] >> np.arange(brot)) & 1).reshape(H := len(d0), width).T
    packed_columns = np.packbits(bit_columns.astype(np.uint8), axis=1, bitorder="little")
    columns = [int.from_bytes(column.tobytes(), "little") for column in packed_columns]
    active = [bit for bit, column in enumerate(columns) if column]
    unique = len(set(columns) - {0})
    basis = {}
    operations = []
    reduced = columns.copy()
    for bit, original in enumerate(columns):
        column = original
        relation = 0
        while column:
            pivot = column.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (column, relation ^ (1 << bit))
                break
            value, combination = basis[pivot]
            column ^= value
            relation ^= combination
        if not column:
            # Independent coordinates retain their original values. A dependent
            # coordinate is zeroed by XORing only independent coordinates into it.
            # In particular, identical columns need just one CNOT each way.
            operations.extend((source, bit) for source in range(width)
                              if (relation >> source) & 1)
            reduced[bit] = 0
    rank = len(basis)
    if mode == "linear":
        d0 = _change_basis(d0, operations)
        transformed_dd = _change_basis(dd, operations)
        active = [bit for bit, column in enumerate(reduced) if column]
    else:
        transformed_dd = dd
        operations = []
        if mode == "baseline":
            active = list(range(width))
    compact = [sum(((value >> bit) & 1) << target
                   for target, bit in enumerate(active))
               for value in transformed_dd]
    # A complete integer certificate of the table identity for every legal a.
    reconstructed = [sum(((value >> target) & 1) << bit
                         for target, bit in enumerate(active)) for value in compact]
    restored = _change_basis(
        [d0[a // 2] ^ (reconstructed[a // 2] if a & 1 else 0)
         for a in range(A)], reversed(operations))
    assert restored == [pack(row, brot) for row in delta]
    return d0, compact, active, operations, {
        "rows": A, "width": width, "active_columns": sum(bool(c) for c in columns),
        "unique_nonzero_columns": unique, "gf2_rank": rank,
        "bank_width": len(active), "basis_cnot_count": 2 * len(operations),
        "integer_table_certificate": "PASS", "mode": mode,
    }


def build_qroam2(delta, brot=10, *, mode="zero", return_report=False):
    """Exact banked XOR oracle; same public register contract as upstream."""
    import kickmix as km
    delta = np.asarray(delta, dtype=np.int64)
    A, J = delta.shape
    nbits = (A - 1).bit_length()
    H = (A + 1) // 2
    hbits = nbits - 1
    W = J * brot
    d0, dd, active, transforms, report = difference_tables(delta, brot, mode)
    b = km.CircuitBuilder()
    sel = b.create_quantum_register(nbits, "selection")
    words = [b.create_quantum_register(brot, f"word_{j}") for j in range(J)]
    tgt = [q for word in words for q in word]
    for source, target in transforms:
        b.cx(tgt[source], tgt[target])
    B = b.alloc_qubits(len(active))
    hreg = sel[1:nbits]
    anc = b.alloc_qubits(hbits - 1)
    hb = [hreg[i] for i in reversed(range(hbits))]

    def load(h, control):
        targets = [tgt[j] for j in range(W) if (d0[h] >> j) & 1]
        targets += [B[j] for j in range(len(active)) if (dd[h] >> j) & 1]
        if targets:
            b.cx(control, km.array(targets))

    def node(control, level, lo, hi):
        if lo >= H:
            return
        if hi - lo == 1 or (hi <= H and len(set(d0[lo:hi])) == 1
                            and len(set(dd[lo:hi])) == 1):
            load(lo, control)
            return
        mid = (lo + hi) // 2
        if H <= mid:
            node(control, level + 1, lo, mid)
            return
        bit, temporary = hb[level], anc[level - 1]
        b.x(bit)
        b.init_and(control, bit, temporary)
        b.x(bit)
        node(temporary, level + 1, lo, mid)
        b.cx(control, temporary)
        node(temporary, level + 1, mid, hi)
        b.del_and(control, bit, temporary)

    half = 1 << (hbits - 1)
    b.x(hb[0])
    node(hb[0], 1, 0, half)
    b.x(hb[0])
    node(hb[0], 1, half, 2 * half)
    b.free(anc)
    for bank_bit, target in enumerate(active):
        b.ccx(sel[0], B[bank_bit], tgt[target])
    if active:
        table = dd + [0] * ((1 << hbits) - H)
        b.del_lookup(table=table, address=hreg, target=B)
    b.free(B)
    for source, target in reversed(transforms):
        b.cx(tgt[source], tgt[target])
    circuit = b.finish_circuit()
    report.update(num_qubits=circuit.num_qubits,
                  static_toffoli=int(circuit.operation_statistics().num_toffoli_like))
    return (circuit, report) if return_report else circuit


def profile(words, brot=10, Js=(4, 5, 6, 7)):
    return {str(J): [difference_tables(delta, brot, "linear")[-1]
                    for delta in batch_deltas(words, J)] for J in Js}


def test_random_targets(circuits, deltas, *, brot=10, repeats=8, seed=20261023):
    """Every legal address, random dirty targets, HMR phase and scratch checks.

    This is simulation evidence; the exhaustive integer identity is separately
    certified above. This test is not a proof over all measurement branches.
    The full official verifier remains the acceptance check for the family.
    """
    import kickmix as km
    from dfthcsos.scoreinfra.circuits import register_layout, _check_state
    rng = np.random.default_rng(seed)
    layout = register_layout(circuits)
    A = len(deltas[0])
    addresses = np.tile(np.arange(A, dtype=np.int64), repeats)
    address_bits = ((addresses[None, :] >> np.arange(len(layout.selection))[:, None]) & 1).astype(bool)
    sim = km.Simulator(batch_size=len(addresses), debug_print=False,
                       seed=seed, counting_operations=True)
    sim.use_same_registers_as(circuits[0])
    place_values = np.int64(1) << np.arange(brot)
    toffolis = []
    for k, (circuit, delta) in enumerate(zip(circuits, deltas)):
        sim.clear_for_shot()
        sim.write_across_shots(layout.selection, address_bits)
        dirty = rng.integers(0, 1 << brot, size=(len(addresses), len(layout.words)), dtype=np.int64)
        for j, word in enumerate(layout.words):
            sim.write_across_shots(word, ((dirty[:, j][None, :] >> np.arange(brot)[:, None]) & 1).astype(bool))
        before = sim.operation_statistics().num_toffoli_like
        sim.do(circuit)
        _check_state(sim, circuit, layout, address_bits, f"random-target ANGLE_{k}")
        result = np.stack([place_values @ sim.read_across_shots(word).astype(np.int64)
                           for word in layout.words], axis=1)
        assert np.array_equal(result, dirty ^ delta[addresses]), f"ANGLE_{k} wrong XOR"
        toffolis.append((sim.operation_statistics().num_toffoli_like - before) / len(addresses))
    return {"status": "PASS", "addresses": A, "repeats": repeats,
            "shots_per_circuit": len(addresses), "num_circuits": len(circuits),
            "random_target_xor": "PASS", "unchanged_selection": "PASS",
            "clean_workspace": "PASS", "zero_observed_phase_errors": True,
            "toffoli_per_circuit": toffolis, "toffoli_per_pass": sum(toffolis),
            "full_official_verification": "PENDING", "seed": seed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("words", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("baseline", "zero", "linear"), default="zero")
    parser.add_argument("--J", type=int, default=5)
    parser.add_argument("--brot", type=int, default=10)
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--repeats", type=int, default=8)
    args = parser.parse_args()
    words = np.loadtxt(args.words, delimiter=",", dtype=np.int64)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"source_csv": str(args.words), "source_csv_sha256": hashlib.sha256(args.words.read_bytes()).hexdigest(),
              "shape": list(words.shape), "brot": args.brot, "J": args.J, "mode": args.mode,
              "profiles": profile(words, args.brot)}
    if not args.profile_only:
        deltas = batch_deltas(words, args.J)
        circuits, resources = [], []
        for k, delta in enumerate(deltas):
            circuit, resource = build_qroam2(delta, args.brot, mode=args.mode, return_report=True)
            if circuit.num_qubits > 128:
                raise ValueError(f"ANGLE_{k} exceeds the 128-qubit cap")
            path = args.output / f"angle_k_{k}.kmb"
            circuit.to_file(path, format="kmb")
            resource.update(k=k, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
            circuits.append(circuit)
            resources.append(resource)
            print(json.dumps(resource), flush=True)
        report["circuits"] = resources
        report["random_target_test"] = test_random_targets(circuits, deltas, brot=args.brot, repeats=args.repeats)
        toffoli = 8794 + 2 * report["random_target_test"]["toffoli_per_pass"]
        report["estimate_using_unchanged_c5_coefficients"] = {
            "full_system_qubits": 631 + args.J * args.brot,
            "full_system_toffoli": toffoli, "lambda_eff": 47.558542335159316,
            "estimated_cost": (631 + args.J * args.brot) * toffoli * 47.558542335159316,
            "label": "RESOURCE ESTIMATE; full official verifier pending"}
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps({key: value for key, value in report.items() if key != "profiles" and key != "circuits"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
