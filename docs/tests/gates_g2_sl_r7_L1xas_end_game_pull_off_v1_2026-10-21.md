# G2 re-check, SL-R7 L1x-as closed loop (oracle goalie) (SA-R3): end_game_pull_off_v1, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **EG-R1 part A closed loop (Lane H8a), goalie pull OFF.** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t, no goalie pull. No delayed-penalty state (INV-70); OT = stage-1 3v3, shootout 50 / 50 stub; no rebounds. Report text produced by the SL-R7 grader.

Generated 2026-10-21 14:20:39 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.5310 |  58.3508 |  0.0031 | 0.0300 | PASS         | n=2624 team-games                       |   58.5557 | PASS         |      0.0246 |
| ('per60_state', 'PP')         | 101.0279 | 101.6226 | -0.0059 | 0.0300 | PASS         | n=2624 team-games                       |  101.0496 | PASS         |      0.0217 |
| ('per60_state', 'PK')         |  14.0039 |  14.3173 | -0.0219 | 0.0300 | PASS         | n=2624 team-games                       |   13.9978 | PASS         |      0.0061 |
| ('per60_state', '4v4')        |  50.0066 |  48.6237 |  0.0284 | 0.0300 | PASS         | n=2624 team-games                       |   50.0105 | PASS         |      0.0039 |
| ('per60_state', '3v3')        |  58.1633 |  55.2313 |  0.0531 | 0.0300 | FAIL         | n=2624 team-games                       |   58.4349 | FAIL         |      0.2716 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.8059 |  65.4302 | -0.0401 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   62.8042 | UNDERPOWERED |      0.0017 |
| ('per60_score', '-2')         |  63.5758 |  68.2253 | -0.0681 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   63.6384 | UNDERPOWERED |      0.0626 |
| ('per60_score', '-1')         |  62.4204 |  64.2065 | -0.0278 | 0.0300 | PASS         | n=476 team-hours                        |   62.4497 | PASS         |      0.0292 |
| ('per60_score', '0')          |  58.8102 |  58.6022 |  0.0035 | 0.0300 | PASS         | n=919 team-hours                        |   58.8241 | PASS         |      0.0139 |
| ('per60_score', '+1')         |  54.7059 |  54.1359 |  0.0105 | 0.0300 | PASS         | n=476 team-hours                        |   54.7239 | PASS         |      0.0180 |
| ('per60_score', '+2')         |  52.1339 |  51.3994 |  0.0143 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   52.1696 | UNDERPOWERED |      0.0356 |
| ('per60_score', '>=+3')       |  49.9236 |  49.2586 |  0.0135 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   49.9495 | UNDERPOWERED |      0.0259 |
| ('team_game', 'mean')         |  58.8875 |  59.4832 | -0.0100 | 0.0300 | PASS         | n=2624 team-games                       |   58.9119 | PASS         |      0.0245 |
| ('team_game', 'sd')           |   9.8750 |  11.6141 | -0.1497 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.8785 | NO-TOLERANCE |      0.0035 |
| ('team_game_P', '[0,40)')     |   0.0170 |   0.0286 | -0.4069 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0169 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1542 |   0.1700 | -0.0929 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1533 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '[50,60)')    |   0.3708 |   0.3266 |  0.1353 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3704 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '[60,70)')    |   0.3165 |   0.2851 |  0.1104 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3170 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '>=70')       |   0.1415 |   0.1898 | -0.2542 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1424 | NO-TOLERANCE |      0.0008 |
| ('game', 'corr_home_away')    |  -0.2307 |  -0.4126 | -0.4409 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2341 | NO-TOLERANCE |      0.0034 |

