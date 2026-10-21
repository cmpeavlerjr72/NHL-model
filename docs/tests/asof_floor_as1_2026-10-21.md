# AS-1: prior-precision floor for the as-of response scale (INV-62; Lane B5, 2026-10-21)

- Spec (binding): `docs/models/asof_scale/experiments.md` AS-1 (D42, L38). Brief: `docs/briefs/lane_B5_block_r5_2026-10-21.md`.
- Code: the floor is a parameter of both existing modules, `src/nhl_sim/goal/scale.py` and `src/nhl_sim/shot_attribute/scale.py` (`floor=(f, I_ref)`, `info_ref`; `floor=None` is the old construction). Runner `scripts/exp_asof_floor_as1.py` (`run`, `write`). Tests `tests/test_asof_floor.py` (6 pass; with the two existing as-of test files, 15 pass).
- Outputs: `results/asof_floor_as1/{as1.json, insample_restated.json, run.log, write.log}` (gitignored). Floored siblings at the selected f: `data/processed/goal/goalie_scale_v2_f{1,2}.parquet`, `data/processed/shot_attribute/sq_scale_v2_f{1,2}.parquet`. The v1 incumbents are untouched.

**Outcome: f = 0.50 is selected.** It is the only grid value that passes on every instance and fold. The goalie burn-in decides it: 0.05 to 0.25 leave the goalie burn-in max at 4x to 10x its judged max. On every instance, fold and f, the judged-season snapshots are bit-identical to the unfloored ones. The floor never binds after 2022-01-24, and the floored and unfloored paths coalesce exactly by 2022-02-07. **No fold-2 row was touched:** fold-2 computations use the 2021-22 to 2023-24 rows only.

## Clock (local, -04:00)

| step | start | end |
|---|---|---|
| lane start (brief, rules, specs, templates read) | 13:14:35 | |
| `run`: f = None identity over every grid cell, I_ref, f grid (both instances and folds) | 13:18:07 | 13:22:25 |
| `write`: v2 siblings at f = 0.5 (every grid cell) + the SL-R7 burn-in in-sample re-statement | 13:22:58 | 13:25:32 |
| tests | 13:26 | 13:27 |

## Construction as implemented

- **Floor.** For a window information Ibar_t at the current Newton iterate, the prior precision is P x Ibar_t when lambda_min(Ibar_t) >= f x lambda_min(I_ref), and P x (Ibar_t + f x I_ref) otherwise. The condition is re-read at every iterate, as Ibar_t is in the template. It enters both the stationarity condition and the Newton matrix.
  - A window with zero information (all-zero ratings) still carries s_prev, because its solution is s_prev either way.
  - Each snapshot row records `floor_binds` at the converged pair; this column exists only when a floor is set.
- **I_ref.** This is Ibar at s = 0 over every in-scope row of the fold's 2021-22 season, unweighted. The ratings are in their standard units (the fold's 2021-22 SD), and the instance's fixed offset is included. For the goalie it is a scalar; for stage 4 it is a 2x2 matrix.
- **Rows.**
  - Fold 1: the incumbent's rows, 2021-22 to 2023-24.
  - Fold 2: the training seasons only. The estimator is causal, so these dates are the same objects as the incumbent's training-date rows; f = None reproduces them bit-for-bit.
  - The fold-2 v2 siblings stop at the end of 2023-24 (`rows_scope` column). Extending them to 2024-25 is one command once the PM rules (`write` with the 2024-25 filter lifted).

## I_ref and the f = None identity

- goalie_f1: I_ref [[0.0801]], lambda_min 0.08010, SD [0.02708]
- goalie_f2: I_ref [[0.08013]], lambda_min 0.08013, SD [0.02713]
- stage4_f1: I_ref [[0.82322, -0.01729], [-0.01729, 0.82934]], lambda_min 0.80872, SD [0.02223, 0.01961]
- stage4_f2: I_ref [[0.83704, -0.01709], [-0.01709, 0.84349]], lambda_min 0.82288, SD [0.02242, 0.01945]

- goalie_f1: f = None bit-identical on 6 / 6 cells (686 dates)
- goalie_f2: f = None bit-identical on 6 / 6 cells (686 dates)
- stage4_f1: f = None bit-identical on 8 / 8 cells (686 dates)
- stage4_f2: f = None bit-identical on 8 / 8 cells (686 dates)

The f = None runs are compared with `goalie_scale_v1_f{fold}` / `sq_scale_v1_f{fold}` on s, the dates and n_eff, using `np.array_equal` on every date computed (every cell of both grids). The tests also compare f = None with the pre-AS-1 modules (`git show 16f877f`) on synthetic data: series and exact paths, `n_exact`, and the frame columns.

