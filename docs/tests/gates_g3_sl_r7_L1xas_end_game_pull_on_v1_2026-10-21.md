# G3 closed loop, SL-R7 L1x-as: end_game_pull_on_v1, fold 2 (2024-25), 1398 games x 200 seeds

> **EG-R1 part A closed loop (Lane H8a), goalie pull ON.** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t, pull P1 + EN cascade (EN attempt and EN goal levels STAND-IN). No delayed-penalty state (INV-70); OT = stage-1 3v3, shootout 50 / 50 stub; no rebounds. Report text produced by the SL-R7 grader.

Generated 2026-10-21 14:21:02 -0400 by `scripts/run_shot_attribute_g3_v4.py grade`.

Engine markers: attr_model `stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)`; stand_in ['block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable']; goal_model `goal: C1s (provisional, D40)`; oracle_goalie `ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)`.

Served-vs-offline parity before the seeds (max |diff|): hazard 0.00e+00 over 523,057 rows; goal_eaf 1.11e-16 over 1,487 rows; block 1.47e-08 over 4,720 rows; miss 2.98e-08 over 3,208 rows; class 2.98e-08 over 3,208 rows.

Tolerances g3_xg_rel 0.03, g3_mix_pp 1.5; cells with n < 300 actual unblocked attempts UNDERPOWERED. Gated cells: all reachable, 5v5, PP, PK (xG_ref per unblocked attempt and the three tier shares); 4v4 / 3v3 reported.

## regular season

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                89759 |   0.0588 |   0.0585 |  0.0048 |            0.2928 |            0.2895 |              0.0598 |              0.0592 | PASS            |
| PP            |                14711 |   0.1009 |   0.1009 | -0.0009 |            0.2616 |            0.2515 |              0.1007 |              0.1023 | PASS            |
| PK            |                 2433 |   0.0700 |   0.0690 |  0.0140 |            0.1251 |            0.1213 |              0.0728 |              0.0752 | PASS            |
| 4v4           |                 1167 |   0.0659 |   0.0702 | -0.0619 |            0.2371 |            0.2368 |              0.0811 |              0.0780 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0368 |            0.1701 |            0.1753 |              0.1432 |              0.1444 | reported (FAIL) |
| all reachable |               109199 |   0.0651 |   0.0649 |  0.0027 |            0.2839 |            0.2800 |              0.0668 |              0.0665 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  89759 |    12.058 |    12.141 |    -0.083 | PASS            |
| ('5v5', 'medium')           |  89759 |    38.790 |    39.167 |    -0.377 | PASS            |
| ('5v5', 'low')              |  89759 |    49.151 |    48.691 |     0.460 | PASS            |
| ('PP', 'high')              |  14711 |    17.042 |    17.069 |    -0.027 | PASS            |
| ('PP', 'medium')            |  14711 |    47.668 |    47.685 |    -0.017 | PASS            |
| ('PP', 'low')               |  14711 |    35.290 |    35.246 |     0.044 | PASS            |
| ('PK', 'high')              |   2433 |    12.696 |    12.125 |     0.571 | PASS            |
| ('PK', 'medium')            |   2433 |    36.959 |    37.896 |    -0.936 | PASS            |
| ('PK', 'low')               |   2433 |    50.345 |    49.979 |     0.366 | PASS            |
| ('4v4', 'high')             |   1167 |    12.765 |    14.567 |    -1.803 | reported (FAIL) |
| ('4v4', 'medium')           |   1167 |    48.580 |    54.070 |    -5.491 | reported (FAIL) |
| ('4v4', 'low')              |   1167 |    38.656 |    31.362 |     7.293 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.193 |    15.855 |     2.338 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.437 |    60.142 |    -8.705 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.370 |    24.004 |     6.367 | reported (FAIL) |
| ('all reachable', 'high')   | 109199 |    12.822 |    12.869 |    -0.048 | PASS            |
| ('all reachable', 'medium') | 109199 |    40.205 |    40.662 |    -0.457 | PASS            |
| ('all reachable', 'low')    | 109199 |    46.973 |    46.468 |     0.505 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.305 |    69.250 |     0.056 |
| slap       |    12.218 |    11.589 |     0.629 |
| backhand   |     7.362 |     7.065 |     0.297 |
| tip+defl   |     9.645 |    10.506 |    -0.861 |
| wrap       |     0.940 |     0.729 |     0.211 |
| other      |     0.530 |     0.862 |    -0.331 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00017; tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         +0.00003 |
| attribute mix within state (sim weights)                         |         +0.00015 |

