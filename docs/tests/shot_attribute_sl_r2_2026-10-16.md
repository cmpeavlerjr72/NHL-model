# SL-R2: as-of league location-mix level (cascade stage 4), Lane A2, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R2 (and SL-R1, inherited); D23. Brief: `docs/briefs/lane_A2_shot_attribute_r2_2026-10-16.md`.
- Step-0 script: `scripts/diag_shot_attribute_mixlevel_step0.py`; level module `src/nhl_sim/shot_attribute/mix_level.py`; level table `data/processed/shot_attribute/mix_level_v2.parquet` (every construction, per game, 3 level groups x 13 cells; `created_at < puck_drop` asserted). Full parity table: `results/shot_attribute_r2/step0_tables.md` (gitignored), reproduced below.

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start | 10:50:37 | |
| step 0: levels, parity, selection | 10:53:14 | 10:53:21 |

## Step 0: mix-level constructions (committed before L1m / L3m are fit)

### Construction details (labelled where the spec left a choice)

- Level groups: ES (EN-for and EN-against pooled into it), PP-for, PK. Shares are over the 13 cells of unblocked attempts, all game types, all games dated strictly before the game (created_at = 6 h after the last puck drop of the previous game date, the LC-2 form).
- s_prev = last season's final shares. 2021-22 has no previous season, so its prior is its own final shares (labelled look-ahead); its rows are shown but not judged.
- M1: K in {500, 2000, 8000} pseudo-attempts per level group. M2: K = 2000 (undiscounted prior), season-to-date counts discounted by 0.5^(gap days / H) at each game date, H in {30, 60}.
- E: the pooled shares of the fold's training rows of the same recording era (era 1 = 2021-22 and 2022-23, era 2 = 2023-24 on). Fold 1 has no era-2 training rows, so on fold 1 era-2 games (the 2023-24 test season) fall back to the pooled training shares, i.e. no level (labelled). **There is no recording-era flag in GameState yet** (`engine/rules.py` only has the 3v3-OT rule era); the season-to-era map lives in `mix_level.ERA_OF_SEASON` for now (flag proposed below).
- O: the season's own final shares (oracle; diagnostic, never selectable).
- L0m for parity: L0 fit on the fold's training rows, times exp(log(s_asof / s_train)) on each cell, renormalised (type given cell unchanged). s_train = the pooled training cell share per level group.
- Parity metrics: ES (strength group ES, EN excluded) high-danger share, pred - actual in pp; mean xG_ref per unblocked attempt over all groups, pred / actual - 1, on the fold's own xG_ref table. Tolerances +/-0.5 pp and +/-0.5%.
- "Smallest max |parity|" within a family is read as the larger of |hd| / 0.5 pp and |xG| / 0.5% (labelled; it was not needed: no construction passed).

### Parity per genuine-prior training season (L0m)

| fold | construction | season | ES high-danger pred / act % | hd pp | xG pred / act - 1 | PP xG | PK xG | pass |
|---|---|---|---|---:|---:|---:|---:|---|
| 1 | none (L0) | 2022-23 | 14.65 / 14.79 | -0.14 | -1.19% | -2.38% | +0.54% | no |
| 1 | M0 | 2022-23 | 14.52 / 14.79 | -0.27 | -2.49% | -4.83% | +0.68% | no |
| 1 | E | 2022-23 | 14.65 / 14.79 | -0.14 | -1.19% | -2.38% | +0.54% | no |
| 1 | M1 K500 | 2022-23 | 14.51 / 14.79 | -0.28 | -0.83% | -1.63% | +0.44% | no |
| 1 | M1 K2000 | 2022-23 | 14.52 / 14.79 | -0.27 | -0.98% | -2.14% | +0.59% | no |
| 1 | M1 K8000 | 2022-23 | 14.54 / 14.79 | -0.24 | -1.27% | -3.06% | +0.65% | no |
| 1 | M2 H30 | 2022-23 | 14.68 / 14.79 | -0.10 | -0.76% | -2.48% | +0.67% | no |
| 1 | M2 H60 | 2022-23 | 14.62 / 14.79 | -0.16 | -0.82% | -2.25% | +0.64% | no |
| 1 | **O (oracle)** | 2022-23 | 14.78 / 14.79 | -0.01 | +0.08% | -0.11% | +0.40% | yes |
| 2 | none (L0) | 2022-23 / 2023-24 | 14.02 / 14.79; 14.00 / 12.75 | -0.77 / +1.25 | -2.04% / +2.30% | | | no |
| 2 | M0 | 2022-23 / 2023-24 | | -0.27 / **+2.01** | -2.33% / **+4.39%** | -4.79% / -0.93% | +0.90% / +5.66% | no |
| 2 | E | 2022-23 / 2023-24 | | -0.14 / -0.00 | -1.17% / +0.49% | -2.50% / +0.65% | +0.61% / -0.02% | no |
| 2 | M1 K500 | 2022-23 / 2023-24 | | -0.28 / +0.13 | -0.85% / +1.30% | -1.76% / -0.22% | +0.54% / +2.88% | no |
| 2 | M1 K2000 | 2022-23 / 2023-24 | | -0.27 / +0.24 | -0.98% / +1.44% | -2.24% / -0.34% | +0.73% / +3.96% | no |
| 2 | M1 K8000 | 2022-23 / 2023-24 | | -0.24 / **+0.50** | -1.25% / +1.81% | -3.12% / -0.54% | +0.84% / +4.97% | no |
| 2 | M2 H30 | 2022-23 / 2023-24 | | -0.10 / +0.33 | -0.77% / +1.34% | -2.58% / -0.28% | +0.83% / +4.63% | no |
| 2 | M2 H60 | 2022-23 / 2023-24 | | -0.16 / +0.29 | -0.83% / +1.36% | -2.36% / -0.29% | +0.80% / +4.32% | no |
| 2 | **O (oracle)** | 2022-23 / 2023-24 | | -0.01 / -0.00 | -0.04% / +0.49% | -0.37% / +0.65% | +0.32% / -0.02% | yes |

