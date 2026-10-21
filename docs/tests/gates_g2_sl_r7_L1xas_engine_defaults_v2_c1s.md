# G2 re-check, SL-R7 L1x-as closed loop (oracle goalie) (SA-R3): engine_defaults_v2_c1s, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **INV-77 closed loop, NEW engine DEFAULT table set** (Lane E4): stage 4 = L1x-as, block = B1a-as (SB-R5), 3v3 OT attempt level ON (EG-R1 part B), goal = C1s (provisional, D40) (ORACLE GOALIE, D8), miss S0t STAND-IN. Pull and shootout flags OFF (no goalie pull, 50/50 shootout stub; no rebounds). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)

Generated 2026-10-21 16:02:23 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.5259 |  58.3508 |  0.0030 | 0.0300 | PASS         | n=2624 team-games                       |   58.5512 | PASS         |      0.0253 |
| ('per60_state', 'PP')         | 101.0280 | 101.6226 | -0.0059 | 0.0300 | PASS         | n=2624 team-games                       |  101.0497 | PASS         |      0.0217 |
| ('per60_state', 'PK')         |  14.0037 |  14.3173 | -0.0219 | 0.0300 | PASS         | n=2624 team-games                       |   13.9962 | PASS         |      0.0075 |
| ('per60_state', '4v4')        |  49.9990 |  48.6237 |  0.0283 | 0.0300 | PASS         | n=2624 team-games                       |   50.0079 | PASS         |      0.0089 |
| ('per60_state', '3v3')        |  55.5893 |  55.2313 |  0.0065 | 0.0300 | PASS         | n=2624 team-games                       |   55.9001 | PASS         |      0.3108 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.8874 |  65.4302 | -0.0389 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   62.8743 | UNDERPOWERED |      0.0131 |
| ('per60_score', '-2')         |  63.6315 |  68.2253 | -0.0673 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   63.6827 | UNDERPOWERED |      0.0512 |
| ('per60_score', '-1')         |  62.4453 |  64.2065 | -0.0274 | 0.0300 | PASS         | n=476 team-hours                        |   62.4866 | PASS         |      0.0414 |
| ('per60_score', '0')          |  58.7495 |  58.6022 |  0.0025 | 0.0300 | PASS         | n=919 team-hours                        |   58.7645 | PASS         |      0.0150 |
| ('per60_score', '+1')         |  54.6918 |  54.1359 |  0.0103 | 0.0300 | PASS         | n=476 team-hours                        |   54.7076 | PASS         |      0.0158 |
| ('per60_score', '+2')         |  52.0908 |  51.3994 |  0.0135 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   52.1224 | UNDERPOWERED |      0.0315 |
| ('per60_score', '>=+3')       |  49.8634 |  49.2586 |  0.0123 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   49.9009 | UNDERPOWERED |      0.0375 |
| ('team_game', 'mean')         |  58.8639 |  59.4832 | -0.0104 | 0.0300 | PASS         | n=2624 team-games                       |   58.8897 | PASS         |      0.0259 |
| ('team_game', 'sd')           |   9.8854 |  11.6141 | -0.1488 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.8890 | NO-TOLERANCE |      0.0036 |
| ('team_game_P', '[0,40)')     |   0.0172 |   0.0286 | -0.3997 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0170 | NO-TOLERANCE |      0.0002 |
| ('team_game_P', '[40,50)')    |   0.1550 |   0.1700 | -0.0881 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1543 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '[50,60)')    |   0.3706 |   0.3266 |  0.1346 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3700 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.3159 |   0.2851 |  0.1083 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3166 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '>=70')       |   0.1413 |   0.1898 | -0.2552 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1422 | NO-TOLERANCE |      0.0008 |
| ('game', 'corr_home_away')    |  -0.2352 |  -0.4126 | -0.4300 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2380 | NO-TOLERANCE |      0.0028 |

