# SB-R2 step 1: fold-1 rating-shrinkage selection (Lane B2, 2026-10-16)

Committed BEFORE any fold-2 fit. Rule (SB-R2, D27): cells with fold-1 B1 LL within 2 paired SE (1,000 game-block bootstrap, vs the best-LL cell) of the best; among them minimise max(|log for-ratio|, |log against-ratio|) of the fold-1 ES Q5-Q1 spread ratios; ties within 0.02 go to the larger b. Level M1_K500; booster frozen from SB-R1.

|     b |      w |   ll_per_attempt |   ll_game_vs_best |   se_vs_best | in_2se   |   spread_for |   spread_against |   max_abs_log_ratio |
|------:|-------:|-----------------:|------------------:|-------------:|:---------|-------------:|-----------------:|--------------------:|
|  1000 | 0.5000 |          -0.5913 |           -0.0019 |       0.0021 | True     |       0.7803 |           1.1070 |              0.2481 |
|  1000 | 0.7000 |          -0.5913 |           -0.0023 |       0.0020 | True     |       0.8270 |           1.1771 |              0.1899 |
|  1000 | 0.8500 |          -0.5913 |           -0.0036 |       0.0024 | True     |       0.8244 |           1.4054 |              0.3403 |
|  3000 | 0.5000 |          -0.5913 |            0.0000 |       0.0000 | True     |       0.7345 |           1.2187 |              0.3086 |
|  3000 | 0.7000 |          -0.5913 |           -0.0027 |       0.0015 | True     |       0.7756 |           1.3767 |              0.3197 |
|  3000 | 0.8500 |          -0.5914 |           -0.0064 |       0.0026 | False    |       0.8090 |           1.4395 |              0.3643 |
| 10000 | 0.5000 |          -0.5913 |           -0.0031 |       0.0019 | True     |       0.7338 |           1.3513 |              0.3096 |
| 10000 | 0.7000 |          -0.5914 |           -0.0103 |       0.0037 | False    |       0.8347 |           1.5637 |              0.4471 |
| 10000 | 0.8500 |          -0.5914 |           -0.0180 |       0.0050 | False    |       0.9102 |           1.6402 |              0.4948 |
| 30000 | 0.5000 |          -0.5914 |           -0.0063 |       0.0029 | False    |       0.8010 |           1.4764 |              0.3896 |
| 30000 | 0.7000 |          -0.5914 |           -0.0167 |       0.0049 | False    |       0.8791 |           1.6119 |              0.4774 |
| 30000 | 0.8500 |          -0.5915 |           -0.0272 |       0.0064 | False    |       0.9712 |           1.7903 |              0.5824 |

- Best-LL cell: b 3000, w 0.5 (n_games 1400).
- Min max|log ratio| among in-2SE cells: 0.1899; cells within 0.02: [(1000, 0.7, 0.1899)].
- **Selected: b 1000, w 0.7** (spread for 0.827, against 1.177).
