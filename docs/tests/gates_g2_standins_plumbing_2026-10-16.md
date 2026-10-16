# G2 closed loop, STAND-IN plumbing (D32) (SA-R3): standins_plumbing_v1, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **STAND-IN / PLUMBING RUN (D32). NOTHING HERE GATES.** Block = B0 STAND-IN (flat: strength group x period type + M1 K500 level); stage 4 = L0s STAND-IN (flat, level E from GameState.rec_era); goals = xG_ref STUB. Team-level and responsiveness readings are against flat stand-ins and are not evidence about any model. G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).

Generated 2026-10-16 12:30:53 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.5533 |  58.3508 |  0.0035 | 0.0300 | PASS         | n=2624 team-games                       |   58.5809 | PASS         |      0.0276 |
| ('per60_state', 'PP')         | 101.1092 | 101.6226 | -0.0051 | 0.0300 | PASS         | n=2624 team-games                       |  101.1491 | PASS         |      0.0399 |
| ('per60_state', 'PK')         |  14.0152 |  14.3173 | -0.0211 | 0.0300 | PASS         | n=2624 team-games                       |   14.0149 | PASS         |      0.0003 |
| ('per60_state', '4v4')        |  50.0961 |  48.6237 |  0.0303 | 0.0300 | FAIL         | n=2624 team-games                       |   50.0100 | PASS         |      0.0861 |
| ('per60_state', '3v3')        |  59.2866 |  55.2313 |  0.0734 | 0.0300 | FAIL         | n=2624 team-games                       |   59.4346 | FAIL         |      0.1480 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.7923 |  65.4302 | -0.0403 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   62.9082 | UNDERPOWERED |      0.1159 |
| ('per60_score', '-2')         |  63.6122 |  68.2253 | -0.0676 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   63.6414 | UNDERPOWERED |      0.0292 |
| ('per60_score', '-1')         |  62.4241 |  64.2065 | -0.0278 | 0.0300 | PASS         | n=476 team-hours                        |   62.4898 | PASS         |      0.0658 |
| ('per60_score', '0')          |  58.8664 |  58.6022 |  0.0045 | 0.0300 | PASS         | n=919 team-hours                        |   58.8942 | PASS         |      0.0278 |
| ('per60_score', '+1')         |  54.6518 |  54.1359 |  0.0095 | 0.0300 | PASS         | n=476 team-hours                        |   54.6221 | PASS         |      0.0297 |
| ('per60_score', '+2')         |  52.0750 |  51.3994 |  0.0131 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   52.1061 | UNDERPOWERED |      0.0311 |
| ('per60_score', '>=+3')       |  49.9170 |  49.2586 |  0.0134 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   49.9145 | UNDERPOWERED |      0.0025 |
| ('team_game', 'mean')         |  59.0498 |  59.4832 | -0.0073 | 0.0300 | PASS         | n=2624 team-games                       |   59.0670 | PASS         |      0.0172 |
| ('team_game', 'sd')           |   9.9502 |  11.6141 | -0.1433 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.9614 | NO-TOLERANCE |      0.0112 |
| ('team_game_P', '[0,40)')     |   0.0167 |   0.0286 | -0.4150 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0166 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1518 |   0.1700 | -0.1071 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1512 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[50,60)')    |   0.3669 |   0.3266 |  0.1233 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3678 | NO-TOLERANCE |      0.0009 |
| ('team_game_P', '[60,70)')    |   0.3180 |   0.2851 |  0.1155 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3164 | NO-TOLERANCE |      0.0016 |
| ('team_game_P', '>=70')       |   0.1466 |   0.1898 | -0.2273 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1480 | NO-TOLERANCE |      0.0014 |
| ('game', 'corr_home_away')    |  -0.2197 |  -0.4126 | -0.4676 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2249 | NO-TOLERANCE |      0.0053 |

