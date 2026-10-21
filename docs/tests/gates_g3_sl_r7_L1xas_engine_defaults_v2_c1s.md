# G3 closed loop, SL-R7 L1x-as: engine_defaults_v2_c1s, fold 2 (2024-25), 1398 games x 200 seeds

> **INV-77 closed loop, NEW engine DEFAULT table set** (Lane E4): stage 4 = L1x-as, block = B1a-as (SB-R5), 3v3 OT attempt level ON (EG-R1 part B), goal = C1s (provisional, D40) (ORACLE GOALIE, D8), miss S0t STAND-IN. Pull and shootout flags OFF (no goalie pull, 50/50 shootout stub; no rebounds). G3 gates overall / 5v5 / PP / PK; 4v4 / 3v3 reported. (Report text produced by the SL-R7 grader.)

Generated 2026-10-21 16:02:20 -0400 by `scripts/run_shot_attribute_g3_v4.py grade`.

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
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0370 |            0.1738 |            0.1753 |              0.1426 |              0.1444 | reported (FAIL) |
| all reachable |               109199 |   0.0650 |   0.0649 |  0.0020 |            0.2848 |            0.2800 |              0.0667 |              0.0665 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  89759 |    12.065 |    12.141 |    -0.076 | PASS            |
| ('5v5', 'medium')           |  89759 |    38.797 |    39.167 |    -0.370 | PASS            |
| ('5v5', 'low')              |  89759 |    49.138 |    48.691 |     0.447 | PASS            |
| ('PP', 'high')              |  14711 |    17.058 |    17.069 |    -0.011 | PASS            |
| ('PP', 'medium')            |  14711 |    47.650 |    47.685 |    -0.036 | PASS            |
| ('PP', 'low')               |  14711 |    35.292 |    35.246 |     0.046 | PASS            |
| ('PK', 'high')              |   2433 |    12.705 |    12.125 |     0.580 | PASS            |
| ('PK', 'medium')            |   2433 |    36.955 |    37.896 |    -0.941 | PASS            |
| ('PK', 'low')               |   2433 |    50.340 |    49.979 |     0.361 | PASS            |
| ('4v4', 'high')             |   1167 |    12.797 |    14.567 |    -1.770 | reported (FAIL) |
| ('4v4', 'medium')           |   1167 |    48.728 |    54.070 |    -5.342 | reported (FAIL) |
| ('4v4', 'low')              |   1167 |    38.475 |    31.362 |     7.113 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.186 |    15.855 |     2.331 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.452 |    60.142 |    -8.690 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.362 |    24.004 |     6.358 | reported (FAIL) |
| ('all reachable', 'high')   | 109199 |    12.815 |    12.869 |    -0.054 | PASS            |
| ('all reachable', 'medium') | 109199 |    40.179 |    40.662 |    -0.484 | PASS            |
| ('all reachable', 'low')    | 109199 |    47.006 |    46.468 |     0.538 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.295 |    69.250 |     0.045 |
| slap       |    12.226 |    11.589 |     0.637 |
| backhand   |     7.356 |     7.065 |     0.291 |
| tip+defl   |     9.654 |    10.506 |    -0.852 |
| wrap       |     0.940 |     0.729 |     0.211 |
| other      |     0.530 |     0.862 |    -0.332 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00013; tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00005 |
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
| ('all reachable', 'medium') | 7517 |    40.119 |    38.180 |     1.938 | FAIL                    |
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
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0370 |            0.1738 |            0.1753 |              0.1426 |              0.1444 | reported (FAIL) |
| all reachable |               116716 |   0.0650 |   0.0648 |  0.0036 |            0.2844 |            0.2809 |              0.0665 |              0.0663 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  95924 |    12.057 |    12.164 |    -0.107 | PASS            |
| ('5v5', 'medium')           |  95924 |    38.794 |    38.998 |    -0.203 | PASS            |
| ('5v5', 'low')              |  95924 |    49.149 |    48.839 |     0.310 | PASS            |
| ('PP', 'high')              |  15819 |    17.053 |    16.885 |     0.168 | PASS            |
| ('PP', 'medium')            |  15819 |    47.657 |    47.620 |     0.037 | PASS            |
| ('PP', 'low')               |  15819 |    35.289 |    35.495 |    -0.206 | PASS            |
| ('PK', 'high')              |   2602 |    12.653 |    11.875 |     0.778 | PASS            |
| ('PK', 'medium')            |   2602 |    36.987 |    37.625 |    -0.638 | PASS            |
| ('PK', 'low')               |   2602 |    50.360 |    50.500 |    -0.140 | PASS            |
| ('4v4', 'high')             |   1242 |    12.810 |    14.332 |    -1.522 | reported (FAIL) |
| ('4v4', 'medium')           |   1242 |    48.782 |    54.267 |    -5.485 | reported (FAIL) |
| ('4v4', 'low')              |   1242 |    38.408 |    31.401 |     7.007 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.186 |    15.855 |     2.331 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.449 |    60.142 |    -8.693 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.366 |    24.004 |     6.362 | reported (FAIL) |
| ('all reachable', 'high')   | 116716 |    12.805 |    12.856 |    -0.051 | PASS            |
| ('all reachable', 'medium') | 116716 |    40.175 |    40.503 |    -0.328 | PASS            |
| ('all reachable', 'low')    | 116716 |    47.020 |    46.641 |     0.379 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.293 |    69.095 |     0.198 |
| slap       |    12.236 |    11.581 |     0.655 |
| backhand   |     7.356 |     7.139 |     0.217 |
| tip+defl   |     9.644 |    10.586 |    -0.942 |
| wrap       |     0.940 |     0.733 |     0.207 |
| other      |     0.531 |     0.866 |    -0.335 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00023; tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00006 |
| attribute mix within state (sim weights)                         |         +0.00030 |