- Decomposition verdict (regular season): CLEAN

## playoffs

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |    rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status                  |
|:--------------|---------------------:|---------:|---------:|-------:|------------------:|------------------:|--------------------:|--------------------:|:------------------------|
| 5v5           |                 6165 |   0.0586 |   0.0567 | 0.0324 |            0.2871 |            0.3028 |              0.0578 |              0.0560 | FAIL                    |
| PP            |                 1108 |   0.1012 |   0.1004 | 0.0074 |            0.2526 |            0.2608 |              0.1020 |              0.1110 | PASS                    |
| PK            |                  169 |   0.0676 |   0.0585 | 0.1559 |            0.1218 |            0.1289 |              0.0709 |              0.0473 | UNDERPOWERED            |
| 4v4           |                   75 |   0.0663 |   0.0553 | 0.1982 |            0.2383 |            0.2925 |              0.0777 |              0.1067 | reported (UNDERPOWERED) |
| all reachable |                 7517 |   0.0648 |   0.0632 | 0.0262 |            0.2788 |            0.2936 |              0.0645 |              0.0644 | PASS                    |

### Location tier shares (%)

|                             |    n |   sim_pct |   act_pct |   diff_pp | status                  |
|:----------------------------|-----:|----------:|----------:|----------:|:------------------------|
| ('5v5', 'high')             | 6165 |    11.934 |    12.490 |    -0.556 | PASS                    |
| ('5v5', 'medium')           | 6165 |    38.732 |    36.529 |     2.204 | FAIL                    |
| ('5v5', 'low')              | 6165 |    49.334 |    50.981 |    -1.648 | FAIL                    |
| ('PP', 'high')              | 1108 |    16.969 |    14.440 |     2.528 | FAIL                    |
| ('PP', 'medium')            | 1108 |    47.824 |    46.751 |     1.073 | PASS                    |
| ('PP', 'low')               | 1108 |    35.208 |    38.809 |    -3.601 | FAIL                    |
| ('PK', 'high')              |  169 |    11.852 |     8.284 |     3.568 | UNDERPOWERED            |
| ('PK', 'medium')            |  169 |    37.474 |    33.728 |     3.746 | UNDERPOWERED            |
| ('PK', 'low')               |  169 |    50.674 |    57.988 |    -7.315 | UNDERPOWERED            |
| ('4v4', 'high')             |   75 |    12.972 |    10.667 |     2.305 | reported (UNDERPOWERED) |
| ('4v4', 'medium')           |   75 |    49.413 |    57.333 |    -7.920 | reported (UNDERPOWERED) |
| ('4v4', 'low')              |   75 |    37.615 |    32.000 |     5.615 | reported (UNDERPOWERED) |
| ('all reachable', 'high')   | 7517 |    12.652 |    12.665 |    -0.013 | PASS                    |
| ('all reachable', 'medium') | 7517 |    40.103 |    38.180 |     1.923 | FAIL                    |
| ('all reachable', 'low')    | 7517 |    47.246 |    49.155 |    -1.910 | FAIL                    |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.272 |    66.848 |     2.423 |
| slap       |    12.417 |    11.467 |     0.950 |
| backhand   |     7.355 |     8.208 |    -0.853 |
| tip+defl   |     9.465 |    11.760 |    -2.295 |
| wrap       |     0.948 |     0.785 |     0.163 |
| other      |     0.543 |     0.931 |    -0.388 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00166; tolerance 0.00190)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00030 |
| attribute mix within state (sim weights)                         |         +0.00196 |

- Decomposition verdict (playoffs): COMPENSATED

