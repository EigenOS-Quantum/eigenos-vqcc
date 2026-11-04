# NOTICE

This repository is Apache-2.0 licensed (see [LICENSE](LICENSE)). It contains
code we wrote and code we adapted from other participants' public Apache-2.0
work. This file credits every third-party artefact, states the licence, and
records the one time we had to remove material for competition-rule reasons.

Two things are deliberately **absent** from this repository and are not
credited here because they must not be distributed: the competition's own
scoring kernel and a copy of a reference instance's word table. Both were
committed in the repository's first two commits, removed from the branch on
3 November 2026, and the repository was **deleted and re-created on
4 November 2026** so that no copy survives anywhere reachable. See the README
section "What this repository does NOT contain, on purpose".

## 1. The current submission (4 November 2026)

Three circuits assembled from public Apache-2.0 notebooks, verified with the
competition's own verifiers, and shipped by SHA-256 pin.

| benchmark | competition name | circuit | qubits | cost | factor vs reference |
|---|---|---|---:|---:|---:|
| `invsqrt.kmb` | fusion | `53000387a86b` | 62 | 98,061.19483958285 | 21.1783489x |
| `dqi.kmb` | combinatorial optimization | `748b01a7a076` | 891 | 375,374,174,093.81177 | 65.1069392x |
| `dfthcsos/angle_k_0..14.kmb` + `dfthcsos/submission.npz` | chemistry | `37204439f717` | 428 | 312,444,127.2287831 | 10.7398390x |

Local geometric mean of the three ratios: **24.556835**.

### The upstream authors of the three circuits

- **invsqrt** - Leo Tang, "VQCC T7421 Submission",
  <https://www.kaggle.com/code/leotang09/vqcc-t7421-submission>, released
  2026-11-04 07:39 UTC, Apache-2.0. Archive member `53000387a86b`, taken from
  `circuits/invsqrt/53000387a86b.kmb` in the public Apache-2.0 dataset
  `manwithacat/vqcc-apache-public-circuits`.
- **dqi** - alex chilton, "24.51 LB: Verified Three-Task Portfolio",
  <https://www.kaggle.com/code/alexchilton/24-51-lb-verified-three-task-portfolio>,
  released 2026-11-04 03:14 UTC, Apache-2.0. Archive member `748b01a7a076`,
  taken from `circuits/dqi/748b01a7a076.kmb`.
- **dfthcsos** - Heliosli, "The dataset is public now. Enjoy!",
  <https://www.kaggle.com/code/heliosli/the-dataset-is-public-now-enjoy>,
  released 2026-11-04 04:10 UTC, Apache-2.0. Archive family `37204439f717`,
  taken from `factorizations/37204439f717.npz` and
  `circuits/chemistry/37204439f717/angle_k_*.kmb`. The underlying parts are
  **Isabe11aM00re**'s (9, 143, 39) factorisation and weights on **Syed Asad
  Ali**'s newer angle loaders; the per-slot combination is Heliosli's.

Every one of the three is Apache-2.0. Apache-2.0 section 4 requires that
recipients of a derivative work receive this NOTICE, that the licence and
the notice are reproduced, and that modified files carry prominent change
notices. We have not modified these circuits; we have assembled them.

### The earlier submission's three circuits (2 November 2026)

Recorded for the audit trail. The 2 November submission used `bce2948ff24e`
(Ehan Mallick), `3779a3431e9c` (Akmal Xodarev / busyaprime) and `289aafc7c5e7`
(Isabe11aM00re). The full attribution for each is preserved in the appendix
below.

---

## 2. The generators of the earlier attempt

The modules under `src/gen_invsqrt/` and `src/gen_dfthcsos/` build the
**earlier** submission, which scored **2.53419**. They are ports and
adaptations of other competitors' public Apache-2.0 notebooks, credited below
by name, by URL and by licence. They are kept here as credited work and as a
record of what was tried. They are **not** on the build path of the current
submission.

## 3. Upstream provenance of the earlier attempt's generators

