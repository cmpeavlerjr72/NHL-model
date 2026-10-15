# NHL API data audit (INV-1 / INV-2), 2026-10-15

Lane A worker (Sonnet). Source: public NHL API (`api-web.nhle.com/v1` schedule / play-by-play / boxscore, `api.nhle.com/stats/rest/en/shiftcharts`). Seasons 2021-22 through 2026-27 to date (pull ran 2026-10-15; 2026-27 has 107 final games, through 2026-10-14). Regular season (RS, gameType 2) and playoffs (PO, gameType 3). Preseason excluded.

Reproduce: `py -3.12 -m venv .venv; pip install -e .[sim,dev]`, then `scripts/pull_schedule.py`, `scripts/pull_games.py` (resumable; cached under `data/raw/nhl_api/`, gitignored), `scripts/build_tables.py`, `scripts/build_verified_finals.py`, `scripts/diag_nhl_api_audit.py <out.md>`. Code: `src/nhl_sim/clients/nhl_api.py`, `src/nhl_sim/pbp/{event_map,tables,shift_cov}.py`.

## Headline

- Pull is complete: 7,100 final games x (pbp, boxscore, shift chart), 0 failures, 3.1 GB raw JSON. Measured rate 5.6 games/s on a 200 s slice (3 requests per game, 4 concurrent); full pull took about 23 min wall (14:29 to 14:52 local).
- Finals: all 7,100 games agree on score and REG/OT/SO across the schedule endpoint, the boxscore and pbp-accumulated goals (0 primary disagreements). Caveat: all three are views of one NHL feed, so this is internal consistency, not independence. A non-NHL second source (e.g. ESPN) was NOT checked; CLAUDE.md asks for a second source, so this item is PARTIAL.
- Shot coordinates: present on 100% of shot attempts, all seasons.
- Shift charts: present for every game except 57 games in 2024-25 (all dated 2025-04-08 or later) and 48 of the first 107 games of 2026-27 (2026-09-30 to 2026-10-07). Re-requested on 2026-10-15: still empty. Where present, shift-derived skater counts match the pbp situationCode in 96-97% of regulation seconds and 98-99% of pbp-5v5 time.
- Goalie starter flag exists in every boxscore (exactly 1 per team-game) and matches the first goalie to face a shot in 99.96-100% of team-games. It is post-game data: the API has no pregame confirmed starter.

## Findings that matter for modelling

1. **Coordinates.** x in [-99, 99], y in [-42, 42]. They are raw rink coordinates, NOT attack-normalised: the sign of x follows `homeTeamDefendingSide` (section 4: zone=O shots have positive raw x for 100% of home shots when home defends left and 0% when home defends right; mirrored for away). `homeTeamDefendingSide` flips every period (P1 to P2 in 99.99% of RS games, P2 to P3 and P3 to OT in 100%) and is present on every play. Events table: `x_norm, y_norm` = coordinates with the event owner attacking +x (both axes sign-flipped, a 180 degree rotation); `sx, sy` = same, for shot attempts, in the shooting team's frame.
2. **Blocked shots.** `eventOwnerTeamId` is the SHOOTING team, x/y are already in the shooter's frame (99.6% have sx>0), but `zoneCode` is relative to the BLOCKING team (94% 'D'). Do not use `zone` for blocks; use coordinates. (An initial build assumed owner = blocker; corrected and rebuilt before this audit.)
3. **Event recording drift (rates per game, section 2).** Giveaways jump from 15.6 to 29.9 per game and takeaways fall from 14.0 to 9.5 between 2023-24 and 2024-25 (a recording change, not hockey); hits fall 47.5 to 42.5 over the span; shots on goal fall 57.6 to 47.9 per game while goals per game stay 6.1-6.4 and attempts per game stay 114-127 (SOG down, blocks 27.3 to 31-34 and misses 23.4 to 28-30 up). Treat shot-type rates and any giveaway/takeaway/hit feature as season-specific; centring on each snapshot's league mean (CLAUDE.md) is mandatory. `delayed-penalty` events roughly double from 2022-23 to 2023-24.
4. **Event vocabulary** is 16 types, all mapped in `src/nhl_sim/pbp/event_map.py`; a test fails on any unmapped type and the loader raises. `failed-shot-attempt` (shootout misses) first appears in 2022-23; how 2021-22 typed its shootout misses was not investigated. No unknown types in any season.
5. **Overtime.** Playoff OT is periods 4+ of 20 min; RS OT is a 5 min 3v3 period 4; SO is period 5 (`periodType` SO). `game_time_s` accounts for this.
6. **Puck drop.** `puck_drop_utc` is the SCHEDULED start (`startTimeUTC`); the API gives no actual drop time. Enough for `created_at < puck_drop`, not for in-game timing.
7. **Strength state** comes from `situationCode` (away goalie, away skaters, home skaters, home goalie). `strength_state` is from the event owner's view: `5v5/4v4/3v3`, `PP`, `PK`, `EN_FOR` (owner pulled its goalie), `EN_AGAINST`, `SO`. PP is not split into 5v4/5v3/4v3 in that column; raw `home_skaters/away_skaters` are in the table.
8. **Goalie box.** Goalie `goals_against` excludes empty-net goals (GA plus pbp empty-net goals equals the opposing score in all but 1 game). Goalies per team-game: 2 in 14,196, 1 in 3, 3 in 1.

