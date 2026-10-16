# Strength-state / penalty process: features (SS-R1, SS-R2 changes in section 4)

Built by `scripts/build_strength_state_tables.py` (code: `src/nhl_sim/strength_state/{penalty_map,events,timeline,tables,models}.py`) into `data/processed/strength_state/*_v1*`. Every feature is the PRE-event state; feature builders raise on missing inputs (L5); ratings are relative to their snapshot league mean (L1).

## 0. Target: penalty-taking events

Source: `data/processed/events` rows with `event == PENALTY`, `period_type != SO`.

### pen_type / pen_minutes -> class (`penalty_map.TYPE_MINUTES`)

| pen_type | pen_minutes | class | strength effect | target? |
|---|---|---|---|---|
| MIN | 2 | minor | 120 s, ends on a PP goal | yes |
| BEN | 2 | minor (bench minor, served by a skater) | same | yes |
| MIN | 4 | double | 2 x 120 s (PP goal in first half ends the first part only) | yes |
| BEN | 4 | double | same | yes |
| MAJ | 5 | major | 300 s, never ended by a goal | yes |
| MAT | 5 | major (match) | 300 s | yes |
| MAT | 10 | major ("match-penatly-10-minutes"; pbp situation codes show a 5-minute, goal-proof strength effect) | 300 s | yes |
| MIS | 10 | misconduct | none | no, tallied |
| GAM | 0 / 10 | game misconduct | none | no, tallied |
| PS | 0 | penalty shot awarded | none (no box time) | no, tallied |

The allowed `pen_desc` per `pen_type` is an explicit list (`penalty_map.KNOWN_DESC`, 82 combinations seen in 2021-22 to 2024-25 and 2026-27; 2025-26 sealed and unread). `tests/test_penalty_map.py` fails on any unmapped type/minutes or type/desc combination. "minor + penalty shot awarded" from the spec appears in the data as a PS row (0 min, tallied) plus, when one is assessed, a separate MIN row (counted as a minor).

### Per-stoppage resolution (`events._resolve`)

All strength penalties at one (game, game_time_s) are one stoppage:
1. Majors cancel majors one for one (no cross-category cancellation: a minor vs a major both stand; pbp codes confirm).
2. Minor units cancel one for one (double = 2 units; singles cancelled before doubles; a half-cancelled double becomes a minor).
3. A stoppage with any cancellation gives ONE `coincidental` event for EACH team; `smp` (5v5 exception) is set when the stoppage holds exactly one single minor per team and nothing else; the bundle's PIM is kept for the engine.
4. Each serving player's uncancelled penalties at the stoppage are served consecutively (majors first) and form ONE event: minor+minor -> `double`, anything with a major -> `major`, single minor -> `minor` (`n_raw` keeps the raw count). Consecutive-service key: `pen_committed_by`, else `pen_served_by` (bench minors).

Class counts 2021-22 to 2024-25: minor 31,853, coincidental 7,238 (3,619 stoppages x 2), double 515, major 149.

## 1. Source manifest

