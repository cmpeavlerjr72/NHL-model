# SL-R1: shot location x type (cascade stage 4), Lane A, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R1 (b024504). Brief: `docs/briefs/lane_A_shot_attribute_r1_2026-10-16.md`.
- Step-0 script: `scripts/diag_shot_attribute_step0.py` (training seasons 2021-22..2023-24 only; full tables in `results/shot_attribute_r1/step0_tables.md`, gitignored).
- Blind grade (every table, both folds): `docs/tests/shot_attribute_sl_r1_grade_2026-10-16.md`. Frozen params: `docs/models/shot_attribute/sl_r1_frozen_params.json`. Results: `results/shot_attribute_r1/` (gitignored).

**Outcome: NO arm is eligible on fold 2, so step 5 (closed-loop G3 and the G2 re-check) was skipped, as the brief requires. The PM rules.** Every arm, L0 included, over-predicts xG_ref per unblocked attempt on 2024-25 by +3.85% to +3.91% (limit 2%) and the high-danger share by +1.7 pp (limit 1.5). The cause is a drift in the recorded location mix that no arm can extrapolate (section 6). L1 and L2 also over-respond to the shot-quality ratings on fold 2 (1.64 / 1.60) and are worse than L0 on likelihood. L3 passes responsiveness and ties L0 on likelihood. Step 0 ruled blocks rule **(b)** (Fenwick target).

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start | 10:11:21 | |
| step 0 audit | 10:14:40 | 10:14:48 |
| step 0 commit (92657bc), before any fit | 10:15 | |
| tables: attempt rows (4 seasons) | 10:18:16 | 10:18:41 |
| tables: xG_ref, ratings grid (both folds) | 10:18:46 | 10:20:27 |
| tables: arena factor | 10:20:30 | 10:20:44 |
| tune: ratings grid (12 L1 fits, 4 processes) | 10:24:12 | 10:33:54 |
| engine flag, parity fixture, tests (while the grid ran) | about 10:26 | 10:30 |
| first tune run stopped by me (own PIDs 4540 / 8156) to apply the L24-guard selection (section 2) | 10:34:10 | |
| tune: LightGBM grid (fold-1 inner split) | 10:34:38 | 10:35:21 |
| fold 2 fits (L0-L3, L3s2) and fold 1 fits, in parallel | 10:35:32 | 10:43:22 |
| blind grade fold 2 / fold 1 | 10:43:34 | 10:43:56 |
| drift diagnostic | 10:44 | 10:44 |
| full test suite (139 passed, 1 xfailed) | 10:44:39 | 10:45:56 |

No compute step came near 15 minutes, so no box request was filed. Step 5 did not run.

## Step 0: data audit (committed before any arm is fitted)

### 0.1 Blocked-shot coordinates: block point, not shot origin

Distance from the goal-line centre (89, 0) in the shooting team's frame, training seasons, penalty shots and shootout excluded:

| kind | n | mean ft | p25 | median | p75 | share < 20 ft | share > 45 ft |
|---|---:|---:|---:|---:|---:|---:|---:|
| BLOCK | 128,048 | 25.9 | 15.2 | 23.0 | 34.0 | 0.406 | 0.093 |
| MISS | 105,235 | 34.8 | 18.0 | 32.5 | 49.2 | 0.281 | 0.306 |
| SOG (incl. goals) | 260,824 | 35.5 | 16.1 | 31.9 | 48.0 | 0.308 | 0.289 |

By shooter position (player_box):

| shooter | BLOCK median | MISS median | SOG median | BLOCK share > 45 ft | MISS share > 45 ft |
|---|---:|---:|---:|---:|---:|
| defencemen | 26.0 | 53.1 | 51.2 | 0.153 | 0.693 |
| forwards | 21.3 | 25.5 | 25.5 | 0.049 | 0.143 |

