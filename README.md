# EigenOS Quantum Suite - Google VQCC submission code

This repository is the software behind our entry to the Kaggle competition
**Google Quantum AI - Verifiable Quantum Circuit Compilation**
(`google-verifiable-quantum-circuit-compilation`, competition id 161954).

It exists because a prize winner is bound to deliver the software. Rule
B(7)(a)(i): *"As a condition to being awarded a Prize, a Prize winner must
fulfill the following obligations: i. Deliver to the Competition Sponsor the
final model's software code as used to generate the winning Submission and
associated documentation."* Rule B(5)(c) is a Winner's Licence term, not an
entry requirement: the sponsor *"may be required"* to ask how the submission
was generated, and that description *"should also include a link to a code
repository with complete and detailed instructions so that the results obtained
can be reproduced."*

**Read [NOTICE.md](NOTICE.md) and [NOTICE-v7.md](NOTICE-v7.md) before anything
else.** The circuits in the current submission are other competitors' Apache-2.0
public work. They are credited by name, by URL and by licence, as Apache-2.0
requires. We did not write them and we do not claim that we did.

## The archive

One archive, `submission.zip`: **26,174,071 bytes**, SHA-256
`1d36f774d4eb7c2ce55b94c98f36dac87ab0f0fefda33312bb4ef869cc37ea22`, 18 members.
Every member is pinned by SHA-256 in
[`receipts/v7-submission-manifest.json`](receipts/v7-submission-manifest.json).

This is the **v7** rebuild, built 5 November 2026. Its **local** geometric mean
is **24.653969** (headline **24.65397**). That is a local measurement and we
publish it as such. The authoritative number is always the one on the
competition's own leaderboard, not this page.

**Measured public leaderboard score of the preceding (v5) submission:
24.55683** (team *Nicks Seringian*, `nicks037`, 4 November 2026) - the
organisers' own number, read from the competition leaderboard. The v5 archive
had SHA-256 `a25c038c923ceca62ba373810715ed8b2d8796444e76143a2d959f168e3d886e`.
The v6 archive was built but **not** uploaded.

| benchmark | competition name | circuit | author | local official-verifier cost | factor vs reference |
|---|---|---|---|---:|---:|
| `invsqrt.kmb` | **fusion** | `af4698478fba` | Agniv Banerjee | 97921.57954257724 | **21.2085451x** |
| `dqi.kmb` | **combinatorial optimization** | `993c70386a3d` | yoyobar | 375373377713.4055 | **65.1071064x** |
| `dfthcsos/angle_k_0..14.kmb` + `dfthcsos/submission.npz` | **chemistry** | `a344f422f2e0` loaders + `b93b4db795e7` npz | see [NOTICE-v7.md](NOTICE-v7.md) | 309206676.09009403 | **10.8522873x** |

Local geometric mean of the three ratios: **24.653969**.

The organisers measure the reference cost with a per-split secret salt, so the
last digits of a published score can differ from a local run.

The chemistry family is the competition's own `dfthcsos` verifier reporting
**PASS** on exactly these bytes (`score` 309,206,676.09009403, 15,347 Toffolis,
427 qubits, 78,080 verified shots, `lambda_eff` 47.18429756505502). The dqi
circuit is the same verifier reporting **PASS** (102,400 shots, 891 qubits,
0 value errors, 0 phase errors). The fusion circuit's official-verifier report
is recorded in [`receipts/v7-invsqrt-verify.json`](receipts/v7-invsqrt-verify.json);
the receipts are in [`receipts/`](receipts/).

### A measured comparison we did not expect

Pairing the same fifteen chemistry loaders with a different published
factorization changes the score. We ran both through the official verifier:

| chemistry npz | score | verdict |
|---|---:|---|
| `b93b4db795e7` (shipped) | **309,206,676.09009403** | better |
| `0ed964465654` | 309,746,758.2195386 | worse by 540,082 |

