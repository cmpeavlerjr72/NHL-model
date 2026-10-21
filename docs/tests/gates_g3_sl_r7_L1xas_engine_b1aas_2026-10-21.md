# G3 closed loop, SL-R7 L1x-as: engine_b1aas_v1, fold 2 (2024-25), 1398 games x 200 seeds

> **SB-R5 closed loop: engine DEFAULT table set + block B1a-as flag** (attr['block_b1aas'], replaces the B0 stand-in). Stage 4 = L1x-as, goal = C1s (provisional, D40), ORACLE GOALIE (D8), miss S0t STAND-IN. Pull and shootout flags OFF (stages 7-8 absent: no rebounds, no goalie pull; OT = stage-1 3v3 OT, shootout 50/50 stub). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)

Generated 2026-10-21 15:17:48 -0400 by `scripts/run_shot_attribute_g3_v4.py grade`.

Engine markers: attr_model `stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)`; stand_in ['miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable']; goal_model `goal: C1s (provisional, D40)`; oracle_goalie `ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)`.

Served-vs-offline parity before the seeds (max |diff|): l1xas 1.49e-08 over 116,716 rows; block 1.49e-08 over 162,300 rows; miss 2.98e-08 over 116,716 rows; goal 1.11e-16 over 76,926 rows; block_b1aas 1.67e-16 over 162,300 rows.

Tolerances g3_xg_rel 0.03, g3_mix_pp 1.5; cells with n < 300 actual unblocked attempts UNDERPOWERED. Gated cells: all reachable, 5v5, PP, PK (xG_ref per unblocked attempt and the three tier shares); 4v4 / 3v3 reported.

## regular season

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                89759 |   0.0588 |   0.0585 |  0.0052 |            0.2935 |            0.2895 |              0.0599 |              0.0592 | PASS            |
| PP            |                14711 |   0.1009 |   0.1009 | -0.0007 |            0.2626 |            0.2515 |              0.1007 |              0.1023 | PASS            |
| PK            |                 2433 |   0.0700 |   0.0690 |  0.0145 |            0.1248 |            0.1213 |              0.0729 |              0.0752 | PASS            |
| 4v4           |                 1167 |   0.0660 |   0.0702 | -0.0604 |            0.2365 |            0.2368 |              0.0814 |              0.0780 | reported (FAIL) |
| 3v3           |                 1129 |   0.0839 |   0.0872 | -0.0374 |            0.1739 |            0.1753 |              0.1429 |              0.1444 | reported (FAIL) |
| all reachable |               109199 |   0.0650 |   0.0649 |  0.0021 |            0.2848 |            0.2800 |              0.0667 |              0.0665 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  89759 |    12.065 |    12.141 |    -0.076 | PASS            |
| ('5v5', 'medium')           |  89759 |    38.797 |    39.167 |    -0.370 | PASS            |
| ('5v5', 'low')              |  89759 |    49.138 |    48.691 |     0.447 | PASS            |
| ('PP', 'high')              |  14711 |    17.059 |    17.069 |    -0.010 | PASS            |
| ('PP', 'medium')            |  14711 |    47.647 |    47.685 |    -0.038 | PASS            |
| ('PP', 'low')               |  14711 |    35.294 |    35.246 |     0.048 | PASS            |
| ('PK', 'high')              |   2433 |    12.705 |    12.125 |     0.580 | PASS            |
| ('PK', 'medium')            |   2433 |    36.955 |    37.896 |    -0.941 | PASS            |
| ('PK', 'low')               |   2433 |    50.340 |    49.979 |     0.361 | PASS            |
| ('4v4', 'high')             |   1167 |    12.796 |    14.567 |    -1.771 | reported (FAIL) |
| ('4v4', 'medium')           |   1167 |    48.731 |    54.070 |    -5.339 | reported (FAIL) |
| ('4v4', 'low')              |   1167 |    38.473 |    31.362 |     7.110 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.145 |    15.855 |     2.290 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.471 |    60.142 |    -8.671 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.385 |    24.004 |     6.381 | reported (FAIL) |
| ('all reachable', 'high')   | 109199 |    12.816 |    12.869 |    -0.053 | PASS            |
| ('all reachable', 'medium') | 109199 |    40.181 |    40.662 |    -0.481 | PASS            |
| ('all reachable', 'low')    | 109199 |    47.003 |    46.468 |     0.534 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.297 |    69.250 |     0.047 |
| slap       |    12.224 |    11.589 |     0.635 |
| backhand   |     7.357 |     7.065 |     0.292 |
| tip+defl   |     9.652 |    10.506 |    -0.853 |
| wrap       |     0.940 |     0.729 |     0.211 |
| other      |     0.530 |     0.862 |    -0.332 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00014; tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00004 |
| attribute mix within state (sim weights)                         |         +0.00018 |

