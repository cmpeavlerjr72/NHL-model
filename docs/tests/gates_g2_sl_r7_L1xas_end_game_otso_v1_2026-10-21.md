# G2 re-check, SL-R7 L1x-as closed loop (oracle goalie) (SA-R3): end_game_otso_v1, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **EG-R1 closed loop (Lane H8b, on Lane H8a's pull).** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t; goalie pull P1 + EN cascade (EN attempt and EN goal levels STAND-IN); 3v3 OT attempt level = own as-of M1 K500 (served A3g-c re-levelled); shootout = S1 (rules mechanics, as-of success and home-first share). No delayed-penalty state (INV-70); no rebounds / faceoffs (stage 7 absent). Report text produced by the SL-R7 grader.

Generated 2026-10-21 14:56:11 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.6344 |  58.3508 |  0.0049 | 0.0300 | PASS         | n=2624 team-games                       |   58.6572 | PASS         |      0.0228 |
| ('per60_state', 'PP')         | 101.0883 | 101.6226 | -0.0053 | 0.0300 | PASS         | n=2624 team-games                       |  101.1184 | PASS         |      0.0301 |
| ('per60_state', 'PK')         |  14.0149 |  14.3173 | -0.0211 | 0.0300 | PASS         | n=2624 team-games                       |   14.0078 | PASS         |      0.0070 |
| ('per60_state', '4v4')        |  50.1883 |  48.6237 |  0.0322 | 0.0300 | FAIL         | n=2624 team-games                       |   50.1672 | FAIL         |      0.0211 |
| ('per60_state', '3v3')        |  55.5884 |  55.2313 |  0.0065 | 0.0300 | PASS         | n=2624 team-games                       |   55.7526 | PASS         |      0.1642 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  65.5694 |  65.4302 |  0.0021 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   65.5283 | UNDERPOWERED |      0.0410 |
| ('per60_score', '-2')         |  70.9534 |  68.2253 |  0.0400 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   71.0593 | UNDERPOWERED |      0.1059 |
| ('per60_score', '-1')         |  66.0497 |  64.2065 |  0.0287 | 0.0300 | PASS         | n=476 team-hours                        |   66.0854 | PASS         |      0.0357 |
| ('per60_score', '0')          |  58.7362 |  58.6022 |  0.0023 | 0.0300 | PASS         | n=919 team-hours                        |   58.7489 | PASS         |      0.0127 |
| ('per60_score', '+1')         |  56.1947 |  54.1359 |  0.0380 | 0.0300 | FAIL         | n=476 team-hours                        |   56.2147 | FAIL         |      0.0199 |
| ('per60_score', '+2')         |  54.9516 |  51.3994 |  0.0691 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   54.9879 | UNDERPOWERED |      0.0363 |
| ('per60_score', '>=+3')       |  50.5402 |  49.2586 |  0.0260 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   50.5639 | UNDERPOWERED |      0.0238 |
| ('team_game', 'mean')         |  57.9963 |  59.4832 | -0.0250 | 0.0300 | PASS         | n=2624 team-games                       |   58.0201 | PASS         |      0.0238 |
| ('team_game', 'sd')           |   9.8582 |  11.6141 | -0.1512 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.8627 | NO-TOLERANCE |      0.0045 |
| ('team_game_P', '[0,40)')     |   0.0220 |   0.0286 | -0.2317 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0219 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[40,50)')    |   0.1752 |   0.1700 |  0.0306 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1744 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '[50,60)')    |   0.3809 |   0.3266 |  0.1664 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3803 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.2985 |   0.2851 |  0.0471 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2992 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '>=70')       |   0.1234 |   0.1898 | -0.3496 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1241 | NO-TOLERANCE |      0.0007 |
| ('game', 'corr_home_away')    |  -0.1959 |  -0.4126 | -0.5252 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1993 | NO-TOLERANCE |      0.0034 |

