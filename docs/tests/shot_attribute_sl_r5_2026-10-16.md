# SL-R5: booster capacity under the L0s start (L3d), cascade stage 4, Lane A5, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R5 (inherits SL-R4 / R3 / R2 / R1); D28, D30. Brief: `docs/briefs/lane_A5_shot_attribute_r5_2026-10-16.md`.

**Outcome:**
- **Grid and selection (fold 1), committed in 399c1c7 before any fold-2 prediction.** L3d = lr 0.02, 15 leaves, 800 min-data, 22 rounds. Its fold-1 ES spread ratios are 0.283 / 0.382. Only 2 of the 18 cells lie within 2 SE of the best inner LL, and the best-LL cell is also the one closest to 1.
- **In-sample stratum check: PASS.** On the fold-2 training rows the largest gap is 3v3 -0.41%. **D28 guard (fold 1, L3d minus L0s): PASS.** xG differs by at most +0.18%, tiers by at most 0.13 pp, types by at most 0.04 pp.
- **Fold 2 (blind): L3d is NOT eligible.** L3d beats L0s by +0.1316 nats per game (SE 0.0128), but it fails two gates:
  - **ES responsiveness 0.517 (CI 0.38-0.81) / 0.413 (CI 0.31-0.62): FAIL.** This is worse than L3c's 0.675 / 0.529.
  - **PK xG +3.21%: FAIL.** L0s is +2.86%.

  xG overall is +1.97% (PASS), and every tier and type share passes.
- **No arm is selected.** The D30 stop rule applies: stage-4 work stops and the PM takes the options to the user. No engine change was made and no closed loop was run, since step 4 applies only on selection.

## Clock (Get-Date / date, EDT)

| step | start | end |
|---|---|---|
| lane start (brief read) | 11:51:02 | |
| fold-1 grid (18 cells, inner early stopping + full fold-1 refit + spread on 2023-24) | 11:53:22 | 11:57:25 |
| commit + push of the grid / selection (399c1c7) | about 11:57:30 | before 11:57:40 |
| fold-2 fits L0s, L3d, L3ds2 | 11:57:40 | 11:57:52 |
| in-sample check (fold-2 training rows): **PASS** | 11:57:53 | 11:58:06 |
| fold-1 fits + 2023-24 predictions | 11:58:11 | 11:58:31 |
| D28 guard + oracle read: **PASS** | 11:58:32 | 11:58:38 |
| pred2 (hash-labelled 2024-25) | 11:58:49 | 11:58:55 |
| blind fold-2 grade (`--round r5 --fold 2`) | 11:58:55 | 11:58:58 |

Every step ran in seconds or a few minutes, so no box request was filed.

## 1. Grid and selection (fold 1)

Code: `scripts/train_shot_attribute_v5.py tune`.

**Setup:**
- **Inner split.** The inner validation set is the last 20% of fold-1 training games by date (561 games, 48,935 rows). The inner L0s is fit on the inner-training rows. EN rows are excluded from the booster.
- **Early stopping.** Each cell stops after 50 rounds without improvement, with a cap of 2,000 rounds. No cell came near the cap.
- **Inner LL.** It is the per-game sum on the inner-validation games. The SE vs the best cell comes from a paired game-block bootstrap with 1,000 resamples.
- **Fold-1 ES spread ratios.** Each cell is refit on all fold-1 training rows at its own round count, then predicts 2023-24. The ratios use the grader's responsiveness definition: team-game quintiles of own_r / opp_r on ES rows, with Q5 - Q1 of mean xG_ref, predicted over actual. The refit reproduces the guard's read of L3d exactly (0.283 / 0.382).
- **Selection (D27 form).** Among cells within 2 SE of the best LL, take the smallest max(|log for|, |log against|). Ties within 0.02 go to the fewer leaves x rounds.

Files: `docs/models/shot_attribute/sl_r5_grid_fold1.csv` and `sl_r5_frozen_params.json`. L0s alone on fold 1 is 0.008 / -0.017.

