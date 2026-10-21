# EG-R1 part A step 0 (Lane H8a, INV-66): pull rows and the level question, training seasons only

Generated 2026-10-21 13:42:57 -0400 by `scripts/build_end_game_pull_rows_v1.py step0`. Regular season. Training seasons only (2021-22, 2022-23, 2023-24); nothing from 2024-25 is read. Committed before any fit.

Definitions: `src/nhl_sim/end_game/pull.py` module doc and the Lane H8a execution note in `docs/models/end_game/experiments.md`. Engine-rule episode = non-DP pull start while trailing in the last 600 s, until the first goal against / tying goal / end of regulation. Literal = shift-chart non-DP goalie-out seconds in the window. Bridged = engine-rule out seconds that are goalie-in on the shift chart (a non-goal return).

## Rows and pulled time per game (seconds, both teams, regular season)

| season   |   games |   team_games |   rows |   pulls_y |   episodes |   first_episodes |   repulls |   engine_rule_s_per_game |   literal_nonDP_window_s_per_game |   bridged_s_per_game |   literal_outside_episode_s_per_game |   all_shift_pulls_window_incl_DP_s_per_game |   all_shift_pulls_game_incl_DP_s_per_game |
|:---------|--------:|-------------:|-------:|----------:|-----------:|-----------------:|----------:|-------------------------:|----------------------------------:|---------------------:|-------------------------------------:|--------------------------------------------:|------------------------------------------:|
| 2021-22  |    1312 |         2624 | 544414 |       920 |        920 |              810 |       110 |                    65.47 |                             58.61 |                 7.32 |                                 0.46 |                                       60.05 |                                     72.59 |
| 2022-23  |    1312 |         2624 | 540837 |       881 |        881 |              792 |        89 |                    63.93 |                             56.11 |                 8.57 |                                 0.75 |                                       57.41 |                                     68.37 |
| 2023-24  |    1312 |         2624 | 548154 |       906 |        906 |              809 |        97 |                    67.58 |                             60.00 |                 7.91 |                                 0.34 |                                       61.48 |                                     72.51 |

`all_shift_pulls_game_incl_DP` is the audit's 'pulled time per game, all pulls' (table 1h, any period); the window column restricts it to the last 600 s of P3.

## First-pull seconds left by deficit at the start (engine-rule first episode per team-game)

| season   | deficit   |   n | flag         |   p10 |   p25 |   median |   p75 |   p90 |
|:---------|:----------|----:|:-------------|------:|------:|---------:|------:|------:|
| 2021-22  | trail1    | 435 |              |  60.0 |  86.0 |    108.0 | 133.5 | 155.0 |
| 2021-22  | trail2    | 294 |              |  99.6 | 144.2 |    178.0 | 216.0 | 250.7 |
| 2021-22  | trail3+   |  81 | UNDERPOWERED | 133.0 | 187.0 |    250.0 | 315.0 | 437.0 |
| 2022-23  | trail1    | 426 |              |  62.0 |  88.0 |    112.0 | 134.0 | 154.5 |
| 2022-23  | trail2    | 275 |              | 101.0 | 138.5 |    170.0 | 209.5 | 250.2 |
| 2022-23  | trail3+   |  91 | UNDERPOWERED | 153.0 | 191.0 |    249.0 | 307.5 | 358.0 |
| 2023-24  | trail1    | 417 |              |  63.0 |  91.0 |    113.0 | 136.0 | 162.0 |
| 2023-24  | trail2    | 312 |              | 105.1 | 144.0 |    175.5 | 214.2 | 248.9 |
| 2023-24  | trail3+   |  80 | UNDERPOWERED | 143.1 | 185.2 |    272.5 | 348.5 | 460.4 |

## Episode ends and re-pulls

| season   |   episodes_ended_by_goal_against |   repull_share |   ended_tie |   ended_period_end |   first_cause_stoppage |   first_cause_goal_for |   first_cause_in_play |   share_eps_with_pen_pk |   share_eps_with_pen_pp |
|:---------|---------------------------------:|---------------:|------------:|-------------------:|-----------------------:|-----------------------:|----------------------:|------------------------:|------------------------:|
| 2021-22  |                              477 |          0.222 |          69 |                374 |                    151 |                    122 |                     4 |                   0.030 |                   0.046 |
| 2022-23  |                              444 |          0.198 |          71 |                366 |                    181 |                    117 |                     3 |                   0.034 |                   0.060 |
| 2023-24  |                              444 |          0.218 |          66 |                396 |                    181 |                    115 |                     1 |                   0.032 |                   0.054 |

`first_cause_*` = how the first shift gap of the episode ended on the shift chart (a non-goal return is bridged).

## Level question (L27)

Per-season pulled time per game and first-pull medians above: the spec carries no level in EG-R1; a fold-2 pulled-time miss > 10% makes a level EG-R2's first item. Whether the training seasons show a trend is read from the table above.

