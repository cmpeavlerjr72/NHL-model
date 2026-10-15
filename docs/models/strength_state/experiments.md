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

#### SS-R1 results (Lane H, 2026-10-15; full report `docs/tests/strength_state_ss_r1_2026-10-15.md`)

- Engine mechanics: unit-tested (`tests/engine/`). Fold-1 replay over 4,201 games: gap-aware agreement 99.993%, strict carry-forward 98.13%. 99.65% of the strict misses fall inside ambiguous event gaps of the event-sampled pbp code. Rule gaps fixed: consecutive service by one player, the OT hold applying only to an outnumbered team, and expire-before-events timing.
- Row construction: the first build used run-relative 60 s chunks, which leaked row length into the H3 clock. It was replaced by fixed-minute-grid cuts before any fold-2 number existed.
- Frozen on fold 1: w = 0.7, prior strength 1800 (grid corner); H3 num_leaves 7, min_data_in_leaf 800, 490 rounds.
- Fold 2, LL/game vs H0: H1 +0.052 (SE 0.010), H2 +0.510 (0.032), H3 +0.932 (0.038). H3 vs H2: +0.422 (0.032). Seed floor 0.0067. Every arm beats every simpler arm. **Offline winner H3.** Type: T1 minus T0 +0.046 (SE 0.012), **T1.**
- G1 at 200 seeds (stub goals): H3 passes every toleranced overall cell. PP opps per team-game 2.733 vs 2.584 (+0.149, tol 0.15); the 50-seed slice gave +0.156. The RS segment FAILS (+0.166). 3v3 TOI, EN TOI and the share of minors ended by a PP goal are STUB-DEPENDENT. H2 passes overall and on RS (+0.101 / +0.119). **Literal rule: H3 selected, provisional.**
- Findings (not decided here): (1) season-level drift, with every arm over-predicting 2024-25 by about 10%; (2) delayed-penalty reverse causality, where about 80% of the 6.4% of events in the goalie-pulled state follow a delayed-penalty signal and the sim never visits that state; (3) the G1 PP pass is a partial cancellation of (1) and (2). Recommended next experiment: SS-R2.

---

## PM ruling on SS-R1 (2026-10-15, D12)

- The literal rule selects H3 (hazard) and T1 (type). **H3 is NOT confirmed.** Its G1 PP-opportunity pass (2.733 vs 2.584, tolerance 0.15, inside by 0.001) comes from two known biases partly cancelling. Season-level drift over-predicts by about 10%, and the delayed-penalty goalie-pull states the sim never visits under-predicts by about 6%. A passing aggregate over a biased sub-model is a failure (CLAUDE.md, bottom-up rule). The regular-season-only cell also fails for H3 (2.730 vs 2.564).
- H3's offline lead over H2 (+0.42 log-lik per game, 13 SE) is recorded as real. H3 stays the arm to beat in SS-R2.
- Mechanics replay: the gap-aware measure (99.993%) is the one the 99% bar binds, because seconds inside undatable pbp gaps cannot be scored. The strict carry-forward measure (98.13%) is reported alongside it from now on.
- Status: strength_state stays TESTING. No arm ships.

## SS-R2: penalty hazard with the two SS-R1 biases fixed (pre-registered 2026-10-15 by the PM, before any run)

### Changes vs SS-R1 (shared by every arm; everything not listed here is unchanged)