## Does anything block `docs/FRAMEWORK_PLAN.md`?

- Not blocked: shot-attempt generation, shot location (full coordinates), shot outcome, strength-state / penalty process (type, minutes, drawn-by and committed-by are in `events`), faceoffs, deployment from shifts for 2021-22 to 2025-26 (minus 57 games in 2024-25).
- Gaps: (a) no pregame lineups or confirmed goalies in this API, so honest-backtest goalie knowledge needs another timestamped source (Lane B goalie log); (b) the 2026-27 shift gap (48 of 107 games) hurts any live deployment model until the API backfills; (c) on-ice players are not given per event and must be reconstructed from shifts (1-4% of regulation seconds will not match the pbp skater count; 2023-24 is worst, only 88% of games reach 95% 5v5 agreement); (d) the 2024-25 recording drift (finding 3) means priors on giveaways/takeaways/hits and shot classification are not exchangeable across 2023-24 to 2024-25; (e) no xG, rush or rebound flags (derive from event sequences); (f) 2025-26 is sealed per CLAUDE.md, but it is pulled and sits in the tables: the seal must be enforced where tables are read (not done in this lane).
- Open: independent second source for finals; 2021-22 shootout typing; shift-gap backfill (re-run `scripts/pull_games.py`; empty charts are re-tried automatically).

## Tables written

| table | path | rows |
|---|---|---|
| schedule | `data/processed/schedule.parquet` | 7,224 (incl. 124 future) |
| games | `data/processed/games.parquet` | 7,100 |
| events | `data/processed/events/events_<season>.parquet` | 2,253,128 |
| shifts | `data/processed/shifts/shifts_<season>.parquet` | 5,331,396 |
| player_box | `data/processed/player_box/player_box_<season>.parquet` | 255,541 |
| goalie_box | `data/processed/goalie_box/goalie_box_<season>.parquet` | 28,398 |
| verified finals | `data/reference/verified_finals_v1.parquet` | 7,100 (7,100 verified) |

Verified-finals disagreements. Primary (schedule vs boxscore vs pbp, score and end state): none. Secondary (per-player attribution, not final scores): skater-goal-sum differs from the box score in 6 games (2022020939, 2023020345, 2024020052, 2024020720, 2024020949, 2026020010) and goalie GA plus empty-net goals differs in 1 game (2021020368). Flags are in the `disagreements` column.

## Detailed tables (generated by `scripts/diag_nhl_api_audit.py`)

Season labels: 2021-22 is the 2021-22 season. Playoff games per year 82-89.

### 1. Games pulled vs expected