We ship the better pairing. Both are published, Apache-2.0 ledger files; see
[NOTICE-v7.md](NOTICE-v7.md) for the full provenance of the mixed assembly.

### Honest statement about standing

The circuits above were the best published for their task at the time the
ledger snapshot was taken. **That frontier moves every day** - it moved twice on
4 November alone, and each move made earlier versions of this README false. We
therefore make **no claim that these circuits remain the best in the field**,
and none that nothing published beats them. What we claim is only what is
measured: the archive above is byte-reproducible from a public notebook, and
the three factors in the table are the competition's own verifier output on
those bytes.

Public leaderboard snapshot, read 5 November 2026 00:58 UTC, **2,311 teams**:
**leader 28.83206** (team *James & Geremie & Tony*), **us 24.55683 at rank 460**.
The v7 score of 24.653969 would place us at roughly **rank 196** on that same
snapshot, inside the bronze band. Both are dated snapshots of a moving
leaderboard, not standing claims - the live board is the only authority on rank,
and these lines will go stale. The snapshot we used is in
[`receipts/v7-board-snapshot.json`](receipts/v7-board-snapshot.json).

## The public generator notebook

The archive is generated by a single Kaggle notebook that is **public**:

**<https://www.kaggle.com/code/nicks037/submission-zip>**

That notebook is one code cell. It takes the 18 members from the public
dataset (`manwithacat/vqcc-apache-public-circuits`) - copying them out of
`/kaggle/input` when that dataset is attached, and downloading the same
files from the public Kaggle dataset API when it is not - re-hashes every
one of them, **fails closed** on a missing file, an unpinned member or a hash
mismatch, and writes a fixed-timestamp archive whose SHA-256 is the one
printed above.

**State of that notebook as of 5 November 2026: version 3, carrying the older
v4 cell, no saved outputs, and `dataSources: []`.** Run as it stands it
rebuilds a different, older archive. The v7 cell is
[`notebooks/generate-submission-v7.ipynb`](notebooks/generate-submission-v7.ipynb)
in this repository; publishing it as a new version of the Kaggle notebook and
saving its outputs is what makes the archive reproducible from a public
notebook, which the Milestone and Longest Leader prizes require.

The same cell is also in this repository as
[`notebooks/generate-submission-v7.ipynb`](notebooks/generate-submission-v7.ipynb).

## Measured results, not estimates

Every number above comes from a recorded verifier run. The receipts are in
[`receipts/`](receipts/):

- `receipts/v7-chemistry-verify.json` - the `dfthcsos` verifier result for the v7 chemistry assembly (PASS, 78,080 verified shots, 15,347 Toffolis, 427 qubits, score 309,206,676.09009403, `lambda_eff` 47.18429756505502)
- `receipts/v7-dqi-verify.json` - the `dqi` verifier result (PASS, 102,400 shots, 891 qubits, 0 value errors, 0 phase errors, circuit SHA-256)
- `receipts/v7-invsqrt-verify.json` - the `invsqrt` official-verifier report for the v7 fusion circuit (PASS, 62 qubits, circuit SHA-256, report SHA-256)
- `receipts/v7-submission-manifest.json` - SHA-256 and byte size of every member of `submission.zip`, the dataset path each member came from, and the archive's own SHA-256
- `receipts/v7-board-snapshot.json` - the leaderboard snapshot behind the rank lines above
- `receipts/apache-manifest.csv` - the public circuit ledger this rebuild is taken from
- `receipts/submission-manifest.json`, `receipts/dqi-verify.json`, `receipts/invsqrt-verify.json`, `receipts/dfthcsos-verify.json` - the earlier v6 receipts, kept for the record

## Reproduce it

You need one cell. The dataset is optional.

1. Optionally attach `manwithacat/vqcc-apache-public-circuits` (Add Input, then Datasets). If you do not attach it, turn **Internet** on in the Kaggle session panel and the cell will download the same 18 files itself.
2. Run [`notebooks/generate-submission-v7.ipynb`](notebooks/generate-submission-v7.ipynb), or paste its single cell into a Kaggle notebook.
3. The cell prints the archive SHA-256. It must equal
   `1d36f774d4eb7c2ce55b94c98f36dac87ab0f0fefda33312bb4ef869cc37ea22`.

