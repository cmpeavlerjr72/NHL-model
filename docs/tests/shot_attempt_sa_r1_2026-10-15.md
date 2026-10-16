# SA-R1 shot-attempt bake-off (INV-30, Lane S, 2026-10-15)

Spec: `docs/models/shot_attempt/experiments.md` SA-R1 (committed 9edbe9d before any run). Brief: `docs/briefs/lane_S_shot_attempt_2026-10-15.md`. Full blind grade: `docs/tests/shot_attempt_sa_r1_grade_2026-10-15.md`. Frozen fold-1 choices: `docs/models/shot_attempt/sa_r1_frozen_params.json`.

**Outcome: the decision rule selects NO arm.** Every arm fails the fold-2 bias checks (overall level -4.99% to -5.07% against +/-2%), so no arm is eligible and the closed-loop G2 was not run (step 3 blocked by the rule). The cause is a defect in the shared league-level input (the SS-R3 method), not in any arm. It is diagnosed below with fold-1-only evidence.

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| read-in | 20:39 | 20:44 |
| tables: rows (4 seasons) | 20:44:59 | 20:45:24 |
| tables: level/profile, ratings grid | 20:45:35 | 20:46:45 |
| tune (36-cell A1 grid, arena table, LightGBM grid, latent) | 20:49:43 | 20:50:38 |
| fold-2 fits | 20:50:47 | 20:51:09 |
| fold-1 fits | 20:51:09 | 20:51:22 |
| blind grade | 20:52:28 | 20:52:40 |
| level-anchor diagnostic (fold 1) | 20:53 | 20:55 |

| step-3 code + parity test + smoke (4 seeds) | 20:58 | 21:06 |

No step came near the 15-minute box-request threshold; no AWS request was filed.

## 1. Tables (`data/processed/shot_attempt/*_v1*`)

- Attempt rows: 216,792 / 217,948 / 216,788 / 213,898 rows (two team views per interval) for 2021-22 .. 2024-25, with 159,791 / 163,714 / 170,602 / 167,020 attempts. Exposure is 1,416-1,421 game-hours per season.
- Exclusions (tallied, `exclusions_v1.json`): penalty-shot attempts 36 / 57 / 47 / 30, shootout attempts 747 / 645 / 607 / 508. The L20 delayed-penalty convention changed the goalie state of 5,491 / 5,765 / 5,804 / 4,588 seconds.
- Ratings grid (12 points x 3 groups x for/against), level/profile per fold (k in {15, 50, 150}), arena factor at the frozen grid point. `created_at < puck_drop` is asserted on every ratings, level and arena row.
- Tests: `tests/test_shot_attempt_tables.py` (4 pass). It covers an unmapped attempt type raising, the L20 delayed-penalty state (an attempt inside a signal window is 5v5, not EN-for; a trailing pull without a signal stays EN), and the penalty-shot / shootout exclusions.
- Feature manifest: `docs/models/shot_attempt/features.md`.

## 2. Fold-1 tuning (fold 1 only)

The (k, w, b) grid was tuned on A1, the simplest rating arm (labelled choice). The best cell is **k = 15, w = 0.85, b = 600** team-minutes. k and b are both grid corners.

L24 guard: the fold-1 offline quintile-spread ratio for every cell (5v5; own ES-for / opponent ES-against quintiles):

| k | w | b | fold-1 A1 LL/game | spread own | spread opp | beta own_r | beta opp_r | pred/actual |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | 0.5 | 600 | -180.1588 | 1.152 | 1.124 | 1.148 | 1.135 | 0.980 |
| 15 | 0.5 | 1800 | -180.2057 | 1.256 | 1.230 | 1.489 | 1.522 | 0.980 |
| 15 | 0.5 | 5400 | -180.2679 | 1.346 | 1.343 | 2.331 | 2.462 | 0.981 |
| 15 | 0.7 | 600 | -180.1491 | 1.186 | 1.137 | | | |
| 15 | 0.7 | 1800 | -180.2063 | 1.335 | 1.285 | | | |
| 15 | 0.7 | 5400 | -180.2971 | 1.451 | 1.430 | | | |
| **15** | **0.85** | **600** | **-180.1475** | **1.208** | **1.161** | | | |
| 15 | 0.85 | 1800 | -180.2150 | 1.362 | 1.327 | | | |
| 15 | 0.85 | 5400 | -180.3319 | 1.546 | 1.519 | | | |
| 15 | 1.0 | 600 | -180.1508 | 1.231 | 1.172 | | | |
| 15 | 1.0 | 1800 | -180.2298 | 1.413 | 1.362 | | | |
| 15 | 1.0 | 5400 | -180.3760 | 1.610 | 1.596 | | | |

