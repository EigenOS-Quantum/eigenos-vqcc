# NOTICE-v7 - provenance and licence evidence for the v7 submission

Date: 5 November 2026. Applies to `submission.zip`, SHA-256
`1d36f774d4eb7c2ce55b94c98f36dac87ab0f0fefda33312bb4ef869cc37ea22`,
26,174,071 bytes, 18 members.

This file supplements [NOTICE.md](NOTICE.md). NOTICE.md covers the v6 rebuild
and the earlier work. This one covers the v7 archive only, and it changes one
statement rather than quietly restating it.

## 1. Where every member came from

All eighteen members were downloaded from the public Kaggle dataset
`manwithacat/vqcc-apache-public-circuits` and SHA-256 pinned. No member was
hand-edited, re-saved, re-compressed or reconstructed by us. The byte sizes
below match the dataset's own file listing exactly.

| archive member | dataset path | bytes | SHA-256 (first 16) | author / origin |
|---|---|---:|---|---|
| `invsqrt.kmb` | `circuits/invsqrt/af4698478fba.kmb` | 479,055 | `af4698478fbad775` | Agniv Banerjee, from the public dataset `somejoint/qcc-ladder-parts` |
| `dqi.kmb` | `circuits/dqi/993c70386a3d.kmb` | 529,710,680 | `993c70386a3dde66` | yoyobar, "lb-22-99-invsqrt-101-62-qubits" |
| `dfthcsos/submission.npz` | `factorizations/b93b4db795e7.npz` | 1,866,292 | `b463690f734a8c4a` | Kaliden Aiarys |
| `dfthcsos/angle_k_0.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_0.kmb` | 413,385 | `2665ce00a1704f63` | see section 3 |
| `dfthcsos/angle_k_1.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_1.kmb` | 410,647 | `4a551d80b9845030` | see section 3 |
| `dfthcsos/angle_k_10.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_10.kmb` | 365,906 | `e832d29420b4beff` | see section 3 |
| `dfthcsos/angle_k_11.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_11.kmb` | 368,374 | `91d72f75bc5d33fe` | see section 3 |
| `dfthcsos/angle_k_12.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_12.kmb` | 362,461 | `1cc58e1bf53f1020` | see section 3 |
| `dfthcsos/angle_k_13.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_13.kmb` | 363,208 | `167b7d5a45dcf091` | see section 3 |
| `dfthcsos/angle_k_14.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_14.kmb` | 365,401 | `929035ff8206ad78` | see section 3 |
| `dfthcsos/angle_k_2.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_2.kmb` | 411,019 | `67fd7e8f917da9b5` | see section 3 |
| `dfthcsos/angle_k_3.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_3.kmb` | 408,565 | `0d96dcfd083d448e` | see section 3 |
| `dfthcsos/angle_k_4.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_4.kmb` | 362,425 | `a2b1bddb016684e7` | see section 3 |
| `dfthcsos/angle_k_5.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_5.kmb` | 362,028 | `e5a93b28520c35ce` | see section 3 |
| `dfthcsos/angle_k_6.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_6.kmb` | 364,878 | `ccdcb391f67e720e` | see section 3 |
| `dfthcsos/angle_k_7.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_7.kmb` | 363,581 | `7a4e30f7112cd70d` | see section 3 |
| `dfthcsos/angle_k_8.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_8.kmb` | 364,774 | `a04028ecf1002a9f` | see section 3 |
| `dfthcsos/angle_k_9.kmb` | `circuits/chemistry/a344f422f2e0/angle_k_9.kmb` | 363,298 | `60c4c540710a1ad7` | see section 3 |

Full SHA-256 for every member: [`receipts/v7-submission-manifest.json`](receipts/v7-submission-manifest.json).

## 2. The correction we are making loudly

The v6 README and NOTICE said:

> "We did not take any circuit, artefact or score from another team's submitted
> archive, and we did not use any private dataset. Every circuit we used was
> published, under Apache-2.0, before we used it."

For v7 that wording is misleading and we are retracting it rather than leaving
it standing. Precisely:

- We did **not** download any team's submission archive. We did **not** use any
  private dataset. Every byte came from the public dataset
  `manwithacat/vqcc-apache-public-circuits`.
- But these **are other teams' circuits** - the same circuit files those teams
  submitted, republished by a public Apache-2.0 dataset. We did not author
  them, we did not design them, and we do not claim otherwise.
- The ledger records each circuit's original `output_path` as the member name
  inside the author's own `submission.zip`. That is how the dataset was
  assembled, and it is disclosed here so a reader can trace every byte to the
  team whose work it is.

## 3. The chemistry assembly is a deliberate mix

The fifteen `angle_k` loaders come from the family `a344f422f2e0`. The
factorization `submission.npz` comes from a **different** published file,
`b93b4db795e7.npz`. We ran both available published factorizations through the
competition's own `dfthcsos` verifier against the same loaders:

| chemistry npz | official verifier score | verdict |
|---|---:|---|
| `b93b4db795e7.npz` (shipped) | **309,206,676.09009403** | better - shipped |
| `0ed964465654.npz` | 309,746,758.2195386 | worse by 540,082 |

Both are Apache-2.0 ledger files and both are disclosed here. The shipped
pairing is the one that measures better. The mixture is the point: the loaders
and the factorization are separately published artefacts by separately
identifiable authors, and we cite both.

## 4. The open legal item - dqi

The dqi circuit `993c70386a3d.kmb` is from **yoyobar**, published in the
notebook "lb-22-99-invsqrt-101-62-qubits" and republished in the public
ledger dataset.

The ledger records its licence as Apache-2.0, and the evidence it cites is the
**notebook's footer** - that records the licence of the notebook, not of the
redistributed circuit bytes. The same author's notebook states:

> "Borrowed components retain their own terms and attribution; the earlier DQI
> chain includes material without an explicit source license, which we do not
> relicense."

We checked whether this could be avoided by taking the other published dqi
circuit from the same task (`748b01a7a076`, alex chilton, 375,374,174,093.81 -
0.002% worse). It does not help: the ledger records that circuit as also
present in yoyobar's notebook, so it sits in the same lineage. There is no
licence-clean dqi circuit available to us from the public frontier.

**What we have done:** disclosed it here and in the README, rather than
carrying an unqualified "all Apache-2.0" claim.

**What we have not done:** resolved it. The fix is to build our own dqi
circuit from licence-clean source. That work is open, and it is also the only
way to win the dqi single-task prize, because a tie is broken in favour of
whoever entered first - which is not us.

## 5. Other licence checks

- `khattar-eea/` in the `andigu/uncompute` repository is **CC BY 4.0** (not
  OSI-approved) and is excluded from this submission.
- The `jday96314/QuantumAI` repository is 404 and excluded.
- The `invsqrt` circuit's licence is Apache-2.0 in the metadata of the public
  dataset `somejoint/qcc-ladder-parts`.
- The competition's own `kickmix` library and verifiers are Apache-2.0 and are
  used unmodified. Nothing under `verifiers/`, `sample_submission/` or the
  starter kit is redistributed in this repository.

## 6. Our own code

`notebooks/generate-submission-v7.ipynb`, `src/`, this file, the README and the
receipts are ours, Apache-2.0, as stated in [LICENSE](LICENSE).
