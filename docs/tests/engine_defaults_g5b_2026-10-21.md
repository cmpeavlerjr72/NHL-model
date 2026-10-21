# INV-77 default set and the pre-registered G5b read (Lane E4, 2026-10-21; D53)

Generated 2026-10-21 16:02 by `scripts/run_engine_defaults_v2.py grade` (grading code of Lane G4's `run_engine_goal_r4_v1.py`, which uses Lane D1's real-data construction `diag_margin_inv71_grade_v1.load_real`). Fold 2 (2024-25), 200 paired seeds (0-199), goalie pull OFF, shootout flag OFF (50/50 stub), ORACLE GOALIE (D8). Configuration = the NEW `defaults.default_attr` (stage 4 L1x-as, **block B1a-as**, miss S0t STAND-IN, goal C1s) with `defaults.att_table` (A3g-c, **3v3 OT level ON**). Arms: **c1s** = that default set; **sap** = the same with attr["goal"] replaced by C1s-sap (`sc_game` flag). Only attr["goal"] differs, so all RNG streams are aligned. Real = verified finals / pbp with goalie-out goals removed. Both arms' outputs carry `block_model` (B1a-as) and no `block:` stand-in label (checked in the run). (The section text below is produced by the G-R4 grader; wherever it says "block B0" it refers to the configuration of Lane G4's earlier loop, not this one.)

Clock: tables + parity 3 s; 8 processes (2 arms x 4 x 50 seeds, 25-seed chunks) 15:55:27 - 16:02:16 (about 194 s per 25-seed chunk with 8 concurrent; a 10-seed solo slice took 55 s, so 200 seeds solo would be about 18 min per arm); grade 14 s.

## Summary (margin cells at 55:00, regular season, sim minus real, pp; gate 1.5 pp on the tie share and each of 0 / 1 / 2 / 3+)

| arm | tie (0) | 1 | 2 | 3+ | G5b |
|:--|--:|--:|--:|--:|:--|
| c1s | +3.05 | -1.99 | -1.19 | +0.14 | FAIL (tie, |1|) |
| sap | +2.18 | -2.22 | -0.56 | +0.60 | FAIL (tie, |1|) |

Real tie share 0.1723 (SE 1.04 pp, n = 1312 regular-season games). Reference, Lane G4's loop (block B0, OT level off): c1s +3.36, sap +2.51. The B1a-as block term and the OT level move the tie by 0.3 pp each arm (about 0.3 pp of the 3.36 / 2.51 pp gap in each arm, against the 22% of the gap INV-71 credited to the block score term, which would be about 0.7 pp). The |margin|=1 cell also fails in both arms (the sim has too few one-goal games at 55:00, as it has too many ties); the |2| and 3+ cells pass.

Goal O/E (team-standardised, tied = 1, all games, non-EN states): trail-1 c1s 1.076 (z +2.46), sap 1.044 (z +1.48) vs real 0.996 (SE 0.033); max |z| c1s 2.46 (trail-1), sap 1.54 (trail2+). Gate (1 real SE): both FAIL; sap closes about 0.03 of the 0.08 trail-1 excess. Lane G4's loop: trail-1 1.080 / 1.049.

G4 (save % by state, sim minus actual, pp; gate g4_sv_pp 0.5): c1s overall +0.05, 5v5 -0.03, PP +0.50, PK -0.16 (4v4 -0.71, 3v3 -0.54 reported); sap overall +0.16, 5v5 +0.08, PP +0.64, PK -0.09 (4v4 -0.59, 3v3 -0.64 reported). PP is at the tolerance edge for c1s (+0.501) and beyond it for sap (+0.635); identical to Lane G4's loop to 0.01 pp (+0.506 / +0.640), so the PP offset is a standing finding of the goal model, not a product of this change. sap minus c1s: +0.11 pp overall (paired seed SE 0.0015); the grader's "2 paired SE" reading flags every state, because streams are paired and the SE is tiny; the shift is the same 0.11 pp that Lane G4 judged inside the real data's noise (about 1 real SE), carried here unchanged.

