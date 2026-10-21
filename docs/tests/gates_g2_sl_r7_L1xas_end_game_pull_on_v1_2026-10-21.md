# G2 re-check, SL-R7 L1x-as closed loop (oracle goalie) (SA-R3): end_game_pull_on_v1, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **EG-R1 part A closed loop (Lane H8a), goalie pull ON.** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t, pull P1 + EN cascade (EN attempt and EN goal levels STAND-IN). No delayed-penalty state (INV-70); OT = stage-1 3v3, shootout 50 / 50 stub; no rebounds. Report text produced by the SL-R7 grader.

Generated 2026-10-21 14:21:04 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.6344 |  58.3508 |  0.0049 | 0.0300 | PASS         | n=2624 team-games                       |   58.6572 | PASS         |      0.0228 |
| ('per60_state', 'PP')         | 101.0837 | 101.6226 | -0.0053 | 0.0300 | PASS         | n=2624 team-games                       |  101.1126 | PASS         |      0.0289 |
| ('per60_state', 'PK')         |  14.0146 |  14.3173 | -0.0211 | 0.0300 | PASS         | n=2624 team-games                       |   14.0074 | PASS         |      0.0072 |
| ('per60_state', '4v4')        |  50.1839 |  48.6237 |  0.0321 | 0.0300 | FAIL         | n=2624 team-games                       |   50.1618 | FAIL         |      0.0221 |
| ('per60_state', '3v3')        |  58.2271 |  55.2313 |  0.0542 | 0.0300 | FAIL         | n=2624 team-games                       |   58.4111 | FAIL         |      0.1840 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  65.5694 |  65.4302 |  0.0021 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   65.5284 | UNDERPOWERED |      0.0410 |
| ('per60_score', '-2')         |  70.9536 |  68.2253 |  0.0400 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   71.0596 | UNDERPOWERED |      0.1060 |
| ('per60_score', '-1')         |  66.0496 |  64.2065 |  0.0287 | 0.0300 | PASS         | n=476 team-hours                        |   66.0851 | PASS         |      0.0356 |
| ('per60_score', '0')          |  58.8109 |  58.6022 |  0.0036 | 0.0300 | PASS         | n=919 team-hours                        |   58.8238 | PASS         |      0.0129 |
| ('per60_score', '+1')         |  56.1948 |  54.1359 |  0.0380 | 0.0300 | FAIL         | n=476 team-hours                        |   56.2147 | FAIL         |      0.0199 |
| ('per60_score', '+2')         |  54.9516 |  51.3994 |  0.0691 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   54.9880 | UNDERPOWERED |      0.0363 |
| ('per60_score', '>=+3')       |  50.5402 |  49.2586 |  0.0260 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   50.5640 | UNDERPOWERED |      0.0238 |
| ('team_game', 'mean')         |  58.0106 |  59.4832 | -0.0248 | 0.0300 | PASS         | n=2624 team-games                       |   58.0345 | PASS         |      0.0239 |
| ('team_game', 'sd')           |   9.8665 |  11.6141 | -0.1505 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.8714 | NO-TOLERANCE |      0.0049 |
| ('team_game_P', '[0,40)')     |   0.0219 |   0.0286 | -0.2325 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0219 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[40,50)')    |   0.1749 |   0.1700 |  0.0293 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1742 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '[50,60)')    |   0.3807 |   0.3266 |  0.1656 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3801 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.2985 |   0.2851 |  0.0472 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2992 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '>=70')       |   0.1239 |   0.1898 | -0.3470 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1246 | NO-TOLERANCE |      0.0006 |
| ('game', 'corr_home_away')    |  -0.1945 |  -0.4126 | -0.5286 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1979 | NO-TOLERANCE |      0.0034 |