| Feature | Dtype | Source | Computation | Fallback | Notes |
|---|---|---|---|---|---|
| `y` | int | events | penalty-taking events of the team assigned to the row holding second t-1 (t = event second; t=0 -> row 0) | none | target |
| `exposure_s` | int | replay timeline | seconds in the row (offset) | none | rows cut at every state change, at whistle seconds (STOPPAGE, GOAL, PENALTY, PERIOD_START), and on the fixed game-minute grid (<= 60 s) |
| `st` | int 0-5 | replay + pbp goalie | team view: 5v5, PP, PK, 4v4, 3v3, other (either goalie pulled, pbp carry-forward) | none | penalty-derived skaters from the GameState replay |
| `ptype` | int | clock | 0 REG, 1 OT (game second >= 3600) | none | |
| `period` | int 1-4 | clock | 4 = any OT | none | |
| `sc` | int 0-4 | GOAL events | team-view score diff bucket {<=-2, -1, 0, +1, >=+2}, pre-event | none | |
| `last5` | 0/1 | clock | game second in [3300, 3600) | none | H2 interacts with `sc` |
| `pdiff` | int 0-4 | target events | own minus opponent penalty-taking events so far, bucketed like `sc` (coincidental counts both: net 0) | none | "make-up call" term |
| `taken_own` | float | `ratings_grid_v1` | as-of log penalties-taken rate of the team, relative to the snapshot league mean | none (raise) | gamma-Poisson; prior = league mean x exp(w x last season's final relative value), strength b team-minutes; frozen w=0.7, b=1800 |
| `drawn_opp` | float | `ratings_grid_v1` | same for the OPPONENT's penalties-drawn rate | none | |
| `is_home` | 0/1 | rows | | none | |
| `b2b_own`, `b2b_opp` | 0/1 | `team_game_v1` | played the previous calendar day (RS + PO games table) | first game of the data: 0 (no previous game) | |
| `season_f` | int | rows | season; the held-out season is mapped to the last training season | | for H0 cells, GLM cells, H3, T0, T1 alike |
| `clock` | int | rows | game minute of the row (`t0 // 60`), constant within a row | | H3 only; see the row-construction leak note below |
| `cell` | int | derived | season_f x st x ptype | season-pooled (st, ptype) effect for a test cell absent from training (2024-25 3v3 in regulation) | GLM arms; 0.5 pseudo-event toward the pooled rate per cell |

Ratings writer: `created_at` = latest puck drop of the games used + 6 h; `assert_pregame` raises unless `created_at < puck_drop` for every row with data (season-opening rows use only the prior, whose `created_at` is last season's final game + 6 h).

## 2. Feature sets tested (SS-R1)

| Set | Features | Arm |
|---|---|---|
| cells | season_f x st x ptype | H0 |
| ratings | cells + taken_own + drawn_opp + is_home + b2b_own + b2b_opp | H1 |
| game state | ratings + sc dummies + P2/P3 + last5 x sc + pdiff dummies | H2 |
| game state + clock | H2 set + clock, LightGBM Poisson (st categorical) | H3 |
| type T0 | season_f | T0 |
| type T1 | season_f + st + sc + period (multinomial logit, unpenalised) | T1 |

## 3. Rejected / not used

- Run-relative 60 s chunking with a row-midpoint clock (first build): rows end at the event's whistle, so a within-run clock leaked the row length to H3 (60 s full chunks starting at period starts had midpoint 30 and y = 0 by construction). Replaced before any fold-2 number was produced by cuts on the fixed minute grid and a per-row constant game-minute clock.
- Player-level penalty rates: out of scope for SS-R1 (candidate for SS-R2, stage 2).
- Delayed-penalty pre-event state: NOT implemented in SS-R1 (spec says the goalie state is a feature level). Finding for SS-R2: about 80% of the 6.4-6.8% of events whose pre-event state is `other` follow a delayed-penalty signal against the same team (goalie pulled because of the penalty itself).

## 4. SS-R2 changes (tables `*_v2*`; code `delayed.py`, `league_level.py`, `models_r2.py`)

| Feature | Change | Source / computation | Notes |
|---|---|---|---|
| `st` | delayed-penalty state | Inside every delayed-penalty signal window, the goalie digits of the pbp carry-forward code are replaced by the code of the last event before the signal. The window runs from the signal second up to (not including) the first STOPPAGE / GOAL / PENALTY / PERIOD_END / GAME_END after it. Skater counts stay the engine replay. | A goalie already pulled before the signal stays pulled. The signal event's own code is not used, because pbp sometimes stamps it post-pull. Windows: `delayed_windows_v2.parquet`. Fold-2 'other' events: 6.36% -> 1.54% |
| `level` | new, every arm, fixed offset (coefficient 1) | `league_level_v2.parquet` `level_k{50,150,450}`: log((E + 2k r_prev) / (H + 2k) / r_prev), with E and H the current season's events and team-hours in games with an earlier date and r_prev the previous season's final rate per team-hour | `created_at` = last puck drop of the previous date + 6 h, `created_at < puck_drop` asserted. 2021-22 = 0 (no prior season in the data). Frozen k = 50 |
| `season_f` | removed | | GLM `cell` = st x ptype, pooled over training seasons; H3' features = `models_r2.LGB_FEATURES` |
| `taken_own`, `drawn_opp` | grid extended | `ratings_grid_v2.parquet`: w in {0.7, 0.85, 1.0}, prior strength in {1800, 5400} | frozen w = 1.0, b = 1800 |
| type rows `st` | follows the new `st` | `type_rows_v2.parquet` | T1 not re-raced (SS-R1 fit carried over) |

## 5. SS-R3 changes (tables `*_v3_f{1,2}*`; code `seasonality.py`, `models_r2.attach_features(profile_fold=)`)

| Feature | Change | Source / computation | Notes |
|---|---|---|---|
| `p(b)` season-phase profile | new, every arm, fixed offset (coefficient 1) | `profile_v3_f{1,2}.json`: mean over TRAINING seasons of log(bin rate / same-season full rate); bins Oct..Apr (RS by game-date month; the one May RS game in Apr) and PO | fold 1 trains 2021-23, fold 2 trains 2021-24. Full rate = all games of the season |
| `level` | now de-seasonalised | `league_level_v3_f{1,2}.parquet` `level_k{15,50,150}`: SS-R2 formula with events divided by exp(p(bin)) for the season-to-date count and for r_prev | arm offset = level_k + p. `created_at < puck_drop` asserted. 2021-22 = 0. Frozen k = 15 |
| everything else | unchanged from SS-R2 | w = 1.0, prior strength 1,800, v2 rows and ratings, T1 carried over | H3'' LightGBM: num_leaves 7, min_data_in_leaf 200, 378 rounds (`ss_r3_frozen_params.json`) |