|    lr |   leaves |   min data |   rounds |   leaves x rounds |   inner LL/game vs L0s |   vs best |   SE vs best | within 2 SE   |   fold-1 ES for |   fold-1 ES against |   max abs log | selected   |
|------:|---------:|-----------:|---------:|------------------:|-----------------------:|----------:|-------------:|:--------------|----------------:|--------------------:|--------------:|:-----------|
| 0.020 |       15 |        200 |       40 |               600 |                  0.057 |    -0.124 |        0.050 | False         |           0.419 |               0.579 |         0.871 | False      |
| 0.020 |       15 |        800 |       22 |               330 |                  0.181 |     0.000 |        0.000 | True          |           0.283 |               0.382 |         1.262 | True       |
| 0.020 |       31 |        200 |       25 |               775 |                 -0.023 |    -0.205 |        0.061 | False         |           0.325 |               0.458 |         1.125 | False      |
| 0.020 |       31 |        800 |       15 |               465 |                  0.157 |    -0.025 |        0.013 | True          |           0.231 |               0.296 |         1.466 | False      |
| 0.020 |       63 |        200 |       21 |              1323 |                 -0.088 |    -0.270 |        0.065 | False         |           0.298 |               0.418 |         1.211 | False      |
| 0.020 |       63 |        800 |        9 |               567 |                  0.137 |    -0.044 |        0.020 | False         |           0.168 |               0.190 |         1.784 | False      |
| 0.050 |       15 |        200 |        2 |                30 |                 -0.217 |    -0.398 |        0.047 | False         |           0.033 |               0.104 |         3.407 | False      |
| 0.050 |       15 |        800 |       10 |               150 |                  0.152 |    -0.029 |        0.010 | False         |           0.415 |               0.405 |         0.904 | False      |
| 0.050 |       31 |        200 |        2 |                62 |                 -0.209 |    -0.391 |        0.046 | False         |           0.066 |               0.145 |         2.717 | False      |
| 0.050 |       31 |        800 |        6 |               186 |                  0.106 |    -0.075 |        0.016 | False         |           0.356 |               0.281 |         1.270 | False      |
| 0.050 |       63 |        200 |        2 |               126 |                 -0.215 |    -0.396 |        0.046 | False         |           0.070 |               0.154 |         2.663 | False      |
| 0.050 |       63 |        800 |        4 |               252 |                  0.091 |    -0.090 |        0.022 | False         |           0.320 |               0.193 |         1.643 | False      |
| 0.100 |       15 |        200 |        2 |                30 |                 -6.842 |    -7.023 |        0.830 | False         |          -0.179 |              -0.577 |       inf     | False      |
| 0.100 |       15 |        800 |        4 |                60 |                 -0.161 |    -0.343 |        0.046 | False         |           0.334 |               0.507 |         1.097 | False      |
| 0.100 |       31 |        200 |        2 |                62 |                 -4.836 |    -5.017 |        0.489 | False         |          -0.098 |              -0.484 |       inf     | False      |
| 0.100 |       31 |        800 |        4 |               124 |                 -0.251 |    -0.433 |        0.047 | False         |           0.356 |               0.530 |         1.032 | False      |
| 0.100 |       63 |        200 |        2 |               126 |                 -4.862 |    -5.043 |        0.472 | False         |          -0.065 |              -0.408 |       inf     | False      |
| 0.100 |       63 |        800 |        4 |               252 |                 -0.303 |    -0.484 |        0.052 | False         |           0.369 |               0.549 |         0.998 | False      |

**Reading the grid:**
- **Every cell stops early, after 2 to 40 rounds.**
  - Cells with min-data 200 at lr >= 0.05 get worse than L0s within 2 rounds; at lr 0.1 they lose 4.8 to 6.8 nats per game. With 78 classes and small hessians on rare classes, the Newton leaf values are large, so extra capacity fits rare-class noise before it fits the rating signal.
  - **No cell reaches the band on fold 1.** The largest spread in the grid is 0.42 / 0.58 (lr 0.02, 15 leaves, min-data 200, 40 rounds), and that cell is 2.5 SE below the best LL.
  - So capacity, as early stopping on inner LL allows it, cannot by itself produce a calibrated rating response under the L0s start.
