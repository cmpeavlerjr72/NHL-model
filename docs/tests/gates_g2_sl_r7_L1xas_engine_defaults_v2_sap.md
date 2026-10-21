# G2 re-check, SL-R7 L1x-as closed loop (oracle goalie) (SA-R3): engine_defaults_v2_sap, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **INV-77 closed loop, NEW engine DEFAULT table set** (Lane E4): stage 4 = L1x-as, block = B1a-as (SB-R5), 3v3 OT attempt level ON (EG-R1 part B), goal = C1s-sap (G-R4, sc_game flag) (ORACLE GOALIE, D8), miss S0t STAND-IN. Pull and shootout flags OFF (no goalie pull, 50/50 shootout stub; no rebounds). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)

Generated 2026-10-21 16:02:28 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.5235 |  58.3508 |  0.0030 | 0.0300 | PASS         | n=2624 team-games                       |   58.5482 | PASS         |      0.0247 |
| ('per60_state', 'PP')         | 101.0188 | 101.6226 | -0.0059 | 0.0300 | PASS         | n=2624 team-games                       |  101.0466 | PASS         |      0.0278 |
| ('per60_state', 'PK')         |  14.0002 |  14.3173 | -0.0221 | 0.0300 | PASS         | n=2624 team-games                       |   13.9931 | PASS         |      0.0071 |
| ('per60_state', '4v4')        |  49.9513 |  48.6237 |  0.0273 | 0.0300 | PASS         | n=2624 team-games                       |   49.9429 | PASS         |      0.0084 |
| ('per60_state', '3v3')        |  55.5084 |  55.2313 |  0.0050 | 0.0300 | PASS         | n=2624 team-games                       |   55.7521 | PASS         |      0.2437 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.8798 |  65.4302 | -0.0390 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   62.8554 | UNDERPOWERED |      0.0244 |
| ('per60_score', '-2')         |  63.7229 |  68.2253 | -0.0660 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   63.7611 | UNDERPOWERED |      0.0382 |
| ('per60_score', '-1')         |  62.4569 |  64.2065 | -0.0272 | 0.0300 | PASS         | n=476 team-hours                        |   62.5041 | PASS         |      0.0471 |
| ('per60_score', '0')          |  58.7416 |  58.6022 |  0.0024 | 0.0300 | PASS         | n=919 team-hours                        |   58.7626 | PASS         |      0.0210 |
| ('per60_score', '+1')         |  54.6856 |  54.1359 |  0.0102 | 0.0300 | PASS         | n=476 team-hours                        |   54.6876 | PASS         |      0.0020 |
| ('per60_score', '+2')         |  52.0636 |  51.3994 |  0.0129 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   52.1189 | UNDERPOWERED |      0.0553 |
| ('per60_score', '>=+3')       |  49.7975 |  49.2586 |  0.0109 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   49.8077 | UNDERPOWERED |      0.0102 |
| ('team_game', 'mean')         |  58.8320 |  59.4832 | -0.0109 | 0.0300 | PASS         | n=2624 team-games                       |   58.8558 | PASS         |      0.0238 |
| ('team_game', 'sd')           |   9.8874 |  11.6141 | -0.1487 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.8895 | NO-TOLERANCE |      0.0021 |
| ('team_game_P', '[0,40)')     |   0.0174 |   0.0286 | -0.3924 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0172 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1558 |   0.1700 | -0.0835 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1549 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '[50,60)')    |   0.3707 |   0.3266 |  0.1351 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3704 | NO-TOLERANCE |      0.0003 |
| ('team_game_P', '[60,70)')    |   0.3153 |   0.2851 |  0.1062 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3162 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '>=70')       |   0.1408 |   0.1898 | -0.2582 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1412 | NO-TOLERANCE |      0.0004 |
| ('game', 'corr_home_away')    |  -0.2388 |  -0.4126 | -0.4213 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2414 | NO-TOLERANCE |      0.0026 |

