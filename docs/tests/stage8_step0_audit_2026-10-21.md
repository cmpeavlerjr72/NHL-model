# Stage 7-8 step-0 audit (INV-65), 2026-10-21

Lane Z (Sonnet). Read-only empirical audit to ground the stage 7 and stage 8 pre-registrations. No model is fit, nothing gates. Training seasons only: 2021-22, 2022-23, 2023-24. 2024-25 (fold-2 holdout) was not requested from the loader at any point, 2025-26 is sealed (`NHL_UNSEAL_2025` not set). All data through `src/nhl_sim/data/load.py`. Regular season (RS) and playoffs (PO) are reported separately; any cell with fewer than 100 events is labelled UNDERPOWERED in its table.

Reproduce (about 1 minute total on the home box; no step projected near 15 minutes, so no box request):

```
.venv/Scripts/python.exe scripts/diag_stage8_step0_a_pulls.py     # items 1, 4   (46 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_b_ot_so.py     # items 2, 3   (1 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_c_reb_fo.py    # item 5       (3 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_d_gates.py     # item 6       (1 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_e_assemble.py  # this document
```

Wall clock: started 2026-10-21 13:13; compute steps 13:18 to 13:25 (part A 46 s, B/C/D under 5 s each); intermediate tables under `results/stage8_step0/` (gitignored).

## Headline numbers that constrain the stage-8 spec

| quantity | 2021-22 RS | 2022-23 RS | 2023-24 RS | note |
|---|---|---|---|---|
| tied after regulation (reg tie rate) | 21.95% | 23.02% | 20.73% | G7 targets match (section 6). PO 16.9 / 27.3 / 18.2% (UNDERPOWERED, 88-89 games) |
| tied games ending in an OT goal / in a shootout | 64.6 / 35.4% | 68.5 / 31.5% | 69.9 / 30.1% | pooled 583 OT goals, 279 shootouts (32.4%) |
| shootout share of all games | 7.77% | 7.24% | 6.25% | |
| 3v3 goals per 60 (both teams combined) | 12.2 | 12.9 | 13.2 | pooled 12.76 (495 goals, 38.8 h of exposure); per team about 6.4. Attempts 113.0 and SOG 73.4 per 60 combined |
| OT time at 3v3 | 88.5% | 83.4% | 83.7% | rest is mostly 4v3 (10%, 14.3 goals/60, 68 goals) and 4v4 (4%) after OT penalties (23-29 per 100 OT games) |
| EN goals against per game (goals into an empty net) | 0.363 | 0.334 | 0.341 | PO 0.49 / 0.28 / 0.43 (UNDERPOWERED) |
| EN goals for per game (own goalie pulled) | 0.155 | 0.155 | 0.163 | |
| pulled time per game (both teams, all pulls) | 72.6 s | 68.4 s | 72.5 s | of which 11 to 12 s is delayed-penalty pulls |
| first pull while trailing by 1, 5v5, seconds left (median, IQR) | 109 (88-134) | 113 (90-134) | 113 (92-138) | trail 2: about 175 s; trail 3+: about 250 s |
| trailing-by-1 team has pulled by 2:00 left | 99.5% | 99.8% | 100% | by 5:00 left: 88.5 / 88.4 / 88.4% |
| relief goalie appearances per 100 team-games | 7.5 | 6.2 | 6.7 | 197 / 163 / 176 appearances; about 60% when down 3 or more |
| share of SOG faced by a relief goalie | 3.20% | 2.45% | 3.10% | pooled RS 2.92% (Lane E2 fold-2 figure of 2.4% is at the low end of this range) |
| shootout per-attempt success | 30.0% | 33.7% | 29.5% | pooled 31.1% (2,034 attempts); no home/away or round-order effect detectable |
| shootouts going past round 3 | 30.4% | 34.7% | 34.1% | pooled 33%; home team shoots first in 80 to 90% |

Data limitations that bind the spec (details in the sections):

1. No actual goalie-pull record exists. Pulls are inferred from gaps in the goalie shift chart (confirmed by the pbp goalie flag in 96.4% of pulls in 2021-22 and 99.5% / 99.95% afterwards; 2021-22 has more spurious gaps). The situation-code goalie flag alone is not a usable pull record: it is observed only at events and also fires on PERIOD_END / GAME_END events (it counts 25% more team-games with a pull than the shift gaps do, mostly end-of-period events; table 1j).
2. The pbp `DELAYED_PENALTY` event is logged for only 42-62% of delayed-penalty pulls (its rate roughly doubled from 2022-23 to 2023-24); delayed-penalty pulls are identified mostly from the pull ending at an opponent penalty call.
3. Strength state in the situation code changes only at events, so OT exposure per state is bracketed (prev-event vs next-event attribution), not exact; the bracket is narrow for 3v3 (+/- 0.1 goals/60) and wide for 4v3.
4. No shootout round index in the pbp (round is derived from alternation, which holds in 100% of shootouts). Shootout misses are typed `missed-shot` / `shot-on-goal` in 2021-22 and partly `failed-shot-attempt` afterwards.
5. A per-shooter shootout model is thin: 383 distinct shooters, 154 with >= 5 attempts, 72 with >= 10 (50% of attempts), 6 with >= 20. Shooter dispersion is 1.21 times binomial; goalie dispersion 0.91 (no goalie signal).
6. The rebound proxy is recording-era sensitive: its share of unblocked attempts rises 7.2% to 8.9% to 10.2% across the three seasons while the goal rate on proxies falls 17.9% to 13.8% to 11.2% (non-rebound goal rate flat at 6.4 to 6.6%). This matches the shot-recording drift flagged in the data audit; any rebound feature needs per-season centring or a recording-era term.
7. The starter flag is post-game data. Whether a relief change is an injury or a performance pull is not recorded.

## Definitions used throughout

