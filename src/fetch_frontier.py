#!/usr/bin/env python3
"""Fetch the three Apache-2.0 frontier circuits and check every SHA-256.

The circuits come from the public Kaggle dataset
    manwithacat/vqcc-apache-public-circuits
via the unauthenticated dataset API.  Every file is checked against the
expected SHA-256 before it is accepted.  A file whose hash does not match is
deleted, not repaired.

Two ways to get the bytes:

  1. A LOCAL COPY of the dataset.  On Kaggle the dataset is already mounted,
     so nothing is downloaded at all.  Point at it with --dataset-root, or let
     the script find it under /kaggle/input or ./input.
  2. THE NETWORK.  The DQI circuit is 580 MB and the transfer is regularly cut
     short, so the download is RESUMABLE: it asks for the byte range it is
     missing and keeps going until the file is whole.  A short file is never
     accepted, only a file whose hash matches.

Usage:
    python3 fetch_frontier.py --out /tmp/frontier
    python3 fetch_frontier.py --out /tmp/frontier --dataset-root /kaggle/input/datasets/manwithacat/vqcc-apache-public-circuits
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DATASET = "manwithacat/vqcc-apache-public-circuits"
BASE = "https://www.kaggle.com/api/v1/datasets/download/" + DATASET

# member path inside submission.zip  ->  path inside the upstream dataset
LAYOUT = [
    ("invsqrt.kmb", "circuits/invsqrt/bce2948ff24e.kmb"),
    ("dqi.kmb", "circuits/dqi/3779a3431e9c.kmb"),
    ("dfthcsos/submission.npz", "circuits/chemistry/289aafc7c5e7/submission.npz"),
]
LAYOUT += [("dfthcsos/angle_k_%d.kmb" % k,
            "circuits/chemistry/289aafc7c5e7/angle_k_%d.kmb" % k) for k in range(15)]

# sha256 of EVERY member, as verified by the official verifier on the bytes
# extracted back out of the packed archive.  All 18 are pinned.  A member with
# no entry here is a FAILURE, not a pass.
EXPECTED = {
    "invsqrt.kmb":                  
        "bce2948ff24e20fe59666d131f7fc4316a905103937272c52fdd39d494b6fe47",
    "dqi.kmb":                      
        "3779a3431e9cb072bad980919236bd961ad3bcbd162d1757d51379316a103a2d",
    "dfthcsos/submission.npz":      
        "64e7299eebd95fc37eb36de108e48cde33aaf6cdd17fa36e276e75f7d9af589c",
    "dfthcsos/angle_k_0.kmb":       
        "8b698f14b339bd282e0332a1f105b41d60bfa5218d107c775db2532fbd88f774",
    "dfthcsos/angle_k_1.kmb":       
        "0d16c5108e48e40931d87f1e3ee12d4486e932b341989ce909a47b032e5a7745",
    "dfthcsos/angle_k_10.kmb":      
        "e2668bf5666ca1e49541bef7a255b2100a8a513188fadef3a8dd4e892cfe2094",
    "dfthcsos/angle_k_11.kmb":      
        "5f69f385cb2040e7124e11e1cedb7cea0e0ffa6ad13abe81b2a337744cb9c2ac",
    "dfthcsos/angle_k_12.kmb":      
        "f86995a0ea1990a11a43f1812f47e00a77658f71cc544d44bd5003e616111272",
    "dfthcsos/angle_k_13.kmb":      
        "4390c8114e191b0c74ccd8b6302e5e0ded4e8cb412a3f146eea9887551658876",
    "dfthcsos/angle_k_14.kmb":      
        "9e596deb120f20d1c92c350456ce9847314ba943a4d196e7942bac518a229f6c",
    "dfthcsos/angle_k_2.kmb":       
        "b7b73491d3aeb59c70d023704df9f2ad69eb96c9d1f9e9920d33d60bd7852d11",
    "dfthcsos/angle_k_3.kmb":       
        "c2437ad406d3772e961e7229580fba7b68c036b97ce36b4067c865e3af729f00",
    "dfthcsos/angle_k_4.kmb":       
        "0df35ae1cb26d3bc09f022b2a397a8b07e5c322283d2c8cf0a53a4bb11b9dd47",
    "dfthcsos/angle_k_5.kmb":       
        "a9a649997bf0696a659c8cbf9e778f92bee2816b6212febc898ed51450ae42c3",
    "dfthcsos/angle_k_6.kmb":       
        "715673382c491b796865dbba235687eafebd16c745872d20f7ae1808f88a62ae",
    "dfthcsos/angle_k_7.kmb":       
        "31e004f932d42750e1dda98abdf3e0097941cb1b1bbd353ed692e52098119cfb",
    "dfthcsos/angle_k_8.kmb":       
        "046ac97b8c6ac9e1895a1da5dc89ea5df55bf487b1822d2ba11697c948145ff9",
    "dfthcsos/angle_k_9.kmb":       
        "10c37a55ab902357cf60c5cf529de0eec9e9497a03f0b2ad7a9888d26d9c1e63",
}

CANDIDATE_ROOTS = [
    "/kaggle/input/datasets/" + DATASET,
    "/kaggle/input/" + DATASET,
    "input/" + DATASET,
    "input",
    DATASET,
]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_local_root(explicit):
    if explicit:
        return explicit if os.path.isdir(explicit) else None
    for cand in CANDIDATE_ROOTS:
        if os.path.isdir(cand):
            return cand
    return None


def copy_local(root, remote, dest):
    src = os.path.join(root, remote.replace("/", os.sep))
    if not os.path.exists(src):
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(src, dest)
    return True


def download_with_curl(remote, dest):
    """Download with curl, resuming if the transfer is cut short.

    The Kaggle endpoint regularly closes a 580 MB transfer early.  curl's
    --retry/--retry-all-errors with -C - puts the transfer back together
    without any special handling here.  Returns False if curl is not
    available.
    """
    curl = shutil.which("curl") or shutil.which("curl.exe")
    if not curl:
        return False
    url = BASE + "/" + urllib.parse.quote(remote, safe="")
    cmd = [curl, "-sL", "--retry", "12", "--retry-all-errors", "--retry-delay", "2",
           "-C", "-", "-m", "3600", "-o", dest, url]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 and proc.stderr:
        print("   curl: %s" % proc.stderr.strip()[:200])
    return True


def download_resumable(remote, dest, attempts=20):
    """Pure-python fallback download, resuming if the transfer is cut short.

    With a sized read, urllib does NOT raise on a short body - it just
    returns fewer bytes and then stops - so a naive download silently
    produces a truncated file.  We therefore compare what we wrote against
    Content-Length and keep asking for the missing range until the file is
    whole.  The caller still checks the SHA-256, so a short or corrupt file
    can never be accepted.
    """
    url = BASE + "/" + urllib.parse.quote(remote, safe="")
    last = None
    for attempt in range(attempts):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        headers = {"User-Agent": "eigenos-vqcc/1.0"}
        if have:
            headers["Range"] = "bytes=%d-" % have
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                code = getattr(resp, "status", 200)
                length = resp.headers.get("Content-Length")
                total = int(length) if length and length.isdigit() else None
                if code == 206:
                    mode = "ab"
                else:
                    if have:
                        print("   server ignored the range request, restarting")
                    have = 0
                    mode = "wb"
                wrote = 0
                with open(dest, mode) as fh:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        fh.write(chunk)
                        wrote += len(chunk)
                got = have + wrote
                if total is not None and got < total:
                    print("   transfer cut short at %d of %d bytes, resuming (attempt %d/%d)"
                          % (got, total, attempt + 1, attempts))
                    continue
                return
        except http.client.IncompleteRead as exc:
            last = exc
            # exc.partial is the WHOLE body read so far, not a remainder.
            if exc.partial:
                with open(dest, "wb") as fh:
                    fh.write(exc.partial)
            print("   transfer cut short at %d bytes, resuming (attempt %d/%d)"
                  % (len(exc.partial or b""), attempt + 1, attempts))
            continue
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            last = exc
            print("   retry %d/%d for %s (%s)" % (attempt + 1, attempts, remote, exc))
            time.sleep(2 + attempt)
    raise SystemExit("download failed: %s (%s)" % (remote, last))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset-root", default=None,
                    help="a local copy of the dataset; nothing is downloaded if given")
    ap.add_argument("--manifest", default=None,
                    help="upstream manifest.csv; used to print the upstream attribution")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    root = find_local_root(args.dataset_root)
    print("source: %s" % (root if root else "network"))

    ok = bad = 0
    for member, remote in LAYOUT:
        dest = os.path.join(args.out, member.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if root:
            if not copy_local(root, remote, dest):
                print("FAIL %-32s not in the local dataset: %s" % (member, remote))
                bad += 1
                continue
        else:
            if not download_with_curl(remote, dest):
                download_resumable(remote, dest)
        got = sha256(dest)
        want = EXPECTED.get(member)
        if want is None:
            # Fail closed. A member with no pinned hash is not "fine", it is
            # UNVERIFIED, and an unverified member must never reach the archive.
            os.remove(dest)
            print("FAIL %-32s no expected SHA-256 is pinned for this member" % member)
            bad += 1
            continue
        if got != want:
            os.remove(dest)
            print("FAIL %-32s hash %s != expected %s" % (member, got, want))
            bad += 1
            continue
        print("OK   %-32s %s  %d bytes" % (member, got, os.path.getsize(dest)))
        ok += 1

    if args.manifest and os.path.exists(args.manifest):
        with open(args.manifest, newline="") as fh:
            upstream = {row["sha12"]: row for row in csv.DictReader(fh)}
        for sha12 in ("bce2948ff24e", "3779a3431e9c", "289aafc7c5e7"):
            row = upstream.get(sha12)
            if row:
                print("upstream %s  author=%-28s licence=%s  %s" %
                      (sha12, row.get("author", "?"), row.get("licence", "?"),
                       row.get("source_notebook_url", "")))

    print("\n%d of %d files OK, %d bad" % (ok, len(LAYOUT), bad))
    if bad:
        return 1
    with open(os.path.join(args.out, "fetch-manifest.json"), "w") as fh:
        json.dump({m: sha256(os.path.join(args.out, m.replace("/", os.sep)))
                   for m, _ in LAYOUT}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