### Decomposition, attempts per team-game: actual 59.483, sim 58.832, sim - actual -0.651 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +0.9400 |
| (s) score-state visits x (bucket rate - mean rate)         |                -0.0077 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0779 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict     |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:------------|
| 5v5     |  58.3508 |  58.5235 |  0.1728 |         0.2660 |                  -0.0099 |     -0.0834 | 1.7505 | CLEAN       |
| PP      | 101.6226 | 101.0188 | -0.6038 |        -0.7057 |                   0.0254 |      0.0765 | 3.0487 | CLEAN       |
| PK      |  14.3173 |  14.0002 | -0.3171 |        -0.3347 |                  -0.0066 |      0.0242 | 0.4295 | CLEAN       |
| 4v4     |  48.6237 |  49.9513 |  1.3276 |         0.8432 |                   0.1025 |      0.3819 | 1.4587 | CLEAN       |
| 3v3     |  55.2313 |  55.5084 |  0.2771 |         2.9801 |                  -0.0468 |     -2.6561 | 1.6569 | COMPENSATED |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.2436 |  60.2558 |   0.0164 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.2966 | UNDERPOWERED |      0.0531 |
| ('per60_state', 'PP')         | 105.1399 | 102.9062 |   0.0217 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.2300 | UNDERPOWERED |      0.0902 |
| ('per60_state', 'PK')         |  14.6482 |  13.3181 |   0.0999 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.6755 | UNDERPOWERED |      0.0272 |
| ('per60_state', '4v4')        |  50.8591 |  51.5258 |  -0.0129 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.7844 | UNDERPOWERED |      0.0748 |
| ('per60_state', '3v3')        |  51.6393 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   34.9776 | UNDERPOWERED |     16.6618 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  66.1551 |  65.1965 |   0.0147 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   65.9191 | UNDERPOWERED |      0.2360 |
| ('per60_score', '-2')         |  66.5231 |  71.0331 |  -0.0635 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   66.5870 | UNDERPOWERED |      0.0639 |
| ('per60_score', '-1')         |  65.2958 |  65.7393 |  -0.0067 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   65.3289 | UNDERPOWERED |      0.0331 |
| ('per60_score', '0')          |  62.0623 |  60.2059 |   0.0308 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.1812 | UNDERPOWERED |      0.1189 |
| ('per60_score', '+1')         |  56.5100 |  56.3612 |   0.0026 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   56.6371 | UNDERPOWERED |      0.1271 |
| ('per60_score', '+2')         |  53.3974 |  54.3527 |  -0.0176 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   53.3793 | UNDERPOWERED |      0.0181 |
| ('per60_score', '>=+3')       |  51.1896 |  47.3922 |   0.0801 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.0990 | UNDERPOWERED |      0.0906 |
| ('team_game', 'mean')         |  62.6702 |  63.5814 |  -0.0143 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.7491 | UNDERPOWERED |      0.0790 |
| ('team_game', 'sd')           |  11.9224 |  14.6140 |  -0.1842 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   12.0088 | NO-TOLERANCE |      0.0864 |
| ('team_game_P', '[0,40)')     |   0.0094 |   0.0174 |  -0.4633 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0105 | NO-TOLERANCE |      0.0011 |
| ('team_game_P', '[40,50)')    |   0.1039 |   0.0930 |   0.1169 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1006 | NO-TOLERANCE |      0.0033 |
| ('team_game_P', '[50,60)')    |   0.3128 |   0.3547 |  -0.1180 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3122 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.3255 |   0.2035 |   0.5994 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3285 | NO-TOLERANCE |      0.0030 |
| ('team_game_P', '>=70')       |   0.2485 |   0.3314 |  -0.2502 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2483 | NO-TOLERANCE |      0.0002 |
| ('game', 'corr_home_away')    |  -0.0009 |  -0.0772 |  -0.9882 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0198 | NO-TOLERANCE |      0.0207 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.670, sim - actual -0.911 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -0.3400 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0031 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.2272 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.2436 |   0.9878 |         1.2744 |                  -0.0140 |     -0.2726 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.1399 |   2.2337 |         1.9991 |                   0.5130 |     -0.2785 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6482 |   1.3302 |         1.4198 |                  -0.0568 |     -0.0328 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.8591 |  -0.6667 |        -1.2389 |                   0.1533 |      0.4189 |   1.5458 | CLEAN     |
| 3v3     | nan      |  51.6393 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.6940 |  58.4717 |  0.0038 | 0.0300 | PASS         | n=2796 team-games                       |   58.7205 | PASS         |      0.0266 |
| ('per60_state', 'PP')         | 101.2881 | 101.7125 | -0.0042 | 0.0300 | PASS         | n=2796 team-games                       |  101.3202 | PASS         |      0.0322 |
| ('per60_state', 'PK')         |  14.0426 |  14.2473 | -0.0144 | 0.0300 | PASS         | n=2796 team-games                       |   14.0377 | PASS         |      0.0048 |
| ('per60_state', '4v4')        |  50.0089 |  48.8019 |  0.0247 | 0.0300 | PASS         | n=2796 team-games                       |   49.9962 | PASS         |      0.0128 |
| ('per60_state', '3v3')        |  55.5076 |  55.2313 |  0.0050 | 0.0300 | PASS         | n=2796 team-games                       |   55.7486 | PASS         |      0.2410 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  63.0798 |  65.4146 | -0.0357 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   63.0444 | UNDERPOWERED |      0.0353 |
| ('per60_score', '-2')         |  63.8942 |  68.3894 | -0.0657 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   63.9346 | UNDERPOWERED |      0.0404 |
| ('per60_score', '-1')         |  62.6318 |  64.3039 | -0.0260 | 0.0300 | PASS         | n=508 team-hours                        |   62.6772 | PASS         |      0.0454 |
| ('per60_score', '0')          |  58.9568 |  58.7080 |  0.0042 | 0.0300 | PASS         | n=984 team-hours                        |   58.9842 | PASS         |      0.0274 |
| ('per60_score', '+1')         |  54.7980 |  54.2774 |  0.0096 | 0.0300 | PASS         | n=508 team-hours                        |   54.8071 | PASS         |      0.0091 |
| ('per60_score', '+2')         |  52.1452 |  51.5720 |  0.0111 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   52.1964 | UNDERPOWERED |      0.0512 |
| ('per60_score', '>=+3')       |  49.8825 |  49.1341 |  0.0152 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   49.8874 | UNDERPOWERED |      0.0049 |
| ('team_game', 'mean')         |  59.0681 |  59.7353 | -0.0112 | 0.0300 | PASS         | n=2796 team-games                       |   59.0953 | PASS         |      0.0272 |
| ('team_game', 'sd')           |  10.0669 |  11.8616 | -0.1513 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.0763 | NO-TOLERANCE |      0.0094 |
| ('team_game_P', '[0,40)')     |   0.0169 |   0.0279 | -0.3951 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0168 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[40,50)')    |   0.1526 |   0.1652 | -0.0765 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1516 | NO-TOLERANCE |      0.0010 |
| ('team_game_P', '[50,60)')    |   0.3672 |   0.3283 |  0.1183 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3668 | NO-TOLERANCE |      0.0003 |
| ('team_game_P', '[60,70)')    |   0.3160 |   0.2800 |  0.1283 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3169 | NO-TOLERANCE |      0.0010 |
| ('team_game_P', '>=70')       |   0.1474 |   0.1985 | -0.2574 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1478 | NO-TOLERANCE |      0.0004 |
| ('game', 'corr_home_away')    |  -0.2076 |  -0.3716 | -0.4413 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2076 | NO-TOLERANCE |      0.0000 |

