# G3 closed loop, SL-R7 L1x-as: end_game_pull_off_v1, fold 2 (2024-25), 1398 games x 200 seeds

> **EG-R1 part A closed loop (Lane H8a), goalie pull OFF.** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t, no goalie pull. No delayed-penalty state (INV-70); OT = stage-1 3v3, shootout 50 / 50 stub; no rebounds. Report text produced by the SL-R7 grader.

Generated 2026-10-21 14:20:37 -0400 by `scripts/run_shot_attribute_g3_v4.py grade`.

Engine markers: attr_model `stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)`; stand_in ['block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable']; goal_model `goal: C1s (provisional, D40)`; oracle_goalie `ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)`.

Served-vs-offline parity before the seeds (max |diff|): .

Tolerances g3_xg_rel 0.03, g3_mix_pp 1.5; cells with n < 300 actual unblocked attempts UNDERPOWERED. Gated cells: all reachable, 5v5, PP, PK (xG_ref per unblocked attempt and the three tier shares); 4v4 / 3v3 reported.

## regular season

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                89759 |   0.0588 |   0.0585 |  0.0049 |            0.2928 |            0.2895 |              0.0598 |              0.0592 | PASS            |
| PP            |                14711 |   0.1008 |   0.1009 | -0.0009 |            0.2616 |            0.2515 |              0.1007 |              0.1023 | PASS            |
| PK            |                 2433 |   0.0700 |   0.0690 |  0.0142 |            0.1250 |            0.1213 |              0.0729 |              0.0752 | PASS            |
| 4v4           |                 1167 |   0.0659 |   0.0702 | -0.0611 |            0.2370 |            0.2368 |              0.0813 |              0.0780 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0367 |            0.1704 |            0.1753 |              0.1433 |              0.1444 | reported (FAIL) |
| all reachable |               109199 |   0.0650 |   0.0649 |  0.0019 |            0.2841 |            0.2800 |              0.0667 |              0.0665 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  89759 |    12.059 |    12.141 |    -0.082 | PASS            |
| ('5v5', 'medium')           |  89759 |    38.794 |    39.167 |    -0.373 | PASS            |
| ('5v5', 'low')              |  89759 |    49.147 |    48.691 |     0.455 | PASS            |
| ('PP', 'high')              |  14711 |    17.051 |    17.069 |    -0.018 | PASS            |
| ('PP', 'medium')            |  14711 |    47.648 |    47.685 |    -0.038 | PASS            |
| ('PP', 'low')               |  14711 |    35.301 |    35.246 |     0.055 | PASS            |
| ('PK', 'high')              |   2433 |    12.707 |    12.125 |     0.582 | PASS            |
| ('PK', 'medium')            |   2433 |    36.948 |    37.896 |    -0.947 | PASS            |
| ('PK', 'low')               |   2433 |    50.344 |    49.979 |     0.365 | PASS            |
| ('4v4', 'high')             |   1167 |    12.779 |    14.567 |    -1.789 | reported (FAIL) |
| ('4v4', 'medium')           |   1167 |    48.696 |    54.070 |    -5.374 | reported (FAIL) |
| ('4v4', 'low')              |   1167 |    38.526 |    31.362 |     7.163 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.216 |    15.855 |     2.361 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.414 |    60.142 |    -8.728 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.370 |    24.004 |     6.367 | reported (FAIL) |
| ('all reachable', 'high')   | 109199 |    12.811 |    12.869 |    -0.058 | PASS            |
| ('all reachable', 'medium') | 109199 |    40.180 |    40.662 |    -0.483 | PASS            |
| ('all reachable', 'low')    | 109199 |    47.009 |    46.468 |     0.540 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.300 |    69.250 |     0.051 |
| slap       |    12.221 |    11.589 |     0.632 |
| backhand   |     7.357 |     7.065 |     0.292 |
| tip+defl   |     9.651 |    10.506 |    -0.855 |
| wrap       |     0.940 |     0.729 |     0.211 |
| other      |     0.530 |     0.862 |    -0.331 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00012; tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00004 |
| attribute mix within state (sim weights)                         |         +0.00016 |

- Decomposition verdict (regular season): CLEAN