## overall

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                95924 |   0.0588 |   0.0584 |  0.0065 |            0.2924 |            0.2904 |              0.0597 |              0.0590 | PASS            |
| PP            |                15819 |   0.1009 |   0.1009 | -0.0003 |            0.2610 |            0.2522 |              0.1008 |              0.1029 | PASS            |
| PK            |                 2602 |   0.0698 |   0.0683 |  0.0218 |            0.1248 |            0.1218 |              0.0727 |              0.0734 | PASS            |
| 4v4           |                 1242 |   0.0659 |   0.0693 | -0.0493 |            0.2372 |            0.2404 |              0.0809 |              0.0797 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0368 |            0.1701 |            0.1753 |              0.1432 |              0.1444 | reported (FAIL) |
| all reachable |               116716 |   0.0651 |   0.0648 |  0.0041 |            0.2835 |            0.2809 |              0.0667 |              0.0663 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  95924 |    12.050 |    12.164 |    -0.114 | PASS            |
| ('5v5', 'medium')           |  95924 |    38.786 |    38.998 |    -0.211 | PASS            |
| ('5v5', 'low')              |  95924 |    49.163 |    48.839 |     0.325 | PASS            |
| ('PP', 'high')              |  15819 |    17.037 |    16.885 |     0.152 | PASS            |
| ('PP', 'medium')            |  15819 |    47.679 |    47.620 |     0.059 | PASS            |
| ('PP', 'low')               |  15819 |    35.284 |    35.495 |    -0.211 | PASS            |
| ('PK', 'high')              |   2602 |    12.638 |    11.875 |     0.762 | PASS            |
| ('PK', 'medium')            |   2602 |    36.995 |    37.625 |    -0.630 | PASS            |
| ('PK', 'low')               |   2602 |    50.368 |    50.500 |    -0.132 | PASS            |
| ('4v4', 'high')             |   1242 |    12.778 |    14.332 |    -1.554 | reported (FAIL) |
| ('4v4', 'medium')           |   1242 |    48.633 |    54.267 |    -5.635 | reported (FAIL) |
| ('4v4', 'low')              |   1242 |    38.589 |    31.401 |     7.189 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.192 |    15.855 |     2.338 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.435 |    60.142 |    -8.706 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.372 |    24.004 |     6.369 | reported (FAIL) |
| ('all reachable', 'high')   | 116716 |    12.810 |    12.856 |    -0.046 | PASS            |
| ('all reachable', 'medium') | 116716 |    40.198 |    40.503 |    -0.304 | PASS            |
| ('all reachable', 'low')    | 116716 |    46.991 |    46.641 |     0.350 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.303 |    69.095 |     0.208 |
| slap       |    12.231 |    11.581 |     0.650 |
| backhand   |     7.361 |     7.139 |     0.223 |
| tip+defl   |     9.633 |    10.586 |    -0.953 |
| wrap       |     0.940 |     0.733 |     0.208 |
| other      |     0.531 |     0.866 |    -0.335 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00027; tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         +0.00001 |
| attribute mix within state (sim weights)                         |         +0.00026 |

- Decomposition verdict (overall): CLEAN

## G3 gate (overall slice; all reachable / 5v5 / PP / PK)

| cell          | check            |   value | status   |
|:--------------|:-----------------|--------:|:---------|
| all reachable | xG per unblocked | +0.0041 | PASS     |
| all reachable | tier high pp     | -0.0456 | PASS     |
| all reachable | tier medium pp   | -0.3042 | PASS     |
| all reachable | tier low pp      | +0.3498 | PASS     |
| 5v5           | xG per unblocked | +0.0065 | PASS     |
| 5v5           | tier high pp     | -0.1136 | PASS     |
| 5v5           | tier medium pp   | -0.2112 | PASS     |
| 5v5           | tier low pp      | +0.3248 | PASS     |
| PP            | xG per unblocked | -0.0003 | PASS     |
| PP            | tier high pp     | +0.1523 | PASS     |
| PP            | tier medium pp   | +0.0591 | PASS     |
| PP            | tier low pp      | -0.2114 | PASS     |
| PK            | xG per unblocked | +0.0218 | PASS     |
| PK            | tier high pp     | +0.7623 | PASS     |
| PK            | tier medium pp   | -0.6303 | PASS     |
| PK            | tier low pp      | -0.1320 | PASS     |

- **G3: PASS**

## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6437 |               1.6503 |     58.6344 |     58.3508 |               58.3508 |     17.1695 |     16.8941 |     41.4649 |     41.4566 |          0.2928 |          0.2895 |      36578.0000 |        89759.0000 |      0.0049 |      0.0163 |      0.0002 |              0.3295 |
| PP      |               0.1492 |               0.1474 |    101.0837 |    101.6226 |              101.6226 |     26.4427 |     25.5582 |     74.6410 |     76.0644 |          0.2616 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0053 |      0.0346 |     -0.0187 |              1.0091 |
| PK      |               0.1492 |               0.1474 |     14.0146 |     14.3173 |               14.3173 |      1.7525 |      1.7373 |     12.2621 |     12.5800 |          0.1251 |          0.1213 |        336.0000 |         2433.0000 |     -0.0211 |      0.0088 |     -0.0253 |              0.3708 |
| 4v4     |               0.0256 |               0.0240 |     50.1839 |     48.6237 |               48.6237 |     11.8979 |     11.5120 |     38.2859 |     37.1118 |          0.2371 |          0.2368 |        362.0000 |         1167.0000 |      0.0321 |      0.0335 |      0.0316 |              0.0331 |
| 3v3     |               0.0204 |               0.0189 |     58.2271 |     55.2313 |               55.2313 |      9.9027 |      9.6826 |     48.3244 |     45.5487 |          0.1701 |          0.1753 |        240.0000 |         1129.0000 |      0.0542 |      0.0227 |      0.0609 |             -0.5241 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6884 |               1.7065 |     61.4104 |     60.2558 |               60.2558 |     17.6339 |     18.2478 |     43.7765 |     42.0080 |          0.2871 |          0.3028 |       2678.0000 |         6165.0000 |      0.0192 |     -0.0336 |      0.0421 |             -1.5690 |
| PP      |               0.1599 |               0.1694 |    105.4092 |    102.9062 |              102.9062 |     26.6251 |     26.8421 |     78.7841 |     76.0641 |          0.2526 |          0.2608 |        391.0000 |         1108.0000 |      0.0243 |     -0.0081 |      0.0358 |             -0.8253 |
| PK      |               0.1599 |               0.1694 |     14.6644 |     13.3181 |               13.3181 |      1.7857 |      1.7162 |     12.8786 |     11.6018 |          0.1218 |          0.1289 |         25.0000 |          169.0000 |      0.1011 |      0.0405 |      0.1101 |             -0.7093 |
| 4v4     |               0.0262 |               0.0239 |     50.9552 |     51.5258 |               51.5258 |     12.1439 |     15.0689 |     38.8112 |     36.4569 |          0.2383 |          0.2925 |         31.0000 |           75.0000 |     -0.0111 |     -0.1941 |      0.0646 |             -5.4127 |
| 3v3     |               0.0001 |               0.0000 |     55.3137 |      0.0000 |                0.0000 |     13.8284 |      0.0000 |     41.4853 |      0.0000 |          0.2500 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6464 |               1.6537 |     58.8095 |     58.4717 |               58.4717 |     17.1988 |     16.9801 |     41.6107 |     41.4916 |          0.2924 |          0.2904 |      39256.0000 |        95924.0000 |      0.0058 |      0.0129 |      0.0029 |              0.2051 |
| PP      |               0.1499 |               0.1488 |    101.3675 |    101.7125 |              101.7125 |     26.4547 |     25.6481 |     74.9128 |     76.0644 |          0.2610 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0034 |      0.0314 |     -0.0151 |              0.8815 |
| PK      |               0.1499 |               0.1488 |     14.0573 |     14.2473 |               14.2473 |      1.7547 |      1.7358 |     12.3025 |     12.5115 |          0.1248 |          0.1218 |        361.0000 |         2602.0000 |     -0.0133 |      0.0109 |     -0.0167 |              0.2991 |
| 4v4     |               0.0256 |               0.0240 |     50.2324 |     48.8019 |               48.8019 |     11.9134 |     11.7304 |     38.3190 |     37.0716 |          0.2372 |          0.2404 |        393.0000 |         1242.0000 |      0.0293 |      0.0156 |      0.0336 |             -0.3201 |
| 3v3     |               0.0191 |               0.0177 |     58.2266 |     55.2313 |               55.2313 |      9.9033 |      9.6826 |     48.3233 |     45.5487 |          0.1701 |          0.1753 |        240.0000 |         1129.0000 |      0.0542 |      0.0228 |      0.0609 |             -0.5228 |

## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES rating; 1,000 game bootstrap)

- for: R 1.242 (95% CI 0.945..1.849; UNDERPOWERED), old Q5-Q1 1.213, 2,796 units
- against: R 1.125 (95% CI 0.859..1.656; UNDERPOWERED), old Q5-Q1 1.197, 2,796 units

## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.82; 28/32 within 3%, 13/32 tiers within 1.5 pp)

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0674 |   0.0675 | -0.0005 |         0.2705 |          -1.0614 |        0.7909 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0644 |   0.0639 |  0.0071 |         0.1912 |           1.5149 |       -1.7061 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0659 |   0.0645 |  0.0203 |         0.7190 |          -2.1850 |        1.4660 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0662 |   0.0671 | -0.0139 |        -0.1682 |           0.3638 |       -0.1955 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0660 |   0.0667 | -0.0105 |        -0.0533 |           2.4228 |       -2.3695 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0674 |   0.0661 |  0.0201 |         0.9259 |           0.7442 |       -1.6701 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         7 |                 3386 |   0.0647 |   0.0642 |  0.0073 |         0.9930 |          -5.2767 |        4.2837 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0664 |   0.0671 | -0.0107 |         0.4658 |          -3.3139 |        2.8481 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0637 |   0.0637 |  0.0011 |         0.0613 |          -0.2943 |        0.2330 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        10 |                 3818 |   0.0671 |   0.0669 |  0.0031 |        -0.5310 |          -1.0035 |        1.5345 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0634 |   0.0635 | -0.0013 |        -0.2800 |          -0.7814 |        1.0614 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        13 |                 4813 |   0.0646 |   0.0633 |  0.0200 |         0.1622 |           1.3084 |       -1.4706 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        14 |                 3605 |   0.0663 |   0.0674 | -0.0175 |        -0.9289 |           1.9784 |       -1.0495 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0017 |        -2.8398 |           2.4615 |        0.3784 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0639 |   0.0647 | -0.0123 |         0.4434 |          -1.3171 |        0.8737 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0654 |   0.0664 | -0.0157 |         0.4983 |          -2.7219 |        2.2236 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0653 |   0.0655 | -0.0029 |         0.7941 |          -2.3017 |        1.5076 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0639 |   0.0645 | -0.0099 |         0.0037 |          -3.7705 |        3.7668 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0627 |   0.0603 |  0.0387 |         0.1668 |          -1.6514 |        1.4846 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0655 |   0.0643 |  0.0191 |        -0.0591 |          -0.8437 |        0.9027 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0668 |   0.0672 | -0.0065 |        -0.0682 |           4.1130 |       -4.0448 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0648 |   0.0636 |  0.0199 |        -0.4384 |           1.5599 |       -1.1215 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        24 |                 3372 |   0.0635 |   0.0632 |  0.0038 |        -0.4007 |          -2.8822 |        3.2828 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        25 |                 4139 |   0.0662 |   0.0688 | -0.0372 |        -0.8978 |           1.2605 |       -0.3627 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0634 |   0.0624 |  0.0163 |         0.2613 |           0.7485 |       -1.0098 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        28 |                 3172 |   0.0639 |   0.0632 |  0.0111 |         1.1312 |          -1.9547 |        0.8235 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        29 |                 3395 |   0.0642 |   0.0627 |  0.0245 |         0.4131 |          -0.6489 |        0.2357 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        30 |                 3531 |   0.0657 |   0.0622 |  0.0556 |        -0.2667 |           0.9951 |       -0.7284 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0641 |   0.0647 | -0.0096 |        -1.4476 |           3.8396 |       -2.3920 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0654 |   0.0651 |  0.0052 |        -0.3992 |          -1.0122 |        1.4114 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0630 |   0.0612 |  0.0306 |         0.4764 |          -0.8525 |        0.3760 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        59 |                 3566 |   0.0643 |   0.0647 | -0.0065 |         0.3604 |          -2.9026 |        2.5422 | UNDERPOWERED (team-level, labelled) | True            | False              |

## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)

