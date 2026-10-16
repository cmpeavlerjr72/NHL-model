# G3 by strength state + blocked / unblocked per 60, STAND-IN plumbing loop: standins_plumbing_v1, fold 2 (2024-25), 1398 games x 200 seeds

> **STAND-IN / PLUMBING RUN (D32). NOTHING HERE GATES.** Block = B0 STAND-IN (flat: strength group x period type + M1 K500 level); stage 4 = L0s STAND-IN (flat, level E from GameState.rec_era); goals = xG_ref STUB. Team-level and responsiveness readings are against flat stand-ins and are not evidence about any model. G2 4v4 is listed under INV-42 and 3v3 under INV-35 (D26).

Generated 2026-10-16 12:30:51 by `scripts/run_engine_standins_v1.py`. Engine marker: ['attr: STAND-IN (D32): stage-4 L0s (SL-R4) levelled by E from GameState.rec_era; EN rows on the baseline; flat, not adoptable', 'block: STAND-IN (D32): block B0 = SB-R1 B0 (one-hot strength group x period type) + M1 K500 as-of league block-share level; flat, not adoptable']. Stage 1 = H3''-LC2 + T2; stage 3 = A3g-c; block = B0 STAND-IN; stage 4 = L0s STAND-IN (rule (b): unblocked attempts only); goals = xG_ref STUB. No goalie pull (EN UNREACHABLE; actual side restricted to 5v5 / PP / PK / 4v4 / 3v3), shootout skipped. Reference tolerances (not gating): g3_xg_rel 0.03, g3_mix_pp 1.5; cells with n < 300 actual unblocked attempts UNDERPOWERED. PASS / FAIL words below are the gate code's labels, read as REFERENCE only.

Served-vs-offline parity before the seeds: B0 max |dp| 1.49e-08 over 162,300 rows; L0s max |dP| 1.21e-08 over 119,924 rows.

## Attempts, blocked and unblocked attempts per 60 by team-view state (sim vs actual)

att60_act from the stage-3 attempt rows (the G2 source); att60_act_attr_rows from the stage-4 attempt rows (blocked / unblocked source), shown as a consistency check. TOI hours per game are per team.

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6758 |               1.6503 |     58.5533 |     58.3508 |               58.3508 |     17.1459 |     16.8941 |     41.4074 |     41.4566 |          0.2928 |          0.2895 |      36578.0000 |        89759.0000 |      0.0035 |      0.0149 |     -0.0012 |              0.3298 |
| PP      |               0.1513 |               0.1474 |    101.1092 |    101.6226 |              101.6226 |     26.4390 |     25.5582 |     74.6702 |     76.0644 |          0.2615 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0051 |      0.0345 |     -0.0183 |              0.9989 |
| PK      |               0.1513 |               0.1474 |     14.0152 |     14.3173 |               14.3173 |      1.7518 |      1.7373 |     12.2634 |     12.5800 |          0.1250 |          0.1213 |        336.0000 |         2433.0000 |     -0.0211 |      0.0083 |     -0.0252 |              0.3647 |
| 4v4     |               0.0258 |               0.0240 |     50.0961 |     48.6237 |               48.6237 |     14.3833 |     11.5120 |     35.7128 |     37.1118 |          0.2871 |          0.2368 |        362.0000 |         1167.0000 |      0.0303 |      0.2494 |     -0.0377 |              5.0358 |
| 3v3     |               0.0214 |               0.0189 |     59.2866 |     55.2313 |               55.2313 |     12.3353 |      9.6826 |     46.9513 |     45.5487 |          0.2081 |          0.1753 |        240.0000 |         1129.0000 |      0.0734 |      0.2740 |      0.0308 |              3.2751 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.7079 |               1.7065 |     61.1982 |     60.2558 |               60.2558 |     17.6139 |     18.2478 |     43.5843 |     42.0080 |          0.2878 |          0.3028 |       2678.0000 |         6165.0000 |      0.0156 |     -0.0347 |      0.0375 |             -1.5021 |
| PP      |               0.1615 |               0.1694 |    105.2271 |    102.9062 |              102.9062 |     26.5350 |     26.8421 |     78.6922 |     76.0641 |          0.2522 |          0.2608 |        391.0000 |         1108.0000 |      0.0226 |     -0.0114 |      0.0346 |             -0.8672 |
| PK      |               0.1615 |               0.1694 |     14.6038 |     13.3181 |               13.3181 |      1.7783 |      1.7162 |     12.8255 |     11.6018 |          0.1218 |          0.1289 |         25.0000 |          169.0000 |      0.0965 |      0.0362 |      0.1055 |             -0.7094 |
| 4v4     |               0.0267 |               0.0239 |     50.9416 |     51.5258 |               51.5258 |     14.8632 |     15.0689 |     36.0784 |     36.4569 |          0.2918 |          0.2925 |         31.0000 |           75.0000 |     -0.0113 |     -0.0136 |     -0.0104 |             -0.0683 |
| 3v3     |               0.0001 |               0.0000 |     60.5568 |      0.0000 |                0.0000 |     19.8376 |      0.0000 |     40.7193 |      0.0000 |          0.3276 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6778 |               1.6537 |     58.7189 |     58.4717 |               58.4717 |     17.1752 |     16.9801 |     41.5437 |     41.4916 |          0.2925 |          0.2904 |      39256.0000 |        95924.0000 |      0.0042 |      0.0115 |      0.0013 |              0.2101 |
| PP      |               0.1519 |               0.1488 |    101.3786 |    101.7125 |              101.7125 |     26.4453 |     25.6481 |     74.9333 |     76.0644 |          0.2609 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0033 |      0.0311 |     -0.0149 |              0.8694 |
| PK      |               0.1519 |               0.1488 |     14.0537 |     14.2473 |               14.2473 |      1.7535 |      1.7358 |     12.3002 |     12.5115 |          0.1248 |          0.1218 |        361.0000 |         2602.0000 |     -0.0136 |      0.0102 |     -0.0169 |              0.2936 |
| 4v4     |               0.0258 |               0.0240 |     50.1497 |     48.8019 |               48.8019 |     14.4138 |     11.7304 |     35.7360 |     37.0716 |          0.2874 |          0.2404 |        393.0000 |         1242.0000 |      0.0276 |      0.2288 |     -0.0360 |              4.7047 |
| 3v3     |               0.0201 |               0.0177 |     59.2868 |     55.2313 |               55.2313 |     12.3365 |      9.6826 |     46.9502 |     45.5487 |          0.2081 |          0.1753 |        240.0000 |         1129.0000 |      0.0734 |      0.2741 |      0.0308 |              3.2772 |

