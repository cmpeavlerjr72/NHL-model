# SL-R4: L3c (EN on the baseline only, 4v4 / 3v3 baseline strata), cascade stage 4, Lane A4, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R4 (inherits SL-R3 / SL-R2 / SL-R1); D26. Brief: `docs/briefs/lane_A4_shot_attribute_r4_2026-10-16.md`.

**Outcome:**
- The in-sample check **PASSES** on the fold-2 training rows: every stratum with n >= 2,000 is within 0.5% of L0s (largest: 3v3 -0.47%).
- The **fold-1 D13 guard FAILS** for L3c: xG +2.62% overall, ES +4.34%, PK +5.45%, PP -3.23%, high-danger tier +1.68 pp.
- So the spec's stop applies. Nothing on fold 2 was predicted or read: no fold-2 grade, no decision, no engine change, no closed loop.
- **The failure is the level, not L3c.** Level E is identically zero on fold 1, because era 2 has no fold-1 training rows (the caveat SL-R2 labelled). The comparator L0s fails by the same amount (+2.49%). Every earlier arm on fold 1 fails the same way (SL-R1 / R2: +2.35% to +2.60%). Under the oracle level, L3c on fold 1 is +0.52% overall with every tier within 0.1 pp.
- **A separate warning:** L3c's fold-1 ES responsiveness is 0.37 / 0.49. That is well under the band, and the level does not cause it.

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start (brief read) | 11:41:03 | |
| fold-2 fits: L0s, L3c, L3cs2 | 11:43:39 | 11:43:55 |
| in-sample check, fold-2 training rows: **PASS** | 11:43:55 | 11:44:09 |
| fold-1 fits + in-sample + 2023-24 predictions | 11:44:44 | 11:45:26 |
| fold-1 blind grade (D13 guard): **FAIL** | 11:45:26 | 11:45:31 |
| fold-1 level diagnostic (oracle split; fold 1 only) | 11:46:08 | 11:46:19 |

All steps took seconds, so no box request was filed.

## 1. Construction (step 1)

`src/nhl_sim/shot_attribute/models_s.py` and `scripts/train_shot_attribute_v4.py` are new versioned files. The SL-R3 code is untouched.

**L0s: (14, 78) unlevelled table**, with rows = 7 team-view states x period type.
- **PP-for, PK, EN-for, EN-against:** the SL-R1 L0 row, unchanged.
- **5v5 cell shares:** a Dirichlet over the 5v5 counts (ALPHA0 = 10 on the pooled cell frequency, the L0 smoothing).
- **4v4 / 3v3 cell shares:** (n + 500 s_5v5) / (N + 500).
- **Type given cell, for the ES states:** the pooled-ES L0 row (5v5 + 4v4 + 3v3) of the same period type, normalised within each cell.
- **Level E:** applied per row as the level-group cell offset. 5v5, 4v4 and 3v3 take the ES ratio; EN stays pooled with ES, as in SL-R2.
- Fold-2 stratum n: 5v5 reg 286,983; 4v4 reg 4,137; 3v3 OT 3,749; 5v5 OT 857; 4v4 OT 197; 3v3 reg 3.

**L3c:** the SL-R3 frozen booster (15 leaves, 800 min-data, lr 0.02, 31 rounds; no re-tune, as written) with init_score = log L0s levelled.
- EN rows are excluded from training: 358,193 of 366,059 rows are used.
- EN rows are served L0s levelled. In-sample they are bit-identical to L0s.
- **L3cs2 is bit-identical to L3c,** so the floor is 0, as D26 labels it.

**Labelled readings:**
1. "Shrunk to the 5v5 cell shares" is read as the 5v5 stratum of the **same period type**. The 3v3 OT prior is therefore 5v5 OT (playoffs, n 857). At K = 500 against n = 3,749 that prior carries about 12% weight.
2. "Pooled ES" type-given-cell is read as pooled within the period type. That is exactly the SL-R1 L0 ES row.

## 2. In-sample check (fold-2 training rows): PASS

| stratum | n | L0s vs actual | L3c vs L0s | gated |
|---|---:|---:|---:|---|
| 5v5 | 287,840 | +0.07% | +0.07% | yes |
| PP | 53,097 | -0.00% | -0.08% | yes |
| PK | 9,170 | +0.04% | +0.27% | yes |
| 4v4 | 4,334 | **-4.43%** | +0.14% | yes |
| 3v3 | 3,752 | **-4.59%** | -0.47% (3v3 OT -0.47%) | yes |
| ENF | 5,721 | -0.07% | 0 (identical) | yes |
| ENA | 2,145 | +0.15% | 0 (identical) | yes |