- **The selected capacity is lower than L3c's.**
  - Under the L0s start the same config stops at 22 rounds; under SL-R3's L0m start it stopped at 31.
  - L3d is therefore a smaller booster than L3c, and its response is smaller on both folds:

    | arm | fold 1 | fold 2 |
    |---|---|---|
    | L3c | 0.37 / 0.49 | 0.675 / 0.529 |
    | L3d | 0.28 / 0.38 | 0.517 / 0.413 |

## 2. In-sample stratum check (fold-2 training rows): PASS

L3d vs L0s, mean xG_ref per attempt (`results/shot_attribute_r5/insample.json`):

| stratum | n | L0s vs actual | L3d vs L0s |
|---|---:|---:|---:|
| 5v5 | 287,840 | +0.07% | +0.06% |
| PP | 53,097 | -0.00% | -0.07% |
| PK | 9,170 | +0.04% | +0.19% |
| 4v4 | 4,334 | -4.43% | +0.11% |
| 3v3 | 3,752 | -4.59% | -0.41% |
| ENF / ENA | 5,721 / 2,145 | -0.07% / +0.15% | 0 (bit-identical) |

- Every state x period-type cell with n >= 2,000 also passes.
- In-sample LL per attempt: L0s -3.18257, L3d -3.16931.
- **L3ds2 is bit-identical to L3d,** so the floor is 0 (D26).

## 3. D28 guard (fold 1, L3d minus L0s): PASS

`results/shot_attribute_r5/fold1/guard.json` and `guard.csv`. The tolerances are the SL-R1 ones; EN is reported, not gated.

**L3d minus L0s:**
- xG: overall +0.10%; ES +0.15%, PP -0.04%, PK +0.18%.
- Months: every powered month is within +0.15%.
- Tiers: every gated cell is within 0.13 pp.
- Types: every type is within 0.04 pp.

**Reported read, level E as graded vs the oracle level O (fold 1 only):**

| level | arm | xG all | ES | PP | PK | ENF | high / med / low pp | ES resp |
|---|---|---:|---:|---:|---:|---:|---|---|
| E | L0s | +2.49% | +4.15% | -3.18% | +5.23% | -1.65% | +1.65 / +0.31 / -1.95 | 0.01 / -0.02 |
| E | L3d | +2.59% | +4.30% | -3.22% | +5.42% | -1.65% | +1.68 / +0.34 / -2.01 | 0.28 / 0.38 |
| O | L0s | +0.39% | +0.35% | +1.09% | -0.39% | -3.46% | -0.01 / -0.05 / +0.07 | 0.01 / -0.02 |
| O | L3d | +0.49% | +0.51% | +1.03% | -0.22% | -3.46% | +0.01 / -0.03 / +0.02 | 0.30 / 0.38 |

## 4. Fold-2 blind grade and decision

Grade report: `docs/tests/shot_attribute_sl_r5_grade_2026-10-16.md`. One grader scores every arm, and the labels stayed hashed until scoring was complete. The test season is 2024-25: 119,924 unblocked attempts in 1,398 games.

| arm | LL / att | LL / game vs L0s (SE) | xG overall | xG fails | tier / type fails | ES resp for / against (95% CI) | eligible |
|---|---:|---:|---:|---|---|---|---|
| L0s | -3.21341 | 0 | +1.86% | none | none | -0.00 / 0.02 | no (flat, D24) |
| **L3d** | -3.21187 | **+0.1316 (0.0128)** | +1.97% | **PK +3.21%** | none | **0.517 (0.38-0.81) / 0.413 (0.31-0.62)** | **no** |
| L3ds2 | identical to L3d | | | | | | (floor 0) |