- Decomposition verdict (regular season): CLEAN

## playoffs

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |    rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status                  |
|:--------------|---------------------:|---------:|---------:|-------:|------------------:|------------------:|--------------------:|--------------------:|:------------------------|
| 5v5           |                 6165 |   0.0586 |   0.0567 | 0.0327 |            0.2861 |            0.3028 |              0.0579 |              0.0560 | FAIL                    |
| PP            |                 1108 |   0.1012 |   0.1004 | 0.0073 |            0.2526 |            0.2608 |              0.1019 |              0.1110 | PASS                    |
| PK            |                  169 |   0.0678 |   0.0585 | 0.1584 |            0.1217 |            0.1289 |              0.0711 |              0.0473 | UNDERPOWERED            |
| 4v4           |                   75 |   0.0663 |   0.0553 | 0.1976 |            0.2347 |            0.2925 |              0.0777 |              0.1067 | reported (UNDERPOWERED) |
| all reachable |                 7517 |   0.0649 |   0.0632 | 0.0263 |            0.2779 |            0.2936 |              0.0646 |              0.0644 | PASS                    |

### Location tier shares (%)

|                             |    n |   sim_pct |   act_pct |   diff_pp | status                  |
|:----------------------------|-----:|----------:|----------:|----------:|:------------------------|
| ('5v5', 'high')             | 6165 |    11.943 |    12.490 |    -0.546 | PASS                    |
| ('5v5', 'medium')           | 6165 |    38.764 |    36.529 |     2.235 | FAIL                    |
| ('5v5', 'low')              | 6165 |    49.293 |    50.981 |    -1.689 | FAIL                    |
| ('PP', 'high')              | 1108 |    16.986 |    14.440 |     2.545 | FAIL                    |
| ('PP', 'medium')            | 1108 |    47.759 |    46.751 |     1.008 | PASS                    |
| ('PP', 'low')               | 1108 |    35.255 |    38.809 |    -3.554 | FAIL                    |
| ('PK', 'high')              |  169 |    11.951 |     8.284 |     3.667 | UNDERPOWERED            |
| ('PK', 'medium')            |  169 |    37.426 |    33.728 |     3.698 | UNDERPOWERED            |
| ('PK', 'low')               |  169 |    50.624 |    57.988 |    -7.365 | UNDERPOWERED            |
| ('4v4', 'high')             |   75 |    13.000 |    10.667 |     2.333 | reported (UNDERPOWERED) |
| ('4v4', 'medium')           |   75 |    49.565 |    57.333 |    -7.768 | reported (UNDERPOWERED) |
| ('4v4', 'low')              |   75 |    37.435 |    32.000 |     5.435 | reported (UNDERPOWERED) |
| ('all reachable', 'high')   | 7517 |    12.663 |    12.665 |    -0.001 | PASS                    |
| ('all reachable', 'medium') | 7517 |    40.119 |    38.180 |     1.939 | FAIL                    |
| ('all reachable', 'low')    | 7517 |    47.218 |    49.155 |    -1.937 | FAIL                    |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.269 |    66.848 |     2.420 |
| slap       |    12.380 |    11.467 |     0.912 |
| backhand   |     7.359 |     8.208 |    -0.849 |
| tip+defl   |     9.503 |    11.760 |    -2.257 |
| wrap       |     0.946 |     0.785 |     0.161 |
| other      |     0.544 |     0.931 |    -0.387 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00166; tolerance 0.00190)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00031 |
| attribute mix within state (sim weights)                         |         +0.00197 |

- Decomposition verdict (playoffs): COMPENSATED

