"""Build a dfthcsos ANGLE_k family with the banked QROM on the new factorization.

Usage: python3 build_family.py <outdir> <J> <mode> [brot]
Writes angle_k_*.kmb + submission.npz and prints the static resource profile.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_DATA = _os.environ.get("EIGENOS_VQCC_DATA", "")
if not _DATA:
    raise SystemExit(
        "EIGENOS_VQCC_DATA is not set.\n"
        "Point it at the official competition data folder, e.g.\n"
        "  set EIGENOS_VQCC_DATA=C:\\path\\to\\google-verifiable-quantum-circuit-compilation\n"
        "It must contain verifiers/ and sample_submission/."
    )
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_DATA, "verifiers"))

from banked_lab import batch_deltas, build_qroam2, difference_tables  # noqa: E402
from dfthcsos.scoreinfra.reference import load_fixed_shifts  # noqa: E402

WORDS = os.path.join(_HERE, "femoco_public_words.npz")
BASE = os.path.join(_DATA, "sample_submission", "dfthcsos", "submission.npz")


def main() -> None:
    outdir = Path(sys.argv[1])
    J = int(sys.argv[2])
    mode = sys.argv[3]
    brot = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    outdir.mkdir(parents=True, exist_ok=True)

    data = np.load(WORDS)
    words = data["words"].astype(np.int64)
    base = np.load(BASE)
    fixed = load_fixed_shifts()

    deltas = batch_deltas(words, J)
    circuits = []
    for k, delta in enumerate(deltas):
        t0 = time.time()
        circuit, report = build_qroam2(delta, brot, mode=mode, return_report=True)
        path = outdir / f"angle_k_{k}.kmb"
        circuit.to_file(path, format="kmb")
        circuits.append(circuit)
        print(f"k={k} qubits={circuit.num_qubits} "
              f"toffoli_static={report['static_toffoli']} bank={report['bank_width']} "
              f"rank={report['gf2_rank']} ({time.time() - t0:.1f}s)", flush=True)

    np.savez(
        outdir / "submission.npz",
        U=base["U"].astype(np.float32),
        W=data["W"].astype(np.float64),
        H2_I=data["H2_I"].astype(np.float64),
        H1_I=np.asarray(fixed["H1_I"]),
        Hsym_lower=np.asarray(fixed["Hsym_lower"]),
        tree_edges=base["tree_edges"].astype(np.int64),
        angle_words=words.astype(np.int64),
    )

    # Analytical score model (no simulation): the verifier's cost model.
    from dfthcsos.verify import heuristic_costs
    heur = heuristic_costs(76, 65, 60, 30, brot)
    qa = max(c.num_qubits for c in circuits)
    sel = 12
    ang_persistent = J * brot
    ang_temp = qa - sel - ang_persistent
    persistent = heur["persistent_qubits"] + ang_persistent
    temporary = max(heur["temporary_qubits"], ang_temp)
    q_total = persistent + temporary
    static_total = sum(int(c.operation_statistics().num_toffoli_like) for c in circuits)
    print(json.dumps({
        "J": J, "mode": mode, "brot": brot, "K": len(circuits),
        "angles_qubits": qa, "angles_temp": ang_temp,
        "angles_persistent": ang_persistent,
        "static_toffoli_total": static_total,
        "static_toffoli_per_pass": static_total / 2,
        "heuristic_toffoli": heur["toffoli"], "heuristic_persistent": heur["persistent_qubits"],
        "heuristic_temporary": heur["temporary_qubits"],
        "persistent_qubits": persistent, "temporary_qubits": temporary,
        "Q_total": q_total,
        "T_total_estimate": static_total + heur["toffoli"],
        "angles_qubits_ok": qa <= 128,
    }, indent=2))


if __name__ == "__main__":
    main()
