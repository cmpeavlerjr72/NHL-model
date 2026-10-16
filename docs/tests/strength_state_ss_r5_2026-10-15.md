# SS-R5 (INV-29): penalty-type model with team terms. Lane P2 report, 2026-10-15

Verdict: **T2 selected offline (beats T1 by 2.9 SE; T3 does not beat T2). Closed-loop G1 with T2: regular-season cells PASS, decomposition CLEAN, but the PP-opportunity spread ratio is 1.19 (own taken-rating quintiles, inside [0.8, 1.2]) and 1.25 (opponent drawn-rating quintiles, OUTSIDE). The pre-registered gate is therefore NOT met: INV-29 stays open and the D15 team-PP block stands; the PM rules again.** The spread ratio improved from 1.54 / 1.85 (T1) to 1.19 / 1.25 (T2); about two thirds of the excess is removed.

Clock (wall, EDT): start 20:58, fold-1 replication 21:00, T1-T3 fit/grade 21:02, G1 run 21:03:44 to 21:15:44 (hazard table 338 s cached, then 4 workers x 50 seeds, 325-368 s each; below the 15-minute box-request threshold, so no AWS and no box request), decomposition 21:16. No AWS used.

## Step 1: fold-1 replication (forking-paths guard), PASSED, stop condition NOT met

Quintiles of team-games by the hazard's as-of own taken-rating (ratings_grid_v2, w=1.0, b=1800; rank cut). Coincidental share = coincidental penalty events / all penalty events of the team; PP opps conferred per penalty = opponent PP opportunities (mechanics replay `G1.real_frame`) / team penalties. Bootstrap = game blocks, 2000 reps. Full tables: `results/strength_state_r5/fold1_replication.md` (RS+PO and RS only for every group).

| group (RS+PO) | coinc share Q1 -> Q5 | Q5-Q1 (95% CI) | PP opps/penalty Q1 -> Q5 | Q5-Q1 (95% CI) |
|---|---|---|---|---|
| 2021-22 | 0.185 -> 0.208 | +0.023 (-0.001, +0.047) | 0.781 -> 0.759 | -0.022 (-0.048, +0.004) |
| 2022-23 | 0.174 -> 0.189 | +0.015 (-0.009, +0.037) | 0.799 -> 0.772 | -0.026 (-0.049, -0.002) |
| fold-1 train pooled | 0.178 -> 0.202 | +0.024 (+0.007, +0.040) | 0.796 -> 0.761 | -0.035 (-0.053, -0.017) |
| **2023-24 (fold 1 test)** | 0.142 -> 0.202 | **+0.060 (+0.036, +0.083)** | 0.823 -> 0.763 | -0.061 (-0.087, -0.035) |
| 2024-25 (R4 finding) | 0.160 -> 0.208 | +0.048 (+0.022, +0.073) | 0.813 -> 0.754 | -0.060 (-0.087, -0.032) |

Stop condition (2023-24 Q5-Q1 coincidental-share CI includes 0): **No, CI [+0.036, +0.083]. SS-R5 proceeds.** The gradient replicates in the same direction in all four seasons; in each single training season the CI touches zero (UNDERPOWERED alone); pooled training seasons exclude zero. Interpretation choice: the stop condition is read on 2023-24, RS+PO (RS only gives +0.065, CI [+0.041, +0.089]).

## Step 2: T1-T3 (`scripts/exp_strength_state_r5_types.py`, `src/nhl_sim/strength_state/models_r5.py`)

T3 prior-strength tuning on fold 1 (train 2021-22 + 2022-23, test 2023-24), LL per penalty: k=50 -0.55388, k=150 -0.55415, k=450 -0.55446. **k = 50 selected** (the lowest candidate; differences are small, 0.0006 nats). Fold-1 LL for information: T1 -0.55809, T2 -0.55474, T3 -0.55388.

Fold 2 (train through 2023-24, test 2024-25, 9,270 penalties, 1,395 games), multinomial LL per penalty:

| arm | LL | SE |
|---|---|---|
| T1 | -0.57728 | 0.00983 |
| T2 | -0.57416 | 0.00981 |
| T3 | -0.57323 | 0.00980 |

