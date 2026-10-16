# SS-R3 season-phase profile for the penalty hazard, full report (Lane H3, INV-27), 2026-10-15

Spec: `docs/models/strength_state/experiments.md` SS-R3 and the D13 ruling (commit dd9faf8), run as written. Worker: Sonnet, no sub-agents. Clock: start 19:59; profile build 20:00; tune 20:01; fold-2 and fold-1 fits 20:01-20:02; grade and bias checks 20:02-20:03. Every step took under 1 minute, so nothing went to Lane O and no AWS or box request was made.

Detail files: `docs/tests/strength_state_ss_r3_grade_2026-10-15.md` (blind table, reveal, decision rule, secondary tables) and `docs/tests/strength_state_ss_r3_bias_2026-10-15.md` (bias checks on fold 2 and fold 1, twins, by month).

## Headline

1. **Bake-off: H3'' > H2'' > H1'' > H0''**, every step significant. **Offline winner H3''** (+0.0752 nats/game over H2'', SE 0.0116, seed floor 0.0073).
2. **Bias checks on fold 2 (gate): FAIL for every arm.** January 2025 still runs +8.3% (H2'') to +9.0% (H1'') against the +/-8% limit, n = 224 games. The overall level check now passes for all four arms, H3'' included (+1.45%; SS-R2's H3' failed at +3.08%). The 'other' check passes for all four.
3. **Fold 1 (diagnostic):** every profile arm passes every check (worst month Nov 2023, -5.4% for H3''); the SS-R2 twins refit on fold 1 fail October 2023 (-8.7% to -9.5%). So the profile removes the fold-1 monthly bias but not the fold-2 January bias. Under D13 a fix counts only if it removes the monthly bias on both folds, so it does not count.
4. **Twin preference:** no SS-R3 arm is preferred over its SS-R2 twin, because none passes the fold-2 checks. The profile arms are not worse on likelihood: +0.008 to +0.010 nats/game for H0''-H2'', -0.0001 for H3'' (SEs 0.004 to 0.005).
5. **Closed-loop G1: NOT RUN** (no arm passed the bias checks; the brief says skip). The engine offset lookup and its 0.5% parity test are not built, because they are conditional on a passing arm.
6. strength_state stays TESTING. Per D13 the PM now decides between accepting an arm with its biases listed and stopping work on stage 1. No SS-R4 is proposed here.

## Step 1: profile and de-seasonalised level (`src/nhl_sim/strength_state/seasonality.py`, `scripts/build_strength_state_profile_v3.py`)

Tables (v2 untouched): `data/processed/strength_state/profile_v3_f{1,2}.json` and `league_level_v3_f{1,2}.parquet` (k in {15, 50, 150}; `created_at < puck_drop` asserted on every row). Test: `tests/test_seasonality.py` (2 tests: the profile uses training seasons only; the level is as-of and stays flat when a season follows the profile). Full suite: 90 passed.

Profile p(b), log ratio of the bin's rate to the season's full rate, equal-weight mean over training seasons:

| bin | Oct | Nov | Dec | Jan | Feb | Mar | Apr | PO |
|---|---|---|---|---|---|---|---|---|
| fold 1 (2021-23) | +0.114 | -0.007 | -0.026 | -0.002 | -0.035 | -0.040 | -0.034 | +0.089 |
| fold 2 (2021-24) | +0.135 | +0.018 | -0.030 | -0.012 | -0.025 | -0.045 | -0.055 | +0.052 |

