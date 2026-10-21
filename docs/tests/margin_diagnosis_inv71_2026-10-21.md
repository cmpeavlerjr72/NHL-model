# INV-71 (Lane D1): where the regulation margin compression comes from, 2026-10-21

DIAGNOSIS ONLY. No fix, no tuning, and no model table was changed. Every counterfactual below re-weights recorded sim output or rates, is labelled DIAGNOSTIC, and is not a proposed fix.

Scope:
- Fold 2 (2024-25), pull flag OFF: the engine default set, ORACLE GOALIE, with the B0 / S0t STAND-INS. 200 seeds.
- Regular season (1,312 games) unless a table says "all" (1,398, playoffs included, which matches the G7 numbers).
- Nothing from 2025-26 was read.

## Answer

The compression exists **before any pull effect**. It is created in period 2 (P2) and carried through period 3 (P3).

The cause is the downstream per-attempt conversion's response to the score state. The attempt volume responds correctly. Relative to tied play, the engine converts a trailing team's attempts into goals about 8% too often. Three sub-models do this:

1. **C1s, goal | SOG score dummies (stage 6).** The main cause. Roughly 55% of the 55:00 tie gap.
2. **Block B0 stand-in, which has no score term (stage 5).** Roughly 20-25%.
3. **Miss S0t stand-in, which has no score term (stage 5b).** Roughly 5%.

Stage 3 (attempts), stage 4 (L1x-as), team spread, goalie spread, home ice and period structure each explain about 0-8%. About 15% is unattributed, and that is inside the sampling noise of the real tie rate.

| quantity | sim | real | gap | SE (real) |
|---|---|---|---|---|
| tie at 20:00 (RS, no goalie-out goals) | 0.3403 | 0.3361 | +0.004 | 0.013 (0.3 SE, clean) |
| tie at 40:00 | 0.2290 | 0.1989 | **+0.030** | 0.011 (2.7 SE) |
| tie at 55:00 | 0.2059 | 0.1723 | **+0.034** | 0.010 (3.2 SE) |
| tie at 55:00, all 1,398 games | 0.2061 | 0.1753 | +0.031 | 0.010 (3.0 SE) |
| tie at 60:00, all games, real without goalie-out goals ("actual pre-pull tie rate") | 0.2045 | **0.1567** | +0.048 | 0.010 (4.9 SE) |
| tie at 60:00, all games, real all goals (the G7 pass by compensation) | 0.2045 | 0.2082 | -0.004 | 0.011 |

How the 60:00 numbers split:

- **Pull off.** The +0.048 gap splits into +0.031 already present at 55:00 (65%) and +0.017 in 55:00-60:00 (35%).
  - The 55:00-60:00 part is not like for like. The pull-off sim lets a trailing team chase at 5v5 for the full 5 minutes. A real trailing team chases at 6v5, and those goals are removed from the real side.
  - So this 35% belongs to the absent pull process, which the pull-on G7 read measures. It is not upstream compression.
- **Pull on (D46).** The gap is 0.2376 vs 0.2082 = +0.029. That equals the 55:00 compression (+0.031) within noise, so the stage-8 mechanics add about 0 net.

## Method and provenance

- **Instrumentation.** I used my own recording runner, `scripts/diag_margin_inv71_sim_v1.py`. It loads `sim.py` and `defaults.py` pinned at 8464696 through `git show`, and leaves the working tree (Lane H8b's in-progress edits) untouched. The hook has three parts:
  - a GameState subclass that logs every goal (second, pre-goal score, skaters) and snapshots the score at 20:00 / 40:00 / 55:00 / 60:00;
  - two pass-through wrappers that aggregate attempts and exposure by (period, team-view state, pre-event score bucket);
  - it draws no random numbers.
- **Identity check.** `cmp` shows that all 279,600 game x seed rows are identical to Lane E3's `results/engine_defaults_v1` (which is file-identical to H8a's pull-off loop), and that the goal log reproduces every final score.
- **Real data.**
  - Finals: `verified_finals_v2`. The pbp goal sums equal the verified finals on 1,398 of 1,398 games.
  - Goals and shots: `events_20242025`.
  - Attempts, goals and exposure by team-view state x score bucket x period: `attempt_rows_v1_20242025` (non-EN rows).
  - Per-attempt outcomes: `attempt_attr_v1_20242025`.