- Defencemen's unblocked attempts come from the point (median 51-53 ft, 64-69% beyond 45 ft). Their blocked attempts sit at a median of 26 ft, only 15% beyond 45 ft. A shot's origin does not depend on whether it is later blocked by 25 ft. So the block coordinate is the **block point** (where the blocker stood), not the shot origin. The same split holds in every strength state (5v5 BLOCK median 23.3 vs MISS 33.0 / SOG 32.6; PP 21.0 vs 30.4 / 29.4) and every season.
- Blocks by a teammate ("teammate-blocked", 3,620) sit closest of all (median 12.6 ft for forward blockers), which also fits block-point recording.
- The blocker-vs-shooter recorded position check: **NOT AVAILABLE**. Shift charts carry ids and times, no coordinates, and the pbp records one coordinate pair per block.
- **shotType on blocks: recorded on 0.00% of 128,048 blocks** (every season). On SHOT and MISS it is 100%; on GOAL 99.76-99.97%.

### 0.2 Shot-type vocabulary by season (unblocked attempts, % of attempts)

| label | 2021-22 | 2022-23 | 2023-24 | max shift pp | flag |
|---|---:|---:|---:|---:|---|
| wrist | 55.98 | 52.96 | 54.52 | 3.02 | DRIFT (> 2 pp) |
| snap | 12.78 | 15.37 | 14.11 | 2.59 | DRIFT (> 2 pp) |
| slap | 13.52 | 12.11 | 11.75 | 1.41 | |
| backhand | 7.40 | 7.46 | 7.15 | 0.32 | |
| tip-in | 6.92 | 8.52 | 8.81 | 1.60 | |
| deflected | 2.58 | 1.99 | 2.02 | 0.58 | |
| wrap-around | 0.83 | 0.86 | 0.81 | 0.05 | |
| poke | 0 | 0.38 | 0.37 | 0.38 | DRIFT (appears 2022-23) |
| bat | 0 | 0.26 | 0.38 | 0.26 | DRIFT (appears 2022-23) |
| between-legs | 0 | 0.06 | 0.07 | 0.06 | DRIFT (appears 2022-23) |
| cradle | 0 | 0.006 | 0.007 | 0.006 | DRIFT (appears 2022-23) |
| (missing) | 0.002 | 0.018 | 0.015 | 0.02 | |

After the pre-registered six-class collapse (missing type goes to "other", a labelled choice):

| class | 2021-22 | 2022-23 | 2023-24 | max shift pp |
|---|---:|---:|---:|---:|
| wrist + snap | 68.76 | 68.33 | 68.62 | 0.42 |
| slap | 13.52 | 12.11 | 11.75 | 1.41 |
| backhand | 7.40 | 7.46 | 7.15 | 0.32 |
| tip-in + deflected | 9.49 | 10.51 | 10.83 | 1.02 |
| wrap-around | 0.83 | 0.86 | 0.81 | 0.05 |
| other | 0.002 | 0.72 | 0.84 | 0.72 |

- The wrist vs snap drift (3.0 / 2.6 pp) is absorbed by the collapse, as the spec anticipated. Tip-in vs deflected (1.6 / 0.6 pp, opposite signs) is absorbed too.
- **Reported, not absorbed:** four labels (poke, bat, between-legs, cradle) appear from 2022-23, so "other" moves from 0.002% to 0.72-0.84%. That is a recording-vocabulary change of 0.7 pp in the smallest class, below the 1.5 pp type-share line. The collapse is NOT changed after the audit.
- Slap falls 1.8 pp over the three seasons (13.5 to 11.75). It is under the 2 pp flag but trends (a pooled-season frequency would sit above the last season; L27). Listed for the fold-2 type-share check.

### 0.3 Arena distance bias (unblocked attempts, goalies-in states)

Bias = mean over the arena's games of the per-game mean of (recorded - expected) distance; expected = season league mean + shooting team's road for-offset + defending team's road against-offset (labelled construction). SE = SD of per-game means / sqrt(games). Full per-arena table: `results/shot_attribute_r1/step0_tables.md`.

| season | SD of arena bias across arenas (ft) | mean SE (ft) | share of arena-seasons with abs(z) > 2 | max abs bias (ft) |
|---|---:|---:|---|---:|
| 2021-22 | 1.33 | 0.44 (all) | 36% (all seasons) | 2.69 (all) |
| 2022-23 | 0.94 | | | |
| 2023-24 | 0.71 | | | |