### Decomposition, attempts per team-game: actual 59.483, sim 58.864, sim - actual -0.619 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +0.9687 |
| (s) score-state visits x (bucket rate - mean rate)         |                -0.0060 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0765 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict     |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:------------|
| 5v5     |  58.3508 |  58.5259 |  0.1751 |         0.2660 |                  -0.0091 |     -0.0818 | 1.7505 | CLEAN       |
| PP      | 101.6226 | 101.0280 | -0.5946 |        -0.7057 |                   0.0345 |      0.0767 | 3.0487 | CLEAN       |
| PK      |  14.3173 |  14.0037 | -0.3136 |        -0.3347 |                  -0.0056 |      0.0268 | 0.4295 | CLEAN       |
| 4v4     |  48.6237 |  49.9990 |  1.3753 |         0.8432 |                   0.1144 |      0.4177 | 1.4587 | CLEAN       |
| 3v3     |  55.2313 |  55.5893 |  0.3580 |         2.9801 |                  -0.0443 |     -2.5777 | 1.6569 | COMPENSATED |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.2394 |  60.2558 |   0.0163 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.2846 | UNDERPOWERED |      0.0452 |
| ('per60_state', 'PP')         | 105.2229 | 102.9062 |   0.0225 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.2943 | UNDERPOWERED |      0.0714 |
| ('per60_state', 'PK')         |  14.6467 |  13.3181 |   0.0998 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.6957 | UNDERPOWERED |      0.0490 |
| ('per60_state', '4v4')        |  50.8268 |  51.5258 |  -0.0136 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.7557 | UNDERPOWERED |      0.0711 |
| ('per60_state', '3v3')        |  51.5854 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   34.9776 | UNDERPOWERED |     16.6078 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  66.0763 |  65.1965 |   0.0135 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   65.8214 | UNDERPOWERED |      0.2549 |
| ('per60_score', '-2')         |  66.4940 |  71.0331 |  -0.0639 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   66.4407 | UNDERPOWERED |      0.0533 |
| ('per60_score', '-1')         |  65.2405 |  65.7393 |  -0.0076 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   65.3168 | UNDERPOWERED |      0.0763 |
| ('per60_score', '0')          |  62.0722 |  60.2059 |   0.0310 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.2159 | UNDERPOWERED |      0.1438 |
| ('per60_score', '+1')         |  56.5589 |  56.3612 |   0.0035 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   56.6622 | UNDERPOWERED |      0.1033 |
| ('per60_score', '+2')         |  53.3576 |  54.3527 |  -0.0183 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   53.2858 | UNDERPOWERED |      0.0719 |
| ('per60_score', '>=+3')       |  51.3043 |  47.3922 |   0.0825 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.1910 | UNDERPOWERED |      0.1133 |
| ('team_game', 'mean')         |  62.7300 |  63.5814 |  -0.0134 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.7902 | UNDERPOWERED |      0.0602 |
| ('team_game', 'sd')           |  11.9846 |  14.6140 |  -0.1799 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   12.0604 | NO-TOLERANCE |      0.0759 |
| ('team_game_P', '[0,40)')     |   0.0093 |   0.0174 |  -0.4667 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0104 | NO-TOLERANCE |      0.0011 |
| ('team_game_P', '[40,50)')    |   0.1033 |   0.0930 |   0.1103 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1007 | NO-TOLERANCE |      0.0026 |
| ('team_game_P', '[50,60)')    |   0.3116 |   0.3547 |  -0.1214 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3107 | NO-TOLERANCE |      0.0009 |
| ('team_game_P', '[60,70)')    |   0.3259 |   0.2035 |   0.6016 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3288 | NO-TOLERANCE |      0.0029 |
| ('team_game_P', '>=70')       |   0.2499 |   0.3314 |  -0.2459 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2494 | NO-TOLERANCE |      0.0006 |
| ('game', 'corr_home_away')    |   0.0088 |  -0.0772 |  -1.1142 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0258 | NO-TOLERANCE |      0.0170 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.730, sim - actual -0.851 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -0.2824 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0080 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.2299 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.2394 |   0.9836 |         1.2744 |                  -0.0096 |     -0.2812 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.2229 |   2.3167 |         1.9991 |                   0.5260 |     -0.2084 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6467 |   1.3286 |         1.4198 |                  -0.0563 |     -0.0349 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.8268 |  -0.6990 |        -1.2389 |                   0.1397 |      0.4001 |   1.5458 | CLEAN     |
| 3v3     | nan      |  51.5854 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.6960 |  58.4717 |  0.0038 | 0.0300 | PASS         | n=2796 team-games                       |   58.7226 | PASS         |      0.0266 |
| ('per60_state', 'PP')         | 101.3026 | 101.7125 | -0.0040 | 0.0300 | PASS         | n=2796 team-games                       |  101.3276 | PASS         |      0.0250 |
| ('per60_state', 'PK')         |  14.0458 |  14.2473 | -0.0141 | 0.0300 | PASS         | n=2796 team-games                       |   14.0420 | PASS         |      0.0038 |
| ('per60_state', '4v4')        |  50.0515 |  48.8019 |  0.0256 | 0.0300 | PASS         | n=2796 team-games                       |   50.0552 | PASS         |      0.0037 |
| ('per60_state', '3v3')        |  55.5885 |  55.2313 |  0.0065 | 0.0300 | PASS         | n=2796 team-games                       |   55.8967 | PASS         |      0.3082 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  63.0819 |  65.4146 | -0.0357 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   63.0567 | UNDERPOWERED |      0.0252 |
| ('per60_score', '-2')         |  63.8082 |  68.3894 | -0.0670 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   63.8536 | UNDERPOWERED |      0.0455 |
| ('per60_score', '-1')         |  62.6180 |  64.3039 | -0.0262 | 0.0300 | PASS         | n=508 team-hours                        |   62.6606 | PASS         |      0.0426 |
| ('per60_score', '0')          |  58.9635 |  58.7080 |  0.0044 | 0.0300 | PASS         | n=984 team-hours                        |   58.9865 | PASS         |      0.0230 |
| ('per60_score', '+1')         |  54.8072 |  54.2774 |  0.0098 | 0.0300 | PASS         | n=508 team-hours                        |   54.8278 | PASS         |      0.0206 |
| ('per60_score', '+2')         |  52.1690 |  51.5720 |  0.0116 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   52.1945 | UNDERPOWERED |      0.0255 |
| ('per60_score', '>=+3')       |  49.9513 |  49.1341 |  0.0166 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   49.9807 | UNDERPOWERED |      0.0295 |
| ('team_game', 'mean')         |  59.1017 |  59.7353 | -0.0106 | 0.0300 | PASS         | n=2796 team-games                       |   59.1297 | PASS         |      0.0280 |
| ('team_game', 'sd')           |  10.0701 |  11.8616 | -0.1510 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.0798 | NO-TOLERANCE |      0.0096 |
| ('team_game_P', '[0,40)')     |   0.0167 |   0.0279 | -0.4023 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0166 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1518 |   0.1652 | -0.0813 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1510 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '[50,60)')    |   0.3669 |   0.3283 |  0.1176 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3663 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.3166 |   0.2800 |  0.1304 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3173 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '>=70')       |   0.1480 |   0.1985 | -0.2543 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1488 | NO-TOLERANCE |      0.0007 |
| ('game', 'corr_home_away')    |  -0.2032 |  -0.3716 | -0.4532 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2038 | NO-TOLERANCE |      0.0006 |

