# G3 by strength state + blocked / unblocked per 60, INV-60 plumbing loop: engine_c1s_plumbing_v1, fold 2 (2024-25), 1398 games x 200 seeds

> **PLUMBING RUN (INV-60). NOTHING HERE GATES. ORACLE GOALIE** (the box-score starter faces every shot on goal, D8; no in-game goalie change). Goal = **C1s (provisional, D40)**. STAND-INS: block B0 (own 4v4 / 3v3 groups, INV-54), stage-4 L0s (level M1 K500, INV-57), miss S0t (D37): flat, not adoptable; team-level and responsiveness readings that pass through them are not evidence about any model. Stages 7-8 absent (no rebounds, no goalie pull, no OT / shootout model: OT is the stage-1 engine's 3v3 OT, the shootout a 50 / 50 stub). G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).

Generated 2026-10-21 12:07:49 -0400 by `scripts/run_engine_c1s_v1.py`.

Engine markers: stand_in ['attr: STAND-IN (D32): stage-4 L0s (SL-R4 table) levelled by the M1 K500 as-of mix level (D35, INV-57); EN rows on the baseline; flat, not adoptable', 'block: STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable', 'miss: STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable']; goal_model `goal: C1s (provisional, D40)`; oracle_goalie `ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; no in-game goalie change (stage 8)`.

Served-vs-offline parity before the seeds (max |diff|): l0s 2.98e-08 over 119,924 rows; block 1.49e-08 over 162,300 rows; miss 2.98e-08 over 116,716 rows; goal 1.11e-16 over 76,926 rows.

Reference tolerances (not gating): g3_xg_rel 0.03, g3_mix_pp 1.5; cells with n < 300 actual unblocked attempts UNDERPOWERED. PASS / FAIL words are the gate code's labels, read as REFERENCE only.

## Attempts, blocked and unblocked attempts per 60 by team-view state (sim vs actual)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6757 |               1.6503 |     58.5382 |     58.3508 |               58.3508 |     17.1411 |     16.8941 |     41.3972 |     41.4566 |          0.2928 |          0.2895 |      36578.0000 |        89759.0000 |      0.0032 |      0.0146 |     -0.0014 |              0.3291 |
| PP      |               0.1512 |               0.1474 |    101.0641 |    101.6226 |              101.6226 |     26.4356 |     25.5582 |     74.6285 |     76.0644 |          0.2616 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0055 |      0.0343 |     -0.0189 |              1.0071 |
| PK      |               0.1512 |               0.1474 |     14.0046 |     14.3173 |               14.3173 |      1.7500 |      1.7373 |     12.2547 |     12.5800 |          0.1250 |          0.1213 |        336.0000 |         2433.0000 |     -0.0218 |      0.0073 |     -0.0259 |              0.3613 |
| 4v4     |               0.0258 |               0.0240 |     50.0254 |     48.6237 |               48.6237 |     11.8520 |     11.5120 |     38.1734 |     37.1118 |          0.2369 |          0.2368 |        362.0000 |         1167.0000 |      0.0288 |      0.0295 |      0.0286 |              0.0164 |
| 3v3     |               0.0178 |               0.0189 |     58.2379 |     55.2313 |               55.2313 |      9.9292 |      9.6826 |     48.3088 |     45.5487 |          0.1705 |          0.1753 |        240.0000 |         1129.0000 |      0.0544 |      0.0255 |      0.0606 |             -0.4818 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.7104 |               1.7065 |     61.2496 |     60.2558 |               60.2558 |     17.6226 |     18.2478 |     43.6270 |     42.0080 |          0.2877 |          0.3028 |       2678.0000 |         6165.0000 |      0.0165 |     -0.0343 |      0.0385 |             -1.5121 |
| PP      |               0.1617 |               0.1694 |    105.2684 |    102.9062 |              102.9062 |     26.5858 |     26.8421 |     78.6826 |     76.0641 |          0.2526 |          0.2608 |        391.0000 |         1108.0000 |      0.0230 |     -0.0095 |      0.0344 |             -0.8288 |
| PK      |               0.1617 |               0.1694 |     14.6297 |     13.3181 |               13.3181 |      1.7843 |      1.7162 |     12.8454 |     11.6018 |          0.1220 |          0.1289 |         25.0000 |          169.0000 |      0.0985 |      0.0397 |      0.1072 |             -0.6902 |
| 4v4     |               0.0266 |               0.0239 |     50.9535 |     51.5258 |               51.5258 |     12.1606 |     15.0689 |     38.7929 |     36.4569 |          0.2387 |          0.2925 |         31.0000 |           75.0000 |     -0.0111 |     -0.1930 |      0.0641 |             -5.3792 |
| 3v3     |               0.0001 |               0.0000 |     56.1488 |      0.0000 |                0.0000 |     15.1170 |      0.0000 |     41.0318 |      0.0000 |          0.2692 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6779 |               1.6537 |     58.7083 |     58.4717 |               58.4717 |     17.1713 |     16.9801 |     41.5370 |     41.4916 |          0.2925 |          0.2904 |      39256.0000 |        95924.0000 |      0.0040 |      0.0113 |      0.0011 |              0.2087 |
| PP      |               0.1518 |               0.1488 |    101.3396 |    101.7125 |              101.7125 |     26.4454 |     25.6481 |     74.8941 |     76.0644 |          0.2610 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0037 |      0.0311 |     -0.0154 |              0.8796 |
| PK      |               0.1518 |               0.1488 |     14.0456 |     14.2473 |               14.2473 |      1.7522 |      1.7358 |     12.2934 |     12.5115 |          0.1248 |          0.1218 |        361.0000 |         2602.0000 |     -0.0142 |      0.0094 |     -0.0174 |              0.2916 |
| 4v4     |               0.0258 |               0.0240 |     50.0843 |     48.8019 |               48.8019 |     11.8716 |     11.7304 |     38.2127 |     37.0716 |          0.2370 |          0.2404 |        393.0000 |         1242.0000 |      0.0263 |      0.0120 |      0.0308 |             -0.3335 |
| 3v3     |               0.0167 |               0.0177 |     58.2375 |     55.2313 |               55.2313 |      9.9302 |      9.6826 |     48.3073 |     45.5487 |          0.1705 |          0.1753 |        240.0000 |         1129.0000 |      0.0544 |      0.0256 |      0.0606 |             -0.4799 |

## G3 regular season

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status   |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:---------|
| 5v5           |                89759 |   0.0588 |   0.0585 |  0.0048 |            0.2928 |            0.2895 |              0.0598 |              0.0592 | PASS     |
| PP            |                14711 |   0.1008 |   0.1009 | -0.0011 |            0.2616 |            0.2515 |              0.1006 |              0.1023 | PASS     |
| PK            |                 2433 |   0.0698 |   0.0690 |  0.0122 |            0.1250 |            0.1213 |              0.0725 |              0.0752 | PASS     |
| 4v4           |                 1167 |   0.0658 |   0.0702 | -0.0620 |            0.2369 |            0.2368 |              0.0809 |              0.0780 | FAIL     |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0368 |            0.1705 |            0.1753 |              0.1435 |              0.1444 | FAIL     |
| all reachable |               109199 |   0.0650 |   0.0649 |  0.0018 |            0.2841 |            0.2800 |              0.0666 |              0.0665 | PASS     |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status   |
|:----------------------------|-------:|----------:|----------:|----------:|:---------|
| ('5v5', 'high')             |  89759 |    12.040 |    12.141 |    -0.101 | PASS     |
| ('5v5', 'medium')           |  89759 |    38.844 |    39.167 |    -0.323 | PASS     |
| ('5v5', 'low')              |  89759 |    49.115 |    48.691 |     0.424 | PASS     |
| ('PP', 'high')              |  14711 |    17.044 |    17.069 |    -0.024 | PASS     |
| ('PP', 'medium')            |  14711 |    47.663 |    47.685 |    -0.023 | PASS     |
| ('PP', 'low')               |  14711 |    35.293 |    35.246 |     0.047 | PASS     |
| ('PK', 'high')              |   2433 |    12.645 |    12.125 |     0.520 | PASS     |
| ('PK', 'medium')            |   2433 |    36.999 |    37.896 |    -0.897 | PASS     |
| ('PK', 'low')               |   2433 |    50.356 |    49.979 |     0.377 | PASS     |
| ('4v4', 'high')             |   1167 |    12.705 |    14.567 |    -1.863 | FAIL     |
| ('4v4', 'medium')           |   1167 |    48.802 |    54.070 |    -5.269 | FAIL     |
| ('4v4', 'low')              |   1167 |    38.494 |    31.362 |     7.131 | FAIL     |
| ('3v3', 'high')             |   1129 |    18.221 |    15.855 |     2.366 | FAIL     |
| ('3v3', 'medium')           |   1129 |    51.351 |    60.142 |    -8.791 | FAIL     |
| ('3v3', 'low')              |   1129 |    30.429 |    24.004 |     6.425 | FAIL     |
| ('all reachable', 'high')   | 109199 |    12.794 |    12.869 |    -0.076 | PASS     |
| ('all reachable', 'medium') | 109199 |    40.227 |    40.662 |    -0.436 | PASS     |
| ('all reachable', 'low')    | 109199 |    46.980 |    46.468 |     0.511 | PASS     |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.324 |    69.250 |     0.075 |
| slap       |    12.216 |    11.589 |     0.627 |
| backhand   |     7.351 |     7.065 |     0.285 |
| tip+defl   |     9.650 |    10.506 |    -0.856 |
| wrap       |     0.934 |     0.729 |     0.205 |
| other      |     0.525 |     0.862 |    -0.336 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00011; reference tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00004 |
| attribute mix within state (sim weights)                         |         +0.00015 |

- Reference verdict (regular season; not a gate): CLEAN

## G3 playoffs

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |    rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status       |
|:--------------|---------------------:|---------:|---------:|-------:|------------------:|------------------:|--------------------:|--------------------:|:-------------|
| 5v5           |                 6165 |   0.0590 |   0.0567 | 0.0400 |            0.2877 |            0.3028 |              0.0583 |              0.0560 | FAIL         |
| PP            |                 1108 |   0.1011 |   0.1004 | 0.0061 |            0.2526 |            0.2608 |              0.1018 |              0.1110 | PASS         |
| PK            |                  169 |   0.0685 |   0.0585 | 0.1716 |            0.1220 |            0.1289 |              0.0709 |              0.0473 | UNDERPOWERED |
| 4v4           |                   75 |   0.0665 |   0.0553 | 0.2015 |            0.2387 |            0.2925 |              0.0780 |              0.1067 | UNDERPOWERED |
| all reachable |                 7517 |   0.0652 |   0.0632 | 0.0319 |            0.2793 |            0.2936 |              0.0649 |              0.0644 | FAIL         |

### Location tier shares (%)

|                             |    n |   sim_pct |   act_pct |   diff_pp | status       |
|:----------------------------|-----:|----------:|----------:|----------:|:-------------|
| ('5v5', 'high')             | 6165 |    12.081 |    12.490 |    -0.409 | PASS         |
| ('5v5', 'medium')           | 6165 |    38.937 |    36.529 |     2.408 | FAIL         |
| ('5v5', 'low')              | 6165 |    48.983 |    50.981 |    -1.999 | FAIL         |
| ('PP', 'high')              | 1108 |    16.909 |    14.440 |     2.469 | FAIL         |
| ('PP', 'medium')            | 1108 |    47.920 |    46.751 |     1.169 | PASS         |
| ('PP', 'low')               | 1108 |    35.171 |    38.809 |    -3.638 | FAIL         |
| ('PK', 'high')              |  169 |    12.054 |     8.284 |     3.770 | UNDERPOWERED |
| ('PK', 'medium')            |  169 |    37.811 |    33.728 |     4.084 | UNDERPOWERED |
| ('PK', 'low')               |  169 |    50.134 |    57.988 |    -7.854 | UNDERPOWERED |
| ('4v4', 'high')             |   75 |    13.092 |    10.667 |     2.425 | UNDERPOWERED |
| ('4v4', 'medium')           |   75 |    49.428 |    57.333 |    -7.905 | UNDERPOWERED |
| ('4v4', 'low')              |   75 |    37.480 |    32.000 |     5.480 | UNDERPOWERED |
| ('all reachable', 'high')   | 7517 |    12.771 |    12.665 |     0.106 | PASS         |
| ('all reachable', 'medium') | 7517 |    40.294 |    38.180 |     2.114 | FAIL         |
| ('all reachable', 'low')    | 7517 |    46.935 |    49.155 |    -2.220 | FAIL         |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.393 |    66.848 |     2.544 |
| slap       |    12.386 |    11.467 |     0.919 |
| backhand   |     7.283 |     8.208 |    -0.925 |
| tip+defl   |     9.467 |    11.760 |    -2.293 |
| wrap       |     0.934 |     0.785 |     0.149 |
| other      |     0.536 |     0.931 |    -0.395 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00202; reference tolerance 0.00190)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00030 |
| attribute mix within state (sim weights)                         |         +0.00231 |

