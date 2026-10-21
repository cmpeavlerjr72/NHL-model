# G3 closed loop, SL-R7 L1x-as: engine_defaults_v2_sap, fold 2 (2024-25), 1398 games x 200 seeds

> **INV-77 closed loop, NEW engine DEFAULT table set** (Lane E4): stage 4 = L1x-as, block = B1a-as (SB-R5), 3v3 OT attempt level ON (EG-R1 part B), goal = C1s-sap (G-R4, sc_game flag) (ORACLE GOALIE, D8), miss S0t STAND-IN. Pull and shootout flags OFF (no goalie pull, 50/50 shootout stub; no rebounds). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)

Generated 2026-10-21 16:02:26 -0400 by `scripts/run_shot_attribute_g3_v4.py grade`.

Engine markers: attr_model `stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)`; stand_in ['miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable']; goal_model `goal: C1s-sap (G-R4: as-of score-bucket deviations H90 P2000 + pooled period interactions)`; oracle_goalie `ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)`.

Served-vs-offline parity before the seeds (max |diff|): l1xas 1.49e-08 over 116,716 rows; block 1.49e-08 over 162,300 rows; miss 2.98e-08 over 116,716 rows; goal 1.11e-16 over 76,926 rows; block_b1aas 1.67e-16 over 162,300 rows; goal_sap 1.11e-16 over 76,926 rows.

Tolerances g3_xg_rel 0.03, g3_mix_pp 1.5; cells with n < 300 actual unblocked attempts UNDERPOWERED. Gated cells: all reachable, 5v5, PP, PK (xG_ref per unblocked attempt and the three tier shares); 4v4 / 3v3 reported.

## regular season

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                89759 |   0.0588 |   0.0585 |  0.0054 |            0.2935 |            0.2895 |              0.0592 |              0.0592 | PASS            |
| PP            |                14711 |   0.1009 |   0.1009 | -0.0006 |            0.2625 |            0.2515 |              0.0997 |              0.1023 | PASS            |
| PK            |                 2433 |   0.0700 |   0.0690 |  0.0141 |            0.1248 |            0.1213 |              0.0723 |              0.0752 | PASS            |
| 4v4           |                 1167 |   0.0660 |   0.0702 | -0.0602 |            0.2364 |            0.2368 |              0.0805 |              0.0780 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0365 |            0.1742 |            0.1753 |              0.1433 |              0.1444 | reported (FAIL) |
| all reachable |               109199 |   0.0650 |   0.0649 |  0.0022 |            0.2848 |            0.2800 |              0.0659 |              0.0665 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  89759 |    12.067 |    12.141 |    -0.074 | PASS            |
| ('5v5', 'medium')           |  89759 |    38.798 |    39.167 |    -0.369 | PASS            |
| ('5v5', 'low')              |  89759 |    49.134 |    48.691 |     0.443 | PASS            |
| ('PP', 'high')              |  14711 |    17.062 |    17.069 |    -0.007 | PASS            |
| ('PP', 'medium')            |  14711 |    47.649 |    47.685 |    -0.037 | PASS            |
| ('PP', 'low')               |  14711 |    35.289 |    35.246 |     0.044 | PASS            |
| ('PK', 'high')              |   2433 |    12.703 |    12.125 |     0.578 | PASS            |
| ('PK', 'medium')            |   2433 |    36.937 |    37.896 |    -0.959 | PASS            |
| ('PK', 'low')               |   2433 |    50.361 |    49.979 |     0.381 | PASS            |
| ('4v4', 'high')             |   1167 |    12.789 |    14.567 |    -1.778 | reported (FAIL) |
| ('4v4', 'medium')           |   1167 |    48.751 |    54.070 |    -5.319 | reported (FAIL) |
| ('4v4', 'low')              |   1167 |    38.460 |    31.362 |     7.098 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.255 |    15.855 |     2.400 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.366 |    60.142 |    -8.776 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.379 |    24.004 |     6.376 | reported (FAIL) |
| ('all reachable', 'high')   | 109199 |    12.816 |    12.869 |    -0.053 | PASS            |
| ('all reachable', 'medium') | 109199 |    40.175 |    40.662 |    -0.487 | PASS            |
| ('all reachable', 'low')    | 109199 |    47.009 |    46.468 |     0.541 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.289 |    69.250 |     0.040 |
| slap       |    12.231 |    11.589 |     0.642 |
| backhand   |     7.354 |     7.065 |     0.289 |
| tip+defl   |     9.655 |    10.506 |    -0.850 |
| wrap       |     0.939 |     0.729 |     0.210 |
| other      |     0.531 |     0.862 |    -0.330 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00014; tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00005 |
| attribute mix within state (sim weights)                         |         +0.00019 |

