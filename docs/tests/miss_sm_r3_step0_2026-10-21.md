# SM-R3 step 0: per-season score-bucket coefficients on S0t (Lane M3, 2026-10-21)

Generated 2026-10-21 14:59:32 by `scripts/exp_miss_smr3_step0.py`. TRAINING seasons of fold 2 only (2021-22, 2022-23, 2023-24); fold 2 (2024-25) is not read. Gated rows (ES / PP / PK, goalie in); offset = the S0t logit (M2_H30 tier level, frozen); 10 level intercepts free; unpenalised logistic; coefficients are logit differences vs tied (shooter-view score before the attempt), SE in parentheses.

| season   |      n | trail2+        | trail1         | lead1          | lead2+         |
|:---------|-------:|:---------------|:---------------|:---------------|:---------------|
| 20212022 | 119056 | -0.021 (0.020) | +0.025 (0.019) | +0.030 (0.020) | +0.004 (0.021) |
| 20222023 | 119486 | +0.026 (0.020) | -0.009 (0.019) | -0.005 (0.020) | -0.006 (0.021) |
| 20232024 | 119651 | +0.007 (0.019) | +0.020 (0.018) | -0.030 (0.019) | -0.056 (0.021) |
| pooled   | 358193 | +0.005 (0.011) | +0.012 (0.011) | -0.002 (0.011) | -0.020 (0.012) |

Trend (WLS of the 3 per-season coefficients on season index, inverse-variance weights; 3 points, 1 df, so the z is a weak test):

| bucket   |   slope_per_season |    se |      z |
|:---------|-------------------:|------:|-------:|
| trail2+  |              0.013 | 0.014 |  0.927 |
| trail1   |             -0.002 | 0.013 | -0.138 |
| lead1    |             -0.030 | 0.014 | -2.174 |
| lead2+   |             -0.031 | 0.015 | -2.055 |

- max |z| = 2.17. **A bucket has |z| > 2: the round STOPS here (as-of construction needed, pre-registered separately).**