### Decomposition, attempts per team-game: actual 59.483, sim 58.011, sim - actual -1.473 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                -0.0056 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0021 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                +0.0365 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.3508 |  58.6344 |  0.2836 |         0.2660 |                  -0.0033 |      0.0209 | 1.7505 | CLEAN     |
| PP      | 101.6226 | 101.0837 | -0.5388 |        -0.7057 |                   0.0511 |      0.1158 | 3.0487 | CLEAN     |
| PK      |  14.3173 |  14.0146 | -0.3027 |        -0.3347 |                  -0.0028 |      0.0348 | 0.4295 | CLEAN     |
| 4v4     |  48.6237 |  50.1839 |  1.5602 |         0.8432 |                   0.1445 |      0.5725 | 1.4587 | FAIL      |
| 3v3     |  55.2313 |  58.2271 |  2.9958 |         2.9801 |                  -0.0376 |      0.0533 | 1.6569 | FAIL      |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.4104 |  60.2558 |   0.0192 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.4501 | UNDERPOWERED |      0.0398 |
| ('per60_state', 'PP')         | 105.4092 | 102.9062 |   0.0243 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.5309 | UNDERPOWERED |      0.1218 |
| ('per60_state', 'PK')         |  14.6644 |  13.3181 |   0.1011 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.7268 | UNDERPOWERED |      0.0624 |
| ('per60_state', '4v4')        |  50.9552 |  51.5258 |  -0.0111 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.8246 | UNDERPOWERED |      0.1306 |
| ('per60_state', '3v3')        |  55.3137 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   36.7347 | UNDERPOWERED |     18.5790 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  68.5757 |  65.1965 |   0.0518 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   68.4575 | UNDERPOWERED |      0.1182 |
| ('per60_score', '-2')         |  73.7919 |  71.0331 |   0.0388 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   73.7544 | UNDERPOWERED |      0.0375 |
| ('per60_score', '-1')         |  68.7955 |  65.7393 |   0.0465 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   68.7239 | UNDERPOWERED |      0.0716 |
| ('per60_score', '0')          |  62.1705 |  60.2059 |   0.0326 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.3113 | UNDERPOWERED |      0.1407 |
| ('per60_score', '+1')         |  58.1285 |  56.3612 |   0.0314 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   58.2346 | UNDERPOWERED |      0.1061 |
| ('per60_score', '+2')         |  56.3802 |  54.3527 |   0.0373 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   56.3462 | UNDERPOWERED |      0.0340 |
| ('per60_score', '>=+3')       |  52.0155 |  47.3922 |   0.0976 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.9305 | UNDERPOWERED |      0.0850 |
| ('team_game', 'mean')         |  62.1086 |  63.5814 |  -0.0232 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.1874 | UNDERPOWERED |      0.0789 |
| ('team_game', 'sd')           |  12.2555 |  14.6140 |  -0.1614 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   12.3242 | NO-TOLERANCE |      0.0687 |
| ('team_game_P', '[0,40)')     |   0.0113 |   0.0174 |  -0.3533 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0127 | NO-TOLERANCE |      0.0014 |
| ('team_game_P', '[40,50)')    |   0.1199 |   0.0930 |   0.2891 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1170 | NO-TOLERANCE |      0.0029 |
| ('team_game_P', '[50,60)')    |   0.3217 |   0.3547 |  -0.0930 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3205 | NO-TOLERANCE |      0.0012 |
| ('team_game_P', '[60,70)')    |   0.3133 |   0.2035 |   0.5396 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3159 | NO-TOLERANCE |      0.0026 |
| ('team_game_P', '>=70')       |   0.2338 |   0.3314 |  -0.2944 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2339 | NO-TOLERANCE |      0.0001 |
| ('game', 'corr_home_away')    |   0.0879 |  -0.0772 |  -2.1396 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1037 | NO-TOLERANCE |      0.0157 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.109, sim - actual -1.473 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -1.0691 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0454 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.1020 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.4104 |   1.1546 |         1.2744 |                   0.0224 |     -0.1422 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.4092 |   2.5030 |         1.9991 |                   0.6129 |     -0.1090 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6644 |   1.3463 |         1.4198 |                  -0.0500 |     -0.0235 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.9552 |  -0.5706 |        -1.2389 |                   0.1555 |      0.5127 |   1.5458 | CLEAN     |
| 3v3     | nan      |  55.3137 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.8095 |  58.4717 |  0.0058 | 0.0300 | PASS         | n=2796 team-games                       |   58.8334 | PASS         |      0.0239 |
| ('per60_state', 'PP')         | 101.3675 | 101.7125 | -0.0034 | 0.0300 | PASS         | n=2796 team-games                       |  101.4029 | PASS         |      0.0354 |
| ('per60_state', 'PK')         |  14.0573 |  14.2473 | -0.0133 | 0.0300 | PASS         | n=2796 team-games                       |   14.0547 | PASS         |      0.0026 |
| ('per60_state', '4v4')        |  50.2324 |  48.8019 |  0.0293 | 0.0300 | PASS         | n=2796 team-games                       |   50.2034 | PASS         |      0.0290 |
| ('per60_state', '3v3')        |  58.2266 |  55.2313 |  0.0542 | 0.0300 | FAIL         | n=2796 team-games                       |   58.4082 | FAIL         |      0.1816 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  65.7519 |  65.4146 |  0.0052 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   65.7091 | UNDERPOWERED |      0.0428 |
| ('per60_score', '-2')         |  71.1278 |  68.3894 |  0.0400 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   71.2260 | UNDERPOWERED |      0.0982 |
| ('per60_score', '-1')         |  66.2197 |  64.3039 |  0.0298 | 0.0300 | PASS         | n=508 team-hours                        |   66.2476 | FAIL         |      0.0279 |
| ('per60_score', '0')          |  59.0295 |  58.7080 |  0.0055 | 0.0300 | PASS         | n=984 team-hours                        |   59.0506 | PASS         |      0.0211 |
| ('per60_score', '+1')         |  56.3146 |  54.2774 |  0.0375 | 0.0300 | FAIL         | n=508 team-hours                        |   56.3390 | FAIL         |      0.0244 |
| ('per60_score', '+2')         |  55.0393 |  51.5720 |  0.0672 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   55.0719 | UNDERPOWERED |      0.0325 |
| ('per60_score', '>=+3')       |  50.6298 |  49.1341 |  0.0304 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   50.6483 | UNDERPOWERED |      0.0185 |
| ('team_game', 'mean')         |  58.2627 |  59.7353 | -0.0247 | 0.0300 | PASS         | n=2796 team-games                       |   58.2900 | PASS         |      0.0273 |
| ('team_game', 'sd')           |  10.0781 |  11.8616 | -0.1504 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.0890 | NO-TOLERANCE |      0.0109 |
| ('team_game_P', '[0,40)')     |   0.0213 |   0.0279 | -0.2372 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0213 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1716 |   0.1652 |  0.0383 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1707 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '[50,60)')    |   0.3771 |   0.3283 |  0.1484 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3765 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '[60,70)')    |   0.2994 |   0.2800 |  0.0692 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3002 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '>=70')       |   0.1307 |   0.1985 | -0.3416 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1313 | NO-TOLERANCE |      0.0006 |
| ('game', 'corr_home_away')    |  -0.1571 |  -0.3716 | -0.5772 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1582 | NO-TOLERANCE |      0.0010 |

