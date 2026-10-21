# INV-78 (Lane D2): second-pass diagnosis of the 55:00 margin compression, 2026-10-21

DIAGNOSIS ONLY. No fix and no tuning. No model table, `sim.py` or `defaults.py` was changed. Every counterfactual (CF) below re-weights recorded sim rates and is labelled DIAGNOSTIC. Nothing from 2025-26 was read.

**Scope.**
- Engine default set (INV-77): H3''-LC2 + T2, A3g-c with the 3v3 OT level, L1x-as, B1a-as, S0t stand-in, C1s. ORACLE GOALIE.
- Pull off, shootout stub, 200 seeds per fold.
- Real side: verified finals and pbp with goalie-out goals removed, as in Lane D1 and Lane E4.
- Regular season unless a table says otherwise.

## Answer

1. **Fold-1 G5b (2023-24, fold-1 tables).**

   | time | fold-1 tie gap | fold-2 tie gap |
   |---|---|---|
   | 20:00 | -0.26 pp | +0.35 pp |
   | 40:00 | +1.42 pp | +2.77 pp |
   | 55:00 | **+0.83 pp (0.77 SE)** | +3.05 pp |

   - **Fold 1 is inside 2 SE.** Real tie SE is 1.09 pp, so 2 SE is 2.18 pp.
   - **Time profile: same shape on both folds.** Below real in P1 (-1.2 to -1.7 pp at 5-15 min), and the gap is built in P2.
   - **Size: smaller on fold 1.** About half of fold 2's at 40:00 and about a quarter at 55:00.
   - **Fold 1's compression sits in a different cell.** Too many |margin| = 1 games (+2.48 pp) and too few |2| (-3.09 pp).
   - **Cells at the re-registered 2.1-2.2 pp tolerance:**
     - fold 1: tie PASS, |1| FAIL by a hair, |2| FAIL;
     - fold 2: tie FAIL, the other cells pass.
   - **Plainly: G5b on one season is at its noise floor.** Pooled over the two folds, the 55:00 tie gap is +1.94 pp (SE about 0.75, 2.6 SE). The rate-implied gap (item 4) is +1.56 / +1.82 pp, pooled +1.69 (SE about 0.64, 2.6 SE). A real defect of about 1.7 pp exists. One season at 2 SE (2.1 pp) cannot resolve it.

2. **Period-2 origin.**
   - Shapley split of the rate-implied gap by period:
     - at 40:00, all of it is P2 (fold 1 +1.91 pp, fold 2 +2.33 pp; P1 about 0);
     - at 55:00, P2 +0.72 / +0.53 pp and P3 +0.86 / +1.43 pp.
   - **The P2 cell is tied play.** Sim tied-P2 goals per 60 are 0.934 (fold 1) and 0.860 (fold 2) of real.
     - On real attempts the served conversion chain gives tied P2 0.952 and 0.873 (redraw SD 0.038), carried by goal | SOG (0.945 / 0.914).
     - Real tied-P2 scoring is the highest P2 bucket. It is 3.10 (fold 1) and 3.21 (fold 2) per team-hour, against 3.0-3.1 in the training seasons.
   - **The P3 cells: trailing teams over-convert and lead-by-1 under-converts, on both folds.**
     - Full chain, trail2+ / trail1: 1.128 / 1.102 (fold 1) and 1.062 / 1.082 (fold 2).
     - Full chain, lead1: 0.928 (fold 1) and 0.907 (fold 2).
   - **What does not move first:**
     - stage-3 attempts (every period x bucket within 0.96-1.05);
     - the stage-1 penalty rate and PP time (no consistent shape across folds; P2-tied PP share 0.946 on fold 1 vs 1.037 on fold 2).
   - **Conversion moves first.**