G1-G3 against Lane E3's loop (`gates_*_engine_defaults_*`): G3 PASS in both arms (as E3); G2 (gate report) PASS in both arms, where E3's was FAIL on the 3v3 per-60 attempts (58.16 vs actual 55.23); now 55.59 (c1s) / 55.51 (sap) vs 55.23 -> PASS, the OT-level repair. The G2 decomposition table still lists one PK row FAIL (13.32 vs 14.65 in both arms; E3 had the same row FAIL at 14.64), unchanged. G1 is NEEDS-INSTRUMENTATION (no event-level output), as in E3.

G7 (reported; pull and shootout flags off, so not a gate read): regulation tie rate (final, incl. OT/SO stub) c1s 0.2014 (PASS at 1.5 pp), sap 0.1927 (-1.55 pp, FAIL) vs real 0.2082; shootout rate 0.0650 / 0.0619 vs 0.0551 (PASS at 1.0 pp; stub); EN goals per game 0 vs 0.41 (pull flag off). Without the pull process the 60:00 tie share is not comparable, so these are reported only. G5, G6, G9 FAIL in the plumbing reports for the known stage 7-8 reasons, not gate reads.

Per-arm per-state detail: `docs/tests/gates_g3_sl_r7_L1xas_engine_defaults_v2_{c1s,sap}.md`, `gates_g2_sl_r7_L1xas_engine_defaults_v2_{c1s,sap}.md`, `gates_g5g7_engine_defaults_v2_{c1s,sap}_2026-10-21.md`. Per-team detail is in the G3 reports (UNDERPOWERED, labelled there).