## G3 regular season

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status   |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:---------|
| 5v5           |                89759 |   0.0600 |   0.0585 |  0.0246 |            0.2928 |            0.2895 |              0.0599 |              0.0592 | PASS     |
| PP            |                14711 |   0.1004 |   0.1009 | -0.0056 |            0.2615 |            0.2515 |              0.1003 |              0.1023 | PASS     |
| PK            |                 2433 |   0.0702 |   0.0690 |  0.0181 |            0.1250 |            0.1213 |              0.0701 |              0.0752 | PASS     |
| 4v4           |                 1167 |   0.0667 |   0.0702 | -0.0504 |            0.2871 |            0.2368 |              0.0670 |              0.0780 | FAIL     |
| 3v3           |                 1129 |   0.0849 |   0.0872 | -0.0269 |            0.2081 |            0.1753 |              0.0852 |              0.1444 | PASS     |
| all reachable |               109199 |   0.0660 |   0.0649 |  0.0164 |            0.2848 |            0.2800 |              0.0659 |              0.0665 | PASS     |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status   |
|:----------------------------|-------:|----------:|----------:|----------:|:---------|
| ('5v5', 'high')             |  89759 |    12.662 |    12.141 |     0.521 | PASS     |
| ('5v5', 'medium')           |  89759 |    38.859 |    39.167 |    -0.308 | PASS     |
| ('5v5', 'low')              |  89759 |    48.479 |    48.691 |    -0.213 | PASS     |
| ('PP', 'high')              |  14711 |    17.361 |    17.069 |     0.293 | PASS     |
| ('PP', 'medium')            |  14711 |    46.661 |    47.685 |    -1.025 | PASS     |
| ('PP', 'low')               |  14711 |    35.978 |    35.246 |     0.732 | PASS     |
| ('PK', 'high')              |   2433 |    13.204 |    12.125 |     1.079 | PASS     |
| ('PK', 'medium')            |   2433 |    36.249 |    37.896 |    -1.646 | FAIL     |
| ('PK', 'low')               |   2433 |    50.547 |    49.979 |     0.567 | PASS     |
| ('4v4', 'high')             |   1167 |    13.260 |    14.567 |    -1.307 | PASS     |
| ('4v4', 'medium')           |   1167 |    48.506 |    54.070 |    -5.565 | FAIL     |
| ('4v4', 'low')              |   1167 |    38.234 |    31.362 |     6.872 | FAIL     |
| ('3v3', 'high')             |   1129 |    18.901 |    15.855 |     3.046 | FAIL     |
| ('3v3', 'medium')           |   1129 |    51.044 |    60.142 |    -9.098 | FAIL     |
| ('3v3', 'low')              |   1129 |    30.055 |    24.004 |     6.052 | FAIL     |
| ('all reachable', 'high')   | 109199 |    13.383 |    12.869 |     0.514 | PASS     |
| ('all reachable', 'medium') | 109199 |    40.095 |    40.662 |    -0.567 | PASS     |
| ('all reachable', 'low')    | 109199 |    46.522 |    46.468 |     0.054 | PASS     |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.087 |    69.250 |    -0.163 |
| slap       |    12.063 |    11.589 |     0.474 |
| backhand   |     7.494 |     7.065 |     0.428 |
| tip+defl   |     9.830 |    10.506 |    -0.675 |
| wrap       |     0.989 |     0.729 |     0.261 |
| other      |     0.537 |     0.862 |    -0.325 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00107; reference tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         +0.00000 |
| attribute mix within state (sim weights)                         |         +0.00107 |