- Decomposition verdict (regular season): CLEAN

## playoffs

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |    rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status                  |
|:--------------|---------------------:|---------:|---------:|-------:|------------------:|------------------:|--------------------:|--------------------:|:------------------------|
| 5v5           |                 6165 |   0.0586 |   0.0567 | 0.0327 |            0.2862 |            0.3028 |              0.0579 |              0.0560 | FAIL                    |
| PP            |                 1108 |   0.1012 |   0.1004 | 0.0075 |            0.2527 |            0.2608 |              0.1022 |              0.1110 | PASS                    |
| PK            |                  169 |   0.0678 |   0.0585 | 0.1597 |            0.1215 |            0.1289 |              0.0715 |              0.0473 | UNDERPOWERED            |
| 4v4           |                   75 |   0.0663 |   0.0553 | 0.1976 |            0.2348 |            0.2925 |              0.0773 |              0.1067 | reported (UNDERPOWERED) |
| all reachable |                 7517 |   0.0649 |   0.0632 | 0.0263 |            0.2780 |            0.2936 |              0.0647 |              0.0644 | PASS                    |

### Location tier shares (%)

|                             |    n |   sim_pct |   act_pct |   diff_pp | status                  |
|:----------------------------|-----:|----------:|----------:|----------:|:------------------------|
| ('5v5', 'high')             | 6165 |    11.941 |    12.490 |    -0.549 | PASS                    |
| ('5v5', 'medium')           | 6165 |    38.781 |    36.529 |     2.253 | FAIL                    |
| ('5v5', 'low')              | 6165 |    49.278 |    50.981 |    -1.704 | FAIL                    |
| ('PP', 'high')              | 1108 |    16.995 |    14.440 |     2.554 | FAIL                    |
| ('PP', 'medium')            | 1108 |    47.720 |    46.751 |     0.969 | PASS                    |
| ('PP', 'low')               | 1108 |    35.285 |    38.809 |    -3.524 | FAIL                    |
| ('PK', 'high')              |  169 |    11.942 |     8.284 |     3.658 | UNDERPOWERED            |
| ('PK', 'medium')            |  169 |    37.441 |    33.728 |     3.713 | UNDERPOWERED            |
| ('PK', 'low')               |  169 |    50.617 |    57.988 |    -7.371 | UNDERPOWERED            |
| ('4v4', 'high')             |   75 |    13.021 |    10.667 |     2.354 | reported (UNDERPOWERED) |
| ('4v4', 'medium')           |   75 |    49.493 |    57.333 |    -7.841 | reported (UNDERPOWERED) |
| ('4v4', 'low')              |   75 |    37.487 |    32.000 |     5.487 | reported (UNDERPOWERED) |
| ('all reachable', 'high')   | 7517 |    12.662 |    12.665 |    -0.002 | PASS                    |
| ('all reachable', 'medium') | 7517 |    40.127 |    38.180 |     1.947 | FAIL                    |
| ('all reachable', 'low')    | 7517 |    47.211 |    49.155 |    -1.944 | FAIL                    |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.276 |    66.848 |     2.427 |
| slap       |    12.376 |    11.467 |     0.909 |
| backhand   |     7.359 |     8.208 |    -0.849 |
| tip+defl   |     9.500 |    11.760 |    -2.260 |
| wrap       |     0.945 |     0.785 |     0.160 |
| other      |     0.544 |     0.931 |    -0.387 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00166; tolerance 0.00190)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00032 |
| attribute mix within state (sim weights)                         |         +0.00197 |

- Decomposition verdict (playoffs): COMPENSATED

