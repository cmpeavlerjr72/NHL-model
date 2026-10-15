# Strength-state / penalty process (cascade stage 1)

Status: TESTING (SS-R1 and SS-R2 run 2026-10-15; final status is the PM's call). Numbers live in `experiments.md` (SS-R1 / SS-R2 Results), `docs/tests/strength_state_ss_r1_2026-10-15.md` and `docs/tests/strength_state_ss_r2_2026-10-15.md`; this file summarises.

## 1. Purpose

Decides when each team takes a penalty and what kind it is. Everything that follows under the rulebook (PP expiry, a PP goal ending a minor, double minors, coincidental minors and the 5v5 exception, the 3-skater floor with stacked penalties, consecutive service by one player, 3v3 OT penalties with the post-expiry hold) is deterministic GameState mechanics (`src/nhl_sim/engine/`), unit-tested and replay-checked, not modelled. The resulting strength state feeds every later stage (shot generation, goals, deployment).

## 2. Target variable

- Hazard: penalty-taking events per (game, team, interval); intervals are maximal constant pre-event-state stretches cut at whistles and on the game-minute grid (<= 60 s), exposure in seconds. Event definition and the pen_type/pen_desc/pen_minutes mapping: `features.md` section 0.
- Type: class of each event in {minor, double, major, coincidental}; 2024-25 shares 79.4 / 1.5 / 0.4 / 18.7%.
- Population: RS + PO, regulation and OT, shootouts excluded; misconducts, game misconducts and penalty shots tallied, not targets.

## 3. Methodology

- Walk-forward, no random split. Fold 1 (train 2021-22 + 2022-23, test 2023-24) for hyperparameters only; fold 2 (train through 2023-24, test 2024-25) selects. 2025-26 sealed (loader-enforced).
- Primary metric: fold-2 Poisson log-likelihood per game of the hazard counts, vs H0; game-block bootstrap SE (1,000); H3 seed-retrain floor. Type: multinomial log-likelihood.
- Families: piecewise-constant league rate (H0), Poisson GLMs with cell fixed effects (H1 ratings, H2 + game state), LightGBM Poisson (H3); T0 league multinomial, T1 multinomial logit.

## 4. Winner (offline)

H3 (LightGBM Poisson, num_leaves 7, min_data_in_leaf 800, 490 rounds at lr 0.05) beat H2 by +0.42 nats/game (SE 0.03), and H2 beat H1 by +0.46; T1 beat T0 (+0.046 nats/game, SE 0.012). Closed-loop G1 result and the selection status: `experiments.md` SS-R1 Results.

## 5. Robustness

- Responsiveness slopes (actual on predicted per-60 across rating quintiles): taken 0.85, opponent drawn 1.10. They slope, not flat.
- Every hazard arm over-predicts 2024-25 by about 10% (H3 10,227 predicted vs 9,270 actual). The season level is carried from 2023-24 (season feature mapped to the last training season), and 2024-25 had 8% fewer penalty-taking events per team-game (3.32 vs 3.61).
- Team-game calibration by decile, evaluated on the real state path, is inverted (decile 1: 2.6 predicted vs 3.9 actual). Teams that took many penalties spend their time on the PK and at a positive penalty differential, and both of those lower the predicted hazard. This is a path-conditioning effect. The closed loop (G1 PP-opportunity SD and P(k)) is the right check on the distribution.
- Per team: 32 rows, all UNDERPOWERED (82-105 team-games each). The predicted-actual correlation across teams is 0.84.

## 6. Decisions log

- Run-relative 60 s chunking leaked row length to H3 through the clock. It was replaced by cuts on the minute grid before any fold-2 number existed.
- Expiry timing convention: a penalty due at second s expires before that second's events. On the fold-1 replay this gave 1,084 disagreeing seconds against 1,588 for the lazy alternative.
- Consecutive service: a player's multiple penalties are served one after another (majors first). This was found as a rule gap in the replay and fixed in the engine.
- A coincidental stoppage counts for both teams. The engine draws it at rate (lam_h p_c,h + lam_a p_c,a) / 2.
- Test-season cells that are missing from training use the season-pooled (strength x period-type) effect.

## 7. Consumption from the sim

```python
from nhl_sim.strength_state import lookup as LK
from nhl_sim.engine.sim import simulate
lam = LK.hazard_table("H3", booster, team_rows)          # (G, 2, 100 min, 5 st, 5 sc, 5 pdiff), events per hour
types = LK.type_table("T1", t1_json, last_train_season)  # (6 st, 5 sc, 4 period, 4 classes)
out = simulate(dict(lam=lam, types=types, coinc_smp=..., coinc_pim=..., goal_rate=..., stop_rate_ot=...),
               game_ids, game_types, n_seeds, era)
```
Feature order: `models.LGB_FEATURES`. No NaN fills: missing ratings raise. `st` = 'other' (goalie pulled) is unreachable until the stage-8 goalie-pull model exists.

## 8. Artifacts

| Path | What it is |
|---|---|
| `data/processed/strength_state/hazard_rows_v1_<season>.parquet` | hazard rows |
| `data/processed/strength_state/type_rows_v1.parquet` | type rows |
| `data/processed/strength_state/ratings_grid_v1.parquet` | as-of ratings for all 9 grid points |
| `data/processed/strength_state/team_game_v1.parquet`, `coinc_bundles_v1.parquet`, `nontarget_tally_v1.parquet` | aggregates, coincidental composition, tallies |
| `docs/models/strength_state/ss_r1_frozen_params.json` | frozen fold-1 choices |
| `results/strength_state_r1/models/*` (gitignored, HF sync) | fold-2 fits (GLM json, LightGBM txt) |
| `results/ss_r1_g1_<arm>/` | closed-loop sim output |

## 9. Known gaps / follow-ups

- Season-level drift: there is no as-of in-season league level, so a held-out season inherits last season's level. This is the leading SS-R2 candidate.
- Delayed-penalty reverse causality: about 80% of the 6.4% of events in state 'other' follow a delayed-penalty signal against the same team, so the goalie pull is caused by the penalty. The sim never visits 'other', so these events are missing from the closed loop. Pre-event state should be taken at the delayed-penalty signal (SS-R2).
- These two biases partly cancel in the closed loop (+10% level, about -6% missing 'other' events). A G1 pass on PP opportunities would therefore not be clean evidence.
- Score-state terms are exercised by stub goals only. They must be re-gated when stage 6 lands.
- Player-level penalty rates belong to SS-R2 / stage 2.

## 10. SS-R2 (2026-10-15)

- Changes shared by every arm: pre-event state at the delayed-penalty signal (tables `*_v2*`, `delayed.py`); an as-of in-season league level as a fixed offset with no season dummies (`league_level.py`, `models_r2.py`); the extended ratings grid. Frozen on fold 1: k = 50, w = 1.0, prior strength 1800 (grid corners).
- Offline: H3' > H2' > H1' > H0' (H3' vs H2' +0.084 nats/game, SE 0.012). SS-R1's large H3 lead mostly came from 'other'-state rows (the delayed-penalty artefact).
- Bias checks fail for every arm: the January 2025 month level is +10.5% to +11.2%, and H3' overall is +3.08%. G1 was not run. Known gap: within-season seasonality (October high, mid-winter low), which a to-date level cannot carry. SS-R3 candidate: a seasonality profile.
- Consumption (if an SS-R2 arm is ever selected): `models_r2.LGB_FEATURES`. The level offset is per game, so `lookup.hazard_table` needs an SS-R2 path that multiplies by exp(level). That path is not built yet.
