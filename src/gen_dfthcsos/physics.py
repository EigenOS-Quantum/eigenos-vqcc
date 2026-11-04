"""Evaluate DF-THC physics for a (words, W, H2_I, tree_edges) combination.

Caches the FCIDUMP reference integrals locally so iterations are fast.
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
sys.path.insert(0, os.path.join(_DATA, "verifiers"))

from dfthcsos.scoreinfra.dfthc_math import (  # noqa: E402
    evaluate_dfthc_angle_words,
    symmetric_from_lower,
)
from dfthcsos.scoreinfra.reference import (  # noqa: E402
    UPPER_ENERGY,
    check_fcidump,
    load_fixed_shifts,
    load_reference,
)

CACHE = Path(_HERE) / "ref_cache.npz"


def get_ref() -> dict:
    if CACHE.is_file():
        with np.load(CACHE, allow_pickle=False) as d:
            return {k: np.array(d[k]) for k in d.files}
    t0 = time.time()
    ref = load_reference(check_fcidump())
    print(f"loaded FCIDUMP in {time.time() - t0:.1f}s", flush=True)
    np.savez(CACHE, oei=ref["oei"], tei=ref["tei"], ecore=ref["ecore"],
             electrons=ref["electrons"], orbitals=ref["orbitals"])
    return ref


def shifts() -> tuple[np.ndarray, float]:
    fixed = load_fixed_shifts()
    S = symmetric_from_lower(fixed["Hsym_lower"], 76)
    beta_1 = float(fixed["H1_I"]) - 0.5 * float(np.trace(S))
    return S, beta_1


def native_inputs(w_lower, H2_I, S_lower):
    """Mirror of dfthcsos.verify.native_inputs (the verifier's exact convention)."""
    w = np.asarray(w_lower, dtype=np.float64)
    W = np.asarray(H2_I, dtype=np.float64) - np.sum(w, axis=1)
    S = symmetric_from_lower(S_lower, 76)
    beta_1 = float(fixed["H1_I"]) - 0.5 * float(np.trace(S))
    return w, W, S, beta_1


fixed = load_fixed_shifts()


def evaluate(words, w, W, tree_edges, brot=10, ref=None):
    """`w` is lowercase w (R,B,C); `W` here is H2_I (R,C) as stored in the npz."""
    ref = ref or get_ref()
    w_l, W_u, S, beta_1 = native_inputs(w, W, fixed["Hsym_lower"])
    return evaluate_dfthc_angle_words(
        words, w_l, W_u, S, beta_1, ref, brot=brot,
        tree_edges=tree_edges, energy_upper=UPPER_ENERGY,
    )


if __name__ == "__main__":
    ref = get_ref()
    base = np.load(os.path.join(_DATA, "sample_submission", "dfthcsos", "submission.npz"))
    tree = base["tree_edges"]

    print("\n=== A. BASELINE words + BASELINE W/H2_I + baseline tree (brot=12) ===")
    m = evaluate(base["angle_words"], base["W"], base["H2_I"], tree, brot=12, ref=ref)
    print(json.dumps({k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                      for k, v in m.items()}, indent=2))
    print("expected baseline: lambda_eff 49.30137")

    print("\n=== B. NEW words + NEW W/H2_I + baseline tree (brot=10) ===")
    d = np.load(os.path.join(_HERE, "femoco_public_words.npz"))
    m2 = evaluate(d["words"].astype(np.int64), d["W"], d["H2_I"], tree, brot=10, ref=ref)
    print(json.dumps({k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                      for k, v in m2.items()}, indent=2))
    print("expected leader: lambda_eff 47.5585")