### regular season

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       58768 |     27.5217 |     27.1429 |           0.3363 |           0.3453 |   0.9099 |   0.9096 |            0.9098 |    2.4803 |    2.4548 |      0.0140 |   -0.9003 |  0.0317 |    0.0104 | nan                          |
| PP            |        9973 |     51.2759 |     51.5662 |           0.3130 |           0.3221 |   0.8535 |   0.8491 |            0.8535 |    7.5138 |    7.7817 |     -0.0056 |   -0.9039 |  0.4370 |   -0.0344 | nan                          |
| PK            |        1923 |      9.6353 |      9.9430 |           0.2142 |           0.2096 |   0.9073 |   0.9048 |            0.9072 |    0.8928 |    0.9462 |     -0.0310 |    0.4604 |  0.2502 |   -0.0564 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |         812 |     25.5789 |     25.8224 |           0.3319 |           0.3042 |   0.8786 |   0.8879 |            0.8788 |    3.1052 |    2.8939 |     -0.0094 |    2.7698 | -0.9327 |    0.0730 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     34.2500 |     33.5664 |           0.2912 |           0.2631 |   0.7980 |   0.8041 |            0.7973 |    6.9191 |    6.5761 |      0.0204 |    2.8184 | -0.6104 |    0.0522 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       72308 |     28.0060 |     27.7237 |           0.3299 |           0.3378 |   0.9003 |   0.8996 |            0.9002 |    2.7925 |    2.7824 |      0.0102 |   -0.7954 |  0.0652 |    0.0036 | nan                          |

### playoffs

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |    sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|---------:|----------:|:-----------------------------|
| 5v5           |        3753 |     28.4414 |     25.5728 |           0.3503 |           0.3912 |   0.9111 |   0.9081 |            0.9108 |    2.5292 |    2.3508 |      0.1122 |   -4.0935 |   0.2999 |    0.0759 | nan                          |
| PP            |         730 |     53.7298 |     50.1144 |           0.3180 |           0.3412 |   0.8504 |   0.8315 |            0.8509 |    8.0354 |    8.4439 |      0.0721 |   -2.3143 |   1.8942 |   -0.0484 | UNDERPOWERED (n SOG < 2,000) |
| PK            |         135 |     10.1717 |      9.2677 |           0.2102 |           0.2012 |   0.9103 |   0.9407 |            0.9082 |    0.9129 |    0.5492 |      0.0975 |    0.9005 |  -3.0486 |    0.6622 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |          52 |     25.4387 |     25.2768 |           0.3446 |           0.3067 |   0.8815 |   0.8462 |            0.8832 |    3.0149 |    3.8887 |      0.0064 |    3.7887 |   3.5331 |   -0.2247 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |           0 |     25.3521 |      0.0000 |           0.3889 |         nan      |   0.8182 | nan      |            0.8605 |    4.6095 |    0.0000 |    nan      |  nan      | nan      |  nan      | UNDERPOWERED (n SOG < 2,000) |
| all reachable |        4670 |     28.9542 |     26.2436 |           0.3425 |           0.3787 |   0.9019 |   0.8964 |            0.9017 |    2.8412 |    2.7199 |      0.1033 |   -3.6261 |   0.5514 |    0.0446 | nan                          |

### overall

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       62521 |     27.5797 |     27.0433 |           0.3372 |           0.3482 |   0.9100 |   0.9095 |            0.9099 |    2.4834 |    2.4482 |      0.0198 |   -1.1026 |  0.0484 |    0.0144 | nan                          |
| PP            |       10703 |     51.4369 |     51.4645 |           0.3134 |           0.3234 |   0.8533 |   0.8479 |            0.8533 |    7.5480 |    7.8281 |     -0.0005 |   -1.0032 |  0.5363 |   -0.0358 | nan                          |
| PK            |        2058 |      9.6705 |      9.8957 |           0.2139 |           0.2091 |   0.9075 |   0.9072 |            0.9072 |    0.8941 |    0.9184 |     -0.0228 |    0.4875 |  0.0348 |   -0.0264 | nan                          |
| 4v4           |         864 |     25.5701 |     25.7889 |           0.3327 |           0.3043 |   0.8788 |   0.8854 |            0.8791 |    3.0995 |    2.9550 |     -0.0085 |    2.8355 | -0.6632 |    0.0489 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     34.2485 |     33.5664 |           0.2913 |           0.2631 |   0.7980 |   0.8041 |            0.7973 |    6.9187 |    6.5761 |      0.0203 |    2.8198 | -0.6102 |    0.0521 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       76978 |     28.0656 |     27.6292 |           0.3307 |           0.3405 |   0.9004 |   0.8994 |            0.9003 |    2.7956 |    2.7784 |      0.0158 |   -0.9757 |  0.0953 |    0.0062 | nan                          |

