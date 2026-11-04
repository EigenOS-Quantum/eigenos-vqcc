# REPRODUCE

Everything below uses one public Kaggle dataset, one notebook cell, and no
credentials.

## The one-cell reproduction

The submitted `submission.zip` is 26,271,346 bytes with SHA-256
`a25c038c923ceca62ba373810715ed8b2d8796444e76143a2d959f168e3d886e`.

The authoritative value of the archive hash is the one printed by the
notebook and recorded in `receipts/submission-manifest.json`. Read it from
there; do not transcribe it from a document.

1. On Kaggle, open any notebook and **Add Input -> Datasets ->
   `manwithacat/vqcc-apache-public-circuits`**.
2. Open [`notebooks/generate-submission-v5.ipynb`](notebooks/generate-submission-v5.ipynb).
   It is one markdown cell and one code cell.
3. Paste the code cell into a Kaggle notebook (or open the file directly as a
   notebook and Run All).
4. Read the printed `archive sha256`. It must equal the value in
   `receipts/submission-manifest.json` under `archive_sha256`.
5. The cell writes `/kaggle/working/submission.zip` and
   `/kaggle/working/receipts/submission-manifest.json`. Both are downloadable
   from the notebook version's Output tab.

The cell takes about one to three minutes. The dqi circuit is 530 MB, so
packing the archive at compression level 9 is the slow step.

## Outside Kaggle

The same cell runs on any CPython 3.8+ with the dataset directory mounted
somewhere on disk. It reads two environment variables:

```bash
export VQCC_INPUT_ROOT=/path/to/the/parent/of/the/dataset
export VQCC_WORK_DIR=/path/to/a/writable/dir
python3 notebooks/generate-submission-v5.ipynb
```

`VQCC_INPUT_ROOT` is the directory **containing** the dataset, not the dataset
itself. The cell searches, in order:

- `$VQCC_INPUT_ROOT/datasets/manwithacat/vqcc-apache-public-circuits`
- `$VQCC_INPUT_ROOT/manwithacat/vqcc-apache-public-circuits`
- `$VQCC_INPUT_ROOT/vqcc-apache-public-circuits`
- then a recursive sweep for `circuits/invsqrt/53000387a86b.kmb`

A root is accepted only if it contains both `circuits/` and `factorizations/`.

## What the cell guarantees

- **Fails closed.** Every one of the 18 members is pinned by SHA-256. A
  missing file, an unpinned member or a hash mismatch raises `SystemExit`
  before anything is packaged, and the archive is not written.
- **Re-verifies inside the archive.** After packing, the cell extracts the
  archive to a temporary directory and re-hashes all 18 members from the
  extracted bytes. A member that does not match its pin inside the packed
  archive raises.
- **Is byte-reproducible.** Fixed member order, fixed timestamps
  (2026-11-04 00:00:00), fixed compression level. On the same zlib build the
  archive is byte-identical. On a different zlib build the *container* bytes
  can differ while the 18 members remain byte-identical, which is why the
  members - not the container - are the gate.

## Verifying the three tasks yourself

The cell has a `RUN_OFFICIAL_VERIFIERS` switch, off by default, because the
competition's verifiers are large and the `dfthcsos` verifier needs the
competition data attached as notebook input. Turn it on only if you have
attached the competition data, and expect the `invsqrt` verifier to run for
one to two hours over 3,133,452 values.

The receipts we obtained are in [`receipts/`](receipts/), and they are the
authority for the numbers in the README.

## Licence

The circuits are other participants' Apache-2.0 work, credited in
[NOTICE.md](NOTICE.md). This repository is Apache-2.0. See [LICENSE](LICENSE).