| paired difference | diff | SE | 95% CI | > 2 SE |
|---|---|---|---|---|
| T2 - T1 | +0.00312 | 0.00107 | (+0.00095, +0.00523) | yes (2.9 SE) |
| T3 - T1 | +0.00405 | 0.00118 | (+0.00171, +0.00642) | yes |
| T3 - T2 | +0.00093 | 0.00054 | (-0.00016, +0.00198) | no (1.7 SE) |

Noise floor: T1-T3 are convex multinomial logits with no random seed, so a spec-identical retrain under another seed is identical (floor exactly 0); the 2 SE bootstrap rule is the operative threshold. **Decision: T2** (ties to the simpler arm).

By segment (T2-T1): RS +0.00331 (SE 0.00108, n=8,617); PO +0.00060 (SE 0.00553, n=653, UNDERPOWERED). By strength state (T2-T1, team view): 5v5 +0.00301 (SE 0.00113, n=8,251); PP, PK, 4v4, 3v3, other all within SE (n = 452, 292, 88, 44, 143: UNDERPOWERED). The gain comes from 5v5.

Responsiveness (fold 2, own taken-rating quintile of the event, coincidental share): actual 0.163, 0.172, 0.182, 0.211, 0.208 (Q5-Q1 +0.045); T1 flat 0.1755 -> 0.1749 (-0.001); T2 0.150 -> 0.197 (+0.047); T3 0.151 -> 0.198 (+0.046). Per-team (32 teams, ~289 penalties each, UNDERPOWERED per team) correlation of predicted vs actual coincidental share: T1 0.01, T2 0.61, T3 0.77. T3's offsetting-share rating improves team-level ranking but not the LL beyond 2 SE. Coefficients: the coincidental class loads on taken_own (+0.38), taken_opp (+0.90), off_own (+0.39), off_opp (+0.26); the opponent's taken-rating is the strongest term (two penalty-prone teams offset each other).

## Step 3: closed-loop G1, T2 with hazard H3'' (200 seeds, 1,398 games; `results/ss_r5_g1_H3_T2/`, `docs/tests/gates_g1_ss_r5_g1_H3_T2_2026-10-15.md`)

Engine: new sibling module `src/nhl_sim/engine/sim_ss_r5.py` (copy of `sim.py` at HEAD c6fb0a5 with ONE change: the type table is indexed per game and team, shape (G,2,6,5,4,4)); `engine/sim.py` untouched (Lane S has uncommitted edits to it; they are NOT in the sibling). Runner `scripts/run_strength_state_g1_v5.py`, decomposition `scripts/diag_strength_state_g1_decomp_v5.py`.

G1 cells (sim / real; tolerance 0.75 min for TOI, 0.15 for PP opps):

| cell | RS | PO (UNDERPOWERED) | overall |
|---|---|---|---|
| TOI 5v5 | 50.17 / 50.39 PASS | 51.52 / 52.20 | 50.25 / 50.50 PASS |
| TOI PP total | 9.14 / 8.95 PASS | 9.68 / 10.24 | 9.17 / 9.03 PASS |
| TOI 4v4 | 0.776 / 0.728 PASS | 0.789 / 0.725 | 0.777 / 0.728 PASS |
| TOI 5v3 | 0.151 / 0.147 PASS | 0.165 / 0.127 | 0.152 / 0.146 PASS |
| PP opps / team-game mean | 2.652 / 2.564 PASS (+0.088) | 2.814 / 2.895 | 2.662 / 2.584 PASS (+0.078) |
| PP opps SD | 1.376 / 1.261 PASS | 1.411 / 1.321 | 1.379 / 1.267 PASS |

TOI 3v3, TOI EN and share of minors ended by PP goal are STUB-DEPENDENT as before. Seed stability |200 - 100| is at most 0.0033 in every overall cell (RS at most 0.0033 in the table; PO at most 0.022 TOI).

D14 decomposition of PP opps (sim - actual), verdicts: **regular season CLEAN** (total +0.088, no component beyond 0.15); overall CLEAN (+0.078); playoffs COMPENSATED (total -0.081 but hazard-level component (a) = -0.207, offset by (c) +0.126 and (d) +0.078; n = 172 team-games, UNDERPOWERED, and unchanged in kind from the T1 baseline, whose (a) is the same -0.207). PP opps per event: sim 0.796 vs actual 0.781 (RS+PO 0.7960 vs 0.7795) against T1 0.7878; the T2 sim coincidental share is 0.174 vs actual 0.187 overall (sim slightly low; the sim minor share is 0.808 vs actual 0.794).