3. **Chain vs loop.** The chain is not what failed.
   - On each of the four wired loops it reproduces the observed 55:00 tie within 0.0014-0.0027.
   - It maps the realised rate changes to the realised tie changes within 0.0011:
     - goal repair: -0.0075 vs -0.0086;
     - block repair: -0.0030 vs -0.0032.
   - **The violated assumption is in INV-71's CF, not in the chain.** The CF assumed each repair would bring served / actual to 1 in every period x bucket cell. The wired repairs realised only 35% (C1s-sap) and 54% (B1a-as) of the score shape the factors targeted. Both fit score terms pooled over periods, and the real score effect on conversion is concentrated in P3 (and tied P2).
   - **Independence assumptions, checked on the sim:**
     - time-homogeneity within P3: 40-55 rates move the gap by under 0.05 pp;
     - between-game heterogeneity: a strength-stratified chain equals the pooled chain to 0.0003;
     - post-goal dependence: real has a 30-second post-goal lull (rate 0.46-0.71 of base); the engine has none (0.95). It is symmetric and does not move the tie (listed).

4. **Split of the fold-2 55:00 gap (+3.05 pp, C1s default).** The identity is

   gap = (sim observed - sim chain) + (sim chain - real chain) + (real chain - real observed) = -0.16 + 1.82 + 1.38.

   - **(a) Season deviation: about 1.4-1.6 pp, 45-52%.**
     - The 2024-25 real tie sits 1.38 pp below what its own rates imply, against +0.16 expected (sim per-seed mean). The difference, 1.22 pp, is 1.9 per-seed SD (SD 0.64 pp). Fold 1 deviates the other way (+0.62 pp, -1.07 SD).
     - Add 0.14-0.35 pp from the 2024-25 tied-P2 real rate, which is above the other seasons (L23).
   - **(b) Located model defect: about 1.5-1.7 pp, 48-55%.**
     - P3 score x conversion: about 1.0-1.3 pp, 33-41%.
       - Real P3 trailing + lead1 rates swapped in: -1.01 pp (fold 1), -1.26 pp (fold 2).
       - Stages: goal C1s lead1 goal | SOG 0.88 / 0.92; block B1a-as P3 block share trailing 0.96-0.97 and leading 1.03-1.07; miss S0t P3 trailing 0.92-0.97; stage-4 xG +1 to +6% on trailing.
     - Systematic tied-P2 under-conversion (C1s goal | SOG): about 0.3-0.5 pp, 10-16%.
   - **(c) Unattributed: about 0 to -0.2 pp.** This is the chain's approximation error (sim observed - chain = -0.16), inside noise.

## Method and provenance

**Fold-1 tables** (`scripts/diag_margin_inv78_tables_v1.py`). Every component is built from the committed fold-1 artefacts and checked against its committed fold-1 offline prediction, served by the engine's own lookup functions:

| component | check | max diff |
|---|---|---|
| H3''-LC2 hazard | 274k rows, rel | 6.0e-8 |
| A3g-c | 212k rows, rel | 5.9e-8 |
| 3v3 OT level | rel | 1.3e-7 |
| L1x-as | | 1.5e-8 |
| B1a-as | | 1.9e-16 |
| S0t | | 3.0e-8 |
| C1s (starter rows) | | 1.1e-16 |

Two labelled exceptions:
- **T2 penalty-type table.** No fold-1 T2 file was committed. T2 is refit by the committed `models_r5.fit` on 2021-22 + 2022-23, the same call `exp_strength_state_r5_types.py` makes for its fold-1 line. It is LABELLED REFIT and has no offline file to check against.
- **`end_game.ot_level.served_delta` reads the frozen A3g-c cell from the fold-2 model file for any fold** (`A3GC_CELL` is a fixed path). Fold-1 parity failed at 6.7e-3 until the runner pointed it at the fold-1 file. The module was not edited. Listed for the owner: a `fold` argument that it ignores.

