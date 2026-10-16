# SM-R1 step 2: fold-1 s-grid selection for the shooting team's road-only miss rating (Lane M, 2026-10-16)

Generated 2026-10-16 12:44:32 by `scripts/train_miss_v1.py select`. Committed BEFORE any fold-2 fit. Rule (SM-R1): the rating enters S1 as the fixed offset s x c (c = the fold-1-train-fitted coefficient of the rating in an S1 fit with the rating free, raw units; the other S1 features are refit at each s). Among s with fold-1 LL within 2 paired SE (1,000 game-block bootstrap, vs the best-LL s) of the best, pick the s whose fold-1 ES decile-slope R (D32) is closest to 1, i.e. minimal |log R|; exact ties go to the smaller s. Level M1_K500. Fold 1 = train 2021-22 + 2022-23, test 2023-24, 1400 games, 119,651 gated test attempts. S1 is fit on gated rows (ES / PP / PK); EN rows are not in this table. R is the point estimate; old = Q5-Q1 endpoint ratio (reported only).

Fold-1 fitted rating coefficient c = 0.7172 per unit of rating (raw units; arena-factor coefficient 1.114, home 0.038). Corr(rating, arena factor) on ES training rows: -0.040 (road-only construction; the incumbent block ratings were +0.19 / +0.14).

|      s |   ll_per_attempt |   ll_game_vs_best |   se_vs_best | in_2se   |      R |    old | status   | under   |   metric |
|-------:|-----------------:|------------------:|-------------:|:---------|-------:|-------:|:---------|:--------|---------:|
| 0.2500 |          -0.6070 |           -0.0032 |       0.0021 | True     | 0.5521 | 0.4194 | FAIL     | True    |   0.5941 |
| 0.5000 |          -0.6070 |           -0.0009 |       0.0010 | True     | 0.7386 | 0.5981 | FAIL     | True    |   0.3029 |
| 0.7500 |          -0.6070 |            0.0000 |       0.0000 | True     | 0.9381 | 0.7769 | PASS     | True    |   0.0639 |
| 1.0000 |          -0.6070 |           -0.0003 |       0.0010 | True     | 1.1435 | 0.9558 | PASS     | True    |   0.1341 |
| 1.2500 |          -0.6070 |           -0.0020 |       0.0021 | True     | 1.3523 | 1.1348 | FAIL     | True    |   0.3018 |

R 95% game-bootstrap CIs: s=0.25: [0.40, 0.93]; s=0.5: [0.54, 1.20]; s=0.75: [0.69, 1.48]; s=1.0: [0.84, 1.76]; s=1.25: [1.00, 2.07].

- **Selected s = 0.75** (R 0.938; best-LL s 0.75).
- S0 (flat reference) fold-1 ES R = 0.257, CI [0.17, 0.81].
- n_games 1400.