- Reference verdict (regular season; not a gate): CLEAN

## G3 playoffs

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |    rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status       |
|:--------------|---------------------:|---------:|---------:|-------:|------------------:|------------------:|--------------------:|--------------------:|:-------------|
| 5v5           |                 6165 |   0.0600 |   0.0567 | 0.0571 |            0.2878 |            0.3028 |              0.0597 |              0.0560 | FAIL         |
| PP            |                 1108 |   0.1006 |   0.1004 | 0.0011 |            0.2522 |            0.2608 |              0.1001 |              0.1110 | PASS         |
| PK            |                  169 |   0.0699 |   0.0585 | 0.1942 |            0.1218 |            0.1289 |              0.0672 |              0.0473 | UNDERPOWERED |
| 4v4           |                   75 |   0.0673 |   0.0553 | 0.2154 |            0.2918 |            0.2925 |              0.0661 |              0.1067 | UNDERPOWERED |
| all reachable |                 7517 |   0.0660 |   0.0632 | 0.0442 |            0.2799 |            0.2936 |              0.0656 |              0.0644 | FAIL         |

### Location tier shares (%)

|                             |    n |   sim_pct |   act_pct |   diff_pp | status       |
|:----------------------------|-----:|----------:|----------:|----------:|:-------------|
| ('5v5', 'high')             | 6165 |    12.613 |    12.490 |     0.123 | PASS         |
| ('5v5', 'medium')           | 6165 |    38.654 |    36.529 |     2.125 | FAIL         |
| ('5v5', 'low')              | 6165 |    48.733 |    50.981 |    -2.248 | FAIL         |
| ('PP', 'high')              | 1108 |    17.383 |    14.440 |     2.942 | FAIL         |
| ('PP', 'medium')            | 1108 |    46.941 |    46.751 |     0.190 | PASS         |
| ('PP', 'low')               | 1108 |    35.677 |    38.809 |    -3.132 | FAIL         |
| ('PK', 'high')              |  169 |    12.805 |     8.284 |     4.521 | UNDERPOWERED |
| ('PK', 'medium')            |  169 |    36.349 |    33.728 |     2.621 | UNDERPOWERED |
| ('PK', 'low')               |  169 |    50.846 |    57.988 |    -7.142 | UNDERPOWERED |
| ('4v4', 'high')             |   75 |    13.482 |    10.667 |     2.816 | UNDERPOWERED |
| ('4v4', 'medium')           |   75 |    49.051 |    57.333 |    -8.283 | UNDERPOWERED |
| ('4v4', 'low')              |   75 |    37.467 |    32.000 |     5.467 | UNDERPOWERED |
| ('all reachable', 'high')   | 7517 |    13.299 |    12.665 |     0.634 | PASS         |
| ('all reachable', 'medium') | 7517 |    39.880 |    38.180 |     1.700 | FAIL         |
| ('all reachable', 'low')    | 7517 |    46.821 |    49.155 |    -2.334 | FAIL         |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.096 |    66.848 |     2.248 |
| slap       |    12.216 |    11.467 |     0.749 |
| backhand   |     7.436 |     8.208 |    -0.772 |
| tip+defl   |     9.729 |    11.760 |    -2.031 |
| wrap       |     0.980 |     0.785 |     0.196 |
| other      |     0.543 |     0.931 |    -0.389 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00279; reference tolerance 0.00190)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00028 |
| attribute mix within state (sim weights)                         |         +0.00307 |