- The state x period-type cells with n >= 2,000 are all within the limit as well.
- In-sample LL per attempt: L0s -3.18257, L3c -3.16557.
- Full table: `results/shot_attribute_r4/insample.json`.
- **Reported, not a gate:** L0s itself sits 4.4-4.6% below actual in-sample at 4v4 and 3v3. Two choices contribute: the 5v5 prior and the pooled-ES type-given-cell. The same holds at 4v4 regulation (-3.9%), where the K = 500 prior weighs only 11%. So the pooled-ES type conditional and the ES xG_ref column carry most of it. The spec fixed these choices; this is flagged for the PM.

## 3. Fold-1 D13 guard (blind grade, `--round r4 --fold 1`): FAIL, so stop

Report: `docs/tests/shot_attribute_sl_r4_grade_fold1_2026-10-16.md`.

| arm | xG overall | xG fails | tier fails | type | ES resp for / against | LL vs L0s (SE) |
|---|---:|---|---|---|---|---|
| L0s | +2.49% | ES +4.15, PP -3.18, PK +5.23, Jan +4.40 | high +1.65, low -1.95 (overall); ES, PK, ENF | PASS | 0.01 / -0.02 | 0 |
| **L3c** | **+2.62%** | ES +4.34, PP -3.23, PK +5.45, Jan +4.51, Apr +4.04 | high +1.68, low -2.03; ES, PK, ENF | PASS | **0.37 / 0.49** | +0.033 (0.021) |

Per state (reported, 4v4 / 3v3 UNDERPOWERED):

| | 5v5 | 4v4 | 3v3 |
|---|---|---|---|
| L3c xG | +4.5% | -2.0% | +0.2% |
| L3c medium tier | +0.55 pp | -5.7 pp | -9.0 pp |

The SL-R3 L0m loop had medium -14.5 / -10.4 pp at 4v4 / 3v3, so the split helps 4v4.