**Loops** (`scripts/diag_margin_inv78_sim_v1.py`).
- The recording hook is Lane D1's, with penalty and coincidental counts added. It is a GameState subclass plus pass-through wrappers and draws no random numbers.
- Fold 2 reproduces Lane E4's c1s loop exactly: `cmp` ALL IDENTICAL, 279,600 rows.
- Fold 1: 280,000 sims (1,400 games x 200 seeds).
- Exposure reconstructed from the goal log equals the recorded exposure exactly on both folds (max diff 0 s). This validates the reconstruction used for Lane E4's and Lane G4's loops, which carry no exposure.

**Grading** (`scripts/diag_margin_inv78_grade_v1.py`, `_chain_v1.py`, `_extra_v1.py`).
- `diag_margin_inv78_grade_v1.py`: items 1-3.
- `diag_margin_inv78_chain_v1.py`: the offline conversion chain by period x bucket, current default set (B1a-as, not B0), with a redraw SD per cell (L39).
- `diag_margin_inv78_extra_v1.py`: per-seed noise floor, Shapley attribution, part 3, post-goal dependence, the tied-P2 CF.
- Outputs go to `results/diag_margin_inv78_v1/*.json` and `*_log.txt` (gitignored).
- Real pbp goal sums equal the verified finals on 1,400 / 1,400 games (fold 1) and 1,398 / 1,398 (fold 2).

## 1. Fold-1 G5b (RS, n = 1,312 real games each fold; cells 0 / 1 / 2 / 3+)

| time | fold 1 sim | fold 1 real | fold 1 gap pp | fold 2 sim | fold 2 real | fold 2 gap pp |
|---|---|---|---|---|---|---|
| 20:00 | .331 / .425 / .177 / .068 | .333 / .425 / .173 / .069 | -0.26 / +0.06 / +0.39 / -0.19 | .340 / .424 / .173 / .063 | .336 / .441 / .166 / .056 | +0.35 / -1.73 / +0.71 / +0.66 |
| 40:00 | .223 / .352 / .228 / .197 | .209 / .354 / .234 / .204 | **+1.42** / -0.18 / -0.60 / -0.63 | .227 / .356 / .229 / .189 | .199 / .367 / .261 / .172 | **+2.77** / -1.18 / -3.29 / +1.70 |
| 55:00 | .200 / .323 / .219 / .258 | .192 / .298 / .250 / .260 | **+0.83** / +2.48 / -3.09 / -0.23 | .203 / .328 / .221 / .248 | .172 / .348 / .233 / .247 | **+3.05** / -1.99 / -1.19 / +0.14 |
| 60:00 (not like for like, pull off) | .200 / .319 / .213 / .269 | .162 / .317 / .254 / .267 | +3.72 / ... | .201 / .324 / .215 / .260 | .155 / .348 / .244 / .254 | +4.66 / ... |

- Real tie SE at 55:00: 1.09 pp (fold 1) and 1.04 pp (fold 2). The 55:00 tie gap is +0.77 SE (fold 1) and +2.92 SE (fold 2).

**Tie-gap time profile (pp, every 5 min to 55:00).**

| | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 55 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fold 1 | -1.39 | -1.23 | -1.72 | -0.26 | +0.60 | +0.55 | +1.77 | +1.42 | +2.32 | +1.52 | +0.83 |
| fold 2 | -1.22 | -0.79 | -1.11 | +0.35 | +0.89 | +1.59 | +0.93 | +2.77 | +1.82 | +1.52 | +3.05 |

- The same profile on both folds: below real in P1 (P1 goals are too high, the INV-71 listed item), rising through P2.
- The 40:00-55:00 path differs by season, and every point carries about ±1.1 pp of real SE.

**Compression at 55:00, both folds.**

| | P(\|margin\| ≤ 1) sim | real | gap | margin SD sim | real |
|---|---|---|---|---|---|
| fold 1 | 0.523 | 0.490 (SE 0.014) | +3.3 pp (2.4 SE) | 2.28 | 2.34 (SE 0.05) |
| fold 2 | 0.531 | 0.521 | +1.0 pp (0.8 SE) | 2.23 | 2.21 |

The sim has too many close games on both folds. Whether the excess lands on 0 or on 1 varies by season.