1. **Delayed-penalty state.** When a penalty-taking event follows a delayed-penalty signal against the same team, its pre-event state is the state at the signal, before the pull. The seconds between the signal and the whistle are hazard exposure in that pre-signal state, not 'other'. Penalties that occur with a goalie pulled and no preceding signal (a trailing-team pull) keep state 'other'; they are counted and reported, and they wait for the stage-8 pull model. The delayed-penalty 6v5 itself is an engine mechanic, logged as a stage-8 candidate, not part of SS-R2.
2. **In-season league level.** Every arm (including H0, which becomes H0' = H0 cells x this level) gets an as-of league penalty level for the current season:
   - log(league rate in the season to date before this game date, gamma-shrunk toward the previous season's final rate with strength k in league-games), as a log ratio vs the previous season's final rate;
   - k is tuned on fold 1 only, from {50, 150, 450}, then frozen;
   - season dummies are removed from H1-H3 (they cannot extrapolate to a held-out season), and H0' keeps the strength-state x period-type cells.
3. **Rating grid extended** because the SS-R1 choice sat on the corner: w in {0.7, 0.85, 1.0} and prior strength in {1800, 5400} team-minutes, tuned on fold 1 only.

### Arms

H0', H1', H2', H3' = SS-R1's H0-H3 with changes 1-3. The H3' hyperparameter grid is the SS-R1 one. T1 carries over unchanged; it is not re-raced.

### Metric, folds, noise floor, decision rule

Identical to SS-R1 (fold 2 selects; game-block bootstrap with 1,000 resamples; H3' seed retrain; > 2 SE and > the seed floor; simpler wins ties; complexity H0' < H1' < H2' < H3').

### Bias checks (pre-registered; every one must pass before the closed-loop result is read as clean)

- **Season level:** predicted / actual penalty-taking events per team-game on fold 2, overall and by month. Pass is within +/-3% overall, with no month beyond +/-8% at n >= 100 games (smaller months UNDERPOWERED).
- **State 'other':** the share of fold-2 events in state 'other' after change 1 is reported, and the sim-vs-real shortfall attributable to it is <= 1.5%.

### Closed-loop G1

As in SS-R1: 200 seeds, the same labelled goal stub, and the 100- vs 200-seed stability check. G1 cells are reported **separately for the regular season and the playoffs** (like-for-like rule), as well as overall. A pass requires the regular-season cells to pass. Playoff cells under min_cell_n are UNDERPOWERED. Per-team PP opportunities are reported with n and labelled.

### Results

(append below this line)

#### SS-R2 results (Lane H2, 2026-10-15; full report `docs/tests/strength_state_ss_r2_2026-10-15.md`)

- Change 1 (delayed-penalty state, `delayed.py`, tables `*_v2*`): fold-2 events in state 'other' 590 (6.36%) -> 143 (1.54%); the residual is trailing-team pulls (123 in the last 3 min of regulation, 17 in OT). Test `tests/test_delayed_penalty_state.py`.
- Change 2 (as-of league level, fixed offset in every arm, no season dummies; 2021-22 level 0 for want of a prior season) and change 3, frozen on fold 1: k = 50, w = 1.0, prior strength 1800 (all grid corners; grid not extended). H3' num_leaves 7, min_data_in_leaf 800, 429 rounds.
- Fold 2, LL/game vs H0': H1' +0.051 (SE 0.011), H2' +0.262 (0.020), H3' +0.345 (0.020); H3' vs H2' +0.084 (0.012); seed floor 0.00025. **Offline winner H3'** (literal rule), runner-up H2'. T1 carried over, not re-raced.
- SS-R1's H3 lead was mostly the delayed-penalty artefact: 0.27 of its 0.42 nats/game over H2 (and 0.36 of H2's 0.51 over H0) came from 'other'-state rows.
- Bias checks: **FAIL for every arm.** Season level overall: H0' +2.4%, H1' +2.7%, H2' +2.5% PASS; H3' +3.08% FAIL. By month: January 2025 fails in every arm (+10.5% to +11.2%, n = 224 games); all other months with n >= 100 pass. 'Other' shortfall: net -0.3% to +0.1% PASS (raw share 1.54%, upper bound).
- Closed-loop G1: **NOT RUN** (the brief bars the closed loop on an arm that fails a bias check; H3' and H2' both fail). No G1 cell has a status other than NOT RUN. Status stays TESTING.

---

## PM ruling on SS-R2 (2026-10-15, D13)

- The result is accepted as reported. H3' wins offline (+0.084 over H2', 7 SE). Every arm fails the bias checks: January 2025 runs +10.5% to +11.2% at n = 224 games (about 4 SE), and H3' runs +3.08% overall. G1 was correctly not run. strength_state stays TESTING.
- The 'other' check binds on the net shortfall attributable to that state, as worded, and it passes. The raw share (1.54%) is reported, not gated.
- Grid: w = 1.0 is the natural maximum of a carry weight, not a grid defect. Prior strength 1,800 is interior across SS-R1 + SS-R2 (200 to 5,400). Only k = 50 is a true corner, and SS-R3 extends it.
- Forking-paths guard: SS-R3 is the third fold-2-informed respec. Every SS-R3 bias check is therefore also reported on fold 1, and a fix counts only if it removes the monthly bias on fold 1 as well. If SS-R3 still fails, the PM decides between accepting an arm with its biases listed and stopping work on stage 1. No SS-R4 is pre-authorised.

## SS-R3: in-season seasonality profile (pre-registered 2026-10-15 by the PM, before any run)

### Change vs SS-R2 (everything else identical, incl. the T1 carry-over)

- **Season-phase profile p(b).** The bins are b in {Oct, Nov, Dec, Jan, Feb, Mar, Apr (regular season), playoffs}.
  - It is estimated from TRAINING seasons only, as the log ratio of each season's league penalty-taking rate in bin b to that same season's full-season rate, averaged across training seasons with equal weight.
  - It enters every arm as a fixed offset.
- **De-seasonalised level.** The as-of in-season league level from SS-R2 is computed on profile-adjusted exposure (observed count / count expected under p), so October's high rate no longer lifts the season-to-date mean.
- k is re-tuned on fold 1 only, from {15, 50, 150}. w and the prior strength stay frozen at the SS-R2 values (1.0, 1,800).

### Arms

H0''-H3'' are SS-R2's H0'-H3' with the change. The SS-R2 arms are carried as the no-profile comparators; they are not refit.

### Metric, noise floor, decision rule, bias checks

These are identical to SS-R2. The bias checks are additionally reported on fold 1, as a diagnostic; the fold-2 checks gate. A profile arm is preferred over its SS-R2 twin only if it passes the bias checks the twin failed and its fold-2 log-likelihood is not worse by more than 2 SE.

### Closed-loop G1

This is the same as SS-R2, for the selected arm and the next simpler arm that passes the bias checks.
- The engine hazard lookup takes the per-game level and profile offsets. It must be built, with a unit test that the offsets reproduce the offline predicted rate for a sample of games to within 0.5%.
- The G1 runs may go to Lane O; otherwise they run locally.

### Results

(append below this line)