- Arena-season correlation of the bias: 0.62 (2021-22 to 2022-23), **0.10** (2022-23 to 2023-24). The dispersion across arenas is real (36% of arena-seasons beyond 2 SE, against 5% by chance) but it shrinks each season and its persistence collapsed in 2023-24. Expect a past-games arena factor to carry little forward signal on fold 2; L2's venue gate (residual slope <= 0.3 of L0's) is judged on that.
- Neutral-site and outdoor venues (1-4 games each) are their own arenas (labelled, as in SA-R1) and UNDERPOWERED.

### 0.4 Coverage and convention

| | BLOCK | MISS | SOG |
|---|---|---|---|
| missing coordinates | 0 | 0 | 0 |
| (0, 0) coordinates | 0 | 0 | 0 |
| out of range (abs x > 100 or abs y > 42.5) | 0 | 0 | 0 |
| sx > 0 | 99.3-99.8% | 99.0-99.3% | 97.0-97.3% |
| behind the goal line (sx > 89) | 0.02-0.06% | 0.6-1.6% | 0.6-1.4% |
| missing shotType | 100% | 0 | 0.00-0.03% |

`sx, sy`: shooting team attacks +x, goal line at x = 89 (L14). Blocks are owned by the shooting team (L15). The behind-the-line share of unblocked attempts rises from 0.6% (2021-22) to 1.5% (2023-24), a small recording drift in the 13th cell (listed).

### 0.5 Blocks rule outcome: **(b)**

Rule (a) needs block coordinates to be shot origins AND shotType on at least 95% of blocks. Both conditions fail: the coordinates are block points (0.1) and type is recorded on 0% of blocks (0.1). So **rule (b) applies, exactly as written**:

- The SL-R1 target is **unblocked attempts (Fenwick) only**: SHOT, MISS, GOAL (penalty shots and shootout attempts excluded, as in stage 3).
- Cascade order: attempt (stage 3) -> blocked? -> (if unblocked) location x type (stage 4) -> SOG / miss -> goal. The block decision moves to the front of stage 5, and its model may not use location.
- Blocked attempts get no location in the sim. In SL-R1's closed loop the sim draws block first at the empirical block rate by strength group, labelled a stub for stage 5.
- xG_ref, the shot-quality ratings, the bias checks and G3 are all per unblocked attempt.

Nothing found in step 0 makes the spec unworkable as written, so the lane continues to step 2.

## 1. Build (step 2)

All tables are in `data/processed/shot_attribute/` (v1), built by `scripts/build_shot_attribute_tables.py`, with `created_at < puck_drop` asserted on every ratings and arena row.