- Decomposition verdict (overall): CLEAN

## G3 gate (overall slice; all reachable / 5v5 / PP / PK)

| cell          | check            |   value | status   |
|:--------------|:-----------------|--------:|:---------|
| all reachable | xG per unblocked | +0.0036 | PASS     |
| all reachable | tier high pp     | -0.0513 | PASS     |
| all reachable | tier medium pp   | -0.3277 | PASS     |
| all reachable | tier low pp      | +0.3790 | PASS     |
| 5v5           | xG per unblocked | +0.0069 | PASS     |
| 5v5           | tier high pp     | -0.1069 | PASS     |
| 5v5           | tier medium pp   | -0.2031 | PASS     |
| 5v5           | tier low pp      | +0.3100 | PASS     |
| PP            | xG per unblocked | -0.0002 | PASS     |
| PP            | tier high pp     | +0.1685 | PASS     |
| PP            | tier medium pp   | +0.0373 | PASS     |
| PP            | tier low pp      | -0.2058 | PASS     |
| PK            | xG per unblocked | +0.0224 | PASS     |
| PK            | tier high pp     | +0.7777 | PASS     |
| PK            | tier medium pp   | -0.6376 | PASS     |
| PK            | tier low pp      | -0.1400 | PASS     |

- **G3: PASS**

## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6755 |               1.6503 |     58.5259 |     58.3508 |               58.3508 |     17.1770 |     16.8941 |     41.3489 |     41.4566 |          0.2935 |          0.2895 |      36578.0000 |        89759.0000 |      0.0030 |      0.0167 |     -0.0026 |              0.3967 |
| PP      |               0.1512 |               0.1474 |    101.0280 |    101.6226 |              101.6226 |     26.5250 |     25.5582 |     74.5030 |     76.0644 |          0.2626 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0059 |      0.0378 |     -0.0205 |              1.1050 |
| PK      |               0.1512 |               0.1474 |     14.0037 |     14.3173 |               14.3173 |      1.7476 |      1.7373 |     12.2561 |     12.5800 |          0.1248 |          0.1213 |        336.0000 |         2433.0000 |     -0.0219 |      0.0059 |     -0.0258 |              0.3454 |
| 4v4     |               0.0258 |               0.0240 |     49.9990 |     48.6237 |               48.6237 |     11.8241 |     11.5120 |     38.1749 |     37.1118 |          0.2365 |          0.2368 |        362.0000 |         1167.0000 |      0.0283 |      0.0271 |      0.0286 |             -0.0270 |
| 3v3     |               0.0176 |               0.0189 |     55.5893 |     55.2313 |               55.2313 |      9.6594 |      9.6826 |     45.9299 |     45.5487 |          0.1738 |          0.1753 |        240.0000 |         1129.0000 |      0.0065 |     -0.0024 |      0.0084 |             -0.1546 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.7102 |               1.7065 |     61.2394 |     60.2558 |               60.2558 |     17.5219 |     18.2478 |     43.7174 |     42.0080 |          0.2861 |          0.3028 |       2678.0000 |         6165.0000 |      0.0163 |     -0.0398 |      0.0407 |             -1.6716 |
| PP      |               0.1616 |               0.1694 |    105.2229 |    102.9062 |              102.9062 |     26.5840 |     26.8421 |     78.6388 |     76.0641 |          0.2526 |          0.2608 |        391.0000 |         1108.0000 |      0.0225 |     -0.0096 |      0.0338 |             -0.8195 |
| PK      |               0.1616 |               0.1694 |     14.6467 |     13.3181 |               13.3181 |      1.7820 |      1.7162 |     12.8647 |     11.6018 |          0.1217 |          0.1289 |         25.0000 |          169.0000 |      0.0998 |      0.0383 |      0.1088 |             -0.7200 |
| 4v4     |               0.0266 |               0.0239 |     50.8268 |     51.5258 |               51.5258 |     11.9275 |     15.0689 |     38.8992 |     36.4569 |          0.2347 |          0.2925 |         31.0000 |           75.0000 |     -0.0136 |     -0.2085 |      0.0670 |             -5.7783 |
| 3v3     |               0.0001 |               0.0000 |     51.5854 |      0.0000 |                0.0000 |     13.1707 |      0.0000 |     38.4146 |      0.0000 |          0.2553 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6776 |               1.6537 |     58.6960 |     58.4717 |               58.4717 |     17.1986 |     16.9801 |     41.4974 |     41.4916 |          0.2930 |          0.2904 |      39256.0000 |        95924.0000 |      0.0038 |      0.0129 |      0.0001 |              0.2614 |
| PP      |               0.1519 |               0.1488 |    101.3026 |    101.7125 |              101.7125 |     26.5289 |     25.6481 |     74.7737 |     76.0644 |          0.2619 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0040 |      0.0343 |     -0.0170 |              0.9715 |
| PK      |               0.1519 |               0.1488 |     14.0458 |     14.2473 |               14.2473 |      1.7499 |      1.7358 |     12.2959 |     12.5115 |          0.1246 |          0.1218 |        361.0000 |         2602.0000 |     -0.0141 |      0.0081 |     -0.0172 |              0.2748 |
| 4v4     |               0.0258 |               0.0240 |     50.0515 |     48.8019 |               48.8019 |     11.8306 |     11.7304 |     38.2209 |     37.0716 |          0.2364 |          0.2404 |        393.0000 |         1242.0000 |      0.0256 |      0.0085 |      0.0310 |             -0.3998 |
| 3v3     |               0.0166 |               0.0177 |     55.5885 |     55.2313 |               55.2313 |      9.6601 |      9.6826 |     45.9284 |     45.5487 |          0.1738 |          0.1753 |        240.0000 |         1129.0000 |      0.0065 |     -0.0023 |      0.0083 |             -0.1532 |

## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES rating; 1,000 game bootstrap)

- for: R 1.244 (95% CI 0.947..1.855; UNDERPOWERED), old Q5-Q1 1.216, 2,796 units
- against: R 1.129 (95% CI 0.862..1.661; UNDERPOWERED), old Q5-Q1 1.200, 2,796 units

## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.82; 29/32 within 3%, 13/32 tiers within 1.5 pp)

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0674 |   0.0675 | -0.0017 |         0.2649 |          -1.0744 |        0.8095 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0643 |   0.0639 |  0.0056 |         0.1624 |           1.4771 |       -1.6395 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0658 |   0.0645 |  0.0198 |         0.7019 |          -2.2121 |        1.5102 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0661 |   0.0671 | -0.0151 |        -0.1741 |           0.3042 |       -0.1302 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0660 |   0.0667 | -0.0110 |        -0.0649 |           2.4096 |       -2.3446 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0674 |   0.0661 |  0.0201 |         0.9226 |           0.7258 |       -1.6483 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         7 |                 3386 |   0.0647 |   0.0642 |  0.0068 |         0.9806 |          -5.2939 |        4.3134 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0664 |   0.0671 | -0.0110 |         0.4656 |          -3.3171 |        2.8515 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0637 |   0.0637 |  0.0002 |         0.0549 |          -0.3217 |        0.2668 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        10 |                 3818 |   0.0670 |   0.0669 |  0.0023 |        -0.5359 |          -1.0084 |        1.5443 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0634 |   0.0635 | -0.0015 |        -0.2858 |          -0.7983 |        1.0841 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        13 |                 4813 |   0.0646 |   0.0633 |  0.0195 |         0.1627 |           1.2832 |       -1.4459 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        14 |                 3605 |   0.0662 |   0.0674 | -0.0177 |        -0.9162 |           1.9662 |       -1.0501 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0010 |        -2.8394 |           2.4479 |        0.3915 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0639 |   0.0647 | -0.0124 |         0.4382 |          -1.3256 |        0.8873 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0654 |   0.0664 | -0.0158 |         0.4900 |          -2.7268 |        2.2368 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0652 |   0.0655 | -0.0038 |         0.7764 |          -2.3132 |        1.5368 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0638 |   0.0645 | -0.0104 |         0.0029 |          -3.8176 |        3.8146 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0627 |   0.0603 |  0.0386 |         0.1732 |          -1.6819 |        1.5087 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0655 |   0.0643 |  0.0195 |        -0.0415 |          -0.8500 |        0.8915 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0668 |   0.0672 | -0.0069 |        -0.0714 |           4.0800 |       -4.0086 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0648 |   0.0636 |  0.0190 |        -0.4493 |           1.5364 |       -1.0871 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        24 |                 3372 |   0.0634 |   0.0632 |  0.0026 |        -0.4076 |          -2.9188 |        3.3264 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        25 |                 4139 |   0.0662 |   0.0688 | -0.0375 |        -0.8958 |           1.2430 |       -0.3471 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0633 |   0.0624 |  0.0148 |         0.2575 |           0.6830 |       -0.9405 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        28 |                 3172 |   0.0639 |   0.0632 |  0.0108 |         1.1271 |          -1.9955 |        0.8684 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        29 |                 3395 |   0.0641 |   0.0627 |  0.0236 |         0.3980 |          -0.6746 |        0.2765 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        30 |                 3531 |   0.0657 |   0.0622 |  0.0549 |        -0.2717 |           0.9642 |       -0.6925 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0640 |   0.0647 | -0.0105 |        -1.4500 |           3.8092 |       -2.3593 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0654 |   0.0651 |  0.0051 |        -0.4077 |          -1.0470 |        1.4547 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0630 |   0.0612 |  0.0295 |         0.4454 |          -0.8609 |        0.4155 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        59 |                 3566 |   0.0643 |   0.0647 | -0.0068 |         0.3543 |          -2.9129 |        2.5586 | UNDERPOWERED (team-level, labelled) | True            | False              |

## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)