## overall

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status          |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:----------------|
| 5v5           |                95924 |   0.0588 |   0.0584 |  0.0071 |            0.2930 |            0.2904 |              0.0591 |              0.0590 | PASS            |
| PP            |                15819 |   0.1009 |   0.1009 | -0.0001 |            0.2618 |            0.2522 |              0.0999 |              0.1029 | PASS            |
| PK            |                 2602 |   0.0698 |   0.0683 |  0.0221 |            0.1246 |            0.1218 |              0.0722 |              0.0734 | PASS            |
| 4v4           |                 1242 |   0.0660 |   0.0693 | -0.0478 |            0.2363 |            0.2404 |              0.0803 |              0.0797 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0366 |            0.1742 |            0.1753 |              0.1433 |              0.1444 | reported (FAIL) |
| all reachable |               116716 |   0.0650 |   0.0648 |  0.0037 |            0.2844 |            0.2809 |              0.0658 |              0.0663 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  95924 |    12.059 |    12.164 |    -0.105 | PASS            |
| ('5v5', 'medium')           |  95924 |    38.797 |    38.998 |    -0.200 | PASS            |
| ('5v5', 'low')              |  95924 |    49.144 |    48.839 |     0.305 | PASS            |
| ('PP', 'high')              |  15819 |    17.057 |    16.885 |     0.172 | PASS            |
| ('PP', 'medium')            |  15819 |    47.654 |    47.620 |     0.034 | PASS            |
| ('PP', 'low')               |  15819 |    35.289 |    35.495 |    -0.206 | PASS            |
| ('PK', 'high')              |   2602 |    12.651 |    11.875 |     0.775 | PASS            |
| ('PK', 'medium')            |   2602 |    36.971 |    37.625 |    -0.654 | PASS            |
| ('PK', 'low')               |   2602 |    50.378 |    50.500 |    -0.121 | PASS            |
| ('4v4', 'high')             |   1242 |    12.804 |    14.332 |    -1.528 | reported (FAIL) |
| ('4v4', 'medium')           |   1242 |    48.799 |    54.267 |    -5.468 | reported (FAIL) |
| ('4v4', 'low')              |   1242 |    38.397 |    31.401 |     6.996 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.254 |    15.855 |     2.400 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.363 |    60.142 |    -8.779 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.383 |    24.004 |     6.379 | reported (FAIL) |
| ('all reachable', 'high')   | 116716 |    12.806 |    12.856 |    -0.050 | PASS            |
| ('all reachable', 'medium') | 116716 |    40.172 |    40.503 |    -0.331 | PASS            |
| ('all reachable', 'low')    | 116716 |    47.022 |    46.641 |     0.381 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.288 |    69.095 |     0.193 |
| slap       |    12.241 |    11.581 |     0.660 |
| backhand   |     7.354 |     7.139 |     0.215 |
| tip+defl   |     9.645 |    10.586 |    -0.941 |
| wrap       |     0.940 |     0.733 |     0.207 |
| other      |     0.532 |     0.866 |    -0.334 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00024; tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00007 |
| attribute mix within state (sim weights)                         |         +0.00031 |

- Decomposition verdict (overall): CLEAN

## G3 gate (overall slice; all reachable / 5v5 / PP / PK)

| cell          | check            |   value | status   |
|:--------------|:-----------------|--------:|:---------|
| all reachable | xG per unblocked | +0.0037 | PASS     |
| all reachable | tier high pp     | -0.0502 | PASS     |
| all reachable | tier medium pp   | -0.3306 | PASS     |
| all reachable | tier low pp      | +0.3808 | PASS     |
| 5v5           | xG per unblocked | +0.0071 | PASS     |
| 5v5           | tier high pp     | -0.1050 | PASS     |
| 5v5           | tier medium pp   | -0.2003 | PASS     |
| 5v5           | tier low pp      | +0.3052 | PASS     |
| PP            | xG per unblocked | -0.0001 | PASS     |
| PP            | tier high pp     | +0.1725 | PASS     |
| PP            | tier medium pp   | +0.0338 | PASS     |
| PP            | tier low pp      | -0.2062 | PASS     |
| PK            | xG per unblocked | +0.0221 | PASS     |
| PK            | tier high pp     | +0.7753 | PASS     |
| PK            | tier medium pp   | -0.6539 | PASS     |
| PK            | tier low pp      | -0.1214 | PASS     |

- **G3: PASS**

## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6750 |               1.6503 |     58.5235 |     58.3508 |               58.3508 |     17.1745 |     16.8941 |     41.3490 |     41.4566 |          0.2935 |          0.2895 |      36578.0000 |        89759.0000 |      0.0030 |      0.0166 |     -0.0026 |              0.3937 |
| PP      |               0.1514 |               0.1474 |    101.0188 |    101.6226 |              101.6226 |     26.5170 |     25.5582 |     74.5018 |     76.0644 |          0.2625 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0059 |      0.0375 |     -0.0205 |              1.0994 |
| PK      |               0.1514 |               0.1474 |     14.0002 |     14.3173 |               14.3173 |      1.7474 |      1.7373 |     12.2528 |     12.5800 |          0.1248 |          0.1213 |        336.0000 |         2433.0000 |     -0.0221 |      0.0058 |     -0.0260 |              0.3470 |
| 4v4     |               0.0258 |               0.0240 |     49.9513 |     48.6237 |               48.6237 |     11.8099 |     11.5120 |     38.1413 |     37.1118 |          0.2364 |          0.2368 |        362.0000 |         1167.0000 |      0.0273 |      0.0259 |      0.0277 |             -0.0327 |
| 3v3     |               0.0168 |               0.0189 |     55.5084 |     55.2313 |               55.2313 |      9.6701 |      9.6826 |     45.8383 |     45.5487 |          0.1742 |          0.1753 |        240.0000 |         1129.0000 |      0.0050 |     -0.0013 |      0.0064 |             -0.1101 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.7085 |               1.7065 |     61.2436 |     60.2558 |               60.2558 |     17.5269 |     18.2478 |     43.7167 |     42.0080 |          0.2862 |          0.3028 |       2678.0000 |         6165.0000 |      0.0164 |     -0.0395 |      0.0407 |             -1.6655 |
| PP      |               0.1615 |               0.1694 |    105.1399 |    102.9062 |              102.9062 |     26.5708 |     26.8421 |     78.5691 |     76.0641 |          0.2527 |          0.2608 |        391.0000 |         1108.0000 |      0.0217 |     -0.0101 |      0.0329 |             -0.8122 |
| PK      |               0.1615 |               0.1694 |     14.6482 |     13.3181 |               13.3181 |      1.7804 |      1.7162 |     12.8678 |     11.6018 |          0.1215 |          0.1289 |         25.0000 |          169.0000 |      0.0999 |      0.0374 |      0.1091 |             -0.7322 |
| 4v4     |               0.0267 |               0.0239 |     50.8591 |     51.5258 |               51.5258 |     11.9426 |     15.0689 |     38.9165 |     36.4569 |          0.2348 |          0.2925 |         31.0000 |           75.0000 |     -0.0129 |     -0.2075 |      0.0675 |             -5.7636 |
| 3v3     |               0.0001 |               0.0000 |     51.6393 |      0.0000 |                0.0000 |     12.6464 |      0.0000 |     38.9930 |      0.0000 |          0.2449 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6771 |               1.6537 |     58.6940 |     58.4717 |               58.4717 |     17.1966 |     16.9801 |     41.4974 |     41.4916 |          0.2930 |          0.2904 |      39256.0000 |        95924.0000 |      0.0038 |      0.0128 |      0.0001 |              0.2590 |
| PP      |               0.1520 |               0.1488 |    101.2881 |    101.7125 |              101.7125 |     26.5205 |     25.6481 |     74.7676 |     76.0644 |          0.2618 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0042 |      0.0340 |     -0.0170 |              0.9669 |
| PK      |               0.1520 |               0.1488 |     14.0426 |     14.2473 |               14.2473 |      1.7496 |      1.7358 |     12.2930 |     12.5115 |          0.1246 |          0.1218 |        361.0000 |         2602.0000 |     -0.0144 |      0.0079 |     -0.0175 |              0.2755 |
| 4v4     |               0.0258 |               0.0240 |     50.0089 |     48.8019 |               48.8019 |     11.8184 |     11.7304 |     38.1906 |     37.0716 |          0.2363 |          0.2404 |        393.0000 |         1242.0000 |      0.0247 |      0.0075 |      0.0302 |             -0.4042 |
| 3v3     |               0.0158 |               0.0177 |     55.5076 |     55.2313 |               55.2313 |      9.6707 |      9.6826 |     45.8369 |     45.5487 |          0.1742 |          0.1753 |        240.0000 |         1129.0000 |      0.0050 |     -0.0012 |      0.0063 |             -0.1087 |

## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES rating; 1,000 game bootstrap)

