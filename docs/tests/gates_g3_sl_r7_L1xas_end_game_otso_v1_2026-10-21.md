# G3 closed loop, SL-R7 L1x-as: end_game_otso_v1, fold 2 (2024-25), 1398 games x 200 seeds

> **EG-R1 closed loop (Lane H8b, on Lane H8a's pull).** Engine default set (D43 / INV-63): L1x-as, C1s ORACLE GOALIE, STAND-INS block B0 / miss S0t; goalie pull P1 + EN cascade (EN attempt and EN goal levels STAND-IN); 3v3 OT attempt level = own as-of M1 K500 (served A3g-c re-levelled); shootout = S1 (rules mechanics, as-of success and home-first share). No delayed-penalty state (INV-70); no rebounds / faceoffs (stage 7 absent). Report text produced by the SL-R7 grader.

Generated 2026-10-21 14:56:08 -0400 by `scripts/run_shot_attribute_g3_v4.py grade`.

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
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0365 |            0.1700 |            0.1753 |              0.1430 |              0.1444 | reported (FAIL) |
| all reachable |               109199 |   0.0651 |   0.0649 |  0.0026 |            0.2839 |            0.2800 |              0.0668 |              0.0665 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  89759 |    12.058 |    12.141 |    -0.083 | PASS            |
| ('5v5', 'medium')           |  89759 |    38.790 |    39.167 |    -0.377 | PASS            |
| ('5v5', 'low')              |  89759 |    49.151 |    48.691 |     0.460 | PASS            |
| ('PP', 'high')              |  14711 |    17.041 |    17.069 |    -0.028 | PASS            |
| ('PP', 'medium')            |  14711 |    47.672 |    47.685 |    -0.014 | PASS            |
| ('PP', 'low')               |  14711 |    35.287 |    35.246 |     0.041 | PASS            |
| ('PK', 'high')              |   2433 |    12.695 |    12.125 |     0.570 | PASS            |
| ('PK', 'medium')            |   2433 |    36.959 |    37.896 |    -0.936 | PASS            |
| ('PK', 'low')               |   2433 |    50.345 |    49.979 |     0.366 | PASS            |
| ('4v4', 'high')             |   1167 |    12.765 |    14.567 |    -1.802 | reported (FAIL) |
| ('4v4', 'medium')           |   1167 |    48.576 |    54.070 |    -5.494 | reported (FAIL) |
| ('4v4', 'low')              |   1167 |    38.658 |    31.362 |     7.296 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.219 |    15.855 |     2.364 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.422 |    60.142 |    -8.719 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.359 |    24.004 |     6.355 | reported (FAIL) |
| ('all reachable', 'high')   | 109199 |    12.820 |    12.869 |    -0.049 | PASS            |
| ('all reachable', 'medium') | 109199 |    40.202 |    40.662 |    -0.460 | PASS            |
| ('all reachable', 'low')    | 109199 |    46.978 |    46.468 |     0.509 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.303 |    69.250 |     0.053 |
| slap       |    12.220 |    11.589 |     0.631 |
| backhand   |     7.360 |     7.065 |     0.295 |
| tip+defl   |     9.646 |    10.506 |    -0.859 |
| wrap       |     0.940 |     0.729 |     0.211 |
| other      |     0.530 |     0.862 |    -0.331 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00017; tolerance 0.00195)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         +0.00002 |
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
| PK            |                 2602 |   0.0698 |   0.0683 |  0.0217 |            0.1248 |            0.1218 |              0.0727 |              0.0734 | PASS            |
| 4v4           |                 1242 |   0.0659 |   0.0693 | -0.0493 |            0.2372 |            0.2404 |              0.0809 |              0.0797 | reported (FAIL) |
| 3v3           |                 1129 |   0.0840 |   0.0872 | -0.0365 |            0.1700 |            0.1753 |              0.1430 |              0.1444 | reported (FAIL) |
| all reachable |               116716 |   0.0651 |   0.0648 |  0.0041 |            0.2836 |            0.2809 |              0.0666 |              0.0663 | PASS            |

### Location tier shares (%)

