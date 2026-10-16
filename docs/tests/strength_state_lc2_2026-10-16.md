# LC-2 penalty league level (INV-33, Lane L2, 2026-10-16)

Spec: `docs/models/strength_state/experiments.md` LC-2 (21fe71e), unchanged. Code: `src/nhl_sim/league_level_lc2.py` (+ `tests/test_league_level_lc2.py`), `scripts/exp_strength_state_lc2_step0.py`, `train_strength_state_lc2.py`, `diag_strength_state_bias_lc2.py`, `run_strength_state_g1_lc2.py`, `diag_strength_state_lc2_spread.py`. Level tables `data/processed/strength_state/league_level_v5_f{1,2}.parquet` (v3/v4 untouched). Results: `results/strength_state_lc2/`.

## Outcome

- Step 0: **no construction passes the 0.5% parity line on the genuine-prior seasons.** Selected by the fallback rule: **L2b, half-life 14 days** (max |parity| 0.93%, fold-2 train 2023-24). The parity failure is listed below.
- Step 1: H3''-LC2 passes every SS-R3c acceptance condition (bias checks, fold-2 LL not worse than H3'' by more than 2 SE, G1 RS cells PASS, RS decomposition CLEAN). H2''-LC2 likewise.
- Step 2: INV-29 spread ratios for H3''-LC2 are inside [0.8, 1.2] at the point estimate in all four cells (1.10 / 1.11 / 1.13 / 1.19). Team-bootstrap CIs are wide and straddle the band. H2''-LC2 is outside (1.41 to 1.54).

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| step 0 (all levels, parity, both folds) | 09:29:45 | 09:30:09 |
| fits fold 2 / fold 1 (H0''-H3'', H3'' seed 2) | 09:30:52 / 09:31:10 | 09:31:10 / 09:31:21 |
| G1 H3'' 200 seeds, 4 workers (hazard table 47 s; chunks 300-336 s) | 09:31:52 | 09:38:27 |
| G1 H2'' 200 seeds | 09:38:27 | about 09:44 |
| decomposition, spread ratios | 09:44:45 | about 09:48 |

Measured G1 chunk time projects about 6.5 min per arm, below the 15 min box threshold; no box request filed. Cores used: 4.

## Step 0: construction table (H0'' level-only fit, in-sample predicted / actual - 1 per training season)

Genuine-prior seasons: fold 1 = 2022-23; fold 2 = 2022-23 and 2023-24. The 2021-22 columns use a look-ahead prior (labelled, uninformative). Limit 0.5%.

| construction | f1 2021-22 (look-ahead prior) | f1 2022-23 | f2 2021-22 (look-ahead) | f2 2022-23 | f2 2023-24 | max abs genuine (both folds) | wmean genuine f1 / f2 | f1 test 2023-24 overall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| L1 | -2.07% | +2.01% | -3.20% | +0.93% | +2.24% | 2.24% | +2.01% / +1.57% | +3.39% |
| L2c | +1.19% | -1.18% | +0.29% | -1.85% | +1.59% | 1.85% | -1.18% / -0.15% | +2.53% |
| O | +0.26% | -0.26% | +0.24% | -0.27% | +0.02% | 0.27% | -0.26% / -0.12% | +0.05% |
| L2a_k50 | -1.72% | +1.67% | -2.83% | +0.65% | +2.15% | 2.15% | +1.67% / +1.39% | +3.22% |
| L2a_k200 | -1.06% | +1.03% | -2.06% | +0.14% | +1.89% | 1.89% | +1.03% / +1.01% | +2.87% |
| L2a_k800 | -0.07% | +0.06% | -0.98% | -0.69% | +1.67% | 1.67% | +0.06% / +0.48% | +2.58% |
| L2b_hl14 | -0.14% | +0.13% | -0.60% | -0.33% | +0.93% | 0.93% | +0.13% / +0.29% | +1.40% |
| L2b_hl30 | -0.74% | +0.72% | -1.43% | +0.05% | +1.36% | 1.36% | +0.72% / +0.70% | +2.05% |
| L2b_hl60 | -1.30% | +1.26% | -2.19% | +0.42% | +1.75% | 1.75% | +1.26% / +1.08% | +2.62% |

Code check: the oracle O at the level (sum of h exp(p + O) against the sum of events per season, from team_game_v2) is 0 to rounding (<= 4e-16) in both folds, and the unit test asserts the same. The O row above is not 0 only because H0'' pools its strength x period-type cells over the training seasons (cell multipliers, about 0.27%), not because of the level. O is the diagnostic ceiling and was never selectable.

Selection (as written): no passer. Smallest max |parity| over the genuine-prior seasons of both folds is L2b hl14 at 0.93% (next L2b hl30 1.36%, L2a k800 1.67%; nothing within 0.3 pp, so no tie to the simpler family). Fold 2 alone gives the same pick. **Parity FAILURE listed: L2b hl14 +0.93% in 2023-24 (fold-2 train).** It passes fold 1 (+0.13%) and fold-2 2022-23 (-0.33%). Exposure-weighted mean parity over the genuine-prior seasons: +0.13% (fold 1), +0.29% (fold 2).