**Level diagnostic** (`scripts/diag_shot_attribute_r4_fold1_level.py`; fold 1 only, not blind, not a gate; oracle O = 2023-24's own final shares):

| level | arm | xG all | ES | PP | PK | ENF | high / med / low pp | ES resp |
|---|---|---:|---:|---:|---:|---:|---|---|
| E (as graded, = 0 on fold 1) | L0s | +2.49% | +4.15% | -3.18% | +5.23% | -1.65% | +1.65 / +0.31 / -1.95 | 0.01 / -0.02 |
| E | L3c | +2.62% | +4.34% | -3.23% | +5.45% | -1.65% | +1.68 / +0.35 / -2.03 | 0.37 / 0.49 |
| O (oracle) | L0s | +0.39% | +0.35% | +1.09% | -0.39% | -3.46% | -0.01 / -0.05 / +0.07 | 0.01 / -0.02 |
| O (oracle) | L3c | +0.52% | +0.55% | +1.02% | -0.20% | -3.46% | +0.02 / -0.02 / +0.00 | 0.39 / 0.49 |

**Reading:**
- The guard failure is the 2023-24 era step that level E cannot see on fold 1. It is the same signature as SL-R1's fold 1 and SL-R2's L0m / L3m fold 1 (+2.57% / +2.35%).
- **The D13 guard as written cannot be passed on fold 1 by any arm that uses level E.** This was knowable from SL-R2's caveat ("E is zero on fold 1, so the fold-1 diagnostic cannot test it"). I applied the stop anyway, because the spec says stop.
- **Two findings stand apart from the level:**
  1. **L3c under-responds on fold 1:** ES 0.37 / 0.49 (CI 0.30-0.49 / 0.38-0.68). For comparison, SL-R2's L3m on fold 1 was 0.68 / 0.81, and 1.09 / 0.86 on fold 2. Starting from a strong stratum baseline at lr 0.02 x 31 rounds leaves the ratings little room. Fold 1 is the diagnostic fold, so this is not a fold-2 result. It does say L3c is at risk on the fold-2 band.
  2. **ENF is -3.5% even under the oracle** (n 2,089, just above the 2,000 gate). ENF is L0s-only, so this is the baseline's EN mix, not tree leakage.

## 4. Not done (spec stop)

- No fold-2 predictions. `pred2` refuses to run unless both `insample.json` pass_all and `grade_fold1.json` d13_guard_pass are true.
- No fold-2 grade, bias checks, responsiveness or decision.
- No engine lookup change, and no closed loop. `sim.py` was not edited.

**Resume command, if the PM rules the guard inapplicable to the level** (for example, D13 judged under the oracle level, or on the E-independent checks):

```
.venv/Scripts/python.exe scripts/train_shot_attribute_v4.py pred2
.venv/Scripts/python.exe scripts/grade_shot_attribute.py --round r4 --fold 2
```

For this, `grade_fold1.json` must be re-ruled: the gate in `pred2` reads `d13_guard_pass`. The models are on disk in `results/shot_attribute_r4/models`.

## 5. Proposed text for PM-owned docs (not edited)

**LEARNINGS candidate L34:** *A guard on a fold where the level is structurally zero tests the level, not the arm. Level E needs training rows in the test season's era. On fold 1 there are none, so every E-levelled arm inherits the era step (+2.5% xG) and fails the fold-1 bias checks identically. L0s and L3c both failed, while under the oracle level L3c was +0.5%. For the sim: when pre-registering a forking-paths guard on an earlier fold, check first that every component the arm depends on is identifiable on that fold. Otherwise, judge the guard under the oracle level, or on the level-free checks (differences vs the comparator, tier shape, responsiveness).*

**For the PM to rule:**
- (a) Whether the D13 guard is re-specified as L3c minus L0s on fold 1, or as L3c under the oracle level on fold 1. Under that reading: xG +0.13 pp vs L0s and +0.52% under the oracle, tiers within 0.08 pp of L0s. As differences vs L0s every check passes (ENF identical); under the oracle every check the diagnostic computes (overall, group, tiers; months not computed) passes except ENF -3.46% (n 2,089, L0s-only, identical for L0s).
- (b) The fold-1 under-response (0.37 / 0.49). The fold-2 band may fail on its own. If so, the next respec is the booster's capacity (more rounds or a higher lr under the baseline start), not the strata.
- (c) The L0s baseline is 4.4-4.6% low at 4v4 / 3v3 in-sample, from the pooled-ES type-given-cell. These strata could take their own type conditional, shrunk to ES.

## Files

- New: `src/nhl_sim/shot_attribute/models_s.py`, `scripts/train_shot_attribute_v4.py`, `scripts/diag_shot_attribute_r4_fold1_level.py`.
- Grader: `scripts/grade_shot_attribute.py`, with a new `--round r4`. The r1 / r2 paths are unchanged, apart from an unused per-state table computed only when `states` is set.
- Reports: this file and `docs/tests/shot_attribute_sl_r4_grade_fold1_2026-10-16.md`.
- Results (gitignored): `results/shot_attribute_r4/` (fit2.log, insample.json / .log, fold1/, grade_fold1.json, fold1/level_diag.json).

---

## Resume after D28 (Lane A4b, 2026-10-16)

D28 (e96f793) restates the D13 guard as the fold-1 SL-R1 checks read on **L3c minus L0s**, with the oracle read reported alongside. EN strata are reported, not gated; they gate at stage 8. The restatement was committed before anything on fold 2 was predicted.

**Outcome:**
- The restated guard **PASSES**.
- On fold 2, **L3c is not eligible**, so no arm is selected:
  - ES responsiveness is 0.675 / 0.529 against the [0.8, 1.2] band (FAIL);
  - xG overall is +2.0007% against the 2.000% limit (FAIL, marginal);
  - PK is +3.31% against 3% (FAIL).
- L3c beats L0s by +0.141 nats per game (SE 0.016).
- The closed loop was skipped, as specified. No engine change was made.

### Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| resume start (pull e96f793) | 11:48:30 | |
| restated D13 guard (fold 1 only) | 11:48:54 | 11:48:57 |
| pred2 (fold-2 hash-labelled predictions) | 11:49:07 | 11:49:12 |
| blind fold-2 grade (`--round r4 --fold 2`) | 11:49:12 | 11:49:15 |

### 1. Restated D13 guard (fold 1): PASS

Computed by `scripts/diag_shot_attribute_r4_d13_restated.py`; the table is in `results/shot_attribute_r4/fold1/d13_restated.csv`.

**L3c minus L0s, with the SL-R1 tolerances:**
- xG overall: +0.13%.
- xG by group: ES +0.19%, PP -0.05%, PK +0.21%. EN is 0 by construction (reported).
- xG by month: the largest powered month is +0.19%.
- Tiers: every cell is within 0.16 pp.
- Types: every type is within 0.05 pp.

**Recorded in `grade_fold1.json`:**
- `d13_guard_basis: "L3c-minus-L0s (D28)"`
- `d13_guard_pass: true`
- `d13_guard_pass_original: false`

The oracle read is attached to the same file: L3c +0.52% xG, tiers within 0.03 pp.

### 2. Fold-2 blind grade

The grade report is `docs/tests/shot_attribute_sl_r4_grade_2026-10-16.md`. It uses one grader for every arm, with labels hashed until scoring was complete. The grader now marks EN group and tier cells "reported (EN, gates at stage 8, D28)" for r4 only.

| arm | LL / att | LL / game vs L0s (SE) | xG overall | xG fails | tier / type fails | ES resp for / against (95% CI) | eligible |
|---|---:|---:|---:|---|---|---|---|
| L0s | -3.21341 | 0 | +1.86% | none | none | -0.00 / 0.02 | no (flat, D24) |
| **L3c** | -3.21177 | **+0.1405 (0.0160)** | **+2.0007%** | overall, PK +3.31% | none | **0.675 (0.50-1.06) / 0.529 (0.39-0.79)** | **no** |

- **Seed floor:** L3cs2 is bit-identical to L3c, so the floor is 0 (D26).
- **Per group, L3c:**
  - xG: ES +2.65%, PP -0.48%, PK +3.31%, ENF +0.39% (reported), ENA +2.49% (reported).
  - Tiers overall: +0.59 / -0.45 / -0.14 pp.
- **Per state, L3c (reported):**

  | state | xG | medium tier |
  |---|---:|---:|
  | 5v5 | +2.84% | |
  | 4v4 | -3.18% | -5.2 pp |
  | 3v3 | -3.07% | -9.0 pp |

  4v4 and 3v3 are UNDERPOWERED.
- **Decision as pre-registered:**
  - L3c fails the bias checks: overall by 0.0007 pp, and PK +3.31%.
  - L3c fails the ES responsiveness band on both sides. Against is decisive: the CI upper bound is 0.79.
  - L3c is not worse than L0s; it is better by 8.8 SE.
  - **No arm selected.** shot_attribute stays BUILDING.

### 3. Reading (for the PM)

- **The under-response is the binding failure.**
  - Fold 1 was 0.37 / 0.49; fold 2 is 0.67 / 0.53.
  - SL-R2's L3m, started from the class frequency, gave 1.09 / 0.86 on fold 2.
  - The baseline start with the SL-R3 booster (lr 0.02, 31 rounds, frozen on fold 1 under an L0m start) leaves too little capacity for the rating terms.
  - The tuning was done for L3b with an L0m start, and SL-R4 reused it as written.
  - The next respec would be the booster's capacity (rounds / lr) re-tuned under the L0s start, with the fold-1 responsiveness spread reported per grid cell (the L24 guard).
- **The xG +2.0007% fail is marginal.** L0s is +1.86% on the same rows, so the level carries most of it. The trees add +0.14 pp.
- **PK +3.31% is mostly the baseline.** L0s is +2.86% on PK, and SL-R2's L0m was +2.86% too. The trees add +0.45 pp.
- **4v4 / 3v3:**
  - Medium-tier gaps shrink from -14.5 / -10.4 pp in the SL-R3 L0m loop to -5.2 / -9.0 pp offline.
  - xG is still about -3%.
  - This is consistent with the in-sample L0s -4.4% / -4.6% from the pooled-ES type-given-cell (listed in D28).

### Files (resume)

- `scripts/diag_shot_attribute_r4_d13_restated.py` (new).
- `scripts/grade_shot_attribute.py`: r4 `en_reported`.
- `docs/tests/shot_attribute_sl_r4_grade_2026-10-16.md` (fold-2 grade).
- `results/shot_attribute_r4/` (gitignored): grade_fold1.json, grade_fold2.json, fold1/d13_restated.csv, pred2.log.