### `invsqrt` (fusion)

Earlier artefact: one `invsqrt.kmb`, 103 qubits. Built by `src/gen_invsqrt/build_ref.py`
from `src/gen_invsqrt/stage_ref.py`.

The provenance chain, in order:

1. **Sumit Chongder** - the centred signed-digit inverse-square-root generator, the
   coefficient fitting, the integer pipeline and the arithmetic. Apache-2.0. Public Kaggle
   notebook "notebook2f196e646b":
   - https://www.kaggle.com/code/sumitchongder/notebook2f196e646b?scriptVersionId=361357149
2. **Artem1410 / anazemcev** - "Signed-Digit Memory": split high-word phasing, allocation
   after normalization, folded final carry and the borrowed constant input bit that gives
   the 93-qubit revision. Apache-2.0:
   - https://www.kaggle.com/code/anazemcev/quantum-circuits-signed-digit-memory
3. **Rudra Bhaskar** - "Highest Public Score | Direct Polynomial Phasing": derivative
   split, top-carry reuse and the static-high phase checkpoint, giving 95 qubits.
   Apache-2.0:
   - https://www.kaggle.com/code/rudrabhaskar/highest-public-score-direct-polynomial-phasing?scriptVersionId=361445283
4. **Alex Chilton** - "Where the Toffolis Go: Anatomy + a Cheaper invsqrt": shared-prefix
   normalization, temporary-AND moves into empty shift targets, and the v6 circuit
   (93 qubits). Apache-2.0:
   - https://www.kaggle.com/code/alexchilton/where-the-toffolis-go-anatomy-a-cheaper-invsqrt?scriptVersionId=361472684
5. **Kirill Tymchishin** - "Quantum Circuits | QROM + Tower42": the integration of the
   above, and the builder module `stage_ref.py` that constructs that earlier circuit.
   Apache-2.0:
   - https://www.kaggle.com/code/kirilltym/quantum-circuits-qrom-tower42

**The earlier attempt's `invsqrt` circuit was Kirill Tymchishin's `stage_ref.py` line.**
`src/gen_invsqrt/stage_ref.py` is byte-identical to the `stage_ref.py` module published in
his notebook (sha256 `c828f54051099b56f0890a54f7171b38226514599c09b5b137a4f55f25ed4b66`).
We did not modify it. Our contribution to the `invsqrt` member is the build driver, the
coefficient table, the verifier receipts and the packaging.

Also credited, because their published work is upstream of the code we ship and their
notices require us to carry the credit forward:

- **lightningv08** - "Quantum Circuits | Memory & Algebra": compressed normalization flags.
  Apache-2.0: https://www.kaggle.com/code/lightningv08/quantum-circuits-memory-algebra
- **Mizero Lucky Gall (mizeroluckygall)** - "Quantum Circuits | Rotation Calibration":
  full-input rotation activation collection, cutting-plane linear programming and the
  integer phase-margin checks. Apache-2.0:
  - https://www.kaggle.com/code/mizeroluckygall/quantum-circuits-rotation-calibration-39-char?scriptVersionId=361537580
- **Cuccaro, Cleve and Watrous**, "A new quantum ripple-carry addition circuit",
  arXiv:quant-ph/0410184 - the MAJ/UMA carry identities used by
  `src/gen_invsqrt/hybrid_add.py`. No URL for this paper is recorded in our evidence
  corpus; the upstream notices cite it by name.
- **Gidney**, "Halving the cost of quantum addition",
  https://quantum-journal.org/papers/q-2018-06-18-74/ - the measured-carry adder, the
  temporary-AND erasure and the normalization-flag clearing used by
  `src/gen_invsqrt/hybrid_add.py` and by the signed-digit generator.
- **Gu, Kemeny, Yelin and Lukin**, arXiv:2610.22367,
  https://github.com/andigu/uncompute (Apache-2.0) - the reversible decoder algebra
  whose Gaussian-circuit scheduling idea `src/gen_invsqrt/deferred_lookup.py` follows.