### Decomposition, attempts per team-game: actual 59.483, sim 57.996, sim - actual -1.487 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +0.0071 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0022 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                +0.0094 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict     |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:------------|
| 5v5     |  58.3508 |  58.6344 |  0.2836 |         0.2660 |                  -0.0033 |      0.0209 | 1.7505 | CLEAN       |
| PP      | 101.6226 | 101.0883 | -0.5343 |        -0.7057 |                   0.0513 |      0.1202 | 3.0487 | CLEAN       |
| PK      |  14.3173 |  14.0149 | -0.3025 |        -0.3347 |                  -0.0028 |      0.0350 | 0.4295 | CLEAN       |
| 4v4     |  48.6237 |  50.1883 |  1.5646 |         0.8432 |                   0.1448 |      0.5766 | 1.4587 | FAIL        |
| 3v3     |  55.2313 |  55.5884 |  0.3571 |         2.9801 |                  -0.0368 |     -2.5862 | 1.6569 | COMPENSATED |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.4104 |  60.2558 |   0.0192 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.4501 | UNDERPOWERED |      0.0398 |
| ('per60_state', 'PP')         | 105.4092 | 102.9062 |   0.0243 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.5309 | UNDERPOWERED |      0.1218 |
| ('per60_state', 'PK')         |  14.6644 |  13.3181 |   0.1011 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.7268 | UNDERPOWERED |      0.0624 |
| ('per60_state', '4v4')        |  50.9552 |  51.5258 |  -0.0111 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.8246 | UNDERPOWERED |      0.1306 |
| ('per60_state', '3v3')        |  50.7042 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   31.0832 | UNDERPOWERED |     19.6210 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  68.5757 |  65.1965 |   0.0518 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   68.4575 | UNDERPOWERED |      0.1182 |
| ('per60_score', '-2')         |  73.7919 |  71.0331 |   0.0388 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   73.7544 | UNDERPOWERED |      0.0375 |
| ('per60_score', '-1')         |  68.7952 |  65.7393 |   0.0465 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   68.7236 | UNDERPOWERED |      0.0716 |
| ('per60_score', '0')          |  62.1705 |  60.2059 |   0.0326 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.3111 | UNDERPOWERED |      0.1407 |
| ('per60_score', '+1')         |  58.1284 |  56.3612 |   0.0314 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   58.2346 | UNDERPOWERED |      0.1062 |
| ('per60_score', '+2')         |  56.3802 |  54.3527 |   0.0373 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   56.3462 | UNDERPOWERED |      0.0340 |
| ('per60_score', '>=+3')       |  52.0155 |  47.3922 |   0.0976 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.9305 | UNDERPOWERED |      0.0850 |
| ('team_game', 'mean')         |  62.1085 |  63.5814 |  -0.0232 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.1873 | UNDERPOWERED |      0.0789 |
| ('team_game', 'sd')           |  12.2554 |  14.6140 |  -0.1614 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   12.3240 | NO-TOLERANCE |      0.0686 |
| ('team_game_P', '[0,40)')     |   0.0113 |   0.0174 |  -0.3533 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0127 | NO-TOLERANCE |      0.0014 |
| ('team_game_P', '[40,50)')    |   0.1199 |   0.0930 |   0.2891 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1170 | NO-TOLERANCE |      0.0029 |
| ('team_game_P', '[50,60)')    |   0.3217 |   0.3547 |  -0.0930 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3205 | NO-TOLERANCE |      0.0012 |
| ('team_game_P', '[60,70)')    |   0.3133 |   0.2035 |   0.5396 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3159 | NO-TOLERANCE |      0.0026 |
| ('team_game_P', '>=70')       |   0.2338 |   0.3314 |  -0.2944 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2339 | NO-TOLERANCE |      0.0001 |
| ('game', 'corr_home_away')    |   0.0879 |  -0.0772 |  -2.1395 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1036 | NO-TOLERANCE |      0.0157 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.108, sim - actual -1.473 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -1.0691 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0454 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.1021 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.4104 |   1.1546 |         1.2744 |                   0.0224 |     -0.1422 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.4092 |   2.5030 |         1.9991 |                   0.6129 |     -0.1090 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6644 |   1.3463 |         1.4198 |                  -0.0500 |     -0.0235 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.9552 |  -0.5706 |        -1.2389 |                   0.1555 |      0.5127 |   1.5458 | CLEAN     |
| 3v3     | nan      |  50.7042 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.8095 |  58.4717 |  0.0058 | 0.0300 | PASS         | n=2796 team-games                       |   58.8334 | PASS         |      0.0239 |
| ('per60_state', 'PP')         | 101.3718 | 101.7125 | -0.0033 | 0.0300 | PASS         | n=2796 team-games                       |  101.4082 | PASS         |      0.0365 |
| ('per60_state', 'PK')         |  14.0575 |  14.2473 | -0.0133 | 0.0300 | PASS         | n=2796 team-games                       |   14.0550 | PASS         |      0.0024 |
| ('per60_state', '4v4')        |  50.2365 |  48.8019 |  0.0294 | 0.0300 | PASS         | n=2796 team-games                       |   50.2084 | PASS         |      0.0280 |
| ('per60_state', '3v3')        |  55.5876 |  55.2313 |  0.0065 | 0.0300 | PASS         | n=2796 team-games                       |   55.7494 | PASS         |      0.1618 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  65.7519 |  65.4146 |  0.0052 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   65.7091 | UNDERPOWERED |      0.0428 |
| ('per60_score', '-2')         |  71.1277 |  68.3894 |  0.0400 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   71.2258 | UNDERPOWERED |      0.0981 |
| ('per60_score', '-1')         |  66.2198 |  64.3039 |  0.0298 | 0.0300 | PASS         | n=508 team-hours                        |   66.2478 | FAIL         |      0.0280 |
| ('per60_score', '0')          |  58.9596 |  58.7080 |  0.0043 | 0.0300 | PASS         | n=984 team-hours                        |   58.9805 | PASS         |      0.0208 |
| ('per60_score', '+1')         |  56.3146 |  54.2774 |  0.0375 | 0.0300 | FAIL         | n=508 team-hours                        |   56.3390 | FAIL         |      0.0245 |
| ('per60_score', '+2')         |  55.0393 |  51.5720 |  0.0672 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   55.0718 | UNDERPOWERED |      0.0325 |
| ('per60_score', '>=+3')       |  50.6297 |  49.1341 |  0.0304 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   50.6483 | UNDERPOWERED |      0.0185 |
| ('team_game', 'mean')         |  58.2493 |  59.7353 | -0.0249 | 0.0300 | PASS         | n=2796 team-games                       |   58.2765 | PASS         |      0.0272 |
| ('team_game', 'sd')           |  10.0708 |  11.8616 | -0.1510 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.0814 | NO-TOLERANCE |      0.0106 |
| ('team_game_P', '[0,40)')     |   0.0213 |   0.0279 | -0.2364 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0214 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1718 |   0.1652 |  0.0395 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1709 | NO-TOLERANCE |      0.0009 |
| ('team_game_P', '[50,60)')    |   0.3773 |   0.3283 |  0.1492 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3767 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.2994 |   0.2800 |  0.0691 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3002 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '>=70')       |   0.1302 |   0.1985 | -0.3439 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1309 | NO-TOLERANCE |      0.0006 |
| ('game', 'corr_home_away')    |  -0.1583 |  -0.3716 | -0.5741 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1593 | NO-TOLERANCE |      0.0011 |