|                             |      n |   sim_pct |   act_pct |   diff_pp | status          |
|:----------------------------|-------:|----------:|----------:|----------:|:----------------|
| ('5v5', 'high')             |  95924 |    12.050 |    12.164 |    -0.114 | PASS            |
| ('5v5', 'medium')           |  95924 |    38.786 |    38.998 |    -0.211 | PASS            |
| ('5v5', 'low')              |  95924 |    49.163 |    48.839 |     0.325 | PASS            |
| ('PP', 'high')              |  15819 |    17.036 |    16.885 |     0.151 | PASS            |
| ('PP', 'medium')            |  15819 |    47.682 |    47.620 |     0.062 | PASS            |
| ('PP', 'low')               |  15819 |    35.282 |    35.495 |    -0.214 | PASS            |
| ('PK', 'high')              |   2602 |    12.637 |    11.875 |     0.762 | PASS            |
| ('PK', 'medium')            |   2602 |    36.995 |    37.625 |    -0.630 | PASS            |
| ('PK', 'low')               |   2602 |    50.368 |    50.500 |    -0.132 | PASS            |
| ('4v4', 'high')             |   1242 |    12.779 |    14.332 |    -1.553 | reported (FAIL) |
| ('4v4', 'medium')           |   1242 |    48.629 |    54.267 |    -5.638 | reported (FAIL) |
| ('4v4', 'low')              |   1242 |    38.592 |    31.401 |     7.191 | reported (FAIL) |
| ('3v3', 'high')             |   1129 |    18.218 |    15.855 |     2.364 | reported (FAIL) |
| ('3v3', 'medium')           |   1129 |    51.420 |    60.142 |    -8.722 | reported (FAIL) |
| ('3v3', 'low')              |   1129 |    30.362 |    24.004 |     6.358 | reported (FAIL) |
| ('all reachable', 'high')   | 116716 |    12.809 |    12.856 |    -0.047 | PASS            |
| ('all reachable', 'medium') | 116716 |    40.196 |    40.503 |    -0.307 | PASS            |
| ('all reachable', 'low')    | 116716 |    46.995 |    46.641 |     0.354 | PASS            |

### Type shares (%), reported

| type       |   sim_pct |   act_pct |   diff_pp |
|:-----------|----------:|----------:|----------:|
| wrist+snap |    69.301 |    69.095 |     0.206 |
| slap       |    12.233 |    11.581 |     0.652 |
| backhand   |     7.360 |     7.139 |     0.221 |
| tip+defl   |     9.634 |    10.586 |    -0.952 |
| wrap       |     0.940 |     0.733 |     0.208 |
| other      |     0.531 |     0.866 |    -0.335 |

### Decomposition of xG per unblocked attempt (sim - actual +0.00026; tolerance 0.00194)

|                                                                  |   xG per attempt |
|:-----------------------------------------------------------------|-----------------:|
| state visits (sim - actual unblocked share by state) x actual xG |         -0.00000 |
| attribute mix within state (sim weights)                         |         +0.00026 |

- Decomposition verdict (overall): CLEAN

## G3 gate (overall slice; all reachable / 5v5 / PP / PK)

| cell          | check            |   value | status   |
|:--------------|:-----------------|--------:|:---------|
| all reachable | xG per unblocked | +0.0041 | PASS     |
| all reachable | tier high pp     | -0.0470 | PASS     |
| all reachable | tier medium pp   | -0.3071 | PASS     |
| all reachable | tier low pp      | +0.3541 | PASS     |
| 5v5           | xG per unblocked | +0.0065 | PASS     |
| 5v5           | tier high pp     | -0.1136 | PASS     |
| 5v5           | tier medium pp   | -0.2112 | PASS     |
| 5v5           | tier low pp      | +0.3248 | PASS     |
| PP            | xG per unblocked | -0.0003 | PASS     |
| PP            | tier high pp     | +0.1512 | PASS     |
| PP            | tier medium pp   | +0.0624 | PASS     |
| PP            | tier low pp      | -0.2136 | PASS     |
| PK            | xG per unblocked | +0.0217 | PASS     |
| PK            | tier high pp     | +0.7618 | PASS     |
| PK            | tier medium pp   | -0.6301 | PASS     |
| PK            | tier low pp      | -0.1317 | PASS     |

- **G3: PASS**

