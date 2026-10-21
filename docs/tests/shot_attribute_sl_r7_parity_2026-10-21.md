# SL-R7 step 0 and parity analogue, (H, P) selection (Lane A7, 2026-10-21)

Generated 2026-10-21 12:21:14 -0400 (44 s) by `scripts/train_shot_attribute_v7.py parity`. Committed BEFORE any fold-2 prediction. Training seasons only (fold 1: 2021-22, 2022-23; fold 2: 2021-22 to 2023-24): no test-season row, prediction or s_t value is read or printed here.

## Construction (spec SL-R7; code `src/nhl_sim/shot_attribute/scale.py`, test `tests/test_shot_attribute_asof_scale.py`)

- L1x-as (non-EN rows): logit = log L0s levelled (M1 K500) + the fold's FROZEN SL-R6 L1x-ot0 home / score / rest terms (score terms zero on OT rows) + (s_for,t zf + s_against,t za) x c, c the frozen quality direction. EN rows: L0s levelled. Nothing is refit.
- zf = own Qa / SD, za = opponent Qa / SD, SD over the fold's 2021-22 in-scope rows (unit only): fold 1 0.02223 / 0.01961, fold 2 0.02242 / 0.01945.
- (s_for,t, s_against,t): two-parameter MNL slope fit on every non-EN unblocked attempt dated before the game date (OT rows included, score terms zero), weights 0.5^(age/H), offset fixed; shrunk to the previous date's pair with prior precision P x the per-attempt Fisher information matrix; Newton from the previous pair; start (0, 0), 2021-22 burn-in (never judged); created_at = previous date's last drop + 6 h, asserted < puck_drop. A coordinate with no information (all-zero season-opening ratings) carries forward.
- Numerical method (labelled): window sums by exact decay recursion, each row's score / information through its cumulant series in t (order 20). Checks (`results/shot_attribute_r7/snap_check.json`): exact direct-evaluation Newton step at 8 sampled dates x 3 cells per fold, max |diff| fold 1 6.2e-17, fold 2 1.8e-15; series order 14 vs 20: max |diff| 1.8e-14.
- Parity R: D32 decile slope ratio on ES rows of that training season, deciles of the row's own as-of Qa (for) / the opponent's (against); CI = 200-resample game bootstrap. The W terms are fitted on the fold's training rows (in sample, as in G-R3's table); the response scale is as-of, so R is out of sample for the scale.

## Step 0: the trend the as-of scale must track

SL-R6 step 0 per-season Qa coefficients (season alone, own unlevelled L0s, free W; raw rating units; `sl_r6_step0.json`):

| rating | 2021-22 | 2022-23 | 2023-24 | p (flat) | trend z |
|---|---|---|---|---|---|
| for | 1.753 (0.184) | 1.495 (0.138) | 1.210 (0.109) | 0.027 | -2.46 |
| against | 1.695 (0.192) | 0.944 (0.159) | 1.103 (0.146) | 0.008 | -2.07 |

SL-R6 fixed scale (Qa x0.75, frozen): s_f 1.1947, s_a 0.9715 (raw units).

Season-alone MLE of the pair under the SL-R7 offset (frozen W of the fold, levelled L0s; P = 0; raw units = z units / SD):

|   fold |        season |   s_for_z |   s_against_z |   s_for_raw |   s_against_raw |
|-------:|--------------:|----------:|--------------:|------------:|----------------:|
| 1.0000 | 20212022.0000 |    0.0379 |        0.0340 |      1.7043 |          1.7311 |
| 1.0000 | 20222023.0000 |    0.0336 |        0.0194 |      1.5137 |          0.9901 |
| 2.0000 | 20212022.0000 |    0.0391 |        0.0329 |      1.7459 |          1.6898 |
| 2.0000 | 20222023.0000 |    0.0342 |        0.0190 |      1.5236 |          0.9744 |
| 2.0000 | 20232024.0000 |    0.0273 |        0.0214 |      1.2183 |          1.0999 |

