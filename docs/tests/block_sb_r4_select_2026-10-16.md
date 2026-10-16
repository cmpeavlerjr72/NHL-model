# SB-R4 step 1: fold-1 s-grid selection (Lane B4, 2026-10-16)

Committed BEFORE any fold-2 fit. Rule (SB-R4): the rating enters as the fixed offset s x c (c = fold-1-train-fitted B1 coefficient of that rating, raw units; the other B1 features are refit). Per construction, among s with fold-1 LL within 2 paired SE (1,000 game-block bootstrap, vs the best-LL s) of the best, pick the s whose fold-1 ES decile-slope R (for and against, D32) is closest to 1, i.e. minimal max(|log R_for|, |log R_against|); exact ties go to the smaller s. B2x's base is the construction with the smaller selected metric (tie: Rr). Level M1_K500; fold 1 = train 2021-22 + 2022-23, test 2023-24. R is the point estimate (CIs are in select.json); old = Q5-Q1 endpoint ratio (reported only).

Fold-1 fitted coefficients c (own / opp): Rr 0.4889 / 1.0935; Ra 0.5969 / 1.0224.

| cons   |      s |   ll_per_attempt |   ll_game_vs_best |   se_vs_best | in_2se   |   R_for |   R_against |   old_for |   old_against |   metric |
|:-------|-------:|-----------------:|------------------:|-------------:|:---------|--------:|------------:|----------:|--------------:|---------:|
| Rr     | 0.2500 |          -0.5916 |           -0.0215 |       0.0050 | False    |  0.9073 |      0.3237 |    0.0407 |        0.2978 |   1.1279 |
| Rr     | 0.5000 |          -0.5915 |           -0.0070 |       0.0025 | False    |  0.4834 |      0.6400 |    0.2125 |        0.6280 |   0.7268 |
| Rr     | 0.7500 |          -0.5914 |            0.0000 |       0.0000 | True     |  0.5906 |      0.9648 |    0.3845 |        0.9584 |   0.5266 |
| Rr     | 1.0000 |          -0.5914 |           -0.0004 |       0.0024 | True     |  0.7485 |      1.2916 |    0.5565 |        1.2889 |   0.2897 |
| Rr     | 1.2500 |          -0.5915 |           -0.0083 |       0.0049 | True     |  0.9217 |      1.6193 |    0.7285 |        1.6193 |   0.4820 |
| Ra     | 0.2500 |          -0.5916 |           -0.0261 |       0.0074 | False    |  0.3685 |      0.2666 |    0.0171 |        0.2417 |   1.3218 |
| Ra     | 0.5000 |          -0.5914 |           -0.0096 |       0.0049 | True     |  0.3588 |      0.5652 |    0.2965 |        0.5492 |   1.0251 |
| Ra     | 0.7500 |          -0.5914 |           -0.0009 |       0.0025 | True     |  0.5729 |      0.8813 |    0.5761 |        0.8568 |   0.5571 |
| Ra     | 1.0000 |          -0.5913 |            0.0000 |       0.0000 | True     |  0.8066 |      1.2007 |    0.8556 |        1.1644 |   0.2149 |
| Ra     | 1.2500 |          -0.5914 |           -0.0069 |       0.0024 | False    |  1.0460 |      1.5210 |    1.1349 |        1.4720 |   0.4194 |

- **Rr: selected s = 1.0** (R for 0.749, against 1.292; best-LL s 0.75).
- **Ra: selected s = 1.0** (R for 0.807, against 1.201; best-LL s 1.0).
- **B2x base = Ra** (smaller selected metric).
- n_games 1400.