## Attempts, blocked and unblocked attempts per 60 by team-view state (reported)

### regular season

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6437 |               1.6503 |     58.6344 |     58.3508 |               58.3508 |     17.1695 |     16.8941 |     41.4649 |     41.4566 |          0.2928 |          0.2895 |      36578.0000 |        89759.0000 |      0.0049 |      0.0163 |      0.0002 |              0.3295 |
| PP      |               0.1492 |               0.1474 |    101.0883 |    101.6226 |              101.6226 |     26.4437 |     25.5582 |     74.6446 |     76.0644 |          0.2616 |          0.2515 |       4943.0000 |        14711.0000 |     -0.0053 |      0.0346 |     -0.0187 |              1.0089 |
| PK      |               0.1492 |               0.1474 |     14.0149 |     14.3173 |               14.3173 |      1.7526 |      1.7373 |     12.2623 |     12.5800 |          0.1251 |          0.1213 |        336.0000 |         2433.0000 |     -0.0211 |      0.0088 |     -0.0253 |              0.3711 |
| 4v4     |               0.0256 |               0.0240 |     50.1883 |     48.6237 |               48.6237 |     11.8988 |     11.5120 |     38.2895 |     37.1118 |          0.2371 |          0.2368 |        362.0000 |         1167.0000 |      0.0322 |      0.0336 |      0.0317 |              0.0327 |
| 3v3     |               0.0208 |               0.0189 |     55.5884 |     55.2313 |               55.2313 |      9.4506 |      9.6826 |     46.1378 |     45.5487 |          0.1700 |          0.1753 |        240.0000 |         1129.0000 |      0.0065 |     -0.0240 |      0.0129 |             -0.5300 |

### playoffs

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6884 |               1.7065 |     61.4104 |     60.2558 |               60.2558 |     17.6339 |     18.2478 |     43.7765 |     42.0080 |          0.2871 |          0.3028 |       2678.0000 |         6165.0000 |      0.0192 |     -0.0336 |      0.0421 |             -1.5690 |
| PP      |               0.1599 |               0.1694 |    105.4092 |    102.9062 |              102.9062 |     26.6251 |     26.8421 |     78.7841 |     76.0641 |          0.2526 |          0.2608 |        391.0000 |         1108.0000 |      0.0243 |     -0.0081 |      0.0358 |             -0.8253 |
| PK      |               0.1599 |               0.1694 |     14.6644 |     13.3181 |               13.3181 |      1.7857 |      1.7162 |     12.8786 |     11.6018 |          0.1218 |          0.1289 |         25.0000 |          169.0000 |      0.1011 |      0.0405 |      0.1101 |             -0.7093 |
| 4v4     |               0.0262 |               0.0239 |     50.9552 |     51.5258 |               51.5258 |     12.1439 |     15.0689 |     38.8112 |     36.4569 |          0.2383 |          0.2925 |         31.0000 |           75.0000 |     -0.0111 |     -0.1941 |      0.0646 |             -5.4127 |
| 3v3     |               0.0001 |               0.0000 |     50.7042 |      0.0000 |                0.0000 |     12.6761 |      0.0000 |     38.0282 |      0.0000 |          0.2500 |        nan      |          0.0000 |            0.0000 |    nan      |    nan      |    nan      |            nan      |

### overall