## playoffs

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |    rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status                  |
|:--------------|---------------------:|---------:|---------:|-------:|------------------:|------------------:|--------------------:|--------------------:|:------------------------|
| 5v5           |                 6165 |   0.0586 |   0.0567 | 0.0326 |            0.2877 |            0.3028 |              0.0578 |              0.0560 | FAIL                    |
| PP            |                 1108 |   0.1012 |   0.1004 | 0.0073 |            0.2525 |            0.2608 |              0.1019 |              0.1110 | PASS                    |
| PK            |                  169 |   0.0677 |   0.0585 | 0.1579 |            0.1221 |            0.1289 |              0.0709 |              0.0473 | UNDERPOWERED            |
| 4v4           |                   75 |   0.0663 |   0.0553 | 0.1983 |            0.2378 |            0.2925 |              0.0775 |              0.1067 | reported (UNDERPOWERED) |
| all reachable |                 7517 |   0.0649 |   0.0632 | 0.0264 |            0.2793 |            0.2936 |              0.0646 |              0.0644 | PASS                    |

### Location tier shares (%)

|                             |    n |   sim_pct |   act_pct |   diff_pp | status                  |
|:----------------------------|-----:|----------:|----------:|----------:|:------------------------|
| ('5v5', 'high')             | 6165 |    11.940 |    12.490 |    -0.550 | PASS                    |
| ('5v5', 'medium')           | 6165 |    38.763 |    36.529 |     2.235 | FAIL                    |
| ('5v5', 'low')              | 6165 |    49.297 |    50.981 |    -1.684 | FAIL                    |
| ('PP', 'high')              | 1108 |    16.981 |    14.440 |     2.541 | FAIL                    |
| ('PP', 'medium')            | 1108 |    47.776 |    46.751 |     1.025 | PASS                    |
| ('PP', 'low')               | 1108 |    35.244 |    38.809 |    -3.565 | FAIL                    |
| ('PK', 'high')              |  169 |    11.907 |     8.284 |     3.623 | UNDERPOWERED            |
| ('PK', 'medium')            |  169 |    37.459 |    33.728 |     3.731 | UNDERPOWERED            |
| ('PK', 'low')               |  169 |    50.634 |    57.988 |    -7.354 | UNDERPOWERED            |
| ('4v4', 'high')             |   75 |    12.987 |    10.667 |     2.321 | reported (UNDERPOWERED) |
| ('4v4', 'medium')           |   75 |    49.456 |    57.333 |    -7.878 | reported (UNDERPOWERED) |
| ('4v4', 'low')              |   75 |    37.557 |    32.000 |     5.557 | reported (UNDERPOWERED) |
| ('all reachable', 'high')   | 7517 |    12.660 |    12.665 |    -0.005 | PASS                    |
| ('all reachable', 'medium') | 7517 |    40.122 |    38.180 |     1.942 | FAIL                    |
| ('all reachable', 'low')    | 7517 |    47.218 |    49.155 |    -1.937 | FAIL                    |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.264 |    66.848 |     2.416 |
| slap       |    12.396 |    11.467 |     0.928 |
| backhand   |     7.355 |     8.208 |    -0.853 |
| tip+defl   |     9.494 |    11.760 |    -2.266 |
| wrap       |     0.948 |     0.785 |     0.163 |
| other      |     0.543 |     0.931 |    -0.388 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00167; tolerance 0.00190)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00030 |
| attribute mix within state (sim weights)                         |         +0.00196 |

- Decomposition verdict (playoffs): COMPENSATED