As-of s_t over training dates, per cell and season (raw units; first / mid / last game date of the season, min / max; n_eff = summed window weight on the last date):

|   fold | cell        |   season |   for_first |   for_mid |   for_last |   for_min |   for_max |   against_first |   against_mid |   against_last |   against_min |   against_max |   n_eff_last |
|-------:|:------------|---------:|------------:|----------:|-----------:|----------:|----------:|----------------:|--------------:|---------------:|--------------:|--------------:|-------------:|
|      1 | H365_P10000 | 20212022 |      0.0000 |    1.8542 |     1.7024 |    0.0000 |  536.7345 |          0.0000 |        1.6392 |         1.7549 |       -1.1616 |      689.1733 |   91001.4996 |
|      1 | H365_P10000 | 20222023 |      1.6805 |    1.5119 |     1.5577 |    1.4483 |    1.8192 |          1.7649 |        1.2438 |         1.2121 |        1.0886 |        1.7652 |  137981.0021 |
|      1 | H365_P2000  | 20212022 |      0.0000 |    1.8539 |     1.7007 |   -1.2446 | 2196.0677 |          0.0000 |        1.6371 |         1.7560 |       -3.0686 |     2819.7765 |   91001.4996 |
|      1 | H365_P2000  | 20222023 |      1.6781 |    1.5115 |     1.5579 |    1.4476 |    1.8232 |          1.7660 |        1.2440 |         1.2122 |        1.0869 |        1.7662 |  137981.0021 |
|      1 | H180_P10000 | 20212022 |      0.0000 |    1.8397 |     1.6800 |    0.0000 |  535.4603 |          0.0000 |        1.6824 |         1.7854 |       -1.1323 |      687.5372 |   70167.0726 |
|      1 | H180_P10000 | 20222023 |      1.6539 |    1.4527 |     1.5432 |    1.3765 |    1.8607 |          1.7974 |        1.1343 |         1.1547 |        0.9705 |        1.7974 |   88346.9961 |
|      1 | H180_P2000  | 20212022 |      0.0000 |    1.8393 |     1.6773 |   -1.2189 | 2191.8009 |          0.0000 |        1.6797 |         1.7872 |       -3.0585 |     2814.2978 |   70167.0726 |
|      1 | H180_P2000  | 20222023 |      1.6495 |    1.4519 |     1.5436 |    1.3757 |    1.8692 |          1.7994 |        1.1348 |         1.1550 |        0.9675 |        1.7995 |   88346.9961 |
|      1 | H90_P10000  | 20212022 |      0.0000 |    1.8096 |     1.6342 |    0.0000 |  532.9558 |          0.0000 |        1.7640 |         1.8376 |       -1.0718 |      684.3214 |   43894.5160 |
|      1 | H90_P10000  | 20222023 |      1.6011 |    1.3694 |     1.5512 |    1.2284 |    2.0006 |          1.8530 |        0.9632 |         1.1263 |        0.8113 |        1.8530 |   46431.9771 |
|      1 | H90_P2000   | 20212022 |      0.0000 |    1.8089 |     1.6281 |   -1.1675 | 2183.4036 |          0.0000 |        1.7599 |         1.8417 |       -3.0384 |     2803.5156 |   43894.5160 |
|      1 | H90_P2000   | 20222023 |      1.5884 |    1.3678 |     1.5525 |    1.2261 |    2.0245 |          1.8590 |        0.9644 |         1.1274 |        0.8052 |        1.8590 |   46431.9771 |
|      1 | H45_P10000  | 20212022 |      0.0000 |    1.7458 |     1.5341 |    0.0000 |  527.9844 |          0.0000 |        1.9112 |         1.9188 |       -0.9384 |      677.9381 |   19959.9692 |
|      1 | H45_P10000  | 20222023 |      1.5018 |    1.3026 |     1.6144 |    1.0504 |    2.3699 |          1.9347 |        0.8038 |         1.2550 |        0.6578 |        1.9347 |   19286.9276 |
|      1 | H45_P2000   | 20212022 |      0.0000 |    1.7436 |     1.5114 |   -1.0610 | 2166.6926 |          0.0000 |        1.9028 |         1.9338 |       -2.9982 |     2782.0586 |   19959.9692 |
|      1 | H45_P2000   | 20222023 |      1.4520 |    1.2992 |     1.6202 |    1.0442 |    2.4281 |          1.9603 |        0.8073 |         1.2600 |        0.6548 |        1.9603 |   19286.9276 |
|      2 | H365_P10000 | 20212022 |      0.0000 |    1.8907 |     1.7440 |    0.0000 |  523.3613 |          0.0000 |        1.5687 |         1.7145 |       -1.2668 |      695.5689 |   91001.4996 |
|      2 | H365_P10000 | 20222023 |      1.7223 |    1.5426 |     1.5738 |    1.4746 |    1.8564 |          1.7257 |        1.2197 |         1.1861 |        1.0632 |        1.7282 |  137981.0021 |
|      2 | H365_P10000 | 20232024 |      1.5764 |    1.5013 |     1.3181 |    1.3165 |    1.6062 |          1.1891 |        1.0593 |         1.1581 |        1.0123 |        1.2271 |  157251.5113 |
|      2 | H365_P2000  | 20212022 |      0.0000 |    1.8904 |     1.7422 |   -0.9822 | 2142.1466 |          0.0000 |        1.5660 |         1.7158 |       -2.8571 |     2847.0018 |   91001.4996 |
|      2 | H365_P2000  | 20222023 |      1.7200 |    1.5422 |     1.5740 |    1.4739 |    1.8600 |          1.7269 |        1.2199 |         1.1863 |        1.0615 |        1.7295 |  137981.0021 |
|      2 | H365_P2000  | 20232024 |      1.5766 |    1.5013 |     1.3179 |    1.3161 |    1.6068 |          1.1893 |        1.0592 |         1.1582 |        1.0121 |        1.2277 |  157251.5113 |
|      2 | H180_P10000 | 20212022 |      0.0000 |    1.8754 |     1.7219 |    0.0000 |  522.1186 |          0.0000 |        1.6126 |         1.7468 |       -1.2387 |      693.9173 |   70167.0726 |
|      2 | H180_P10000 | 20222023 |      1.6960 |    1.4817 |     1.5553 |    1.4062 |    1.8956 |          1.7602 |        1.1150 |         1.1318 |        0.9484 |        1.7634 |   88346.9961 |
|      2 | H180_P10000 | 20232024 |      1.5588 |    1.4651 |     1.2317 |    1.2277 |    1.6157 |          1.1361 |        0.9763 |         1.1594 |        0.9108 |        1.2138 |   88507.2687 |
|      2 | H180_P2000  | 20212022 |      0.0000 |    1.8750 |     1.7190 |   -0.9574 | 2137.9826 |          0.0000 |        1.6092 |         1.7489 |       -2.8472 |     2841.4677 |   70167.0726 |
|      2 | H180_P2000  | 20222023 |      1.6917 |    1.4810 |     1.5557 |    1.4049 |    1.9034 |          1.7625 |        1.1155 |         1.1323 |        0.9453 |        1.7661 |   88346.9961 |
|      2 | H180_P2000  | 20232024 |      1.5593 |    1.4651 |     1.2311 |    1.2268 |    1.6179 |          1.1367 |        0.9762 |         1.1599 |        0.9067 |        1.2156 |   88507.2687 |
|      2 | H90_P10000  | 20212022 |      0.0000 |    1.8438 |     1.6766 |    0.0000 |  519.6762 |          0.0000 |        1.6953 |         1.8018 |       -1.1802 |      690.6713 |   43894.5160 |
|      2 | H90_P10000  | 20222023 |      1.6439 |    1.3963 |     1.5578 |    1.2663 |    2.0262 |          1.8189 |        0.9501 |         1.1058 |        0.7916 |        1.8224 |   46431.9771 |
|      2 | H90_P10000  | 20232024 |      1.5629 |    1.4293 |     1.1334 |    1.1228 |    1.6808 |          1.1124 |        0.8972 |         1.2275 |        0.7543 |        1.2911 |   43135.5085 |
|      2 | H90_P2000   | 20212022 |      0.0000 |    1.8430 |     1.6702 |   -0.9076 | 2129.7878 |          0.0000 |        1.6902 |         1.8063 |       -2.8277 |     2830.5764 |   43894.5160 |
|      2 | H90_P2000   | 20222023 |      1.6313 |    1.3948 |     1.5589 |    1.2645 |    2.0498 |          1.8256 |        0.9514 |         1.1074 |        0.7858 |        1.8318 |   46431.9771 |
|      2 | H90_P2000   | 20232024 |      1.5650 |    1.4289 |     1.1318 |    1.1202 |    1.6915 |          1.1152 |        0.8970 |         1.2290 |        0.7468 |        1.2995 |   43135.5085 |
|      2 | H45_P10000  | 20212022 |      0.0000 |    1.7769 |     1.5780 |    0.0000 |  514.8281 |          0.0000 |        1.8435 |         1.8859 |       -1.0791 |      684.2279 |   19959.9692 |
|      2 | H45_P10000  | 20222023 |      1.5461 |    1.3268 |     1.6158 |    1.0913 |    2.3723 |          1.9033 |        0.7942 |         1.2324 |        0.6504 |        1.9033 |   19286.9276 |
|      2 | H45_P10000  | 20232024 |      1.6206 |    1.3978 |     1.0384 |    0.9857 |    1.8004 |          1.2392 |        0.8521 |         1.3938 |        0.5849 |        1.5259 |   16915.8122 |
|      2 | H45_P2000   | 20212022 |      0.0000 |    1.7746 |     1.5543 |   -0.8048 | 2113.4798 |          0.0000 |        1.8332 |         1.9025 |       -2.7886 |     2808.9025 |   19959.9692 |
|      2 | H45_P2000   | 20222023 |      1.4964 |    1.3237 |     1.6203 |    1.0863 |    2.4283 |          1.9316 |        0.7977 |         1.2401 |        0.6394 |        1.9316 |   19286.9276 |
|      2 | H45_P2000   | 20232024 |      1.6298 |    1.3956 |     1.0339 |    0.9351 |    1.8373 |          1.2530 |        0.8516 |         1.3987 |        0.4737 |        1.5911 |   16915.8122 |