- **Dmitrii Gluzdov** - "Quantum Circuit Compilation from Source" V4 and V6: the
  deferred coefficient-register demolition and the shared algebraic-normal-form
  measurement phase repair that `src/gen_invsqrt/deferred_lookup.py` adapts.
  Apache-2.0:
  - https://www.kaggle.com/code/dmitriigluzdov/quantum-circuit-compilation-from-source?scriptVersionId=361569612
  - https://www.kaggle.com/code/dmitriigluzdov/quantum-circuit-compilation-from-source?scriptVersionId=361592338

### `dfthcsos` (chemistry)

Earlier artefacts: 15 `ANGLE_k` circuits plus `submission.npz`, 681 qubits in total.
Built by `src/gen_dfthcsos/build_family.py` from `src/gen_dfthcsos/banked_lab.py`.
The word-table copy it used to read has been removed from this repository; see
section 1.

1. **Artem1410 / anazemcev** - "Quantum Circuits | Open QROM": the optimised sparse SOS
   factors and the earlier public decoder binaries. Apache-2.0:
   - https://www.kaggle.com/code/anazemcev/quantum-circuits-open-qrom-measured-gains
2. **Artem1410 / anazemcev** - "Clean Staging" (`vqcc-banked-clean-staging`): the exact
   GF(2) output-basis compression and the removal of zero and dependent difference-bank
   columns. Apache-2.0:
   - https://www.kaggle.com/code/anazemcev/vqcc-banked-clean-staging?scriptVersionId=361470758
3. **Kozykorpesh (Kozykappa)** - "Quantum AI | Compact Arithmetic Banked QROM": the
   two-address banked XOR QROM construction, adapted from Sumit Chongder's public
   arithmetic. Apache-2.0:
   - https://www.kaggle.com/code/kozykappa/quantum-ai-compact-arithmetic-banked-qrom?scriptVersionId=361433617
4. **Kozykorpesh (Kozykappa)** - "Quantum AI | LB score - 6.68108": physical ensemble
   compression, sparse column rotations, reachable-control simplification, clean-wire
   allocation, and the four DQI scheduling gadgets. Apache-2.0:
   - https://www.kaggle.com/code/kozykappa/quantum-ai-lb-score-6-68108?scriptVersionId=361677445
5. **Kirill Tymchishin** - "Quantum Circuits | QROM + Tower42" v10 and v11: the integration
   of the above, the batch selection of J = 5 from a 4/5/6/7 comparison, and the builder
   module `banked_lab.py` that we ship. Apache-2.0:
   - https://www.kaggle.com/code/kirilltym/quantum-circuits-qrom-tower42
6. **Dmitrii Gluzdov** - "Quantum Circuit Compilation from Source": the competition-field
   port and the readable source-built portfolio. Apache-2.0:
   - https://www.kaggle.com/code/dmitriigluzdov/quantum-circuit-compilation-from-source
7. **k256.dev** - the original factor refinement traces for the starting chemistry
   factorization, as recorded in the upstream notices:
   - https://www.kaggle.com/code/k256net/claude?scriptVersionId=361337610
8. **Dmitrii Gluzdov** - the public FeMoCo dataset "vqcc-femoco-public-factorization",
   version 2 (source 21143008), Apache-2.0:
   - https://www.kaggle.com/datasets/dmitriigluzdov/vqcc-femoco-public-factorization/versions/2
   - The word table this build used was a byte-identical copy of that dataset file
     (sha256 `9afd0ca5e90dd1740fe713e4ac1c26736184ea9bc4d4b57a6eeefafd608ee193`).
     It has been removed from this repository; see section 1.

**Correction of an earlier claim in this file.** An earlier version of this NOTICE called
the GF(2) change of basis to the difference bank "our change". It is not ours. It is
anazemcev/Artem1410's "Clean Staging" output-basis compression, integrated in Kirill
Tymchishin's published `banked_lab.py`, which we ship byte-identically. What we did is
enable that upstream option (`mode=linear`) in our own build driver, and it applies to
`angle_k_2` through `angle_k_14`. The words "Our change" in the header of
`src/gen_dfthcsos/banked_lab.py` are the upstream author's words, not ours; we ship that
file unchanged.