## overall

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                95924 |   0.0588 |   0.0584 |  0.0069 |            0.2930 |            0.2904 |              0.0598 |              0.0590 | PASS            |
| PP            |                15819 |   0.1009 |   0.1009 | -0.0002 |            0.2619 |            0.2522 |              0.1008 |              0.1029 | PASS            |
| PK            |                 2602 |   0.0698 |   0.0683 |  0.0224 |            0.1246 |            0.1218 |              0.0728 |              0.0734 | PASS            |
| 4v4           |                 1242 |   0.0660 |   0.0693 | -0.0479 |            0.2364 |            0.2404 |              0.0811 |              0.0797 | reported (FAIL) |
| 3v3           |                 1129 |   0.0839 |   0.0872 | -0.0375 |            0.1739 |            0.1753 |              0.1429 |              0.1444 | reported (FAIL) |
| all reachable |               116716 |   0.0650 |   0.0648 |  0.0036 |            0.2843 |            0.2809 |              0.0666 |              0.0663 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  95924 |    12.057 |    12.164 |    -0.107 | PASS            |
| ('5v5', 'medium')           |  95924 |    38.794 |    38.998 |    -0.203 | PASS            |
| ('5v5', 'low')              |  95924 |    49.149 |    48.839 |     0.310 | PASS            |
| ('PP', 'high')              |  15819 |    17.054 |    16.885 |     0.169 | PASS            |
| ('PP', 'medium')            |  15819 |    47.655 |    47.620 |     0.035 | PASS            |
| ('PP', 'low')               |  15819 |    35.291 |    35.495 |    -0.204 | PASS            |
| ('PK', 'high')              |   2602 |    12.653 |    11.875 |     0.778 | PASS            |
| ('PK', 'medium')            |   2602 |    36.987 |    37.625 |    -0.638 | PASS            |
| ('PK', 'low')               |   2602 |    50.359 |    50.500 |    -0.140 | PASS            |
| ('4v4', 'high')             |   1242 |    12.809 |    14.332 |    -1.523 | reported (FAIL) |
| ('4v4', 'medium')           |   1242 |    48.785 |    54.267 |    -5.482 | reported (FAIL) |
| ('4v4', 'low')              |   1242 |    38.406 |    31.401 |     7.005 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.144 |    15.855 |     2.289 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.468 |    60.142 |    -8.674 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.388 |    24.004 |     6.385 | reported (FAIL) |
| ('all reachable', 'high')   | 116716 |    12.806 |    12.856 |    -0.050 | PASS            |
| ('all reachable', 'medium') | 116716 |    40.177 |    40.503 |    -0.325 | PASS            |
| ('all reachable', 'low')    | 116716 |    47.017 |    46.641 |     0.376 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.295 |    69.095 |     0.200 |
| slap       |    12.234 |    11.581 |     0.653 |
| backhand   |     7.357 |     7.139 |     0.218 |
| tip+defl   |     9.643 |    10.586 |    -0.944 |
| wrap       |     0.940 |     0.733 |     0.207 |
| other      |     0.531 |     0.866 |    -0.335 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00023; tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00006 |
| attribute mix within state (sim weights)                         |         +0.00029 |

- Decomposition verdict (overall): CLEAN

## G3 gate (overall slice; all reachable / 5v5 / PP / PK)

| cell          | check            |   value | status   |
|:--------------|:-----------------|--------:|:---------|
| all reachable | xG per unblocked | +0.0036 | PASS     |
| all reachable | tier high pp     | -0.0503 | PASS     |
| all reachable | tier medium pp   | -0.3253 | PASS     |
| all reachable | tier low pp      | +0.3756 | PASS     |
| 5v5           | xG per unblocked | +0.0069 | PASS     |
| 5v5           | tier high pp     | -0.1069 | PASS     |
| 5v5           | tier medium pp   | -0.2031 | PASS     |
| 5v5           | tier low pp      | +0.3100 | PASS     |
| PP            | xG per unblocked | -0.0002 | PASS     |
| PP            | tier high pp     | +0.1693 | PASS     |
| PP            | tier medium pp   | +0.0348 | PASS     |
| PP            | tier low pp      | -0.2041 | PASS     |
| PK            | xG per unblocked | +0.0224 | PASS     |
| PK            | tier high pp     | +0.7778 | PASS     |
| PK            | tier medium pp   | -0.6377 | PASS     |
| PK            | tier low pp      | -0.1401 | PASS     |

- **G3: PASS**

## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6755 |               1.6503 |     58.5259 |     58.3508 |               58.3508 |     17.1770 |     16.8941 |     41.3489 |     41.4566 |          0.2935 |          0.2895 |      36578.0000 |        89759.0000 |      0.0030 |      0.0167 |     -0.0026 |              0.3967 |
| PP      |               0.1512 |               0.1474 |    101.0246 |    101.6226 |              101.6226 |     26.5245 |     25.5582 |     74.5001 |     76.0644 |          0.2626 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0059 |      0.0378 |     -0.0206 |              1.1054 |
| PK      |               0.1512 |               0.1474 |     14.0037 |     14.3173 |               14.3173 |      1.7475 |      1.7373 |     12.2561 |     12.5800 |          0.1248 |          0.1213 |        336.0000 |         2433.0000 |     -0.0219 |      0.0059 |     -0.0257 |              0.3447 |
| 4v4     |               0.0258 |               0.0240 |     49.9957 |     48.6237 |               48.6237 |     11.8233 |     11.5120 |     38.1724 |     37.1118 |          0.2365 |          0.2368 |        362.0000 |         1167.0000 |      0.0282 |      0.0270 |      0.0286 |             -0.0270 |
| 3v3     |               0.0173 |               0.0189 |     58.2338 |     55.2313 |               55.2313 |     10.1244 |      9.6826 |     48.1094 |     45.5487 |          0.1739 |          0.1753 |        240.0000 |         1129.0000 |      0.0544 |      0.0456 |      0.0562 |             -0.1452 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.7102 |               1.7065 |     61.2394 |     60.2558 |               60.2558 |     17.5219 |     18.2478 |     43.7174 |     42.0080 |          0.2861 |          0.3028 |       2678.0000 |         6165.0000 |      0.0163 |     -0.0398 |      0.0407 |             -1.6716 |
| PP      |               0.1616 |               0.1694 |    105.2229 |    102.9062 |              102.9062 |     26.5840 |     26.8421 |     78.6388 |     76.0641 |          0.2526 |          0.2608 |        391.0000 |         1108.0000 |      0.0225 |     -0.0096 |      0.0338 |             -0.8195 |
| PK      |               0.1616 |               0.1694 |     14.6467 |     13.3181 |               13.3181 |      1.7820 |      1.7162 |     12.8647 |     11.6018 |          0.1217 |          0.1289 |         25.0000 |          169.0000 |      0.0998 |      0.0383 |      0.1088 |             -0.7200 |
| 4v4     |               0.0266 |               0.0239 |     50.8268 |     51.5258 |               51.5258 |     11.9275 |     15.0689 |     38.8992 |     36.4569 |          0.2347 |          0.2925 |         31.0000 |           75.0000 |     -0.0136 |     -0.2085 |      0.0670 |             -5.7783 |
| 3v3     |               0.0001 |               0.0000 |     55.9756 |      0.0000 |                0.0000 |     14.2683 |      0.0000 |     41.7073 |      0.0000 |          0.2549 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6776 |               1.6537 |     58.6960 |     58.4717 |               58.4717 |     17.1986 |     16.9801 |     41.4974 |     41.4916 |          0.2930 |          0.2904 |      39256.0000 |        95924.0000 |      0.0038 |      0.0129 |      0.0001 |              0.2614 |
| PP      |               0.1519 |               0.1488 |    101.2994 |    101.7125 |              101.7125 |     26.5284 |     25.6481 |     74.7711 |     76.0644 |          0.2619 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0041 |      0.0343 |     -0.0170 |              0.9718 |
| PK      |               0.1519 |               0.1488 |     14.0458 |     14.2473 |               14.2473 |      1.7498 |      1.7358 |     12.2960 |     12.5115 |          0.1246 |          0.1218 |        361.0000 |         2602.0000 |     -0.0141 |      0.0080 |     -0.0172 |              0.2741 |
| 4v4     |               0.0258 |               0.0240 |     50.0485 |     48.8019 |               48.8019 |     11.8299 |     11.7304 |     38.2185 |     37.0716 |          0.2364 |          0.2404 |        393.0000 |         1242.0000 |      0.0255 |      0.0085 |      0.0309 |             -0.3998 |
| 3v3     |               0.0162 |               0.0177 |     58.2334 |     55.2313 |               55.2313 |     10.1253 |      9.6826 |     48.1081 |     45.5487 |          0.1739 |          0.1753 |        240.0000 |         1129.0000 |      0.0544 |      0.0457 |      0.0562 |             -0.1437 |

## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES rating; 1,000 game bootstrap)