**L3d detail:**
- xG by group: ES +2.62%, PP -0.49%, PK +3.21%, ENF +0.39% (reported), ENA +2.49% (reported, n 892).
- Tiers overall: +0.58 / -0.45 / -0.13 pp.
- The largest powered month is 2024-11 at +3.39% (limit 4%).
- PK and PP responsiveness are UNDERPOWERED (reported).

**Per state (reported, not gated):**

| state | xG | medium tier | note |
|---|---:|---:|---|
| 5v5 | +2.81% | | |
| 4v4 | -3.23% | -5.2 pp | UNDERPOWERED (n 1,242) |
| 3v3 | -3.04% | -9.0 pp | UNDERPOWERED (n 1,129) |

**Decision as pre-registered:**
- L3d is not eligible: it fails the ES band on both sides (the against CI upper bound is 0.62) and PK xG.
- It is not worse than L0s; it is better by 10.3 SE.
- **No arm is selected.** shot_attribute stays BUILDING.
- **D30 stop rule:** stage-4 work stops, and the PM takes the options to the user. No SL-R6 without the user.

## 5. Not done (by the spec)

- **Step 4 not run** (applies only on selection):
  - no engine lookup for the L0s strata;
  - no EN routing in `sim.py`;
  - no closed loop.

  `sim.py` was not edited.
- **No fold-1 grade** through `grade_shot_attribute.py`: the D28 guard is computed by `train_shot_attribute_v5.py guard`. The fold-1 responsiveness is in `guard.json`.

## 6. For the PM (options for the user, D30)

**Evidence for the user:**
- Across SL-R3 to SL-R5, a booster started from the stratum baseline under-responds, and tuning capacity cannot fix it.
  - Early stopping on likelihood allows only 2 to 40 rounds.
  - Across the whole pre-registered grid the fold-1 spread never exceeds 0.58.
  - L3d (0.52 / 0.41) is further from the band than L3c (0.675 / 0.529).
- PK +3.2 to 3.3% is mostly the baseline: L0s is +2.86% on every round since SL-R2.

**Ranked options, as the brief frames them:**
1. Accept L3c (the better responder) with its failures listed. These are the ES band at 0.675 / 0.529, xG +2.0007% and PK +3.31%.
2. Change the gate, with a reason.
3. Park stage 4 and build stage 5 on L0s as a labelled stub. L0s passes every bias check on fold 2 but is flat.

**Lane observation (not a proposal for an SL-R6):** the response is set by how many rounds the trees get, not by a fixed-scale term. A rating that enters with a fixed scale would be tunable by the D27 rule; the tree arm is not.

**LEARNINGS candidate L35:** *Early stopping on likelihood bounds a booster's rating response. Started from a strong stratum baseline, a 78-class booster over-fits rare classes within a few rounds, so the LL-optimal capacity leaves team ratings under-expressed (fold-1 spread at most 0.58 across 18 capacity cells; fold 2 0.52 / 0.41 for the selected cell). For the sim: when the matchup response must be calibrated, give the rating a term whose scale can be tuned for spread (D27), rather than relying on tree capacity chosen by likelihood.*

## Files

- New: `scripts/train_shot_attribute_v5.py`, `docs/models/shot_attribute/sl_r5_frozen_params.json`, `docs/models/shot_attribute/sl_r5_grid_fold1.csv` (all in 399c1c7).
- Grader: `scripts/grade_shot_attribute.py` gains `--round r5`; the decision heading now names the round. The r1 / r2 / r4 paths are otherwise unchanged.
- Reports: this file and `docs/tests/shot_attribute_sl_r5_grade_2026-10-16.md`.
- Results (gitignored): `results/shot_attribute_r5/`, containing:
  - logs: tune.log, fit2.log, insample.log, fold1.log, guard.log, pred2.log, grade_fold2.log;
  - insample.json, fold1/guard.json, grade_fold2.json;
  - the models, plus tune/ (per-cell boosters and inner per-game LL).
