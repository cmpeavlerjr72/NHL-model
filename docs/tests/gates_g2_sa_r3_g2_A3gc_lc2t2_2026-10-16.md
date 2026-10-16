# G2 closed loop (SA-R3): sa_r3_g2_A3gc_lc2t2, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

Generated 2026-10-16 09:59:26 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.5556 |  58.3508 |  0.0035 | 0.0300 | PASS         | n=2624 team-games                       |   58.5806 | PASS         |      0.0249 |
| ('per60_state', 'PP')         | 101.1278 | 101.6226 | -0.0049 | 0.0300 | PASS         | n=2624 team-games                       |  101.1722 | PASS         |      0.0443 |
| ('per60_state', 'PK')         |  14.0109 |  14.3173 | -0.0214 | 0.0300 | PASS         | n=2624 team-games                       |   14.0034 | PASS         |      0.0075 |
| ('per60_state', '4v4')        |  49.9960 |  48.6237 |  0.0282 | 0.0300 | PASS         | n=2624 team-games                       |   49.9653 | PASS         |      0.0307 |
| ('per60_state', '3v3')        |  58.1288 |  55.2313 |  0.0525 | 0.0300 | FAIL         | n=2624 team-games                       |   58.1337 | FAIL         |      0.0049 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.8552 |  65.4302 | -0.0394 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   62.8900 | UNDERPOWERED |      0.0348 |
| ('per60_score', '-2')         |  63.6394 |  68.2253 | -0.0672 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   63.6729 | UNDERPOWERED |      0.0335 |
| ('per60_score', '-1')         |  62.4234 |  64.2065 | -0.0278 | 0.0300 | PASS         | n=476 team-hours                        |   62.4361 | PASS         |      0.0127 |
| ('per60_score', '0')          |  58.8292 |  58.6022 |  0.0039 | 0.0300 | PASS         | n=919 team-hours                        |   58.8485 | PASS         |      0.0193 |
| ('per60_score', '+1')         |  54.6586 |  54.1359 |  0.0097 | 0.0300 | PASS         | n=476 team-hours                        |   54.7040 | PASS         |      0.0454 |
| ('per60_score', '+2')         |  52.0396 |  51.3994 |  0.0125 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   52.0346 | UNDERPOWERED |      0.0051 |
| ('per60_score', '>=+3')       |  49.9032 |  49.2586 |  0.0131 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   49.9383 | UNDERPOWERED |      0.0351 |
| ('team_game', 'mean')         |  58.9234 |  59.4832 | -0.0094 | 0.0300 | PASS         | n=2624 team-games                       |   58.9465 | PASS         |      0.0232 |
| ('team_game', 'sd')           |   9.9124 |  11.6141 | -0.1465 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.9147 | NO-TOLERANCE |      0.0022 |
| ('team_game_P', '[0,40)')     |   0.0169 |   0.0286 | -0.4099 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0167 | NO-TOLERANCE |      0.0002 |
| ('team_game_P', '[40,50)')    |   0.1545 |   0.1700 | -0.0909 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1540 | NO-TOLERANCE |      0.0005 |
| ('team_game_P', '[50,60)')    |   0.3692 |   0.3266 |  0.1303 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3688 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '[60,70)')    |   0.3164 |   0.2851 |  0.1099 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3171 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '>=70')       |   0.1431 |   0.1898 | -0.2462 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1435 | NO-TOLERANCE |      0.0004 |
| ('game', 'corr_home_away')    |  -0.2302 |  -0.4126 | -0.4420 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2331 | NO-TOLERANCE |      0.0028 |