Readings for the PM:

1. L2a k800 passes fold 1 (+0.06%) only by cancellation; fold 2 gives -0.69% / +1.67%.
2. The oracle row shows the level path is not the main remaining error. With the season's own final rate as the level, the fold-1 test season's bias by month is still Oct -7.5%, Nov -7.4%, Apr +7.8%, PO +10.4%: the training-only SS-R3 profile does not fit the 2023-24 month shape. Short-memory L2b hl14 scores best partly because it tracks that profile error in-season (fold-1 test month bias is smaller: Oct +2.7%, Apr +6.0%, PO +2.9%). That is the level compensating for a profile defect.
3. Fold-1 test overall (diagnostic): L1 +3.39%, L2b hl14 +1.40%.

Fold-1 test (2023-24) level-only H0'' bias by month (pred / actual - 1; diagnostic):

| construction | Oct | Nov | Dec | Jan | Feb | Mar | Apr | PO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| L1 | +3.1% | -2.0% | +5.2% | +5.8% | -1.1% | +3.4% | +8.4% | +10.0% |
| L2c | -5.2% | -5.1% | +4.1% | +6.3% | -0.1% | +4.9% | +10.5% | +13.2% |
| O | -7.5% | -7.4% | +1.6% | +3.8% | -2.5% | +2.4% | +7.8% | +10.4% |
| L2a_k50 | -0.5% | -2.4% | +5.5% | +6.2% | -0.7% | +3.9% | +9.0% | +10.5% |
| L2a_k200 | -3.4% | -3.3% | +5.2% | +6.4% | -0.4% | +4.3% | +9.4% | +11.1% |
| L2a_k800 | -4.9% | -4.4% | +4.7% | +6.4% | -0.2% | +4.6% | +9.9% | +11.8% |
| L2b_hl14 | +2.7% | -3.1% | +2.7% | +2.9% | -1.6% | +1.7% | +6.0% | +2.9% |
| L2b_hl30 | +3.0% | -2.7% | +3.9% | +4.0% | -2.2% | +2.1% | +6.6% | +5.6% |
| L2b_hl60 | +3.1% | -2.4% | +4.6% | +4.8% | -1.9% | +2.5% | +7.2% | +7.5% |

## Step 1: refit and grade (H3'' = old level SS-R3, from `results/strength_state_r3`)

Frozen SS-R3 LightGBM parameters, type arm T2. In-sample parity of the fitted arms: fold-1 train H0-H2 within +-0.14%, H3 -0.58% / +0.57%; fold-2 train H0 -0.60 / -0.33 / +0.93%, H3 -1.05 / +0.04 / +1.01%. The 2023-24 line fails for every arm, as for the level alone.

Fold-2 blind grade (`docs/tests/strength_state_lc2_grade_2026-10-16.md`): H3 is the offline winner; H3 - H2 +0.0754 (SE 0.0114). Seed floor |H3 - H3 seed 2| = 0.001131 nats/game.

Bias checks (`docs/tests/strength_state_lc2_bias_2026-10-16.md`), fold 2 gates:

| arm | pred/actual | overall | months failed | worst month | other net | all pass |
|---|---:|---|---:|---|---:|---|
| H0''L | 1.0072 | PASS | 0 | 2025-01 +7.3% | -0.0027 | True |
| H1''L | 1.0096 | PASS | 0 | 2025-01 +7.7% | -0.0027 | True |
| H2''L | 1.0086 | PASS | 0 | 2025-01 +7.0% | +0.0012 | True |
| H3''L | 1.0156 | PASS | 0 | 2025-01 +7.6% | -0.0002 | True |

January 2025 stays a listed bias (+7.6%, under the 8% line; the old-level H3'' sat at +8.8% and failed one month). Fold-1 diagnostic: overall 1.013 to 1.018, worst month 2024-04 +3.8% to +4.3%.

Fold-2 LL/game against the old level (paired game-block bootstrap): H3''L - H3'' -0.0015 (SE 0.0023), not worse by more than 2 SE. H0 -0.0017 (0.0015), H1 -0.0020 (0.0015), H2 -0.0017 (0.0015). The differences are the size of the seed floor: no offline gain or loss.

Closed-loop G1 (200 seeds, T2; `docs/tests/gates_g1_ss_lc2_g1_{H3,H2}_T2_2026-10-16.md`, decomposition in `results/strength_state_lc2/decomp_{H3,H2}.log`):

| | H3''-LC2 | H2''-LC2 |
|---|---|---|
| RS cells (TOI 5v5/PP/4v4/5v3, PP opps mean and SD) | PASS | PASS |
| RS PP opps / team-game, sim vs actual | 2.6505 vs 2.5640 (+0.0865) | 2.6325 vs 2.5640 (+0.0684) |
| decomposition RS / overall | CLEAN / CLEAN | CLEAN / CLEAN |
| decomposition playoffs (UNDERPOWERED) | CLEAN | COMPENSATED |
| overall PP opps, sim vs real | 2.6640 vs 2.5844 | 2.6446 vs 2.5844 |

