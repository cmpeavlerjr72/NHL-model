# SA-R3: thin-state (4v4 / 3v3) attempt hazard, T2 engine merge, G2 on H3'' + T2 (INV-32, Lane S3, 2026-10-16)

- Spec: `docs/models/shot_attempt/experiments.md` SA-R3 (21fe71e). Brief: `docs/briefs/lane_S3_shot_attempt_r3_2026-10-16.md`.
- Blind grade: `docs/tests/shot_attempt_sa_r3_grade_2026-10-16.md`. G2: `docs/tests/gates_g2_sa_r3_g2_A3g_r3t2_2026-10-16.md`.
- Frozen params: `docs/models/shot_attempt/sa_r3_frozen_params.json`. Results: `results/shot_attempt_r3/`, `results/sa_r3_g2_A3g_r3t2/` (gitignored).

**Outcome: NO arm passes the SA-R3 decision rule. The 3v3 cell fails offline in every arm (best: A3g-s at +4.2%, tolerance 3%).** A3g-s fixes 4v4 offline (-0.5%) but fails the strict D13 fold-1 guard on 4v4 (it overshoots, -2.2% against A3g's +1.5%). The c arms barely move anything, because the in-sample cells are near zero. The T2 merge is done: both parity tests are bit-identical and the full suite passes. G2 ran on A3g alone, with stage 1 = H3'' + T2. The core cells PASS and the run is CLEAN, but 4v4 (+4.4%) and 3v3 (+6.6%) FAIL, the same as SA-R2 on T1. The PM rules.

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start | 09:28:09 | |
| v3 thin-state levels (`build_shot_attempt_tables_v3.py`) | 09:30:21 | 09:30:48 |
| tune (b_c, fold 1) | 09:31:51 | 09:32:13 |
| fold 2 fits | 09:32:17 | 09:32:59 |
| fold 1 fits | 09:33:06 | 09:33:26 |
| blind grade | 09:34:59 | 09:35:02 |
| T2 merge fixture + parity tests | 09:35:49 | 09:36:44 |
| G2 slice (attempt table 172 s + 6 seeds 41 s) | 09:37:34 | 09:41:08 |
| G2 200 seeds, 4 parallel blocks of 50 | 09:41:15 | 09:47:44 |
| G2 grade | 09:47:53 | 09:47:55 |
| full test suite | 09:48:01 | 09:49:09 |

Slice projection: 6.8 s per seed per process. Four blocks of 50 seeds came to about 6.5 min wall, under the 15-min box rule, so no AWS request was filed.

## 1. Arms

Everything not listed is A3g as frozen in SA-R2.

- **A3g reproduction.** The refit fold-2 predictions are **bit-identical** to SA-R2's A3g (max |diff| 0).
- **A3g-s.** This arm uses `league_level_v3_f{1,2}` (k = 5): 5v5, 4v4 and 3v3 LC-1 levels, each with its own training-only profile. PP-for and PK keep their `_v2` levels. Level `lc1s` in `shot_attempt/models.py`.
- **A3g-c / A2g-c.** Cell = log((Y + b_c) / (M + b_c)) on training in-sample predictions. Tuned on fold 1:

| arm | b_c | in-sample pred/actual 4v4, 3v3 | cells 4v4, 3v3 (fold 2) |
|---|---|---|---|
| A3g-c | 50 (grid corner) | 1.015, 1.021 | -0.0162, -0.0133 |
| A2g-c | 800 (corner; LL flat to 1e-6) | 1.000, 1.000 | -0.0000, +0.0001 |

The GLM fits its st x ptype cells exactly in-sample, so A2g-c is A2g. The tree's in-sample over-prediction is only about 2%.

## 2. Bake-off, fold 2 (blind; salt `SA-R3-2026-10-16`)

| arm | LL/game vs A3g | SE | 4v4 bias (SE) | 3v3 bias (SE) | SA-R2 checks | D13 (fold 1) | passes |
|---|---:|---:|---|---|---|---|---|
| A2g-c | -0.1258 (worse by > 2 SE) | 0.0176 | +1.32% (2.42) PASS | **+5.44%** (2.23) FAIL | pass | pass | no |
| A3g | 0 | | **+3.12%** (2.43) FAIL | **+6.81%** (2.37) FAIL | pass (resp 1.17 / 1.08) | reference | no |
| A3g-c | +0.0012 | 0.0005 | +1.47% PASS | **+5.40%** FAIL | pass | pass | no |
| A3g-s | +0.0008 | 0.0036 | -0.54% PASS | **+4.24%** (2.30) FAIL | pass (1.17 / 1.07) | **FAIL** (4v4 -2.22% vs +1.53%) | no |

- **Noise floor.** |A3g - A3gs2| = 0.0015 nats/game. The seed-2 thin biases are +3.17% and +6.69%.
- **Cell power.** Every thin cell's SE (2.2-2.4%) is below the 3% tolerance, so each is labelled powered. A3g-s's 3v3 cell sits 1.8 SE from zero.
- **Fold-1 thin bias** (2023-24 test; SEs about 2.1 / 3.0):

| arm | 4v4 | 3v3 |
|---|---|---|
| A2g-c | +0.09% | +9.03% |
| A3g | +1.53% | +11.62% |
| A3g-c | +0.01% | +9.40% |
| A3g-s | -2.22% | +3.26% |

- **Segment breakdowns.** RS / PO, regulation / OT, home / away and month are in the grade file. Cells under 300 attempts are labelled UNDERPOWERED.

**Diagnosis (fold 2, in-sample vs test, offline).**

- **The shared ES level drives the A3g miss.** A3g's 3v3 rate tracks the ES level, which is 5v5-dominated. 5v5 rose (55.4, 56.7, 59.4, 58.4 per 60 for 2021-22 to 2024-25) while 3v3 fell (57.4, 56.9, 55.7, 55.2).
  - A3g's in-sample 3v3 pred/actual drifts by training season: 0.970, 1.004, 1.076.
  - So the test season inherits about +6% (level-implied / actual 1.062).
- **A3g-s halves the miss.** Its remaining +4.2% splits into two parts:
  - its 3v3 level runs +2.1% over the 2024-25 actual (shrunk toward 2023-24's 55.8, and noisy at about 25 team-hours);
  - the tree over-predicts 3v3 by about +1.9% in-sample. With min_data 800 and the 3v3 rows thin, the tree does not pin the cell.
- **The cells cannot fix it.** The c arms are in-sample corrections, and the defect is out-of-sample drift.

**Decision rule (literal): no arm passes. Selected: NONE.** No SA-R4 is pre-authorised, so the PM rules.

## 3. Engine merge (T2 into `sim.py`)

- **Flag.** `simulate(..., per_team_types=False)`. On, it reads `types[g, team, st, sc, per]` with shape (G, 2, 6, 5, 4, 4). Shape guards raise in both directions.
- **Retirement.** `sim_ss_r5.py` is marked SUPERSEDED and left in place as the parity reference.
- **Parity tests** (`tests/engine/test_sim_t2_merge.py`, sha256 of every output array):
  - **Flag off = pre-merge `sim.py`** (fixture `tests/fixtures/sim_t2_merge_parity.json`, recorded by `scripts/diag_engine_t2_parity_fixture.py` from the HEAD file, content-identical to 45d2b04). Three cases, all bit-identical:
    - synthetic stub goals (6 games x 8 seeds, seed0 3);
    - synthetic attempt variant;
    - real H3'' tables (16 games x 4 seeds).
  - **Flag on = `sim_ss_r5.simulate`**, bit-identical on synthetic per-team tables and on the real H3'' + T2 tables.
  - **Extra test.** A per-team table broadcast from the shared table, with attempts on, reproduces flag off exactly.
- **Lookup parity** for the SA-R3 arms (`tests/test_shot_attempt_lookup_r3.py`, including the `lc1s` and cell arms, and the 4v4 / 3v3 cells): PASS.
- **Full suite:** 124 passed, 1 xfailed.

## 4. G2 (A3g only, per the brief's no-pass clause; stage 1 = H3'' + T2 via the merged flag; goal stub as SA-R2; 200 seeds)

| cell | RS | overall | PO |
|---|---|---|---|
| per 60, 5v5 | 58.55 vs 58.35, +0.35% PASS | +0.43% PASS | UNDERPOWERED |
| per 60, PP | -0.49% PASS | -0.30% PASS | UNDERPOWERED |
| per 60, PK | -2.11% PASS | -1.35% PASS | UNDERPOWERED (+9.9%) |
| per 60, 4v4 | **50.77 vs 48.62, +4.42% FAIL** | **+4.18% FAIL** | UNDERPOWERED |
| per 60, 3v3 | **58.89 vs 55.23, +6.62% FAIL** | **+6.62% FAIL** | no actual 3v3 |
| attempts / team-game | 58.93 vs 59.48, -0.92% PASS | -0.93% PASS | UNDERPOWERED |
| team-game SD (reported) | 9.91 vs 11.61 | | |
| home-away corr (reported) | -0.23 vs -0.41 | | |
| score buckets -1 / 0 / +1 | -2.75% / +0.44% / +0.97% PASS | PASS | UNDERPOWERED |
| 100 vs 200 seeds | every status identical; per-60 moved by at most 0.054 | | |

**Decomposition, attempts per team-game, RS** (tolerance 1.78):

| component | value |
|---|---:|
| hazard level | +0.20 |
| EN unreachable | -1.69 |
| state visits | +0.97 |
| score visits | +0.04 |
| remainder | -0.07 |

- **Verdict: CLEAN.** It is also CLEAN overall and in PO (PO is UNDERPOWERED).
- **By state (RS).** 5v5, PP and PK are CLEAN. 4v4 and 3v3 FAIL, and the hazard level dominates both (+1.65 and +3.76 per 60).
- **Closed-loop responsiveness:** own 1.135 (0.997..1.314), opp 1.122 (0.973..1.328), PASS.
- **Per team** (UNDERPOWERED): correlation of for 0.93, against 0.94.
- **T2 vs T1 stage 1.** The G2 numbers are within 0.3 points of SA-R2's T1 run in every cell. T2 changes penalty types only, so attempts are insensitive to it, as expected.
- **EN watch item (D17, reported, not gated).** -1.69 of EN attempts are unreachable, offset by +0.97 of extra 5v5 time. This is unchanged.

## 5. Interpretation choices (labelled)

1. A3g-s: "EN keeps the ES level" is read as the SA-R2 ES (5v5 + 4v4 + 3v3) level. 5v5 rows take the new 5v5-only level.
2. The 3v3 profile's PO bin is set to 0. Bins with under 1 pooled training team-hour get p = 0, because playoff OT is 5v5.
3. The cells use in-sample training predictions, read literally. b_c is tuned separately for each base arm.
4. D13 guard, strict reading: BOTH thin cells' |fold-1 bias| must shrink against A3g's. Under a looser reading (only the cell being fixed), A3g-s would pass D13, but it still fails the fold-2 3v3 gate, so the outcome is the same.
5. The thin-gate SE is a game-block bootstrap (1,000 resamples) of the pred/actual ratio.
6. The G2 stage-1 tables are read from the SS-R5 cache (`lam_H3_fold2.npy`, `types_T2_fold2.npy`), read-only, with the same game order as `run_strength_state_g1_v5.build_tables`.
7. The attempt table is cached once per arm (`results/shot_attempt_r3/att_lam_A3g_fold2.npy`).

## 6. Not done

- `results/` was not pushed to HF. A shared-dir push would upload other lanes' in-progress files. Resume command: `.venv/Scripts/python.exe scripts/hf_sync_data.py push --dirs results`, for the PM or Lane O to schedule.

## 7. For the PM

- **What would need a ruling.** None of the pre-registered thin-state fixes passes. The residual 3v3 miss splits evenly between level noise and drift in a 25-team-hour cell, and the tree's own in-sample thin-cell bias. Both are inside about 2 SE of the cell, although the cell is labelled powered.
- **Candidates a new spec could consider:**
  - a GLM-style exact thin cell on a separate 3v3 level (A2g-s);
  - treating 3v3 as one pooled OT cell with a longer prior;
  - a ruling on how the 3v3 G2 cell gates.