### Decomposition, attempts per team-game: actual 59.483, sim 58.923, sim - actual -0.560 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +0.9728 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0434 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0704 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.3508 |  58.5556 |  0.2049 |         0.2660 |                   0.0444 |     -0.1056 | 1.7505 | CLEAN     |
| PP      | 101.6226 | 101.1278 | -0.4947 |        -0.7057 |                   0.0528 |      0.1582 | 3.0487 | CLEAN     |
| PK      |  14.3173 |  14.0109 | -0.3064 |        -0.3347 |                   0.0024 |      0.0259 | 0.4295 | CLEAN     |
| 4v4     |  48.6237 |  49.9960 |  1.3723 |         0.8432 |                   0.1415 |      0.3876 | 1.4587 | CLEAN     |
| 3v3     |  55.2313 |  58.1288 |  2.8975 |         2.9801 |                  -0.0448 |     -0.0378 | 1.6569 | FAIL      |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.2478 |  60.2558 |   0.0165 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.2941 | UNDERPOWERED |      0.0463 |
| ('per60_state', 'PP')         | 105.4129 | 102.9062 |   0.0244 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.4332 | UNDERPOWERED |      0.0203 |
| ('per60_state', 'PK')         |  14.6340 |  13.3181 |   0.0988 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.6851 | UNDERPOWERED |      0.0511 |
| ('per60_state', '4v4')        |  51.0344 |  51.5258 |  -0.0095 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.9171 | UNDERPOWERED |      0.1173 |
| ('per60_state', '3v3')        |  50.8651 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   39.3586 | UNDERPOWERED |     11.5065 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  64.8862 |  65.1965 |  -0.0048 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   64.9571 | UNDERPOWERED |      0.0709 |
| ('per60_score', '-2')         |  66.0372 |  71.0331 |  -0.0703 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   66.2844 | UNDERPOWERED |      0.2472 |
| ('per60_score', '-1')         |  65.0414 |  65.7393 |  -0.0106 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   65.1115 | UNDERPOWERED |      0.0701 |
| ('per60_score', '0')          |  62.2260 |  60.2059 |   0.0336 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.3097 | UNDERPOWERED |      0.0837 |
| ('per60_score', '+1')         |  56.5912 |  56.3612 |   0.0041 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   56.5866 | UNDERPOWERED |      0.0046 |
| ('per60_score', '+2')         |  53.9315 |  54.3527 |  -0.0077 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   53.7968 | UNDERPOWERED |      0.1347 |
| ('per60_score', '>=+3')       |  51.9115 |  47.3922 |   0.0954 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.6797 | UNDERPOWERED |      0.2319 |
| ('team_game', 'mean')         |  62.8961 |  63.5814 |  -0.0108 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.9805 | UNDERPOWERED |      0.0844 |
| ('team_game', 'sd')           |  12.1328 |  14.6140 |  -0.1698 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   12.2064 | NO-TOLERANCE |      0.0737 |
| ('team_game_P', '[0,40)')     |   0.0085 |   0.0174 |  -0.5117 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0090 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '[40,50)')    |   0.1004 |   0.0930 |   0.0794 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1003 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[50,60)')    |   0.3096 |   0.3547 |  -0.1271 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3042 | NO-TOLERANCE |      0.0054 |
| ('team_game_P', '[60,70)')    |   0.3326 |   0.2035 |   0.6344 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3355 | NO-TOLERANCE |      0.0029 |
| ('team_game_P', '>=70')       |   0.2489 |   0.3314 |  -0.2489 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2510 | NO-TOLERANCE |      0.0021 |
| ('game', 'corr_home_away')    |   0.0864 |  -0.0772 |  -2.1195 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0889 | NO-TOLERANCE |      0.0025 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.896, sim - actual -0.685 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -0.1406 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0350 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.2325 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.2478 |   0.9920 |         1.2744 |                   0.0226 |     -0.3050 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.4129 |   2.5067 |         1.9991 |                   0.4481 |      0.0595 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6340 |   1.3159 |         1.4198 |                  -0.0405 |     -0.0634 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  51.0344 |  -0.4914 |        -1.2389 |                   0.2138 |      0.5337 |   1.5458 | CLEAN     |
| 3v3     | nan      |  50.8651 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.7247 |  58.4717 |  0.0043 | 0.0300 | PASS         | n=2796 team-games                       |   58.7512 | PASS         |      0.0264 |
| ('per60_state', 'PP')         | 101.4096 | 101.7125 | -0.0030 | 0.0300 | PASS         | n=2796 team-games                       |  101.4522 | PASS         |      0.0426 |
| ('per60_state', 'PK')         |  14.0519 |  14.2473 | -0.0137 | 0.0300 | PASS         | n=2796 team-games                       |   14.0482 | PASS         |      0.0037 |
| ('per60_state', '4v4')        |  50.0618 |  48.8019 |  0.0258 | 0.0300 | PASS         | n=2796 team-games                       |   50.0251 | PASS         |      0.0367 |
| ('per60_state', '3v3')        |  58.1273 |  55.2313 |  0.0524 | 0.0300 | FAIL         | n=2796 team-games                       |   58.1306 | FAIL         |      0.0033 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.9850 |  65.4146 | -0.0371 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   63.0239 | UNDERPOWERED |      0.0390 |
| ('per60_score', '-2')         |  63.7887 |  68.3894 | -0.0673 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   63.8325 | UNDERPOWERED |      0.0438 |
| ('per60_score', '-1')         |  62.5845 |  64.3039 | -0.0267 | 0.0300 | PASS         | n=508 team-hours                        |   62.6006 | PASS         |      0.0161 |
| ('per60_score', '0')          |  59.0463 |  58.7080 |  0.0058 | 0.0300 | PASS         | n=984 team-hours                        |   59.0713 | PASS         |      0.0250 |
| ('per60_score', '+1')         |  54.7775 |  54.2774 |  0.0092 | 0.0300 | PASS         | n=508 team-hours                        |   54.8197 | PASS         |      0.0422 |
| ('per60_score', '+2')         |  52.1574 |  51.5720 |  0.0114 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   52.1423 | UNDERPOWERED |      0.0152 |
| ('per60_score', '>=+3')       |  50.0315 |  49.1341 |  0.0183 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   50.0511 | UNDERPOWERED |      0.0196 |
| ('team_game', 'mean')         |  59.1678 |  59.7353 | -0.0095 | 0.0300 | PASS         | n=2796 team-games                       |   59.1947 | PASS         |      0.0269 |
| ('team_game', 'sd')           |  10.1084 |  11.8616 | -0.1478 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.1173 | NO-TOLERANCE |      0.0089 |
| ('team_game_P', '[0,40)')     |   0.0164 |   0.0279 | -0.4138 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0162 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[40,50)')    |   0.1512 |   0.1652 | -0.0850 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1507 | NO-TOLERANCE |      0.0005 |
| ('team_game_P', '[50,60)')    |   0.3655 |   0.3283 |  0.1132 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3648 | NO-TOLERANCE |      0.0007 |
| ('team_game_P', '[60,70)')    |   0.3174 |   0.2800 |  0.1334 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3182 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '>=70')       |   0.1496 |   0.1985 | -0.2465 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1501 | NO-TOLERANCE |      0.0005 |
| ('game', 'corr_home_away')    |  -0.1909 |  -0.3716 | -0.4864 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1925 | NO-TOLERANCE |      0.0017 |

