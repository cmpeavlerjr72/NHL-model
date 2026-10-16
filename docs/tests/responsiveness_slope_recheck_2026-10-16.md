# Lane R: D32 slope-based responsiveness gate, re-check of the stage-1 and stage-3 incumbents (2026-10-16)

Run 2026-10-16 12:17:10 to 12:17:16 -0400 (6 s; existing outputs only, no new sim). Code: `src/nhl_sim/eval/responsiveness.py` (`slope_ratio`), tests `tests/test_responsiveness.py` (4 pass: calibrated R about 1; over-responding R > 1; bootstrap resamples games not rows; UNDERPOWERED flag), driver `scripts/diag_responsiveness_slope_recheck.py`. Raw numbers: `results/responsiveness_slope_recheck.json` (gitignored).

Method (D32): deciles of the as-of rating (rank-based, over team-games); b = n-weighted LS slope of actual bucket means on sim bucket means; R = 1/b; band [0.8, 1.2] on the point estimate; 1,000-resample game-block bootstrap (buckets fixed at the point-estimate deciles); CI wider than the band = UNDERPOWERED. Sim = mean over 200 seeds per team-game. Stage 3 bucket values are rates (attempts per 60, exposure-weighted). Sanity: the reported old Q5-Q1 endpoint ratios reproduce the earlier reports (stage 1: 1.10/1.11 RS, 1.13/1.19 all, D18; stage 3: 1.135/1.122, D20).

## Summary (PM rules; no status changed here)

| Incumbent | Cell | R | 95% CI | old Q5-Q1 | Band | Powered |
|---|---|---|---|---|---|---|
| Stage 1, PP opps conferred | RS, own taken | 1.181 | 0.893..1.742 | 1.099 | PASS | UNDERPOWERED |
| Stage 1 | RS, opp drawn | 1.182 | 0.726..2.809 | 1.107 | PASS | UNDERPOWERED |
| Stage 1 | all games, own taken | 1.180 | 0.889..1.731 | 1.132 | PASS | UNDERPOWERED |
| Stage 1 | all games, opp drawn | 1.187 | 0.735..2.973 | 1.185 | PASS | UNDERPOWERED |
| Stage 3, 5v5 attempts/60 | overall, own | 1.142 | 1.010..1.328 | 1.135 | PASS | ok (CI width 0.32 < 0.4) |
| Stage 3 | overall, opp | 1.170 | 1.021..1.377 | 1.122 | PASS | ok (0.36 < 0.4) |
| Stage 3 | RS, own | 1.165 | 1.024..1.364 | 1.138 | PASS | ok (0.34) |
| Stage 3 | RS, opp | 1.174 | 1.020..1.411 | 1.125 | PASS | ok (0.39) |

Plain reading:
- All 8 cells PASS on the point estimate (the D18 rule). Zero cells FAIL.
- Stage 1: all four R values sit at 1.18 to 1.19, 0.01 to 0.02 inside the 1.2 line, and every CI is wide (upper end 1.73 to 2.97, UNDERPOWERED). The slope measure is slightly higher than the endpoint measure in RS (1.18 vs 1.10), i.e. less favourable. The data cannot distinguish R=1 from R=1.7 for the drawn-rating cells. Edge-of-band, not clean.
- Stage 3: the four cells are powered (CI width 0.32 to 0.39) and every lower bound is above 1.0 (1.01 to 1.02): the sim over-responds by about 14 to 17%, statistically distinguishable from calibrated, while the point estimate stays inside the band. The upper CI ends (1.33 to 1.41) exceed 1.2.

Decile tables (n, sim mean, actual mean) follow for every cell.

## Stage 1 H3''-LC2 + T2: PP opportunities conferred (200 seeds, sim = mean over seeds per team-game)

### regular season, by own taken-rating (n team-games 2624, games 1312): R=1.181 (CI 0.893..1.742) b=0.847 old Q5-Q1=1.099 PASS UNDERPOWERED

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 263.000 |  2.404 |    2.209 |
|  2 | 262.000 |  2.473 |    2.397 |
|  3 | 262.000 |  2.530 |    2.370 |
|  4 | 263.000 |  2.585 |    2.665 |
|  5 | 262.000 |  2.563 |    2.557 |
|  6 | 262.000 |  2.590 |    2.660 |
|  7 | 263.000 |  2.751 |    2.684 |
|  8 | 262.000 |  2.815 |    2.656 |
|  9 | 262.000 |  2.841 |    2.626 |
| 10 | 263.000 |  2.952 |    2.814 |

### regular season, by opponent drawn-rating (n team-games 2624, games 1312): R=1.182 (CI 0.726..2.809) b=0.846 old Q5-Q1=1.107 PASS UNDERPOWERED

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 263.000 |  2.540 |    2.331 |
|  2 | 262.000 |  2.516 |    2.485 |
|  3 | 262.000 |  2.623 |    2.622 |
|  4 | 263.000 |  2.605 |    2.574 |
|  5 | 262.000 |  2.641 |    2.534 |
|  6 | 262.000 |  2.624 |    2.580 |
|  7 | 263.000 |  2.664 |    2.601 |
|  8 | 262.000 |  2.674 |    2.592 |
|  9 | 262.000 |  2.778 |    2.542 |
| 10 | 263.000 |  2.839 |    2.779 |