H3''-LC2 RS decomposition (PP opps / team-game): hazard level +0.0449, 'other' state -0.0402, state-visit -0.0070, remainder +0.0389, PP opps per event +0.0499; none above the 0.15 tolerance. Simulated penalties by team taken-rating quintile (all games) are 2.97, 3.20, 3.26, 3.54, 3.77 against actual 2.87, 3.14, 3.39, 3.53, 3.65, so the sim slopes with the actuals.

SS-R3c acceptance for H3''-LC2 is met as written, with the level-parity failure listed above.

## Step 2: INV-29 spread ratios (PP opportunities conferred, Q5 - Q1, sim / actual; band [0.8, 1.2])

## INV-29 spread ratios, H3''-LC2 + T2 (fold 2, 200 seeds); band [0.8, 1.2]

| rating | games | actual Q5-Q1 | sim Q5-Q1 | ratio | 95% CI (team bootstrap) | sim - actual spread, 95% CI | in band |
|---|---|---:|---:|---:|---|---|---|
| regular season, own taken-rating | 2624 | 0.417 | 0.459 | 1.10 | 0.74 to 2.34 (unstable: the actual spread is near 0 in many resamples) | +0.041 (-0.162, +0.243) | yes (CI overlaps edge/outside) |
| regular season, opponent drawn-rating | 2624 | 0.253 | 0.281 | 1.11 | -5.27 to 7.02 (unstable: the actual spread is near 0 in many resamples) | +0.027 (-0.245, +0.273) | yes (CI overlaps edge/outside) |
| all games, own taken-rating | 2796 | 0.412 | 0.466 | 1.13 | 0.74 to 2.80 (unstable: the actual spread is near 0 in many resamples) | +0.054 (-0.172, +0.258) | yes (CI overlaps edge/outside) |
| all games, opponent drawn-rating | 2796 | 0.241 | 0.285 | 1.19 | -5.16 to 8.87 (unstable: the actual spread is near 0 in many resamples) | +0.045 (-0.228, +0.280) | yes (CI overlaps edge/outside) |

## INV-29 spread ratios, H2''-LC2 + T2 (fold 2, 200 seeds); band [0.8, 1.2]

| rating | games | actual Q5-Q1 | sim Q5-Q1 | ratio | 95% CI (team bootstrap) | sim - actual spread, 95% CI | in band |
|---|---|---:|---:|---:|---|---|---|
| regular season, own taken-rating | 2624 | 0.417 | 0.592 | 1.42 | 1.02 to 2.76 (unstable: the actual spread is near 0 in many resamples) | +0.174 (+0.010, +0.331) | NO (CI overlaps edge/outside) |
| regular season, opponent drawn-rating | 2624 | 0.253 | 0.358 | 1.41 | -6.12 to 8.75 (unstable: the actual spread is near 0 in many resamples) | +0.105 (-0.122, +0.324) | NO (CI overlaps edge/outside) |
| all games, own taken-rating | 2796 | 0.412 | 0.607 | 1.47 | 1.04 to 3.32 (unstable: the actual spread is near 0 in many resamples) | +0.195 (+0.028, +0.350) | NO (CI overlaps edge/outside) |
| all games, opponent drawn-rating | 2796 | 0.241 | 0.371 | 1.54 | -6.85 to 11.04 (unstable: the actual spread is near 0 in many resamples) | +0.130 (-0.096, +0.333) | NO (CI overlaps edge/outside) |

The ratio CIs are unstable because the actual spread is close to 0 in many team resamples (one actual quintile mean has SE about 0.055). The CI on the spread difference (sim - actual) is the usable number. For H3''-LC2 that CI contains 0 in all four cells. The SS-R5 H3''+T2 (old level) all-games ratios were 1.19 (taken) and 1.25 (drawn); the all-games drawn ratio is now 1.19. One season of sampling error cannot separate 1.19 from 1.25. H2''-LC2 sits at 1.4 to 1.5.

## Not done / caveats

- No INV-29 arm fitted (per spec). Nothing on fold-2 test was read for the level selection.
- Selection used both folds' genuine-prior seasons; fold-2 alone gives the same pick.
- Playoff cells are UNDERPOWERED throughout.

## Resume

```
.venv/Scripts/python.exe scripts/exp_strength_state_lc2_step0.py
.venv/Scripts/python.exe scripts/train_strength_state_lc2.py fold2   (then fold1)
.venv/Scripts/python.exe scripts/diag_strength_state_bias_lc2.py
.venv/Scripts/python.exe scripts/run_strength_state_g1_lc2.py g1 --arm H3 --seeds 200 --workers 4   (then --arm H2; then decomp --arm H3|H2)
.venv/Scripts/python.exe scripts/diag_strength_state_lc2_spread.py --arm H3
```