**Noise floor (L39, per-seed redraw).** Each of the 200 seeds is a synthetic season on the real schedule.

| quantity | SD per season |
|---|---|
| observed 55:00 tie | 1.08 pp (fold 1), 1.15 pp (fold 2): equals the binomial SE |
| chain-implied tie from that season's own rates | 0.88-0.90 pp |
| difference (observed - chain) | 0.64-0.68 pp, mean -0.11 / -0.16 pp |
| real chain tie, from Poisson goal-count noise | 0.90 pp |

**Statement for the gate.**
- The fold-1 gap is inside 2 SE. The fold-2 gap is not.
- Neither one-season read can separate a 1.7 pp defect from zero at 2 SE. A pooled two-fold read can (2.6 SE).
- The fold-2 gap is partly a one-season deviation (a) and partly a systematic defect (b). The two are about equal.

## 2. Period-2 origin (both folds; all games, non-EN states; sim / real)

**Stage 3 (attempts per 60) is right in every cell.** The sim / real ratio is within 0.96-1.05 by period x bucket on both folds. The largest deviations are fold 1 P1 lead2+ (1.049) and P2 trail2+ (0.965).

**Goals per 60 (sim / real) by period x bucket (trail2+, trail1, tied, lead1, lead2+).**

| | fold 1 | fold 2 |
|---|---|---|
| P1 | 1.118, 1.058, 1.061, 1.044, 0.963 | 1.028, 1.057, 1.023, 1.070, 1.007 |
| P2 | 0.975, 1.027, **0.965**, 0.922, 1.002 | 1.023, 1.002, **0.861**, 1.030, 1.026 |
| P3 | **1.126, 1.069**, 1.020, **0.945**, 1.013 | **1.059, 1.085**, 0.992, **0.918**, 0.965 |

- Real goal counts per cell: 119-1,361.
- P1 trail2+ / lead2+ (about 120 goals, Poisson SE about 9%) are UNDERPOWERED.
- 5v5 shows the same pattern: P2 tied 0.958 / 0.855; P3 trail1 1.139 / 1.118.

**Stage 1 by period x bucket (sim / real).**

