# SM-R2 step 2: fold-1 s-grid re-selection under the tier level (Lane M2, 2026-10-16)

Generated 2026-10-16 13:04:44 by `scripts/train_miss_v2.py select`. Committed BEFORE any fold-2 fit. Rule as SM-R1 / D32: the shooting team's road-only miss rating enters S1t as the fixed offset s x c (c = the fold-1-train-fitted coefficient of the rating in an S1t fit with the rating free, raw units; the other features are refit at each s). Among s with fold-1 LL within 2 paired SE (1,000 game-block bootstrap vs the best-LL s) of the best, pick the s with fold-1 ES decile-slope R closest to 1 (minimal |log R|; exact ties to the smaller s). Level M2_H30 per (group x tier). Fold 1 = train 2021-22 + 2022-23, test 2023-24, 1400 games, 119,651 gated test attempts. Fit on gated rows; EN rows take S0t.

Fold-1 fitted rating coefficient c = 0.7156 (arena-factor coefficient 1.113, home 0.038). Corr(rating, arena factor) on ES training rows: -0.040.

|      s |   ll_per_attempt |   ll_game_vs_best |   se_vs_best | in_2se   |      R |    old | status   | under   |   metric |
|-------:|-----------------:|------------------:|-------------:|:---------|-------:|-------:|:---------|:--------|---------:|
| 0.2500 |          -0.6070 |           -0.0032 |       0.0021 | True     | 0.5671 | 0.4093 | FAIL     | True    |   0.5672 |
| 0.5000 |          -0.6069 |           -0.0010 |       0.0010 | True     | 0.7464 | 0.5871 | FAIL     | True    |   0.2925 |
| 0.7500 |          -0.6069 |            0.0000 |       0.0000 | True     | 0.9412 | 0.7651 | PASS     | True    |   0.0606 |
| 1.0000 |          -0.6069 |           -0.0003 |       0.0010 | True     | 1.1434 | 0.9431 | PASS     | True    |   0.1340 |
| 1.2500 |          -0.6069 |           -0.0019 |       0.0021 | True     | 1.3495 | 1.1212 | FAIL     | True    |   0.2998 |

R 95% game-bootstrap CIs: s=0.25: [0.41, 0.96]; s=0.5: [0.55, 1.20]; s=0.75: [0.69, 1.48]; s=1.0: [0.84, 1.78]; s=1.25: [0.99, 2.08].

- **Selected s = 0.75** (R 0.941; best-LL s 0.75).
- S0t (flat reference) fold-1 ES R = 0.304, CI [0.20, 1.22].
- n_games 1400.