## Parity analogue (genuine-prior training seasons; band [0.9, 1.1] on both R)

|   fold |   season | arm                                  | cell        |   R_for | for_ci    |   R_against | against_ci   |   max_abs_logR | both_in   |
|-------:|---------:|:-------------------------------------|:------------|--------:|:----------|------------:|:-------------|---------------:|:----------|
|      1 | 20222023 | L1x-ot0 fixed (SL-R6)                | Qa x0.75    |  0.9213 | 0.71-1.22 |      0.8882 | 0.65-1.25    |         0.1185 | False     |
|      1 | 20222023 | season-own MLE (post-hoc diagnostic) | -           |  1.1668 | 0.90-1.55 |      0.9094 | 0.67-1.27    |         0.1543 | False     |
|      1 | 20222023 | L1x-as                               | H365_P10000 |  1.2315 | 0.95-1.64 |      1.2386 | 0.90-1.77    |         0.2140 | False     |
|      1 | 20222023 | L1x-as                               | H365_P2000  |  1.2315 | 0.95-1.64 |      1.2384 | 0.90-1.77    |         0.2138 | False     |
|      1 | 20222023 | L1x-as                               | H180_P10000 |  1.2071 | 0.93-1.60 |      1.1700 | 0.85-1.67    |         0.1882 | False     |
|      1 | 20222023 | L1x-as                               | H180_P2000  |  1.2070 | 0.93-1.60 |      1.1696 | 0.85-1.67    |         0.1881 | False     |
|      1 | 20222023 | L1x-as                               | H90_P10000  |  1.1816 | 0.91-1.57 |      1.0556 | 0.78-1.51    |         0.1669 | False     |
|      1 | 20222023 | L1x-as                               | H90_P2000   |  1.1814 | 0.91-1.57 |      1.0546 | 0.78-1.51    |         0.1667 | False     |
|      1 | 20222023 | L1x-as                               | H45_P10000  |  1.1814 | 0.91-1.56 |      0.9324 | 0.69-1.33    |         0.1667 | False     |
|      1 | 20222023 | L1x-as                               | H45_P2000   |  1.1814 | 0.91-1.56 |      0.9293 | 0.69-1.32    |         0.1667 | False     |
|      2 | 20222023 | L1x-ot0 fixed (SL-R6)                | Qa x0.75    |  0.9158 | 0.72-1.19 |      0.8675 | 0.63-1.25    |         0.1421 | False     |
|      2 | 20222023 | season-own MLE (post-hoc diagnostic) | -           |  1.1673 | 0.92-1.53 |      0.8759 | 0.64-1.27    |         0.1547 | False     |
|      2 | 20232024 | L1x-ot0 fixed (SL-R6)                | Qa x0.75    |  1.0084 | 0.86-1.21 |      0.9634 | 0.77-1.38    |         0.0373 | True      |
|      2 | 20232024 | season-own MLE (post-hoc diagnostic) | -           |  1.0263 | 0.88-1.24 |      1.0777 | 0.86-1.54    |         0.0748 | True      |
|      2 | 20222023 | L1x-as                               | H365_P10000 |  1.2469 | 0.98-1.63 |      1.1812 | 0.85-1.67    |         0.2206 | False     |
|      2 | 20232024 | L1x-as                               | H365_P10000 |  1.2478 | 1.07-1.51 |      1.0831 | 0.87-1.54    |         0.2213 | False     |
|      2 | 20222023 | L1x-as                               | H365_P2000  |  1.2468 | 0.98-1.63 |      1.1810 | 0.85-1.67    |         0.2206 | False     |
|      2 | 20232024 | L1x-as                               | H365_P2000  |  1.2477 | 1.07-1.51 |      1.0831 | 0.87-1.54    |         0.2213 | False     |
|      2 | 20222023 | L1x-as                               | H180_P10000 |  1.2206 | 0.96-1.60 |      1.1174 | 0.81-1.58    |         0.1994 | False     |
|      2 | 20232024 | L1x-as                               | H180_P10000 |  1.2142 | 1.04-1.47 |      1.0337 | 0.83-1.47    |         0.1941 | False     |
|      2 | 20222023 | L1x-as                               | H180_P2000  |  1.2205 | 0.96-1.60 |      1.1170 | 0.81-1.58    |         0.1993 | False     |
|      2 | 20232024 | L1x-as                               | H180_P2000  |  1.2141 | 1.04-1.47 |      1.0335 | 0.83-1.47    |         0.1940 | False     |
|      2 | 20222023 | L1x-as                               | H90_P10000  |  1.1924 | 0.94-1.56 |      1.0100 | 0.74-1.44    |         0.1759 | False     |
|      2 | 20232024 | L1x-as                               | H90_P10000  |  1.1793 | 1.01-1.42 |      1.0051 | 0.81-1.44    |         0.1650 | False     |
|      2 | 20222023 | L1x-as                               | H90_P2000   |  1.1921 | 0.94-1.56 |      1.0091 | 0.74-1.43    |         0.1757 | False     |
|      2 | 20232024 | L1x-as                               | H90_P2000   |  1.1791 | 1.01-1.42 |      1.0046 | 0.80-1.44    |         0.1648 | False     |
|      2 | 20222023 | L1x-as                               | H45_P10000  |  1.1886 | 0.93-1.54 |      0.8934 | 0.66-1.29    |         0.1727 | False     |
|      2 | 20232024 | L1x-as                               | H45_P10000  |  1.1433 | 0.97-1.38 |      1.0121 | 0.81-1.46    |         0.1339 | False     |
|      2 | 20222023 | L1x-as                               | H45_P2000   |  1.1886 | 0.93-1.54 |      0.8906 | 0.66-1.28    |         0.1728 | False     |
|      2 | 20232024 | L1x-as                               | H45_P2000   |  1.1424 | 0.97-1.38 |      1.0103 | 0.81-1.46    |         0.1331 | False     |