## overall

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                95924 |   0.0588 |   0.0584 |  0.0066 |            0.2925 |            0.2904 |              0.0597 |              0.0590 | PASS            |
| PP            |                15819 |   0.1009 |   0.1009 | -0.0003 |            0.2610 |            0.2522 |              0.1008 |              0.1029 | PASS            |
| PK            |                 2602 |   0.0698 |   0.0683 |  0.0221 |            0.1248 |            0.1218 |              0.0728 |              0.0734 | PASS            |
| 4v4           |                 1242 |   0.0659 |   0.0693 | -0.0485 |            0.2370 |            0.2404 |              0.0810 |              0.0797 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0368 |            0.1704 |            0.1753 |              0.1433 |              0.1444 | reported (FAIL) |
| all reachable |               116716 |   0.0650 |   0.0648 |  0.0034 |            0.2838 |            0.2809 |              0.0665 |              0.0663 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  95924 |    12.051 |    12.164 |    -0.112 | PASS            |
| ('5v5', 'medium')           |  95924 |    38.792 |    38.998 |    -0.205 | PASS            |
| ('5v5', 'low')              |  95924 |    49.157 |    48.839 |     0.318 | PASS            |
| ('PP', 'high')              |  15819 |    17.046 |    16.885 |     0.161 | PASS            |
| ('PP', 'medium')            |  15819 |    47.657 |    47.620 |     0.037 | PASS            |
| ('PP', 'low')               |  15819 |    35.297 |    35.495 |    -0.198 | PASS            |
| ('PK', 'high')              |   2602 |    12.652 |    11.875 |     0.777 | PASS            |
| ('PK', 'medium')            |   2602 |    36.983 |    37.625 |    -0.642 | PASS            |
| ('PK', 'low')               |   2602 |    50.364 |    50.500 |    -0.135 | PASS            |
| ('4v4', 'high')             |   1242 |    12.792 |    14.332 |    -1.540 | reported (FAIL) |
| ('4v4', 'medium')           |   1242 |    48.745 |    54.267 |    -5.523 | reported (FAIL) |
| ('4v4', 'low')              |   1242 |    38.463 |    31.401 |     7.062 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.215 |    15.855 |     2.360 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.411 |    60.142 |    -8.730 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.374 |    24.004 |     6.370 | reported (FAIL) |
| ('all reachable', 'high')   | 116716 |    12.801 |    12.856 |    -0.055 | PASS            |
| ('all reachable', 'medium') | 116716 |    40.176 |    40.503 |    -0.326 | PASS            |
| ('all reachable', 'low')    | 116716 |    47.022 |    46.641 |     0.381 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.298 |    69.095 |     0.203 |
| slap       |    12.233 |    11.581 |     0.651 |
| backhand   |     7.357 |     7.139 |     0.218 |
| tip+defl   |     9.641 |    10.586 |    -0.946 |
| wrap       |     0.940 |     0.733 |     0.208 |
| other      |     0.531 |     0.866 |    -0.335 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00022; tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00006 |
| attribute mix within state (sim weights)                         |         +0.00028 |

- Decomposition verdict (overall): CLEAN

## G3 gate (overall slice; all reachable / 5v5 / PP / PK)

| cell          | check            |   value | status   |
|:--------------|:-----------------|--------:|:---------|
| all reachable | xG per unblocked | +0.0034 | PASS     |
| all reachable | tier high pp     | -0.0546 | PASS     |
| all reachable | tier medium pp   | -0.3264 | PASS     |
| all reachable | tier low pp      | +0.3811 | PASS     |
| 5v5           | xG per unblocked | +0.0066 | PASS     |
| 5v5           | tier high pp     | -0.1125 | PASS     |
| 5v5           | tier medium pp   | -0.2055 | PASS     |
| 5v5           | tier low pp      | +0.3180 | PASS     |
| PP            | xG per unblocked | -0.0003 | PASS     |
| PP            | tier high pp     | +0.1614 | PASS     |
| PP            | tier medium pp   | +0.0367 | PASS     |
| PP            | tier low pp      | -0.1981 | PASS     |
| PK            | xG per unblocked | +0.0221 | PASS     |
| PK            | tier high pp     | +0.7769 | PASS     |
| PK            | tier medium pp   | -0.6415 | PASS     |
| PK            | tier low pp      | -0.1354 | PASS     |

- **G3: PASS**

## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6756 |               1.6503 |     58.5310 |     58.3508 |               58.3508 |     17.1396 |     16.8941 |     41.3914 |     41.4566 |          0.2928 |          0.2895 |      36578.0000 |        89759.0000 |      0.0031 |      0.0145 |     -0.0016 |              0.3303 |
| PP      |               0.1512 |               0.1474 |    101.0279 |    101.6226 |              101.6226 |     26.4268 |     25.5582 |     74.6012 |     76.0644 |          0.2616 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0059 |      0.0340 |     -0.0192 |              1.0078 |
| PK      |               0.1512 |               0.1474 |     14.0039 |     14.3173 |               14.3173 |      1.7508 |      1.7373 |     12.2532 |     12.5800 |          0.1250 |          0.1213 |        336.0000 |         2433.0000 |     -0.0219 |      0.0078 |     -0.0260 |              0.3677 |
| 4v4     |               0.0258 |               0.0240 |     50.0066 |     48.6237 |               48.6237 |     11.8513 |     11.5120 |     38.1553 |     37.1118 |          0.2370 |          0.2368 |        362.0000 |         1167.0000 |      0.0284 |      0.0295 |      0.0281 |              0.0239 |
| 3v3     |               0.0175 |               0.0189 |     58.1633 |     55.2313 |               55.2313 |      9.9083 |      9.6826 |     48.2550 |     45.5487 |          0.1704 |          0.1753 |        240.0000 |         1129.0000 |      0.0531 |      0.0233 |      0.0594 |             -0.4957 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.7111 |               1.7065 |     61.2506 |     60.2558 |               60.2558 |     17.6223 |     18.2478 |     43.6283 |     42.0080 |          0.2877 |          0.3028 |       2678.0000 |         6165.0000 |      0.0165 |     -0.0343 |      0.0386 |             -1.5130 |
| PP      |               0.1617 |               0.1694 |    105.2869 |    102.9062 |              102.9062 |     26.5808 |     26.8421 |     78.7061 |     76.0641 |          0.2525 |          0.2608 |        391.0000 |         1108.0000 |      0.0231 |     -0.0097 |      0.0347 |             -0.8380 |
| PK      |               0.1617 |               0.1694 |     14.6406 |     13.3181 |               13.3181 |      1.7869 |      1.7162 |     12.8537 |     11.6018 |          0.1221 |          0.1289 |         25.0000 |          169.0000 |      0.0993 |      0.0412 |      0.1079 |             -0.6814 |
| 4v4     |               0.0266 |               0.0239 |     50.8390 |     51.5258 |               51.5258 |     12.0878 |     15.0689 |     38.7513 |     36.4569 |          0.2378 |          0.2925 |         31.0000 |           75.0000 |     -0.0133 |     -0.1978 |      0.0629 |             -5.4687 |
| 3v3     |               0.0001 |               0.0000 |     55.9756 |      0.0000 |                0.0000 |     14.2683 |      0.0000 |     41.7073 |      0.0000 |          0.2549 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6778 |               1.6537 |     58.7016 |     58.4717 |               58.4717 |     17.1699 |     16.9801 |     41.5317 |     41.4916 |          0.2925 |          0.2904 |      39256.0000 |        95924.0000 |      0.0039 |      0.0112 |      0.0010 |              0.2097 |
| PP      |               0.1518 |               0.1488 |    101.3069 |    101.7125 |              101.7125 |     26.4369 |     25.6481 |     74.8700 |     76.0644 |          0.2610 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0040 |      0.0308 |     -0.0157 |              0.8795 |
| PK      |               0.1518 |               0.1488 |     14.0456 |     14.2473 |               14.2473 |      1.7531 |      1.7358 |     12.2925 |     12.5115 |          0.1248 |          0.1218 |        361.0000 |         2602.0000 |     -0.0142 |      0.0100 |     -0.0175 |              0.2982 |
| 4v4     |               0.0258 |               0.0240 |     50.0594 |     48.8019 |               48.8019 |     11.8663 |     11.7304 |     38.1931 |     37.0716 |          0.2370 |          0.2404 |        393.0000 |         1242.0000 |      0.0258 |      0.0116 |      0.0303 |             -0.3323 |
| 3v3     |               0.0164 |               0.0177 |     58.1629 |     55.2313 |               55.2313 |      9.9092 |      9.6826 |     48.2537 |     45.5487 |          0.1704 |          0.1753 |        240.0000 |         1129.0000 |      0.0531 |      0.0234 |      0.0594 |             -0.4941 |

## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES rating; 1,000 game bootstrap)

- for: R 1.243 (95% CI 0.948..1.852; UNDERPOWERED), old Q5-Q1 1.216, 2,796 units
- against: R 1.126 (95% CI 0.860..1.660; UNDERPOWERED), old Q5-Q1 1.197, 2,796 units

## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.82; 29/32 within 3%, 13/32 tiers within 1.5 pp)

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0674 |   0.0675 | -0.0012 |         0.2616 |          -1.0764 |        0.8148 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0643 |   0.0639 |  0.0061 |         0.1749 |           1.4748 |       -1.6497 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0658 |   0.0645 |  0.0196 |         0.7022 |          -2.2114 |        1.5092 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0662 |   0.0671 | -0.0147 |        -0.1812 |           0.3254 |       -0.1442 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0660 |   0.0667 | -0.0111 |        -0.0595 |           2.3922 |       -2.3327 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0674 |   0.0661 |  0.0194 |         0.9163 |           0.7162 |       -1.6325 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         7 |                 3386 |   0.0646 |   0.0642 |  0.0064 |         0.9778 |          -5.2897 |        4.3119 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0663 |   0.0671 | -0.0112 |         0.4671 |          -3.3332 |        2.8661 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0637 |   0.0637 |  0.0003 |         0.0568 |          -0.3178 |        0.2610 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        10 |                 3818 |   0.0670 |   0.0669 |  0.0026 |        -0.5315 |          -1.0101 |        1.5416 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0634 |   0.0635 | -0.0018 |        -0.2907 |          -0.7992 |        1.0899 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        13 |                 4813 |   0.0646 |   0.0633 |  0.0196 |         0.1512 |           1.2954 |       -1.4466 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        14 |                 3605 |   0.0662 |   0.0674 | -0.0182 |        -0.9319 |           1.9667 |       -1.0348 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0011 |        -2.8401 |           2.4551 |        0.3851 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0639 |   0.0647 | -0.0129 |         0.4418 |          -1.3442 |        0.9024 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0653 |   0.0664 | -0.0166 |         0.4808 |          -2.7372 |        2.2563 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0652 |   0.0655 | -0.0039 |         0.7720 |          -2.3218 |        1.5498 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0638 |   0.0645 | -0.0107 |        -0.0019 |          -3.7990 |        3.8009 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0626 |   0.0603 |  0.0379 |         0.1535 |          -1.6821 |        1.5286 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0655 |   0.0643 |  0.0184 |        -0.0631 |          -0.8615 |        0.9246 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0668 |   0.0672 | -0.0070 |        -0.0762 |           4.0987 |       -4.0225 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0648 |   0.0636 |  0.0188 |        -0.4535 |           1.5317 |       -1.0782 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        24 |                 3372 |   0.0634 |   0.0632 |  0.0031 |        -0.4099 |          -2.9060 |        3.3159 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        25 |                 4139 |   0.0662 |   0.0688 | -0.0378 |        -0.9003 |           1.2452 |       -0.3448 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0634 |   0.0624 |  0.0154 |         0.2641 |           0.7081 |       -0.9722 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        28 |                 3172 |   0.0639 |   0.0632 |  0.0103 |         1.1217 |          -1.9873 |        0.8656 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        29 |                 3395 |   0.0641 |   0.0627 |  0.0237 |         0.3995 |          -0.6721 |        0.2726 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        30 |                 3531 |   0.0656 |   0.0622 |  0.0546 |        -0.2786 |           0.9686 |       -0.6900 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0640 |   0.0647 | -0.0103 |        -1.4518 |           3.8113 |       -2.3595 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0654 |   0.0651 |  0.0044 |        -0.4037 |          -1.0359 |        1.4396 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0630 |   0.0612 |  0.0296 |         0.4450 |          -0.8703 |        0.4253 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        59 |                 3566 |   0.0643 |   0.0647 | -0.0074 |         0.3531 |          -2.9255 |        2.5724 | UNDERPOWERED (team-level, labelled) | True            | False              |

## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)