### Decomposition, attempts per team-game: actual 59.483, sim 58.887, sim - actual -0.596 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +0.9652 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0054 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0608 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.3508 |  58.5310 |  0.1803 |         0.2660 |                   0.0029 |     -0.0887 | 1.7505 | CLEAN     |
| PP      | 101.6226 | 101.0279 | -0.5946 |        -0.7057 |                   0.0414 |      0.0697 | 3.0487 | CLEAN     |
| PK      |  14.3173 |  14.0039 | -0.3134 |        -0.3347 |                  -0.0035 |      0.0249 | 0.4295 | CLEAN     |
| 4v4     |  48.6237 |  50.0066 |  1.3829 |         0.8432 |                   0.1257 |      0.4140 | 1.4587 | CLEAN     |
| 3v3     |  55.2313 |  58.1633 |  2.9320 |         2.9801 |                  -0.0449 |     -0.0031 | 1.6569 | FAIL      |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.2506 |  60.2558 |   0.0165 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.2894 | UNDERPOWERED |      0.0388 |
| ('per60_state', 'PP')         | 105.2869 | 102.9062 |   0.0231 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.3693 | UNDERPOWERED |      0.0824 |
| ('per60_state', 'PK')         |  14.6406 |  13.3181 |   0.0993 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.6938 | UNDERPOWERED |      0.0532 |
| ('per60_state', '4v4')        |  50.8390 |  51.5258 |  -0.0133 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.7100 | UNDERPOWERED |      0.1291 |
| ('per60_state', '3v3')        |  55.9756 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   40.3587 | UNDERPOWERED |     15.6169 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  65.9190 |  65.1965 |   0.0111 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   65.6899 | UNDERPOWERED |      0.2291 |
| ('per60_score', '-2')         |  66.4159 |  71.0331 |  -0.0650 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   66.2900 | UNDERPOWERED |      0.1259 |
| ('per60_score', '-1')         |  65.1918 |  65.7393 |  -0.0083 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   65.2723 | UNDERPOWERED |      0.0805 |
| ('per60_score', '0')          |  62.0935 |  60.2059 |   0.0314 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.2141 | UNDERPOWERED |      0.1206 |
| ('per60_score', '+1')         |  56.5862 |  56.3612 |   0.0040 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   56.7348 | UNDERPOWERED |      0.1486 |
| ('per60_score', '+2')         |  53.3925 |  54.3527 |  -0.0177 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   53.3205 | UNDERPOWERED |      0.0719 |
| ('per60_score', '>=+3')       |  51.4456 |  47.3922 |   0.0855 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.3160 | UNDERPOWERED |      0.1295 |
| ('team_game', 'mean')         |  62.7757 |  63.5814 |  -0.0127 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.8285 | UNDERPOWERED |      0.0528 |
| ('team_game', 'sd')           |  11.9781 |  14.6140 |  -0.1804 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   12.0207 | NO-TOLERANCE |      0.0426 |
| ('team_game_P', '[0,40)')     |   0.0088 |   0.0174 |  -0.4933 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0099 | NO-TOLERANCE |      0.0011 |
| ('team_game_P', '[40,50)')    |   0.1028 |   0.0930 |   0.1056 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1006 | NO-TOLERANCE |      0.0023 |
| ('team_game_P', '[50,60)')    |   0.3107 |   0.3547 |  -0.1239 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3094 | NO-TOLERANCE |      0.0013 |
| ('team_game_P', '[60,70)')    |   0.3277 |   0.2035 |   0.6103 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3302 | NO-TOLERANCE |      0.0025 |
| ('team_game_P', '>=70')       |   0.2499 |   0.3314 |  -0.2458 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2499 | NO-TOLERANCE |      0.0000 |
| ('game', 'corr_home_away')    |   0.0185 |  -0.0772 |  -1.2392 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0330 | NO-TOLERANCE |      0.0146 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.776, sim - actual -0.806 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -0.2511 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0294 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.2368 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.2506 |   0.9948 |         1.2744 |                   0.0111 |     -0.2907 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.2869 |   2.3807 |         1.9991 |                   0.5497 |     -0.1681 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6406 |   1.3225 |         1.4198 |                  -0.0498 |     -0.0474 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.8390 |  -0.6868 |        -1.2389 |                   0.1641 |      0.3880 |   1.5458 | CLEAN     |
| 3v3     | nan      |  55.9756 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.7016 |  58.4717 |  0.0039 | 0.0300 | PASS         | n=2796 team-games                       |   58.7272 | PASS         |      0.0255 |
| ('per60_state', 'PP')         | 101.3069 | 101.7125 | -0.0040 | 0.0300 | PASS         | n=2796 team-games                       |  101.3327 | PASS         |      0.0258 |
| ('per60_state', 'PK')         |  14.0456 |  14.2473 | -0.0142 | 0.0300 | PASS         | n=2796 team-games                       |   14.0434 | PASS         |      0.0022 |
| ('per60_state', '4v4')        |  50.0594 |  48.8019 |  0.0258 | 0.0300 | PASS         | n=2796 team-games                       |   50.0548 | PASS         |      0.0046 |
| ('per60_state', '3v3')        |  58.1629 |  55.2313 |  0.0531 | 0.0300 | FAIL         | n=2796 team-games                       |   58.4320 | FAIL         |      0.2691 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.9944 |  65.4146 | -0.0370 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   62.9822 | UNDERPOWERED |      0.0123 |
| ('per60_score', '-2')         |  63.7502 |  68.3894 | -0.0678 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   63.8021 | UNDERPOWERED |      0.0519 |
| ('per60_score', '-1')         |  62.5921 |  64.3039 | -0.0266 | 0.0300 | PASS         | n=508 team-hours                        |   62.6233 | PASS         |      0.0312 |
| ('per60_score', '0')          |  59.0224 |  58.7080 |  0.0054 | 0.0300 | PASS         | n=984 team-hours                        |   59.0429 | PASS         |      0.0205 |
| ('per60_score', '+1')         |  54.8224 |  54.2774 |  0.0100 | 0.0300 | PASS         | n=508 team-hours                        |   54.8476 | PASS         |      0.0252 |
| ('per60_score', '+2')         |  52.2112 |  51.5720 |  0.0124 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   52.2406 | UNDERPOWERED |      0.0294 |
| ('per60_score', '>=+3')       |  50.0158 |  49.1341 |  0.0179 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   50.0337 | UNDERPOWERED |      0.0180 |
| ('team_game', 'mean')         |  59.1267 |  59.7353 | -0.0102 | 0.0300 | PASS         | n=2796 team-games                       |   59.1529 | PASS         |      0.0262 |
| ('team_game', 'sd')           |  10.0606 |  11.8616 | -0.1518 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.0676 | NO-TOLERANCE |      0.0070 |
| ('team_game_P', '[0,40)')     |   0.0165 |   0.0279 | -0.4102 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0165 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[40,50)')    |   0.1510 |   0.1652 | -0.0860 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1501 | NO-TOLERANCE |      0.0009 |
| ('team_game_P', '[50,60)')    |   0.3671 |   0.3283 |  0.1181 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3666 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '[60,70)')    |   0.3172 |   0.2800 |  0.1328 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3178 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '>=70')       |   0.1482 |   0.1985 | -0.2533 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1490 | NO-TOLERANCE |      0.0008 |
| ('game', 'corr_home_away')    |  -0.1981 |  -0.3716 | -0.4670 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1996 | NO-TOLERANCE |      0.0015 |