Two of the fifteen chemistry circuits the earlier attempt submitted, `angle_k_0` and
`angle_k_1`, are
byte-identical to the circuits Kirill Tymchishin's public notebook produces (sha256
`28ef7c7eb63f08fcd5a5aa622c5d5b44116dde74e8161bb13bceadce8b28d971` and
`6258f37d546783315e528b14b2c86d35dacb34e6441e0cacefe902320661c4bc`). The other thirteen
differ from his because we apply the GF(2) change of basis to them. We state this so that
no reader can mistake all fifteen for our own work.

### `dqi` (combinatorial optimization)

- The earlier attempt's `dqi` member was a **byte-identical copy of a published
  decoder**, not the competition's official sample circuit. This notice said
  otherwise before 2 November 2026 and was wrong; the correction is recorded here
  rather than left in place. We did not build a dqi decoder and we do not claim
  one. The current submission's `dqi` member is credited in section 1.
- For the record, the decoder lineage that the public notes describe is:
  - **Gu, Kemeny, Yelin and Lukin**, "Reversible decoding" (arXiv:2610.22367),
    https://arxiv.org/abs/2610.22367 and https://github.com/andigu/uncompute,
    Apache-2.0 - the truncated Berlekamp-Massey reversible decoder.
  - **Kozykorpesh (Kozykappa)** - the four scheduling gadgets that take the port from
    1,837 to 1,789 qubits:
    https://www.kaggle.com/code/kozykappa/quantum-ai-lb-score-6-68108
  - **Alex Chilton** - the port of that decoder onto this competition's task:
    https://www.kaggle.com/code/alexchilton/where-the-toffolis-go-anatomy-a-cheaper-invsqrt
  - **k256.dev** and **anazemcev "Open QROM"** - the earlier public decoder binaries.
  - **Kirill Tymchishin** - the dqi candidate in his portfolio:
    https://www.kaggle.com/code/kirilltym/quantum-circuits-qrom-tower42
- `notebooks/vqcc-dqi-build.ipynb` is included as a **rebuild attempt. It is not the
  source of our submitted member.** That notebook carries 13 decoder source files
  recovered from Kozykorpesh's public kernel "Quantum AI | LB score - 6.68108"
  (Apache-2.0), corroborated against the public upstream
  https://github.com/andigu/uncompute at pinned commit
  `64b5a13aa249f1360846657392e6c66817b26d0f` (Apache-2.0), with the Apache-2.0 licence
  text shipped beside them as `gen_dqi_v6/ref/GU_LICENSE`. Each file is checked against
  the SHA-256 map published in that kernel. We do not claim that rebuild as our work, and
  the earlier attempt's `dqi.kmb` was a copy of a published decoder, not that notebook's
  output.

## 4. Attribution map: shipped file to upstream file