### Decomposition, attempts per team-game: actual 59.735, sim 58.263, sim - actual -1.473 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                -0.0684 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0046 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                +0.0255 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.4717 |  58.8095 |  0.3378 |         0.3301 |                  -0.0012 |      0.0090 | 1.7542 | CLEAN     |
| PP      | 101.7125 | 101.3675 | -0.3450 |        -0.5163 |                   0.0804 |      0.0909 | 3.0514 | CLEAN     |
| PK      |  14.2473 |  14.0573 | -0.1901 |        -0.2119 |                  -0.0052 |      0.0270 | 0.4274 | CLEAN     |
| 4v4     |  48.8019 |  50.2324 |  1.4304 |         0.7153 |                   0.1498 |      0.5654 | 1.4641 | CLEAN     |
| 3v3     |  55.2313 |  58.2266 |  2.9953 |         2.9801 |                  -0.0413 |      0.0566 | 1.6569 | FAIL      |

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
|         1 |    60.99 |        58.45 |             87 |        59.17 |            57.20 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        57.63 |            59.08 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        59.21 |            60.72 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        55.22 |            59.05 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        61.77 |            59.04 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        54.34 |            57.59 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        58.64 |            57.46 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        53.98 |            62.63 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        59.77 |            56.85 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        57.96 |            60.79 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        66.55 |            49.25 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        63.67 |            54.75 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        57.18 |            57.39 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        57.63 |            59.59 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        51.31 |            60.43 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        53.74 |            60.49 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        59.84 |            56.20 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.06 |            58.17 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.01 |            58.96 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        61.68 |            54.93 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        63.12 |            55.22 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        55.12 |            55.49 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.06 |            65.21 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        59.97 |            57.61 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.05 |            55.10 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        54.46 |            64.53 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.02 |            59.99 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        55.15 |            59.34 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        57.61 |            58.78 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        58.21 |            59.70 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        57.49 |            59.74 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        60.64 |            56.26 | UNDERPOWERED |