k = 50 and k = 150 rows repeat the same pattern, about 0.01-0.04 nats/game lower. The full 36 rows, including the betas and pred/actual, are in `sa_r1_frozen_params.json`. Every cell over-responds on fold 1 (ratio 1.14-1.61). It is steeper the stronger the shrinkage, because the fitted coefficient grows (1.1 -> 2.5) to re-expand shrunk ratings, and the expansion does not hold up out of season.

- A3 LightGBM: num_leaves 7, min_data_in_leaf 800, 765 rounds (inner early stopping). The fold-1 grid ran -179.525 to -179.630.
- A4 latent variance: v = 0.00115 (game multiplier SD 3.4%). The fold-1-train marginal gain is +0.004 nats/game.

## 3. Bake-off, fold 2 (blind; labels revealed after the table was final)

1,398 games, 213,898 rows, 167,020 attempts. The SE is a game-block bootstrap (1,000) of paired per-game differences.

| arm (hash) | LL/game | vs A0 | SE | pred / actual |
|---|---:|---:|---:|---:|
| A0 (4e21b43e) | -178.7431 | 0 | | 0.9501 |
| A1 (fc5ae556) | -178.3415 | +0.4016 | 0.0439 | 0.9493 |
| A2 (47c67d9a) | -177.7785 | +0.9646 | 0.0559 | 0.9500 |
| A5 (bc206221) | -177.7793 | +0.9638 | 0.0559 | 0.9494 |
| A4 (50a723d4) | -177.7544 | +0.9887 | 0.0562 | 0.9500 |
| A3 (c9f99511) | -177.6808 | +1.0623 | 0.0582 | 0.9494 |

Hashes use the salt `SA-R1-2026-10-15`; A3 seed 2 is 12cedb21. The seed floor (|A3 - A3 seed 2|) is 0.00132 nats/game.

Key pairs (more complex minus simpler):