Closed-loop spread of PP opportunities conferred (RS+PO, quintiles of team-games, Q5 minus Q1; ratio = sim / actual), both rating sets:

| quintile set | actual spread | T1 baseline sim (ratio) | T2 sim (ratio) | in [0.8, 1.2]? |
|---|---|---|---|---|
| own taken-rating | 0.412 | 0.634 (1.54) | 0.489 (**1.19**) | yes (edge) |
| opponent drawn-rating | 0.241 | 0.444 (1.85) | 0.300 (**1.25**) | **NO** |

Slope ratios (sim/actual): taken 1.15, drawn 1.30 (T1 1.48 / 1.99). Uncertainty: the actual quintile-mean SE is about 0.055 (so the actual spread SE is about 0.08); the drawn ratio of 1.25 is within roughly 1 SE of 1.0 and of 1.2, i.e. the actual spreads are too noisy on one season to separate 1.25 from the band edge. This is stated, not used to relax the gate. Quintile detail: sim penalties at Q5 taken 3.78 vs actual 3.65 and at Q1 2.96 vs 2.87; sim PP opps conferred Q1 2.44 vs 2.34 and Q5 2.93 vs 2.75 (the remaining excess is mainly a penalty-count over-response at the top quintile plus the stub/type residual, no longer the coincidental share).

**Gate outcome: arm T2 wins offline but fails the closed-loop gate on the drawn-rating spread ratio (1.25 > 1.2). INV-29 stays open; the D15 team-PP block is NOT lifted; the PM rules again.** (Spec outcome clause: "If the arm wins offline but fails the gate, INV-29 stays open and the PM rules again.")

## Interpretation choices (labelled) and PARTIAL items

- Ratings for T2/T3 are the hazard's (ratings_grid_v2, w=1.0, b=1800), own and opponent taken-rating. "Opponent taken-rating" read literally (not the opponent drawn-rating).
- Offsetting-share rating: cumulative across all earlier game dates in the data (2021-22 on, no season reset, no decay), C = coincidental penalty events charged to the team, N = all penalty events, league share (sum C + 1)/(sum N + 4); rating = logit shrunk team share - logit league share, minus the snapshot mean over teams; same-day games see the pre-day snapshot (as `tables.asof_ratings`).
- T1-T3 are all refit on `type_rows_v2` through the same code (not the SS-R1 T1 trained on v1 rows). The G1 baseline T1 numbers above come from the existing 200-seed run `ss_r3_g1_H3` (T1 from v1 rows), re-run through the v5 decomposition only.
- Spread ratio = (Q5 - Q1 of sim PP opps conferred) / (Q5 - Q1 of actual), RS+PO, quintiles over team-games by the as-of rating of that game (as the D14 responsiveness table). A regular-season-only ratio was NOT computed (PARTIAL; one-line variant of the decomp script; would not change the decision rule since the spec does not distinguish).
- The 3v3 / EN / PP-goal cells remain stub-dependent; playoffs UNDERPOWERED.
- Core use: up to 4 workers for the sim (cap 4). Hazard table cached at `results/strength_state_r5/lam_H3_fold2.npy` (gitignored).

## Reproduce
```
.venv/Scripts/python.exe scripts/exp_strength_state_r5_fold1.py
.venv/Scripts/python.exe scripts/exp_strength_state_r5_types.py
.venv/Scripts/python.exe scripts/run_strength_state_g1_v5.py --arm H3 --type-arm T2 --seeds 200 --chunk 50 --workers 4 --tag ss_r5_g1_H3_T2 --report docs/tests/gates_g1_ss_r5_g1_H3_T2_2026-10-15.md
.venv/Scripts/python.exe scripts/diag_strength_state_g1_decomp_v5.py --arm H3 --tag ss_r5_g1_H3_T2
.venv/Scripts/python.exe scripts/diag_strength_state_g1_decomp_v5.py --arm H3 --tag ss_r3_g1_H3   # T1 baseline spread
```
