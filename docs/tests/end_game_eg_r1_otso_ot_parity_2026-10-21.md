# EG-R1 part B: 3v3 attempt level, training-season parity (Lane H8b, 2026-10-21)

Training seasons only (2021-22 .. 2023-24); the 2024-25 rows were not loaded. Level = attempts per team-hour, regular-season 3v3 team-view rows, both teams. Parity = predicted / actual - 1 per genuine-prior training season; limit 0.5% (SA-R2 form). E and O are reported, never selectable (D35, L29). 2021-22 is burn-in (its prior is its own final rate) and is never judged.

|   fold | season   | level    |   actual |   predicted |   parity | pass_0.5pp   |   team_hours |   games_with_3v3 |   actual_per_team_hour |   pred_per_team_hour |
|-------:|:---------|:---------|---------:|------------:|---------:|:-------------|-------------:|-----------------:|-----------------------:|---------------------:|
|      1 | 2022-23  | M1_K500  |     1523 |     1536.77 |   0.009  | False        |      26.7683 |              297 |                56.8956 |              57.41   |
|      1 | 2022-23  | M1_K2000 |     1523 |     1536.29 |   0.0087 | False        |      26.7683 |              297 |                56.8956 |              57.3922 |
|      1 | 2022-23  | M2_H30   |     1523 |     1537.32 |   0.0094 | False        |      26.7683 |              297 |                56.8956 |              57.4307 |
|      1 | 2022-23  | E        |     1523 |     1530.34 |   0.0048 | True         |      26.7683 |              297 |                56.8956 |              57.1696 |
|      1 | 2022-23  | O        |     1523 |     1523    |   0      | True         |      26.7683 |              297 |                56.8956 |              56.8956 |
|      2 | 2022-23  | M1_K500  |     1523 |     1536.77 |   0.009  | False        |      26.7683 |              297 |                56.8956 |              57.41   |
|      2 | 2022-23  | M1_K2000 |     1523 |     1536.29 |   0.0087 | False        |      26.7683 |              297 |                56.8956 |              57.3922 |
|      2 | 2022-23  | M2_H30   |     1523 |     1537.32 |   0.0094 | False        |      26.7683 |              297 |                56.8956 |              57.4307 |
|      2 | 2022-23  | E        |     1523 |     1530.34 |   0.0048 | True         |      26.7683 |              297 |                56.8956 |              57.1696 |
|      2 | 2022-23  | O        |     1523 |     1523    |   0      | True         |      26.7683 |              297 |                56.8956 |              56.8956 |
|      2 | 2023-24  | M1_K500  |     1338 |     1363.7  |   0.0192 | False        |      24.0244 |              260 |                55.6933 |              56.7631 |
|      2 | 2023-24  | M1_K2000 |     1338 |     1365.38 |   0.0205 | False        |      24.0244 |              260 |                55.6933 |              56.8329 |
|      2 | 2023-24  | M2_H30   |     1338 |     1365.34 |   0.0204 | False        |      24.0244 |              260 |                55.6933 |              56.8312 |
|      2 | 2023-24  | E        |     1338 |     1338    |   0      | True         |      24.0244 |              260 |                55.6933 |              55.6933 |
|      2 | 2023-24  | O        |     1338 |     1338    |   0      | True         |      24.0244 |              260 |                55.6933 |              55.6933 |

Poisson relative SE of the season's 3v3 attempt count (the floor under any parity read):

| season   |   actual |   poisson_se_rel |
|:---------|---------:|-----------------:|
| 2022-23  |     1523 |           0.0256 |
| 2023-24  |     1338 |           0.0273 |

Selection (rule in the experiments.md H8b execution note):

```
{
 "1": {
  "selected": "M1_K2000",
  "how": "fallback: smallest max |parity|, ties within 0.1 pp to the simpler (no construction passes)",
  "max_abs_parity": {
   "M1_K2000": 0.00872789308513755,
   "M1_K500": 0.009041477246979124,
   "M2_H30": 0.009405501348875855
  }
 },
 "2": {
  "selected": "M1_K500",
  "how": "fallback: smallest max |parity|, ties within 0.1 pp to the simpler (no construction passes)",
  "max_abs_parity": {
   "M1_K2000": 0.02046178567502932,
   "M1_K500": 0.019209343038041782,
   "M2_H30": 0.020431452859607457
  }
 }
}
```

No construction passes the 0.5% limit in any judged season (the sampling error of a season's own count is about 2.6%, five times the limit). The fallback rule applies. Fold 2 (the served fold): the smallest max |parity| is M1 K500 (1.92%), 0.13 pp better than M1 K2000 and M2 H30, so **M1 K500 is selected**. Fold 1 (D13 guard): K2000 0.87%, K500 0.90%, within the 0.1 pp tie; the same M1 K500 is carried on fold 1 for consistency (labelled). The 2023-24 over-prediction (+1.9%) is the as-of level lagging a falling 3v3 attempt rate (55.7 vs 56.9 per team-hour); E (the era mean) is in-sample on 2023-24 and not selectable.