### Decomposition, attempts per team-game: actual 59.483, sim 59.050, sim - actual -0.433 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +1.0888 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0437 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0603 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.3508 |  58.5533 |  0.2026 |         0.2660 |                   0.0435 |     -0.1070 | 1.7505 | CLEAN     |
| PP      | 101.6226 | 101.1092 | -0.5134 |        -0.7057 |                   0.0527 |      0.1396 | 3.0487 | CLEAN     |
| PK      |  14.3173 |  14.0152 | -0.3021 |        -0.3347 |                   0.0023 |      0.0303 | 0.4295 | CLEAN     |
| 4v4     |  48.6237 |  50.0961 |  1.4723 |         0.8432 |                   0.1569 |      0.4722 | 1.4587 | FAIL      |
| 3v3     |  55.2313 |  59.2866 |  4.0553 |         2.9801 |                  -0.0363 |      1.1115 | 1.6569 | FAIL      |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.1982 |  60.2558 |   0.0156 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.2430 | UNDERPOWERED |      0.0448 |
| ('per60_state', 'PP')         | 105.2271 | 102.9062 |   0.0226 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.2438 | UNDERPOWERED |      0.0167 |
| ('per60_state', 'PK')         |  14.6038 |  13.3181 |   0.0965 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.6335 | UNDERPOWERED |      0.0297 |
| ('per60_state', '4v4')        |  50.9416 |  51.5258 |  -0.0113 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.8720 | UNDERPOWERED |      0.0696 |
| ('per60_state', '3v3')        |  60.5568 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   38.7931 | UNDERPOWERED |     21.7637 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  64.9756 |  65.1965 |  -0.0034 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   64.7296 | UNDERPOWERED |      0.2460 |
| ('per60_score', '-2')         |  66.1649 |  71.0331 |  -0.0685 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   66.2531 | UNDERPOWERED |      0.0882 |
| ('per60_score', '-1')         |  65.1330 |  65.7393 |  -0.0092 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   65.2809 | UNDERPOWERED |      0.1479 |
| ('per60_score', '0')          |  61.9977 |  60.2059 |   0.0298 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.0901 | UNDERPOWERED |      0.0924 |
| ('per60_score', '+1')         |  56.5682 |  56.3612 |   0.0037 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   56.6279 | UNDERPOWERED |      0.0598 |
| ('per60_score', '+2')         |  53.8576 |  54.3527 |  -0.0091 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   53.7998 | UNDERPOWERED |      0.0577 |
| ('per60_score', '>=+3')       |  52.0332 |  47.3922 |   0.0979 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.7841 | UNDERPOWERED |      0.2491 |
| ('team_game', 'mean')         |  62.6183 |  63.5814 |  -0.0151 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.6903 | UNDERPOWERED |      0.0719 |
| ('team_game', 'sd')           |  11.6631 |  14.6140 |  -0.2019 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   11.7894 | NO-TOLERANCE |      0.1263 |
| ('team_game_P', '[0,40)')     |   0.0088 |   0.0174 |  -0.4967 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0095 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '[40,50)')    |   0.1013 |   0.0930 |   0.0894 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1009 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '[50,60)')    |   0.3124 |   0.3547 |  -0.1191 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3109 | NO-TOLERANCE |      0.0015 |
| ('team_game_P', '[60,70)')    |   0.3344 |   0.2035 |   0.6433 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3324 | NO-TOLERANCE |      0.0020 |
| ('team_game_P', '>=70')       |   0.2431 |   0.3314 |  -0.2665 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2462 | NO-TOLERANCE |      0.0031 |
| ('game', 'corr_home_away')    |   0.0087 |  -0.0772 |  -1.1130 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0299 | NO-TOLERANCE |      0.0211 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.618, sim - actual -0.963 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -0.3580 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0272 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.2851 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.1982 |   0.9425 |         1.2744 |                   0.0172 |     -0.3491 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.2271 |   2.3209 |         1.9991 |                   0.4449 |     -0.1231 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6038 |   1.2858 |         1.4198 |                  -0.0428 |     -0.0912 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.9416 |  -0.5842 |        -1.2389 |                   0.1703 |      0.4844 |   1.5458 | CLEAN     |
| 3v3     | nan      |  60.5568 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.7189 |  58.4717 |  0.0042 | 0.0300 | PASS         | n=2796 team-games                       |   58.7477 | PASS         |      0.0287 |
| ('per60_state', 'PP')         | 101.3786 | 101.7125 | -0.0033 | 0.0300 | PASS         | n=2796 team-games                       |  101.4173 | PASS         |      0.0387 |
| ('per60_state', 'PK')         |  14.0537 |  14.2473 | -0.0136 | 0.0300 | PASS         | n=2796 team-games                       |   14.0554 | PASS         |      0.0017 |
| ('per60_state', '4v4')        |  50.1497 |  48.8019 |  0.0276 | 0.0300 | PASS         | n=2796 team-games                       |   50.0644 | PASS         |      0.0853 |
| ('per60_state', '3v3')        |  59.2868 |  55.2313 |  0.0734 | 0.0300 | FAIL         | n=2796 team-games                       |   59.4317 | FAIL         |      0.1449 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.9322 |  65.4146 | -0.0379 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   63.0267 | UNDERPOWERED |      0.0945 |
| ('per60_score', '-2')         |  63.7706 |  68.3894 | -0.0675 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   63.8032 | UNDERPOWERED |      0.0326 |
| ('per60_score', '-1')         |  62.5907 |  64.3039 | -0.0266 | 0.0300 | PASS         | n=508 team-hours                        |   62.6611 | PASS         |      0.0704 |
| ('per60_score', '0')          |  59.0639 |  58.7080 |  0.0061 | 0.0300 | PASS         | n=984 team-hours                        |   59.0958 | PASS         |      0.0319 |
| ('per60_score', '+1')         |  54.7697 |  54.2774 |  0.0091 | 0.0300 | PASS         | n=508 team-hours                        |   54.7452 | PASS         |      0.0246 |
| ('per60_score', '+2')         |  52.1856 |  51.5720 |  0.0119 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   52.2110 | UNDERPOWERED |      0.0254 |
| ('per60_score', '>=+3')       |  50.0526 |  49.1341 |  0.0187 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   50.0361 | UNDERPOWERED |      0.0165 |
| ('team_game', 'mean')         |  59.2693 |  59.7353 | -0.0078 | 0.0300 | PASS         | n=2796 team-games                       |   59.2899 | PASS         |      0.0205 |
| ('team_game', 'sd')           |  10.1004 |  11.8616 | -0.1485 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.1209 | NO-TOLERANCE |      0.0205 |
| ('team_game_P', '[0,40)')     |   0.0162 |   0.0279 | -0.4181 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0162 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1487 |   0.1652 | -0.1003 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1481 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[50,60)')    |   0.3635 |   0.3283 |  0.1072 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3643 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '[60,70)')    |   0.3190 |   0.2800 |  0.1391 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3174 | NO-TOLERANCE |      0.0016 |
| ('team_game_P', '>=70')       |   0.1526 |   0.1985 | -0.2313 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1541 | NO-TOLERANCE |      0.0015 |
| ('game', 'corr_home_away')    |  -0.1919 |  -0.3716 | -0.4835 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1944 | NO-TOLERANCE |      0.0024 |

