# SB-R4 step 0: per-season rating coefficients, incumbent vs Rr vs Ra (Lane B4, 2026-10-16)

Spec: `docs/models/block/experiments.md` SB-R4 step 0. Seasons 2021-22..2023-24 only; 2024-25 not read. Ratings b 1000, w 0.7; level M1_K500; B1 design (SB-R1) with the arena factor as a feature, unpenalised fits. 'for' = shooting team's as-of blocked-against rating (`own_r`), 'against' = defending team's as-of blocks-for rating (`opp_r`). Raw rating units. Generated 2026-10-16 12:20:39 by `scripts/diag_block_sbr4_step0.py`. Report only, no decision.

## Coefficients (SE model-based and game-cluster)

|                                                         |   coef |   se_model |   se_cluster |   rating_sd |   coef_x_sd |
|:--------------------------------------------------------|-------:|-----------:|-------------:|------------:|------------:|
| ('incumbent', 'fold-1 train (21-22, 22-23)', 'own_r')   | 0.5261 |     0.0840 |       0.0885 |      0.0500 |      0.0263 |
| ('incumbent', 'fold-1 train (21-22, 22-23)', 'opp_r')   | 0.9945 |     0.0599 |       0.0627 |      0.0689 |      0.0685 |
| ('incumbent', 'fold-1 train (21-22, 22-23)', 'arena_f') | 0.6587 |     0.0824 |       0.0862 |      0.0515 |      0.0340 |
| ('incumbent', 'fold-2 train (21-22..23-24)', 'own_r')   | 0.6276 |     0.0665 |       0.0694 |      0.0499 |      0.0313 |
| ('incumbent', 'fold-2 train (21-22..23-24)', 'opp_r')   | 0.9435 |     0.0484 |       0.0512 |      0.0677 |      0.0639 |
| ('incumbent', 'fold-2 train (21-22..23-24)', 'arena_f') | 0.5401 |     0.0710 |       0.0736 |      0.0474 |      0.0256 |
| ('incumbent', 'season 20212022 alone', 'own_r')         | 0.6784 |     0.1163 |       0.1237 |      0.0519 |      0.0352 |
| ('incumbent', 'season 20212022 alone', 'opp_r')         | 1.0593 |     0.0991 |       0.1014 |      0.0595 |      0.0630 |
| ('incumbent', 'season 20212022 alone', 'arena_f')       | 0.7545 |     0.1174 |       0.1276 |      0.0519 |      0.0392 |
| ('incumbent', 'season 20222023 alone', 'own_r')         | 0.3634 |     0.1218 |       0.1264 |      0.0481 |      0.0175 |
| ('incumbent', 'season 20222023 alone', 'opp_r')         | 0.9593 |     0.0753 |       0.0795 |      0.0769 |      0.0738 |
| ('incumbent', 'season 20222023 alone', 'arena_f')       | 0.5731 |     0.1159 |       0.1169 |      0.0511 |      0.0293 |
| ('incumbent', 'season 20232024 alone', 'own_r')         | 0.7790 |     0.1092 |       0.1122 |      0.0496 |      0.0387 |
| ('incumbent', 'season 20232024 alone', 'opp_r')         | 0.8472 |     0.0826 |       0.0887 |      0.0655 |      0.0555 |
| ('incumbent', 'season 20232024 alone', 'arena_f')       | 0.2042 |     0.1427 |       0.1397 |      0.0383 |      0.0078 |
| ('Rr', 'fold-1 train (21-22, 22-23)', 'own_r')          | 0.4889 |     0.0986 |       0.1022 |      0.0415 |      0.0203 |
| ('Rr', 'fold-1 train (21-22, 22-23)', 'opp_r')          | 1.0935 |     0.0724 |       0.0757 |      0.0563 |      0.0616 |
| ('Rr', 'fold-1 train (21-22, 22-23)', 'arena_f')        | 1.0262 |     0.0794 |       0.0844 |      0.0515 |      0.0529 |
| ('Rr', 'fold-2 train (21-22..23-24)', 'own_r')          | 0.6020 |     0.0745 |       0.0774 |      0.0436 |      0.0262 |
| ('Rr', 'fold-2 train (21-22..23-24)', 'opp_r')          | 0.9832 |     0.0560 |       0.0594 |      0.0578 |      0.0568 |
| ('Rr', 'fold-2 train (21-22..23-24)', 'arena_f')        | 0.9039 |     0.0691 |       0.0725 |      0.0474 |      0.0428 |
| ('Rr', 'season 20212022 alone', 'own_r')                | 0.8820 |     0.1492 |       0.1533 |      0.0396 |      0.0350 |
| ('Rr', 'season 20212022 alone', 'opp_r')                | 1.1751 |     0.1221 |       0.1234 |      0.0483 |      0.0567 |
| ('Rr', 'season 20212022 alone', 'arena_f')              | 1.1887 |     0.1141 |       0.1242 |      0.0519 |      0.0617 |
| ('Rr', 'season 20222023 alone', 'own_r')                | 0.1795 |     0.1317 |       0.1364 |      0.0432 |      0.0078 |
| ('Rr', 'season 20222023 alone', 'opp_r')                | 1.0524 |     0.0900 |       0.0957 |      0.0632 |      0.0665 |
| ('Rr', 'season 20222023 alone', 'arena_f')              | 0.8821 |     0.1110 |       0.1151 |      0.0511 |      0.0451 |
| ('Rr', 'season 20232024 alone', 'own_r')                | 0.7447 |     0.1138 |       0.1182 |      0.0474 |      0.0353 |
| ('Rr', 'season 20232024 alone', 'opp_r')                | 0.8256 |     0.0888 |       0.0956 |      0.0604 |      0.0498 |
| ('Rr', 'season 20232024 alone', 'arena_f')              | 0.5189 |     0.1412 |       0.1379 |      0.0383 |      0.0199 |
| ('Ra', 'fold-1 train (21-22, 22-23)', 'own_r')          | 0.5969 |     0.0923 |       0.0949 |      0.0444 |      0.0265 |
| ('Ra', 'fold-1 train (21-22, 22-23)', 'opp_r')          | 1.0224 |     0.0619 |       0.0641 |      0.0659 |      0.0673 |
| ('Ra', 'fold-1 train (21-22, 22-23)', 'arena_f')        | 0.8961 |     0.0794 |       0.0841 |      0.0515 |      0.0462 |
| ('Ra', 'fold-2 train (21-22..23-24)', 'own_r')          | 0.6693 |     0.0697 |       0.0716 |      0.0466 |      0.0312 |
| ('Ra', 'fold-2 train (21-22..23-24)', 'opp_r')          | 0.9493 |     0.0500 |       0.0523 |      0.0649 |      0.0616 |
| ('Ra', 'fold-2 train (21-22..23-24)', 'arena_f')        | 0.8339 |     0.0690 |       0.0720 |      0.0474 |      0.0395 |
| ('Ra', 'season 20212022 alone', 'own_r')                | 0.7717 |     0.1263 |       0.1298 |      0.0469 |      0.0362 |
| ('Ra', 'season 20212022 alone', 'opp_r')                | 1.0896 |     0.1011 |       0.1025 |      0.0578 |      0.0630 |
| ('Ra', 'season 20212022 alone', 'arena_f')              | 0.9266 |     0.1144 |       0.1248 |      0.0519 |      0.0481 |
| ('Ra', 'season 20222023 alone', 'own_r')                | 0.3889 |     0.1359 |       0.1395 |      0.0419 |      0.0163 |
| ('Ra', 'season 20222023 alone', 'opp_r')                | 0.9795 |     0.0783 |       0.0819 |      0.0729 |      0.0714 |
| ('Ra', 'season 20222023 alone', 'arena_f')              | 0.8490 |     0.1109 |       0.1144 |      0.0511 |      0.0434 |
| ('Ra', 'season 20232024 alone', 'own_r')                | 0.7410 |     0.1074 |       0.1093 |      0.0505 |      0.0374 |
| ('Ra', 'season 20232024 alone', 'opp_r')                | 0.8106 |     0.0851 |       0.0908 |      0.0631 |      0.0511 |
| ('Ra', 'season 20232024 alone', 'arena_f')              | 0.6380 |     0.1419 |       0.1390 |      0.0383 |      0.0245 |