### regular season

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       58768 |     27.4462 |     27.1429 |           0.3362 |           0.3453 |   0.9098 |   0.9096 |            0.9097 |    2.4762 |    2.4548 |      0.0112 |   -0.9041 |  0.0220 |    0.0087 | nan                          |
| PP            |        9973 |     51.1891 |     51.5662 |           0.3129 |           0.3221 |   0.8534 |   0.8491 |            0.8534 |    7.5033 |    7.7817 |     -0.0073 |   -0.9146 |  0.4327 |   -0.0358 | nan                          |
| PK            |        1923 |      9.6320 |      9.9430 |           0.2141 |           0.2096 |   0.9072 |   0.9048 |            0.9071 |    0.8939 |    0.9462 |     -0.0313 |    0.4484 |  0.2362 |   -0.0553 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |         812 |     25.4862 |     25.8224 |           0.3324 |           0.3042 |   0.8781 |   0.8879 |            0.8785 |    3.1060 |    2.8939 |     -0.0130 |    2.8186 | -0.9801 |    0.0733 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     32.5328 |     33.5664 |           0.2917 |           0.2631 |   0.7986 |   0.8041 |            0.7975 |    6.5507 |    6.5761 |     -0.0308 |    2.8621 | -0.5444 |   -0.0039 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       72308 |     27.9092 |     27.7237 |           0.3299 |           0.3378 |   0.9005 |   0.8996 |            0.9004 |    2.7776 |    2.7824 |      0.0067 |   -0.7885 |  0.0841 |   -0.0017 | nan                          |

### playoffs

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |    sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|---------:|----------:|:-----------------------------|
| 5v5           |        3753 |     28.3977 |     25.5728 |           0.3504 |           0.3912 |   0.9109 |   0.9081 |            0.9107 |    2.5309 |    2.3508 |      0.1105 |   -4.0816 |   0.2804 |    0.0766 | nan                          |
| PP            |         730 |     53.6051 |     50.1144 |           0.3183 |           0.3412 |   0.8505 |   0.8315 |            0.8508 |    8.0122 |    8.4439 |      0.0697 |   -2.2818 |   1.9026 |   -0.0511 | UNDERPOWERED (n SOG < 2,000) |
| PK            |         135 |     10.1669 |      9.2677 |           0.2097 |           0.2012 |   0.9100 |   0.9407 |            0.9080 |    0.9147 |    0.5492 |      0.0970 |    0.8525 |  -3.0714 |    0.6656 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |          52 |     25.4090 |     25.2768 |           0.3468 |           0.3067 |   0.8811 |   0.8462 |            0.8829 |    3.0206 |    3.8887 |      0.0052 |    4.0132 |   3.4966 |   -0.2232 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |           0 |     21.9512 |      0.0000 |           0.4286 |         nan      |   0.8000 | nan      |            0.8583 |    4.3902 |    0.0000 |    nan      |  nan      | nan      |  nan      | UNDERPOWERED (n SOG < 2,000) |
| all reachable |        4670 |     28.9063 |     26.2436 |           0.3427 |           0.3787 |   0.9017 |   0.8964 |            0.9016 |    2.8405 |    2.7199 |      0.1015 |   -3.6088 |   0.5374 |    0.0443 | nan                          |

### overall

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       62521 |     27.5059 |     27.0433 |           0.3372 |           0.3482 |   0.9099 |   0.9095 |            0.9098 |    2.4796 |    2.4482 |      0.0171 |   -1.1057 |  0.0380 |    0.0128 | nan                          |
| PP            |       10703 |     51.3472 |     51.4645 |           0.3133 |           0.3234 |   0.8532 |   0.8479 |            0.8532 |    7.5366 |    7.8281 |     -0.0023 |   -1.0110 |  0.5329 |   -0.0372 | nan                          |
| PK            |        2058 |      9.6670 |      9.8957 |           0.2138 |           0.2091 |   0.9074 |   0.9072 |            0.9071 |    0.8952 |    0.9184 |     -0.0231 |    0.4731 |  0.0201 |   -0.0252 | nan                          |
| 4v4           |         864 |     25.4813 |     25.7889 |           0.3333 |           0.3043 |   0.8783 |   0.8854 |            0.8788 |    3.1006 |    2.9550 |     -0.0119 |    2.8967 | -0.7097 |    0.0493 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     32.5307 |     33.5664 |           0.2917 |           0.2631 |   0.7986 |   0.8041 |            0.7975 |    6.5503 |    6.5761 |     -0.0309 |    2.8644 | -0.5443 |   -0.0039 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       76978 |     27.9716 |     27.6292 |           0.3308 |           0.3405 |   0.9006 |   0.8994 |            0.9005 |    2.7815 |    2.7784 |      0.0124 |   -0.9683 |  0.1121 |    0.0011 | nan                          |