|    | season   | type   |   schedule_listed |   schedule_final |   pulled_pbp_box_shift | expected                   |
|---:|:---------|:-------|------------------:|-----------------:|-----------------------:|:---------------------------|
|  0 | 2021-22  | RS     |              1312 |             1312 |                   1312 | 1312                       |
|  1 | 2021-22  | PO     |                89 |               89 |                     89 | n/a (series length varies) |
|  2 | 2022-23  | RS     |              1312 |             1312 |                   1312 | 1312                       |
|  3 | 2022-23  | PO     |                88 |               88 |                     88 | n/a (series length varies) |
|  4 | 2023-24  | RS     |              1312 |             1312 |                   1312 | 1312                       |
|  5 | 2023-24  | PO     |                88 |               88 |                     88 | n/a (series length varies) |
|  6 | 2024-25  | RS     |              1312 |             1312 |                   1312 | 1312                       |
|  7 | 2024-25  | PO     |                86 |               86 |                     86 | n/a (series length varies) |
|  8 | 2025-26  | RS     |              1312 |             1312 |                   1312 | 1312                       |
|  9 | 2025-26  | PO     |                82 |               82 |                     82 | n/a (series length varies) |
| 10 | 2026-27  | RS     |               231 |              107 |                    107 | n/a (in progress)          |


### 2. Event-type vocabulary and drift (events per game)

| type_desc_key       |   2021-22 |   2022-23 |   2023-24 |   2024-25 |   2025-26 |   2026-27 |
|:--------------------|----------:|----------:|----------:|----------:|----------:|----------:|
| blocked-shot        |    27.283 |    29.789 |    34.371 |    33.688 |    31.323 |    31.430 |
| delayed-penalty     |     1.344 |     1.657 |     2.576 |     2.493 |     2.613 |     2.907 |
| faceoff             |    56.839 |    57.209 |    56.808 |    56.853 |    56.306 |    57.963 |
| failed-shot-attempt |     0.000 |     0.019 |     0.009 |     0.005 |     0.011 |     0.009 |
| game-end            |     1.000 |     1.000 |     1.000 |     1.000 |     1.000 |     1.000 |
| giveaway            |    18.173 |    17.519 |    15.591 |    29.876 |    30.825 |    33.430 |
| goal                |     6.378 |     6.448 |     6.266 |     6.155 |     6.339 |     6.411 |
| hit                 |    47.473 |    46.634 |    47.297 |    45.077 |    42.524 |    44.953 |
| missed-shot         |    23.387 |    24.732 |    27.289 |    29.349 |    29.994 |    28.626 |
| penalty             |     7.518 |     7.761 |     7.644 |     6.981 |     7.529 |     8.355 |
| period-end          |     3.291 |     3.304 |     3.267 |     3.266 |     3.338 |     3.280 |
| period-start        |     3.298 |     3.305 |     3.267 |     3.267 |     3.338 |     3.280 |
| shootout-complete   |     0.074 |     0.068 |     0.059 |     0.055 |     0.085 |     0.075 |
| shot-on-goal        |    57.565 |    56.471 |    54.400 |    50.664 |    49.862 |    47.935 |
| stoppage            |    43.803 |    43.974 |    44.333 |    44.941 |    43.874 |    45.991 |
| takeaway            |    14.348 |    14.959 |    14.004 |     9.548 |     9.238 |     8.364 |

Raw counts:

| type_desc_key       |   2021-22 |   2022-23 |   2023-24 |   2024-25 |   2025-26 |   2026-27 |
|:--------------------|----------:|----------:|----------:|----------:|----------:|----------:|
| blocked-shot        |     38224 |     41705 |     48120 |     47096 |     43664 |      3363 |
| delayed-penalty     |      1883 |      2320 |      3607 |      3485 |      3643 |       311 |
| faceoff             |     79631 |     80092 |     79531 |     79480 |     78491 |      6202 |
| failed-shot-attempt |         0 |        27 |        13 |         7 |        15 |         1 |
| game-end            |      1401 |      1400 |      1400 |      1398 |      1394 |       107 |
| giveaway            |     25461 |     24526 |     21827 |     41767 |     42970 |      3577 |
| goal                |      8936 |      9027 |      8772 |      8604 |      8836 |       686 |
| hit                 |     66509 |     65287 |     66216 |     63017 |     59279 |      4810 |
| missed-shot         |     32765 |     34625 |     38204 |     41030 |     41811 |      3063 |
| penalty             |     10533 |     10865 |     10701 |      9759 |     10496 |       894 |
| period-end          |      4610 |      4626 |      4574 |      4566 |      4653 |       351 |
| period-start        |      4620 |      4627 |      4574 |      4567 |      4653 |       351 |
| shootout-complete   |       103 |        95 |        82 |        77 |       119 |         8 |
| shot-on-goal        |     80649 |     79059 |     76160 |     70828 |     69507 |      5129 |
| stoppage            |     61368 |     61563 |     62066 |     62828 |     61160 |      4921 |
| takeaway            |     20102 |     20942 |     19605 |     13348 |     12878 |       895 |