### Decomposition, attempts per team-game: actual 59.735, sim 59.168, sim - actual -0.568 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                +0.9075 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0434 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0841 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.4717 |  58.7247 |  0.2531 |         0.3301 |                   0.0439 |     -0.1209 | 1.7542 | CLEAN     |
| PP      | 101.7125 | 101.4096 | -0.3028 |        -0.5163 |                   0.0743 |      0.1391 | 3.0514 | CLEAN     |
| PK      |  14.2473 |  14.0519 | -0.1955 |        -0.2119 |                   0.0004 |      0.0160 | 0.4274 | CLEAN     |
| 4v4     |  48.8019 |  50.0618 |  1.2599 |         0.7153 |                   0.1502 |      0.3944 | 1.4641 | CLEAN     |
| 3v3     |  55.2313 |  58.1273 |  2.8960 |         2.9801 |                  -0.0489 |     -0.0351 | 1.6569 | FAIL      |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.135 (95% CI 0.996..1.313) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.555 |         54.316 |        560.000 |
|  2 |      56.578 |         56.489 |        559.000 |
|  3 |      58.955 |         58.333 |        559.000 |
|  4 |      60.373 |         59.643 |        559.000 |
|  5 |      64.173 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.122 (95% CI 0.973..1.329) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.246 |         53.883 |        560.000 |
|  2 |      56.955 |         57.551 |        559.000 |
|  3 |      58.718 |         59.405 |        559.000 |
|  4 |      60.083 |         59.246 |        559.000 |
|  5 |      63.622 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        60.30 |            57.90 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        58.48 |            60.00 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        60.31 |            61.52 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        55.86 |            60.26 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        62.42 |            60.25 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        55.19 |            58.38 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        59.58 |            58.36 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        54.86 |            63.75 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        60.49 |            57.91 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        59.22 |            61.37 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        67.27 |            50.05 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        64.34 |            55.71 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        58.36 |            57.96 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        58.80 |            60.28 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        51.91 |            61.59 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        54.70 |            61.25 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        60.48 |            57.32 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.85 |            58.95 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.56 |            60.19 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        62.82 |            55.73 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        64.12 |            56.06 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        56.20 |            56.14 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.71 |            66.56 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        61.06 |            58.35 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.96 |            55.90 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        55.10 |            65.97 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.85 |            61.21 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        56.16 |            60.02 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        58.78 |            59.32 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        59.38 |            60.56 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        58.40 |            60.73 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        61.52 |            57.19 | UNDERPOWERED |

