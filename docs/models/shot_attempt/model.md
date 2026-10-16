# Shot-attempt generation (cascade stage 3)

Status: TESTING (SA-R1 run 2026-10-15; no arm selected). Numbers: `experiments.md` SA-R1 Results, `docs/tests/shot_attempt_sa_r1_2026-10-15.md`, `docs/tests/shot_attempt_sa_r1_grade_2026-10-15.md`. Features: `features.md`.

## 1. Purpose

Decides when each team takes a shot attempt (SHOT, MISS, BLOCK, GOAL; Corsi), given strength state, score state, the teams and home ice. Location, type, outcome and shooter are stages 4-6 and player attribution. SA-R1 is team-level, since stage 2 (deployment) is deferred (D15).

## 2. Target

- Attempts per (game, team, interval) on the one-minute grid, cut at changes of the 7-level team-view strength state and the 7-level pre-event score bucket. Exposure is in seconds.
- Penalty shots and shootout attempts are excluded and tallied.
- Goalie-pulled time is included as EN-for / EN-against, with the L20 delayed-penalty convention.

## 3. Methodology

- Walk-forward. Fold 1 (train 2021-23, test 2023-24) is for tuning only. Fold 2 (train 2021-24, test 2024-25) selects. 2025-26 is sealed (loader-enforced).
- Primary metric: fold-2 per-game joint LL of all rows of both teams, vs A0. A4 is graded by its exact negative-multinomial marginal. The SE is a game-block bootstrap (1,000); the noise floor is the A3 seed retrain.
- Families:
  - A0: piecewise-constant cells.
  - A1: Poisson GLM with ratings, home and b2b.
  - A2: A1 plus score x period and last-5 x score.
  - A5: A2 plus the arena factor.
  - A4: A2 plus a shared per-game gamma latent.
  - A3: LightGBM Poisson.
- Every arm carries the SS-R3-method league level plus the season-phase profile as a fixed offset.

## 4. Result (offline, fold 2)

- A3 is +1.062 nats/game over A0 (SE 0.058), A4 +0.989, A2 +0.965, A5 +0.964, A1 +0.402.
- The arena factor adds nothing (A5 - A2 = -0.001, SE 0.002). The shared latent adds +0.024 (SE 0.004).
- **Every arm fails the bias checks**: the overall level is about -5%, and so are most months, 5v5, the central score buckets, and home and away. No arm is eligible and nothing is selected. The offline responsiveness band passes for A1, A2, A5, A4 and A3 (spread ratios 1.04-1.16); A0 is flat by construction.

## 5. Known defects / follow-ups

- **League-level anchoring.** The SS-R3 level is a ratio to the PREVIOUS season. When it is pooled as a fixed offset, a test season inherits the earlier season-to-season ratios (-2% fold 1, -5% fold 2). An anchored level (ratio to one fixed reference season) removes the fold-1 bias (A0 -2.03% -> +0.22%). This is the SA-R2 candidate. It may also affect the stage-1 penalty level.
- **Strength-specific drift.** PK attempts are +6% to +11% on fold 1 in every arm, and PP is -1% to -4.5%. One all-state level cannot carry this; a per-group level is a candidate arm.
- **Rating over-response on fold 1.** The offline spread ratio is 1.14-1.61 across the grid, and lowest at the weakest shrinkage, b = 600 (a grid corner, as is k = 15). Fold 2 is inside the band.
- Score-state terms are fed from engine state, so the closed-loop G2 is mandatory before any selection (L3). It has not been run.
- EN states are unreachable in the engine until the stage-8 goalie-pull model exists. EN-for / EN-against attempts were 2.8% of 2024-25 attempts.

## 6. Artifacts

| Path | What it is |
|---|---|
| `data/processed/shot_attempt/attempt_rows_v1_<season>.parquet` | attempt rows |
| `data/processed/shot_attempt/team_game_v1.parquet` | per team-game attempts / minutes per group |
| `data/processed/shot_attempt/ratings_grid_v1.parquet` | as-of ratings, 12 grid points x 3 groups |
| `data/processed/shot_attempt/profile_v1_f{1,2}.json`, `league_level_v1_f{1,2}.parquet` | profile and level |
| `data/processed/shot_attempt/arena_v1.parquet` | arena factor (w = 0.85, b = 600, c = 1,200) |
| `data/processed/shot_attempt/exclusions_v1.json` | tallies |
| `docs/models/shot_attempt/sa_r1_frozen_params.json` | fold-1 choices: k = 15, w = 0.85, b = 600; A3 7 leaves / 800 min-data / 765 rounds; A4 v = 0.00115 |
| `results/shot_attempt_r1/` (gitignored) | fold-2 / fold-1 fits, hashed predictions, decision.json |