- **Attempt rows** `attempt_attr_v1_<season>.parquet`: one row per stage-3 target attempt, with `blocked`. The pre-event stage-1 state is read at t - 1 from the same replay and delayed-penalty fix as the stage-3 rows. **Parity: the (game, team, state) attempt counts match `shot_attempt/attempt_rows_v1` exactly in all four seasons (0 mismatched cells).** Unblocked attempts: 121,567 / 122,010 / 122,482 / 119,924.
- **xG_ref** `xg_ref_v1_f{1,2}.npy`: (78 classes x 5 groups), the empirical goal rate from fold-train seasons only. In-sample mean = goal rate (0.07179 fold 1, 0.07119 fold 2).
- **Shot-quality ratings** `sq_ratings_v1_f{1,2}.parquet`: per fold (built on that fold's xG_ref), groups ES / PP / PK, for and against, with the full grid w {0.5, 0.7, 0.85, 1.0} x b {300, 1000, 3000} attempts.
- **Arena factor** `arena_dist_v1.parquet`: as-of log ratio of recorded to both-teams expected distance over all earlier games at the arena, c = 1,200 pseudo-attempts. SD across games is 0.019-0.027 (about 0.7-0.9 ft).

## 2. Fit (step 3), tuned on fold 1 only

Fold-1 L1 test LL per attempt and offline quintile-spread ratio (ES, for / against) for every grid cell:

| w / b | 300 | 1000 | 3000 |
|---|---|---|---|
| 0.5 | -3.248908; 1.201 / 1.210 | -3.248952; 1.147 / 1.120 | -3.249076; 1.265 / 1.153 |
| 0.7 | -3.248866; 1.237 / 1.168 | **-3.248919; 1.191 / 1.119 (selected)** | -3.249132; 1.295 / 1.271 |
| 0.85 | -3.248857; 1.230 / 1.171 | -3.248892; 1.224 / 1.173 | -3.249208; 1.307 / 1.504 |
| 1.0 | **-3.248849 (max LL)**; 1.214 / 1.151 | -3.248925; 1.289 / 1.192 | -3.249306; 1.326 / 1.709 |

- **Interpretation choice (labelled):** I read "(L24 guard)" as a constraint on the tuning. The selection is the max fold-1 LL among cells whose spread ratios both lie in [0.8, 1.2]: **w = 0.7, b = 1,000**. The LL-best cell (w = 1.0, b = 300) over-responds (1.214) and is better by only 0.00007 nats per attempt (about 0.006 per game). The whole grid spans 0.00046 per attempt. My first run used plain max-LL. I stopped it (my own PIDs) before any fold-2 fit and re-ran with the guard; the grid numbers above come from that first run's log (`results/shot_attribute_r1/tune_grid_1024.log`). No fold-2 number existed when the rule was set.
- **LightGBM (fold-1 inner split = last 20% of training games by date):**

| leaves | min data | best rounds | inner logloss |
|---|---|---|---|
| 15 | 200 | 22 | 3.24202 |
| **15** | **800** | **35** | **3.23584** |
| 31 | 200 | 21 | 3.24278 |
| 31 | 800 | 27 | 3.23944 |

  With 78 classes, early stopping comes in under 40 rounds. Fold 2 reuses 35 rounds (labelled). L3s2 differs only in the seed, which acts through LightGBM's bin-construction sampling (no bagging was in the spec grid; this follows the SA precedent).

## 3. Blind grade, fold 2 (selection; 2024-25, 119,924 unblocked attempts, 1,398 games)

Bold = fails its gate.

| arm | LL / game vs L0 (SE) | xG pred/act overall | ES | PP | PK | high tier pp (overall / ES) | type shares | resp ES for / against | arena slope ratio | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| L0 | 0 | **+3.91%** | **+5.65%** | -2.95% | **+7.01%** | **+1.68 / +1.78** | PASS | **0.00 / -0.03** | 1 (reference) | no |
| L1 | -0.088 (0.037) | **+3.87%** | **+5.61%** | **-3.04%** | **+7.36%** | **+1.67 / +1.76** | PASS | **1.64 / 1.36** | 0.03 (not gated) | no |
| L2 | -0.095 (0.038) | **+3.87%** | **+5.60%** | **-3.04%** | **+7.37%** | **+1.67 / +1.76** | PASS | **1.60 / 1.32** | **-1.42** | no |
| L3 | -0.013 (0.041) | **+3.85%** | **+6.19%** | **-4.73%** | **+6.55%** | **+1.71 / +1.93** | PASS | 1.09 / 0.90 | **-0.73** | no |
| L3s2 | +0.003 (0.042) | +3.86% | +6.20% | -4.72% | +6.57% | +1.71 / +1.94 | PASS | 1.08 / 0.90 | -0.72 | (noise floor) |

- Months: November (+5.1-5.2%) and January (+5.0%) fail the 4% line in every arm. The other powered months run +2.4% to +3.7%.
- Seed floor |L3 - L3s2| = 0.0166 nats per game. Pairwise: L2 vs L1 -0.007 (SE 0.007); L3 vs L1 +0.075 (0.042); L3 vs L2 +0.081 (0.042).
- **Decision rule: no arm passes every bias check, so none is eligible; no arm is selected.** On likelihood alone, no arm beats L0: L1 and L2 are worse by 2.4-2.5 SE, and L3 ties.
- Arena: L0's residual slope on the arena factor is -7.8 ft per unit (jackknife SE 10.1), indistinguishable from zero. Step 0 predicted this (the arena bias persistence fell to 0.10). A ratio to a noise slope cannot be met reliably, so the L2 / L3 venue gate is uninformative here (listed).
- Responsiveness: L1 / L2 pass on fold 1 (the guard selected for that) but over-respond on fold 2 (1.64, CI 1.21-2.59). The actual ES spread is small (Q1 0.0575 to Q5 0.0605), so every ratio is noisy. L3 is the only arm inside the band on fold 2 (1.09, CI 0.80-1.71), and it fails on fold 1 (0.68 / 0.81).

## 4. Fold 1 (diagnostic; 2023-24 test)

| arm | LL / game vs L0 (SE) | xG overall | ES | PP | PK | high tier pp | resp for / against |
|---|---|---|---|---|---|---|---|
| L0 | 0 | +2.57% | +4.26% | -3.18% | +5.23% | +1.66 | 0.01 / -0.05 |
| L1 | -0.123 (0.039) | +2.59% | +4.29% | -3.27% | +5.44% | +1.66 | 1.19 / 1.12 |
| L2 | -0.157 (0.040) | +2.60% | +4.32% | -3.29% | +5.41% | +1.67 | 1.05 / 1.09 |
| L3 | -0.505 (0.048) | +2.35% | +4.77% | -4.87% | +4.47% | +1.67 | 0.68 / 0.81 |

The fold-1 test season shows the same signature: ES over-predicted, PP under-predicted, high tier too high by 1.7 pp.

## 5. Segments (fold 2, L3; no gate; the other arms are in the grade file)

| segment | n | xG pred | xG actual | high-tier pred / actual % |
|---|---:|---:|---:|---|
| rebound (same team, <= 3 s, no stoppage) | 12,206 | 0.069 | 0.117 | 14.7 / 29.5 |
| rush (<= 4 s after an own N/D-zone event; labelled construction) | 1,127 | 0.087 | 0.052 | 14.0 / 5.1 |
| 3v3 OT | 1,129 | 0.079 | 0.087 | 18.1 / 15.9 |
| playoffs | 7,717 | 0.073 | 0.068 | 14.8 / 12.7 |
| regular season | 112,207 | 0.072 | 0.069 | 14.6 / 12.9 |

Rebound attempts are twice as dangerous as predicted. Per the spec, the rebound flag belongs to the rebound / faceoff stage, so this is reported, not owned here. Per-team tables are in the grade file.

## 6. Diagnosis: the recorded location mix drifts (all four seasons; fold-2 xG_ref table)

| season | ES high-danger share % | ES mean xG_ref | ES goals per unblocked attempt | ES miss share % | ES mean distance ft | blocks per game |
|---|---:|---:|---:|---:|---:|---:|
| 2021-22 | 14.50 | 0.0627 | 0.0627 | 27.0 | 35.0 | 27.3 |
| 2022-23 | 14.79 | 0.0639 | 0.0628 | 28.4 | 34.7 | 29.8 |
| 2023-24 | 12.75 | 0.0601 | 0.0611 | 31.5 | 35.8 | 34.4 |
| 2024-25 | 12.23 | 0.0589 | 0.0602 | 34.7 | 36.4 | 33.7 |

- The high-danger share of unblocked ES attempts dropped by 2 pp at the 2023-24 season boundary (the October 2023 share is already 12.3%) and kept falling. The miss share rose steadily, which matches L13 (misses and blocks up, SOG down).
- Goals per unblocked attempt barely moved (0.0627 to 0.0602), while xG_ref of the recorded mix fell further (0.0627 to 0.0589). The recorded location mix degrades faster than scoring does. That points at least partly to a recording change (more, and farther, recorded misses), not only a change in play.
- A frequency pooled over the training seasons sits above the test season under this trend: the L27 mechanism, applied to a mix rather than a rate. None of L0-L3 has a league-level mix term, and the ratings are relative to the snapshot league mean (L1), so they cannot carry a league-wide shift. That is why every arm, L0 included, misses by the same amount.
- An as-of level would track most of it. Last season's ES high-danger share (12.75%) is 0.5 pp from 2024-25, against 1.8 pp for the pooled training mix.

## 7. Engine and tests (prepared; the closed loop did NOT run)

Step 5 was skipped because no arm was eligible. These parts were built and tested before grading, and are committed default-off:

- `engine/sim.py` gains the default-off stage-4 variant (`tables["attr"]`): block stub, then joint class from the arm's lookup, then an xG_ref goal draw. RNG families are `attempt_block`, `attempt_attr` and `attempt_goal`. **Parity: `tests/engine/test_sim_attr_flag.py`. With the flag off, every output array is bit-identical (sha256) to the pre-change engine (b024504) on 4 cases**: synthetic stub, synthetic attempts, synthetic attempts + T2, and real H3''-LC2 + T2 + A3g-c on 12 fold-2 games. The fixture `tests/fixtures/sim_attr_flag_parity.json` was recorded by `scripts/diag_engine_attr_parity_fixture.py` from `git show b024504:src/nhl_sim/engine/sim.py`. Flag-on bookkeeping tests pass.
- `src/nhl_sim/shot_attribute/lookup.py`: the engine table, exact by construction. For L3 the clock intervals are cut at the booster's own split thresholds. `tests/test_shot_attribute_lookup.py` passes for L1, L2 and L3: max |lookup - offline| < 2e-5 on real fold-2 attempts.
- `scripts/run_shot_attribute_g3.py` (sim, then G3 grade, then the G2 re-check through the INV-36 grader) is written and has **NOT been run**.
- The full suite gives 139 passed, 1 xfailed.

## 8. Interpretation choices (labelled)

1. An unblocked attempt with a missing shotType (0.002-0.018%) goes to "other".
2. EN rows use the ES ratings (the stage-3 convention). Group names: ENF = own goalie pulled, ENA = opponent's net empty.
3. L0 uses a Dirichlet posterior mean, with 10 pseudo-attempts on the pooled joint, so that unseen classes stay finite.
4. The MNLs use C = 1e4 (near-unpenalised; resolves one-hot collinearity). In P(type | cell), the cell enters additively.
5. xG_ref fallbacks for empty (class, group) cells: the class pooled over groups, then the cell, then the league.
6. Arena factor: road-only team offsets; all earlier games across seasons (the SA-R1 A5 precedent); c = 1,200, not tuned.
7. The ratings grid selection uses the L24 guard (section 2).
8. Arena gate: residuals use per-cell representative distances (training mean distance per cell), so within-cell recording is out of scope. The slope is unweighted OLS over arenas with n >= 1,500, with a jackknife SE. Raw-distance residuals are in the grade file.
9. Tier shares gate per strength group only at n >= 2,000 (the xG group line). The ES responsiveness gate requires both "for" and "against" in band.
10. Rebound and rush flags use the constructions in `shot_attribute/tables.py` (segments only).
11. The game clock for L3 is the game minute. Playoff OT minutes of 100 and over reuse minute 99 in the lookup (the stage-3 clamp).

## 9. Proposed text for PM-owned docs (not edited)

- LEARNINGS candidate L30: *The recorded shot-location mix drifts. Between 2022-23 and 2024-25 the ES high-danger share of unblocked attempts fell from 14.8% to 12.2%, and misses rose from 28% to 35%, while goals per unblocked attempt held at 0.060-0.063. A location model on pooled training seasons over-predicts shot quality by about 4% on the next season (SL-R1, every arm). For the sim: location and type mixes need an as-of league mix level, as rates do (L27). A fixed xG yardstick also drifts with recording, so stage 4 and stage 6 must be levelled together.*
- Recommendation for the PM: an SL-R2 that adds an as-of league mix offset (per-cell log shares, last season + season to date, LC-style). It needs a per-training-season parity check and an oracle row (L28 / L29), and should be run on L3 and on L0 + offset, keeping the arms that pass here. It also needs a ruling on whether the xG_ref yardstick should be season-levelled before it gates, since goals per attempt did not fall with the mix.
