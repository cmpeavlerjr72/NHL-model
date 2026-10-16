# Shot-attempt generation: features (SA-R1)

Built by `scripts/build_shot_attempt_tables.py` (code: `src/nhl_sim/shot_attempt/{tables,models}.py`, reusing Lane H's `strength_state.timeline` replay, `strength_state.delayed` (L20), `strength_state.tables.asof_ratings` / `assert_pregame` and `strength_state.seasonality`) into `data/processed/shot_attempt/*_v1*`. Every feature is the PRE-event state. Feature builders raise on missing inputs (L5). Ratings are relative to their snapshot league mean (L1).

## 0. Target: shot attempts

| pbp event (canonical) | typeDescKey | target? |
|---|---|---|
| SHOT | shot-on-goal | yes |
| MISS | missed-shot | yes |
| BLOCK | blocked-shot | yes, owned by the shooting team (L15; owner == `shooting_team_id` asserted for every attempt) |
| GOAL | goal | yes |
| any of the above with pbp situation code 0101 / 1010 outside the shootout | | no: penalty shot, tallied |
| any of the above with period type SO | | no: shootout, tallied |
| FAILED_SHOT_ATTEMPT (shootout / penalty-shot miss, family "shootout") | | no, tallied |

`tables.ATTEMPT_TYPE_MAP` is explicit, and `check_event_types` raises on any event type not in `pbp.event_map.EVENT_MAP` and on any attempt whose (event, typeDescKey) pair is not in the map (`tests/test_shot_attempt_tables.py`).

Exclusion tallies (`exclusions_v1.json`):

| season | target attempts | penalty-shot attempts (goals) | shootout attempts | FAILED_SHOT_ATTEMPT events | delayed-state seconds changed |
|---|---|---|---|---|---|
| 2021-22 | 159,791 | 36 (9) | 747 | 0 | 5,491 |
| 2022-23 | 163,714 | 57 (17) | 645 | 27 | 5,765 |
| 2023-24 | 170,602 | 47 (17) | 607 | 13 | 5,804 |
| 2024-25 | 167,020 | 30 (7) | 508 | 7 | 4,588 |

Both goalies pulled at once: 0 seconds in every season (the mapping exists and is labelled: EN-for for both teams).

## 1. Source manifest

| Feature | Dtype | Source | Computation | Fallback | Notes |
|---|---|---|---|---|---|
| `y` | int | events | the team's attempts whose second t has t-1 inside the row (t = 0 -> row 0) | none | target; `y_goal` = goals among them (goal-stub source), `y_opp` = the opponent's attempts in the same interval |
| `exposure_s` | int | replay timeline | seconds in the row (offset) | none | rows cut at every change of the 7-level strength state (either team's view), the 7-level score bucket, period, last-5 flag, and on the fixed game-clock minute grid (<= 60 s). Not cut at whistles |
| `st` | int 0-6 | engine replay of the real penalties + pbp goalie digits, L20 delayed fix | team view: 0 5v5, 1 PP (5v4, 5v3, 4v3), 2 PK, 3 4v4, 4 3v3, 5 EN-for (own goalie pulled), 6 EN-against (opponent's pulled) | none | inside a delayed-penalty signal window the goalie digits are the pre-signal ones (`delayed.apply_delayed_fix`) |
| `sc` | int 0-6 | GOAL events (SO excluded) | team-view score diff bucket {<=-3, -2, -1, 0, +1, +2, >=+3}, pre-event | none | |
| `period` | int 1-4 | clock | 4 = any OT | none | |
| `ptype` | int | clock | 0 regulation, 1 OT | none | |
| `last5` | 0/1 | clock | game second in [3300, 3600) | none | |
| `own_r` | float | `ratings_grid_v1` | own as-of log attempts-FOR rate in the row's strength group, relative to the snapshot league mean | none (raise) | groups: ES = 5v5 + 4v4 + 3v3, PP, PK; EN rows use the ES ratings (labelled) |
| `opp_r` | float | `ratings_grid_v1` | opponent's as-of log attempts-AGAINST rate in the opponent's group (ES -> ES, own PP -> opponent PK, own PK -> opponent PP) | none | |
| `is_home` | 0/1 | rows | | none | |
| `b2b_own`, `b2b_opp` | 0/1 | `strength_state/team_game_v2.parquet` (Lane H) | played the previous calendar day | first game in the data: 0 | the "rest/back-to-back" term is the b2b flag only (labelled) |
| `level` | float | `league_level_v1_f{1,2}` | `level_k` + `p(bin)` (SS-R3 method on total attempts per team-hour), fixed offset, coefficient 1 | 2021-22 level 0 | see section 3 for the defect found |
| `arena_f` | float | `arena_v1` | as-of shrunk log ratio of attempts recorded at the arena to attempts expected from both teams' ratings, all earlier-dated games | first games of the data: 0 | A5 / A3 only |
| `clock` | int | rows | game minute `t0 // 60`, constant within a row | | A3 only; minute resolution so the engine lookup (minute grid) can serve it (labelled reading of "continuous game clock") |
| `cell` | int | derived | st x ptype | none: an unseen cell raises | GLM arms; 0.5 pseudo-event toward the pooled rate per cell (Lane H code) |
| `own_rf_es`, `opp_ra_es` | float | ratings | own ES-for and opponent ES-against ratings | | responsiveness bucketing only |

## 2. As-of tables

- **Ratings** (`ratings_grid_v1.parquet`, columns `rf_<g>_w<w>_b<b>` and `ra_<g>_w<w>_b<b>`, g in es/pp/pk): Lane H's `asof_ratings` applied per group to (attempts for, attempts against, minutes in the group). Gamma-Poisson: prior = league rate x exp(w x last season's final relative value), strength b team-minutes in the group; 12 grid points (w in {0.5, 0.7, 0.85, 1.0} x b in {600, 1800, 5400}). Writer: `created_at` = latest puck drop used + 6 h; `assert_pregame` raises unless `created_at < puck_drop`.
- **Profile and level** (`profile_v1_f{1,2}.json`, `league_level_v1_f{1,2}.parquet`): `seasonality.estimate_profile` / `asof_level_adj` with the rate = all target attempts per team-hour. Fold-2 profile: Oct -0.004, Nov -0.007, Dec -0.008, Jan +0.000, Feb +0.010, Mar -0.005, Apr -0.012, PO +0.045 (attempts are much less seasonal than penalties). k in {15, 50, 150}; `created_at < puck_drop` asserted.
- **Arena** (`arena_v1.parquet`, built at the frozen w = 0.85, b = 600): arena = home team id, or the venue string for neutral-site games (labelled). Expected attempts of a past game = sum over teams and groups of minutes x R_g x exp(rf_g(team) + ra_g'(opp)), with R_g the league group rate of that game's season from games dated before the factor's game (to date for the current season, full season for earlier ones). Factor = log((A + c) / (E + c)), all earlier-dated games at the arena, c = 1,200 pseudo-attempts (about 10 games; labelled, not tuned). SD across games 1.3-2.1% per season. Known attenuation: the home team's own ratings already contain half its home games' recording effect.

## 3. Defect found in the shared level (SA-R1 result; not fixed here)

The SS-R3 level is log(season-to-date rate / previous season's final rate). As a fixed offset pooled over several training seasons its reference changes each season, so the cell effects learn a blend of past season rates and the test season inherits the product of the earlier season-to-season ratios. With de-seasonalised attempt rates rising 2.3% (2022-23) and 4.5% (2023-24), every arm under-predicts fold 1 by about 2% and fold 2 by about 5%. Anchoring the level to one fixed reference (adding log(r_prev / r_first), completed seasons only) moves fold-1 A0 from -2.03% to +0.22% (`scripts/diag_shot_attempt_level_anchor.py`, fold 1 only). A second, separate drift: PK attempts run +7.5% to +8.2% on fold 1 in every arm (+10% under the anchored level), a strength-specific level change that one all-state level cannot carry.

## 4. Rejected / not used

- Cutting rows at whistles (Lane H's penalty rows): not needed for attempts; rows are cut on state changes and the minute grid only.
- Rest days beyond the b2b flag: not built (b2b is the pre-registered candidate's literal content; labelled).