### 3. Shot coordinate coverage (non-shootout shot attempts: SHOT, MISS, BLOCK, GOAL)

|         |   BLOCK |    GOAL |    MISS |    SHOT |     ALL |   n_attempts |
|:--------|--------:|--------:|--------:|--------:|--------:|-------------:|
| 2021-22 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |   159827.000 |
| 2022-23 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |   163771.000 |
| 2023-24 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |   170649.000 |
| 2024-25 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |   167050.000 |
| 2025-26 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |   163021.000 |
| 2026-27 | 100.000 | 100.000 | 100.000 | 100.000 | 100.000 |    12177.000 |

Exact (0,0) coordinate share among shot attempts with coordinates, and out-of-bounds counts:

|         |   pct_xy_exactly_0_0 |   x_min |   x_max |   y_min |   y_max |
|:--------|---------------------:|--------:|--------:|--------:|--------:|
| 2021-22 |                0.001 | -99.000 |  99.000 | -42.000 |  42.000 |
| 2022-23 |                0.002 | -99.000 |  99.000 | -42.000 |  42.000 |
| 2023-24 |                0.002 | -99.000 |  99.000 | -42.000 |  42.000 |
| 2024-25 |                0.004 | -99.000 |  99.000 | -42.000 |  42.000 |
| 2025-26 |                0.003 | -99.000 |  99.000 | -42.000 |  42.000 |
| 2026-27 |                0.008 | -99.000 |  99.000 | -42.000 |  42.000 |


### 4. Coordinate convention

Raw x sign for offensive-zone (zone=O) shots by the home team's defending side (if coordinates were already attack-normalised, raw x would be positive for every side):

|    | owner_is_home   | home_def_side   |   share_raw_x_positive |      n |
|---:|:----------------|:----------------|-----------------------:|-------:|
|  0 | False           | left            |                 0.0000 | 141003 |
|  1 | False           | right           |                 1.0000 | 145492 |
|  2 | True            | left            |                 1.0000 | 147370 |
|  3 | True            | right           |                 0.0000 | 154573 |

After normalisation (owner attacks +x): zone=O shots with x_norm>0: 100.000% (n=588438).