| state   |   toi_h_per_game_sim |   toi_h_per_game_act |   att60_sim |   att60_act |   att60_act_attr_rows |   blk60_sim |   blk60_act |   unb60_sim |   unb60_act |   blk_share_sim |   blk_share_act |   n_blocked_act |   n_unblocked_act |   att60_rel |   blk60_rel |   unb60_rel |   blk_share_diff_pp |
|:--------|---------------------:|---------------------:|------------:|------------:|----------------------:|------------:|------------:|------------:|------------:|----------------:|----------------:|----------------:|------------------:|------------:|------------:|------------:|--------------------:|
| 5v5     |               1.6464 |               1.6537 |     58.8095 |     58.4717 |               58.4717 |     17.1988 |     16.9801 |     41.6107 |     41.4916 |          0.2924 |          0.2904 |      39256.0000 |        95924.0000 |      0.0058 |      0.0129 |      0.0029 |              0.2051 |
| PP      |               0.1499 |               0.1488 |    101.3718 |    101.7125 |              101.7125 |     26.4556 |     25.6481 |     74.9162 |     76.0644 |          0.2610 |          0.2522 |       5334.0000 |        15819.0000 |     -0.0033 |      0.0315 |     -0.0151 |              0.8813 |
| PK      |               0.1499 |               0.1488 |     14.0575 |     14.2473 |               14.2473 |      1.7548 |      1.7358 |     12.3027 |     12.5115 |          0.1248 |          0.1218 |        361.0000 |         2602.0000 |     -0.0133 |      0.0109 |     -0.0167 |              0.2993 |
| 4v4     |               0.0256 |               0.0240 |     50.2365 |     48.8019 |               48.8019 |     11.9142 |     11.7304 |     38.3223 |     37.0716 |          0.2372 |          0.2404 |        393.0000 |         1242.0000 |      0.0294 |      0.0157 |      0.0337 |             -0.3204 |
| 3v3     |               0.0195 |               0.0177 |     55.5876 |     55.2313 |               55.2313 |      9.4511 |      9.6826 |     46.1365 |     45.5487 |          0.1700 |          0.1753 |        240.0000 |         1129.0000 |      0.0065 |     -0.0239 |      0.0129 |             -0.5289 |

## Closed-loop ES responsiveness (reported; D32 slope R over (game, team) units, deciles of the as-of Qa ES rating; 1,000 game bootstrap)

- for: R 1.241 (95% CI 0.944..1.847; UNDERPOWERED), old Q5-Q1 1.212, 2,796 units
- against: R 1.124 (95% CI 0.859..1.656; UNDERPOWERED), old Q5-Q1 1.196, 2,796 units

## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual 0.82; 28/32 within 3%, 13/32 tiers within 1.5 pp)

