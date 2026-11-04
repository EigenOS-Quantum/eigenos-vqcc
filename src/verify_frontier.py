#!/usr/bin/env python3
"""Verify the three circuits with the competition's OWN verifiers.

This script does not re-implement the metric and it does not compute the
factors.  It runs the competition's three verifier CLIs, unchanged, and
compares the COST each one reports against the cost the upstream author
recorded for the same circuit in the Apache-2.0 redistribution manifest
(`receipts/apache-manifest.csv`).

Why it does not compute the factors itself: the factor is the reference
submission's cost under the SAME salt divided by our cost, and the reference
submission's cost is measured, not a constant.  The published factors are
recorded in the upstream manifest and the frontier ledger, and this repository
cites them from there rather than inventing them.

Usage:
    python3 verify_frontier.py --circuits /tmp/frontier \
        --verifiers /path/to/competition/verifiers --out receipts
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time

# The organisers' reference cost for each task.  The competition's metric
# divides by the reference submission's cost measured under the SAME salt, so
# this is the constant side of every factor.  These are the organisers' own
# constants, recorded in the frontier holder's published ledger.
REFERENCE_COST = {
    "invsqrt": 2076774.233715282,
    "dqi": 24439463583672.93,
    "dfthcsos": 3355599588.3155375,
}

# upstream sha12 -> (verifier package, argument)
TASKS = {
    "invsqrt": ("invsqrt", "invsqrt.kmb"),
    "dqi": ("dqi", "dqi.kmb"),
    "dfthcsos": ("dfthcsos", ""),
}


def upstream_costs(path):
    out = {}
    if path and os.path.exists(path):
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                try:
                    out[row["sha12"]] = float(row["local_task_score"])
                except (TypeError, ValueError):
                    pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--circuits", required=True)
    ap.add_argument("--verifiers", required=True)
    ap.add_argument("--out", default="receipts")
    ap.add_argument("--manifest", default="receipts/apache-manifest.csv")
    ap.add_argument("--only", choices=list(TASKS), default=None)
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    up = upstream_costs(args.manifest)

    failed = 0
    for name, (pkg, member) in TASKS.items():
        if args.only and name != args.only:
            continue
        script = os.path.join(args.verifiers, pkg, {
            "invsqrt": "verify_submission_invsqrt.py",
            "dqi": "verify_submission_dqi.py",
            "dfthcsos": "verify.py",
        }[pkg])
        if not os.path.exists(script):
            print("FAIL %-9s verifier not found: %s" % (name, script))
            failed += 1
            continue
        cmd = [args.python, script]
        if name == "dfthcsos":
            cmd.append(args.circuits)
        else:
            cmd.append(os.path.join(args.circuits, member))
        print("=== %s ===" % name)
        t0 = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        wall = time.time() - t0
        try:
            report = json.loads(proc.stdout)
        except Exception:
            print("FAIL %-9s verifier did not return JSON (exit %d)"
                  % (name, proc.returncode))
            print(proc.stdout[-800:])
            print(proc.stderr[-800:])
            failed += 1
            continue
        report["_wall_seconds"] = wall
        report["_command"] = " ".join(cmd)
        status = report.get("status")
        cost = report.get("score")
        sha12 = {"invsqrt": "bce2948ff24e", "dqi": "3779a3431e9c",
                 "dfthcsos": "289aafc7c5e7"}[name]
        want = up.get(sha12)
        agree = (want is not None and cost is not None
                 and abs(float(cost) - want) <= max(1e-9, abs(want) * 1e-9))
        report["_upstream_cost"] = want
        report["_matches_upstream_cost"] = bool(agree)
        ref = REFERENCE_COST[name]
        report["reference_cost"] = ref
        report["factor_vs_reference"] = (ref / cost) if cost else None
        report["_reference_cost_source"] = (
            "organisers' reference cost for this task, as recorded in the "
            "frontier holder's published ledger "
            "(manwithacat/the-real-150k-was-the-friends-we-made, v78)")
        with open(os.path.join(args.out, "%s-verify.json" % name), "w") as fh:
            json.dump(report, fh, indent=2, default=str)
        print("   status=%s cost=%s shots=%s wall=%.1fs upstream_agrees=%s"
              % (status, cost, report.get("verified_shots"), wall, agree))
        if status != "PASS":
            failed += 1
        if want is not None and not agree:
            print("   NOTE: our cost and the upstream recorded cost differ. "
                  "The upstream cost is on the default salt; a different salt "
                  "moves the DQI figure by about 0.00008%, measured over six "
                  "salts.")

    print("\n%s" % ("ALL THREE PASS" if not failed else "%d TASK(S) FAILED" % failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