Level on profile-adjusted exposure: E is the sum of observed events / exp(p of the game's bin) over the season-to-date games; H is team-hours; r_prev is the previous season's final profile-adjusted rate; level = log(((E + 2k r_prev) / (H + 2k)) / r_prev). The arm offset is level + p(bin of the game), coefficient 1, in every arm (GLM and LightGBM `init_score`); `models_r2.attach_features(profile_fold=1|2)`.

Tuned on fold 1 only: H1'' LL/game for k = 15 / 50 / 150: -35.9559 / -35.9568 / -35.9579. **k = 15** (the smallest value of the grid, a corner again; the spread is 0.002 nats/game). w = 1.0 and prior strength 1,800 frozen as in SS-R2. H3'' re-tuned on the SS-R1 grid on fold 1: num_leaves 7, min_data_in_leaf 200, 378 rounds (`ss_r3_frozen_params.json`).

## Step 2: bake-off (fold 2, 1,398 games, 330,280 rows, 9,270 events)

| arm | LL/game vs H0'' | SE | predicted events (actual 9,270) | SS-R2 twin predicted events |
|---|---|---|---|---|
| H0'' | 0 | | 9,330 | H0' 9,492 |
| H1'' | +0.0512 | 0.0105 | 9,353 | H1' 9,516 |
| H2'' | +0.2608 | 0.0197 | 9,344 | H2' 9,505 |
| H3'' | +0.3360 | 0.0196 | 9,404 | H3' 9,555 |

- Pairwise: H2'' vs H1'' +0.2096 (0.0176); H3'' vs H2'' +0.0752 (0.0116); H3'' vs H1'' +0.2848 (0.0180). H3'' seed retrain: floor 0.0073 (larger than SS-R2's 0.0003). Every comparison clears 2 SE and the H3'' ones clear the seed floor. **Literal rule: offline winner H3'', runner-up H2''.** T1 carried over, not re-raced.
- Paired LL vs the SS-R2 twin (fold 2, same rows): H0'' +0.0093 (SE 0.0043), H1'' +0.0096 (0.0041), H2'' +0.0083 (0.0040), H3'' -0.0001 (0.0048). None is worse by more than 2 SE.
- Responsiveness for H3'': slope 0.86 by own taken-rating quintile and 1.00 by opponent drawn-rating quintile. All 32 teams are UNDERPOWERED (min_cell_n 300). Other secondary tables are in the grade file.

## Step 3: bias checks (`scripts/diag_strength_state_bias_r3.py`)

Fold 2 (2024-25; GATES):

| arm | pred / actual | overall (+/-3%) | months failing (+/-8%, n >= 100) | worst month | 'other' net shortfall | all pass |
|---|---|---|---|---|---|---|
| H0'' | 1.0065 | PASS | 1 | Jan +8.6% | -0.27% | **FAIL** |
| H1'' | 1.0089 | PASS | 1 | Jan +9.0% | -0.26% | **FAIL** |
| H2'' | 1.0079 | PASS | 1 | Jan +8.3% | +0.12% | **FAIL** |
| H3'' | 1.0145 | PASS | 1 | Jan +8.8% | -0.03% | **FAIL** |
| twins H0'-H3' (SS-R2) | 1.024 / 1.027 / 1.025 / 1.031 | 3 PASS, H3' FAIL | 1 each | Jan +10.5% to +11.2% | | FAIL |

H3'' by month, fold 2 (predicted / actual): Oct 1.031, Nov 1.000, Dec 0.992, **Jan 1.088**, Feb 1.049, Mar 0.986, Apr 0.990, May 0.957 (n = 40, UNDERPOWERED), Jun 0.897 (n = 6, UNDERPOWERED). January is the only month beyond 8%. The profile removed the October-December and March-April misses and cut January from +10.8% to +8.8%. The profile value for January is only -0.012, because January sat close to the season mean in 2021-24; 2024-25's January (3.04 events per team-game) was a dip that a profile estimated from other seasons cannot anticipate.

Fold 1 (2023-24; diagnostic):

| arm | pred / actual | months failing | worst month | all pass |
|---|---|---|---|---|
| H0'' / H1'' / H2'' / H3'' | 1.007 / 1.010 / 1.011 / 1.003 | 0 / 0 / 0 / 0 | Nov -4.6% / Nov -4.8% / Apr +4.8% / Nov -5.4% | PASS x4 |
| twins refit on fold 1: H0' / H1' / H2' / H3' | 1.014 / 1.017 / 1.018 / 1.009 | 1 each | Oct -9.5% / -9.3% / -8.7% / -9.5% | FAIL x4 |

Reading: the profile fixes the fold-1 October miss and most of the level drift. The fold-2 January miss is a one-season event. The 'other' check passes in every arm on both folds (raw share 1.54% on fold 2, reported, not gated, per D13).

## Step 4: closed-loop G1: NOT RUN

No arm passes the fold-2 bias checks, so by the brief G1 is skipped and no engine offset lookup or parity test was built.

| cell | RS | PO | overall |
|---|---|---|---|
| TOI by strength state | NOT RUN | NOT RUN | NOT RUN |
| PP opps / team-game (mean, SD, P(k)) | NOT RUN | NOT RUN | NOT RUN |
| PIM / game | NOT RUN | NOT RUN | NOT RUN |
| share of minors ended by a PP goal | NOT RUN | NOT RUN | NOT RUN |
| per-team PP opps | NOT RUN | NOT RUN | NOT RUN |
| 100 vs 200 seed check | NOT RUN | | |

## Interpretation choices (most literal reading, labelled)

1. "That same season's full-season rate" = the season's rate over all its games, regular season and playoffs, per team-hour.
2. The one regular-season game dated in May (2021-22) is put in the Apr bin. Playoffs (game_type 3) form the PO bin whatever the month.
3. "Observed count / count expected under p" is implemented as each game's events divided by exp(p of its bin), for both the season-to-date count and the previous season's final rate r_prev (so the level is a ratio of de-seasonalised rates).
4. The arm offset is level + p (coefficient 1) in every arm, including the LightGBM `init_score`; no profile feature is given to the tree model.
5. The H3'' LightGBM grid was re-tuned on fold 1 (the spec fixes k, w and prior strength only; SS-R2 re-tuned it too).
6. The fold-1 twins are the SS-R2 arms refit on fold 1 with SS-R2's frozen parameters (k = 50, w = 1.0, prior 1,800, SS-R2 LightGBM settings), because the SS-R2 run did not write fold-1 predictions.
7. The grade script prints double-prime labels for round SS-R3 (a one-line, backward-compatible change).

## Proposed text for the PM

- LEARNINGS candidate: a season-phase profile estimated from other seasons fixes systematic seasonality (October, level drift: fold 1 fully, fold 2 except January) but cannot fix a season-specific within-season dip. A +/-8% monthly check at n = 224 games on a single test season is sensitive to such an event (+9% is about 4 Poisson SE).
- k = 15 is the grid corner again (spread 0.002 nats/game, so the choice is weakly identified).

## Resume / reproduce

```
.venv/Scripts/python.exe scripts/build_strength_state_profile_v3.py
.venv/Scripts/python.exe scripts/train_strength_state_v3.py tune
.venv/Scripts/python.exe scripts/train_strength_state_v3.py fold2
.venv/Scripts/python.exe scripts/train_strength_state_v3.py fold1
.venv/Scripts/python.exe scripts/grade_strength_state.py --res results/strength_state_r3 --round SS-R3 --out docs/tests/strength_state_ss_r3_grade_2026-10-15.md
.venv/Scripts/python.exe scripts/diag_strength_state_bias_r3.py
```

PARTIAL: G1 (not run, by rule), engine offset lookup and 0.5% parity test (conditional on a passing arm). AWS: not used. Incidents: none.