Blocked shots: eventOwnerTeamId is the SHOOTING team (matches the shooter's team in boxscore for 99.99% of blocks, 2024-25 check); x/y are in the shooter's frame (share with x_norm>0 = 99.62%, mean 66.2, n=222172), but zoneCode is relative to the BLOCKING team (zone shares %: {'D': 94.2, 'O': 5.6, 'N': 0.2}).

Home defending side (RS games): flips P1->P2 in 99.99% of games, P2->P3 100.00%, P3->OT 100.00% (n=1481). Periods with more than one value of homeTeamDefendingSide inside the period: 4 of 21482.

Shot-attempt x_norm/y_norm summary (SHOT/MISS/GOAL): x_norm mean 59.4, y range [-42.0, 42.0]; goals with sx<0 (scored from own half): 831.


### 5. Per-season reference numbers

|                            |   ('2021-22', 'PO') |   ('2021-22', 'RS') |   ('2022-23', 'PO') |   ('2022-23', 'RS') |   ('2023-24', 'PO') |   ('2023-24', 'RS') |   ('2024-25', 'PO') |   ('2024-25', 'RS') |   ('2025-26', 'PO') |   ('2025-26', 'RS') |   ('2026-27', 'RS') |
|:---------------------------|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|--------------------:|
| games                      |              89.000 |            1312.000 |              88.000 |            1312.000 |              88.000 |            1312.000 |              86.000 |            1312.000 |              82.000 |            1312.000 |             107.000 |
| goals_per_game             |               6.315 |               6.290 |               6.284 |               6.359 |               5.727 |               6.226 |               6.209 |               6.081 |               5.927 |               6.254 |               6.271 |
| goals_per_game_ex_SO_bonus |               6.315 |               6.212 |               6.284 |               6.286 |               5.727 |               6.162 |               6.209 |               6.020 |               5.927 |               6.163 |               6.187 |
| sog_per_game_pbp           |              67.101 |              63.265 |              63.045 |              62.492 |              56.239 |              60.583 |              55.709 |              56.567 |              56.378 |              55.688 |              53.832 |
| sog_per_game_box           |              67.090 |              63.250 |              63.034 |              62.476 |              56.193 |              60.572 |              55.709 |              56.549 |              56.354 |              55.665 |              53.822 |
| attempts_per_game          |             125.416 |             113.312 |             125.773 |             116.389 |             126.511 |             121.582 |             127.163 |             118.989 |             122.732 |             116.583 |             113.804 |
| pp_segments_per_team_game  |               3.455 |               3.029 |               3.188 |               3.152 |               2.767 |               2.862 |               2.895 |               2.557 |               3.213 |               2.719 |               3.103 |
| pp_goals_per_team_game     |               0.685 |               0.582 |               0.710 |               0.638 |               0.585 |               0.618 |               0.715 |               0.570 |               0.628 |               0.596 |               0.654 |
| pp_pct_approx              |              19.837 |              19.223 |              22.282 |              20.237 |              21.150 |              21.601 |              24.699 |              22.280 |              19.545 |              21.937 |              21.084 |
| penalties_all_per_game     |               9.404 |               7.390 |               9.114 |               7.670 |               7.875 |               7.628 |               8.698 |               6.868 |               9.805 |               7.387 |               8.355 |
| minor2_per_team_game       |               4.309 |               3.307 |               3.795 |               3.428 |               3.602 |               3.394 |               3.890 |               3.080 |               4.506 |               3.294 |               3.682 |
| ot_rate_pct                |              16.854 |              21.951 |              27.273 |              23.018 |              18.182 |              20.732 |              23.256 |              20.655 |              26.829 |              24.848 |              20.561 |
| so_rate_pct                |               0.000 |               7.774 |               0.000 |               7.241 |               0.000 |               6.250 |               0.000 |               5.869 |               0.000 |               9.070 |               7.477 |
| en_goals_per_game          |               0.494 |               0.363 |               0.284 |               0.334 |               0.432 |               0.341 |               0.512 |               0.399 |               0.476 |               0.387 |               0.346 |
| home_win_pct               |              60.674 |              53.659 |              46.591 |              52.363 |              47.727 |              54.116 |              60.465 |              56.250 |              47.561 |              52.210 |              53.271 |

Notes: `pp_pct_approx` = PP goals (strength state PP, both goalies in net) / PP segments, where a PP segment is a transition into skater advantage with both goalies on ice, so 5v4 -> 5v3 is one segment and a PP ended and restarted counts twice. It is a reference scale, not an official NHL PP%. `so_rate_pct`/`ot_rate_pct` are percent of all games; for playoffs the OT rate counts any OT game and no SO exists. `en_goals_per_game` = non-shootout goals with no goalie in net (goalieInNetId absent).


### 6. pbp-derived SOG vs boxscore SOG (non-shootout)

|         |   pct_team_games_exact |   pct_within_1 |   mean_diff |   max_abs_diff |
|:--------|-----------------------:|---------------:|------------:|---------------:|
| 2021-22 |                 99.251 |        100.000 |       0.007 |          1.000 |
| 2022-23 |                 99.214 |        100.000 |       0.008 |          1.000 |
| 2023-24 |                 99.357 |        100.000 |       0.006 |          1.000 |
| 2024-25 |                 99.142 |        100.000 |       0.009 |          1.000 |
| 2025-26 |                 98.852 |        100.000 |       0.011 |          1.000 |
| 2026-27 |                 99.533 |        100.000 |       0.005 |          1.000 |


### 7. Goalie identification

|         |   team_games |   pct_exactly_one_starter |   pct_zero |   pct_two_plus |
|:--------|-------------:|--------------------------:|-----------:|---------------:|
| 2021-22 |     2802.000 |                   100.000 |      0.000 |          0.000 |
| 2022-23 |     2800.000 |                   100.000 |      0.000 |          0.000 |
| 2023-24 |     2800.000 |                   100.000 |      0.000 |          0.000 |
| 2024-25 |     2796.000 |                   100.000 |      0.000 |          0.000 |
| 2025-26 |     2788.000 |                   100.000 |      0.000 |          0.000 |
| 2026-27 |      214.000 |                   100.000 |      0.000 |          0.000 |

|         |   pct_first_faced_goalie_is_boxscore_starter |   n_team_games |
|:--------|---------------------------------------------:|---------------:|
| 2021-22 |                                       99.964 |       2802.000 |
| 2022-23 |                                      100.000 |       2800.000 |
| 2023-24 |                                      100.000 |       2800.000 |
| 2024-25 |                                       99.964 |       2796.000 |
| 2025-26 |                                      100.000 |       2788.000 |
| 2026-27 |                                      100.000 |        214.000 |

Goalies appearing per team-game: {1: 3, 2: 14196, 3: 1}. Goalie rows with decision missing: 50.0% (non-decision rows are the non-starters/relievers).


### 8. Shift-chart coverage

|         |   games |   pct_games_with_shifts |   pct_reg_time_skater_counts_match_pbp |   pct_of_pbp_5v5_time_with_5_and_5_identified |   pct_games_5v5_identified_ge_95pct |   games_missing_position_rows |
|:--------|--------:|------------------------:|---------------------------------------:|----------------------------------------------:|------------------------------------:|------------------------------:|
| 2021-22 | 1401.00 |                  100.00 |                                  96.49 |                                         98.36 |                               95.07 |                          0.00 |
| 2022-23 | 1400.00 |                  100.00 |                                  97.27 |                                         99.11 |                               96.71 |                          0.00 |
| 2023-24 | 1400.00 |                  100.00 |                                  96.11 |                                         97.96 |                               88.00 |                          0.00 |
| 2024-25 | 1398.00 |                   95.92 |                                  97.22 |                                         98.85 |                               92.06 |                          1.00 |
| 2025-26 | 1394.00 |                  100.00 |                                  96.96 |                                         98.75 |                               95.19 |                          1.00 |
| 2026-27 |  107.00 |                   55.14 |                                  96.39 |                                         98.25 |                               50.47 |                          0.00 |

Method: regulation time only (0-3600 s). For each second, skaters on ice = shifts (typeCode 517, goalies excluded by roster position) with start <= t < end, vs the skater counts of the latest pbp event's situationCode. `5_and_5_identified` = seconds where pbp says 5v5 (both goalies in) AND shifts give exactly 5 and 5. Event-timestamp lag around stoppages and shift-boundary rounding (whole seconds) cause some mismatch even when coverage is complete.

|         |   shift_rows |   pct_missing_start_or_end |   median_dur_s |   pct_no_position |
|:--------|-------------:|---------------------------:|---------------:|------------------:|
| 2021-22 |  1083846.000 |                      0.000 |         45.000 |             0.000 |
| 2022-23 |  1069433.000 |                      0.000 |         46.000 |             0.000 |
| 2023-24 |  1062112.000 |                      0.000 |         46.000 |             0.000 |
| 2024-25 |  1018818.000 |                      0.000 |         46.000 |             0.000 |
| 2025-26 |  1052966.000 |                      0.000 |         46.000 |             0.063 |
| 2026-27 |    44221.000 |                      0.000 |         46.000 |             0.000 |