To run it outside Kaggle, mount the dataset directory and point the two
environment variables at it:

```bash
export VQCC_INPUT_ROOT=/path/to/the/dataset/parent
export VQCC_WORK_DIR=/path/to/a/writable/dir
python3 notebooks/generate-submission-v7.ipynb
```

The archive is byte-reproducible: fixed timestamps, fixed member order, fixed
compression level. Only the zip container's bytes can differ if your zlib
build differs; the 18 members are pinned by SHA-256 and are identical.

Where each member comes from:

| archive member | path inside the dataset | author |
|---|---|---|
| `invsqrt.kmb` | `circuits/invsqrt/af4698478fba.kmb` | Agniv Banerjee |
| `dqi.kmb` | `circuits/dqi/993c70386a3d.kmb` | yoyobar |
| `dfthcsos/submission.npz` | `factorizations/b93b4db795e7.npz` | Kaliden Aiarys |
| `dfthcsos/angle_k_0..14.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_*.kmb` | see [NOTICE-v7.md](NOTICE-v7.md) |

## What this repository does NOT contain, on purpose

**No competition data.** The competition's own scoring kernel and a copy of a
reference instance's word table were committed to this repository in its first
two commits and removed from the branch on 3 November 2026. Removing a file
does not remove it from git history, so on **4 November 2026 the repository was
deleted and re-created** from a clean single-commit tree. This is the only way
to guarantee that nothing is distributable, because the rules state that
participants agree not to *"transmit, duplicate, publish, redistribute or
otherwise provide or make available the Competition Data to any party not
participating in the Competition"*, and the Competition Data includes
*"any prototype or executable code provided on the Competition Website"*.
A git history rewrite would leave the old objects reachable until GitHub
garbage-collected them; deleting and re-creating does not.

Concretely, the following are **not** in this repository and must never be
added to it:

- anything under `verifiers/`, `sample_submission/`, `kickmix/`, or the starter kit
- any `.kmb` circuit binary from the competition data
- the competition PDF or the metric notebook's source

Readers obtain the competition data themselves, from the competition page, as
participants do. Several other teams in this competition publish their own
code and notes and explicitly keep the competition data out for this reason.

## What we did not do

- We did not modify any verifier. `kickmix`, the verifiers and the reference
  circuits are the competition's own, Apache-2.0, and are used unmodified.
- We did not design, build or modify the seventeen circuit binaries in the
  current submission, nor the published factorization. We assembled,
  hash-pinned, verified and documented them.
- We did not measure our factors with our own scoring code. The official
  verifier does the scoring.
- We did not download any team's submission archive, and we did not use any
  private dataset. Every member was fetched from the public dataset
  `manwithacat/vqcc-apache-public-circuits` and is SHA-256 pinned.
- **Corrected, stated loudly:** an earlier version of this file said *"We did
  not take any circuit, artefact or score from another team's submitted
  archive."* For v7 that wording was misleading. These are other teams'
  circuits - the same circuit files those teams submitted, republished by a
  public Apache-2.0 dataset - and we did not author them. We corrected the
  sentence rather than leave it standing.
- **Open legal item, disclosed not buried:** the dqi circuit is from a lineage
  whose own author states that the earlier chain *"includes material without
  an explicit source license, which we do not relicense"*. The ledger's
  Apache-2.0 tag for it came from a notebook footer, not from the
  redistributed circuit bytes. We did not resolve this. It is documented in
  [NOTICE-v7.md](NOTICE-v7.md), and building our own dqi circuit from
  licence-clean source is the fix we are working on.

## Licence

Apache-2.0. See [LICENSE](LICENSE). The competition's own `kickmix` library and
verifiers are Apache-2.0 and are used unmodified; see [NOTICE.md](NOTICE.md).