- for: R 1.245 (95% CI 0.947..1.852; UNDERPOWERED), old Q5-Q1 1.215, 2,796 units
- against: R 1.131 (95% CI 0.863..1.663; UNDERPOWERED), old Q5-Q1 1.201, 2,796 units

## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.82; 29/32 within 3%, 13/32 tiers within 1.5 pp)

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0674 |   0.0675 | -0.0015 |         0.2612 |          -1.0697 |        0.8085 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0643 |   0.0639 |  0.0057 |         0.1581 |           1.4833 |       -1.6414 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0658 |   0.0645 |  0.0199 |         0.7047 |          -2.2190 |        1.5143 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0661 |   0.0671 | -0.0152 |        -0.1703 |           0.2825 |       -0.1122 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0660 |   0.0667 | -0.0109 |        -0.0610 |           2.4017 |       -2.3408 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0674 |   0.0661 |  0.0200 |         0.9212 |           0.7211 |       -1.6423 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         7 |                 3386 |   0.0647 |   0.0642 |  0.0069 |         0.9905 |          -5.3021 |        4.3116 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0664 |   0.0671 | -0.0109 |         0.4674 |          -3.3149 |        2.8475 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0637 |   0.0637 |  0.0005 |         0.0589 |          -0.3185 |        0.2595 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        10 |                 3818 |   0.0670 |   0.0669 |  0.0023 |        -0.5326 |          -1.0133 |        1.5459 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0634 |   0.0635 | -0.0013 |        -0.2880 |          -0.7959 |        1.0839 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        13 |                 4813 |   0.0646 |   0.0633 |  0.0195 |         0.1643 |           1.2750 |       -1.4393 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        14 |                 3605 |   0.0662 |   0.0674 | -0.0177 |        -0.9171 |           1.9604 |       -1.0433 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0011 |        -2.8273 |           2.4417 |        0.3857 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0639 |   0.0647 | -0.0123 |         0.4349 |          -1.3236 |        0.8887 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0654 |   0.0664 | -0.0156 |         0.4920 |          -2.7329 |        2.2409 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0652 |   0.0655 | -0.0038 |         0.7705 |          -2.3114 |        1.5409 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0638 |   0.0645 | -0.0101 |         0.0063 |          -3.8163 |        3.8100 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0627 |   0.0603 |  0.0388 |         0.1708 |          -1.6769 |        1.5060 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0655 |   0.0643 |  0.0198 |        -0.0421 |          -0.8550 |        0.8971 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0668 |   0.0672 | -0.0069 |        -0.0673 |           4.0798 |       -4.0126 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0648 |   0.0636 |  0.0193 |        -0.4466 |           1.5449 |       -1.0983 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        24 |                 3372 |   0.0634 |   0.0632 |  0.0027 |        -0.4133 |          -2.9265 |        3.3399 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        25 |                 4139 |   0.0662 |   0.0688 | -0.0373 |        -0.8968 |           1.2409 |       -0.3441 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0633 |   0.0624 |  0.0149 |         0.2550 |           0.6750 |       -0.9300 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        28 |                 3172 |   0.0639 |   0.0632 |  0.0108 |         1.1291 |          -1.9976 |        0.8685 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        29 |                 3395 |   0.0642 |   0.0627 |  0.0238 |         0.3976 |          -0.6794 |        0.2818 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        30 |                 3531 |   0.0657 |   0.0622 |  0.0552 |        -0.2718 |           0.9781 |       -0.7063 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0640 |   0.0647 | -0.0104 |        -1.4523 |           3.8019 |       -2.3496 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0654 |   0.0651 |  0.0054 |        -0.3987 |          -1.0481 |        1.4469 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0630 |   0.0612 |  0.0294 |         0.4394 |          -0.8714 |        0.4321 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        59 |                 3566 |   0.0643 |   0.0647 | -0.0068 |         0.3605 |          -2.9253 |        2.5648 | UNDERPOWERED (team-level, labelled) | True            | False              |

## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)