### Decomposition, attempts per team-game: actual 59.735, sim 58.249, sim - actual -1.486 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                -0.0565 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0048 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                +0.0001 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict     |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:------------|
| 5v5     |  58.4717 |  58.8095 |  0.3378 |         0.3301 |                  -0.0012 |      0.0090 | 1.7542 | CLEAN       |
| PP      | 101.7125 | 101.3718 | -0.3407 |        -0.5163 |                   0.0806 |      0.0950 | 3.0514 | CLEAN       |
| PK      |  14.2473 |  14.0575 | -0.1899 |        -0.2119 |                  -0.0052 |      0.0272 | 0.4274 | CLEAN       |
| 4v4     |  48.8019 |  50.2365 |  1.4346 |         0.7153 |                   0.1500 |      0.5692 | 1.4641 | CLEAN       |
| 3v3     |  55.2313 |  55.5876 |  0.3563 |         2.9801 |                  -0.0404 |     -2.5834 | 1.6569 | COMPENSATED |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.155 (95% CI 1.014..1.334) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.596 |         54.316 |        560.000 |
|  2 |      56.625 |         56.489 |        559.000 |
|  3 |      58.914 |         58.333 |        559.000 |
|  4 |      60.522 |         59.643 |        559.000 |
|  5 |      64.398 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.113 (95% CI 0.967..1.320) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.308 |         53.883 |        560.000 |
|  2 |      57.106 |         57.551 |        559.000 |
|  3 |      58.834 |         59.405 |        559.000 |
|  4 |      60.195 |         59.246 |        559.000 |
|  5 |      63.608 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        59.16 |            57.19 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        57.61 |            59.07 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        59.20 |            60.70 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        55.20 |            59.03 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        61.75 |            59.03 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        54.33 |            57.57 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        58.62 |            57.44 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        53.97 |            62.62 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        59.76 |            56.84 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        57.94 |            60.78 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        66.53 |            49.24 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        63.66 |            54.74 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        57.17 |            57.38 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        57.62 |            59.58 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        51.29 |            60.42 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        53.73 |            60.47 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        59.83 |            56.19 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.05 |            58.15 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.00 |            58.95 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        61.67 |            54.92 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        63.11 |            55.21 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        55.10 |            55.48 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.04 |            65.20 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        59.95 |            57.60 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.03 |            55.09 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        54.45 |            64.52 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.01 |            59.98 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        55.14 |            59.33 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        57.60 |            58.77 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        58.19 |            59.69 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        57.47 |            59.73 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        60.63 |            56.25 | UNDERPOWERED |