- **"Goalie-out goals"** are goals with either goalie out. In the regular season that is 749: 702 late-pull goals (0.535 per game) and 47 others, mostly delayed-penalty extra attacker, 44 of them before 55:00.
- **Grading and analysis scripts.**
  - `scripts/diag_margin_inv71_grade_v1.py`: items 1-6.
  - `scripts/diag_margin_inv71_chain_v1.py`: the offline conversion chain by score bucket, served by the same default tables.
  - `scripts/diag_margin_inv71_markov_v1.py`: the tie-gap attribution.
  - Outputs: `results/diag_margin_inv71_v1/{grade,chain,markov}.json` and `*_log.txt` (gitignored).

## 1. Margin and score state in time (RS, n = 1,312)

**|margin| at 0 / 1 / 2 / 3+, with SD**

| time | sim | real, all goals | real, no goalie-out goals |
|---|---|---|---|
| 20:00 | 0.340 / 0.426 / 0.172 / 0.061, SD 1.33 | 0.333 / 0.445 / 0.163 / 0.059, SD 1.32 | 0.336 / 0.441 / 0.166 / 0.056, SD 1.32 |
| 40:00 | **0.229** / 0.360 / 0.228 / 0.183, SD 1.92 | 0.195 / 0.370 / 0.260 / 0.175, SD 1.93 | **0.199** / 0.367 / 0.261 / 0.172, SD 1.92 |
| 55:00 | **0.206** / 0.333 / 0.221 / 0.240, SD 2.19 | 0.175 / 0.345 / 0.234 / 0.245, SD 2.22 | **0.172** / 0.348 / 0.233 / 0.247, SD 2.21 |
| 60:00 | 0.204 / 0.330 / 0.216 / 0.250, SD 2.24 | 0.207 / 0.176 / 0.219 / 0.399, SD 2.56 | 0.155 / 0.348 / 0.244 / 0.254, SD 2.28 |

- **Shape, not width.** The margin SD at 40:00 and 55:00 is right to within 1% (1.917 vs 1.919; 2.185 vs 2.207). The sim's distribution is more peaked: too many ties and too few 2-goal margins (0.228 vs 0.261 at 40:00), with the 3+ tail about equal.
  - The engine pulls 1-goal games back to level too often and holds them there. This is the signature of state-dependent catch-up, not of a narrow game-mean spread.
- **Home score state at 55:00 (home margin -3..+3).**

  | | -3 | -2 | -1 | 0 | +1 | +2 | +3 |
  |---|---|---|---|---|---|---|---|
  | sim | .103 | .101 | .159 | .206 | .174 | .121 | .137 |
  | real, no goalie-out goals | .105 | .098 | .159 | .172 | .189 | .134 | .142 |

  The excess ties come mostly out of home +1 / +2, which ties into item 6 (home level).
- **Without the pull goals, real ties fall from 55:00 to 60:00** (0.172 to 0.155). The sim stays flat (0.206 to 0.204) because, with no pull, its trailing teams chase at 5v5.
- **The actual pre-pull tie rate** (60:00 without goalie-out goals) is 0.1547 (RS) and 0.1567 (all games).

## 2. Score effects (L23 / L27), all 1,398 games, non-EN states

**Per team-hour by pre-event team-view bucket (trail2+, trail1, tied, lead1, lead2+), all periods**

| | trail2+ | trail1 | tied | lead1 | lead2+ |
|---|---|---|---|---|---|
| time share, sim / real | .145 / .145 | .176 / .179 | .358 / .353 | .176 / .179 | .145 / .145 |
| attempts/60, sim / real | 63.4 / 64.3 | 62.6 / 62.5 | 59.0 / 58.7 | 54.8 / 54.4 | 51.3 / 50.6 |
| goals/60, sim | 2.835 | **2.976** | **2.764** | 2.715 | 2.640 |
| goals/60, real | 2.695 | 2.816 | 2.833 | 2.737 | 2.735 |
| goals/60, sim / real | **1.052** | **1.057** | **0.976** | 0.992 | 0.965 |