- Reference verdict (playoffs; not a gate): FAIL

## G3 overall

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status   |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:---------|
| 5v5           |                95924 |   0.0588 |   0.0584 |  0.0070 |            0.2925 |            0.2904 |              0.0597 |              0.0590 | PASS     |
| PP            |                15819 |   0.1008 |   0.1009 | -0.0006 |            0.2610 |            0.2522 |              0.1007 |              0.1029 | PASS     |
| PK            |                 2602 |   0.0697 |   0.0683 |  0.0210 |            0.1248 |            0.1218 |              0.0724 |              0.0734 | PASS     |
| 4v4           |                 1242 |   0.0659 |   0.0693 | -0.0493 |            0.2370 |            0.2404 |              0.0807 |              0.0797 | FAIL     |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0368 |            0.1705 |            0.1753 |              0.1435 |              0.1444 | FAIL     |
| all reachable |               116716 |   0.0650 |   0.0648 |  0.0037 |            0.2838 |            0.2809 |              0.0665 |              0.0663 | PASS     |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status   |
|:----------------------------|-------:|----------:|----------:|----------:|:---------|
| ('5v5', 'high')             |  95924 |    12.043 |    12.164 |    -0.121 | PASS     |
| ('5v5', 'medium')           |  95924 |    38.850 |    38.998 |    -0.147 | PASS     |
| ('5v5', 'low')              |  95924 |    49.106 |    48.839 |     0.268 | PASS     |
| ('PP', 'high')              |  15819 |    17.035 |    16.885 |     0.150 | PASS     |
| ('PP', 'medium')            |  15819 |    47.680 |    47.620 |     0.060 | PASS     |
| ('PP', 'low')               |  15819 |    35.284 |    35.495 |    -0.211 | PASS     |
| ('PK', 'high')              |   2602 |    12.605 |    11.875 |     0.729 | PASS     |
| ('PK', 'medium')            |   2602 |    37.054 |    37.625 |    -0.570 | PASS     |
| ('PK', 'low')               |   2602 |    50.341 |    50.500 |    -0.159 | PASS     |
| ('4v4', 'high')             |   1242 |    12.730 |    14.332 |    -1.602 | FAIL     |
| ('4v4', 'medium')           |   1242 |    48.842 |    54.267 |    -5.425 | FAIL     |
| ('4v4', 'low')              |   1242 |    38.428 |    31.401 |     7.027 | FAIL     |
| ('3v3', 'high')             |   1129 |    18.220 |    15.855 |     2.365 | FAIL     |
| ('3v3', 'medium')           |   1129 |    51.349 |    60.142 |    -8.793 | FAIL     |
| ('3v3', 'low')              |   1129 |    30.431 |    24.004 |     6.428 | FAIL     |
| ('all reachable', 'high')   | 116716 |    12.792 |    12.856 |    -0.064 | PASS     |
| ('all reachable', 'medium') | 116716 |    40.231 |    40.503 |    -0.271 | PASS     |
| ('all reachable', 'low')    | 116716 |    46.977 |    46.641 |     0.335 | PASS     |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.329 |    69.095 |     0.234 |
| slap       |    12.227 |    11.581 |     0.646 |
| backhand   |     7.346 |     7.139 |     0.207 |
| tip+defl   |     9.638 |    10.586 |    -0.949 |
| wrap       |     0.934 |     0.733 |     0.202 |
| other      |     0.526 |     0.866 |    -0.340 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00024; reference tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00005 |
| attribute mix within state (sim weights)                         |         +0.00029 |

- Reference verdict (overall; not a gate): CLEAN