- for: R 1.245 (95% CI 0.948..1.857; UNDERPOWERED), old Q5-Q1 1.216, 2,796 units
- against: R 1.129 (95% CI 0.862..1.661; UNDERPOWERED), old Q5-Q1 1.201, 2,796 units

## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.82; 29/32 within 3%, 13/32 tiers within 1.5 pp)

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0674 |   0.0675 | -0.0016 |         0.2658 |          -1.0720 |        0.8062 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0643 |   0.0639 |  0.0056 |         0.1639 |           1.4798 |       -1.6437 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0658 |   0.0645 |  0.0199 |         0.7056 |          -2.2116 |        1.5061 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0661 |   0.0671 | -0.0150 |        -0.1724 |           0.3064 |       -0.1340 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0660 |   0.0667 | -0.0110 |        -0.0631 |           2.4102 |       -2.3471 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0674 |   0.0661 |  0.0201 |         0.9239 |           0.7290 |       -1.6529 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         7 |                 3386 |   0.0647 |   0.0642 |  0.0069 |         0.9803 |          -5.2893 |        4.3089 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0664 |   0.0671 | -0.0110 |         0.4659 |          -3.3138 |        2.8479 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0637 |   0.0637 |  0.0002 |         0.0542 |          -0.3172 |        0.2630 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        10 |                 3818 |   0.0670 |   0.0669 |  0.0024 |        -0.5341 |          -1.0060 |        1.5401 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0634 |   0.0635 | -0.0014 |        -0.2864 |          -0.7950 |        1.0813 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        13 |                 4813 |   0.0646 |   0.0633 |  0.0195 |         0.1614 |           1.2874 |       -1.4488 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        14 |                 3605 |   0.0662 |   0.0674 | -0.0176 |        -0.9147 |           1.9658 |       -1.0511 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0010 |        -2.8378 |           2.4515 |        0.3863 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0639 |   0.0647 | -0.0123 |         0.4394 |          -1.3215 |        0.8821 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0654 |   0.0664 | -0.0157 |         0.4913 |          -2.7249 |        2.2336 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0652 |   0.0655 | -0.0037 |         0.7796 |          -2.3111 |        1.5315 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0638 |   0.0645 | -0.0104 |         0.0035 |          -3.8146 |        3.8111 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0627 |   0.0603 |  0.0387 |         0.1743 |          -1.6786 |        1.5043 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0655 |   0.0643 |  0.0196 |        -0.0402 |          -0.8514 |        0.8916 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0668 |   0.0672 | -0.0068 |        -0.0711 |           4.0835 |       -4.0124 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0648 |   0.0636 |  0.0191 |        -0.4500 |           1.5408 |       -1.0908 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        24 |                 3372 |   0.0634 |   0.0632 |  0.0027 |        -0.4067 |          -2.9172 |        3.3239 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        25 |                 4139 |   0.0662 |   0.0688 | -0.0375 |        -0.8953 |           1.2459 |       -0.3506 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0633 |   0.0624 |  0.0149 |         0.2580 |           0.6880 |       -0.9460 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        28 |                 3172 |   0.0639 |   0.0632 |  0.0108 |         1.1281 |          -1.9947 |        0.8665 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        29 |                 3395 |   0.0641 |   0.0627 |  0.0237 |         0.4010 |          -0.6712 |        0.2702 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        30 |                 3531 |   0.0657 |   0.0622 |  0.0550 |        -0.2708 |           0.9644 |       -0.6936 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0640 |   0.0647 | -0.0104 |        -1.4492 |           3.8101 |       -2.3608 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0654 |   0.0651 |  0.0051 |        -0.4073 |          -1.0419 |        1.4492 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0630 |   0.0612 |  0.0296 |         0.4459 |          -0.8599 |        0.4140 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        59 |                 3566 |   0.0643 |   0.0647 | -0.0067 |         0.3563 |          -2.9135 |        2.5572 | UNDERPOWERED (team-level, labelled) | True            | False              |

## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)

