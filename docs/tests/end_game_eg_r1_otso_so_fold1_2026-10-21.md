# EG-R1 part C: shootout, fold-1 table (Lane H8b, 2026-10-21)

Training seasons only (2021-22 .. 2023-24); the 2024-25 events were not loaded. Fold 1 = train through 2022-23, test 2023-24 (about 80 shootouts, about 500 attempts: every cell here is UNDERPOWERED). Committed before any fold-2 grade.

## Attempt data (audit rule: SO SHOT / MISS / GOAL / FAILED_SHOT_ATTEMPT, regular season; strict alternation asserted)

| season   |   shootouts |   attempts |   success |   null_shooter |
|:---------|------------:|-----------:|----------:|---------------:|
| 2021-22  |         102 |        747 |    0.2999 |              0 |
| 2022-23  |          95 |        670 |    0.3373 |              0 |
| 2023-24  |          82 |        617 |    0.295  |              0 |

## As-of S1 inputs per season (mean over that season's shootout games): p = M1 K500 over attempts; home-first share = M1, K = 100 shootouts (labelled)

| season   |   p_mean |   home_first_asof |
|:---------|---------:|------------------:|
| 2021-22  |   0.3176 |            0.799  |
| 2022-23  |   0.3171 |            0.8006 |
| 2023-24  |   0.3231 |            0.8494 |

## S1 bias checks on fold 1 (2023-24; the D13 guard; simulated from each shootout game's as-of inputs)

| check               |   actual |   predicted |   diff_pp |   limit_pp | PASS   |   binomial_SE_pp | label        |
|:--------------------|---------:|------------:|----------:|-----------:|:-------|-----------------:|:-------------|
| per-attempt success |   0.295  |      0.3233 |    2.8355 |          2 | False  |           1.8359 | UNDERPOWERED |
| share past round 3  |   0.3415 |      0.3376 |   -0.386  |          5 | True   |           5.2367 | UNDERPOWERED |
| winner home share   |   0.5854 |      0.4997 |   -8.5713 |          5 | False  |           5.4405 | UNDERPOWERED |

## S2 (shooter rating, w 0.7, b 50 attempts, relative to the snapshot mean) on fold 1: per-attempt LL minus S1 with paired SE; R by the D32 recipe (decile buckets of the rating, 1,000 game-block bootstrap)

|    s |   n_attempts |   ll_per_attempt |   ll_minus_S1 |     se |        R |     R_lo |   R_hi |   slope_b |   sd_rating | label        |
|-----:|-------------:|-----------------:|--------------:|-------:|---------:|---------:|-------:|----------:|------------:|:-------------|
| 0    |          617 |          -0.609  |       -0      | 0      | nan      | nan      |    nan |  nan      |      0.0829 | UNDERPOWERED |
| 0.5  |          617 |          -0.6088 |        0.0002 | 0.0008 |   0.3872 |   0.1523 |    inf |    2.583  |      0.0829 | UNDERPOWERED |
| 0.75 |          617 |          -0.6088 |        0.0001 | 0.0012 |   0.5816 |   0.2306 |    inf |    1.7194 |      0.0829 | UNDERPOWERED |
| 1    |          617 |          -0.609  |       -0      | 0.0016 |   0.7781 |   0.3122 |    inf |    1.2852 |      0.0829 | UNDERPOWERED |
| 1.25 |          617 |          -0.6092 |       -0.0003 | 0.002  |   0.9759 |   0.3929 |    inf |    1.0247 |      0.0829 | UNDERPOWERED |
| 1.5  |          617 |          -0.6096 |       -0.0006 | 0.0024 |   1.1747 |   0.4729 |    inf |    0.8513 |      0.0829 | UNDERPOWERED |

S2 scale selected on fold 1: **s = 1.25** (D27: closest |log R| to 1 among cells within 2 SE of the best LL). The LL surface over s is flat; s is fixed here and carried unchanged to fold 2. The rating is the as-of shrunk log-odds relative to the as-of league mean, entered at the fixed scale s ('standardised' in the spec's grid wording means relative to the snapshot mean, not divided by its SD).