- Pull = a gap of at least 3 s inside a period (shootout excluded) in which a team has no goalie shift on the ice (union of that team's goalie shifts, period windows from the PERIOD_START / PERIOD_END events). Gap-length sensitivity is in 1k. A goalie change (second goalie id) shows a gap of 0 s in all but 3 cases, so it is not mistaken for a pull.
- Failure cases of the rule: (a) shifts have 1 s resolution so start / end times are +/- 1 s; (b) 2021-22 shows 3.6% unconfirmed gaps (shift-chart noise); (c) simultaneous pulls by both teams are not separated; (d) the pre-pull strength state comes from the last event with the goalie in net, which can predate a penalty that began after it; (e) the deficit counts goals at or before the pull second, so a pull at the same second as a goal is assigned the post-goal score.
- Pull end cause: a goal within 1 s of the return (goal_for / goal_against; any goal against while pulled is an empty-net goal), the period end, a stoppage / faceoff / penalty event within 1 s, or in-play return.
- Delayed-penalty (DP) pull: a `DELAYED_PENALTY` event owned by the opponent within [start - 3 s, end + 1 s], or the pull ends within 3 s of a PENALTY called on the opponent. Exception: a team trailing in the last 5:00 of P3 is treated as an EN-style pull whatever follows (about 3.6% of such pulls end at an opponent penalty call and cannot be separated).
- EN goals per game follows the G7 gate: non-shootout goals with no goalie id (goals into an empty net), both teams.


## 1 and 4. Goalie pull, empty net, and in-game goalie changes (part A tables; section numbers 1x are item 1, 4x are item 4)

### 1.0 Shift-gap length distribution

Independent confirmation: share of shift-derived pulls (gap >= 3 s) with at least one pbp event inside [start, end] whose own-goalie flag in the situation code is 0:

|    | season   | game_type   |   n_pulls |   share_confirmed |
|---:|:---------|:------------|----------:|------------------:|
|  0 | 2021-22  | RS          |      2019 |            0.9638 |
|  1 | 2021-22  | PO          |       133 |            1.0000 |
|  2 | 2022-23  | RS          |      2010 |            0.9950 |
|  3 | 2022-23  | PO          |       125 |            0.9920 |
|  4 | 2023-24  | RS          |      2092 |            0.9995 |
|  5 | 2023-24  | PO          |       152 |            1.0000 |
Goalie-shift gaps within a period (no goalie shift on the ice for a team; period windows from PERIOD_START / PERIOD_END events, shootout excluded), all training seasons and both types, gaps > 0 s:

|        |   (0, 1] |   (1, 2] |   (2, 3] |   (3, 5] |   (5, 10] |   (10, 20] |   (20, 40] |   (40, 80] |   (80, 200] |   (200, 5000] |
|:-------|---------:|---------:|---------:|---------:|----------:|-----------:|-----------:|-----------:|------------:|--------------:|
| n_gaps |      107 |      180 |      198 |      415 |       823 |       1261 |       1366 |       1195 |        1205 |            68 |

### 1a. Seconds remaining in regulation at the first pull per team-game, by deficit at the pull and penalty-on: pulls NOT overlapping a delayed-penalty event

`penalty_on` = pre-pull skater counts not 5v5 (taken from the last event with the goalie still in net). Deficit = pulling team's goals against minus for, goals at or before the pull second.

|    | season   | type   | deficit   | penalty_on   |   n | flag         |    p10 |    p25 |   median |    p75 |    p90 |   mean |
|---:|:---------|:-------|:----------|:-------------|----:|:-------------|-------:|-------:|---------:|-------:|-------:|-------:|
|  0 | 2021-22  | RS     | leading   | False        |   6 | UNDERPOWERED | 1072.5 | 1291.2 |   1870.0 | 2406.0 | 2599.0 | 1847.2 |
|  1 | 2021-22  | RS     | leading   | True         |   2 | UNDERPOWERED | 2035.7 | 2120.8 |   2262.5 | 2404.2 | 2489.3 | 2262.5 |
|  2 | 2021-22  | RS     | tied      | False        |   3 | UNDERPOWERED |  488.8 | 1205.5 |   2400.0 | 2612.5 | 2740.0 | 1745.3 |
|  3 | 2021-22  | RS     | tied      | True         |   4 | UNDERPOWERED |  298.4 |  477.5 |   1490.0 | 2635.8 | 3054.7 | 1623.2 |
|  4 | 2021-22  | RS     | trail1    | False        | 398 |              |   62.0 |   88.0 |    109.0 |  134.0 |  155.3 |  123.2 |
|  5 | 2021-22  | RS     | trail1    | True         |  40 | UNDERPOWERED |   42.1 |   80.5 |    105.5 |  142.8 |  179.2 |  203.2 |
|  6 | 2021-22  | RS     | trail2    | False        | 263 |              |  102.0 |  146.0 |    178.0 |  215.5 |  248.8 |  194.0 |
|  7 | 2021-22  | RS     | trail2    | True         |  28 | UNDERPOWERED |   44.8 |  107.0 |    175.5 |  236.0 |  279.5 |  174.7 |
|  8 | 2021-22  | RS     | trail3+   | False        |  69 | UNDERPOWERED |  140.4 |  196.0 |    250.0 |  315.0 |  437.6 |  265.3 |
|  9 | 2021-22  | RS     | trail3+   | True         |  16 | UNDERPOWERED |  134.5 |  165.2 |    299.5 |  455.0 |  738.5 |  373.4 |
| 10 | 2021-22  | PO     | trail1    | False        |  29 | UNDERPOWERED |   36.2 |   79.0 |    112.0 |  134.0 |  147.4 |  101.7 |
| 11 | 2021-22  | PO     | trail1    | True         |   3 | UNDERPOWERED |   62.8 |   74.5 |     94.0 |  109.5 |  118.8 |   91.3 |
| 12 | 2021-22  | PO     | trail2    | False        |  16 | UNDERPOWERED |  146.5 |  161.0 |    190.5 |  209.2 |  250.5 |  193.0 |
| 13 | 2021-22  | PO     | trail3+   | False        |  13 | UNDERPOWERED |  121.6 |  175.0 |    272.0 |  292.0 |  348.0 |  248.5 |
| 14 | 2021-22  | PO     | trail3+   | True         |   4 | UNDERPOWERED |  258.4 |  298.0 |    339.0 |  378.0 |  414.0 |  337.0 |
| 15 | 2022-23  | RS     | leading   | False        |   8 | UNDERPOWERED |  660.9 | 1089.0 |   1310.0 | 1965.8 | 2609.4 | 1541.1 |
| 16 | 2022-23  | RS     | leading   | True         |   1 | UNDERPOWERED | 2280.0 | 2280.0 |   2280.0 | 2280.0 | 2280.0 | 2280.0 |
| 17 | 2022-23  | RS     | tied      | False        |   9 | UNDERPOWERED |   29.6 |  199.0 |   1304.0 | 3072.0 | 3527.2 | 1700.7 |
| 18 | 2022-23  | RS     | tied      | True         |   1 | UNDERPOWERED | 1668.0 | 1668.0 |   1668.0 | 1668.0 | 1668.0 | 1668.0 |
| 19 | 2022-23  | RS     | trail1    | False        | 388 |              |   69.7 |   90.0 |    113.0 |  134.2 |  156.0 |  136.4 |
| 20 | 2022-23  | RS     | trail1    | True         |  40 | UNDERPOWERED |   48.8 |   58.0 |     88.0 |  122.8 |  149.3 |   92.4 |
| 21 | 2022-23  | RS     | trail2    | False        | 242 |              |  104.2 |  140.5 |    170.5 |  208.8 |  251.0 |  177.8 |
| 22 | 2022-23  | RS     | trail2    | True         |  32 | UNDERPOWERED |   76.3 |  123.0 |    157.0 |  228.5 |  294.5 |  184.4 |
| 23 | 2022-23  | RS     | trail3+   | False        |  73 | UNDERPOWERED |  153.6 |  189.0 |    249.0 |  312.0 |  387.0 |  270.4 |
| 24 | 2022-23  | RS     | trail3+   | True         |  19 | UNDERPOWERED |  168.0 |  213.5 |    254.0 |  307.0 |  330.0 |  256.4 |
| 25 | 2022-23  | PO     | trail1    | False        |  21 | UNDERPOWERED |   71.0 |   83.0 |    110.0 |  121.0 |  149.0 |  107.3 |
| 26 | 2022-23  | PO     | trail1    | True         |   1 | UNDERPOWERED |  144.0 |  144.0 |    144.0 |  144.0 |  144.0 |  144.0 |
| 27 | 2022-23  | PO     | trail2    | False        |  17 | UNDERPOWERED |  152.8 |  169.0 |    197.0 |  229.0 |  258.0 |  199.6 |
| 28 | 2022-23  | PO     | trail2    | True         |   1 | UNDERPOWERED |  119.0 |  119.0 |    119.0 |  119.0 |  119.0 |  119.0 |
| 29 | 2022-23  | PO     | trail3+   | False        |  13 | UNDERPOWERED |  180.6 |  244.0 |    283.0 |  403.0 |  902.8 |  491.2 |
| 30 | 2022-23  | PO     | trail3+   | True         |   2 | UNDERPOWERED |  317.5 |  319.8 |    323.5 |  327.2 |  329.5 |  323.5 |
| 31 | 2023-24  | RS     | leading   | False        |   9 | UNDERPOWERED | 1335.8 | 1423.0 |   1789.0 | 2301.0 | 3020.0 | 1993.9 |
| 32 | 2023-24  | RS     | leading   | True         |   1 | UNDERPOWERED | 2403.0 | 2403.0 |   2403.0 | 2403.0 | 2403.0 | 2403.0 |
| 33 | 2023-24  | RS     | tied      | False        |   7 | UNDERPOWERED |  545.8 |  850.5 |   1330.0 | 1918.0 | 2795.0 | 1491.4 |
| 34 | 2023-24  | RS     | trail1    | False        | 382 |              |   67.0 |   92.0 |    113.0 |  138.0 |  166.0 |  135.3 |
| 35 | 2023-24  | RS     | trail1    | True         |  36 | UNDERPOWERED |   41.5 |   73.5 |    106.0 |  131.2 |  143.0 |  100.2 |
| 36 | 2023-24  | RS     | trail2    | False        | 282 |              |  116.0 |  145.0 |    176.5 |  215.0 |  253.8 |  193.2 |
| 37 | 2023-24  | RS     | trail2    | True         |  33 | UNDERPOWERED |   86.4 |  100.0 |    175.0 |  216.0 |  280.4 |  187.8 |
| 38 | 2023-24  | RS     | trail3+   | False        |  59 | UNDERPOWERED |  142.2 |  173.0 |    255.0 |  331.0 |  462.2 |  268.8 |
| 39 | 2023-24  | RS     | trail3+   | True         |  22 | UNDERPOWERED |  170.6 |  258.8 |    341.5 |  409.5 |  471.6 |  336.6 |
| 40 | 2023-24  | PO     | tied      | False        |   1 | UNDERPOWERED |  458.0 |  458.0 |    458.0 |  458.0 |  458.0 |  458.0 |
| 41 | 2023-24  | PO     | trail1    | False        |  37 | UNDERPOWERED |   87.6 |  108.0 |    127.0 |  150.0 |  168.0 |  124.5 |
| 42 | 2023-24  | PO     | trail1    | True         |   1 | UNDERPOWERED |   57.0 |   57.0 |     57.0 |   57.0 |   57.0 |   57.0 |
| 43 | 2023-24  | PO     | trail2    | False        |  23 | UNDERPOWERED |  109.4 |  130.0 |    172.0 |  206.5 |  223.0 |  167.0 |
| 44 | 2023-24  | PO     | trail2    | True         |   1 | UNDERPOWERED |  353.0 |  353.0 |    353.0 |  353.0 |  353.0 |  353.0 |
| 45 | 2023-24  | PO     | trail3+   | False        |   4 | UNDERPOWERED |  165.1 |  199.8 |    230.0 |  263.2 |  303.3 |  233.0 |
| 46 | 2023-24  | PO     | trail3+   | True         |   3 | UNDERPOWERED |  205.8 |  214.5 |    229.0 |  716.0 | 1008.2 |  544.0 |

### 1a. Seconds remaining in regulation at the first pull per team-game, by deficit at the pull and penalty-on: all pulls including delayed-penalty overlaps

`penalty_on` = pre-pull skater counts not 5v5 (taken from the last event with the goalie still in net). Deficit = pulling team's goals against minus for, goals at or before the pull second.

|    | season   | type   | deficit   | penalty_on   |   n | flag         |    p10 |    p25 |   median |    p75 |    p90 |   mean |
|---:|:---------|:-------|:----------|:-------------|----:|:-------------|-------:|-------:|---------:|-------:|-------:|-------:|
|  0 | 2021-22  | RS     | leading   | False        | 172 |              |  571.2 | 1027.0 |   1831.5 | 2513.8 | 2937.7 | 1788.3 |
|  1 | 2021-22  | RS     | leading   | True         |  17 | UNDERPOWERED |  776.8 | 1011.0 |   2247.0 | 3029.0 | 3167.0 | 2038.2 |
|  2 | 2021-22  | RS     | tied      | False        | 269 |              |  808.2 | 1526.0 |   2504.0 | 3149.0 | 3409.4 | 2295.3 |
|  3 | 2021-22  | RS     | tied      | True         |  10 | UNDERPOWERED | 1471.9 | 2591.2 |   2773.0 | 3125.5 | 3208.5 | 2609.7 |
|  4 | 2021-22  | RS     | trail1    | False        | 422 |              |   72.0 |   98.0 |    130.0 | 1170.5 | 2578.4 |  715.5 |
|  5 | 2021-22  | RS     | trail1    | True         |  34 | UNDERPOWERED |   51.5 |   83.0 |    137.5 | 1223.8 | 2848.6 |  747.8 |
|  6 | 2021-22  | RS     | trail2    | False        | 246 |              |  111.0 |  154.2 |    202.0 |  335.5 | 1586.0 |  504.3 |
|  7 | 2021-22  | RS     | trail2    | True         |  26 | UNDERPOWERED |   48.0 |  148.8 |    217.5 |  295.2 | 1338.5 |  433.3 |
|  8 | 2021-22  | RS     | trail3+   | False        |  96 | UNDERPOWERED |  190.5 |  250.8 |    535.5 | 1439.0 | 2075.5 |  880.7 |
|  9 | 2021-22  | RS     | trail3+   | True         |  12 | UNDERPOWERED |  133.3 |  165.2 |    316.5 |  514.2 | 1009.4 |  456.4 |
| 10 | 2021-22  | PO     | leading   | False        |   9 | UNDERPOWERED | 1392.4 | 1586.0 |   2356.0 | 3104.0 | 3146.8 | 2256.3 |
| 11 | 2021-22  | PO     | leading   | True         |   4 | UNDERPOWERED |  374.3 |  694.2 |    948.0 | 1158.2 | 1399.9 |  904.5 |
| 12 | 2021-22  | PO     | tied      | False        |  14 | UNDERPOWERED | 1603.2 | 2639.0 |   2959.0 | 3275.5 | 3413.1 | 2681.0 |
| 13 | 2021-22  | PO     | tied      | True         |   2 | UNDERPOWERED | 2855.5 | 2908.8 |   2997.5 | 3086.2 | 3139.5 | 2997.5 |
| 14 | 2021-22  | PO     | trail1    | False        |  27 | UNDERPOWERED |   78.6 |   91.0 |    120.0 |  145.5 |  536.2 |  287.3 |
| 15 | 2021-22  | PO     | trail1    | True         |   2 | UNDERPOWERED |   97.1 |  101.8 |    109.5 |  117.2 |  121.9 |  109.5 |
| 16 | 2021-22  | PO     | trail2    | False        |  15 | UNDERPOWERED |  159.8 |  185.0 |    228.0 |  410.5 | 1515.2 |  510.7 |
| 17 | 2021-22  | PO     | trail2    | True         |   1 | UNDERPOWERED | 2284.0 | 2284.0 |   2284.0 | 2284.0 | 2284.0 | 2284.0 |
| 18 | 2021-22  | PO     | trail3+   | False        |  12 | UNDERPOWERED |  176.6 |  218.8 |    290.5 |  379.8 | 1166.2 |  489.8 |
| 19 | 2021-22  | PO     | trail3+   | True         |   3 | UNDERPOWERED |  257.2 |  295.0 |    358.0 |  398.0 |  422.0 |  342.7 |
| 20 | 2022-23  | RS     | leading   | False        | 205 |              |  680.4 | 1071.0 |   1747.0 | 2551.0 | 2945.4 | 1809.7 |
| 21 | 2022-23  | RS     | leading   | True         |  19 | UNDERPOWERED |  786.8 |  976.5 |   1410.0 | 2352.0 | 2480.6 | 1548.2 |
| 22 | 2022-23  | RS     | tied      | False        | 254 |              |  820.9 | 1883.0 |   2639.5 | 3140.0 | 3436.7 | 2378.9 |
| 23 | 2022-23  | RS     | tied      | True         |  15 | UNDERPOWERED |  790.4 | 1316.5 |   1913.0 | 2561.5 | 2924.6 | 1920.5 |
| 24 | 2022-23  | RS     | trail1    | False        | 427 |              |   82.6 |  105.0 |    136.0 | 1357.0 | 2585.8 |  769.3 |
| 25 | 2022-23  | RS     | trail1    | True         |  37 | UNDERPOWERED |   50.8 |   73.0 |    103.0 |  153.0 | 1856.6 |  463.5 |
| 26 | 2022-23  | RS     | trail2    | False        | 248 |              |  113.0 |  153.0 |    201.0 |  781.2 | 1893.7 |  595.0 |
| 27 | 2022-23  | RS     | trail2    | True         |  21 | UNDERPOWERED |   76.0 |   93.0 |    195.0 |  350.0 |  950.0 |  392.1 |
| 28 | 2022-23  | RS     | trail3+   | False        | 101 |              |  178.0 |  224.0 |    325.0 | 1145.0 | 1603.0 |  684.3 |
| 29 | 2022-23  | RS     | trail3+   | True         |  17 | UNDERPOWERED |  158.0 |  222.0 |    260.0 |  323.0 |  999.0 |  412.1 |
| 30 | 2022-23  | PO     | leading   | False        |  13 | UNDERPOWERED |  921.4 | 1505.0 |   2277.0 | 2719.0 | 3203.4 | 2125.7 |
| 31 | 2022-23  | PO     | leading   | True         |   1 | UNDERPOWERED |  546.0 |  546.0 |    546.0 |  546.0 |  546.0 |  546.0 |
| 32 | 2022-23  | PO     | tied      | False        |  15 | UNDERPOWERED | 1699.0 | 2144.5 |   2731.0 | 3221.0 | 3341.8 | 2544.3 |
| 33 | 2022-23  | PO     | tied      | True         |   2 | UNDERPOWERED | 1938.5 | 2032.2 |   2188.5 | 2344.8 | 2438.5 | 2188.5 |
| 34 | 2022-23  | PO     | trail1    | False        |  25 | UNDERPOWERED |   75.0 |   96.0 |    121.0 | 1325.0 | 2717.4 |  807.4 |
| 35 | 2022-23  | PO     | trail1    | True         |   1 | UNDERPOWERED |  144.0 |  144.0 |    144.0 |  144.0 |  144.0 |  144.0 |
| 36 | 2022-23  | PO     | trail2    | False        |  13 | UNDERPOWERED |  157.0 |  170.0 |    197.0 |  234.0 |  265.6 |  266.5 |
| 37 | 2022-23  | PO     | trail2    | True         |   1 | UNDERPOWERED |  119.0 |  119.0 |    119.0 |  119.0 |  119.0 |  119.0 |
| 38 | 2022-23  | PO     | trail3+   | False        |  14 | UNDERPOWERED |  183.4 |  263.5 |    307.5 |  877.5 | 1965.0 |  700.6 |
| 39 | 2022-23  | PO     | trail3+   | True         |   1 | UNDERPOWERED |  331.0 |  331.0 |    331.0 |  331.0 |  331.0 |  331.0 |
| 40 | 2023-24  | RS     | leading   | False        | 214 |              |  559.2 | 1060.2 |   1856.0 | 2509.5 | 2969.7 | 1798.8 |
| 41 | 2023-24  | RS     | leading   | True         |  11 | UNDERPOWERED |  562.0 | 1050.5 |   1596.0 | 1860.5 | 2118.0 | 1482.1 |
| 42 | 2023-24  | RS     | tied      | False        | 283 |              |  767.2 | 1679.5 |   2672.0 | 3156.0 | 3432.6 | 2372.9 |
| 43 | 2023-24  | RS     | tied      | True         |  16 | UNDERPOWERED |  497.5 | 1703.2 |   2805.5 | 2914.0 | 3103.0 | 2259.0 |
| 44 | 2023-24  | RS     | trail1    | False        | 411 |              |   77.0 |  104.0 |    140.0 | 1310.5 | 2790.0 |  773.8 |
| 45 | 2023-24  | RS     | trail1    | True         |  41 | UNDERPOWERED |   54.0 |   85.0 |    126.0 |  937.0 | 1722.0 |  585.3 |
| 46 | 2023-24  | RS     | trail2    | False        | 278 |              |  130.0 |  156.0 |    206.5 |  382.5 | 1804.6 |  545.6 |
| 47 | 2023-24  | RS     | trail2    | True         |  27 | UNDERPOWERED |   87.2 |  100.5 |    191.0 |  275.0 |  857.4 |  349.1 |
| 48 | 2023-24  | RS     | trail3+   | False        |  97 | UNDERPOWERED |  173.6 |  265.0 |    502.0 | 1141.0 | 2090.0 |  843.6 |
| 49 | 2023-24  | RS     | trail3+   | True         |  13 | UNDERPOWERED |  176.8 |  279.0 |    346.0 |  454.0 |  561.8 |  357.3 |
| 50 | 2023-24  | PO     | leading   | False        |   6 | UNDERPOWERED |  487.5 |  704.8 |   1379.0 | 2385.5 | 2641.5 | 1502.7 |
| 51 | 2023-24  | PO     | tied      | False        |  13 | UNDERPOWERED |  682.4 | 1621.0 |   1879.0 | 3342.0 | 3511.4 | 2230.9 |
| 52 | 2023-24  | PO     | tied      | True         |   3 | UNDERPOWERED | 1335.8 | 1451.0 |   1643.0 | 2254.5 | 2621.4 | 1922.7 |
| 53 | 2023-24  | PO     | trail1    | False        |  38 | UNDERPOWERED |   90.7 |  110.5 |    149.0 |  356.8 | 2220.2 |  623.0 |
| 54 | 2023-24  | PO     | trail1    | True         |   1 | UNDERPOWERED |   57.0 |   57.0 |     57.0 |   57.0 |   57.0 |   57.0 |
| 55 | 2023-24  | PO     | trail2    | False        |  20 | UNDERPOWERED |  110.8 |  149.8 |    198.5 |  333.5 | 1501.9 |  507.8 |
| 56 | 2023-24  | PO     | trail3+   | False        |   8 | UNDERPOWERED |  234.4 |  307.8 |    824.5 | 1471.0 | 1800.4 |  951.2 |
| 57 | 2023-24  | PO     | trail3+   | True         |   2 | UNDERPOWERED |  300.3 |  450.8 |    701.5 |  952.2 | 1102.7 |  701.5 |

### 1b. Pooled 3 seasons, P3 first non-DP pull while trailing, by pre-pull strength state

|    | type   | deficit   | pre_state    |    n | flag         |   median_rem |   p25 |   p75 |
|---:|:-------|:----------|:-------------|-----:|:-------------|-------------:|------:|------:|
|  0 | RS     | trail1    | even_5v5     | 1158 |              |        111.0 |  90.0 | 135.0 |
|  1 | RS     | trail1    | even_reduced |   15 | UNDERPOWERED |        122.0 |  90.5 | 144.5 |
|  2 | RS     | trail1    | team_PK      |   39 | UNDERPOWERED |         58.0 |  40.5 |  81.0 |
|  3 | RS     | trail1    | team_PP      |   60 | UNDERPOWERED |        117.0 |  96.5 | 140.0 |
|  4 | RS     | trail2    | even_5v5     |  783 |              |        175.0 | 143.0 | 213.0 |
|  5 | RS     | trail2    | even_reduced |   20 | UNDERPOWERED |        217.5 | 151.8 | 304.0 |
|  6 | RS     | trail2    | team_PK      |   29 | UNDERPOWERED |         91.0 |  60.0 | 135.0 |
|  7 | RS     | trail2    | team_PP      |   44 | UNDERPOWERED |        199.0 | 157.8 | 238.0 |
|  8 | RS     | trail3+   | even_5v5     |  200 |              |        250.0 | 186.8 | 318.2 |
|  9 | RS     | trail3+   | even_reduced |   11 | UNDERPOWERED |        372.0 | 282.5 | 569.0 |
| 10 | RS     | trail3+   | team_PK      |    6 | UNDERPOWERED |        197.0 | 140.5 | 321.0 |
| 11 | RS     | trail3+   | team_PP      |   40 | UNDERPOWERED |        283.5 | 217.8 | 347.0 |
| 12 | PO     | trail1    | even_5v5     |   87 | UNDERPOWERED |        115.0 |  90.5 | 140.0 |
| 13 | PO     | trail1    | even_reduced |    1 | UNDERPOWERED |        144.0 | 144.0 | 144.0 |
| 14 | PO     | trail1    | team_PK      |    2 | UNDERPOWERED |         56.0 |  55.5 |  56.5 |
| 15 | PO     | trail1    | team_PP      |    2 | UNDERPOWERED |        109.5 | 101.8 | 117.2 |
| 16 | PO     | trail2    | even_5v5     |   56 | UNDERPOWERED |        185.5 | 157.8 | 215.5 |
| 17 | PO     | trail2    | even_reduced |    1 | UNDERPOWERED |        353.0 | 353.0 | 353.0 |
| 18 | PO     | trail2    | team_PK      |    1 | UNDERPOWERED |        119.0 | 119.0 | 119.0 |
| 19 | PO     | trail3+   | even_5v5     |   29 | UNDERPOWERED |        272.0 | 191.0 | 318.0 |
| 20 | PO     | trail3+   | even_reduced |    2 | UNDERPOWERED |        377.0 | 346.5 | 407.5 |
| 21 | PO     | trail3+   | team_PK      |    1 | UNDERPOWERED |        320.0 | 320.0 | 320.0 |
| 22 | PO     | trail3+   | team_PP      |    5 | UNDERPOWERED |        232.0 | 229.0 | 331.0 |

### 1c. Period of the first pull (all first pulls incl. DP overlaps), counts

|            |   1 |   2 |   3 |
|:-----------|----:|----:|----:|
| 2021-22 RS | 299 | 251 | 754 |
| 2021-22 PO |  17 |  14 |  58 |
| 2022-23 RS | 301 | 281 | 762 |
| 2022-23 PO |  21 |  15 |  50 |
| 2023-24 RS | 321 | 276 | 794 |
| 2023-24 PO |  14 |  20 |  57 |

### 1d. Share of games with a non-DP pull, by deficit at a given time remaining

Trailing team (by `deficit` at `rem` seconds left in regulation) pulled at any time from `rem` to the end of regulation (an already-pulled goalie counts). Tied games at `rem` excluded.

|    | season   | game_type   |   rem |   deficit |   n_games |   share_pulled | flag         |
|---:|:---------|:------------|------:|----------:|----------:|---------------:|:-------------|
|  0 | 2021-22  | RS          |    60 |         1 |       349 |          0.997 |              |
|  1 | 2021-22  | RS          |    60 |         2 |       232 |          0.884 |              |
|  2 | 2021-22  | RS          |    60 |         3 |       464 |          0.058 |              |
|  3 | 2021-22  | RS          |   120 |         1 |       412 |          0.995 |              |
|  4 | 2021-22  | RS          |   120 |         2 |       220 |          0.977 |              |
|  5 | 2021-22  | RS          |   120 |         3 |       411 |          0.114 |              |
|  6 | 2021-22  | RS          |   180 |         1 |       434 |          0.956 |              |
|  7 | 2021-22  | RS          |   180 |         2 |       255 |          0.980 |              |
|  8 | 2021-22  | RS          |   180 |         3 |       366 |          0.158 |              |
|  9 | 2021-22  | RS          |   300 |         1 |       417 |          0.885 |              |
| 10 | 2021-22  | RS          |   300 |         2 |       284 |          0.915 |              |
| 11 | 2021-22  | RS          |   300 |         3 |       348 |          0.253 |              |
| 12 | 2021-22  | PO          |    60 |         1 |        22 |          1.000 | UNDERPOWERED |
| 13 | 2021-22  | PO          |    60 |         2 |        17 |          0.941 | UNDERPOWERED |
| 14 | 2021-22  | PO          |    60 |         3 |        33 |          0.061 | UNDERPOWERED |
| 15 | 2021-22  | PO          |   120 |         1 |        26 |          1.000 | UNDERPOWERED |
| 16 | 2021-22  | PO          |   120 |         2 |        16 |          1.000 | UNDERPOWERED |
| 17 | 2021-22  | PO          |   120 |         3 |        29 |          0.103 | UNDERPOWERED |
| 18 | 2021-22  | PO          |   180 |         1 |        28 |          0.964 | UNDERPOWERED |
| 19 | 2021-22  | PO          |   180 |         2 |        17 |          1.000 | UNDERPOWERED |
| 20 | 2021-22  | PO          |   180 |         3 |        27 |          0.333 | UNDERPOWERED |
| 21 | 2021-22  | PO          |   300 |         1 |        34 |          0.882 | UNDERPOWERED |
| 22 | 2021-22  | PO          |   300 |         2 |        14 |          1.000 | UNDERPOWERED |
| 23 | 2021-22  | PO          |   300 |         3 |        27 |          0.481 | UNDERPOWERED |
| 24 | 2022-23  | RS          |    60 |         1 |       336 |          0.994 |              |
| 25 | 2022-23  | RS          |    60 |         2 |       224 |          0.844 |              |
| 26 | 2022-23  | RS          |    60 |         3 |       475 |          0.038 |              |
| 27 | 2022-23  | RS          |   120 |         1 |       405 |          0.998 |              |
| 28 | 2022-23  | RS          |   120 |         2 |       210 |          0.976 |              |
| 29 | 2022-23  | RS          |   120 |         3 |       422 |          0.085 |              |
| 30 | 2022-23  | RS          |   180 |         1 |       406 |          0.958 |              |
| 31 | 2022-23  | RS          |   180 |         2 |       246 |          0.972 |              |
| 32 | 2022-23  | RS          |   180 |         3 |       391 |          0.153 |              |
| 33 | 2022-23  | RS          |   300 |         1 |       421 |          0.884 |              |
| 34 | 2022-23  | RS          |   300 |         2 |       269 |          0.911 |              |
| 35 | 2022-23  | RS          |   300 |         3 |       352 |          0.253 |              |
| 36 | 2022-23  | PO          |    60 |         1 |        20 |          1.000 | UNDERPOWERED |
| 37 | 2022-23  | PO          |    60 |         2 |        11 |          1.000 | UNDERPOWERED |
| 38 | 2022-23  | PO          |    60 |         3 |        34 |          0.118 | UNDERPOWERED |
| 39 | 2022-23  | PO          |   120 |         1 |        22 |          1.000 | UNDERPOWERED |
| 40 | 2022-23  | PO          |   120 |         2 |        15 |          1.000 | UNDERPOWERED |
| 41 | 2022-23  | PO          |   120 |         3 |        31 |          0.226 | UNDERPOWERED |
| 42 | 2022-23  | PO          |   180 |         1 |        24 |          0.958 | UNDERPOWERED |
| 43 | 2022-23  | PO          |   180 |         2 |        18 |          0.944 | UNDERPOWERED |
| 44 | 2022-23  | PO          |   180 |         3 |        28 |          0.250 | UNDERPOWERED |
| 45 | 2022-23  | PO          |   300 |         1 |        26 |          0.846 | UNDERPOWERED |
| 46 | 2022-23  | PO          |   300 |         2 |        17 |          0.941 | UNDERPOWERED |
| 47 | 2022-23  | PO          |   300 |         3 |        29 |          0.414 | UNDERPOWERED |
| 48 | 2023-24  | RS          |    60 |         1 |       326 |          0.991 |              |
| 49 | 2023-24  | RS          |    60 |         2 |       247 |          0.866 |              |
| 50 | 2023-24  | RS          |    60 |         3 |       483 |          0.048 |              |
| 51 | 2023-24  | RS          |   120 |         1 |       392 |          1.000 |              |
| 52 | 2023-24  | RS          |   120 |         2 |       243 |          0.963 |              |
| 53 | 2023-24  | RS          |   120 |         3 |       432 |          0.111 |              |
| 54 | 2023-24  | RS          |   180 |         1 |       396 |          0.972 |              |
| 55 | 2023-24  | RS          |   180 |         2 |       286 |          0.965 |              |
| 56 | 2023-24  | RS          |   180 |         3 |       383 |          0.133 |              |
| 57 | 2023-24  | RS          |   300 |         1 |       397 |          0.884 |              |
| 58 | 2023-24  | RS          |   300 |         2 |       328 |          0.918 |              |
| 59 | 2023-24  | RS          |   300 |         3 |       342 |          0.199 |              |
| 60 | 2023-24  | PO          |    60 |         1 |        33 |          1.000 | UNDERPOWERED |
| 61 | 2023-24  | PO          |    60 |         2 |        18 |          0.889 | UNDERPOWERED |
| 62 | 2023-24  | PO          |    60 |         3 |        20 |          0.050 | UNDERPOWERED |
| 63 | 2023-24  | PO          |   120 |         1 |        36 |          1.000 | UNDERPOWERED |
| 64 | 2023-24  | PO          |   120 |         2 |        19 |          1.000 | UNDERPOWERED |
| 65 | 2023-24  | PO          |   120 |         3 |        16 |          0.250 | UNDERPOWERED |
| 66 | 2023-24  | PO          |   180 |         1 |        37 |          1.000 | UNDERPOWERED |
| 67 | 2023-24  | PO          |   180 |         2 |        19 |          1.000 | UNDERPOWERED |
| 68 | 2023-24  | PO          |   180 |         3 |        15 |          0.333 | UNDERPOWERED |
| 69 | 2023-24  | PO          |   300 |         1 |        35 |          0.971 | UNDERPOWERED |
| 70 | 2023-24  | PO          |   300 |         2 |        24 |          0.917 | UNDERPOWERED |
| 71 | 2023-24  | PO          |   300 |         3 |        11 |          0.636 | UNDERPOWERED |

### 1e. Re-pulls after a pull ended by a goal against (P3, non-DP pulls)

Ended-by-goal rule: a goal event within 1 s of the shift-derived pull end. Lag = the same team's next pull start minus the return time.

|    | season   | type   |   n_pulls_ended_by_goal_against | flag         |   share_repulled_same_period |   lag_p25 |   lag_median |   lag_p75 |   share_repull_within_60s |   share_repull_within_120s |
|---:|:---------|:-------|--------------------------------:|:-------------|-----------------------------:|----------:|-------------:|----------:|--------------------------:|---------------------------:|
|  0 | 2021-22  | RS     |                             466 |              |                        0.225 |    12.000 |       18.000 |    33.000 |                     0.206 |                      0.223 |
|  1 | 2021-22  | PO     |                              44 | UNDERPOWERED |                        0.227 |     7.250 |       13.500 |    22.750 |                     0.182 |                      0.227 |
|  2 | 2022-23  | RS     |                             432 |              |                        0.201 |     8.000 |       14.000 |    25.500 |                     0.194 |                      0.201 |
|  3 | 2022-23  | PO     |                              25 | UNDERPOWERED |                        0.080 |    36.750 |       64.500 |    92.250 |                     0.040 |                      0.080 |
|  4 | 2023-24  | RS     |                             439 |              |                        0.221 |     9.000 |       14.000 |    36.000 |                     0.200 |                      0.212 |
|  5 | 2023-24  | PO     |                              38 | UNDERPOWERED |                        0.289 |    11.000 |       24.000 |    40.500 |                     0.263 |                      0.289 |

### 1f. How pulls end (non-DP pulls, P3), and final-minute pulls

|    | season   | type   | subset              |    n | flag         |   period_end |   goal_for |   goal_against |   goal_both |   stoppage |   in_play |   med_dur |
|---:|:---------|:-------|:--------------------|-----:|:-------------|-------------:|-----------:|---------------:|------------:|-----------:|----------:|----------:|
|  0 | 2021-22  | RS     | all P3 pulls        | 1150 |              |        0.291 |      0.135 |          0.405 |       0.000 |      0.162 |     0.007 |    57.000 |
|  1 | 2021-22  | RS     | start in final 60 s |  170 |              |        0.612 |      0.071 |          0.241 |       0.000 |      0.071 |     0.006 |    30.000 |
|  2 | 2021-22  | RS     | start 60-180 s left |  730 |              |        0.297 |      0.122 |          0.430 |       0.000 |      0.145 |     0.005 |    66.500 |
|  3 | 2021-22  | RS     | start >180 s left   |  250 |              |        0.056 |      0.216 |          0.444 |       0.000 |      0.272 |     0.012 |    65.000 |
|  4 | 2021-22  | PO     | all P3 pulls        |   88 | UNDERPOWERED |        0.216 |      0.068 |          0.500 |       0.000 |      0.216 |     0.000 |    60.500 |
|  5 | 2021-22  | PO     | start in final 60 s |   12 | UNDERPOWERED |        0.500 |      0.000 |          0.250 |       0.000 |      0.250 |     0.000 |    28.500 |
|  6 | 2021-22  | PO     | start 60-180 s left |   50 | UNDERPOWERED |        0.220 |      0.060 |          0.500 |       0.000 |      0.220 |     0.000 |    63.000 |
|  7 | 2021-22  | PO     | start >180 s left   |   26 | UNDERPOWERED |        0.077 |      0.115 |          0.615 |       0.000 |      0.192 |     0.000 |    78.000 |
|  8 | 2022-23  | RS     | all P3 pulls        | 1097 |              |        0.284 |      0.134 |          0.394 |       0.000 |      0.185 |     0.004 |    58.000 |
|  9 | 2022-23  | RS     | start in final 60 s |  148 |              |        0.628 |      0.034 |          0.264 |       0.000 |      0.068 |     0.007 |    32.000 |
| 10 | 2022-23  | RS     | start 60-180 s left |  707 |              |        0.293 |      0.132 |          0.397 |       0.000 |      0.178 |     0.000 |    69.000 |
| 11 | 2022-23  | RS     | start >180 s left   |  242 |              |        0.045 |      0.202 |          0.463 |       0.000 |      0.277 |     0.012 |    59.000 |
| 12 | 2022-23  | PO     | all P3 pulls        |   76 | UNDERPOWERED |        0.303 |      0.171 |          0.329 |       0.000 |      0.184 |     0.013 |    55.500 |
| 13 | 2022-23  | PO     | start in final 60 s |    8 | UNDERPOWERED |        0.500 |      0.125 |          0.375 |       0.000 |      0.000 |     0.000 |    20.500 |
| 14 | 2022-23  | PO     | start 60-180 s left |   37 | UNDERPOWERED |        0.405 |      0.135 |          0.216 |       0.000 |      0.216 |     0.027 |    67.000 |
| 15 | 2022-23  | PO     | start >180 s left   |   31 | UNDERPOWERED |        0.129 |      0.226 |          0.452 |       0.000 |      0.194 |     0.000 |    64.000 |
| 16 | 2023-24  | RS     | all P3 pulls        | 1142 |              |        0.290 |      0.130 |          0.384 |       0.000 |      0.194 |     0.002 |    57.000 |
| 17 | 2023-24  | RS     | start in final 60 s |  152 |              |        0.671 |      0.020 |          0.211 |       0.000 |      0.099 |     0.000 |    34.000 |
| 18 | 2023-24  | RS     | start 60-180 s left |  721 |              |        0.297 |      0.132 |          0.393 |       0.000 |      0.179 |     0.000 |    68.000 |
| 19 | 2023-24  | RS     | start >180 s left   |  269 |              |        0.056 |      0.190 |          0.461 |       0.000 |      0.286 |     0.007 |    64.000 |
| 20 | 2023-24  | PO     | all P3 pulls        |  103 |              |        0.330 |      0.117 |          0.369 |       0.000 |      0.184 |     0.000 |    60.000 |
| 21 | 2023-24  | PO     | start in final 60 s |   14 | UNDERPOWERED |        0.714 |      0.000 |          0.214 |       0.000 |      0.071 |     0.000 |    33.000 |
| 22 | 2023-24  | PO     | start 60-180 s left |   68 | UNDERPOWERED |        0.324 |      0.132 |          0.338 |       0.000 |      0.206 |     0.000 |    66.500 |
| 23 | 2023-24  | PO     | start >180 s left   |   21 | UNDERPOWERED |        0.095 |      0.143 |          0.571 |       0.000 |      0.190 |     0.000 |    63.000 |

### 1g. Pulls overlapping a delayed-penalty event (opponent about to be penalised)

Rule: a DELAYED_PENALTY event owned by the other team within [pull start - 3 s, pull end + 1 s], OR the pull ends within 3 s of a PENALTY called on the other team (the pbp logs far fewer DELAYED_PENALTY events than there are delayed-penalty pulls: 95% of P1/P2 pulls end at an opponent penalty call). Exception: a team trailing in the last 5:00 of P3 is treated as an EN-style pull whatever follows (about 3.6% of such pulls end at an opponent penalty and cannot be separated from a delayed-penalty pull).

|    | season   | game_type   |   by_event |   by_penalty_call_only |
|---:|:---------|:------------|-----------:|-----------------------:|
|  0 | 2021-22  | RS          |      0.622 |                  0.970 |
|  1 | 2021-22  | PO          |      0.556 |                  1.000 |
|  2 | 2022-23  | RS          |      0.619 |                  0.973 |
|  3 | 2022-23  | PO          |      0.458 |                  0.979 |
|  4 | 2023-24  | RS          |      0.466 |                  0.980 |
|  5 | 2023-24  | PO          |      0.417 |                  0.979 |
|    | season   | type   |   n_dp_pulls |   per_game | flag         |   med_dur_s |   share_leading_or_tied |   share_P3 |   share_goal_for |   share_goal_against |   goals_for_in |   goals_against_in |
|---:|:---------|:-------|-------------:|-----------:|:-------------|------------:|------------------------:|-----------:|-----------------:|---------------------:|---------------:|-------------------:|
|  0 | 2021-22  | RS     |          847 |      0.646 |              |      13.000 |                   0.647 |      0.283 |            0.027 |                0.001 |             24 |                  2 |
|  1 | 2021-22  | PO     |           45 |      0.506 | UNDERPOWERED |      11.000 |                   0.756 |      0.222 |            0.000 |                0.000 |              0 |                  0 |
|  2 | 2022-23  | RS     |          892 |      0.680 |              |      14.000 |                   0.637 |      0.283 |            0.027 |                0.001 |             24 |                  1 |
|  3 | 2022-23  | PO     |           48 |      0.545 | UNDERPOWERED |      14.500 |                   0.750 |      0.208 |            0.042 |                0.000 |              2 |                  0 |
|  4 | 2023-24  | RS     |          928 |      0.707 |              |      13.000 |                   0.645 |      0.291 |            0.025 |                0.001 |             23 |                  1 |
|  5 | 2023-24  | PO     |           48 |      0.545 | UNDERPOWERED |      13.000 |                   0.500 |      0.229 |            0.021 |                0.000 |              1 |                  0 |

### 1h. Empty-net goals and EN time per game

`en_goals_against_per_game` = goals scored into an empty net (pbp EN_AGAINST; the G7 gate quantity); `en_goals_for_per_game` = goals scored by a team with its own goalie pulled (EN_FOR). Per-pulled-minute rates for the `_nonDP` columns count goals inside shift-derived pull intervals; `_all` columns divide the pbp totals by all pulled minutes. Pulled minutes are team-minutes.

|    | season   | type   |   games |   pulls_per_game |   en_time_s_per_game_all |   en_time_s_per_game_nonDP |   en_goals_against_per_game |   en_goals_for_per_game |   EN_against_per_pulled_min_all |   EN_for_per_pulled_min_all |   EN_against_per_pulled_min_nonDP |   EN_for_per_pulled_min_nonDP |   n_en_goals_for | flag         |
|---:|:---------|:-------|--------:|-----------------:|-------------------------:|---------------------------:|----------------------------:|------------------------:|--------------------------------:|----------------------------:|----------------------------------:|------------------------------:|-----------------:|:-------------|
|  0 | 2021-22  | RS     |    1312 |            1.539 |                   72.593 |                     61.191 |                       0.363 |                   0.155 |                           0.300 |                       0.129 |                             0.368 |                         0.129 |              204 |              |
|  1 | 2021-22  | PO     |      89 |            1.494 |                   74.966 |                     67.449 |                       0.494 |                   0.101 |                           0.396 |                       0.081 |                             0.460 |                         0.070 |                9 | UNDERPOWERED |
|  2 | 2022-23  | RS     |    1312 |            1.532 |                   68.374 |                     57.081 |                       0.334 |                   0.155 |                           0.293 |                       0.136 |                             0.357 |                         0.132 |              204 |              |
|  3 | 2022-23  | PO     |      88 |            1.420 |                   78.580 |                     69.034 |                       0.284 |                   0.216 |                           0.217 |                       0.165 |                             0.257 |                         0.138 |               19 | UNDERPOWERED |
|  4 | 2023-24  | RS     |    1312 |            1.595 |                   72.508 |                     60.478 |                       0.341 |                   0.163 |                           0.282 |                       0.135 |                             0.343 |                         0.133 |              214 |              |
|  5 | 2023-24  | PO     |      88 |            1.727 |                   86.625 |                     77.386 |                       0.432 |                   0.182 |                           0.299 |                       0.126 |                             0.335 |                         0.123 |               16 | UNDERPOWERED |

### 1i. Validation: pbp-flagged EN goals (EN_FOR + EN_AGAINST) falling inside a shift-derived pull (tolerance 1 s)

|    | season   | type   |   en_goals |   inside_shift_derived_pull |   share |
|---:|:---------|:-------|-----------:|----------------------------:|--------:|
|  0 | 2021-22  | RS     |        680 |                         667 |  0.9809 |
|  1 | 2021-22  | PO     |         53 |                          51 |  0.9623 |
|  2 | 2022-23  | RS     |        642 |                         623 |  0.9704 |
|  3 | 2022-23  | PO     |         44 |                          41 |  0.9318 |
|  4 | 2023-24  | RS     |        661 |                         642 |  0.9713 |
|  5 | 2023-24  | PO     |         54 |                          53 |  0.9815 |

### 1j. Team-games with a pull: event goalie flags vs shift gaps >= 3 s

Event flags are seen only at events and also fire on PERIOD_END / GAME_END events (stale code, or an end-of-period pull shorter than 3 s): of the 1,205 flagged events in team-games with no shift gap of 3 s or more, 913 are PERIOD_END or GAME_END events. So the flag count exceeds the shift count; it is not a lower bound.

|    | season   | type   |   team_games |   with_pull_by_event_flags |   with_pull_by_shifts |
|---:|:---------|:-------|-------------:|---------------------------:|----------------------:|
|  0 | 2021-22  | RS     |         2624 |                       1643 |                  1312 |
|  1 | 2021-22  | PO     |          178 |                        115 |                    90 |
|  2 | 2022-23  | RS     |         2624 |                       1684 |                  1357 |
|  3 | 2022-23  | PO     |          176 |                         92 |                    87 |
|  4 | 2023-24  | RS     |         2624 |                       1669 |                  1398 |
|  5 | 2023-24  | PO     |          176 |                        112 |                    92 |

### 1k. Sensitivity of pull count to the minimum gap

|    |   min_gap_s |   n_pulls_total |   per_game |
|---:|------------:|----------------:|-----------:|
|  0 |       1.000 |        6818.000 |      1.623 |
|  1 |       2.000 |        6711.000 |      1.597 |
|  2 |       3.000 |        6531.000 |      1.555 |
|  3 |       5.000 |        6120.000 |      1.457 |

### 4a. Relief goalie appearances (shift chart: a second distinct goalie id on the ice)

|    | season   | type   |   team_games |   relief_appearances |   per_100_team_games | flag         |   share_P1 |   share_P2 |   share_P3 |   share_OT |   share_at_period_start |   share_right_after_opp_goal |   share_starter_returns |   median_relief_toi_min |
|---:|:---------|:-------|-------------:|---------------------:|---------------------:|:-------------|-----------:|-----------:|-----------:|-----------:|------------------------:|-----------------------------:|------------------------:|------------------------:|
|  0 | 2021-22  | RS     |         2624 |                  197 |                7.508 |              |      0.168 |      0.431 |      0.396 |      0.005 |                   0.371 |                        0.482 |                   0.081 |                  27.017 |
|  1 | 2021-22  | PO     |          178 |                   18 |               10.112 | UNDERPOWERED |      0.278 |      0.444 |      0.222 |      0.056 |                   0.222 |                        0.333 |                   0.056 |                  32.175 |
|  2 | 2022-23  | RS     |         2624 |                  163 |                6.212 |              |      0.166 |      0.485 |      0.350 |      0.000 |                   0.294 |                        0.479 |                   0.055 |                  27.400 |
|  3 | 2022-23  | PO     |          176 |                   22 |               12.500 | UNDERPOWERED |      0.091 |      0.455 |      0.455 |      0.000 |                   0.364 |                        0.545 |                   0.000 |                  24.800 |
|  4 | 2023-24  | RS     |         2624 |                  176 |                6.707 |              |      0.239 |      0.455 |      0.301 |      0.006 |                   0.318 |                        0.506 |                   0.045 |                  31.933 |
|  5 | 2023-24  | PO     |          176 |                    6 |                3.409 | UNDERPOWERED |      0.000 |      0.333 |      0.667 |      0.000 |                   0.500 |                        0.500 |                   0.167 |                  18.267 |

### 4b. Team score differential (own minus opponent, goals at or before the change second) at the change; counts

|    | season   | type   |   n |   <=-3 |   -2 |   -1 |   0 (tied) |   +1 |   >=+2 |
|---:|:---------|:-------|----:|-------:|-----:|-----:|-----------:|-----:|-------:|
|  0 | 2021-22  | RS     | 197 |    119 |   28 |   17 |         13 |    9 |     11 |
|  1 | 2021-22  | PO     |  18 |     11 |    1 |    0 |          2 |    2 |      2 |
|  2 | 2022-23  | RS     | 163 |     93 |   20 |   17 |         11 |    8 |     14 |
|  3 | 2022-23  | PO     |  22 |     16 |    3 |    0 |          1 |    1 |      1 |
|  4 | 2023-24  | RS     | 176 |    102 |   27 |   12 |         16 |    5 |     14 |
|  5 | 2023-24  | PO     |   6 |      4 |    2 |    0 |          0 |    0 |      0 |

### 4c. Cross-check: relief appearances by goalie box (non-starter, TOI > 0) vs shift chart

|    | season   | game_type   |   relief_by_goalie_box |   relief_by_shifts |
|---:|:---------|:------------|-----------------------:|-------------------:|
|  0 | 2021-22  | RS          |                    194 |                197 |
|  1 | 2021-22  | PO          |                     18 |                 18 |
|  2 | 2022-23  | RS          |                    161 |                163 |
|  3 | 2022-23  | PO          |                     22 |                 22 |
|  4 | 2023-24  | RS          |                    173 |                176 |
|  5 | 2023-24  | PO          |                      6 |                  6 |

### 4d. Share of shots on goal (non-EN, non-shootout) faced by a non-starter goalie

Starter = goalie_box `starter` flag (post-game data). Computed from pbp `goalie_id` on SHOT / GOAL events.

|    | season   | type   |   sog_faced |   share_by_relief |   share_by_relief_regulation_only |   goal_share_by_relief |   no_starter_match |
|---:|:---------|:-------|------------:|------------------:|----------------------------------:|-----------------------:|-------------------:|
|  0 | 2021-22  | RS     |       82528 |            0.0320 |                            0.0321 |                 0.0365 |                  0 |
|  1 | 2021-22  | PO     |        5928 |            0.0545 |                            0.0532 |                 0.0598 |                  0 |
|  2 | 2022-23  | RS     |       81552 |            0.0245 |                            0.0244 |                 0.0261 |                  0 |
|  3 | 2022-23  | PO     |        5523 |            0.0416 |                            0.0431 |                 0.0455 |                  0 |
|  4 | 2023-24  | RS     |       79038 |            0.0310 |                            0.0312 |                 0.0340 |                  0 |
|  5 | 2023-24  | PO     |        4911 |            0.0100 |                            0.0103 |                 0.0107 |                  0 |
## 2 and 3. Overtime and shootout (part B tables; 2x are item 2, 3x are item 3)

### 2a. Games tied after regulation and how they end (end state from the box score / verified finals; pbp end state mismatch count alongside)

|    | season   | type   |   games |   tied_after_reg |   reg_tie_rate |   decided_in_OT |   shootout |   so_rate_all_games |   so_share_of_tied |   pbp_vs_box_end_state_mismatch | flag         |
|---:|:---------|:-------|--------:|-----------------:|---------------:|----------------:|-----------:|--------------------:|-------------------:|--------------------------------:|:-------------|
|  0 | 2021-22  | RS     |    1312 |              288 |         0.2195 |             186 |        102 |              0.0777 |             0.3542 |                               0 |              |
|  1 | 2021-22  | PO     |      89 |               15 |         0.1685 |              15 |          0 |              0.0000 |             0.0000 |                               0 | UNDERPOWERED |
|  2 | 2022-23  | RS     |    1312 |              302 |         0.2302 |             207 |         95 |              0.0724 |             0.3146 |                               0 |              |
|  3 | 2022-23  | PO     |      88 |               24 |         0.2727 |              24 |          0 |              0.0000 |             0.0000 |                               0 | UNDERPOWERED |
|  4 | 2023-24  | RS     |    1312 |              272 |         0.2073 |             190 |         82 |              0.0625 |             0.3015 |                               0 |              |
|  5 | 2023-24  | PO     |      88 |               16 |         0.1818 |              16 |          0 |              0.0000 |             0.0000 |                               0 | UNDERPOWERED |

### 2b. Regular-season overtime: how it ends and how long it lasts (OT clock seconds; SO games count as 300 s)

Check on the end state: games with end_state OT must have exactly one OT goal and games with SO none (see sanity table 2b2).

|    | season   |   tied_games |   ended_by_OT_goal |   went_to_SO |   share_goal |   share_SO |   mean_OT_s |   median_OT_s |    p25 |     p75 |   goal_in_first60 |   goal_in_first120 |   OT_goal_games_mean_s | flag   |
|---:|:---------|-------------:|-------------------:|-------------:|-------------:|-----------:|------------:|--------------:|-------:|--------:|------------------:|-------------------:|-----------------------:|:-------|
|  0 | 2021-22  |          288 |                186 |          102 |        0.646 |      0.354 |     191.493 |       198.500 | 99.750 | 300.000 |             0.156 |              0.302 |                131.989 |        |
|  1 | 2022-23  |          302 |                207 |           95 |        0.685 |      0.315 |     190.126 |       206.500 | 96.000 | 300.000 |             0.149 |              0.315 |                139.700 |        |
|  2 | 2023-24  |          272 |                190 |           82 |        0.699 |      0.301 |     188.688 |       206.500 | 94.750 | 300.000 |             0.162 |              0.331 |                140.647 |        |

### 2b2. Sanity: OT goal counts vs end state

|    | season   |   OT_games_with_1_goal |   OT_games_not_1_goal |   SO_games_with_0_OT_goals |   SO_games_with_OT_goals |
|---:|:---------|-----------------------:|----------------------:|---------------------------:|-------------------------:|
|  0 | 2021-22  |                    186 |                     0 |                        102 |                        0 |
|  1 | 2022-23  |                    207 |                     0 |                         95 |                        0 |
|  2 | 2023-24  |                    190 |                     0 |                         82 |                        0 |

### 2c. OT goal hazard by OT minute (all strengths, both teams combined)

Exposure uses the game's OT end (goal time, or 300 s for shootout games). Cells under 100 goals are UNDERPOWERED by the brief's rule.

|    | season   |   ot_minute |   games_alive_at_start |   goals |   exposure_min |   goals_per_min | flag         |
|---:|:---------|------------:|-----------------------:|--------:|---------------:|----------------:|:-------------|
|  0 | 2021-22  |           1 |                    288 |      45 |       271.2667 |          0.1659 | UNDERPOWERED |
|  1 | 2021-22  |           2 |                    243 |      42 |       222.5833 |          0.1887 | UNDERPOWERED |
|  2 | 2021-22  |           3 |                    201 |      49 |       174.3167 |          0.2811 | UNDERPOWERED |
|  3 | 2021-22  |           4 |                    152 |      29 |       137.3667 |          0.2111 | UNDERPOWERED |
|  4 | 2021-22  |           5 |                    123 |      21 |       113.6333 |          0.1848 | UNDERPOWERED |
|  5 | 2022-23  |           1 |                    302 |      45 |       282.5167 |          0.1593 | UNDERPOWERED |
|  6 | 2022-23  |           2 |                    257 |      50 |       230.5833 |          0.2168 | UNDERPOWERED |
|  7 | 2022-23  |           3 |                    207 |      44 |       180.5167 |          0.2437 | UNDERPOWERED |
|  8 | 2022-23  |           4 |                    163 |      28 |       148.8333 |          0.1881 | UNDERPOWERED |
|  9 | 2022-23  |           5 |                    135 |      40 |       114.5167 |          0.3493 | UNDERPOWERED |
| 10 | 2023-24  |           1 |                    272 |      44 |       253.5000 |          0.1736 | UNDERPOWERED |
| 11 | 2023-24  |           2 |                    228 |      46 |       206.4167 |          0.2229 | UNDERPOWERED |
| 12 | 2023-24  |           3 |                    182 |      35 |       162.4000 |          0.2155 | UNDERPOWERED |
| 13 | 2023-24  |           4 |                    147 |      32 |       131.9500 |          0.2425 | UNDERPOWERED |
| 14 | 2023-24  |           5 |                    115 |      33 |       101.1167 |          0.3264 | UNDERPOWERED |
| 15 | pooled   |           1 |                    862 |     134 |       807.2833 |          0.1660 |              |
| 16 | pooled   |           2 |                    728 |     138 |       659.5833 |          0.2092 |              |
| 17 | pooled   |           3 |                    590 |     128 |       517.2333 |          0.2475 |              |
| 18 | pooled   |           4 |                    462 |      89 |       418.1500 |          0.2128 | UNDERPOWERED |
| 19 | pooled   |           5 |                    373 |      94 |       329.2667 |          0.2855 | UNDERPOWERED |

### 2d. Regular-season OT (period 4): exposure and event rates by strength state, both teams combined

Exposure: seconds between consecutive events are attributed to the state in the situation code of the earlier event (`prevstate`) or the later event (`nextstate`); the situation code changes only at events, so penalty expiry and the state after a whistle are known only at the next event. `_lo` / `_hi` are the rates under the two extreme attributions, `per60` uses their mean. 3v3 state is the INV-35 hazard target. Per-team rate = combined / 2.

|    | season   | state    |   exposure_s_prevstate |   exposure_s_nextstate |   attempts |      sog |   goals |   attempts_per60 |   sog_per60 |   goals_per60 |   goals_per60_lo |   goals_per60_hi | flag         | goals_flag   |
|---:|:---------|:---------|-----------------------:|-----------------------:|-----------:|---------:|--------:|-----------------:|------------:|--------------:|-----------------:|-----------------:|:-------------|:-------------|
|  0 | 2021-22  | 3v3      |              48906.000 |              48658.000 |   1554.000 | 1034.000 | 165.000 |          114.682 |      76.307 |        12.177 |           12.146 |           12.208 |              |              |
| 10 | 2022-23  | 3v3      |              48095.000 |              47663.000 |   1503.000 |  986.000 | 172.000 |          113.010 |      74.137 |        12.933 |           12.875 |           12.991 |              |              |
| 19 | 2023-24  | 3v3      |              43140.000 |              42766.000 |   1324.000 |  826.000 | 158.000 |          110.968 |      69.229 |        13.242 |           13.185 |           13.300 |              |              |
|  1 | 2021-22  | 4v3      |               5227.000 |               4412.000 |    207.000 |  117.000 |  17.000 |          154.622 |      87.395 |        12.698 |           11.708 |           13.871 |              | goals<100    |
| 11 | 2022-23  | 4v3      |               7128.000 |               5941.000 |    292.000 |  161.000 |  29.000 |          160.869 |      88.698 |        15.977 |           14.646 |           17.573 |              | goals<100    |
| 20 | 2023-24  | 4v3      |               6113.000 |               5349.000 |    248.000 |  129.000 |  22.000 |          155.784 |      81.033 |        13.820 |           12.956 |           14.807 |              | goals<100    |
|  2 | 2021-22  | 4v4      |                919.000 |               1750.000 |     57.000 |   34.000 |   2.000 |          153.765 |      91.720 |         5.395 |            4.114 |            7.835 | UNDERPOWERED | goals<100    |
| 12 | 2022-23  | 4v4      |               2092.000 |               3253.000 |    103.000 |   60.000 |   4.000 |          138.746 |      80.823 |         5.388 |            4.427 |            6.883 |              | goals<100    |
| 21 | 2023-24  | 4v4      |               2042.000 |               2878.000 |     99.000 |   55.000 |   6.000 |          144.878 |      80.488 |         8.780 |            7.505 |           10.578 | UNDERPOWERED | goals<100    |
| 14 | 2022-23  | EN (1v0) |                  0.000 |                 78.000 |      3.000 |    2.000 |   0.000 |          276.923 |     184.615 |         0.000 |            0.000 |            0.000 | UNDERPOWERED | goals<100    |
|  6 | 2021-22  | EN (3v4) |                  7.000 |                 70.000 |      3.000 |    1.000 |   1.000 |          280.519 |      93.506 |        93.506 |           51.429 |          514.286 | UNDERPOWERED | goals<100    |
| 15 | 2022-23  | EN (3v4) |                 44.000 |                233.000 |      9.000 |    5.000 |   0.000 |          233.935 |     129.964 |         0.000 |            0.000 |            0.000 | UNDERPOWERED | goals<100    |
| 24 | 2023-24  | EN (3v4) |                 13.000 |                117.000 |      3.000 |    2.000 |   1.000 |          166.154 |     110.769 |        55.385 |           30.769 |          276.923 | UNDERPOWERED | goals<100    |
|  8 | 2021-22  | EN (4v3) |                 86.000 |                204.000 |      7.000 |    1.000 |   0.000 |          173.793 |      24.828 |         0.000 |            0.000 |            0.000 | UNDERPOWERED | goals<100    |
| 17 | 2022-23  | EN (4v3) |                 59.000 |                228.000 |     11.000 |    9.000 |   2.000 |          275.958 |     225.784 |        50.174 |           31.579 |          122.034 | UNDERPOWERED | goals<100    |
| 26 | 2023-24  | EN (4v3) |                  8.000 |                177.000 |      3.000 |    3.000 |   2.000 |          116.757 |     116.757 |        77.838 |           40.678 |          900.000 | UNDERPOWERED | goals<100    |

### 2e. Regular-season OT, three seasons pooled, by strength state

|    | state    |   exposure_s_prevstate |   exposure_s_nextstate |   attempts |      sog |   goals |   exposure_s_mid |   attempts_per60 |   sog_per60 |   goals_per60 |   goals_per60_lo |   goals_per60_hi |   share_of_OT_time | flag         |
|---:|:---------|-----------------------:|-----------------------:|-----------:|---------:|--------:|-----------------:|-----------------:|------------:|--------------:|-----------------:|-----------------:|-------------------:|:-------------|
|  0 | 3v3      |             140141.000 |             139087.000 |   4381.000 | 2846.000 | 495.000 |       139614.000 |          112.966 |      73.385 |        12.764 |           12.716 |           12.812 |              0.852 |              |
|  1 | 4v3      |              18468.000 |              15702.000 |    747.000 |  407.000 |  68.000 |        17085.000 |          157.401 |      85.759 |        14.328 |           13.255 |           15.590 |              0.104 |              |
|  2 | 4v4      |               5053.000 |               7881.000 |    259.000 |  149.000 |  12.000 |         6467.000 |          144.178 |      82.944 |         6.680 |            5.482 |            8.549 |              0.039 |              |
|  8 | EN (4v3) |                153.000 |                609.000 |     21.000 |   13.000 |   4.000 |          381.000 |          198.425 |     122.835 |        37.795 |           23.645 |           94.118 |              0.002 | UNDERPOWERED |
|  6 | EN (3v4) |                 64.000 |                420.000 |     15.000 |    8.000 |   2.000 |          242.000 |          223.140 |     119.008 |        29.752 |           17.143 |          112.500 |              0.001 | UNDERPOWERED |
|  5 | EN (1v0) |                  0.000 |                 83.000 |      7.000 |    6.000 |   1.000 |           41.500 |          607.229 |     520.482 |        86.747 |           43.373 |         3600.000 |              0.000 | UNDERPOWERED |

### 2f. Penalties and non-3v3 time in regulation-season OT

|    | season   |   ot_games |   penalties_called_in_OT |   per_100_ot_games |   total_OT_clock_s |   share_time_3v3 |   games_with_penalty | flag         |
|---:|:---------|-----------:|-------------------------:|-------------------:|-------------------:|-----------------:|---------------------:|:-------------|
|  0 | 2021-22  |        288 |                       67 |             23.264 |          55149.000 |            0.885 |                   61 | UNDERPOWERED |
|  1 | 2022-23  |        302 |                       89 |             29.470 |          57418.000 |            0.834 |                   75 | UNDERPOWERED |
|  2 | 2023-24  |        272 |                       65 |             23.897 |          51323.000 |            0.837 |                   56 | UNDERPOWERED |

OT penalty minutes (counts):

|         |   0.0 |   2.0 |   4.0 |   10.0 |
|:--------|------:|------:|------:|-------:|
| 2021-22 |     1 |    64 |     0 |      2 |
| 2022-23 |     2 |    81 |     1 |      5 |
| 2023-24 |     4 |    57 |     1 |      3 |

### 2g. Home share of winners: OT goal, shootout, regulation decided (regular season)

OT cells with n < 100 are UNDERPOWERED. Binomial SE on a 0.5 proportion at n = 100 is about 0.05.

|    | season   |   ot_decided |   home_wins_in_OT |   so_decided |   home_wins_in_SO |   home_win_in_regulation_decided | flag         |
|---:|:---------|-------------:|------------------:|-------------:|------------------:|---------------------------------:|:-------------|
|  0 | 2021-22  |          186 |             0.538 |          102 |             0.510 |                            0.539 |              |
|  1 | 2022-23  |          207 |             0.565 |           95 |             0.421 |                            0.525 | UNDERPOWERED |
|  2 | 2023-24  |          190 |             0.537 |           82 |             0.585 |                            0.538 | UNDERPOWERED |

### 2h. Playoff OT (periods 4+, 5v5 continuous): exposure and event rates by strength state

All playoff OT cells are small; flagged UNDERPOWERED where fewer than 100 attempts.

|    | season   | state   |   exposure_s_prevstate |   exposure_s_nextstate |   attempts |     sog |   goals |   attempts_per60 |   sog_per60 |   goals_per60 |   goals_per60_lo |   goals_per60_hi | flag         | goals_flag   |
|---:|:---------|:--------|-----------------------:|-----------------------:|-----------:|--------:|--------:|-----------------:|------------:|--------------:|-----------------:|-----------------:|:-------------|:-------------|
|  0 | 2021-22  | 5v4     |                325.000 |                287.000 |     15.000 |   9.000 |   1.000 |          176.471 |     105.882 |        11.765 |           11.077 |           12.544 | UNDERPOWERED | goals<100    |
|  4 | 2022-23  | 5v4     |               1761.000 |               1471.000 |     67.000 |  30.000 |   7.000 |          149.257 |      66.832 |        15.594 |           14.310 |           17.131 | UNDERPOWERED | goals<100    |
|  8 | 2023-24  | 5v4     |                595.000 |                483.000 |     21.000 |   8.000 |   2.000 |          140.260 |      53.432 |        13.358 |           12.101 |           14.907 | UNDERPOWERED | goals<100    |
|  1 | 2021-22  | 5v5     |               7837.000 |               7861.000 |    319.000 | 171.000 |  14.000 |          146.312 |      78.430 |         6.421 |            6.411 |            6.431 |              | goals<100    |
|  5 | 2022-23  | 5v5     |              14908.000 |              15171.000 |    542.000 | 254.000 |  17.000 |          129.738 |      60.800 |         4.069 |            4.034 |            4.105 |              | goals<100    |
|  9 | 2023-24  | 5v5     |               9427.000 |               9533.000 |    353.000 | 159.000 |  14.000 |          134.051 |      60.380 |         5.316 |            5.287 |            5.346 |              | goals<100    |

Playoff OT summary:

|    | season   |   po_games |   ot_games |   ot_rate |   games_2plus_OT |   home_wins_in_OT | flag         |
|---:|:---------|-----------:|-----------:|----------:|-----------------:|------------------:|:-------------|
|  0 | 2021-22  |         89 |         15 |     0.169 |                1 |             0.467 | UNDERPOWERED |
|  1 | 2022-23  |         88 |         24 |     0.273 |                3 |             0.375 | UNDERPOWERED |
|  2 | 2023-24  |         88 |         16 |     0.182 |                4 |             0.375 | UNDERPOWERED |

### 3a. Shootout data integrity

|    | season   |   so_games_by_end_state |   games_with_attempt_events |   attempts |   strictly_alternating_share |   null_shooter_id |   null_goalie_id |   events_FAILED_SHOT_ATTEMPT |   winner_by_SO_goals_matches_final |   home_shoots_first_share |
|---:|:---------|------------------------:|----------------------------:|-----------:|-----------------------------:|------------------:|-----------------:|-----------------------------:|-----------------------------------:|--------------------------:|
|  0 | 2021-22  |                     102 |                         102 |        747 |                        1.000 |                 0 |                0 |                            0 |                              1.000 |                     0.804 |
|  1 | 2022-23  |                      95 |                          95 |        670 |                        1.000 |                 0 |                0 |                           25 |                              1.000 |                     0.821 |
|  2 | 2023-24  |                      82 |                          82 |        617 |                        1.000 |                 0 |                0 |                           10 |                              1.000 |                     0.902 |

### 3b. Rounds per shootout

|    | season   |   shootouts |   mean_attempts |   mean_rounds |   share_3_rounds_or_fewer |   share_past_round_3 |   share_ended_after_attempt_4_or_5 |   max_rounds | flag         |
|---:|:---------|------------:|----------------:|--------------:|--------------------------:|---------------------:|-----------------------------------:|-------------:|:-------------|
|  0 | 2021-22  |         102 |           7.324 |         3.784 |                     0.696 |                0.304 |                              0.324 |            9 |              |
|  1 | 2022-23  |          95 |           7.053 |         3.663 |                     0.653 |                0.347 |                              0.347 |            9 | UNDERPOWERED |
|  2 | 2023-24  |          82 |           7.524 |         3.866 |                     0.659 |                0.341 |                              0.280 |           12 | UNDERPOWERED |

Pooled attempts-per-shootout distribution (counts): 4: 21, 5: 68, 6: 98, 8: 34, 10: 19, 12: 14, 14: 15, 16: 2, 18: 7, 24: 1


### 3c. Per-attempt success by round and by home / away shooter

|    | season   | round   | shooter   |   attempts |   goals |   success_rate | flag         |
|---:|:---------|:--------|:----------|-----------:|--------:|---------------:|:-------------|
|  0 | 2021-22  | 1       | both      |        204 |      57 |          0.279 |              |
|  3 | 2021-22  | 2       | both      |        204 |      57 |          0.279 |              |
|  6 | 2021-22  | 3       | both      |        163 |      61 |          0.374 |              |
|  9 | 2021-22  | 4       | both      |         62 |      16 |          0.258 | UNDERPOWERED |
| 12 | 2021-22  | 5       | both      |         46 |      10 |          0.217 | UNDERPOWERED |
| 15 | 2021-22  | 6+      | both      |         68 |      23 |          0.338 | UNDERPOWERED |
| 18 | 2022-23  | 1       | both      |        190 |      65 |          0.342 |              |
| 21 | 2022-23  | 2       | both      |        190 |      65 |          0.342 |              |
| 24 | 2022-23  | 3       | both      |        150 |      51 |          0.340 |              |
| 27 | 2022-23  | 4       | both      |         66 |      24 |          0.364 | UNDERPOWERED |
| 30 | 2022-23  | 5       | both      |         38 |       8 |          0.211 | UNDERPOWERED |
| 33 | 2022-23  | 6+      | both      |         36 |      13 |          0.361 | UNDERPOWERED |
| 36 | 2023-24  | 1       | both      |        164 |      48 |          0.293 |              |
| 39 | 2023-24  | 2       | both      |        164 |      53 |          0.323 |              |
| 42 | 2023-24  | 3       | both      |        135 |      41 |          0.304 |              |
| 45 | 2023-24  | 4       | both      |         56 |      14 |          0.250 | UNDERPOWERED |
| 48 | 2023-24  | 5       | both      |         32 |       7 |          0.219 | UNDERPOWERED |
| 51 | 2023-24  | 6+      | both      |         66 |      19 |          0.288 | UNDERPOWERED |
| 54 | pooled   | 1       | both      |        558 |     170 |          0.305 |              |
| 57 | pooled   | 2       | both      |        558 |     175 |          0.314 |              |
| 60 | pooled   | 3       | both      |        448 |     153 |          0.342 |              |
| 63 | pooled   | 4       | both      |        184 |      54 |          0.293 |              |
| 66 | pooled   | 5       | both      |        116 |      25 |          0.216 |              |
| 69 | pooled   | 6+      | both      |        170 |      55 |          0.324 |              |

By shooter side:

|    | ('season', '')   | ('round', '')   |   ('attempts', 'away') |   ('attempts', 'home') |   ('success_rate', 'away') |   ('success_rate', 'home') |
|---:|:-----------------|:----------------|-----------------------:|-----------------------:|---------------------------:|---------------------------:|
|  0 | 2021-22          | 1               |                102.000 |                102.000 |                      0.255 |                      0.304 |
|  1 | 2021-22          | 2               |                102.000 |                102.000 |                      0.294 |                      0.265 |
|  2 | 2021-22          | 3               |                 74.000 |                 89.000 |                      0.405 |                      0.348 |
|  3 | 2021-22          | 4               |                 31.000 |                 31.000 |                      0.226 |                      0.290 |
|  4 | 2021-22          | 5               |                 23.000 |                 23.000 |                      0.130 |                      0.304 |
|  5 | 2021-22          | 6+              |                 34.000 |                 34.000 |                      0.324 |                      0.353 |
|  6 | 2022-23          | 1               |                 95.000 |                 95.000 |                      0.368 |                      0.316 |
|  7 | 2022-23          | 2               |                 95.000 |                 95.000 |                      0.347 |                      0.337 |
|  8 | 2022-23          | 3               |                 67.000 |                 83.000 |                      0.358 |                      0.325 |
|  9 | 2022-23          | 4               |                 33.000 |                 33.000 |                      0.364 |                      0.364 |
| 10 | 2022-23          | 5               |                 19.000 |                 19.000 |                      0.368 |                      0.053 |
| 11 | 2022-23          | 6+              |                 18.000 |                 18.000 |                      0.500 |                      0.222 |
| 12 | 2023-24          | 1               |                 82.000 |                 82.000 |                      0.305 |                      0.280 |
| 13 | 2023-24          | 2               |                 82.000 |                 82.000 |                      0.329 |                      0.317 |
| 14 | 2023-24          | 3               |                 62.000 |                 73.000 |                      0.226 |                      0.370 |
| 15 | 2023-24          | 4               |                 28.000 |                 28.000 |                      0.250 |                      0.250 |
| 16 | 2023-24          | 5               |                 16.000 |                 16.000 |                      0.188 |                      0.250 |
| 17 | 2023-24          | 6+              |                 33.000 |                 33.000 |                      0.242 |                      0.333 |
| 18 | pooled           | 1               |                279.000 |                279.000 |                      0.308 |                      0.301 |
| 19 | pooled           | 2               |                279.000 |                279.000 |                      0.323 |                      0.305 |
| 20 | pooled           | 3               |                203.000 |                245.000 |                      0.335 |                      0.347 |
| 21 | pooled           | 4               |                 92.000 |                 92.000 |                      0.283 |                      0.304 |
| 22 | pooled           | 5               |                 58.000 |                 58.000 |                      0.224 |                      0.207 |
| 23 | pooled           | 6+              |                 85.000 |                 85.000 |                      0.329 |                      0.318 |

Overall pooled success 0.3107 over 2034 attempts; home 0.3092, away 0.3122; first shooter of the round 0.3130, second shooter 0.3082. Per-season overall: 2021-22 0.2999 (n=747); 2022-23 0.3373 (n=670); 2023-24 0.2950 (n=617)


### 3d. Shooter and goalie identity: is a per-shooter model feasible?

|    | entity   |   min_attempts |   n_entities |   share_of_all_attempts |   distinct_total |
|---:|:---------|---------------:|-------------:|------------------------:|-----------------:|
|  0 | shooter  |              5 |          154 |                   0.783 |              383 |
|  1 | shooter  |             10 |           72 |                   0.503 |              383 |
|  2 | shooter  |             20 |            6 |                   0.066 |              383 |
|  3 | shooter  |             30 |            0 |                   0.000 |              383 |
|  4 | goalie   |              5 |           88 |                   0.984 |              100 |
|  5 | goalie   |             10 |           72 |                   0.931 |              100 |
|  6 | goalie   |             20 |           40 |                   0.698 |              100 |
|  7 | goalie   |             30 |           24 |                   0.498 |              100 |

Dispersion check (observed squared deviation of goals from n*p0 over binomial expectation; 1.0 means no shooter / goalie signal beyond chance): shooters with >= 10 attempts 1.209 over 72 shooters (1023 attempts); goalies with >= 10 attempts faced 0.909 over 72 goalies (1894 attempts). With 90% of shooters near 10-30 attempts the test has little power: treat as UNDERPOWERED for any individual shooter.

## 5. Rebounds and faceoffs (part C tables)

### 5.0 Rebound proxy definition

Unblocked attempt = SHOT, MISS or GOAL (shootouts excluded). It is a rebound proxy if the immediately preceding shot attempt (SHOT, MISS, BLOCK or GOAL) in the same period was by the same team, was at most 3 game-clock seconds earlier, and no STOPPAGE, FACEOFF, PENALTY, GOAL or period event lies between them (so no whistle intervened). `game_time_s` has 1 s resolution, so the window is effectively 3 to 4 s. Blocked attempts are not themselves classified (they cannot be rebounds-on-goal). The prior attempt's class says whether the puck came off a save (SHOT), a miss (off the glass / boards) or a block.


### 5a. Rebound proxy by season and game type

|    | season   | game_type   |   unblocked |   reb_n |   reb_share |   goal_rate_per_unblocked_reb |   goal_rate_per_unblocked_other |   goal_per_sog_reb |   goal_per_sog_other |   sog_share_of_reb | flag   |
|---:|:---------|:------------|------------:|--------:|------------:|------------------------------:|--------------------------------:|-------------------:|---------------------:|-------------------:|:-------|
|  0 | 2021-22  | RS          |      113290 |    8160 |      0.0720 |                        0.1792 |                          0.0636 |             0.2129 |               0.0878 |             0.8417 |        |
|  1 | 2021-22  | PO          |        8313 |     734 |      0.0883 |                        0.1526 |                          0.0594 |             0.2000 |               0.0831 |             0.7629 |        |
|  2 | 2022-23  | RS          |      114088 |   10204 |      0.0894 |                        0.1379 |                          0.0659 |             0.1786 |               0.0923 |             0.7722 |        |
|  3 | 2022-23  | PO          |        7978 |     743 |      0.0931 |                        0.1373 |                          0.0623 |             0.1875 |               0.0901 |             0.7322 |        |
|  4 | 2023-24  | RS          |      114839 |   11743 |      0.1023 |                        0.1122 |                          0.0657 |             0.1558 |               0.0953 |             0.7199 |        |
|  5 | 2023-24  | PO          |        7690 |     825 |      0.1073 |                        0.0945 |                          0.0621 |             0.1423 |               0.0968 |             0.6642 |        |

### 5b. Rebound proxy by strength state of the shooting team (3 seasons pooled, RS + PO)

State from the shooting team's view: PP = shooting team has the man advantage, PK = shorthanded, EN_FOR = own goalie pulled, EN_AGAINST = shooting into an empty net.

|    | state      |   unblocked |   reb_n |   reb_share |   goal_rate_per_unblocked_reb |   goal_rate_per_unblocked_other |   goal_per_sog_reb |   goal_per_sog_other |   sog_share_of_reb | flag         |
|---:|:-----------|------------:|--------:|------------:|------------------------------:|--------------------------------:|-------------------:|---------------------:|-------------------:|:-------------|
|  0 | 3v3        |        3719 |     221 |      0.0594 |                        0.1946 |                          0.1295 |             0.2457 |               0.1695 |             0.7919 |              |
|  1 | 4v4        |        4276 |     261 |      0.0610 |                        0.1762 |                          0.0745 |             0.2222 |               0.1002 |             0.7931 |              |
|  2 | 5v5        |      286035 |   25214 |      0.0882 |                        0.1252 |                          0.0542 |             0.1655 |               0.0769 |             0.7567 |              |
|  3 | EN_AGAINST |        2426 |      59 |      0.0243 |                        0.6780 |                          0.6033 |             1.0000 |               0.9993 |             0.6780 | UNDERPOWERED |
|  4 | EN_FOR     |        7975 |    1056 |      0.1324 |                        0.1686 |                          0.0705 |             0.2127 |               0.1034 |             0.7926 |              |
|  5 | PK         |        9100 |     371 |      0.0408 |                        0.1563 |                          0.0693 |             0.1933 |               0.0847 |             0.8086 |              |
|  6 | PP         |       52667 |    5227 |      0.0992 |                        0.1829 |                          0.0889 |             0.2268 |               0.1266 |             0.8064 |              |

### 5b2. By season and strength state

|    | season   | state      |   unblocked |   reb_n |   reb_share |   goal_rate_per_unblocked_reb |   goal_rate_per_unblocked_other |   goal_per_sog_reb |   goal_per_sog_other |   sog_share_of_reb | flag         |
|---:|:---------|:-----------|------------:|--------:|------------:|------------------------------:|--------------------------------:|-------------------:|---------------------:|-------------------:|:-------------|
|  0 | 2021-22  | 3v3        |        1337 |      77 |      0.0576 |                        0.2208 |                          0.1175 |             0.2464 |               0.1534 |             0.8961 | UNDERPOWERED |
|  1 | 2021-22  | 4v4        |        1495 |      77 |      0.0515 |                        0.1948 |                          0.0684 |             0.2206 |               0.0901 |             0.8831 | UNDERPOWERED |
|  2 | 2021-22  | 5v5        |       95540 |    6875 |      0.0720 |                        0.1619 |                          0.0533 |             0.1954 |               0.0739 |             0.8285 |              |
|  3 | 2021-22  | EN_AGAINST |         798 |      18 |      0.0226 |                        0.9444 |                          0.6449 |             1.0000 |               1.0000 |             0.9444 | UNDERPOWERED |
|  4 | 2021-22  | EN_FOR     |        2553 |     277 |      0.1085 |                        0.1841 |                          0.0712 |             0.2161 |               0.1017 |             0.8520 |              |
|  5 | 2021-22  | PK         |        3077 |      94 |      0.0305 |                        0.2021 |                          0.0640 |             0.2436 |               0.0770 |             0.8298 | UNDERPOWERED |
|  6 | 2021-22  | PP         |       16803 |    1476 |      0.0878 |                        0.2317 |                          0.0853 |             0.2706 |               0.1193 |             0.8564 |              |
|  7 | 2022-23  | 3v3        |        1271 |      83 |      0.0653 |                        0.1928 |                          0.1322 |             0.2462 |               0.1701 |             0.7831 | UNDERPOWERED |
|  8 | 2022-23  | 4v4        |        1342 |      81 |      0.0604 |                        0.1728 |                          0.0730 |             0.2188 |               0.0973 |             0.7901 | UNDERPOWERED |
|  9 | 2022-23  | 5v5        |       95067 |    8525 |      0.0897 |                        0.1254 |                          0.0547 |             0.1654 |               0.0771 |             0.7584 |              |
| 10 | 2022-23  | EN_AGAINST |         785 |      22 |      0.0280 |                        0.5455 |                          0.5911 |             1.0000 |               0.9978 |             0.5455 | UNDERPOWERED |
| 11 | 2022-23  | EN_FOR     |        2576 |     336 |      0.1304 |                        0.1815 |                          0.0723 |             0.2293 |               0.1055 |             0.7917 |              |
| 12 | 2022-23  | PK         |        3049 |     127 |      0.0417 |                        0.1181 |                          0.0739 |             0.1442 |               0.0899 |             0.8189 |              |
| 13 | 2022-23  | PP         |       17976 |    1773 |      0.0986 |                        0.1816 |                          0.0912 |             0.2224 |               0.1295 |             0.8167 |              |
| 14 | 2023-24  | 3v3        |        1111 |      61 |      0.0549 |                        0.1639 |                          0.1410 |             0.2439 |               0.1885 |             0.6721 | UNDERPOWERED |
| 15 | 2023-24  | 4v4        |        1439 |     103 |      0.0716 |                        0.1650 |                          0.0823 |             0.2267 |               0.1142 |             0.7282 |              |
| 16 | 2023-24  | 5v5        |       95428 |    9814 |      0.1028 |                        0.0993 |                          0.0545 |             0.1409 |               0.0799 |             0.7050 |              |
| 17 | 2023-24  | EN_AGAINST |         843 |      19 |      0.0225 |                        0.5789 |                          0.5752 |             1.0000 |               1.0000 |             0.5789 | UNDERPOWERED |
| 18 | 2023-24  | EN_FOR     |        2846 |     443 |      0.1557 |                        0.1490 |                          0.0682 |             0.1970 |               0.1030 |             0.7562 |              |
| 19 | 2023-24  | PK         |        2974 |     150 |      0.0504 |                        0.1600 |                          0.0701 |             0.2034 |               0.0876 |             0.7867 |              |
| 20 | 2023-24  | PP         |       17888 |    1978 |      0.1106 |                        0.1476 |                          0.0901 |             0.1943 |               0.1309 |             0.7599 |              |

### 5c. Rebound proxies by the prior attempt's class (3 seasons pooled)

|    | prior_attempt_class   |     n |   share_of_rebound_proxies |   goal_rate_per_unblocked |   goal_per_sog |   sog_share | flag   |
|---:|:----------------------|------:|---------------------------:|--------------------------:|---------------:|------------:|:-------|
|  0 | BLOCK                 |  7636 |                     0.2356 |                    0.1101 |         0.1526 |      0.7218 |        |
|  1 | MISS                  |  4934 |                     0.1522 |                    0.1196 |         0.1698 |      0.7041 |        |
|  2 | SHOT                  | 19839 |                     0.6121 |                    0.1536 |         0.1920 |      0.7998 |        |

### 5c2. Prior class by strength state (pooled)

|    | prior_attempt_class   | state      |     n |   goal_rate_per_unblocked | flag         |
|---:|:----------------------|:-----------|------:|--------------------------:|:-------------|
|  0 | BLOCK                 | 3v3        |    25 |                    0.2800 | UNDERPOWERED |
|  1 | BLOCK                 | 4v4        |    59 |                    0.1356 | UNDERPOWERED |
|  2 | BLOCK                 | 5v5        |  6113 |                    0.0962 |              |
|  3 | BLOCK                 | EN_AGAINST |    24 |                    0.7083 | UNDERPOWERED |
|  4 | BLOCK                 | EN_FOR     |   281 |                    0.1352 |              |
|  5 | BLOCK                 | PK         |    47 |                    0.1277 | UNDERPOWERED |
|  6 | BLOCK                 | PP         |  1087 |                    0.1628 |              |
|  7 | MISS                  | 3v3        |    21 |                    0.2857 | UNDERPOWERED |
|  8 | MISS                  | 4v4        |    30 |                    0.2333 | UNDERPOWERED |
|  9 | MISS                  | 5v5        |  4035 |                    0.1001 |              |
| 10 | MISS                  | EN_AGAINST |    35 |                    0.6571 | UNDERPOWERED |
| 11 | MISS                  | EN_FOR     |   137 |                    0.2190 |              |
| 12 | MISS                  | PK         |    48 |                    0.1667 | UNDERPOWERED |
| 13 | MISS                  | PP         |   628 |                    0.1783 |              |
| 14 | SHOT                  | 3v3        |   175 |                    0.1714 |              |
| 15 | SHOT                  | 4v4        |   172 |                    0.1802 |              |
| 16 | SHOT                  | 5v5        | 15066 |                    0.1437 |              |
| 17 | SHOT                  | EN_FOR     |   638 |                    0.1724 |              |
| 18 | SHOT                  | PK         |   276 |                    0.1594 |              |
| 19 | SHOT                  | PP         |  3512 |                    0.1899 |              |

### 5d. Rebound proxy by clock gap to the prior attempt (pooled)

|    |   seconds_since_prior_attempt |     n |   goal_rate_per_unblocked |   goal_per_sog | flag   |
|---:|------------------------------:|------:|--------------------------:|---------------:|:-------|
|  0 |                             0 |  1972 |                    0.2008 |         0.2513 |        |
|  1 |                             1 | 12161 |                    0.0991 |         0.1253 |        |
|  2 |                             2 | 11149 |                    0.1614 |         0.2135 |        |
|  3 |                             3 |  7127 |                    0.1511 |         0.2061 |        |

### 5e. Rebound-proxy share by shot type (pooled)

|    | shot_type    |   unblocked |   rebound_share |   goal_rate |   goal_rate_rebound |   reb_n | flag         |
|---:|:-------------|------------:|----------------:|------------:|--------------------:|--------:|:-------------|
|  0 | backhand     |       26887 |          0.1895 |      0.0857 |              0.1380 |    5095 |              |
|  1 | bat          |         779 |          0.5327 |      0.1515 |              0.1855 |     415 |              |
|  2 | between-legs |         154 |          0.2338 |      0.1104 |              0.1389 |      36 | UNDERPOWERED |
|  3 | cradle       |          16 |          0.1250 |      0.2500 |              0.0000 |       2 | UNDERPOWERED |
|  4 | deflected    |        8039 |          0.1052 |      0.0901 |              0.1513 |     846 |              |
|  5 | poke         |         916 |          0.5175 |      0.1212 |              0.1308 |     474 |              |
|  6 | slap         |       45605 |          0.0400 |      0.0505 |              0.0647 |    1824 |              |
|  7 | snap         |       51590 |          0.0703 |      0.0899 |              0.1615 |    3629 |              |
|  8 | tip-in       |       29596 |          0.0521 |      0.0883 |              0.1252 |    1541 |              |
|  9 | wrap-around  |        3045 |          0.1307 |      0.0535 |              0.1055 |     398 |              |
| 10 | wrist        |      199528 |          0.0909 |      0.0655 |              0.1408 |   18138 |              |

### 5f. Rebound proxies per game

|    | season   | game_type   |   rebounds |      n |   rebounds_per_game |   unblocked_per_game |
|---:|:---------|:------------|-----------:|-------:|--------------------:|---------------------:|
|  0 | 2021-22  | RS          |       8160 | 113290 |               6.220 |               86.349 |
|  1 | 2021-22  | PO          |        734 |   8313 |               8.247 |               93.404 |
|  2 | 2022-23  | RS          |      10204 | 114088 |               7.777 |               86.957 |
|  3 | 2022-23  | PO          |        743 |   7978 |               8.443 |               90.659 |
|  4 | 2023-24  | RS          |      11743 | 114839 |               8.950 |               87.530 |
|  5 | 2023-24  | PO          |        825 |   7690 |               9.375 |               87.386 |

### 5g. Team spread of the rebound-proxy share (own shots; 32 teams per season)

|         |   mean |    std |    min |    max |   binomial_sd |
|:--------|-------:|-------:|-------:|-------:|--------------:|
| 2021-22 | 0.0728 | 0.0074 | 0.0530 | 0.0864 |        0.0043 |
| 2022-23 | 0.0891 | 0.0094 | 0.0678 | 0.1077 |        0.0047 |
| 2023-24 | 0.1024 | 0.0084 | 0.0896 | 0.1224 |        0.0049 |

Cross-season correlation of team rebound-proxy share: 2021-22 vs 2022-23 r=0.298; 2022-23 vs 2023-24 r=0.680


### 5h. Faceoffs per game by zone (zone from the home team's view: O = home offensive zone, D = home defensive zone)

|    | season   | type   |   games |   faceoffs_per_game |   zone_N_home_view_per_game |   zone_O_home_view_per_game |   zone_D_home_view_per_game |
|---:|:---------|:-------|--------:|--------------------:|----------------------------:|----------------------------:|----------------------------:|
|  0 | 2021-22  | RS     |    1312 |              56.594 |                      17.072 |                      20.226 |                      19.295 |
|  1 | 2021-22  | PO     |      89 |              60.449 |                      18.022 |                      22.640 |                      19.787 |
|  2 | 2022-23  | RS     |    1312 |              56.905 |                      17.026 |                      20.476 |                      19.403 |
|  3 | 2022-23  | PO     |      88 |              61.739 |                      18.659 |                      22.511 |                      20.568 |
|  4 | 2023-24  | RS     |    1312 |              56.546 |                      16.914 |                      20.331 |                      19.301 |
|  5 | 2023-24  | PO     |      88 |              60.716 |                      18.159 |                      22.330 |                      20.227 |

### 5i. Faceoffs per game by strength state (unordered skater counts; EN = either goalie out)

|    | season   | type   |   5v5_per_game |   5v4_per_game |   4v4_per_game |   3v3_per_game |   5v3_per_game |   4v3_per_game |   EN_per_game |   other_per_game |
|---:|:---------|:-------|---------------:|---------------:|---------------:|---------------:|---------------:|---------------:|--------------:|-----------------:|
|  0 | 2021-22  | RS     |         43.662 |          9.746 |          1.146 |          0.502 |          0.277 |          0.168 |         1.093 |            0.000 |
|  1 | 2021-22  | PO     |         45.697 |         10.966 |          1.888 |          0.011 |          0.551 |          0.101 |         1.236 |            0.000 |
|  2 | 2022-23  | RS     |         43.622 |         10.287 |          0.969 |          0.480 |          0.293 |          0.205 |         1.048 |            0.000 |
|  3 | 2022-23  | PO     |         48.295 |         10.352 |          1.375 |          0.000 |          0.193 |          0.170 |         1.352 |            0.000 |
|  4 | 2023-24  | RS     |         43.439 |         10.008 |          1.057 |          0.416 |          0.257 |          0.184 |         1.184 |            0.000 |
|  5 | 2023-24  | PO     |         47.341 |          9.875 |          1.625 |          0.000 |          0.170 |          0.091 |         1.614 |            0.000 |

### 5j. Home faceoff win share by strength state and zone (regular season, pooled)

|    | state   |      n |   home_win_share | flag   |   n_N |   home_win_N |   n_O |   home_win_O |   n_D |   home_win_D |
|---:|:--------|-------:|-----------------:|:-------|------:|-------------:|------:|-------------:|------:|-------------:|
|  0 | 3v3     |   1834 |           0.5256 |        |   912 |       0.5296 |   487 |       0.4969 |   435 |       0.5494 |
|  1 | 4v3     |    732 |           0.5164 |        |   105 |       0.5238 |   360 |       0.6028 |   267 |       0.3970 |
|  2 | 4v4     |   4161 |           0.5254 |        |  1171 |       0.5107 |  1533 |       0.4847 |  1457 |       0.5800 |
|  3 | 5v3     |   1085 |           0.5263 |        |    81 |       0.6049 |   523 |       0.6310 |   481 |       0.3992 |
|  4 | 5v4     |  39415 |           0.5162 |        |  5474 |       0.5026 | 17592 |       0.5549 | 16349 |       0.4792 |
|  5 | 5v5     | 171509 |           0.5079 |        | 58946 |       0.5026 | 57507 |       0.5010 | 55056 |       0.5207 |
|  6 | EN      |   4362 |           0.5078 |        |   239 |       0.5774 |  2073 |       0.5822 |  2050 |       0.4244 |

### 5k. Faceoff win share spread across teams (regular season)

Win share = wins / (wins + losses) for the team; mean is 0.5 by construction. `ratio_obs_to_binomial` of 1.0 means the spread is what chance alone gives; `odd_even_game_split_corr` is the correlation of team shares computed on odd vs even game ids (about 16 teams' worth of persistence evidence: values near 0 mean no stable team signal).

|    | season   | faceoffs   |   n_teams |   mean_n_per_team |   mean_share |   sd_across_teams |   binomial_sd |   ratio_obs_to_binomial |    min |    max |   odd_even_game_split_corr |
|---:|:---------|:-----------|----------:|------------------:|-------------:|------------------:|--------------:|------------------------:|-------:|-------:|---------------------------:|
|  0 | 2021-22  | all        |        32 |         4640.6875 |       0.4998 |            0.0242 |        0.0073 |                  3.2938 | 0.4599 | 0.5505 |                     0.8572 |
|  1 | 2021-22  | 5v5 only   |        32 |         3580.3125 |       0.4997 |            0.0261 |        0.0084 |                  3.1224 | 0.4592 | 0.5599 |                     0.8816 |
|  2 | 2022-23  | all        |        32 |         4666.1875 |       0.4999 |            0.0268 |        0.0073 |                  3.6600 | 0.4512 | 0.5475 |                     0.8841 |
|  3 | 2022-23  | 5v5 only   |        32 |         3577.0000 |       0.5001 |            0.0273 |        0.0084 |                  3.2595 | 0.4542 | 0.5506 |                     0.8263 |
|  4 | 2023-24  | all        |        32 |         4636.7500 |       0.4998 |            0.0264 |        0.0073 |                  3.6010 | 0.4502 | 0.5464 |                     0.7815 |
|  5 | 2023-24  | 5v5 only   |        32 |         3562.0000 |       0.4997 |            0.0269 |        0.0084 |                  3.2054 | 0.4562 | 0.5459 |                     0.7317 |

Cross-season correlation of team win share:

|    | faceoffs   | pair               |   team_share_corr |
|---:|:-----------|:-------------------|------------------:|
|  0 | all        | 2021-22 vs 2022-23 |             0.669 |
|  1 | all        | 2022-23 vs 2023-24 |             0.602 |
|  2 | 5v5 only   | 2021-22 vs 2022-23 |             0.662 |
|  3 | 5v5 only   | 2022-23 vs 2023-24 |             0.553 |
## 6. Gate targets (part D)

### 6. G7 quantities restated for the training seasons (gate_targets_<season>.parquet) vs pbp-derived

Tolerances in `docs/gates.yaml`: regulation tie rate 1.5 pp, shootout share 1.0 pp, EN goals per game 0.03. `reg_tie_rate` is the share of games not decided in regulation (OT or SO); `ot_rate` is the share decided in OT (not SO). `en_goals_per_game` = non-shootout goals with no goalie id (goals into an empty net), both teams. 'match' = within 0.0005 of the gate target.

|    | season   | segment   | metric            |   gate_target |   pbp_derived |   diff |   n_games |   alt_EN_AGAINST_flag | match   |
|---:|:---------|:----------|:------------------|--------------:|--------------:|-------:|----------:|----------------------:|:--------|
|  0 | 2021-22  | all       | reg_tie_rate      |        0.2163 |        0.2163 | 0.0000 |      1401 |              nan      | OK      |
|  1 | 2021-22  | all       | ot_rate           |        0.1435 |        0.1435 | 0.0000 |      1401 |              nan      | OK      |
|  2 | 2021-22  | all       | so_rate           |        0.0728 |        0.0728 | 0.0000 |      1401 |              nan      | OK      |
|  3 | 2021-22  | all       | en_goals_per_game |        0.3712 |        0.3712 | 0.0000 |      1401 |                0.3712 | OK      |
|  4 | 2021-22  | RS        | reg_tie_rate      |        0.2195 |        0.2195 | 0.0000 |      1312 |              nan      | OK      |
|  5 | 2021-22  | RS        | ot_rate           |        0.1418 |        0.1418 | 0.0000 |      1312 |              nan      | OK      |
|  6 | 2021-22  | RS        | so_rate           |        0.0777 |        0.0777 | 0.0000 |      1312 |              nan      | OK      |
|  7 | 2021-22  | RS        | en_goals_per_game |        0.3628 |        0.3628 | 0.0000 |      1312 |                0.3628 | OK      |
|  8 | 2021-22  | PO        | reg_tie_rate      |        0.1685 |        0.1685 | 0.0000 |        89 |              nan      | OK      |
|  9 | 2021-22  | PO        | ot_rate           |        0.1685 |        0.1685 | 0.0000 |        89 |              nan      | OK      |
| 10 | 2021-22  | PO        | so_rate           |        0.0000 |        0.0000 | 0.0000 |        89 |              nan      | OK      |
| 11 | 2021-22  | PO        | en_goals_per_game |        0.4944 |        0.4944 | 0.0000 |        89 |                0.4944 | OK      |
| 12 | 2022-23  | all       | reg_tie_rate      |        0.2329 |        0.2329 | 0.0000 |      1400 |              nan      | OK      |
| 13 | 2022-23  | all       | ot_rate           |        0.1650 |        0.1650 | 0.0000 |      1400 |              nan      | OK      |
| 14 | 2022-23  | all       | so_rate           |        0.0679 |        0.0679 | 0.0000 |      1400 |              nan      | OK      |
| 15 | 2022-23  | all       | en_goals_per_game |        0.3307 |        0.3307 | 0.0000 |      1400 |                0.3307 | OK      |
| 16 | 2022-23  | RS        | reg_tie_rate      |        0.2302 |        0.2302 | 0.0000 |      1312 |              nan      | OK      |
| 17 | 2022-23  | RS        | ot_rate           |        0.1578 |        0.1578 | 0.0000 |      1312 |              nan      | OK      |
| 18 | 2022-23  | RS        | so_rate           |        0.0724 |        0.0724 | 0.0000 |      1312 |              nan      | OK      |
| 19 | 2022-23  | RS        | en_goals_per_game |        0.3338 |        0.3338 | 0.0000 |      1312 |                0.3338 | OK      |
| 20 | 2022-23  | PO        | reg_tie_rate      |        0.2727 |        0.2727 | 0.0000 |        88 |              nan      | OK      |
| 21 | 2022-23  | PO        | ot_rate           |        0.2727 |        0.2727 | 0.0000 |        88 |              nan      | OK      |
| 22 | 2022-23  | PO        | so_rate           |        0.0000 |        0.0000 | 0.0000 |        88 |              nan      | OK      |
| 23 | 2022-23  | PO        | en_goals_per_game |        0.2841 |        0.2841 | 0.0000 |        88 |                0.2841 | OK      |
| 24 | 2023-24  | all       | reg_tie_rate      |        0.2057 |        0.2057 | 0.0000 |      1400 |              nan      | OK      |
| 25 | 2023-24  | all       | ot_rate           |        0.1471 |        0.1471 | 0.0000 |      1400 |              nan      | OK      |
| 26 | 2023-24  | all       | so_rate           |        0.0586 |        0.0586 | 0.0000 |      1400 |              nan      | OK      |
| 27 | 2023-24  | all       | en_goals_per_game |        0.3464 |        0.3464 | 0.0000 |      1400 |                0.3464 | OK      |
| 28 | 2023-24  | RS        | reg_tie_rate      |        0.2073 |        0.2073 | 0.0000 |      1312 |              nan      | OK      |
| 29 | 2023-24  | RS        | ot_rate           |        0.1448 |        0.1448 | 0.0000 |      1312 |              nan      | OK      |
| 30 | 2023-24  | RS        | so_rate           |        0.0625 |        0.0625 | 0.0000 |      1312 |              nan      | OK      |
| 31 | 2023-24  | RS        | en_goals_per_game |        0.3407 |        0.3407 | 0.0000 |      1312 |                0.3407 | OK      |
| 32 | 2023-24  | PO        | reg_tie_rate      |        0.1818 |        0.1818 | 0.0000 |        88 |              nan      | OK      |
| 33 | 2023-24  | PO        | ot_rate           |        0.1818 |        0.1818 | 0.0000 |        88 |              nan      | OK      |
| 34 | 2023-24  | PO        | so_rate           |        0.0000 |        0.0000 | 0.0000 |        88 |              nan      | OK      |
| 35 | 2023-24  | PO        | en_goals_per_game |        0.4318 |        0.4318 | 0.0000 |        88 |                0.4318 | OK      |
Match result: all 36 comparisons (reg_tie_rate, ot_rate, so_rate, en_goals_per_game x 3 seasons x all / RS / PO) agree with the gate target files to within 0.0005 (differences are exactly 0 at the printed precision). No mismatch to list. Note `ot_rate` in the gate files is the share decided in OT, excluding shootouts.

## 7. Candidate constructions (no fit, no preference)

Each line is a construction the data would support and the data limitation that rules any of it out. The PM chooses; these are not recommendations.

**Goalie pull (stage 8a)**
- Empirical lookup of pull time keyed by (deficit 1 / 2 / 3+, penalty-on flag), sampling from the observed seconds-remaining distribution (1a, 1b). Support: trail1 5v5 first pulls n = 1,158 (3 seasons), trail2 783, trail3+ 200; penalty-on cells are 15 to 60 each (UNDERPOWERED). Limit: pooled across teams.
- Deterministic threshold per deficit (about 2:00 / 3:00 / 4:10) plus noise equal to the observed IQR (about 45 s for trail1). Limit: a single threshold cannot reproduce the observed spread (trail1 p10 to p90 of about 65 to 160 s); the 1d table shows trail1 teams are 88% pulled by 5:00 left and 96 to 97% by 3:00.
- Discrete-time hazard (per game second, features: deficit, seconds left, penalty-on, pulled-before flag). Score state must be the pre-event state and closed-loop gated (CBB L23/L27). Limit: team- or coach-specific pull timing has about 36 first pulls per team over three seasons (UNDERPOWERED); only league-level behaviour is identifiable.
- Re-pull after a goal against: 20 to 22% of pulls ended by a goal against are followed by another pull in the same period, median lag 14 to 18 s (1e). Construct as a separate stage-state rule or fold into the hazard model via the pulled-before flag. Limit: the shift chart has the goalie back at the goal's clock time, so 're-pull' is a new gap, not a continuous pull.
- Delayed-penalty pulls (0.65 to 0.71 per game, median 13 s, mostly P1 and P2 leading or tied) as a rider on the stage-1 penalty process: pull with probability p whenever the penalty process raises a delayed penalty. Limit: the pbp DELAYED_PENALTY event is logged for only 42 to 62% of them, so the delayed-penalty rate itself cannot be learned from that event; it must be inferred from pulls ending at an opponent penalty call, and the stage-1 penalty process has no delayed-penalty concept to hang it on.
- Empty-net scoring once pulled: (i) reuse the shot-attempt / SOG / goal cascade with EN_FOR / EN_AGAINST as strength states (the events exist: 7,975 EN_FOR and 2,426 EN_AGAINST unblocked attempts, 3 seasons); (ii) a stand-alone constant per pulled-team-minute (EN against 0.28 to 0.30 per pulled minute counting all pulled time, 0.34 to 0.37 excluding delayed-penalty pulls; EN for about 0.13); (iii) shot rate from the cascade and conversion fixed near 1.0 on SOG into an empty net (observed goal per SOG 0.9993 / 1.000). Limit: EN_FOR goals are 204 to 214 per season, and EN_AGAINST attempts are scarce for team-level responsiveness checks.

**Overtime (stage 8b)**
- 3v3 as a strength state inside the cascade with its own rate offsets (combined 113 attempts, 73 SOG, 12.8 goals per 60). Limit: only 495 3v3 goals in three seasons: any team or goalie responsiveness inside 3v3 is UNDERPOWERED, so strength must come from the 5v5 cascade parameters.
- Direct OT-goal time hazard (constant, or rising by minute: pooled 0.166, 0.209, 0.248, 0.213, 0.286 goals per minute; minutes 4 and 5 are 89 and 94 goals, UNDERPOWERED). Limit: the rise includes the survivor effect of penalty-induced PP time and cannot be separated from it at this sample size; the hazard also averages over 4v3 and 4v4 time.
- OT penalties as an extra stage-1 process in OT (23 to 29 penalties per 100 OT games, 4v3 PP at 14.3 goals per 60 on 68 goals; 4v4 after offsetting minors 6.7 per 60 on 12 goals). Limit: both are UNDERPOWERED; either reuse the regulation penalty process or accept 3v3 only with a fixed non-3v3 share (about 15%).
- Playoff OT is 5v5 continuous (periods 4+; 5v5 OT exposure 7.8k to 14.9k s per season, 319 / 542 / 353 attempts, 14 / 17 / 14 goals): reuse the regulation 5v5 cascade with no shootout; the sample (15 to 24 OT games per season) only permits a consistency check. Limit: 'ties resolve through the OT and shootout models' means PO games need no shootout branch at all.
- Home advantage in OT and SO: OT winner home share 54.7% (n = 583) and SO winner home share 50.2% (n = 279); the OT split is within about one SE of the regulation-decided home share (53 to 54%).

**Shootout (stage 8c)**
- Constant p = 0.31 per attempt with the rules mechanics (3 rounds, then sudden death; home shoots first 80 to 90%; the ordering effect is nil: first shooter 31.3%, second 30.8%). Limit: none beyond sample.
- Shooter x goalie logit with partial pooling. Limit: see data limitation 5. Shooter dispersion is 1.21 over 72 shooters, and the goalie dispersion is 0.91 over 72 goalies, so a goalie effect is not detectable. Shooter and goalie ids are present for 100% of attempts (null count 0).
- Roster-level shooter strength (use only the top three or so skaters by projected shootout use). Limit: pregame shootout shooter order is not published; the three shooters are chosen in game.

**In-game goalie change (stage 8d)**
- Per team-game Bernoulli relief (6.2 to 7.5% RS) with a score-state timing rule (57 to 60% when trailing by 3 or more; 48% of changes occur within a second of an opponent goal; 29 to 37% at a period start). Limit: the cause (performance or injury) is not recorded, and 92 to 96% of pulled starters do not return.
- Hazard on goals against while in net, applied after each goal against (closed-loop gate required). Limit: 163 to 197 events per season is enough for a league-level table only; goalie-specific rates are UNDERPOWERED.
- Fixed relief share of SOG (2.9%). Limit: wrong if the engine is later used per game, but it is the construction that stage-6 saves already see through the starter flag.

**Rebounds and faceoffs (stage 7)**
- Rebound as a post-attempt branch: after each saved SOG, with probability p(class, state) a same-team attempt follows within 3 s. Support: 19,839 proxies after a saved SOG (goal per SOG 0.192), 7,636 after a block (0.153) and 4,934 after a miss (0.170). Limit: the proxy share and goal rate shift by season (limitation 6), the 1 s clock resolution hides ordering at dt = 0 (1,972 cases, goal rate 20%), and blocked-prior proxies are not physical rebounds.
- Rebound as a feature (time since own previous attempt) inside the shot-attempt and goal-given-shot models rather than a branch. Limit: same recording drift; the shot-type field has no rebound flag.
- Faceoff win as a team-level logit (home advantage, team strength). Support is strong: team win-share SD across teams is 0.024 to 0.027 against a 0.007 to 0.008 binomial SD (ratio 3.1 to 3.7), odd / even split correlation 0.73 to 0.88, cross-season 0.55 to 0.67. Limit: player-level matchup needs on-ice centre identification (faceoff winner / loser ids are present on every faceoff), which has to come from shifts.
- Faceoff location after each stoppage kind (icing, offside, goal, penalty): counts per game are 56.5 to 56.9 (RS), 17.0 N / 20.3 home-O / 19.3 home-D, 43.5 of them at 5v5, 10.0 at 5v4. Limit: zone-by-state home-win shares (5j) mix which side holds the man advantage with home / away, so they should not be read as a causal zone effect without a power-play-team view.