|   team_id |   n_actual_unblocked |   xg_sim |   xg_act |     rel |   high_diff_pp |   medium_diff_pp |   low_diff_pp | status                              | would_pass_xg   | would_pass_tiers   |
|----------:|---------------------:|---------:|---------:|--------:|---------------:|-----------------:|--------------:|:------------------------------------|:----------------|:-------------------|
|         1 |                 3632 |   0.0674 |   0.0675 | -0.0006 |         0.2681 |          -1.0639 |        0.7958 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         2 |                 3542 |   0.0644 |   0.0639 |  0.0071 |         0.1902 |           1.5111 |       -1.7013 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         3 |                 3511 |   0.0659 |   0.0645 |  0.0202 |         0.7146 |          -2.1845 |        1.4699 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         4 |                 3241 |   0.0662 |   0.0671 | -0.0140 |        -0.1700 |           0.3613 |       -0.1913 | UNDERPOWERED (team-level, labelled) | True            | True               |
|         5 |                 3487 |   0.0660 |   0.0667 | -0.0106 |        -0.0564 |           2.4226 |       -2.3662 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         6 |                 3185 |   0.0674 |   0.0661 |  0.0201 |         0.9244 |           0.7407 |       -1.6651 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         7 |                 3386 |   0.0647 |   0.0642 |  0.0073 |         0.9913 |          -5.2808 |        4.2894 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         8 |                 3390 |   0.0664 |   0.0671 | -0.0108 |         0.4664 |          -3.3169 |        2.8504 | UNDERPOWERED (team-level, labelled) | True            | False              |
|         9 |                 3684 |   0.0637 |   0.0637 |  0.0010 |         0.0616 |          -0.3009 |        0.2393 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        10 |                 3818 |   0.0671 |   0.0669 |  0.0030 |        -0.5335 |          -1.0058 |        1.5393 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        12 |                 4774 |   0.0634 |   0.0635 | -0.0013 |        -0.2799 |          -0.7853 |        1.0651 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        13 |                 4813 |   0.0646 |   0.0633 |  0.0200 |         0.1627 |           1.3039 |       -1.4666 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        14 |                 3605 |   0.0662 |   0.0674 | -0.0176 |        -0.9306 |           1.9779 |       -1.0473 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        15 |                 3822 |   0.0658 |   0.0657 |  0.0017 |        -2.8427 |           2.4574 |        0.3853 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        16 |                 2856 |   0.0639 |   0.0647 | -0.0124 |         0.4413 |          -1.3207 |        0.8794 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        17 |                 3339 |   0.0654 |   0.0664 | -0.0158 |         0.4978 |          -2.7247 |        2.2270 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        18 |                 3439 |   0.0653 |   0.0655 | -0.0030 |         0.7900 |          -2.3050 |        1.5151 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        19 |                 3358 |   0.0638 |   0.0645 | -0.0100 |         0.0035 |          -3.7744 |        3.7709 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        20 |                 3548 |   0.0626 |   0.0603 |  0.0385 |         0.1646 |          -1.6561 |        1.4915 | UNDERPOWERED (team-level, labelled) | False           | False              |
|        21 |                 3942 |   0.0655 |   0.0643 |  0.0191 |        -0.0611 |          -0.8422 |        0.9032 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        22 |                 4735 |   0.0668 |   0.0672 | -0.0065 |        -0.0687 |           4.1085 |       -4.0399 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        23 |                 3190 |   0.0648 |   0.0636 |  0.0198 |        -0.4380 |           1.5536 |       -1.1156 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        24 |                 3372 |   0.0635 |   0.0632 |  0.0037 |        -0.4006 |          -2.8840 |        3.2847 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        25 |                 4139 |   0.0662 |   0.0688 | -0.0372 |        -0.8982 |           1.2564 |       -0.3582 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        26 |                 3806 |   0.0634 |   0.0624 |  0.0162 |         0.2601 |           0.7426 |       -1.0028 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        28 |                 3172 |   0.0639 |   0.0632 |  0.0111 |         1.1295 |          -1.9548 |        0.8253 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        29 |                 3395 |   0.0642 |   0.0627 |  0.0244 |         0.4107 |          -0.6519 |        0.2412 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        30 |                 3531 |   0.0657 |   0.0622 |  0.0555 |        -0.2689 |           0.9932 |       -0.7243 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        52 |                 4035 |   0.0641 |   0.0647 | -0.0097 |        -1.4487 |           3.8376 |       -2.3889 | UNDERPOWERED (team-level, labelled) | True            | False              |
|        54 |                 4039 |   0.0654 |   0.0651 |  0.0051 |        -0.3986 |          -1.0173 |        1.4160 | UNDERPOWERED (team-level, labelled) | True            | True               |
|        55 |                 3364 |   0.0630 |   0.0612 |  0.0306 |         0.4755 |          -0.8513 |        0.3758 | UNDERPOWERED (team-level, labelled) | False           | True               |
|        59 |                 3566 |   0.0643 |   0.0647 | -0.0066 |         0.3575 |          -2.9024 |        2.5450 | UNDERPOWERED (team-level, labelled) | True            | False              |

## Stage 5b / 6 by state (reported; stand-in miss, C1s goal, oracle goalie)

### regular season

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       58768 |     27.5217 |     27.1429 |           0.3363 |           0.3453 |   0.9099 |   0.9096 |            0.9098 |    2.4803 |    2.4548 |      0.0140 |   -0.9003 |  0.0317 |    0.0104 | nan                          |
| PP            |        9973 |     51.2782 |     51.5662 |           0.3130 |           0.3221 |   0.8535 |   0.8491 |            0.8535 |    7.5142 |    7.7817 |     -0.0056 |   -0.9037 |  0.4369 |   -0.0344 | nan                          |
| PK            |        1923 |      9.6352 |      9.9430 |           0.2142 |           0.2096 |   0.9073 |   0.9048 |            0.9072 |    0.8928 |    0.9462 |     -0.0310 |    0.4620 |  0.2503 |   -0.0564 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |         812 |     25.5816 |     25.8224 |           0.3319 |           0.3042 |   0.8786 |   0.8879 |            0.8788 |    3.1056 |    2.8939 |     -0.0093 |    2.7690 | -0.9330 |    0.0732 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     32.6917 |     33.5664 |           0.2914 |           0.2631 |   0.7982 |   0.8041 |            0.7973 |    6.5978 |    6.5761 |     -0.0261 |    2.8369 | -0.5905 |    0.0033 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       72308 |     27.9913 |     27.7237 |           0.3299 |           0.3378 |   0.9003 |   0.8996 |            0.9003 |    2.7900 |    2.7824 |      0.0097 |   -0.7940 |  0.0687 |    0.0027 | nan                          |