### regular season

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       58768 |     27.4731 |     27.1429 |           0.3363 |           0.3453 |   0.9098 |   0.9096 |            0.9098 |    2.4771 |    2.4548 |      0.0122 |   -0.9008 |  0.0274 |    0.0091 | nan                          |
| PP            |        9973 |     51.2539 |     51.5662 |           0.3130 |           0.3221 |   0.8535 |   0.8491 |            0.8534 |    7.5105 |    7.7817 |     -0.0061 |   -0.9111 |  0.4372 |   -0.0349 | nan                          |
| PK            |        1923 |      9.6300 |      9.9430 |           0.2141 |           0.2096 |   0.9072 |   0.9048 |            0.9071 |    0.8935 |    0.9462 |     -0.0315 |    0.4459 |  0.2380 |   -0.0557 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |         812 |     25.4795 |     25.8224 |           0.3322 |           0.3042 |   0.8783 |   0.8879 |            0.8786 |    3.1011 |    2.8939 |     -0.0133 |    2.8017 | -0.9642 |    0.0716 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     34.2199 |     33.5664 |           0.2909 |           0.2631 |   0.7979 |   0.8041 |            0.7974 |    6.9144 |    6.5761 |      0.0195 |    2.7787 | -0.6145 |    0.0514 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       72308 |     27.9503 |     27.7237 |           0.3300 |           0.3378 |   0.9005 |   0.8996 |            0.9004 |    2.7816 |    2.7824 |      0.0082 |   -0.7876 |  0.0842 |   -0.0003 | nan                          |

### playoffs

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |    sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|---------:|----------:|:-----------------------------|
| 5v5           |        3753 |     28.3422 |     25.5728 |           0.3504 |           0.3912 |   0.9110 |   0.9081 |            0.9107 |    2.5233 |    2.3508 |      0.1083 |   -4.0869 |   0.2896 |    0.0734 | nan                          |
| PP            |         730 |     53.6676 |     50.1144 |           0.3181 |           0.3412 |   0.8505 |   0.8315 |            0.8509 |    8.0208 |    8.4439 |      0.0709 |   -2.3029 |   1.9040 |   -0.0501 | UNDERPOWERED (n SOG < 2,000) |
| PK            |         135 |     10.1519 |      9.2677 |           0.2102 |           0.2012 |   0.9103 |   0.9407 |            0.9081 |    0.9109 |    0.5492 |      0.0954 |    0.9012 |  -3.0468 |    0.6586 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |          52 |     25.3561 |     25.2768 |           0.3457 |           0.3067 |   0.8816 |   0.8462 |            0.8831 |    3.0017 |    3.8887 |      0.0031 |    3.9003 |   3.5464 |   -0.2281 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |           0 |     25.2439 |      0.0000 |           0.3947 |         nan      |   0.8261 | nan      |            0.8651 |    4.3902 |    0.0000 |    nan      |  nan      | nan      |  nan      | UNDERPOWERED (n SOG < 2,000) |
| all reachable |        4670 |     28.8632 |     26.2436 |           0.3426 |           0.3787 |   0.9018 |   0.8964 |            0.9016 |    2.8343 |    2.7199 |      0.0998 |   -3.6176 |   0.5443 |    0.0421 | nan                          |

### overall

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       62521 |     27.5276 |     27.0433 |           0.3372 |           0.3482 |   0.9099 |   0.9095 |            0.9099 |    2.4800 |    2.4482 |      0.0179 |   -1.1033 |  0.0437 |    0.0130 | nan                          |
| PP            |       10703 |     51.4120 |     51.4645 |           0.3133 |           0.3234 |   0.8533 |   0.8479 |            0.8533 |    7.5439 |    7.8281 |     -0.0010 |   -1.0092 |  0.5372 |   -0.0363 | nan                          |
| PK            |        2058 |      9.6642 |      9.8957 |           0.2138 |           0.2091 |   0.9074 |   0.9072 |            0.9072 |    0.8947 |    0.9184 |     -0.0234 |    0.4741 |  0.0235 |   -0.0259 | nan                          |
| 4v4           |         864 |     25.4717 |     25.7889 |           0.3331 |           0.3043 |   0.8785 |   0.8854 |            0.8789 |    3.0948 |    2.9550 |     -0.0123 |    2.8733 | -0.6918 |    0.0473 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     34.2182 |     33.5664 |           0.2909 |           0.2631 |   0.7979 |   0.8041 |            0.7974 |    6.9139 |    6.5761 |      0.0194 |    2.7805 | -0.6141 |    0.0514 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       76978 |     28.0075 |     27.6292 |           0.3308 |           0.3405 |   0.9006 |   0.8994 |            0.9005 |    2.7849 |    2.7784 |      0.0137 |   -0.9682 |  0.1127 |    0.0023 | nan                          |