| comparison | diff | SE | beats (> 2 SE and > seed floor) |
|---|---:|---:|---|
| A1 vs A0 | +0.402 | 0.044 | yes |
| A2 vs A1 | +0.563 | 0.034 | yes |
| A5 vs A2 | -0.001 | 0.002 | **no** (the arena factor adds nothing) |
| A4 vs A2 | +0.024 | 0.004 | yes |
| A4 vs A5 | +0.025 | 0.004 | yes |
| A3 vs A2 | +0.098 | 0.021 | yes |
| A3 vs A4 | +0.074 | 0.022 | yes (A3 independent Poisson vs A4's exact latent marginal) |

## 4. Bias checks and responsiveness

Fold 2 is gating; fold 1 is a diagnostic.

| arm | fold-2 bias | fold-2 failing cells | resp own (95% CI) | resp opp (95% CI) | resp band | eligible |
|---|---|---|---|---|---|---|
| A0 | FAIL | level -4.99%; Oct, Jan, Feb, Apr; 5v5 -5.48%; PK +3.20%; score -1 -10.5%, 0 -5.5%; home -6.3%, away -3.7% | 0.030 (0.016, 0.044) | -0.037 (-0.056, -0.022) | FAIL | no |
| A1 | FAIL | level -5.07%; Oct, Jan-Apr; 5v5; PK +3.27%; score -1, 0; home, away | 1.040 (0.92, 1.19) | 1.133 (0.99, 1.32) | pass | no |
| A2 | FAIL | level -5.00%; Oct, Jan-Apr; 5v5 -5.47%; PK +3.40%; score -1 -5.5%, 0 -4.6%; home, away | 1.072 (0.95, 1.23) | 1.155 (1.01, 1.34) | pass | no |
| A5 | FAIL | as A2 (level -5.06%) | 1.085 (0.96, 1.25) | 1.142 (1.00, 1.33) | pass | no |
| A4 | FAIL | as A2 (same mean) | 1.072 | 1.155 | pass | no |
| A3 | FAIL | level -5.06%; Oct, Jan-Apr; 5v5 -5.52%; score -1, 0, +1; home -4.9%, away -5.2% (PP -2.5%, PK +2.6% pass) | 1.091 (0.97, 1.26) | 1.086 (0.95, 1.26) | pass | no |

- Fold-2 months Nov and Dec pass (about -4.2%). EN-for and EN-against (reported, not gating) run -9% to -12%. The score buckets beyond +/-2 are UNDERPOWERED (< 300 team-hours).
- Fold 1 (diagnostic): the level runs -1.90% to -2.12% in every arm. PK is +5.9% (A3) to +8.2% (A2) and PP is -3.4% to -4.5% in every arm. Offline responsiveness on fold 1 is 1.09-1.23.
- Multi-level (A3, fold 2): the per-team correlation of predicted and actual attempts per team-game is 0.92. All 32 teams are UNDERPOWERED (n = 82-105 team-games). In the team-game calibration deciles, decile 1 is 44.8 predicted vs 49.8 actual and decile 10 is 71.0 vs 73.3.

**Decision rule, applied literally:** eligible arms are none, so the **selected arm is NONE** and the next simpler eligible arm is none. Step 3 (engine wiring for the selected arm, the parity test, and G2 with the decomposition and closed-loop responsiveness) is not run, by rule.

Had the level passed, the literal ordering would read as follows. A5 does not beat A2. A4 beats A0-A2 and A5. A3 beats every simpler arm, including A4 (+0.074, SE 0.022). This is not a selection: no arm is eligible.

## 4b. Step 3 status: BLOCKED by the rule; engine code built and tested, G2 not run

The closed loop cannot be run as specified, because there is no selected arm. The code it needs was built so that a future selected arm can go straight to G2. Nothing here is a gate result.

- **Engine variant** `src/nhl_sim/engine/sim.py`:
  - It is default-off: it is active only when the tables hold `att_lam`.
  - Each team draws an attempt count per second from `att_lam[g, team, minute, st, sc7]`. The draw is a Poisson inverse CDF over k in {0, 1, 2}; P(k >= 3) is about 1e-6 per second and is folded into k = 2.
  - Each attempt is a goal with probability `p_goal[st]`. This is the LABELLED goal stub: league goals per attempt by state in 2023-24 (5v5 .0424, PP .0703, PK .0657, 4v4 .0689, 3v3 .1196). It replaces the stub goal table.
  - RNG families are `attempt` and `attempt_goal`.
  - It records attempts by team-view state and score bucket, and pre-event exposure by (state, bucket).
  - Tests: `tests/engine/test_sim_attempts.py` (4 pass: rate, no stub goals, goals only from attempts, paired streams, default-off path unchanged). The existing engine tests still pass (105/105 in the full suite).
- **Lookup** `src/nhl_sim/shot_attempt/lookup.py` (`attempt_table`, `goal_stub`).
- **Parity test** `tests/test_shot_attempt_lookup.py`: 220 fold-2 games and 33,132 rows per arm. The sample error is at most 1.8e-9 and the maximum per-game error 3.3e-8 for A0, A1, A2, A5 and A3, against the 0.5% limit. PASS.
- **G2 runner** `scripts/run_shot_attempt_g2.py`:
  - It runs the sim in seed blocks, as parallel processes, then grades.
  - Grading covers G2 RS / PO / overall, 100 vs 200 seeds, the D14-style decomposition (hazard level, unreachable EN, state visits, score-state visits, remainder; and per 60 by state) and the closed-loop responsiveness with a bootstrap CI.
  - G2 metrics live in `src/nhl_sim/eval/g2.py`. The `eval_gates.py` G2 hook and the `build_gate_reference.py` G2 targets go to the sibling `data/reference/gate_targets_g2_20242025.parquet`; the shared targets file is not rewritten.
  - Measured: 6 s per seed over 1,398 games, so 200 seeds is about 20 min single-process, or about 6 min as 4 parallel blocks of 50.
- **Smoke run (plumbing only)**: 4 seeds, arm A2, which is NOT selected and NOT a gate (`results/smoke_sa_r1_A2/`). It ran end to end.
  - 5v5 per 60 was -5.5% vs actual, matching the offline level defect.
  - The decomposition puts -2.9 attempts/team-game on the hazard level and -1.7 on unreachable EN attempts.
  - Two hints for later: team-game SD 9.6 sim vs 11.6 actual, and home-away attempt correlation -0.23 sim vs -0.41 actual. Both are 4-seed values.

## 5. Diagnosis: the shared league level is mis-anchored (fold-1 evidence only)

The SS-R3 level is log(season-to-date rate / previous season's final rate), and it is a fixed offset pooled over several training seasons. Its reference therefore changes every season:

- The cell effects learn a blend of past season rates.
- A test season inherits the product of the earlier season-to-season ratios.
- The de-seasonalised attempt rate rose 56.36 -> 57.65 -> 60.24 per team-hour from 2021-22 to 2023-24.
- The predicted shortfall is about r21/r22 = -2.2% on fold 1 (observed -2.0%), and about -5.6% on fold 2 (observed -5.0%).

`scripts/diag_shot_attempt_level_anchor.py` (fold 1 only, A0 and A2, frozen params) tests a fix that adds the completed-season constant log(r_prev / r_first), so that the level is a log ratio vs ONE fixed reference:

| level | A0 fold-1 pred/actual - 1 | A2 | A2 PK | A2 PP |
|---|---:|---:|---:|---:|
| SS-R3 (SA-R1 literal) | -2.03% | -1.90% | +8.2% | -3.4% |
| anchored (diagnostic) | +0.22% | +0.35% | +10.7% | -1.2% |

The anchoring removes the overall bias on fold 1. A second, independent drift remains: PK attempts (shorthanded attempts) +8 to +11% on fold 1. One all-state level cannot carry a strength-specific change. The same mechanism probably contributes to the penalty-level biases of SS-R2 and SS-R3, whose test season inherits the same chained ratios. That is a hypothesis for the PM; it is not tested here.

Fold 2 was not re-run under the anchored level (doing so would be a fold-2-informed respec).

## 6. Interpretation choices (labelled)

1. Penalty shots are identified by pbp situation code 0101 / 1010 outside the shootout (30 in 2024-25 against 32 PS penalties).
2. An attempt at second t uses the state of second t-1 (Lane H's convention).
3. Both goalies pulled maps to EN-for for both teams. It never occurs.
4. Rating groups: EN rows use the ES ratings, and EN time is excluded from the rating exposure. The opponent rating is the opponent's attempts-against in its own state (own PP -> opp PK). One coefficient each for own_r and opp_r across groups (the spec's two features).
5. "rest/back-to-back" is the b2b flag of each team (Lane H's `team_game_v2`).
6. k, w and b were tuned jointly on A1 by fold-1 LL.
7. A4 uses the A2 Poisson coefficients, with v fitted on fold-1 train by the exact marginal and then carried to fold 2.
8. A3's "continuous game clock" is the game minute (t0 // 60), for engine-lookup parity and Lane H's leak note.
9. Arena: home team id, or the venue for neutral sites, with c = 1,200 pseudo-attempts (not tuned).
10. The score-bucket power rule "n >= 300 team-games of exposure" is read as >= 300 team-hours.
11. Month = the calendar month of the game date (playoffs included).
12. The seed floor is applied to every pairwise comparison (the spec's wording), not only to A3's.

## 7. Recommended next stage (for the PM)

SA-R2, pre-registered, with one shared-input change: an anchored league level (a log ratio vs a fixed reference season, completed seasons only). Optionally, a candidate per-strength-group level (ES / PP / PK) for the PK/PP drift, raced as arms, not adopted. Re-tune on fold 1, then grade fold 2 once. The arms, grader and tables are reusable as they stand (`train_shot_attempt_v1.py` would get a v2 sibling with the level choice). The SS-R2 / SS-R3 penalty level may carry the same anchoring defect; it is worth one fold-1 check on stage 1.