| shipped file | upstream counterpart | author and licence | relation to the upstream work |
|---|---|---|---|
| `src/gen_invsqrt/stage_ref.py` | `stage_ref.py` module in "Quantum Circuits \| QROM + Tower42" | Kirill Tymchishin, Apache-2.0, credited by him to Sumit Chongder's public generator | byte-identical copy. **No attribution header in the file.** This is the file that builds the `invsqrt` circuit of our EARLIER attempt, not of the current submission. |
| `src/gen_invsqrt/sumit_reference.py` | the same `stage_ref.py` module | Kirill Tymchishin, Apache-2.0, credited by him to Sumit Chongder | byte-identical to the same upstream module (same sha256 as the row above). **No attribution header in the file.** |
| `src/gen_invsqrt/signed_digit_lab.py` | Sumit Chongder's centred signed-digit generator, notebook "notebook2f196e646b" | Sumit Chongder, Apache-2.0 | his source, with our added exact integer certificate, reporting helpers and memory-schedule adaptations. Header present in the file. |
| `src/gen_invsqrt/round2.py` | Sumit Chongder's schedules and Rudra Bhaskar's R4/R5 | Sumit Chongder and Rudra Bhaskar, Apache-2.0 | derived from both; our changes are configurable precisions and split widths, borrowing the normalized leading one for a clean carry, and pruning the final phase-shift stage on the promised `s <= 10` bound. Header present. |
| `src/gen_invsqrt/hybrid_add.py` | new implementation by us | ours, Apache-2.0; identities credited to Cuccaro et al. and Gidney | our file. Header present. |
| `src/gen_invsqrt/deferred_lookup.py` | new implementation by us | ours, Apache-2.0; scheduling idea credited to Gu, Kemeny, Yelin and Lukin | our file. Header present. |
| `src/gen_invsqrt/stage_r5.py` | `stage_r5.py` module in "Quantum Circuits \| QROM + Tower42" | Kirill Tymchishin, Apache-2.0, over Sumit Chongder's generator | byte-identical copy. Header present. Its dependency `private_arithmetic_r4.py` is shipped in this repository (next row), so the module runs. It is **not** on the build path of the submission we shipped. |
| `src/gen_invsqrt/private_arithmetic_r4.py` | `private_arithmetic_r4.py` module in "Quantum Circuits \| QROM + Tower42" | Kirill Tymchishin, Apache-2.0; the derivative split and top-carry reuse are credited by him to Rudra Bhaskar, over Sumit Chongder's generator | byte-identical copy. Header present. Shipped so that `stage_r5.py` resolves its import; not on the build path of the submission we shipped. |
| `src/gen_invsqrt/tables_ref.pkl` | the coefficient table and layout produced by `stage_ref.build_tables()` | upstream fitting code (Sumit Chongder's, as credited above) | generated output of the upstream generator at the configuration F2 = 10, F1 = 19, FYR = 26, GY = 2, DROP2 = (5,). sha256 `cf60c2935d59001954ede9ca27b671fce195c670fc4bc0296ec9ce8fafca9254`. Used by the earlier attempt's build, not by the current submission. |
| `src/gen_invsqrt/build_ref.py` | - | ours, Apache-2.0 | our build driver for the `invsqrt` member. |
| `src/gen_invsqrt/sweep_tables.py` | - | ours, Apache-2.0 | our precision sweep over the upstream generator. |
| `src/gen_invsqrt/spot.py` | - | ours, Apache-2.0 | our spot-check harness. |
| `src/gen_dfthcsos/banked_lab.py` | `banked_lab.py` module in "Quantum Circuits \| QROM + Tower42" | Kirill Tymchishin, Apache-2.0, over Kozykorpesh's banked QROM and anazemcev/Artem1410's Clean Staging compression | byte-identical copy. Header present. Its "Our change" refers to the upstream authors, not to us. |
| `src/gen_dfthcsos/build_family.py` | - | ours, Apache-2.0 | our build driver for the `ANGLE_k` family of our EARLIER attempt, not of the current submission. |
| `src/gen_dfthcsos/physics.py` | - | ours, Apache-2.0 | our physics evaluation harness for the earlier attempt. |
| `notebooks/vqcc-dqi-build.ipynb` | 13 decoder source files recovered from Kozykorpesh's "Quantum AI \| LB score - 6.68108", corroborated against `andigu/uncompute` at commit `64b5a13` | Kozykorpesh and Gu, Kemeny, Yelin and Lukin, Apache-2.0 | third-party source carried inside the notebook. It does not produce the current submission's `dqi.kmb`. |
| `notebooks/t54-kickmix-audit.ipynb` | - | ours, Apache-2.0 | our audit of the three reference benchmarks. Reads `kickmix` from the competition data. It is an audit, not a generator. |
| `receipts/` | - | ours | our verifier outputs and the submission manifest. |
| `src/fetch_frontier.py` | - | ours, Apache-2.0 | our fetcher for the current submission. Pins all 18 member hashes and fails closed.
| `src/verify_frontier.py` | - | ours, Apache-2.0 | our driver for the competition's own verifiers.
| `src/package_submission.py` | - | ours, Apache-2.0 | our packager for the current submission.
| `notebooks/vqcc-frontier-blend.ipynb` | - | ours, Apache-2.0 | the GENERATING notebook for the current submission.
| `README.md`, `REPRODUCE.md`, `NOTICE.md`, `CITATION.cff`, `LICENSE` | - | ours, Apache-2.0 | our documentation. |

**The two shipped files that carry no attribution header of their own** are
`src/gen_invsqrt/stage_ref.py` and `src/gen_invsqrt/sumit_reference.py`. They are
byte-identical to each other and to the `stage_ref.py` module published by Kirill
Tymchishin in "Quantum Circuits | QROM + Tower42" (Apache-2.0,
https://www.kaggle.com/code/kirilltym/quantum-circuits-qrom-tower42), which is in turn the
centred signed-digit generator that its author credits to Sumit Chongder's public
notebook. `stage_ref.py` is the file that builds the earlier attempt's `invsqrt`
circuit. We have
not edited either file, so this NOTICE is where their attribution lives.

The build path of the EARLIER archive was: `src/gen_invsqrt/build_ref.py` (with
`src/gen_invsqrt/stage_ref.py` and `src/gen_invsqrt/tables_ref.pkl`) for `invsqrt`;
`src/gen_dfthcsos/build_family.py` (with `src/gen_dfthcsos/banked_lab.py`) for
`dfthcsos`; a published `dqi` decoder copied byte-identically for `dqi`; and
`src/package_submission.py` for the archive. Everything else in `src/` is
supporting material, credited above.

---

## 5. What actually runs

The current submission is produced by three commands. None of them uses our own
scoring code; the competition's own verifiers do the scoring.

| step | command | what it reads |
|---|---|---|
| fetch | `python3 src/fetch_frontier.py --out /tmp/frontier` | the public Apache-2.0 dataset; every one of the 18 members is checked against a SHA-256 pinned in the script, and a member with no pinned hash is a failure |
| verify | `python3 src/verify_frontier.py --circuits /tmp/frontier --verifiers $EIGENOS_VQCC_VERIFIERS` | the competition's own `invsqrt`, `dqi` and `dfthcsos` verifiers, unmodified; writes one receipt per task |
| pack | `python3 src/package_submission.py /tmp/frontier submission.zip` | the 18 verified members; the archive is then extracted back out and every member re-hashed from the extracted copy |

`notebooks/vqcc-frontier-blend.ipynb` is the same pipeline as a notebook, with
a gate at every step: an unpinned member, a missing verifier and a hash
mismatch each stop it before anything is packaged.

Every other Python file under `src/gen_invsqrt/` and `src/gen_dfthcsos/` is
reference and attribution material for the earlier attempt. It is shipped so
that the upstream lineage of that work can be read, checked and re-run, not
because the current submission depends on it. Nothing in this repository
re-implements or modifies the competition's verifiers.

---

## 6. What we did not do

- We did not modify any verifier. `kickmix`, the verifiers and the reference
  circuits are the competition's own, Apache-2.0, and are used unmodified.
- We did not design, build or modify any of the three circuits in the current
  submission. We assembled, hash-pinned, verified and documented them.
- We did not measure our factors with our own scoring code. The official
  verifier does the scoring. The factor for each task is the organisers'
  reference cost, which the metric kernel measures at grading time, divided by
  the cost the official verifier reports; both numbers are in the receipts.
- We did not take any circuit, artefact or score from another team's submitted
  archive, and we did not use any private dataset. Every circuit we used was
  published, under Apache-2.0, before we used it.
- We did not invent the algorithms the earlier attempt shipped. They are other
  people's published work, credited above.
- We did not redistribute any third-party binary in the current submission
  other than the three Apache-2.0 circuits it is made of, credited above with
  their SHA-256.
