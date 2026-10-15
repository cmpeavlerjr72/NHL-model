# Strength-state / penalty process: experiments (append-only)

Cascade stage 1 (FRAMEWORK_PLAN section 1). This sub-model decides when each team takes a penalty and what kind it is. Everything that follows from a penalty under the rulebook (PP expiry, a PP goal ending a minor, coincidental minors, the 5v3 floor, majors not ending on a goal, 3v3 OT plus penalties) is deterministic GameState mechanics, not a model. It is unit-tested, not bake-offed.

---

## SS-R1: penalty hazard bake-off (pre-registered 2026-10-15 by the PM, before any run)

### Question

Which penalty-hazard model gives the best held-out likelihood of when penalties occur and who takes them, and does it reproduce G1 (TOI by strength state, PP opportunities per team-game) when run in a closed loop through GameState?

### Unit and target

- **Hazard rows:** one row per (game, team, interval). An interval is a maximal stretch of game clock with constant pre-event state (strength state, score diff bucket, period, the in-game penalty differential). Each row is cut at every state change and at every whistle-to-whistle boundary, with a 60 s maximum length. Exposure is seconds. The target is the count of **penalty-taking events** by that team in the interval.
- A penalty-taking event is a penalty-family event in `data/processed/events` that puts at least one player of the team in the box with time that changes on-ice strength, OR a coincidental minor/major pair (these are counted for both teams and typed as coincidental). Misconducts and game misconducts with no strength effect, and penalty shots, are tallied separately in the report and are not part of the target. The worker documents the exact mapping from `pen_type`/`pen_desc`/`pen_minutes` to the target classes in `features.md`, and a test fails on any unmapped `pen_type`/`pen_desc` combination (LEARNINGS L13 pattern).
- **Type rows:** for each penalty-taking event, the class in {minor, double minor, major (5), coincidental-offsetting, minor + penalty shot awarded (counted as minor)}. The type mix is a secondary sub-model (T arms below).
- EN state: intervals with a goalie pulled are included, with the goalie state as a feature level. G1 reports EN TOI separately and labels it **STUB-DEPENDENT** until the stage-8 goalie-pull model exists.
- Shootouts are excluded. OT (3v3 regular season, 5v5 playoff) intervals are included, with period type as a feature.

### Ratings (as-of, shared by arms that use them)

- Per team, as-of each game date, using only games with puck drop strictly before that date: penalties-taken per 60 and penalties-drawn per 60 at all strengths, as log rates **relative to the snapshot's league mean** (L1). Raw levels are banned.
- Shrinkage is a gamma-Poisson (empirical Bayes) toward the league mean. Season carry-over is the prior from last season's final value with weight w. The prior strength and w are tuned on fold 1 only, from the grid w in {0.3, 0.5, 0.7} and prior strength in {200, 600, 1800} team-minutes, then frozen.
- Player-level penalty rates are **out of scope for SS-R1**. They belong to stage 2 (deployment) and are logged as a candidate for SS-R2.

### Hazard arms

| Arm | Model | Features |
|---|---|---|
| H0 | piecewise-constant league rate | season x strength state (5v5, PP-for, PK, 4v4, 3v3, other) x period type (REG, OT) |
| H1 | Poisson GLM, log link, exposure offset | H0 cells + team taken-rating + opponent drawn-rating + home + rest/back-to-back (both teams) |
| H2 | H1 + game-state terms | H1 + pre-event score diff bucket {<=-2, -1, 0, +1, >=+2} from the team's view + period (1/2/3/OT) + last-5-min-of-3rd flag x score bucket + pre-event in-game penalty differential bucket {<=-2, -1, 0, +1, >=+2} ("make-up call" effect) |
| H3 | LightGBM Poisson | the same feature set as H2 plus continuous game clock. The hyperparameters (num_leaves in {7, 15}, min_data_in_leaf in {200, 800}, learning_rate 0.05, early stopping on a fold-1 time-ordered inner split) are tuned on fold 1 only, then frozen |

H2 and H3 consume engine-fed state (score diff, penalty differential), so the closed-loop gate below is mandatory for them (L3).

### Type arms (secondary; same folds and grading)

| Arm | Model |
|---|---|
| T0 | season-level league multinomial |
| T1 | multinomial logit: season + strength state + score diff bucket + period |