### regular season

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       58768 |     27.4475 |     27.1429 |           0.3362 |           0.3453 |   0.9109 |   0.9096 |            0.9109 |    2.4459 |    2.4548 |      0.0112 |   -0.9069 |  0.1329 |   -0.0036 | nan                          |
| PP            |        9973 |     51.1935 |     51.5662 |           0.3129 |           0.3221 |   0.8549 |   0.8491 |            0.8548 |    7.4288 |    7.7817 |     -0.0072 |   -0.9216 |  0.5796 |   -0.0454 | nan                          |
| PK            |        1923 |      9.6287 |      9.9430 |           0.2142 |           0.2096 |   0.9080 |   0.9048 |            0.9079 |    0.8858 |    0.9462 |     -0.0316 |    0.4543 |  0.3164 |   -0.0638 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |         812 |     25.4566 |     25.8224 |           0.3326 |           0.3042 |   0.8794 |   0.8879 |            0.8796 |    3.0710 |    2.8939 |     -0.0142 |    2.8373 | -0.8569 |    0.0612 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     32.4703 |     33.5664 |           0.2916 |           0.2631 |   0.7977 |   0.8041 |            0.7973 |    6.5686 |    6.5761 |     -0.0327 |    2.8569 | -0.6381 |   -0.0011 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       72308 |     27.9081 |     27.7237 |           0.3299 |           0.3378 |   0.9017 |   0.8996 |            0.9016 |    2.7447 |    2.7824 |      0.0067 |   -0.7904 |  0.2014 |   -0.0136 | nan                          |

### playoffs

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |    sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|---------:|----------:|:-----------------------------|
| 5v5           |        3753 |     28.3953 |     25.5728 |           0.3505 |           0.3912 |   0.9108 |   0.9081 |            0.9106 |    2.5331 |    2.3508 |      0.1104 |   -4.0771 |   0.2719 |    0.0775 | nan                          |
| PP            |         730 |     53.5822 |     50.1144 |           0.3180 |           0.3412 |   0.8501 |   0.8315 |            0.8504 |    8.0331 |    8.4439 |      0.0692 |   -2.3130 |   1.8572 |   -0.0487 | UNDERPOWERED (n SOG < 2,000) |
| PK            |         135 |     10.1702 |      9.2677 |           0.2096 |           0.2012 |   0.9096 |   0.9407 |            0.9076 |    0.9197 |    0.5492 |      0.0974 |    0.8457 |  -3.1174 |    0.6747 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |          52 |     25.3794 |     25.2768 |           0.3479 |           0.3067 |   0.8814 |   0.8462 |            0.8823 |    3.0102 |    3.8887 |      0.0041 |    4.1184 |   3.5239 |   -0.2259 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |           0 |     21.0773 |      0.0000 |           0.4595 |         nan      |   0.8000 | nan      |            0.8552 |    4.2155 |    0.0000 |    nan      |  nan      | nan      |  nan      | UNDERPOWERED (n SOG < 2,000) |
| all reachable |        4670 |     28.9024 |     26.2436 |           0.3427 |           0.3787 |   0.9016 |   0.8964 |            0.9014 |    2.8443 |    2.7199 |      0.1013 |   -3.6082 |   0.5230 |    0.0457 | nan                          |

### overall

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       62521 |     27.5069 |     27.0433 |           0.3371 |           0.3482 |   0.9109 |   0.9095 |            0.9108 |    2.4513 |    2.4482 |      0.0171 |   -1.1082 |  0.1412 |    0.0013 | nan                          |
| PP            |       10703 |     51.3496 |     51.4645 |           0.3132 |           0.3234 |   0.8546 |   0.8479 |            0.8545 |    7.4683 |    7.8281 |     -0.0022 |   -1.0198 |  0.6667 |   -0.0460 | nan                          |
| PK            |        2058 |      9.6641 |      9.8957 |           0.2139 |           0.2091 |   0.9081 |   0.9072 |            0.9079 |    0.8881 |    0.9184 |     -0.0234 |    0.4781 |  0.0917 |   -0.0330 | nan                          |
| 4v4           |         864 |     25.4517 |     25.7889 |           0.3336 |           0.3043 |   0.8795 |   0.8854 |            0.8797 |    3.0672 |    2.9550 |     -0.0131 |    2.9213 | -0.5926 |    0.0380 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     32.4679 |     33.5664 |           0.2917 |           0.2631 |   0.7977 |   0.8041 |            0.7973 |    6.5681 |    6.5761 |     -0.0327 |    2.8600 | -0.6381 |   -0.0012 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       76978 |     27.9703 |     27.6292 |           0.3308 |           0.3405 |   0.9016 |   0.8994 |            0.9016 |    2.7509 |    2.7784 |      0.0123 |   -0.9700 |  0.2209 |   -0.0099 | nan                          |