### all games, by own taken-rating (n team-games 2796, games 1398): R=1.180 (CI 0.889..1.731) b=0.847 old Q5-Q1=1.132 PASS UNDERPOWERED

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 280.000 |  2.413 |    2.211 |
|  2 | 280.000 |  2.487 |    2.461 |
|  3 | 279.000 |  2.546 |    2.412 |
|  4 | 280.000 |  2.605 |    2.614 |
|  5 | 279.000 |  2.572 |    2.642 |
|  6 | 280.000 |  2.603 |    2.621 |
|  7 | 279.000 |  2.759 |    2.724 |
|  8 | 280.000 |  2.823 |    2.664 |
|  9 | 279.000 |  2.851 |    2.638 |
| 10 | 280.000 |  2.982 |    2.857 |

### all games, by opponent drawn-rating (n team-games 2796, games 1398): R=1.187 (CI 0.735..2.973) b=0.843 old Q5-Q1=1.185 PASS UNDERPOWERED

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 280.000 |  2.544 |    2.332 |
|  2 | 280.000 |  2.532 |    2.561 |
|  3 | 279.000 |  2.632 |    2.627 |
|  4 | 280.000 |  2.626 |    2.593 |
|  5 | 279.000 |  2.652 |    2.548 |
|  6 | 280.000 |  2.645 |    2.582 |
|  7 | 279.000 |  2.681 |    2.613 |
|  8 | 280.000 |  2.682 |    2.614 |
|  9 | 279.000 |  2.792 |    2.556 |
| 10 | 280.000 |  2.855 |    2.818 |

## Stage 3 A3g-c on H3''-LC2 + T2: closed-loop 5v5 attempts per 60 (200 seeds, overall RS+PO)

### overall (RS+PO), by own ES attempts-for rating (n team-games 2796, games 1398): R=1.142 (CI 1.010..1.328) b=0.875 old Q5-Q1=1.135 PASS

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 280.000 | 53.041 |   53.920 |
|  2 | 280.000 | 54.067 |   54.712 |
|  3 | 279.000 | 55.763 |   55.272 |
|  4 | 280.000 | 57.386 |   57.711 |
|  5 | 279.000 | 58.601 |   58.147 |
|  6 | 280.000 | 59.310 |   58.517 |
|  7 | 279.000 | 59.542 |   59.230 |
|  8 | 280.000 | 61.203 |   60.054 |
|  9 | 279.000 | 62.365 |   62.160 |
| 10 | 280.000 | 65.974 |   65.159 |

### overall (RS+PO), by opponent ES attempts-against rating (n team-games 2796, games 1398): R=1.170 (CI 1.021..1.377) b=0.855 old Q5-Q1=1.122 PASS

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 280.000 | 53.204 |   52.920 |
|  2 | 280.000 | 55.280 |   54.841 |
|  3 | 279.000 | 56.621 |   57.388 |
|  4 | 280.000 | 57.286 |   57.711 |
|  5 | 279.000 | 58.153 |   58.575 |
|  6 | 280.000 | 59.282 |   60.230 |
|  7 | 279.000 | 59.951 |   57.977 |
|  8 | 280.000 | 60.214 |   60.501 |
|  9 | 279.000 | 62.185 |   61.119 |
| 10 | 280.000 | 65.068 |   63.371 |

### regular season, by own ES attempts-for rating (n team-games 2624, games 1312): R=1.165 (CI 1.024..1.364) b=0.858 old Q5-Q1=1.138 PASS

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 263.000 | 52.889 |   53.966 |
|  2 | 262.000 | 54.090 |   54.559 |
|  3 | 262.000 | 55.554 |   55.536 |
|  4 | 263.000 | 57.271 |   57.203 |
|  5 | 262.000 | 58.350 |   58.255 |
|  6 | 262.000 | 59.224 |   58.914 |
|  7 | 263.000 | 59.527 |   58.838 |
|  8 | 262.000 | 61.041 |   59.764 |
|  9 | 262.000 | 62.258 |   62.224 |
| 10 | 263.000 | 65.365 |   64.443 |

### regular season, by opponent ES attempts-against rating (n team-games 2624, games 1312): R=1.174 (CI 1.020..1.411) b=0.852 old Q5-Q1=1.125 PASS

|    |       n |   pred |   actual |
|---:|--------:|-------:|---------:|
|  1 | 263.000 | 52.720 |   52.807 |
|  2 | 262.000 | 54.864 |   54.273 |
|  3 | 262.000 | 56.365 |   57.451 |
|  4 | 263.000 | 57.254 |   57.657 |
|  5 | 262.000 | 58.376 |   59.068 |
|  6 | 262.000 | 59.150 |   59.677 |
|  7 | 263.000 | 59.755 |   58.037 |
|  8 | 262.000 | 59.939 |   59.985 |
|  9 | 262.000 | 61.897 |   60.703 |
| 10 | 263.000 | 65.204 |   63.734 |