Per cell (L1x-as, all three genuine-prior season cells, both directions):

| cell        |        H |          P |   max_abs_logR | all_in   |   R_for_min |   R_for_max |   R_against_min |   R_against_max |
|:------------|---------:|-----------:|---------------:|:---------|------------:|------------:|----------------:|----------------:|
| H365_P10000 | 365.0000 | 10000.0000 |         0.2213 | False    |      1.2315 |      1.2478 |          1.0831 |          1.2386 |
| H365_P2000  | 365.0000 |  2000.0000 |         0.2213 | False    |      1.2315 |      1.2477 |          1.0831 |          1.2384 |
| H180_P10000 | 180.0000 | 10000.0000 |         0.1994 | False    |      1.2071 |      1.2206 |          1.0337 |          1.1700 |
| H180_P2000  | 180.0000 |  2000.0000 |         0.1993 | False    |      1.2070 |      1.2205 |          1.0335 |          1.1696 |
| H90_P10000  |  90.0000 | 10000.0000 |         0.1759 | False    |      1.1793 |      1.1924 |          1.0051 |          1.0556 |
| H90_P2000   |  90.0000 |  2000.0000 |         0.1757 | False    |      1.1791 |      1.1921 |          1.0046 |          1.0546 |
| H45_P10000  |  45.0000 | 10000.0000 |         0.1727 | False    |      1.1433 |      1.1886 |          0.8934 |          1.0121 |
| H45_P2000   |  45.0000 |  2000.0000 |         0.1728 | False    |      1.1424 |      1.1886 |          0.8906 |          1.0103 |

