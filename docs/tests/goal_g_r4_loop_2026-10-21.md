# G-R4 closed loop: C1s vs C1s-sap, paired seeds (Lane G4, 2026-10-21)

Generated 2026-10-21 15:46:33 -0400 by `scripts/run_engine_goal_r4_v1.py grade`. Fold 2 (2024-25), goalie pull OFF, ORACLE GOALIE (D8), engine DEFAULT table set (block B0 and miss S0t STAND-INS, stage 4 L1x-as); only attr['goal'] differs between arms, so every RNG stream is aligned. Real = verified finals / pbp with goalie-out goals removed (Lane D1's construction, `diag_margin_inv71_grade_v1.load_real`).

## |margin| distribution by time, regular season (gate) (n real = 1312; cells 0 / 1 / 2 / 3+)

| time   |   real_0 |   real_1 |   real_2 |   real_3 |   real_tie_se |   c1s_0 |   c1s_1 |   c1s_2 |   c1s_3 |   sap_0 |   sap_1 |   sap_2 |   sap_3 |
|:-------|---------:|---------:|---------:|---------:|--------------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| 20:00  |   0.3361 |   0.4413 |   0.1662 |   0.0564 |        0.0130 |  0.3403 |  0.4263 |  0.1722 |  0.0612 |  0.3399 |  0.4332 |  0.1698 |  0.0571 |
| 40:00  |   0.1989 |   0.3674 |   0.2614 |   0.1723 |        0.0110 |  0.2290 |  0.3597 |  0.2283 |  0.1830 |  0.2201 |  0.3592 |  0.2389 |  0.1818 |
| 55:00  |   0.1723 |   0.3483 |   0.2325 |   0.2470 |        0.0104 |  0.2059 |  0.3334 |  0.2211 |  0.2395 |  0.1974 |  0.3312 |  0.2273 |  0.2442 |
| 60:00  |   0.1547 |   0.3476 |   0.2439 |   0.2538 |        0.0100 |  0.2043 |  0.3296 |  0.2159 |  0.2503 |  0.1953 |  0.3274 |  0.2216 |  0.2556 |

- **G5b c1s** (55:00, RS): sim - real (pp) tie +3.36, |1| -1.49, |2| -1.13, 3+ -0.74; real tie SE 1.04 pp -> **FAIL**
- **G5b sap** (55:00, RS): sim - real (pp) tie +2.51, |1| -1.71, |2| -0.52, 3+ -0.28; real tie SE 1.04 pp -> **FAIL**

## |margin| distribution by time, all games (n real = 1398; cells 0 / 1 / 2 / 3+)

| time   |   real_0 |   real_1 |   real_2 |   real_3 |   real_tie_se |   c1s_0 |   c1s_1 |   c1s_2 |   c1s_3 |   sap_0 |   sap_1 |   sap_2 |   sap_3 |
|:-------|---------:|---------:|---------:|---------:|--------------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| 20:00  |   0.3383 |   0.4371 |   0.1681 |   0.0565 |        0.0127 |  0.3403 |  0.4263 |  0.1722 |  0.0612 |  0.3401 |  0.4331 |  0.1697 |  0.0572 |
| 40:00  |   0.1953 |   0.3727 |   0.2561 |   0.1760 |        0.0106 |  0.2294 |  0.3598 |  0.2281 |  0.1828 |  0.2207 |  0.3592 |  0.2386 |  0.1816 |
| 55:00  |   0.1753 |   0.3448 |   0.2310 |   0.2489 |        0.0102 |  0.2061 |  0.3335 |  0.2213 |  0.2392 |  0.1979 |  0.3313 |  0.2270 |  0.2438 |
| 60:00  |   0.1567 |   0.3441 |   0.2425 |   0.2568 |        0.0097 |  0.2045 |  0.3297 |  0.2161 |  0.2497 |  0.1958 |  0.3276 |  0.2216 |  0.2550 |

## Team-standardised goal O/E by pre-goal score bucket (tied = 1), all games, non-EN states

E = exposure x the team's own season goal rate (Lane D1 item 2b). Gate: |sim - real| <= 1 real SE per bucket.

| series   |   trail2+ |   trail1 |   tied |   lead1 |   lead2+ |
|:---------|----------:|---------:|-------:|--------:|---------:|
| real     |    0.9600 |   0.9959 | 1.0000 |  0.9622 |   0.9452 |
| real SE  |    0.0343 |   0.0326 | 0.0268 |  0.0318 |   0.0336 |
| sim c1s  |    1.0345 |   1.0804 | 1.0000 |  0.9786 |   0.9460 |
| z c1s    |    2.1702 |   2.5910 | 0.0000 |  0.5169 |   0.0237 |
| sim sap  |    1.0116 |   1.0491 | 1.0000 |  0.9769 |   0.9347 |
| z sap    |    1.5040 |   1.6311 | 0.0000 |  0.4614 |  -0.3130 |

- **O/E c1s**: max |z| 2.59 -> **FAIL**
- **O/E sap**: max |z| 1.63 -> **FAIL**

## G4: save % by state in the loop (sap vs c1s; paired seed-block SE, 500 resamples)

| state   |     c1s |     sap |   sap_minus_c1s_pp |   paired_seed_se_pp |
|:--------|--------:|--------:|-------------------:|--------------------:|
| 3v3     | 79.7946 | 79.7161 |            -0.0785 |              0.0464 |
| 4v4     | 87.8499 | 87.9654 |             0.1155 |              0.0209 |
| 5v5     | 90.9907 | 91.0933 |             0.1026 |              0.0015 |
| PK      | 90.7426 | 90.8150 |             0.0723 |              0.0117 |
| PP      | 85.3265 | 85.4605 |             0.1340 |              0.0054 |
| all     | 90.0566 | 90.1650 |             0.1084 |              0.0015 |

Reading: G4 'unchanged within noise' = |sap - c1s| <= 2 paired SE in every gated state, and the overall sv % of each arm within the g4_sv_pp 0.5 pp of actual (actual from the stage-6 rows, below).

|     |   actual_sv_pct |   c1s_minus_actual_pp |   sap_minus_actual_pp |
|:----|----------------:|----------------------:|----------------------:|
| 5v5 |         91.0111 |               -0.0204 |                0.0822 |
| PP  |         84.8210 |                0.5055 |                0.6395 |
| PK  |         90.8958 |               -0.1532 |               -0.0808 |
| 4v4 |         88.5417 |               -0.6918 |               -0.5763 |
| 3v3 |         80.4087 |               -0.6141 |               -0.6926 |
| all |         90.0047 |                0.0519 |                0.1603 |