### playoffs

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |    sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|---------:|----------:|:-----------------------------|
| 5v5           |        3753 |     28.4414 |     25.5728 |           0.3503 |           0.3912 |   0.9111 |   0.9081 |            0.9108 |    2.5292 |    2.3508 |      0.1122 |   -4.0935 |   0.2999 |    0.0759 | nan                          |
| PP            |         730 |     53.7298 |     50.1144 |           0.3180 |           0.3412 |   0.8504 |   0.8315 |            0.8509 |    8.0354 |    8.4439 |      0.0721 |   -2.3143 |   1.8942 |   -0.0484 | UNDERPOWERED (n SOG < 2,000) |
| PK            |         135 |     10.1717 |      9.2677 |           0.2102 |           0.2012 |   0.9103 |   0.9407 |            0.9082 |    0.9129 |    0.5492 |      0.0975 |    0.9005 |  -3.0486 |    0.6622 | UNDERPOWERED (n SOG < 2,000) |
| 4v4           |          52 |     25.4387 |     25.2768 |           0.3446 |           0.3067 |   0.8815 |   0.8462 |            0.8832 |    3.0149 |    3.8887 |      0.0064 |    3.7887 |   3.5331 |   -0.2247 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |           0 |     21.8950 |      0.0000 |           0.4242 |         nan      |   0.7895 | nan      |            0.8527 |    4.6095 |    0.0000 |    nan      |  nan      | nan      |  nan      | UNDERPOWERED (n SOG < 2,000) |
| all reachable |        4670 |     28.9541 |     26.2436 |           0.3425 |           0.3787 |   0.9019 |   0.8964 |            0.9017 |    2.8412 |    2.7199 |      0.1033 |   -3.6260 |   0.5513 |    0.0446 | nan                          |

### overall

| state         |   n_sog_act |   sog60_sim |   sog60_act |   miss_share_sim |   miss_share_act |   sv_sim |   sv_act |   sv_c1s_expected |   g60_sim |   g60_act |   sog60_rel |   miss_pp |   sv_pp |   g60_rel | note                         |
|:--------------|------------:|------------:|------------:|-----------------:|-----------------:|---------:|---------:|------------------:|----------:|----------:|------------:|----------:|--------:|----------:|:-----------------------------|
| 5v5           |       62521 |     27.5797 |     27.0433 |           0.3372 |           0.3482 |   0.9100 |   0.9095 |            0.9099 |    2.4834 |    2.4482 |      0.0198 |   -1.1026 |  0.0484 |    0.0144 | nan                          |
| PP            |       10703 |     51.4391 |     51.4645 |           0.3134 |           0.3234 |   0.8533 |   0.8479 |            0.8533 |    7.5484 |    7.8281 |     -0.0005 |   -1.0030 |  0.5362 |   -0.0357 | nan                          |
| PK            |        2058 |      9.6704 |      9.8957 |           0.2140 |           0.2091 |   0.9075 |   0.9072 |            0.9072 |    0.8941 |    0.9184 |     -0.0228 |    0.4889 |  0.0349 |   -0.0264 | nan                          |
| 4v4           |         864 |     25.5727 |     25.7889 |           0.3327 |           0.3043 |   0.8788 |   0.8854 |            0.8791 |    3.0999 |    2.9550 |     -0.0084 |    2.8347 | -0.6636 |    0.0490 | UNDERPOWERED (n SOG < 2,000) |
| 3v3           |         832 |     32.6900 |     33.5664 |           0.2915 |           0.2631 |   0.7982 |   0.8041 |            0.7973 |    6.5975 |    6.5761 |     -0.0261 |    2.8387 | -0.5906 |    0.0032 | UNDERPOWERED (n SOG < 2,000) |
| all reachable |       76978 |     28.0518 |     27.6292 |           0.3307 |           0.3405 |   0.9004 |   0.8994 |            0.9004 |    2.7932 |    2.7784 |      0.0153 |   -0.9743 |  0.0986 |    0.0053 | nan                          |

