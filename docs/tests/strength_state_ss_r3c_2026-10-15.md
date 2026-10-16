# SS-R3c stage-1 incumbent re-levelled with LC-1 (INV-31, Lane S2, 2026-10-15)

Spec: `docs/models/strength_state/experiments.md` SS-R3c, D16. Type arm: **T2**, per the PM note (SS-R5 ruled in dff868d / 9b299f3; the G1 wrapper `scripts/run_strength_state_g1_v3c.py` uses T2 through Lane P2's `run_strength_state_g1_v5.py`, unmodified).

**Outcome: STOPPED at the spec's LC-1 parity assertion.** The parity test fails on fold-1 train for every arm, including the level-only H0''c. Fold 2 was fitted (hash-labelled, in `results/strength_state_r3c/`) but **not graded**: no bias checks, no fold-2 comparison with H3'', no G1. By the decision rule's spirit nothing changes, and D15 (H3'' + T2 per the SS-R5 ruling) stays in force. The PM rules.

## Clock (Get-Date, EDT)

| step | time |
|---|---|
| level tables `league_level_v4_f{1,2}` | 21:17:39-21:17:52 |
| tune k (fold 1, H1''c) | 21:17:58-21:18:04 |
| fold-2 + fold-1 fits with parity | 21:29:13-21:29:56 |
| stop decision | 21:35 |

## What was run

- **LC-1 tables:** `data/processed/strength_state/league_level_v4_f{1,2}.parquet` (v3 untouched). These use the SS-R3 profile (`profile_v3_f{fold}`, unchanged as the spec requires), k in {5, 15, 50}, and the shared `src/nhl_sim/league_level_lc1.py`. `created_at < puck_drop` is asserted.
- **k tuned on fold 1** with H1'' (SS-R3 practice): k = 5, 15, 50 give fold-1 LL -35.95991 / -35.96017 / -35.96074, so k = 5 is frozen (a grid corner). Fold-1 test pred/actual for H1''c is 1.037 / 1.037 / 1.035, i.e. a +3.7% fold-1 diagnostic bias.
- **Fits:** H0''c-H3''c and H3''c seed 2, with SS-R3's frozen LightGBM parameters (7 leaves, 200 min-data, 378 rounds), on both folds (`scripts/train_strength_state_v3c.py`).

## Parity (in-sample predicted / actual - 1 per training season; the limit is 0.5%)

| arm | fold-1 train 2021-22 | 2022-23 | fold-2 train 2021-22 | 2022-23 | 2023-24 |
|---|---:|---:|---:|---:|---:|
| H0''c | -2.07% | +2.01% | -3.20% | +0.93% | +2.24% |
| H1''c | -1.96% | +1.91% | -3.19% | +0.73% | +2.43% |
| H2''c | -2.06% | +2.00% | -3.30% | +0.79% | +2.47% |
| H3''c | -2.19% | +2.15% | -3.27% | +1.19% | +2.05% |

**FAIL** for every arm, by about 4x the limit.

## Diagnosis (fold-1 / training data only)

Penalty rate per team-hour by season: 3.550 (2021-22), 3.626 (2022-23), 3.568 (2023-24). The exposure-weighted mean of exp(level + p) over the 2022-23 rows is 3.74 per team-hour. That is 3% ABOVE the season's actual rate, while 2021-22 sits 1.5% below its own.

The as-of level is a season-to-date de-seasonalised rate. When one season's month pattern differs from the training-mean profile (penalties are strongly seasonal, L22 / L23), the error in the early-month de-seasonalisation persists in the to-date rate for weeks. The time average of the level then misses the season rate by a few percent, in a different direction each season. Attempts are nearly flat across the season (profile within +/-1.2% by month), so SA-R2's level-only arm stays inside 0.5% (-0.48% / +0.46%). Penalties are not flat, and theirs does not.

This is a property of LC-1 under a season-varying profile. It is not a coding error: the level tests in `tests/test_league_level_lc1.py` pass, and the same module passes on attempts.

Candidates for the PM (not run):
- a season-to-date level with a shorter memory, or recomputed on full-season-profile residuals;
- a per-season profile fit, as in L23 (its fold-2 use is risky);
- relaxing the parity limit for seasonal targets.

## Resume

The fold-2 predictions and models exist, ungraded. If the PM rules that the parity assertion does not block, resume from these commands, in order:

```
.venv/Scripts/python.exe scripts/diag_strength_state_bias_r3c.py
.venv/Scripts/python.exe scripts/grade_strength_state.py --res results/strength_state_r3c --round SS-R3c --out docs/tests/strength_state_ss_r3c_grade_2026-10-15.md
.venv/Scripts/python.exe scripts/run_strength_state_g1_v3c.py g1 --arm H3 --seeds 200 --workers 4
.venv/Scripts/python.exe scripts/run_strength_state_g1_v3c.py decomp --arm H3
```

The last two run G1 and its decomposition (including the PP-opportunities-conferred spread ratios, RS and all games). They take about 10 min with 4 workers. Repeat them with `--arm H2` for the H2''c report.