### Decomposition, attempts per team-game: actual 59.735, sim 59.068, sim - actual -0.667 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                +0.8650 |
| (s) score-state visits x (bucket rate - mean rate)         |                -0.0073 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0905 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict     |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:------------|
| 5v5     |  58.4717 |  58.6940 |  0.2223 |         0.3301 |                  -0.0098 |     -0.0979 | 1.7542 | CLEAN       |
| PP      | 101.7125 | 101.2881 | -0.4244 |        -0.5163 |                   0.0491 |      0.0428 | 3.0514 | CLEAN       |
| PK      |  14.2473 |  14.0426 | -0.2048 |        -0.2119 |                  -0.0092 |      0.0163 | 0.4274 | CLEAN       |
| 4v4     |  48.8019 |  50.0089 |  1.2070 |         0.7153 |                   0.1100 |      0.3817 | 1.4641 | CLEAN       |
| 3v3     |  55.2313 |  55.5076 |  0.2763 |         2.9801 |                  -0.0518 |     -2.6520 | 1.6569 | COMPENSATED |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.150 (95% CI 1.010..1.329) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.518 |         54.316 |        560.000 |
|  2 |      56.505 |         56.489 |        559.000 |
|  3 |      58.775 |         58.333 |        559.000 |
|  4 |      60.407 |         59.643 |        559.000 |
|  5 |      64.277 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.115 (95% CI 0.968..1.321) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.176 |         53.883 |        560.000 |
|  2 |      56.990 |         57.551 |        559.000 |
|  3 |      58.721 |         59.405 |        559.000 |
|  4 |      60.093 |         59.246 |        559.000 |
|  5 |      63.491 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        60.04 |            57.98 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        58.42 |            59.98 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        60.00 |            61.58 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        55.88 |            60.02 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        62.72 |            59.79 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        55.11 |            58.36 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        59.50 |            58.20 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        54.78 |            63.57 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        60.56 |            57.67 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        58.68 |            61.69 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        67.47 |            49.85 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        64.56 |            55.33 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        57.94 |            58.20 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        58.34 |            60.49 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        52.05 |            61.27 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        54.54 |            61.31 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        60.74 |            56.94 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.83 |            58.88 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.87 |            59.79 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        62.54 |            55.72 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        63.91 |            55.96 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        55.92 |            56.22 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.89 |            66.14 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        60.81 |            58.29 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.83 |            55.92 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        55.31 |            65.41 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.86 |            60.86 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        55.90 |            60.12 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        58.29 |            59.61 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        58.94 |            60.65 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        58.34 |            60.58 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        61.46 |            57.05 | UNDERPOWERED |