### Decomposition, attempts per team-game: actual 59.735, sim 59.127, sim - actual -0.609 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                +0.8939 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0068 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0750 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.4717 |  58.7016 |  0.2300 |         0.3301 |                   0.0039 |     -0.1040 | 1.7542 | CLEAN     |
| PP      | 101.7125 | 101.3069 | -0.4056 |        -0.5163 |                   0.0674 |      0.0433 | 3.0514 | CLEAN     |
| PK      |  14.2473 |  14.0456 | -0.2017 |        -0.2119 |                  -0.0059 |      0.0161 | 0.4274 | CLEAN     |
| 4v4     |  48.8019 |  50.0594 |  1.2575 |         0.7153 |                   0.1327 |      0.4095 | 1.4641 | CLEAN     |
| 3v3     |  55.2313 |  58.1629 |  2.9316 |         2.9801 |                  -0.0496 |      0.0012 | 1.6569 | FAIL      |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.147 (95% CI 1.007..1.325) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.525 |         54.316 |        560.000 |
|  2 |      56.541 |         56.489 |        559.000 |
|  3 |      58.795 |         58.333 |        559.000 |
|  4 |      60.404 |         59.643 |        559.000 |
|  5 |      64.254 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.111 (95% CI 0.965..1.317) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.208 |         53.883 |        560.000 |
|  2 |      57.005 |         57.551 |        559.000 |
|  3 |      58.726 |         59.405 |        559.000 |
|  4 |      60.085 |         59.246 |        559.000 |
|  5 |      63.487 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        60.03 |            58.06 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        58.52 |            59.98 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        60.09 |            61.65 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        56.07 |            59.89 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        62.72 |            59.94 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        55.17 |            58.41 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        59.52 |            58.31 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        54.84 |            63.58 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        60.66 |            57.68 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        58.80 |            61.69 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        67.46 |            49.95 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        64.54 |            55.51 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        58.00 |            58.26 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        58.47 |            60.47 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        52.10 |            61.31 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        54.57 |            61.40 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        60.75 |            57.04 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.85 |            59.00 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.94 |            59.83 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        62.57 |            55.78 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        64.00 |            56.01 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        55.94 |            56.31 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.94 |            66.21 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        60.80 |            58.45 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.93 |            55.91 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        55.34 |            65.51 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.93 |            60.91 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        55.97 |            60.18 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        58.44 |            59.66 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        59.05 |            60.63 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        58.37 |            60.66 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        61.53 |            57.10 | UNDERPOWERED |