- **By period, the trailing-goal excess is in P1 and P3, and the tied deficit is in P2.**
  - P1, sim / real by bucket: 1.04, 1.07, 1.03, 1.06, 0.98.
  - P2: 1.03, 1.02, **0.87**, 1.02, 1.00.
  - P3: 1.07, **1.10**, 1.00, **0.91**, 0.93.
  - 5v5 shows the same pattern (P3 trail1 1.13, lead1 0.92).
  - Real goal counts per cell: 120-1,348. Every P1 trail2+ / lead2+ cell (about 120 goals, Poisson SE about 9%) is UNDERPOWERED.
- **Attempts match** in every bucket and period (sim / real 0.97-1.04).

**Team-standardised O/E (E = exposure x the team's own season rate; tied = 1).** This removes who is trailing and leaves only the response to the score.

| | trail2+ | trail1 | tied | lead1 | lead2+ |
|---|---|---|---|---|---|
| attempts, sim | 1.082 | 1.063 | 1 | 0.926 | 0.863 |
| attempts, real | 1.101 | 1.069 | 1 | 0.925 | 0.857 |
| goals, sim | **1.034** | **1.080** | 1 | 0.979 | 0.946 |
| goals, real (SE about 0.034) | 0.960 | 0.996 | 1 | 0.962 | 0.945 |

**Sign and size.** Trailing teams' goal rate relative to tied is about 8% too high in the closed loop: trail1 +8.4%, trail2+ +7.7%, each about 2.3 SE. Attempt volume does not cause it; volume score effects are right, if anything 1-2% weak at trail2+. Per-attempt conversion causes it.

- **Offline check (no loop): stage-3 A3g-c on the real fold-2 rows**, predicted / actual by bucket: 0.983, 1.000, 1.006, 1.015, 1.018. There is no over-response.
- **The pre-event construction is sound.** Every score feature is pre-event. This is a level and shape bias in the score terms, not the CBB L23 / L27 post-event feedback defect.

**The conversion chain by bucket.** Served by the default tables on every real non-EN fold-2 attempt (`chain_v1`), served / actual, all periods:

| | trail2+ | trail1 | tied | lead1 | lead2+ |
|---|---|---|---|---|---|
| actual block % | 29.9 | 29.3 | 27.9 | 26.9 | 26.0 |
| block, B0 (flat in score) | 0.953 | 0.972 | 1.010 | 1.058 | 1.091 |
| actual miss % of unblocked | 35.0 | 34.8 | 33.7 | 33.5 | 33.3 |
| miss, S0t (flat in score) | 0.960 | 0.967 | 0.990 | 0.991 | 0.991 |
| actual goal % of SOG | 9.19 | 9.78 | 10.10 | 10.35 | 10.95 |
| goal \| SOG, C1s | 1.004 | **1.028** | **0.968** | 0.993 | 0.980 |
| xG per unblocked attempt, stage 4 L1x-as | 1.014 | 1.001 | 0.999 | 1.010 | 1.006 |
| **goals per attempt, full chain** | **1.059** | **1.057** | **0.973** | 0.988 | 0.960 |

Relative to tied, the full chain over-converts trailing teams' attempts by 8.6%. The closed-loop excess of 8.4% matches it. The split, as log shares of trail1 / tied:

- **C1s: about 65%.** The pooled score dummies give tied 0.968 and trail1 1.028.
- **B0: about 18%.** B0 serves one block share regardless of score, but real leaders block about 1.5 pp more of a trailing team's attempts.
- **S0t: about 14%.** Real trailing teams miss about 1 pp more.
- **Stage 4: about 2%.**

**These biases are systematic, not one-season noise.**

- Block and miss shares follow the same score gradient in all four seasons from 2021-22 to 2024-25 (block: trailing above tied above leading every season). B0 and S0t have no score term by construction (D32 / D37 stand-ins).
- C1s shows the same holdout shape on **fold 1** (2023-24 test, fold-1 model): trail2+ 1.047, trail1 1.006, tied **0.973**, lead1 0.927, lead2+ 0.994.
- Over seasons, real trail1 goal | SOG relative to tied drifts **1.038, 1.029, 0.998, 0.968** (2021-22 to 2024-25; SE about 0.033 each). Pooled dummies lag a trend, which is the L27 pattern applied to a score term.
- The fold-2 P2-tied cell (real tied goals/60 3.21, the highest P2 bucket) does look like a one-season deviation; the training seasons sit at 3.0-3.1 and in the middle of the buckets. Per L23 it is listed and not chased. Setting it to its P1 / P3 mean changes the C1s share below from -0.0179 to -0.0157.

## 3. Team spread

**Game level, RS.** Actual margin regressed on the sim game-mean margin (D32 helper on deciles of the sim mean):

| margin | slope b (SE) | R (CI) |
|---|---|---|
| 55:00 | 0.923 (0.121) | 1.054 (0.84-1.42), UNDERPOWERED |
| 60:00, real without goalie-out goals | 0.905 (0.116) | 1.088 (0.87-1.47), UNDERPOWERED |
| final, real without goalie-out goals | 0.931 (0.115) | 1.077 |
| final, real all goals | 1.090 (0.129) | 0.924 |

- **The game means are not too flat.** If anything they are slightly steep, within noise.
- **Variance at 55:00.** Sim between-game 0.246 and within-game 4.529 (total 4.775). Real total 4.906, residual about the fitted line 4.696.

**Per team (32 teams x 82 games).**

| per-game quantity | b | R | sim SD | real SD (noise-corrected) |
|---|---|---|---|---|
| margin, real without goalie-out goals | 0.984 (bootstrap CI 0.74-1.25) | 1.02 | 0.346 | 0.398 |
| attempt differential | 1.066 | 0.94 | 5.99 | 6.44 |
| SOG differential | 0.828 | 1.21 | 2.88 | 2.62 |
| goals for | 0.860 | 1.16 | 0.181 | 0.163 |
| goals against | 1.106 | 0.90 | 0.203 | 0.252 |
| sv% against | 1.98 | 0.50 | 0.0032 | raw 0.0086 |

- **The ratings' effect on margin is carried at the right slope**, with correlation 0.72.
- Stage by stage it is carried by offsetting errors: SOG too steep, finishing and goaltending too flat (the sv% row: sim 0.0032 vs real raw 0.0086).
- This is a watch item for the D33-style over-response and for goaltending (item 4). It is **not** a source of the tie gap.

## 4. Goalie spread (RS, 71 starters with at least 10 starts; sim = box-score starter faces every SOG, ORACLE)

| | sim | real |
|---|---|---|
| league sv% | 0.9005 | 0.9012 |
| per-starter sv% SD | 0.0039 | 0.0074 (binomial-noise-corrected; raw 0.0132) |
| goals against per start, SD across starters | 0.211 | 0.249 (noise-corrected) |

- Real per-starter sv% regressed on sim: **b 2.13 (bootstrap CI 1.43-2.55)**, R 0.47; correlation 0.52.
- The served goalie and team-defence effect is about half as spread as the realised season.
- This is a different measurement from E2's offline served R 0.975 (deciles of the goalie rating, CI 0.55-2.72, UNDERPOWERED). The noise correction ignores per-game shot-quality overdispersion, so the real SD is an upper bound.
- **Effect on the tie rate is small.** DIAGNOSTIC: random game-level tilts that add the whole missing between-game variance (0.131, the sim-vs-real total-variance gap at 55:00) lower the 55:00 tie by only **0.0026**, at most 8% of the gap.
- It matters for G5 / G9 calibration, not for G7. Listed as a separate item.

## 5. Period structure (RS)

Goals per game (sim vs real without goalie-out goals; real all goals in brackets):

| period | sim | real |
|---|---|---|
| P1 | 1.799 | 1.723 (+4.4%, about 2.1 SE) |
| P2 | 1.934 | 1.983 (-2.4%) |
| P3, 40:00-55:00 | 1.340 | 1.325 |
| P3, 55:00-60:00 | 0.411 | 0.275 [+0.54 goalie-out goals] |
| OT | 0.138 | 0.146 |

- The 55:00-60:00 row is not like for like: real games spend about 78 s per game pulled.
- **First goal.** Quantiles 10 / 25 / 50 / 75%: sim 84 / 212 / 481 / 946 s vs real 93 / 236 / 509 / 986 s. P(no goal by 20:00): 0.171 vs 0.176 (SE 0.011).
- **Effect on the tie rate is about 0.** The 20:00 tie rate matches; swapping the real P1 rates into the tie chain changes the 55:00 tie by +0.001.
- The P1 excess is the same conversion chain: P1 full chain 1.02-1.07 in every bucket except lead2+.

## 6. G5 / G6 decomposition, with DIAGNOSTIC counterfactuals

All 1,398 games, pull off. For "real, no goalie-out goals", goalie-out goals are removed from the final score, the tie is the 60:00 margin without them, and home win is the real result.

| arm | reg tie | margin SD | home goal diff | home win | score corr | total mean | total SD |
|---|---|---|---|---|---|---|---|
| sim | 0.2045 | 2.270 | 0.208 | 0.539 | +0.035 | 5.64 | 2.35 |
| real, all goals | 0.2082 | 2.599 | 0.330 | 0.565 | -0.115 | 6.03 | 2.32 |
| real, no goalie-out goals | 0.1567 | 2.310 | 0.289 | 0.565 | -0.018 | 5.46 | 2.27 |
| CF: game-mean spread stretched by b (tilting) | 0.2055 | 2.258 | 0.208 | 0.539 | +0.040 | 5.63 | 2.35 |
| CF: home level shifted to real | 0.2040 | 2.271 | 0.268 | 0.549 | +0.035 | 5.64 | 2.35 |
| CF: both | 0.2050 | 2.258 | 0.268 | 0.549 | +0.040 | 5.63 | 2.35 |

- **Margin SD.** The G5 margin-SD failure (ratio 0.873) is mostly the absent EN goals: without goalie-out goals the ratio is 2.270 / 2.310 = 0.98. Team spread does not move the tie (+0.001).
- **Score correlation.** EN goals explain -0.097 of the -0.150 gap. The remaining +0.053 (SE about 0.027, about 2 SE) has the sign that over-converting trailing teams produce: the scores co-move. It is consistent with item 2 but not separately attributed (UNDERPOWERED).
- **Home ice (G6).** The home goal differential is 0.08 short of real without goalie-out goals (0.208 vs 0.289, SE about 0.063, 1.3 SE: UNDERPOWERED). Home win is 0.539 vs 0.565 (1.9 SE). Shifting the home level moves the tie by only -0.0006.
- **Total.** P(total = k) and the total mean are dominated by EN goals and by OT parity; like for like at 55:00, sim totals are within 0.9% of real.

**Tie-gap attribution.** DIAGNOSTIC margin Markov chain (`markov_v1`): symmetric, one-second steps, per-team-hour goal rates by period x bucket.

- **Validation.** On the sim's own rates the chain reproduces the sim tie (0.2075 vs observed 0.2059 at 55:00). On the real rates it gives 0.1865 vs observed 0.1723, 1.4 SE of the real tie. The rate-explained gap is therefore 0.021 of the observed 0.034.
- **Method.** Divide the sim rates, by period and bucket, by each served / actual factor from the chain table.

| sim rates corrected for | 55:00 tie | change | share of observed RS gap (+0.0336) |
|---|---|---|---|
| none (chain) | 0.2075 | | |
| C1s goal \| SOG | 0.1896 | **-0.0179** | **53%** (the fold-1 residual shape gives -0.0182) |
| B0 block | 0.2000 | **-0.0075** | **22%** |
| S0t miss | 0.2053-0.2062 | -0.0013 to -0.0022 | 4-7% |
| stage 4 L1x-as xG | 0.2087 | +0.0012 | -3% |
| B0 x S0t x C1s | 0.1813 | -0.0262 | 78% |
| full served chain | 0.1828 | -0.0247 | 74% |
| team spread (item 6 CF) | | +0.001 | about 0% |
| home level (item 6 CF) | | -0.0006 | 2% |
| missing between-game heterogeneity (item 4, upper bound) | | -0.0026 | at most 8% |
| unattributed | | about 0.005 | about 15%, inside the real tie's SE (0.010) |

Swapping real rates in by bucket group: the trailing rates carry 70% of the chain gap, tied 23%, leading 8%.

## 7. Conclusion

**Responsible sub-models.** These are levels and shapes of score terms in the per-attempt conversion, all upstream of stage 8.

| sub-model | defect | share of the 55:00 tie gap (+0.034 RS) | systematic? |
|---|---|---|---|
| goal C1s (stage 6, CONFIRMED-INCUMBENT provisional) | pooled score dummies with no period interaction; tied under-predicted (fold 2 0.968, fold 1 0.973), trailing over-predicted relative to tied | about 53% | yes: both holdout folds, plus a season trend |
| block B0 (stage 5, STAND-IN) | no score term; real leaders block 1.5-3 pp more | about 22% | yes: same gradient in 4 seasons |
| miss S0t (stage 5b, STAND-IN) | no score term; real trailing teams miss about 1 pp more | about 5% | yes |
| stage 3 A3g-c, stage 4 L1x-as, team spread, home level, period structure | none material | 0 to 3% each | |
| goalie / team-defence spread under-carried (b 2.13) | real, but changes the tie by at most 0.003 | at most 8% | listed |
| unattributed | | about 15% | inside noise |

**Tie-rate gaps.**

- **With pulls (0.2376 vs 0.2082, +0.029).** About 100% is this upstream compression (+0.031 at 55:00, all games), carried through. It splits roughly 55 / 22 / 5 across C1s / B0 / S0t, with about 15% unattributed. The pull mechanics net about 0 (within noise).
- **Pull off, 60:00 (0.2045 vs 0.1567, +0.048).**
  - 65% (+0.031) is the same compression.
  - 35% (+0.017) is the absent pull process in 55:00-60:00 (5v5 chase vs real 6v5). That is not a compression, and EG-R1 / EG-R2 own it.

**Pre-registrations needed (the PM writes them; nothing here was fitted).**

1. **Goal C1s score terms (stage 6).**
   - Arms, against the incumbent C1s:
     - C1s with as-of (recency-weighted) score-dummy levels, per L27 (a pooled coefficient lags a trend);
     - C1s with score bucket x period (P1 / P2 / P3) or x last-10-min;
     - both.
   - Same folds; LL per SOG as the primary metric.
   - New pre-registered checks: holdout served / actual by score bucket, relative to tied, within ±3% on fold 2 and on the fold-1 D13 guard.
   - Closed-loop gates: team-standardised goal O/E by bucket within 1 SE of real, and the 55:00 |margin| distribution (tie within 1 SE of real).
2. **Block B0 + score bucket (stage 5).**
   - A flat-in-team score term (5 buckets, optionally x P3).
   - It is a construction change to the stand-in, so it needs its own arm and parity checks; it is independent of the parked team ratings (D34).
   - Check: block share by bucket on fold 2 within ±1 pp.
3. **Miss S0t + score bucket (stage 5b).** Same form as 2; can share the round with it.
4. **Order.** The closed-loop 55:00 tie / |margin| gate runs after 1-3 and before any stage-8 acceptance or EG-R2 level fit. Stage 8 is not adjusted to absorb any of this.

**Listed, not pre-registered here.**

- The per-starter sv% spread is under-carried in the closed loop (b 2.13, CI 1.43-2.55). Reconcile it with E2's offline goalie R before reading it as a goal-model defect.
- G6 home level is 0.08 goals per game short (UNDERPOWERED).
- P1 goals are +4.4% (about 2.1 SE).
- The fold-2 P2-tied scoring cell is a one-season deviation (L23).

**Underpowered cells.**

- Every P1 trail2+ / lead2+ cell (about 120 real goals).
- The OT cells.
- D32 game-level R (CI wider than the band).
- The home goal differential.
- The score-correlation residual.
- Each 55:00 tie comparison carries about ±0.010 real SE.

## Clock (wall)

- 14:31 start.
- Slice: seeds 0-24, 14:35:12-14:38:00 (168 s, 165 s of sim). Projected 4 x 50 seeds in parallel at about 7 min, under the 15-minute limit, so no box request.
- Loop: seeds 25-199 in 4 processes x 2 threads, 14:38:13-14:44:33.
- `cmp` identical. Grading and chain 14:44-14:51; Markov 14:51.

## Incidents

None. No process outside this lane was touched. Only lane files were edited.