- Reference verdict (playoffs; not a gate): FAIL

## G3 overall

### xG_ref per unblocked attempt by team-view state

| state         |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   block_share_sim |   block_share_act |   goals_per_fen_sim |   goals_per_fen_act | status   |
|:--------------|---------------------:|---------:|---------:|--------:|------------------:|------------------:|--------------------:|--------------------:|:---------|
| 5v5           |                95924 |   0.0600 |   0.0584 |  0.0266 |            0.2925 |            0.2904 |              0.0599 |              0.0590 | PASS     |
| PP            |                15819 |   0.1004 |   0.1009 | -0.0052 |            0.2609 |            0.2522 |              0.1003 |              0.1029 | PASS     |
| PK            |                 2602 |   0.0702 |   0.0683 |  0.0279 |            0.1248 |            0.1218 |              0.0699 |              0.0734 | PASS     |
| 4v4           |                 1242 |   0.0667 |   0.0693 | -0.0376 |            0.2874 |            0.2404 |              0.0669 |              0.0797 | FAIL     |
| 3v3           |                 1129 |   0.0849 |   0.0872 | -0.0269 |            0.2081 |            0.1753 |              0.0852 |              0.1444 | PASS     |
| all reachable |               116716 |   0.0660 |   0.0648 |  0.0182 |            0.2845 |            0.2809 |              0.0659 |              0.0663 | PASS     |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status   |
|:----------------------------|-------:|----------:|----------:|----------:|:---------|
| ('5v5', 'high')             |  95924 |    12.659 |    12.164 |     0.495 | PASS     |
| ('5v5', 'medium')           |  95924 |    38.846 |    38.998 |    -0.152 | PASS     |
| ('5v5', 'low')              |  95924 |    48.496 |    48.839 |    -0.343 | PASS     |
| ('PP', 'high')              |  15819 |    17.363 |    16.885 |     0.478 | PASS     |
| ('PP', 'medium')            |  15819 |    46.680 |    47.620 |    -0.940 | PASS     |
| ('PP', 'low')               |  15819 |    35.957 |    35.495 |     0.462 | PASS     |
| ('PK', 'high')              |   2602 |    13.177 |    11.875 |     1.302 | PASS     |
| ('PK', 'medium')            |   2602 |    36.256 |    37.625 |    -1.369 | PASS     |
| ('PK', 'low')               |   2602 |    50.567 |    50.500 |     0.067 | PASS     |
| ('4v4', 'high')             |   1242 |    13.275 |    14.332 |    -1.057 | PASS     |
| ('4v4', 'medium')           |   1242 |    48.540 |    54.267 |    -5.727 | FAIL     |
| ('4v4', 'low')              |   1242 |    38.185 |    31.401 |     6.784 | FAIL     |
| ('3v3', 'high')             |   1129 |    18.900 |    15.855 |     3.045 | FAIL     |
| ('3v3', 'medium')           |   1129 |    51.044 |    60.142 |    -9.098 | FAIL     |
| ('3v3', 'low')              |   1129 |    30.057 |    24.004 |     6.053 | FAIL     |
| ('all reachable', 'high')   | 116716 |    13.377 |    12.856 |     0.521 | PASS     |
| ('all reachable', 'medium') | 116716 |    40.081 |    40.503 |    -0.422 | PASS     |
| ('all reachable', 'low')    | 116716 |    46.542 |    46.641 |    -0.100 | PASS     |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.088 |    69.095 |    -0.007 |
| slap       |    12.073 |    11.581 |     0.492 |
| backhand   |     7.490 |     7.139 |     0.351 |
| tip+defl   |     9.824 |    10.586 |    -0.763 |
| wrap       |     0.989 |     0.733 |     0.256 |
| other      |     0.537 |     0.866 |    -0.329 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00118; reference tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00002 |
| attribute mix within state (sim weights)                         |         +0.00119 |

