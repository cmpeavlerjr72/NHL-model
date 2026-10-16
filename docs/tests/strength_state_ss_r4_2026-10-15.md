# SS-R4 (INV-29): team-rating response. Lane P report, 2026-10-15

Verdict: **STOPPED at the pre-registered stop condition.** The incumbent H3'' offline spread ratio on fold 1 is already inside [0.8, 1.2] for both ratings, so arms R0-R2 were NOT RUN (no grid built, nothing tuned, no fold-2 grading, no G1). Clock: start 20:54, diagnosis done 20:56 (wall clock), no AWS used, no box request filed.

## Step 0: replay regression (current engine, fold-1 seasons 2021-22..2023-24, 4,201 games, 15,322,353 s)

| variant | strict | gap-aware | games < 99% gap-aware |
|---|---|---|---|
| default (penalties expire BEFORE the second's events; this is what `--expire-first` selected) | 98.134% | **99.993%** | 10 |
| `--lazy-expiry` (alternative convention) | 98.131% | 99.990% | 18 |

SS-R1 reported 99.993% gap-aware and 98.13% strict: **CONFIRMED** on the current engine. Note: the script has no `--expire-first` flag; expire-first is the default (`--lazy-expiry` flips it). I took "the --expire-first variant" to mean the default and ran the lazy variant as the alternative. Outputs `results/strength_state_r4/replay_{default,lazy}/` (gitignored). Remaining disagreement (default): 1,084 s in total (goalie-pull-adjacent 98 s, other 869 s, overtime 117 s).

## Step 1: diagnosis (scripts/diag_strength_state_spread_r4.py)

Spread ratio = predicted (Q5 - Q1) / actual (Q5 - Q1) of penalties taken per 60, quintiles of team-games by own taken-rating and by opponent drawn-rating. SE = game-block bootstrap (500). Phases are regular season only; playoffs are UNDERPOWERED (SEs of 2-40) and in the CSV only.

| fold | arm | rating | all (SE) | Oct-Nov | Dec-Jan | Feb-Apr |
|---|---|---|---|---|---|---|
| 1 | H3'' | own taken | **0.81** (0.12) | 1.09 (0.50) | 0.92 (0.29) | 0.58 (0.15) |
| 1 | H3'' | opp drawn | **0.85** (0.18) | 0.71 (1.14) | 0.53 (0.15) | 1.81 (10.7) |
| 1 | H2'' | own taken | 1.10 (0.16) | 1.42 (0.63) | 1.20 (0.36) | 0.82 (0.19) |
| 1 | H2'' | opp drawn | 1.01 (0.21) | 0.82 (1.35) | 0.68 (0.18) | 2.08 (12.2) |
| 2 | H3'' | own taken | 1.12 (0.16) | 1.31 (0.47) | 1.06 (0.30) | 1.05 (0.35) |
| 2 | H3'' | opp drawn | 0.98 (0.27) | 0.87 (0.93) | 0.73 (0.33) | 1.12 (0.88) |
| 2 | H2'' | own taken | 1.36 (0.20) | 1.51 (0.54) | 1.26 (0.36) | 1.31 (0.43) |
| 2 | H2'' | opp drawn | 1.16 (0.31) | 0.93 (0.96) | 0.89 (0.38) | 1.34 (1.05) |

Full table including playoffs: `results/strength_state_r4/diag_spread_incumbent.csv`.

- Stop condition met: fold-1 H3'' ratios 0.81 and 0.85, both inside [0.8, 1.2] (taken near the lower edge). Interpretation choice (labelled): the condition requires BOTH ratings inside, read on the "all" row.
- The PM's early-season hypothesis (full carry-over inflates the early-season response) is not supported. Oct-Nov ratios are noisy (SE 0.5-1.1) and show no consistent excess over the other phases; no cell is separable from 1.0 at 2 SE except where noted by SE above.
- An offline rating-construction cause is not indicated either: H2'' (GLM) is the steeper offline model on fold 2 (1.36 / 1.16), H3'' is closer to 1.

## Where the closed-loop over-steepness appears to sit (supplementary lead, not an arm)

The G1 over-steepness (0.63 vs 0.41 and 0.44 vs 0.24) is measured on PP opportunities CONFERRED, not on penalties taken. In the committed G1 tables (fold 2, RS+PO) the sim's penalty spread is faithful (taken quintiles Q4-Q0: sim 0.784, offline 0.863, actual 0.775). The excess appears in the penalty-to-PP-opportunity step:

| taken-rating quintile | actual PP opps conferred / penalty | sim conferred / penalty |
|---|---|---|
| Q0 (low) | 0.813 | 0.785 |
| Q4 (high) | 0.754 | 0.790 |

Actual conversion falls with the team's penalty-taking rating; the sim's stays flat. In the data, the coincidental (offsetting, no-PP) share of a team's penalties rises with its taken-rating: 16.0% (Q0), 17.0, 18.3, 20.7, 20.8% (Q4), fold 2, about 560 team-games per quintile (`scripts/diag_strength_state_coinc_by_rating_r4.py`, `results/strength_state_r4/coinc_by_taken_quintile_fold2.csv`). The type arm T1 (`t1_design` in `src/nhl_sim/strength_state/models.py`) uses season, strength state, score and period only; it has NO team-rating feature, so the sim gives every team the league-average coincidental share. That matches the direction and roughly the size of the excess. Caveat: one season, no significance test, minor/double/major mix not checked. This is a lead for a pre-registered type-arm bake-off, not a finding that resolves INV-29.

## Status and recommendation

- INV-29 stays open; the D15 team-PP block stands. The R1 grid (w x prior strength) is not the lever: the offline response is already about 1.0, so a fold-1 constrained grid has nothing to fix.
- Suggested next (PM decision): pre-register "SS-R5", a type-arm bake-off with team-rating features in T1 (T1, T1 + own taken-rating, T1 + both ratings, with strength-state interaction), graded on fold-2 type log-likelihood, then re-run the G1 conferred-PP-opps spread. The engine consumes T1 by lookup, so only the type lookup would gain a rating axis.

## Interpretation choices and PARTIAL items

- Penalties per 60 from hazard-row exposure; quintiles on team-games by rank as `grade_strength_state.py` does; ratio of per-60 spreads.
- Not run (by the stop condition): R0-R2, the ratings grid (w x b), fold-2 conditions (a)-(d), G1 and decomposition. No ratings_grid_v4 built; no engine file touched.

## Reproduce
```
.venv/Scripts/python.exe scripts/diag_strength_state_replay.py --out results/strength_state_r4/replay_default
.venv/Scripts/python.exe scripts/diag_strength_state_replay.py --lazy-expiry --out results/strength_state_r4/replay_lazy
.venv/Scripts/python.exe scripts/diag_strength_state_spread_r4.py
.venv/Scripts/python.exe scripts/diag_strength_state_coinc_by_rating_r4.py
```