### Decomposition, attempts per team-game: actual 59.735, sim 59.269, sim - actual -0.466 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                +1.0036 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0436 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0789 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.4717 |  58.7189 |  0.2473 |         0.3301 |                   0.0430 |     -0.1257 | 1.7542 | CLEAN     |
| PP      | 101.7125 | 101.3786 | -0.3339 |        -0.5163 |                   0.0740 |      0.1084 | 3.0514 | CLEAN     |
| PK      |  14.2473 |  14.0537 | -0.1936 |        -0.2119 |                   0.0003 |      0.0180 | 0.4274 | CLEAN     |
| 4v4     |  48.8019 |  50.1497 |  1.3478 |         0.7153 |                   0.1628 |      0.4697 | 1.4641 | CLEAN     |
| 3v3     |  55.2313 |  59.2868 |  4.0555 |         2.9801 |                  -0.0397 |      1.1152 | 1.6569 | FAIL      |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.134 (95% CI 0.994..1.312) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.555 |         54.316 |        560.000 |
|  2 |      56.574 |         56.489 |        559.000 |
|  3 |      58.945 |         58.333 |        559.000 |
|  4 |      60.373 |         59.643 |        559.000 |
|  5 |      64.159 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.121 (95% CI 0.972..1.325) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.241 |         53.883 |        560.000 |
|  2 |      56.958 |         57.551 |        559.000 |
|  3 |      58.699 |         59.405 |        559.000 |
|  4 |      60.090 |         59.246 |        559.000 |
|  5 |      63.605 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        60.36 |            58.01 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        58.66 |            60.15 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        60.39 |            61.61 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        56.03 |            60.34 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        62.52 |            60.39 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        55.36 |            58.47 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        59.69 |            58.44 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        55.03 |            63.78 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        60.60 |            57.99 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        59.29 |            61.47 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        67.29 |            50.09 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        64.35 |            55.72 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        58.45 |            58.08 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        58.82 |            60.38 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        52.09 |            61.70 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        54.76 |            61.52 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        60.61 |            57.38 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.96 |            59.08 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.71 |            60.27 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        62.89 |            55.78 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        64.16 |            56.17 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        56.31 |            56.30 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.89 |            66.70 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        61.18 |            58.36 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        61.06 |            56.01 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        55.25 |            66.13 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.95 |            61.34 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        56.24 |            60.15 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        58.86 |            59.43 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        59.44 |            60.65 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        58.53 |            60.85 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        61.68 |            57.33 | UNDERPOWERED |

