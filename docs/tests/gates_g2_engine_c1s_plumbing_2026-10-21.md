# G2 closed loop, INV-60 plumbing (oracle goalie) (SA-R3): engine_c1s_plumbing_v1, arm A3g-c, fold 2 (2024-25), 1398 games x 200 seeds

> **PLUMBING RUN (INV-60). NOTHING HERE GATES. ORACLE GOALIE** (the box-score starter faces every shot on goal, D8; no in-game goalie change). Goal = **C1s (provisional, D40)**. STAND-INS: block B0 (own 4v4 / 3v3 groups, INV-54), stage-4 L0s (level M1 K500, INV-57), miss S0t (D37): flat, not adoptable; team-level and responsiveness readings that pass through them are not evidence about any model. Stages 7-8 absent (no rebounds, no goalie pull, no OT / shootout model: OT is the stage-1 engine's 3v3 OT, the shootout a 50 / 50 stub). G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).

Generated 2026-10-21 12:07:51 by `scripts/run_shot_attempt_g2.py`. Stage 1 = H3''-LC2 + T2 (D18; LC-2 level tables v5); attempts from A3g-c; goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull (EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.

## regular season (actual team-games n = 2624)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.5382 |  58.3508 |  0.0032 | 0.0300 | PASS         | n=2624 team-games                       |   58.5606 | PASS         |      0.0223 |
| ('per60_state', 'PP')         | 101.0641 | 101.6226 | -0.0055 | 0.0300 | PASS         | n=2624 team-games                       |  101.0922 | PASS         |      0.0280 |
| ('per60_state', 'PK')         |  14.0046 |  14.3173 | -0.0218 | 0.0300 | PASS         | n=2624 team-games                       |   14.0023 | PASS         |      0.0024 |
| ('per60_state', '4v4')        |  50.0254 |  48.6237 |  0.0288 | 0.0300 | PASS         | n=2624 team-games                       |   49.9967 | PASS         |      0.0287 |
| ('per60_state', '3v3')        |  58.2379 |  55.2313 |  0.0544 | 0.0300 | FAIL         | n=2624 team-games                       |   58.3395 | FAIL         |      0.1015 |
| ('per60_state', 'EN-for')     |   0.0000 | 154.6454 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.3382 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  62.8413 |  65.4302 | -0.0396 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   62.8719 | UNDERPOWERED |      0.0306 |
| ('per60_score', '-2')         |  63.6024 |  68.2253 | -0.0678 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   63.6389 | UNDERPOWERED |      0.0365 |
| ('per60_score', '-1')         |  62.4583 |  64.2065 | -0.0272 | 0.0300 | PASS         | n=476 team-hours                        |   62.4817 | PASS         |      0.0233 |
| ('per60_score', '0')          |  58.8243 |  58.6022 |  0.0038 | 0.0300 | PASS         | n=919 team-hours                        |   58.8404 | PASS         |      0.0161 |
| ('per60_score', '+1')         |  54.6628 |  54.1359 |  0.0097 | 0.0300 | PASS         | n=476 team-hours                        |   54.6801 | PASS         |      0.0173 |
| ('per60_score', '+2')         |  52.0668 |  51.3994 |  0.0130 | 0.0300 | UNDERPOWERED | n=228 team-hours                        |   52.0719 | UNDERPOWERED |      0.0052 |
| ('per60_score', '>=+3')       |  49.8344 |  49.2586 |  0.0117 | 0.0300 | UNDERPOWERED | n=163 team-hours                        |   49.8686 | UNDERPOWERED |      0.0343 |
| ('team_game', 'mean')         |  58.9073 |  59.4832 | -0.0097 | 0.0300 | PASS         | n=2624 team-games                       |   58.9273 | PASS         |      0.0200 |
| ('team_game', 'sd')           |   9.8992 |  11.6141 | -0.1477 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    9.9018 | NO-TOLERANCE |      0.0026 |
| ('team_game_P', '[0,40)')     |   0.0170 |   0.0286 | -0.4054 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0170 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[40,50)')    |   0.1541 |   0.1700 | -0.0932 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1532 | NO-TOLERANCE |      0.0010 |
| ('team_game_P', '[50,60)')    |   0.3700 |   0.3266 |  0.1329 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3700 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[60,70)')    |   0.3164 |   0.2851 |  0.1098 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3167 | NO-TOLERANCE |      0.0003 |
| ('team_game_P', '>=70')       |   0.1425 |   0.1898 | -0.2492 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1431 | NO-TOLERANCE |      0.0006 |
| ('game', 'corr_home_away')    |  -0.2292 |  -0.4126 | -0.4445 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.2335 | NO-TOLERANCE |      0.0043 |

### Decomposition, attempts per team-game: actual 59.483, sim 58.907, sim - actual -0.576 (tolerance 1.784 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.1811 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6867 |
| (b) strength-state visits x offline rate                   |                +0.9753 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0201 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0657 |

- **Verdict (regular season, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.3508 |  58.5382 |  0.1875 |         0.2660 |                   0.0185 |     -0.0970 | 1.7505 | CLEAN     |
| PP      | 101.6226 | 101.0641 | -0.5584 |        -0.7057 |                   0.0509 |      0.0964 | 3.0487 | CLEAN     |
| PK      |  14.3173 |  14.0046 | -0.3127 |        -0.3347 |                  -0.0013 |      0.0233 | 0.4295 | CLEAN     |
| 4v4     |  48.6237 |  50.0254 |  1.4017 |         0.8432 |                   0.1414 |      0.4171 | 1.4587 | CLEAN     |
| 3v3     |  55.2313 |  58.2379 |  3.0066 |         2.9801 |                  -0.0447 |      0.0713 | 1.6569 | FAIL      |

## playoffs (actual team-games n = 172)

|                               |      sim |     real |      rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|---------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  61.2496 |  60.2558 |   0.0165 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   61.2755 | UNDERPOWERED |      0.0259 |
| ('per60_state', 'PP')         | 105.2684 | 102.9062 |   0.0230 | 0.0300 | UNDERPOWERED | n=172 team-games                        |  105.3055 | UNDERPOWERED |      0.0371 |
| ('per60_state', 'PK')         |  14.6297 |  13.3181 |   0.0985 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   14.6670 | UNDERPOWERED |      0.0374 |
| ('per60_state', '4v4')        |  50.9535 |  51.5258 |  -0.0111 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   50.8802 | UNDERPOWERED |      0.0733 |
| ('per60_state', '3v3')        |  56.1488 |   0.0000 | inf      | 0.0300 | UNDERPOWERED | n=172 team-games                        |   41.3793 | UNDERPOWERED |     14.7695 |
| ('per60_state', 'EN-for')     |   0.0000 | 137.3558 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  50.4703 |  -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  65.5671 |  65.1965 |   0.0057 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   65.4517 | UNDERPOWERED |      0.1154 |
| ('per60_score', '-2')         |  66.4369 |  71.0331 |  -0.0647 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   66.3660 | UNDERPOWERED |      0.0709 |
| ('per60_score', '-1')         |  65.2338 |  65.7393 |  -0.0077 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   65.3177 | UNDERPOWERED |      0.0839 |
| ('per60_score', '0')          |  62.1186 |  60.2059 |   0.0318 | 0.0300 | UNDERPOWERED | n=65 team-hours                         |   62.1776 | UNDERPOWERED |      0.0590 |
| ('per60_score', '+1')         |  56.4513 |  56.3612 |   0.0016 | 0.0300 | UNDERPOWERED | n=32 team-hours                         |   56.5678 | UNDERPOWERED |      0.1165 |
| ('per60_score', '+2')         |  53.4739 |  54.3527 |  -0.0162 | 0.0300 | UNDERPOWERED | n=14 team-hours                         |   53.3941 | UNDERPOWERED |      0.0798 |
| ('per60_score', '>=+3')       |  51.6571 |  47.3922 |   0.0900 | 0.0300 | UNDERPOWERED | n=12 team-hours                         |   51.6343 | UNDERPOWERED |      0.0227 |
| ('team_game', 'mean')         |  62.7539 |  63.5814 |  -0.0130 | 0.0300 | UNDERPOWERED | n=172 team-games                        |   62.7604 | UNDERPOWERED |      0.0065 |
| ('team_game', 'sd')           |  12.0136 |  14.6140 |  -0.1779 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   11.9911 | NO-TOLERANCE |      0.0225 |
| ('team_game_P', '[0,40)')     |   0.0092 |   0.0174 |  -0.4700 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0100 | NO-TOLERANCE |      0.0008 |
| ('team_game_P', '[40,50)')    |   0.1030 |   0.0930 |   0.1075 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1018 | NO-TOLERANCE |      0.0012 |
| ('team_game_P', '[50,60)')    |   0.3116 |   0.3547 |  -0.1214 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3101 | NO-TOLERANCE |      0.0015 |
| ('team_game_P', '[60,70)')    |   0.3268 |   0.2035 |   0.6060 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3306 | NO-TOLERANCE |      0.0038 |
| ('team_game_P', '>=70')       |   0.2493 |   0.3314 |  -0.2476 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.2475 | NO-TOLERANCE |      0.0018 |
| ('game', 'corr_home_away')    |   0.0356 |  -0.0772 |  -1.4613 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0403 | NO-TOLERANCE |      0.0047 |

### Decomposition, attempts per team-game: actual 63.581, sim 62.754, sim - actual -0.827 (tolerance 1.907 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +1.3621 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.7093 |
| (b) strength-state visits x offline rate                   |                -0.2713 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0353 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.2443 |

- **Verdict (playoffs, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |    total |   hazard level |   score mix within state |   remainder |      tol | verdict   |
|:--------|---------:|---------:|---------:|---------------:|-------------------------:|------------:|---------:|:----------|
| 5v5     |  60.2558 |  61.2496 |   0.9938 |         1.2744 |                   0.0180 |     -0.2986 |   1.8077 | CLEAN     |
| PP      | 102.9062 | 105.2684 |   2.3622 |         1.9991 |                   0.5355 |     -0.1724 |   3.0872 | CLEAN     |
| PK      |  13.3181 |  14.6297 |   1.3116 |         1.4198 |                  -0.0465 |     -0.0617 |   0.3995 | FAIL      |
| 4v4     |  51.5258 |  50.9535 |  -0.5723 |        -1.2389 |                   0.1692 |      0.4974 |   1.5458 | CLEAN     |
| 3v3     | nan      |  56.1488 | nan      |       nan      |                 nan      |    nan      | nan      | CLEAN     |

## overall (actual team-games n = 2796)

|                               |      sim |     real |     rel |    tol | status       | note                                    |   sim_100 | status_100   |   |200-100| |
|:------------------------------|---------:|---------:|--------:|-------:|:-------------|:----------------------------------------|----------:|:-------------|------------:|
| ('per60_state', '5v5')        |  58.7083 |  58.4717 |  0.0040 | 0.0300 | PASS         | n=2796 team-games                       |   58.7307 | PASS         |      0.0224 |
| ('per60_state', 'PP')         | 101.3396 | 101.7125 | -0.0037 | 0.0300 | PASS         | n=2796 team-games                       |  101.3686 | PASS         |      0.0290 |
| ('per60_state', 'PK')         |  14.0456 |  14.2473 | -0.0142 | 0.0300 | PASS         | n=2796 team-games                       |   14.0459 | PASS         |      0.0003 |
| ('per60_state', '4v4')        |  50.0843 |  48.8019 |  0.0263 | 0.0300 | PASS         | n=2796 team-games                       |   50.0530 | PASS         |      0.0313 |
| ('per60_state', '3v3')        |  58.2375 |  55.2313 |  0.0544 | 0.0300 | FAIL         | n=2796 team-games                       |   58.3367 | FAIL         |      0.0991 |
| ('per60_state', 'EN-for')     |   0.0000 | 153.4874 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_state', 'EN-against') |   0.0000 |  48.4810 | -1.0000 | 0.0300 | UNREACHABLE  | no goalie-pull model (stage 8)          |    0.0000 | UNREACHABLE  |      0.0000 |
| ('per60_score', '<=-3')       |  63.0107 |  65.4146 | -0.0367 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   63.0356 | UNDERPOWERED |      0.0250 |
| ('per60_score', '-2')         |  63.7751 |  68.3894 | -0.0675 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   63.8068 | UNDERPOWERED |      0.0317 |
| ('per60_score', '-1')         |  62.6301 |  64.3039 | -0.0260 | 0.0300 | PASS         | n=508 team-hours                        |   62.6565 | PASS         |      0.0265 |
| ('per60_score', '0')          |  59.0362 |  58.7080 |  0.0056 | 0.0300 | PASS         | n=984 team-hours                        |   59.0532 | PASS         |      0.0170 |
| ('per60_score', '+1')         |  54.7735 |  54.2774 |  0.0091 | 0.0300 | PASS         | n=508 team-hours                        |   54.7965 | PASS         |      0.0230 |
| ('per60_score', '+2')         |  52.1525 |  51.5720 |  0.0113 | 0.0300 | UNDERPOWERED | n=242 team-hours                        |   52.1534 | UNDERPOWERED |      0.0008 |
| ('per60_score', '>=+3')       |  49.9476 |  49.1341 |  0.0166 | 0.0300 | UNDERPOWERED | n=174 team-hours                        |   49.9807 | UNDERPOWERED |      0.0331 |
| ('team_game', 'mean')         |  59.1439 |  59.7353 | -0.0099 | 0.0300 | PASS         | n=2796 team-games                       |   59.1631 | PASS         |      0.0192 |
| ('team_game', 'sd')           |  10.0846 |  11.8616 | -0.1498 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   10.0850 | NO-TOLERANCE |      0.0004 |
| ('team_game_P', '[0,40)')     |   0.0165 |   0.0279 | -0.4079 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.0166 | NO-TOLERANCE |      0.0000 |
| ('team_game_P', '[40,50)')    |   0.1510 |   0.1652 | -0.0862 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1500 | NO-TOLERANCE |      0.0010 |
| ('team_game_P', '[50,60)')    |   0.3664 |   0.3283 |  0.1160 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3663 | NO-TOLERANCE |      0.0001 |
| ('team_game_P', '[60,70)')    |   0.3170 |   0.2800 |  0.1320 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.3176 | NO-TOLERANCE |      0.0006 |
| ('team_game_P', '>=70')       |   0.1491 |   0.1985 | -0.2491 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |    0.1495 | NO-TOLERANCE |      0.0005 |
| ('game', 'corr_home_away')    |  -0.1955 |  -0.3716 | -0.4740 |        | NO-TOLERANCE | SD ratio / P(k) / correlation: reported |   -0.1991 | NO-TOLERANCE |      0.0036 |

### Decomposition, attempts per team-game: actual 59.735, sim 59.144, sim - actual -0.591 (tolerance 1.792 = g2_rate_rel x actual)

|                                                            |   attempts / team-game |
|:-----------------------------------------------------------|-----------------------:|
| (a) hazard level, reachable states (offline pred - actual) |                +0.2537 |
| (a') actual EN-state attempts (unreachable in the sim)     |                -1.6881 |
| (b) strength-state visits x offline rate                   |                +0.9022 |
| (s) score-state visits x (bucket rate - mean rate)         |                +0.0212 |
| (d) remainder (sim-path hazard mix: clock / joint state)   |                -0.0804 |

- **Verdict (overall, per team-game): CLEAN**

### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)

| state   |   actual |      sim |   total |   hazard level |   score mix within state |   remainder |    tol | verdict   |
|:--------|---------:|---------:|--------:|---------------:|-------------------------:|------------:|-------:|:----------|
| 5v5     |  58.4717 |  58.7083 |  0.2366 |         0.3301 |                   0.0191 |     -0.1126 | 1.7542 | CLEAN     |
| PP      | 101.7125 | 101.3396 | -0.3729 |        -0.5163 |                   0.0762 |      0.0671 | 3.0514 | CLEAN     |
| PK      |  14.2473 |  14.0456 | -0.2018 |        -0.2119 |                  -0.0035 |      0.0136 | 0.4274 | CLEAN     |
| 4v4     |  48.8019 |  50.0843 |  1.2824 |         0.7153 |                   0.1485 |      0.4185 | 1.4641 | CLEAN     |
| 3v3     |  55.2313 |  58.2375 |  3.0062 |         2.9801 |                  -0.0488 |      0.0749 | 1.6569 | FAIL      |

## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])

### by own ES attempts-for rating: spread ratio 1.144 (95% CI 1.003..1.324) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      53.534 |         54.316 |        560.000 |
|  2 |      56.551 |         56.489 |        559.000 |
|  3 |      58.825 |         58.333 |        559.000 |
|  4 |      60.405 |         59.643 |        559.000 |
|  5 |      64.238 |         63.669 |        559.000 |

### by opponent ES attempts-against rating: spread ratio 1.121 (95% CI 0.973..1.330) **PASS**

|    |   sim_per60 |   actual_per60 |   n_team_games |
|---:|------------:|---------------:|---------------:|
|  1 |      54.206 |         53.883 |        560.000 |
|  2 |      56.979 |         57.551 |        559.000 |
|  3 |      58.709 |         59.405 |        559.000 |
|  4 |      60.078 |         59.246 |        559.000 |
|  5 |      63.569 |         62.237 |        559.000 |

## Per team (n = team-games, all UNDERPOWERED; corr for 0.93, against 0.94)

|   team_id |   for_pg |   against_pg |   n_team_games |   for_pg_sim |   against_pg_sim | status       |
|----------:|---------:|-------------:|---------------:|-------------:|-----------------:|:-------------|
|         1 |    60.99 |        58.45 |             87 |        60.23 |            57.92 | UNDERPOWERED |
|         2 |    61.38 |        61.52 |             82 |        58.57 |            60.01 | UNDERPOWERED |
|         3 |    60.22 |        60.89 |             82 |        60.07 |            61.71 | UNDERPOWERED |
|         4 |    55.85 |        60.21 |             82 |        56.15 |            59.84 | UNDERPOWERED |
|         5 |    60.54 |        60.78 |             82 |        62.81 |            59.94 | UNDERPOWERED |
|         6 |    56.11 |        60.02 |             82 |        55.31 |            58.29 | UNDERPOWERED |
|         7 |    59.24 |        59.87 |             82 |        59.47 |            58.43 | UNDERPOWERED |
|         8 |    56.45 |        63.37 |             87 |        54.84 |            63.67 | UNDERPOWERED |
|         9 |    60.41 |        58.50 |             88 |        60.54 |            57.78 | UNDERPOWERED |
|        10 |    56.26 |        64.58 |             95 |        59.02 |            61.58 | UNDERPOWERED |
|        12 |    70.85 |        50.41 |             97 |        67.26 |            50.07 | UNDERPOWERED |
|        13 |    66.42 |        54.23 |            105 |        64.54 |            55.52 | UNDERPOWERED |
|        14 |    59.63 |        57.02 |             87 |        58.10 |            58.22 | UNDERPOWERED |
|        15 |    58.78 |        61.27 |             92 |        58.54 |            60.43 | UNDERPOWERED |
|        16 |    49.29 |        62.77 |             82 |        52.05 |            61.42 | UNDERPOWERED |
|        17 |    57.07 |        60.59 |             82 |        54.58 |            61.38 | UNDERPOWERED |
|        18 |    61.02 |        57.00 |             82 |        60.76 |            57.10 | UNDERPOWERED |
|        19 |    54.89 |        58.39 |             89 |        54.80 |            59.04 | UNDERPOWERED |
|        20 |    63.45 |        60.38 |             82 |        61.75 |            59.97 | UNDERPOWERED |
|        21 |    64.84 |        55.21 |             89 |        62.59 |            55.81 | UNDERPOWERED |
|        22 |    64.03 |        57.04 |            104 |        64.21 |            55.93 | UNDERPOWERED |
|        23 |    56.02 |        57.62 |             82 |        55.99 |            56.26 | UNDERPOWERED |
|        24 |    57.95 |        67.66 |             82 |        56.87 |            66.45 | UNDERPOWERED |
|        25 |    59.87 |        60.25 |            100 |        60.97 |            58.37 | UNDERPOWERED |
|        26 |    61.73 |        56.20 |             88 |        60.93 |            55.87 | UNDERPOWERED |
|        28 |    56.44 |        66.70 |             82 |        55.21 |            65.71 | UNDERPOWERED |
|        29 |    59.37 |        62.96 |             82 |        58.81 |            61.09 | UNDERPOWERED |
|        30 |    57.05 |        63.06 |             88 |        56.04 |            60.00 | UNDERPOWERED |
|        52 |    59.04 |        58.54 |             95 |        58.48 |            59.61 | UNDERPOWERED |
|        54 |    61.56 |        59.14 |             93 |        59.14 |            60.58 | UNDERPOWERED |
|        55 |    58.37 |        62.78 |             82 |        58.30 |            60.78 | UNDERPOWERED |
|        59 |    61.96 |        57.93 |             82 |        61.47 |            57.16 | UNDERPOWERED |

