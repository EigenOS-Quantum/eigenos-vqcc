#!/usr/bin/env python3
"""Write submission.zip and re-hash every member FROM THE EXTRACTED ARCHIVE.

A hash computed on the files in the download directory is not a fact about
the archive that will be uploaded.  This script packs the archive, extracts
it again into a temporary directory, and re-hashes every member from the
extracted copy.  The manifest it writes describes the bytes that will
actually be uploaded.

Usage:
    python3 package_submission.py /tmp/frontier submission.zip
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import zipfile

LAYOUT = [
    ("invsqrt.kmb", "invsqrt.kmb"),
    ("dqi.kmb", "dqi.kmb"),
    ("dfthcsos/submission.npz", "dfthcsos/submission.npz"),
]
LAYOUT += [("dfthcsos/angle_k_%d.kmb" % k, "dfthcsos/angle_k_%d.kmb" % k)
           for k in range(15)]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    src, out = sys.argv[1], sys.argv[2]

    for _, rel in LAYOUT:
        p = os.path.join(src, rel.replace("/", os.sep))
        if not os.path.exists(p):
            print("MISSING %s" % p)
            return 2

    if os.path.exists(out):
        os.remove(out)
    # A FIXED timestamp for every member, so the archive is byte-reproducible.
    # A zip stores each entry's mtime; without this, the same inputs produce a
    # different archive hash every time and the published hash is a lie.
    FIXED = (2026, 11, 2, 0, 0, 0)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for member, rel in LAYOUT:
            path = os.path.join(src, rel.replace("/", os.sep))
            info = zipfile.ZipInfo(member, date_time=FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            with open(path, "rb") as fh:
                z.writestr(info, fh.read(), compresslevel=9)

    stage = tempfile.mkdtemp(prefix="eigvqcc_pack_")
    try:
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
            if len(names) != len(LAYOUT):
                print("WRONG MEMBER COUNT %d" % len(names))
                return 1
            z.extractall(stage)
        members = []
        for member, rel in LAYOUT:
            p = os.path.join(stage, member.replace("/", os.sep))
            if not os.path.exists(p):
                print("MISSING IN ARCHIVE %s" % member)
                return 1
            members.append({"member": member, "sha256": sha256(p),
                            "bytes": os.path.getsize(p)})
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    manifest = {
        "archive_sha256": sha256(out),
        "archive_bytes": os.path.getsize(out),
        "members": members,
    }
    # Write to a NEW file name.  The repository ships receipts/submission-manifest.json
    # as a receipt of the submitted archive; overwriting it with a freshly generated
    # copy would destroy the record of what was actually submitted.
    manifest_path = os.path.join(os.path.dirname(os.path.abspath(out)),
                                 "submission-manifest.generated.json")
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print("manifest      %s" % manifest_path)

    print("members        %d" % len(members))
    print("archive bytes  %d" % manifest["archive_bytes"])
    print("archive sha256 %s" % manifest["archive_sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