## Selection table (incumbent cells: goalie H90 P2000, stage-4 H45 P10000; raw = s / SD; stage-4 shows for / against)

Judged seasons: fold 1 2022-23; fold 2 2022-23 and 2023-24. "Last date differing" is the last date where the floored and unfloored pairs differ at all; it is always in the 2021-22 burn-in.

| instance   |   fold |    f | burn-in max raw, unfloored   | burn-in max raw   | judged max raw   | burn <= 3x judged   | judged bit-identical   | fold-1 2023-24 bit-identical   | dates floor binds (judged)   | last bind   | last date differing   |
|:-----------|-------:|-----:|:-----------------------------|:------------------|:-----------------|:--------------------|:-----------------------|:-------------------------------|:-----------------------------|:------------|:----------------------|
| goalie     |      1 | 0.05 | 109.36                       | 26.27             | 2.71             | NO                  | yes                    | yes                            | 13 (0)                       | 2021-10-26  | 2021-11-15            |
| goalie     |      1 | 0.1  | 109.36                       | 19.05             | 2.71             | NO                  | yes                    | yes                            | 29 (0)                       | 2021-11-11  | 2021-11-27            |
| goalie     |      1 | 0.25 | 109.36                       | 11.35             | 2.71             | NO                  | yes                    | yes                            | 54 (0)                       | 2021-12-07  | 2021-12-21            |
| goalie     |      1 | 0.5  | 109.36                       | 6.90              | 2.71             | yes                 | yes                    | yes                            | 94 (0)                       | 2022-01-23  | 2022-02-07            |
| goalie     |      2 | 0.05 | 112.59                       | 25.73             | 2.71             | NO                  | yes                    | n/a                            | 14 (0)                       | 2021-10-27  | 2021-11-16            |
| goalie     |      2 | 0.1  | 112.59                       | 18.78             | 2.71             | NO                  | yes                    | n/a                            | 29 (0)                       | 2021-11-11  | 2021-11-28            |
| goalie     |      2 | 0.25 | 112.59                       | 11.21             | 2.71             | NO                  | yes                    | n/a                            | 54 (0)                       | 2021-12-07  | 2021-12-21            |
| goalie     |      2 | 0.5  | 112.59                       | 6.81              | 2.71             | yes                 | yes                    | n/a                            | 95 (0)                       | 2022-01-24  | 2022-02-07            |
| stage4     |      1 | 0.05 | 527.98 / 677.94              | 2.89 / 2.96       | 2.37 / 1.93      | yes                 | yes                    | yes                            | 8 (0)                        | 2021-10-21  | 2021-12-09            |
| stage4     |      1 | 0.1  | 527.98 / 677.94              | 2.89 / 2.55       | 2.37 / 1.93      | yes                 | yes                    | yes                            | 12 (0)                       | 2021-10-25  | 2021-12-09            |
| stage4     |      1 | 0.25 | 527.98 / 677.94              | 2.86 / 1.99       | 2.37 / 1.93      | yes                 | yes                    | yes                            | 28 (0)                       | 2021-11-10  | 2021-12-18            |
| stage4     |      1 | 0.5  | 527.98 / 677.94              | 2.56 / 1.99       | 2.37 / 1.93      | yes                 | yes                    | yes                            | 55 (0)                       | 2021-12-08  | 2022-01-12            |
| stage4     |      2 | 0.05 | 514.83 / 684.23              | 2.83 / 2.80       | 2.37 / 1.90      | yes                 | yes                    | n/a                            | 8 (0)                        | 2021-10-21  | 2021-12-10            |
| stage4     |      2 | 0.1  | 514.83 / 684.23              | 2.83 / 2.38       | 2.37 / 1.90      | yes                 | yes                    | n/a                            | 12 (0)                       | 2021-10-25  | 2021-12-10            |
| stage4     |      2 | 0.25 | 514.83 / 684.23              | 2.77 / 1.95       | 2.37 / 1.90      | yes                 | yes                    | n/a                            | 29 (0)                       | 2021-11-11  | 2021-12-17            |
| stage4     |      2 | 0.5  | 514.83 / 684.23              | 2.64 / 1.95       | 2.37 / 1.90      | yes                 | yes                    | n/a                            | 56 (0)                       | 2021-12-09  | 2022-01-12            |

- **Selected f = 0.50**: the smallest f with burn-in max <= 3x the judged max on every instance and fold (goalie 6.90 <= 8.13 and 6.81 <= 8.14; stage 4 2.56 / 1.99 and 2.64 / 1.95), with judged snapshots bit-identical.
- The goalie spike, which G-R3 never listed, was 109-113 raw against a judged max of 2.7. It is the same defect as stage 4's 515-684.
- At f = 0.5 the floor binds on the first 94-95 goalie dates (to 2022-01-24) and the first 55-56 stage-4 dates (to 2021-12-09). It binds on no judged date.