### Decomposition, attempts per team-game: actual 59.735, sim 59.102, sim - actual -0.634 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                +0.8954 |
| (s) score-state visits x (bucket rate - mean rate)         |                -0.0051 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0895 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict     |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:------------|
| 5v5     |  58.4717 |  58.6960 |  0.2244 |         0.3301 |                  -0.0086 |     -0.0971 | 1.7542 | CLEAN       |
| PP      | 101.7125 | 101.3026 | -0.4099 |        -0.5163 |                   0.0598 |      0.0466 | 3.0514 | CLEAN       |
| PK      |  14.2473 |  14.0458 | -0.2015 |        -0.2119 |                  -0.0083 |      0.0186 | 0.4274 | CLEAN       |
| 4v4     |  48.8019 |  50.0515 |  1.2496 |         0.7153 |                   0.1205 |      0.4137 | 1.4641 | CLEAN       |
| 3v3     |  55.2313 |  55.5885 |  0.3572 |         2.9801 |                  -0.0490 |     -2.5738 | 1.6569 | COMPENSATED |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.151 (95% CI 1.010..1.329) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.517 |         54.316 |        560.000 |
|  2 |      56.508 |         56.489 |        559.000 |
|  3 |      58.777 |         58.333 |        559.000 |
|  4 |      60.411 |         59.643 |        559.000 |
|  5 |      64.278 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.115 (95% CI 0.968..1.321) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.178 |         53.883 |        560.000 |
|  2 |      56.990 |         57.551 |        559.000 |
|  3 |      58.725 |         59.405 |        559.000 |
|  4 |      60.099 |         59.246 |        559.000 |
|  5 |      63.490 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        60.07 |            57.98 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        58.45 |            60.01 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        60.06 |            61.62 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        55.92 |            60.06 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        62.76 |            59.83 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        55.14 |            58.38 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        59.54 |            58.22 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        54.81 |            63.59 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        60.60 |            57.69 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        58.71 |            61.74 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        67.50 |            49.89 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        64.61 |            55.38 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        57.94 |            58.24 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        58.38 |            60.53 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        52.07 |            61.29 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        54.57 |            61.34 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        60.77 |            56.98 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.86 |            58.94 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.91 |            59.83 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        62.58 |            55.75 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        63.94 |            55.98 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        55.94 |            56.25 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.94 |            66.15 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        60.83 |            58.34 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.87 |            55.94 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        55.35 |            65.45 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.89 |            60.89 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        55.91 |            60.18 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        58.37 |            59.65 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        58.95 |            60.68 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        58.37 |            60.62 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        61.50 |            57.08 | UNDERPOWERED |