| quantity | fold 1 | fold 2 |
|---|---|---|
| penalties taken / 60 (penalised team's bucket), P2 | 0.994, 1.024, 0.964, 1.031, 1.002 | 0.979, 1.028, 1.037, 1.004, 1.017 |
| penalties taken / 60, P3 | 0.939, 1.075, 1.066, 0.943, 1.040 | 1.046, 1.094, 1.101, 1.085, 1.008 (a level, not a shape) |
| PP time share, P2 | 0.995, 1.014, 0.946, 1.002, 0.934 | 1.014, 0.974, 1.037, 1.004, 0.953 |
| PP time share, P3 | 1.011, 0.936, 1.088, 0.997, 0.866 | 1.052, 1.008, 1.057, 1.004, 0.973 |

- Real penalties per cell: 143-1,387. Real PP goals per cell: 32-534; PP-goal-rate cells are UNDERPOWERED (SE 8-18%).
- **No stage-1 quantity has the same shape on both folds.** The tied-P2 PP share is -5.4% on fold 1 and +3.7% on fold 2. At about 20% of goals from the PP, even the fold-1 value moves tied-P2 goals by about 1%, against -3.5% / -14%. **Stage 1 does not move first.**

**The offline conversion chain on the real test-season attempts.** Served / actual, current default set. Redraw SD of the full chain is 0.04-0.06 per P2 / P3 cell.

| period, bucket | fold 1: unblocked / SOG\|unb / goal\|SOG / xG / **full** | fold 2: same |
|---|---|---|
| P2 tied | 0.994 / 1.007 / 0.945 / 0.999 / **0.952** | 0.983 / 1.007 / 0.914 / 0.963 / **0.873** |
| P3 trail2+ | 1.014 / 1.015 / 1.085 / 1.008 / **1.128** | 1.018 / 1.030 / 0.996 / 1.020 / **1.062** |
| P3 trail1 | 1.015 / 1.041 / 0.985 / 1.060 / **1.102** | 1.013 / 1.022 / 1.023 / 1.019 / **1.082** |
| P3 tied | 1.017 / 1.025 / 0.951 / 1.041 / 1.026 | 0.997 / 1.019 / 0.925 / 1.037 / 0.976 |
| P3 lead1 | 0.990 / 1.017 / **0.879** / 1.037 / **0.928** | 0.975 / 1.002 / **0.922** / 1.012 / **0.907** |

- Block share s / a in P3: trailing 0.968 / 0.964 (fold 1) and 0.960 / 0.971 (fold 2); lead1 1.028 / 1.073.
- Miss s / a in P3: trailing 0.967 / 0.918 (fold 1) and 0.946 / 0.959 (fold 2).
- Regulation overall the chain is 1.08 / 1.05 / 1.02 / 0.96 / 0.99 (fold 1) and 1.05 / 1.04 / 0.97 / 1.00 / 0.99 (fold 2). The period-pooled view hides the P3 shape that both folds share.

**Where the tie excess is carried** (INV-71 chain on regulation RS rates; real rates swapped into one cell).

| swap real rates into the sim chain | fold 1, 55:00 tie change | fold 2, 55:00 tie change |
|---|---|---|
| (sim chain / real chain) | 0.2015 / 0.1859 | 0.2043 / 0.1861 |
| P3 trailing + lead1 | **-0.0101** | **-0.0126** |
| P3 all | -0.0085 | -0.0142 |
| P2 tied | -0.0028 | -0.0064 |
| P2 all | -0.0072 | -0.0053 |
| P1 all | +0.0002 | +0.0015 |
| P2 + P3 all | reaches 0.1857 (= real) | reaches 0.1847 (= real) |

- At 40:00 the tied-P2 swap alone moves the tie by -0.0114 (fold 1) and -0.0252 (fold 2), more than the whole 40:00 gap (+0.0184 / +0.0212). The other cells offset part of it.
- **Team-standardised goal O/E, regulation, tied = 1:**
  - fold 1: sim 1.075 / 1.116 / 1 / 1.026 / 1.021 vs real 1.054 / 1.094 / 1 / 1.090 / 1.034 (z +0.6 / +0.6 / - / -1.8 / -0.4);
  - fold 2: sim 1.075 / 1.118 / 1 / 1.042 / 1.023 vs real 1.000 / 1.038 / 1 / 1.002 / 0.984 (z +2.1 / +2.3 / - / +1.2 / +1.1).
  - Regulation only, so it differs from Lane E4's all-period figure, which has the OT goals in tied.
  - Fold 1's real trailing O/E is 1.09. The fold-2 trailing O/E failure is mostly a 2024-25 real value: across seasons, real trail-1 goal | SOG relative to tied drifts 1.038 → 0.968 (INV-71, L27).
- **Per strength state.** 5v5 carries the pattern (P2 tied 0.958 / 0.855; P3 trail1 1.139 / 1.118; P3 lead1 0.940 / 0.932). PP cells are UNDERPOWERED.
- **Per team.** The team-standardised O/E above is the per-team control. Per-team cells (82 games) are UNDERPOWERED and were not read.
- **Per goalie.** Not relevant to this score-state question; not read.

## 3. Chain vs loop (fold 2, RS; rates per team-hour by period x bucket, reconstructed from each loop's goal log)

| loop | observed tie 20 / 40 / 55 | chain tie 20 / 40 / 55 |
|---|---|---|
| G4 c1s (block B0) | .3403 / .2290 / .2059 | .3455 / .2299 / .2073 |
| G4 sap (B0) | .3399 / .2201 / .1974 | .3452 / .2217 / .1997 |
| E4 c1s (B1a-as) | .3397 / .2267 / .2027 | .3449 / .2275 / .2043 |
| E4 sap (B1a-as) | .3395 / .2176 / .1941 | .3447 / .2192 / .1968 |

| repair | observed tie change | chain on the realised loop rates | INV-71 factor CF (sim rates / served-actual factor) | share of the factor's score shape realised |
|---|---|---|---|---|
| goal C1s -> C1s-sap (E4) | -0.0086 | -0.0075 | -0.0177 | 0.35 |
| goal C1s -> C1s-sap (G4) | -0.0085 | -0.0075 | -0.0178 | 0.34 |
| block B0 -> B1a-as (C1s) | -0.0032 | -0.0030 | -0.0075 | 0.54 |
| block B0 -> B1a-as (sap) | -0.0033 | -0.0029 | -0.0073 | 0.54 |

- **The chain reproduces each loop and each realised change.** On each loop the chain overstates the 55:00 tie by 0.0014-0.0027. It understates the realised change by 0.0002-0.0011.
- **The INV-71 predictions (53% / 22%) failed in the CF step, not in the chain.** Dividing the loop rates by the full served / actual factor assumes the repair makes served = actual in every period x bucket cell. The repairs were period-pooled score terms. C1s-sap carries pooled period interactions; B1a-as carries pooled score dummies. They realised 35% and 54% of the targeted score shape.
- After C1s-sap the loop's P3 trailing rates are near real (2.65 / 2.80 vs 2.61 / 2.71). P3 lead1 stays at -10% (2.39 vs 2.64), and tied P2 at -10% (2.90 vs 3.21).
- **Which independence assumption fails.** None materially, at this resolution:
  - **Time-homogeneity within P3.** Chaining 40-55 rates instead of all-P3 rates moves the sim and real chain ties together. The gap goes 1.56 → 1.43 pp (fold 1) and 1.82 → 1.87 pp (fold 2).
  - **One league rate for every game (no team heterogeneity).** A chain stratified into terciles of the sim's own game-mean margin gives 0.2015 (pooled 0.2015) on fold 1 and 0.2043 (pooled 0.2043) on fold 2, with the observed values inside.
  - **Memoryless rates (no post-goal or strength-state persistence).** Real has a post-goal lull. In the first 30 s after a goal, the rate is 0.71 / 0.46 (fold 1, same / other team) and 0.58 / 0.55 (fold 2) of base. The engine sits at 0.95. By 30-60 s both are at about 1. The lull is symmetric (it suppresses extensions as much as answers) and short. On the real side the chain misfits by +0.62 pp (fold 1) and -1.38 pp (fold 2): opposite signs, inside the 0.65 pp per-season SD of that quantity. **There is no evidence that the lull moves the tie.** Listed as an engine clock-structure item (a post-goal faceoff dead time), not part of this gap.
  - **The weakest assumption is the one the CF added:** that a repair removes the whole served / actual factor in every cell.

## 4. Conclusion

**Split of the fold-2 55:00 gap, +3.05 pp, C1s default set.**

| part | pp | share | evidence |
|---|---|---|---|
| (a) season deviation | 1.4-1.6 | 45-52% | Real tie 1.38 pp below its own rates' chain (expected +0.16, per-season SD 0.64): 1.22 pp, 1.9 SD; fold 1 deviates the other way (-1.07 SD). Plus 0.14-0.35 pp from the 2024-25 tied-P2 real rate (3.21 vs 3.10 fold 1, 3.0-3.1 training; L23). |
| (b) located model defect | 1.5-1.7 | 48-55% | Rate-implied gap 1.82 pp (fold 1 1.56). Of which: **P3 score x conversion** 1.0-1.3 pp (fold 1 1.01, fold 2 1.26), both folds; **tied-P2 conversion, systematic part** 0.3-0.5 pp; P1 about -0.1. |
| (c) unattributed | about -0.2 to 0 | about 0% | The chain's approximation error (sim observed - sim chain = -0.16), inside noise. |

- **Under C1s-sap the gap is +2.18 pp.** Its rate-implied part falls to 1.07 pp: P3 all 0.92, tied P2 0.45. The season part (1.22) is then more than half of it.

**Located defect, by stage.** The per-attempt conversion's score response is pooled over periods. In real play it is concentrated in P3, plus a tied-P2 level.

| stage, sub-model | P3 defect (both folds) | other | status |
|---|---|---|---|
| 6, goal C1s (score dummies pooled; C1s-sap's period interactions pooled) | lead1 goal \| SOG 0.88 / 0.92; P3 tied 0.95 / 0.93 | tied P2 0.945 / 0.914 | the largest single piece |
| 5, block B1a-as (score dummies pooled over periods) | trailing block share 0.96-0.97; leading 1.03-1.07 | | |
| 5b, miss S0t (no score term) | trailing miss 0.92-0.97 | | D49's step 0 pooled over periods and found no gradient; the P3 gradient was not tested |
| 4, L1x-as | trailing xG / unblocked attempt +1 to +6% | | smaller, mixed |

Not responsible: stage 3 (attempts), stage 1 (penalties, PP time), team heterogeneity, the chain's independence assumptions.

**Pre-registration the located defect needs (the PM writes it; nothing here was fitted).**

1. **Step 0, a round across stages 5 / 5b / 6, training seasons only (2021-22 to 2023-24).**
   - Test: does a score-bucket x P3 interaction (and a tied x P2 term) in block share, miss share and goal | SOG exceed the pooled score term by more than 2 SE?
   - Size each band by a parametric redraw first (L39). The per-cell chain redraw SD here is 0.04-0.06, so a per-cell ±3% band is below its floor.
   - Stop rule as in SM-R3: no arm if no gradient survives.
2. **Arms, if step 0 passes** (each against its incumbent, same folds; with the closed loop):
   - C1s + bucket x P3;
   - B1a-as + bucket x P3;
   - S0t + trailing x P3.
3. **The G5b read itself.**
   - Re-register it as a pooled two-fold read: the fold-1 + fold-2 mean tie gap within 2 pooled SE (about 1.5 pp).
   - Add the rate-implied (chain) gap as a lower-variance companion (per-season SD about 0.9 pp vs 1.1 pp).
   - Report the |margin| ≤ 1 share. On fold 1 the compression shows there, not in the tie.
   - A one-season tie gate at 2 SE (2.1 pp) has little power against a 1.7 pp defect.

**Listed.**
- `ot_level.served_delta` ignores `fold` for the frozen A3g-c cell (fixed fold-2 path). Owner fix, not done here.
- No committed fold-1 T2 file. Here it is refit by the committed code (labelled).
- The engine has no post-goal dead time (real first-30-s rate about 0.5-0.7 of base).
- P1 goals are too high on both folds (fold 1 full chain P1 tied 1.053; INV-71 item).
- G4 PP save % (pre-existing).

**Underpowered cells.**
- P1 trail2+ / lead2+.
- Every PP-goal cell by period x bucket.
- Per-team O/E.
- Each one-season 55:00 tie read (±1.0-1.1 pp SE).
- Each one-season rate-implied gap (±0.9 pp).

## Clock (wall, -04:00)

- 16:13 start; reading 16:13-16:18.
- Fold-1 tables + parity: 16:18:33-16:20:19 (hazard 45 s, attempts 26 s; cached after).
- Slice: fold 1 and fold 2, seeds 0-24, 2 processes, 16:22:37-16:25:29. 157 s per 25 seeds; projected 7 min for the rest at 8 processes x 1 thread, under 15 min, so no box request.
- Loop: seeds 25-199 for both folds, 8 processes x 1 thread, 16:26:44-16:33:55. `cmp` fold 2: ALL IDENTICAL to Lane E4.
- Grade: 16:34:19-16:34:45. Chain: 16:36:36-16:36:57. Extra: 16:38:20-16:39:26, 16:40, 16:41.
- No process of this lane is running (checked 16:41:55).

## Incidents

None. No process outside this lane was touched. Only lane files were written: four scripts, this report, and `results/diag_margin_inv78_v1/` (gitignored).