### regular season

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       58768 |     27.4462 |     27.1429 |           0.3362 |           0.3453 |   0.9098 |   0.9096 |            0.9097 |    2.4762 |    2.4548 |      0.0112 |   -0.9041 |  0.0220 |    0.0087 | nan                          |
| PP            |        9973 |     51.1871 |     51.5662 |           0.3129 |           0.3221 |   0.8534 |   0.8491 |            0.8534 |    7.5028 |    7.7817 |     -0.0074 |   -0.9146 |  0.4332 |   -0.0358 | nan                          |
| PK            |        1923 |      9.6322 |      9.9430 |           0.2141 |           0.2096 |   0.9072 |   0.9048 |            0.9071 |    0.8939 |    0.9462 |     -0.0313 |    0.4474 |  0.2363 |   -0.0553 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |         812 |     25.4843 |     25.8224 |           0.3324 |           0.3042 |   0.8781 |   0.8879 |            0.8785 |    3.1059 |    2.8939 |     -0.0131 |    2.8191 | -0.9807 |    0.0733 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     34.0819 |     33.5664 |           0.2916 |           0.2631 |   0.7982 |   0.8041 |            0.7975 |    6.8761 |    6.5761 |      0.0154 |    2.8511 | -0.5838 |    0.0456 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       72308 |     27.9215 |     27.7237 |           0.3299 |           0.3378 |   0.9004 |   0.8996 |            0.9004 |    2.7796 |    2.7824 |      0.0071 |   -0.7896 |  0.0810 |   -0.0010 | nan                          |

### playoffs

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |    sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|---------:|----------:|:-----------------------------|
| 5v5           |        3753 |     28.3977 |     25.5728 |           0.3504 |           0.3912 |   0.9109 |   0.9081 |            0.9107 |    2.5309 |    2.3508 |      0.1105 |   -4.0816 |   0.2804 |    0.0766 | nan                          |
| PP            |         730 |     53.6051 |     50.1144 |           0.3183 |           0.3412 |   0.8505 |   0.8315 |            0.8508 |    8.0122 |    8.4439 |      0.0697 |   -2.2818 |   1.9026 |   -0.0511 | UNDERPOWERED (n SOG < 2,000) |
| PK            |         135 |     10.1669 |      9.2677 |           0.2097 |           0.2012 |   0.9100 |   0.9407 |            0.9080 |    0.9147 |    0.5492 |      0.0970 |    0.8525 |  -3.0714 |    0.6656 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |          52 |     25.4090 |     25.2768 |           0.3468 |           0.3067 |   0.8811 |   0.8462 |            0.8829 |    3.0206 |    3.8887 |      0.0052 |    4.0132 |   3.4966 |   -0.2232 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |           0 |     25.2439 |      0.0000 |           0.3947 |         nan      |   0.8261 | nan      |            0.8652 |    4.3902 |    0.0000 |    nan      |  nan      | nan      |  nan      | UNDERPOWERED (n SOG < 2,000) |
| all reachable |        4670 |     28.9064 |     26.2436 |           0.3427 |           0.3787 |   0.9017 |   0.8964 |            0.9016 |    2.8405 |    2.7199 |      0.1015 |   -3.6089 |   0.5374 |    0.0443 | nan                          |

### overall

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       62521 |     27.5059 |     27.0433 |           0.3372 |           0.3482 |   0.9099 |   0.9095 |            0.9098 |    2.4796 |    2.4482 |      0.0171 |   -1.1057 |  0.0380 |    0.0128 | nan                          |
| PP            |       10703 |     51.3454 |     51.4645 |           0.3133 |           0.3234 |   0.8532 |   0.8479 |            0.8532 |    7.5361 |    7.8281 |     -0.0023 |   -1.0110 |  0.5334 |   -0.0373 | nan                          |
| PK            |        2058 |      9.6672 |      9.8957 |           0.2138 |           0.2091 |   0.9074 |   0.9072 |            0.9071 |    0.8952 |    0.9184 |     -0.0231 |    0.4722 |  0.0203 |   -0.0252 | nan                          |
| 4v4           |         864 |     25.4795 |     25.7889 |           0.3333 |           0.3043 |   0.8783 |   0.8854 |            0.8788 |    3.1005 |    2.9550 |     -0.0120 |    2.8972 | -0.7103 |    0.0493 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     34.0801 |     33.5664 |           0.2916 |           0.2631 |   0.7983 |   0.8041 |            0.7975 |    6.8756 |    6.5761 |      0.0153 |    2.8529 | -0.5834 |    0.0455 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       76978 |     27.9831 |     27.6292 |           0.3308 |           0.3405 |   0.9005 |   0.8994 |            0.9005 |    2.7834 |    2.7784 |      0.0128 |   -0.9693 |  0.1093 |    0.0018 | nan                          |