- **Selected: H45_P10000 (H 45, P 10000)**: no passer: smallest max |log R| over both directions and all judged seasons (listed), proceed. Passers: none.
- The season-own-MLE rows are a post-hoc diagnostic (in sample), used for no choice.
## Reading (Lane A7; written before any fold-2 prediction)

- **Burn-in.** On the first 2021-22 dates the ratings are near zero and nearly collinear. The prior precision (P x the per-attempt information) is then near zero too, so the specified estimate jumps (raw max 500-2,800 in the table) and settles by 2021-10-25 (H any; direct evaluation used only on dates up to 2021-10-25, `snap_check.json`). 2021-22 is burn-in and never judged, as specified.
- **The as-of pair tracks the likelihood slope.** In 2022-23 the as-of "for" pair sits at 1.30-1.62 raw (season-alone MLE 1.51-1.52), and in 2023-24 it falls toward 1.03-1.32 (MLE 1.22). The "for" trend is tracked; shorter H tracks it faster.
- **The likelihood slope over-responds on R.** Even the in-sample season-own MLE gives "for" R 1.17 on 2022-23. The SL-R6 fixed scale was 0.75 x the fold-1 free fit, chosen for R near 1 (its Qa x1.0 cell had fold-1 R 1.27 / 1.22). The as-of scale has no such multiplier (the spec drops it), so every cell over-responds on "for" by 14-25% on the training seasons. "Against" is in [0.89, 1.24].
- **Selection.** No cell passes [0.9, 1.1] on all three season cells. The fallback picks H45 P10000 (max |log R| 0.1727; H45 P2000 is 0.00004 behind). The P values are indistinguishable (n_eff 17k-158k against P 2k-10k), as in G-R3.