Summary over the genuine-prior cells (fold 1: 2022-23; fold 2: 2022-23 and 2023-24):

| construction | all pass | max abs hd pp | max abs xG | max parity / tol |
|---|---|---:|---:|---:|
| M0 | no | 2.01 | 4.39% | 8.77 |
| E | no | 0.14 | **1.19%** | 2.39 |
| M1 K500 | no | 0.28 | 1.30% | 2.59 |
| M1 K2000 | no | 0.27 | 1.44% | 2.88 |
| M1 K8000 | no | 0.50 | 1.81% | 3.62 |
| M2 H30 | no | 0.33 | 1.34% | 2.68 |
| M2 H60 | no | 0.29 | 1.36% | 2.71 |
| O (oracle) | **yes** | 0.01 | 0.49% | 0.99 |
| none (plain L0) | no | 1.25 | 2.30% | 4.60 |

### Selection: **E** (fallback rule)

- No selectable construction passes. The rule then takes the smallest max |xG_ref parity|: E at 1.19%. M1 K500 (1.30%), M2 H30 (1.34%) and M2 H60 (1.36%) lie within 0.2% of it, and E is the simplest of those (M0 < E < M1 < M2). **Selected: E.** The failure is listed, as the LC-2 rule requires: every as-of construction fails xG parity by 0.8-1.8%; only the oracle passes.
- **The oracle passes both lines** (max 0.01 pp, 0.49%). So the residual under the as-of constructions is the level's (lag), not the arm's. With the oracle level, xG parity is within 0.5% in every season. The L0 type and within-group composition do not carry a mix error.
- **Caveat on E, for the PM (labelled, the spec is followed as written):** E's parity is in-sample on every judged cell. Fold 2's era 2 has a single training season (2023-24), so E on 2023-24 *is* that season's own shares, identical to the oracle (-0.00 pp, +0.49%). Era 1 pools 2021-22 and 2022-23, so E on 2022-23 includes the season itself. E's max (1.19%) comes from the within-era-1 spread, not from forecasting. The as-of constructions are genuinely out-of-sample. On the fold-2 test season, E = the 2023-24 final shares, the same value as M0 for 2024-25. So the fold-2 test of E is a test of "last season's shares" applied to a season inside the same era. On fold 1 every training season is era 1, so s_asof = s_train and **E is identical to plain L0 on fold 1** (offset 0 everywhere, including the 2023-24 fallback); the fold-1 E rows above equal the fold-1 none rows.
- Where the as-of constructions miss: 2022-23 under-predicted (-0.8% to -1.3%; the mix moved toward the slot from 2021-22, with PP -1.6% to -3.1%), and 2023-24 over-predicted (+1.3% to +1.8%; the era step). PK on 2023-24 is +2.9% to +5.0% for every as-of construction (PK mix stepped too and the PK group is small, so season-to-date catches up slowly). Short memory helps: K500 and H30 track best.

Next: fit L0m, L1m and L3m (+ seed 2) with level E.