## Leakage tests on the floored construction (`tests/test_asof_floor.py`, f = 0.5)

| test | goalie | stage 4 |
|---|---|---|
| f = None equals the pre-AS-1 module bit-for-bit | pass | pass (series and exact) |
| flip every outcome and rating on or after a date: s on and before it bit-identical, changed after | pass | pass (series and exact) |
| first date = prior (0), created_at < first drop | pass | pass |
| within-day shuffle, |diff| < 1e-10 | pass | pass |
| floor binds while the ratings have no spread, not once they do; start-up spike damped | pass | pass; series = exact to 1e-9 under the floor |

## SL-R7 burn-in in-sample check re-stated under the floored stage-4 snapshot (reported, gates nothing)

This uses fold-2 training rows, L1x-as at H45 P10000 vs L0s, and xG_ref per attempt. v1 is the incumbent snapshot; v2 is floored at f = 0.5.

| scope                 | stratum   |      n | v1 (SL-R7 incumbent)   | v2 (floored)   |
|:----------------------|:----------|-------:|:-----------------------|:---------------|
| all training rows     | 5v5       | 287840 | +0.18%                 | +0.02%         |
| all training rows     | PP        |  53097 | +0.06%                 | +0.08%         |
| all training rows     | PK        |   9170 | +0.05%                 | +0.07%         |
| all training rows     | 4v4       |   4334 | +0.62%                 | +0.09%         |
| all training rows     | 3v3       |   3752 | -0.30%                 | -0.02%         |
| all training rows     | 4v4 reg   |   4137 | +0.61%                 | +0.07%         |
| all training rows     | 3v3 OT    |   3749 | -0.30%                 | -0.02%         |
| 2021-22 through 10-25 | 5v5       |   5843 | +7.66%                 | +0.02%         |
| 2021-22 through 10-25 | PP        |   1236 | -1.04%                 | +0.05%         |
| 2021-22 through 10-25 | PK        |    210 | -0.99%                 | +0.13%         |
| 2021-22 through 10-25 | 4v4       |    116 | +20.29%                | +0.14%         |
| 2021-22 through 10-25 | 3v3       |    105 | -10.31%                | -0.02%         |
| 2021-22 through 10-25 | 4v4 reg   |    111 | +20.66%                | +0.13%         |
| 2021-22 through 10-25 | 3v3 OT    |    105 | -10.31%                | -0.02%         |
| 2021-22 after 10-25   | 5v5       |  90351 | +0.03%                 | +0.03%         |
| 2021-22 after 10-25   | PP        |  15668 | +0.10%                 | +0.10%         |
| 2021-22 after 10-25   | PK        |   2887 | +0.03%                 | +0.03%         |
| 2021-22 after 10-25   | 4v4       |   1401 | +0.10%                 | +0.10%         |
| 2021-22 after 10-25   | 3v3       |   1239 | +0.12%                 | +0.10%         |
| 2021-22 after 10-25   | 4v4 reg   |   1359 | +0.07%                 | +0.07%         |
| 2021-22 after 10-25   | 3v3 OT    |   1238 | +0.12%                 | +0.10%         |
| judged 2022-23 onward | 5v5       | 191646 | +0.02%                 | +0.02%         |
| judged 2022-23 onward | PP        |  36193 | +0.08%                 | +0.08%         |
| judged 2022-23 onward | PK        |   6073 | +0.09%                 | +0.09%         |
| judged 2022-23 onward | 4v4       |   2817 | +0.08%                 | +0.08%         |
| judged 2022-23 onward | 3v3       |   2408 | -0.09%                 | -0.09%         |
| judged 2022-23 onward | 4v4 reg   |   2667 | +0.06%                 | +0.06%         |
| judged 2022-23 onward | 3v3 OT    |   2406 | -0.09%                 | -0.09%         |


- **The spike is gone.** The 2021-10-12 to 10-25 4v4 cell goes from +20.3% to +0.14% (n 116), and 5v5 from +7.7% to +0.02%. On all training rows, 4v4 goes from +0.62% (the D42 stop) to +0.09%, so every gated stratum (n >= 2,000) passes the inherited +/-0.5% check on all rows.
- On the judged seasons the predictions are bit-identical (v1 = v2).
- LL per attempt on the fold-2 training rows: L0s -3.18212, v1 -3.19179, v2 -3.17938.

## Not done / for the PM

- The incumbents are not replaced; this needs a PM ruling. Because the judged-season snapshots are bit-identical, replacing v1 with v2 changes nothing served or graded, but the fold-2 siblings would first need their 2024-25 dates.
- SB-R5 uses f = 0.5 (step 2 onward).
