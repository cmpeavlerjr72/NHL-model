# EG-R1 part C: shootout, blind fold-2 grade (Lane H8b, 2026-10-21)

Read AFTER the fold-1 table and the S2 scale (s = 1.25) were committed. Fold 2 = 2024-25 regular season.

## S1 bias checks (UNDERPOWERED where 2 x binomial SE exceeds the limit)

| check               |   actual |   predicted |   diff_pp |   limit_pp | PASS   |   binomial_SE_pp | label        |
|:--------------------|---------:|------------:|----------:|-----------:|:-------|-----------------:|:-------------|
| per-attempt success |   0.3294 |      0.3114 |   -1.806  |          2 | True   |           2.0751 | UNDERPOWERED |
| share past round 3  |   0.2468 |      0.3424 |    9.563  |          5 | False  |           4.9131 | UNDERPOWERED |
| winner home share   |   0.5325 |      0.5001 |   -3.2344 |          5 | True   |           5.686  | UNDERPOWERED |

Other S1 quantities: {"shootouts": 77, "attempts": 513, "success_actual": 0.3294, "success_pred": 0.3114, "past3_actual": 0.2468, "past3_pred": 0.3424, "home_win_actual": 0.5325, "home_win_pred": 0.5001, "mean_att_actual": 6.6623, "mean_att_pred": 7.1641, "home_first_actual": 0.9091, "home_first_pred": 0.9081}

## S2 vs S1 (per-attempt LL difference with paired SE; R by D32)

|    s |   n_attempts |   ll_per_attempt |   ll_minus_S1 |     se |        R |     R_lo |   R_hi |   slope_b |   sd_rating | label        |
|-----:|-------------:|-----------------:|--------------:|-------:|---------:|---------:|-------:|----------:|------------:|:-------------|
| 0    |          513 |          -0.6357 |       -0      | 0      | nan      | nan      |    nan |  nan      |      0.0757 | UNDERPOWERED |
| 1.25 |          513 |          -0.636  |       -0.0003 | 0.0021 |   2.3745 |   0.4103 |    inf |    0.4211 |      0.0757 | UNDERPOWERED |

Shooter dispersion (squared deviation of goals from the S1 expectation over its binomial variance, shooters with >= 5 attempts, n = 33): 1.15 (1.0 = no shooter signal; the audit found 1.21 on training seasons). 198 distinct shooters in the season.

Nothing is served from S2 (the shooter order is chosen in game).