## Flatness across the three single seasons

chi2 = inverse-variance-weighted heterogeneity (2 df; > 5.99 rejects equality at 5%); trend = weighted slope of the coefficient on season index, with its SE and z. Each season's cluster SE is wide, so a flat verdict is only as strong as these SEs.

|                        |   coef_21_22 |   coef_22_23 |   coef_23_24 |   chi2_equal_2df |   trend_per_season |   trend_se |   trend_z |
|:-----------------------|-------------:|-------------:|-------------:|-----------------:|-------------------:|-----------:|----------:|
| ('incumbent', 'own_r') |       0.6784 |       0.3634 |       0.7790 |           6.3523 |             0.0611 |     0.0834 |    0.7329 |
| ('incumbent', 'opp_r') |       1.0593 |       0.9593 |       0.8472 |           2.5162 |            -0.1064 |     0.0671 |   -1.5852 |
| ('Rr', 'own_r')        |       0.8820 |       0.1795 |       0.7447 |          14.3795 |            -0.0146 |     0.0957 |   -0.1528 |
| ('Rr', 'opp_r')        |       1.1751 |       1.0524 |       0.8256 |           5.6254 |            -0.1799 |     0.0771 |   -2.3341 |
| ('Ra', 'own_r')        |       0.7717 |       0.3889 |       0.7410 |           5.0669 |             0.0016 |     0.0845 |    0.0184 |
| ('Ra', 'opp_r')        |       1.0896 |       0.9795 |       0.8106 |           4.3402 |            -0.1410 |     0.0683 |   -2.0651 |

## Correlation of the as-of ratings with the arena factor (fold-2 train, gated rows)

| construction   |   corr_own_r_arena_f |   corr_opp_r_arena_f |   sd_own_r |   sd_opp_r |
|:---------------|---------------------:|---------------------:|-----------:|-----------:|
| incumbent      |               0.1889 |               0.1408 |     0.0499 |     0.0677 |
| Rr             |              -0.0564 |              -0.0111 |     0.0436 |     0.0577 |
| Ra             |               0.0051 |               0.0197 |     0.0466 |     0.0649 |