### Folds

Per CLAUDE.md. Fold 1 trains through 2022-23 and tests 2023-24; it is for hyperparameters only. Fold 2 trains through 2023-24 and tests 2024-25; it is the SELECTION fold. 2025-26 is sealed and loaded only through `src/nhl_sim/data/load.py`. 2021-22 is training data and the carry-over prior source.

### Primary metric (fold 2)

The held-out Poisson log-likelihood per game of the penalty-taking counts across all hazard rows, as the difference vs H0 (higher is better). It is computed by one grading script (`scripts/grade_strength_state.py`) with the arm labels hashed until the table is final.

### Noise floor and decision rule

- GLM arms are deterministic. Their uncertainty is a **game-block bootstrap** (1,000 resamples of fold-2 games) of the paired per-game log-likelihood difference between two arms.
- H3 is also retrained under a second seed. Its seed-retrain difference is the seed noise floor.
- An arm beats a simpler arm only if the paired difference is > 2 bootstrap SE AND > the H3 seed-retrain |difference| (for H3 comparisons). Otherwise the simpler arm wins (H0 < H1 < H2 < H3 in complexity).
- The offline winner is provisional until the closed-loop gate passes. If the offline winner fails the closed-loop gate and a simpler arm passes, the simpler arm is selected and the failure is written up as a finding.
- The type sub-model uses the same rule (T0 simpler than T1), with multinomial log-likelihood per penalty.

### Secondary metrics (reported, never deciding)

At every level the multi-level rule requires, for the fold-2 winner and runner-up:
- Calibration: predicted vs actual penalties per team-game by decile of predicted rate.
- **Responsiveness:** predicted vs actual penalties taken per 60, bucketed by team taken-rating quintile and by opponent drawn-rating quintile. It must slope, not sit flat.
- By strength state, by score diff bucket, by period, home vs away, and per team (32 rows, n labelled; cells under `min_cell_n` are UNDERPOWERED).

### Closed-loop gate (G1, mandatory before selection is final)

- Run the GameState engine with the selected hazard and type models and the rulebook mechanics, over fold-2 games, for at least 200 seeds per game. A seed-count check reports how stable the G1 numbers are at 100 vs 200 seeds.
- Downstream stages do not exist yet. Goals are drawn from a **labelled stub**: league per-season goal rate per strength state, from fold-2 TRAIN data, constant per state, no team terms. Its only purpose is to end PP minors at the right frequency, and it is not graded. There is no goalie pull, so EN TOI is STUB-DEPENDENT. OT is 3v3 for 5 min (regular season) with the stub goal rate. The SO is skipped (no strength effect).
- Score diff for H2/H3 comes from the stub goals. Because the stub goals are not team-matchup-specific, score-state terms are exercised but not validated here; they are re-gated when stage 6 lands. This is recorded in the results.
- G1 quantities vs `gate_targets_2024-25` (the worker extends `build_gate_reference.py` to add them if absent):
  - TOI per game by strength state (5v5, PP, PK, 4v4, 3v3, 5v3/3v5);
  - PP opportunities per team-game (mean, SD, P(k) for k = 0..7+), overall and per team;
  - penalty minutes per game;
  - the share of minors ended by a PP goal.
- Tolerances come from `docs/gates.yaml` `g1_*`. Any G1 cell that fails because of the stub is labelled STUB-DEPENDENT with the reason, never PASS.

### Engine work in scope (unit-tested, not bake-offed)

`src/nhl_sim/engine/`: GameState arrays over (games x seeds), the clock, the period/OT structure, the penalty box queue with rulebook mechanics (minor 120 s, double minor 2 x 120 s with the second minor surviving a goal, major 300 s, a PP goal ending the oldest expirable minor of the shorthanded team, coincidental minors per the current NHL rule incl. the 5v5 exception, the 3-skater floor with a stacked-penalty queue, OT 3v3 penalty -> 4v3 / 5v3). There are rule-era flags in GameState. RNG is seeded on (seed, game_id, family). The tests cover every rule with a hand-built sequence, and the empirical check is that replaying the real penalty/goal sequence of a fold-1 sample through the mechanics reproduces the real strength-state timeline (agreement >= 99% of seconds, with disagreements listed).

### Results

(append below this line)