Disposition (D53): with every repair wired (G-R4 sap, SM-R3 stand-in still miss S0t, B1a-as, OT level), the 55:00 tie gap is +2.18 pp (sap) against 1.5 pp: G5b FAIL; remaining gap to be reported as unattributed (INV-71's 15%) plus the lag of the H90 as-of levels, and the next step is a diagnosis, not a tune.

## |margin| distribution by time, regular season (gate) (n real = 1312; cells 0 / 1 / 2 / 3+)

| time   |   real_0 |   real_1 |   real_2 |   real_3 |   real_tie_se |   c1s_0 |   c1s_1 |   c1s_2 |   c1s_3 |   sap_0 |   sap_1 |   sap_2 |   sap_3 |
|:-------|---------:|---------:|---------:|---------:|--------------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| 20:00  |   0.3361 |   0.4413 |   0.1662 |   0.0564 |        0.0130 |  0.3397 |  0.4240 |  0.1732 |  0.0630 |  0.3395 |  0.4309 |  0.1707 |  0.0588 |
| 40:00  |   0.1989 |   0.3674 |   0.2614 |   0.1723 |        0.0110 |  0.2267 |  0.3556 |  0.2285 |  0.1892 |  0.2176 |  0.3551 |  0.2394 |  0.1879 |
| 55:00  |   0.1723 |   0.3483 |   0.2325 |   0.2470 |        0.0104 |  0.2027 |  0.3284 |  0.2205 |  0.2483 |  0.1941 |  0.3261 |  0.2269 |  0.2529 |
| 60:00  |   0.1547 |   0.3476 |   0.2439 |   0.2538 |        0.0100 |  0.2013 |  0.3239 |  0.2151 |  0.2597 |  0.1923 |  0.3217 |  0.2210 |  0.2650 |

- **G5b c1s** (55:00, RS): sim - real (pp) tie +3.05, |1| -1.99, |2| -1.19, 3+ +0.14; real tie SE 1.04 pp -> **FAIL**
- **G5b sap** (55:00, RS): sim - real (pp) tie +2.18, |1| -2.22, |2| -0.56, 3+ +0.60; real tie SE 1.04 pp -> **FAIL**

## |margin| distribution by time, all games (n real = 1398; cells 0 / 1 / 2 / 3+)

| time   |   real_0 |   real_1 |   real_2 |   real_3 |   real_tie_se |   c1s_0 |   c1s_1 |   c1s_2 |   c1s_3 |   sap_0 |   sap_1 |   sap_2 |   sap_3 |
|:-------|---------:|---------:|---------:|---------:|--------------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|--------:|
| 20:00  |   0.3383 |   0.4371 |   0.1681 |   0.0565 |        0.0127 |  0.3396 |  0.4240 |  0.1733 |  0.0631 |  0.3396 |  0.4308 |  0.1707 |  0.0589 |
| 40:00  |   0.1953 |   0.3727 |   0.2561 |   0.1760 |        0.0106 |  0.2270 |  0.3555 |  0.2284 |  0.1891 |  0.2182 |  0.3549 |  0.2392 |  0.1877 |
| 55:00  |   0.1753 |   0.3448 |   0.2310 |   0.2489 |        0.0102 |  0.2028 |  0.3284 |  0.2206 |  0.2481 |  0.1945 |  0.3262 |  0.2266 |  0.2527 |
| 60:00  |   0.1567 |   0.3441 |   0.2425 |   0.2568 |        0.0097 |  0.2014 |  0.3241 |  0.2152 |  0.2593 |  0.1927 |  0.3219 |  0.2209 |  0.2646 |

## Team-standardised goal O/E by pre-goal score bucket (tied = 1), all games, non-EN states

E = exposure x the team's own season goal rate (Lane D1 item 2b). Gate: |sim - real| <= 1 real SE per bucket.

| series   |   trail2+ |   trail1 |   tied |   lead1 |   lead2+ |
|:---------|----------:|---------:|-------:|--------:|---------:|
| real     |    0.9600 |   0.9959 | 1.0000 |  0.9622 |   0.9452 |
| real SE  |    0.0343 |   0.0326 | 0.0268 |  0.0318 |   0.0336 |
| sim c1s  |    1.0351 |   1.0761 | 1.0000 |  1.0032 |   0.9848 |
| z c1s    |    2.1878 |   2.4588 | 0.0000 |  1.2885 |   1.1779 |
| sim sap  |    1.0129 |   1.0441 | 1.0000 |  1.0018 |   0.9725 |
| z sap    |    1.5421 |   1.4795 | 0.0000 |  1.2443 |   0.8099 |

- **O/E c1s**: max |z| 2.46 -> **FAIL**
- **O/E sap**: max |z| 1.54 -> **FAIL**

## G4: save % by state in the loop (sap vs c1s; paired seed-block SE, 500 resamples)

| state   |     c1s |     sap |   sap_minus_c1s_pp |   paired_seed_se_pp |
|:--------|--------:|--------:|-------------------:|--------------------:|
| 3v3     | 79.8643 | 79.7706 |            -0.0937 |              0.0494 |
| 4v4     | 87.8320 | 87.9491 |             0.1171 |              0.0214 |
| 5v5     | 90.9850 | 91.0883 |             0.1032 |              0.0015 |
| PK      | 90.7393 | 90.8108 |             0.0715 |              0.0122 |
| PP      | 85.3223 | 85.4560 |             0.1338 |              0.0055 |
| all     | 90.0560 | 90.1648 |             0.1088 |              0.0015 |

Reading: G4 'unchanged within noise' = |sap - c1s| <= 2 paired SE in every gated state, and the overall sv % of each arm within the g4_sv_pp 0.5 pp of actual (actual from the stage-6 rows, below).

|     |   actual_sv_pct |   c1s_minus_actual_pp |   sap_minus_actual_pp |
|:----|----------------:|----------------------:|----------------------:|
| 5v5 |         91.0111 |               -0.0261 |                0.0772 |
| PP  |         84.8210 |                0.5012 |                0.6350 |
| PK  |         90.8958 |               -0.1566 |               -0.0850 |
| 4v4 |         88.5417 |               -0.7097 |               -0.5926 |
| 3v3 |         80.4087 |               -0.5443 |               -0.6381 |
| all |         90.0047 |                0.0513 |                0.1601 |