- Reference verdict (overall; not a gate): CLEAN

## Per team, against the FLAT stand-in (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.13). Stage 4 is flat, so team variation in the sim comes only from strength-state and score paths.

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0663 |   0.0675 | -0.0174 |         0.1365 |          -1.4494 |        1.3129 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0655 |   0.0639 |  0.0254 |         0.8643 |           1.4697 |       -2.3340 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0663 |   0.0645 |  0.0272 |         1.1383 |          -2.4334 |        1.2950 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0659 |   0.0671 | -0.0193 |        -0.0374 |          -0.0274 |        0.0648 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0657 |   0.0667 | -0.0152 |         0.1180 |           2.1138 |       -2.2318 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0667 |   0.0661 |  0.0091 |         0.9213 |           0.3808 |       -1.3021 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         7 |                 3386 |   0.0658 |   0.0642 |  0.0237 |         1.6500 |          -5.3902 |        3.7402 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0659 |   0.0671 | -0.0186 |         0.5094 |          -3.7292 |        3.2198 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0662 |   0.0637 |  0.0407 |         1.1376 |          -0.1473 |       -0.9903 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        10 |                 3818 |   0.0662 |   0.0669 | -0.0103 |        -0.5972 |          -1.4230 |        2.0202 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0654 |   0.0635 |  0.0309 |         0.7022 |          -0.7040 |        0.0018 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        13 |                 4813 |   0.0664 |   0.0633 |  0.0490 |         1.0551 |           1.3037 |       -2.3588 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        14 |                 3605 |   0.0664 |   0.0674 | -0.0159 |        -0.5677 |           1.7262 |       -1.1585 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0017 |        -2.5870 |           2.1845 |        0.4025 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0658 |   0.0647 |  0.0172 |         1.3351 |          -1.2599 |       -0.0752 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0668 |   0.0664 |  0.0057 |         1.1960 |          -2.6850 |        1.4891 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0663 |   0.0655 |  0.0130 |         1.3990 |          -2.4741 |        1.0751 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0657 |   0.0645 |  0.0191 |         0.8636 |          -3.6763 |        2.8127 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0660 |   0.0603 |  0.0945 |         1.5633 |          -1.3138 |       -0.2494 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0657 |   0.0643 |  0.0217 |         0.2591 |          -1.0756 |        0.8165 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0655 |   0.0672 | -0.0253 |        -0.2513 |           3.6999 |       -3.4486 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0662 |   0.0636 |  0.0411 |         0.2753 |           1.5353 |       -1.8105 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        24 |                 3372 |   0.0660 |   0.0632 |  0.0434 |         0.7218 |          -2.8146 |        2.0928 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        25 |                 4139 |   0.0659 |   0.0688 | -0.0422 |        -0.7492 |           0.9062 |       -0.1570 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0655 |   0.0624 |  0.0492 |         1.2269 |           0.8121 |       -2.0390 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        28 |                 3172 |   0.0659 |   0.0632 |  0.0429 |         2.0936 |          -1.9015 |       -0.1921 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        29 |                 3395 |   0.0657 |   0.0627 |  0.0484 |         1.1874 |          -0.7055 |       -0.4819 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        30 |                 3531 |   0.0669 |   0.0622 |  0.0742 |         0.3866 |           0.9226 |       -1.3092 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0658 |   0.0647 |  0.0162 |        -0.6186 |           3.8793 |       -3.2608 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0659 |   0.0651 |  0.0119 |        -0.0049 |          -1.2311 |        1.2360 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0656 |   0.0612 |  0.0728 |         1.6087 |          -0.6857 |       -0.9230 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        59 |                 3566 |   0.0656 |   0.0647 |  0.0128 |         1.0254 |          -2.9119 |        1.8865 | UNDERPOWERED (team-level, labelled) | True            | False              |

Responsiveness (D32 slope R) is not computed here: both stand-ins are flat by construction (R undefined / no slope), and the D32 helper is Lane R's.

## Goals (reported; stub goal model): sim goals per game ex-shootout 5.588; actual goals per game in reachable states 5.537 (+ 0.491 in EN states, unreachable in the sim)

