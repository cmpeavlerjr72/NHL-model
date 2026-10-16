# SL-R6: arena-free shot-quality ratings, L1x fixed-scale quality tilt on L0s (cascade stage 4, Lane A6, 2026-10-16)

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R6 (inherits SL-R4 / R3 / R2 / R1); D28, D32. Brief: `docs/briefs/lane_A6_shot_attribute_r6_2026-10-16.md`.
- Code: `scripts/build_shot_attribute_tables_v2.py` (Qr / Qa ratings), `src/nhl_sim/shot_attribute/models_x.py` (L1x), `scripts/train_shot_attribute_v6.py` (step 0, fold-1 grid, fits, checks, predictions), `scripts/diag_shot_attribute_r6_insample_l33.py` (OT diagnostic).

**Outcome: STOPPED before fold 2. Under both levels (E, then M1 K500 per D35), the inherited in-sample stratum check fails at 3v3 by about 0.005 pp over the 0.5% line. Nothing on 2024-25 was predicted or read.**
- **Step 0** (3f1aa27). Qr and Qa remove the arena contamination of the ratings: corr with the arena factor goes from -0.13 / -0.20 to +0.02 / +0.02 (Qr) and +0.01 / -0.05 (Qa). The per-season response is still not flat for Qa (p 0.03 / 0.008). Qr is closest to flat (p 0.24 / 0.08).
- **Fold-1 grid.** Under E (005dd23) and again under D35's M1 K500 (13e43e3), the pick is the same: Qa x0.75. Under M1 K500, s_f is 1.195 and s_a 0.972; it is the best-LL cell (+0.033 nats per game vs L0s), with fold-1 R 0.969 / 0.944. No Qr cell lies within 2 SE.
- **In-sample check** (fold-2 training rows, SL-R4 rule): **FAIL**. 3v3 is -0.503% vs L0s (n 3,752; limit 0.5%); under E it was -0.508%. Every other gated stratum is within 0.07%. Cause: L33. All 3v3 rows are OT and tied, and the pooled "tied" score coefficient learned on regulation rows is applied on top of an OT baseline that already conditions on the state.
- **D28 guard** (fold 1, L1x minus L0s): **PASS** under both levels. xG is within 0.07% in every gated cell, tiers and types within 0.09 pp.
- **Diagnostic** (training rows only, not an arm): with the fitted terms switched off on OT rows, 3v3 is -0.02% and every stratum passes, under both levels.
- **No engine change and no closed loop.** sim.py was not touched.
- **PM ruling needed** (section 6).

## Clock (date, EDT)

| step | start | end |
|---|---|---|
| lane start (brief read) | 12:18:31 | |
| Qr / Qa ratings build (both folds) | 12:21:22 | 12:21:40 |
| step 0, first attempt (serial, untuned optimiser; killed by my own 590 s timeout, discarded) | 12:24:02 | 12:33:52 |
| step 0 (15 fits, 5 parallel workers) | 12:36:01 | 12:42:10 |
| fold-1 grid under E (2 free fits + 14 cells, 7 workers); commit 005dd23 | 12:43:10 | 12:49:42 |
| fits, in-sample check (FAIL), D28 guard (PASS), OT diagnostic, all under E | 12:50:24 | 12:57:04 |
| D35 received; fold-1 grid re-run under M1 K500; commit 13e43e3 | 12:58:08 | 13:04:54 |
| fold-2 fits + fold-1 fits / predictions under M1 K500 | 13:05:08 | 13:07:42 |
| in-sample check (FAIL, exit 3), D28 guard (PASS), OT diagnostic, under M1 K500 | 13:07:42 | 13:09:44 |

Every step ran in minutes, so no box request was filed.

## Constructions (labelled readings)

Both are the SL-R1 rating (shrunk mean xG_ref per unblocked attempt, log ratio to the snapshot league mean, w 0.7, b 1,000, per rating group ES / PP / PK, for and against, fold-specific xG_ref), built from different inputs. `created_at < puck_drop` is asserted on every row.

- **Qr (road games only).** A team's for-rating accumulates only its attempts in games it plays on the road; its against-rating only the attempts it allows on the road. Neutral-site games count as road for both teams (as in the arena factor). The as-of rating is served for every game. The snapshot league mean is over the road accumulations; the prior is last season's final Qr.
- **Qa (arena-adjusted).** All games. Each attempt's recorded distance d is replaced by d x exp(-arena_f), with arena_f the as-of arena distance factor of the game's arena (`arena_dist_v1`, past games only, c = 1,200). The angle is kept, the cell is re-banded from the adjusted distance, and behind-the-net stays behind. The attempt's xG_ref is read at the adjusted class. 4.2-4.4% of attempts change cell.

## Step 0: per-season coefficients (training seasons only; committed before step 1)

`train_shot_attribute_v6.py step0` -> `docs/models/shot_attribute/sl_r6_step0.json`.

**The "L1-style coefficient" (labelled reading).** The SL-R1 L1 is a factorised MNL with one coefficient per class, so it has no single rating coefficient. Step 0 therefore fits the L1x form freely on each season alone: L0s fit on that season (unlevelled) + s_f x own rating x c_k + s_a x opponent rating x c_k + per-class home / score / rest terms. Here c_k is the centred log xG_ref of the class (fold-2 xG_ref). The SEs are conditional on the per-class terms (model-based, and a game-cluster sandwich). The flatness test is Cochran's Q over the three seasons (cluster SEs), plus a weighted linear trend.

| construction | rating | 2021-22 | 2022-23 | 2023-24 | weighted mean | Q (df 2) | p | trend / season (SE) | trend z |
|---|---|---|---|---|---|---|---|---|---|
| orig (SL-R1) | for | 1.645 (0.164) | 1.426 (0.136) | 1.329 (0.113) | 1.429 | 2.52 | 0.28 | -0.137 (0.093) | -1.48 |
| orig (SL-R1) | against | 1.722 (0.175) | 1.018 (0.143) | 1.199 (0.139) | 1.260 | 10.01 | 0.007 | -0.216 (0.109) | -1.98 |
| Qr | for | 1.711 (0.232) | 1.280 (0.150) | 1.298 (0.127) | 1.353 | 2.81 | 0.24 | -0.125 (0.111) | -1.12 |
| Qr | against | 0.813 (0.268) | 0.763 (0.209) | 1.356 (0.194) | 1.023 | 5.10 | 0.078 | +0.291 (0.157) | +1.85 |
| Qa | for | 1.753 (0.184) | 1.495 (0.138) | 1.210 (0.109) | 1.396 | 7.22 | 0.027 | -0.230 (0.094) | -2.46 |
| Qa | against | 1.695 (0.192) | 0.944 (0.159) | 1.103 (0.146) | 1.189 | 9.66 | 0.008 | -0.240 (0.116) | -2.07 |

Pooled fits (reference): fold-1 train orig 1.523 / 1.305, Qr 1.434 / 0.788, Qa 1.607 / 1.256; fold-2 train orig 1.441 / 1.264, Qr 1.372 / 0.978, Qa 1.431 / 1.200 (for / against).

Rating spread and arena contamination (ES, team-game level, fold-2 training seasons):

| construction | SD for | SD against | corr(for, arena_f) | corr(against, arena_f) |
|---|---|---|---|---|
| orig | 0.0282 | 0.0251 | -0.133 | -0.202 |
| Qr | 0.0241 | 0.0177 | +0.018 | +0.018 |
| Qa | 0.0277 | 0.0233 | +0.008 | -0.050 |

**Reading (no decision here):**
- Both rebuilt ratings remove the arena contamination. The SL-R1 rating correlates -0.13 / -0.20 with the arena factor (a long-distance-recording arena lowers its home team's recorded xG for and against). Qr and Qa sit at +0.02 / +0.02 and +0.01 / -0.05.
- **The per-season response is not flat for the SL-R1 rating or Qa.** "Against" has p 0.007 (orig) and 0.008 (Qa); Qa "for" falls at z -2.5. Both "for" series fall from 2021-22 onward.
- **Qr is the closest to flat.** For: p 0.24. Against: p 0.08, and it RISES in 2023-24 (0.81, 0.76, 1.36). The per-season SEs are 0.13-0.27, so a 3-season flatness test is weakly powered (labelled).
- Every pooled coefficient is above 1 in "for". That is expected: the rating is a shrunk log-ratio of mean xG, and s is the tilt per unit rating along c, not a calibrated ratio.

## Step 2: fold-1 s-grid and construction pick (committed before any fold-2 fit)

`train_shot_attribute_v6.py grid` (12:43:10 to 12:49:42) -> `docs/models/shot_attribute/sl_r6_grid_fold1.csv`, `sl_r6_frozen_params.json`.

**Setup (labelled readings):**
- **Fitted s.** For each construction, (s_f, s_a) are fitted freely on fold-1 training (2021-22 + 2022-23) together with the per-class home / score / rest terms, on L0s levelled by E (E is 0 on fold 1, D24 / D28). Fold-1 ratings and xG_ref are used. Results: Qr 1.409 / 0.821; Qa 1.593 / 1.289.
- **"s" is a pair with one common multiplier.** The spec names one s, but there are two ratings (own for, opponent against). Each keeps its fitted value, and the grid multiplier m in {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0} scales both. At each m, s is fixed and only the home / score / rest terms are refit. Each cell then predicts 2023-24 (the fold-1 test season).
- **LL** is per game on 2023-24, with a paired game-block bootstrap SE (1,000) vs the best cell.
- **R** is the D32 slope ratio on ES rows (5v5 + 4v4 + 3v3), with deciles of the row's own as-of rating (for) and the opponent's (against). The grid CIs use 200 resamples.
- **Selection.** Over all 14 cells, both constructions together: among the cells within 2 SE of the best LL, take the smallest max(|log R_for|, |log R_against|). Ties within 0.02 go to Qr, then to m closest to 1.

| cell | s_f | s_a | LL/game vs L0s | vs best (SE) | within 2 SE | R for (CI) | R against (CI) | old Q5-Q1 for / against | max abs log R | xG rel |
|---|---|---|---|---|---|---|---|---|---|---|
| Qr x0.25 | 0.352 | 0.205 | +0.0015 | -0.046 (0.009) | no | 0.29 (0.24-0.39) | 0.22 (0.17-0.36) | 0.29 / 0.22 | 1.517 | +2.47% |
| Qr x0.5 | 0.704 | 0.411 | +0.0194 | -0.029 (0.007) | no | 0.57 (0.47-0.72) | 0.35 (0.28-0.53) | 0.56 / 0.37 | 1.038 | +2.47% |
| Qr x0.75 | 1.057 | 0.616 | +0.0307 | -0.017 (0.006) | no | 0.84 (0.70-1.06) | 0.49 (0.39-0.73) | 0.83 / 0.53 | 0.710 | +2.47% |
| Qr x1.0 | 1.409 | 0.821 | +0.0355 | -0.012 (0.006) | no | 1.12 (0.93-1.42) | 0.63 (0.50-0.93) | 1.10 / 0.69 | 0.461 | +2.48% |
| Qr x1.25 | 1.761 | 1.027 | +0.0337 | -0.014 (0.007) | no | 1.40 (1.16-1.77) | 0.77 (0.61-1.14) | 1.38 / 0.85 | 0.335 | +2.48% |
| Qr x1.5 | 2.113 | 1.232 | +0.0254 | -0.023 (0.009) | no | 1.67 | 0.91 | 1.65 / 1.00 | 0.515 | +2.49% |
| Qr x2.0 | 2.818 | 1.643 | -0.0106 | -0.059 (0.013) | no | 2.22 | 1.19 | 2.18 / 1.32 | 0.799 | +2.50% |
| Qa x0.25 | 0.398 | 0.322 | +0.0139 | -0.034 (0.007) | no | 0.34 | 0.42 | 0.34 / 0.37 | 1.076 | +2.47% |
| Qa x0.5 | 0.797 | 0.644 | +0.0375 | -0.010 (0.004) | no | 0.65 (0.55-0.80) | 0.68 (0.54-1.05) | 0.66 / 0.64 | 0.433 | +2.48% |
| **Qa x0.75** | **1.195** | **0.967** | **+0.0479** | **best** | **yes** | **0.957 (0.81-1.17)** | **0.949 (0.77-1.43)** | 0.99 / 0.92 | **0.052** | +2.50% |
| Qa x1.0 | 1.593 | 1.289 | +0.0452 | -0.003 (0.004) | yes | 1.27 (1.07-1.54) | 1.22 (0.99-1.80) | 1.31 / 1.20 | 0.236 | +2.51% |
| Qa x1.25 | 1.991 | 1.611 | +0.0294 | -0.019 (0.007) | no | 1.57 | 1.50 | 1.63 / 1.47 | 0.453 | +2.52% |
| Qa x1.5 | 2.390 | 1.933 | +0.0006 | -0.047 (0.011) | no | 1.88 | 1.77 | 1.95 / 1.75 | 0.632 | +2.54% |
| Qa x2.0 | 3.186 | 2.578 | -0.0960 | -0.144 (0.019) | no | 2.49 | 2.31 | 2.58 / 2.29 | 0.913 | +2.57% |

**Selected: Qa, m = 0.75, so s_f = 1.1948 and s_a = 0.9666 (frozen).** It is both the best-LL cell and the cell with R closest to 1 (0.957 / 0.949).

**The construction pick (reported):**
- Qa is picked. No Qr cell lies within 2 SE of the best LL; Qr x1.0 is 2.2 SE below.
- Qr cannot be put in band with one multiplier. Its fitted "against" response is weaker relative to "for": at m 1.0, R is 1.12 / 0.63, and its best cell (x1.25, 1.40 / 0.77) misses both ends.
- Fold-1 xG overall sits at +2.5% for every cell. That is level E being 0 on fold 1 (the D28 caveat), not the tilt; the D28 guard reads L1x minus L0s.
- The LL gain over L0s on fold 1 is small: +0.048 nats per game. L1x has no clock or period terms (not in the spec).

## D35: level E replaced by M1 K500

- **When.** The PM correction D35 arrived after the fold-1 grid, fits, in-sample check and guard under E, and before anything on fold 2 was predicted or read. So it was applied as instructed:
  - the L0s level was switched to M1_K500 (`mix_level_v2.parquet`; as-of, non-zero on fold 1, unlike E);
  - every step that depends on L0s was re-run;
  - the new outputs are versioned files (`sl_r6_d35_frozen_params.json`, `sl_r6_d35_grid_fold1.csv`, `results/shot_attribute_r6_d35`, salt `SL-R6-D35-2026-10-16`).
- **The E-run artefacts are kept as the record** (`sl_r6_frozen_params.json`, `sl_r6_grid_fold1.csv`, commit 005dd23). Step 0 used unlevelled per-season L0s, so it is unaffected.
- **Grid under M1 K500** (13e43e3): the same pick, **Qa x0.75 (s_f 1.1947, s_a 0.9715)**.
  - It is the best-LL cell, +0.0329 nats per game vs L0s.
  - Fold-1 R is 0.969 (CI 0.82-1.19) / 0.944 (CI 0.77-1.40). Only Qa x1.0 is also within 2 SE (-0.0039, SE 0.0034; R 1.28 / 1.22).
  - Every Qr cell is at least 2.3 SE below. Fold-1 xG overall is now +1.1% for every cell (M1 K500 is live on fold 1), against +2.5% under E.

  The section 2 table above is the E run. The D35 table is in the csv; its R and LL pattern is the same within 0.02.

## 3. Fits (frozen s; only the home / score / rest terms are refit per fold)

- **L1x** starts from W = 0. **L1xs2** is the same fit from a seeded random start (normal(0, 0.05), seed 2).
- **Floor.** Under M1 K500, the largest |L1x - L1xs2| probability difference is 9.2e-7 (fold 2) and 1.2e-6 (fold 1); under E it was 6.3e-7. Fold 2 converges in 203-207 iterations to the same loss (3.1848134 per row under M1 K500). The floor is effectively 0 (convex fit).
- **EN rows** are served L0s levelled, bit-identical.

## 4. In-sample stratum check (fold-2 training rows, SL-R4 rule: L1x within +/-0.5% xG_ref of L0s in every stratum with n >= 2,000): FAIL

`train_shot_attribute_v6.py insample` exited 3 under both levels, so `pred2` refuses to run. Data: `results/shot_attribute_r6_d35/insample.json`. The level only changes the "L0s vs actual" column.

| stratum | n | L0s vs actual (M1 K500) | **L1x vs L0s (M1 K500)** | L1x vs L0s (E) | high / medium / low pp (M1 K500) | gated |
|---|---|---|---|---|---|---|
| 5v5 | 287,840 | -0.06% | +0.019% | +0.019% | +0.016 / -0.040 / +0.024 | yes |
| PP | 53,097 | -1.21% | +0.071% | +0.068% | +0.033 / -0.014 / -0.020 | yes |
| PK | 9,170 | +0.71% | +0.028% | +0.037% | +0.038 / -0.091 / +0.054 | yes |
| 4v4 | 4,334 | -4.66% | +0.065% | +0.068% | +0.024 / -0.037 / +0.013 | yes |
| **3v3** | 3,752 | -4.91% | **-0.503%** | -0.508% | -0.234 / +0.006 / +0.228 | yes: **FAIL** |
| 5v5 OT | 857 | +8.06% | -1.86% | -1.83% | -0.405 / -0.418 / +0.823 | no |
| 4v4 OT | 197 | -14.79% | -0.59% | -0.59% | | no |
| ENF / ENA | 5,721 / 2,145 | -0.32% / +0.35% | 0 (bit-identical) | 0 | 0 | reported |

Every regulation stratum is within 0.1%. The miss is confined to OT rows, where it is about -0.5% to -1.9% xG, with the high tier moving to the low tier.

**Cause: L33.** The fitted score dummies are per class and pooled over the non-EN states. They are centred on the training means, so a mean row is served L0s. Every OT row is tied, so it gets the full "tied vs average" deviation that was learned on regulation 5v5. But the OT baselines already condition on the state. L33 forbids exactly this ("strata whose state is defined by score and clock (empty net, OT) get their own model or the baseline only, never shared score / clock splits"). My construction kept EN on the baseline, as SL-R4 requires, but not OT. That is my construction defect, and the check caught it.

**Diagnostic** (`scripts/diag_shot_attribute_r6_insample_l33.py`, `results/shot_attribute_r6_d35/insample_ot0_diag.json`; training rows only; not an arm). L1x-ot0 is the same model with the fitted home / score / rest terms switched off on OT rows, in fit and serving; OT rows keep L0s plus the rating tilt. Every stratum then passes: 3v3 -0.023%, 4v4 +0.110%, 5v5 +0.022%, PP +0.075%, PK +0.048%, 5v5 OT -0.65% (n 857).

## 5. D28 guard (fold 1, every SL-R1 bias check read on L1x minus L0s; EN reported): PASS

`results/shot_attribute_r6_d35/fold1/guard.json`. Under M1 K500:
- **xG L1x / L0s:** overall +0.011%, ES -0.004%, PP +0.068%, PK -0.021%.
- **Tiers and types:** every tier and type cell within 0.09 pp, with no FAIL row.

Under E it also passed.

Level read on 2023-24 (reported):

| level | arm | xG overall | ES | PP | PK | ENF | high pp | R for | R against |
|---|---|---|---|---|---|---|---|---|---|
| M1 K500 (as graded, D35) | L0s | +1.13% | +1.53% | +0.18% | +2.59% | -2.74% | +0.08 | 0.43 | 0.21 |
| M1 K500 | L1x | +1.14% | +1.52% | +0.24% | +2.56% | -2.74% | +0.09 | 0.969 | 0.944 |
| O oracle (diagnostic) | L0s | +0.39% | +0.35% | +1.09% | -0.39% | -3.46% | -0.01 | 0.11 | -0.46 |
| O oracle | L1x | +0.40% | +0.34% | +1.16% | -0.40% | -3.46% | -0.00 | 0.966 | 0.950 |

## 6. Stop, and what the PM must rule

The SL-R6 spec says "Everything not listed is as in SL-R4". SL-R4's "Checks before fold 2 (stop if any fails)" include this in-sample check. The SL-R6 list names the D28 guard but not the in-sample check, and so does the brief's step 4. I read the check as inherited and stopped, because a stop keeps the holdout clean whichever way the PM rules. Reading fold 2 would have closed off a construction fix.

Options (proposals; the PM decides):
1. **Rule the check not inherited.** Then run `pred2` (it needs a one-line override of the insample gate), add `--round r6` to the grader with D32 R as the responsiveness gate, then grade, decide, and run step 5.
2. **Accept L1x-ot0 as an L33 construction fix before any fold-2 read** (the D28 kind: a defect caught before the holdout, fixed by a standing learning). Fit it at the same frozen s, re-run insample and the D28 guard, then continue as in option 1.
   - **Recommended.**
   - The rating scale, the construction pick and the grid are unchanged in substance, because OT rows are about 1% of the rows. The fold-1 R would be re-reported under ot0.
3. **Report the round as failed** (no SL-R7 without the user).

**Not done:**
- No fold-2 prediction, grade or decision.
- The grader `--round r6` is not written.
- No sim.py change and no closed loop.

Resume: `scripts/train_shot_attribute_v6.py fit2 | insample | fold1 | guard | pred2` (level M1 K500), then `grade_shot_attribute.py --round r6 --fold 2` once it is written.

## Resume after D38

D38 (dbee933) accepted option 2: **L1x-ot0**, the same model with the centred score-bucket terms set to zero on OT rows, in fit and serving. Home and rest terms are unchanged. Everything else is frozen: Qa x0.75 (s_f 1.1947, s_a 0.9715), level M1 K500 (D35), and `sl_r6_d35_frozen_params.json`. Code: `models_x.zero_ot_score`; `train_shot_attribute_v6.py` with OT0 = True. Outputs: `results/shot_attribute_r6_d38`, salt `SL-R6-D38-2026-10-16`.

Clock (EDT):

| step | start | end |
|---|---|---|
| fold-2 and fold-1 fits (concurrent) | 13:12:00 | 13:14:36 |
| in-sample check, D28 guard | 13:14:36 | 13:14:51 |
| grader `--round r6`: fold-1 diagnostic, then pred2, then blind fold-2 grade | 13:15:16 | 13:15:48 |

**Fits.** The fold-2 loss is 3.1847931 per row for both L1x and L1xs2 (seeded start), with max |dP| 9.5e-7. The floor is 0, and EN rows are bit-identical to L0s.

**In-sample check (fold-2 training rows): PASS.** L1x-ot0 vs L0s:

| stratum | 5v5 | PP | PK | 4v4 | 3v3 |
|---|---|---|---|---|---|
| xG | +0.023% | +0.078% | +0.048% | +0.119% | -0.021% |

5v5 OT is -0.71% (n 857, not gated).

**D28 guard (fold 1, L1x-ot0 minus L0s): PASS.** xG overall +0.023%, ES +0.009%, PP +0.077%, PK +0.003%, no FAIL row. Fold-1 R is 0.969 / 0.945 (oracle level: 0.966 / 0.951).

**Grader.** `grade_shot_attribute.py --round r6` gates ES responsiveness on the D32 R (row deciles of the arm's own as-of Qa rating; game-block bootstrap 1,000). The old team-game Q5-Q1 is reported alongside. The grader reproduces the trainer's fold-1 R (0.969 / 0.945).
- Fold-1 grade (diagnostic, `docs/tests/shot_attribute_sl_r6_grade_fold1_2026-10-16.md`): its absolute SL-R1-style bias read shows PK tier cells of +1.61 / -2.26 pp. Those come from the level read on fold 1 and are not the gate; the D28 guard on the deviation passed.

### Fold 2 (blind, 2024-25, 119,924 unblocked attempts; `docs/tests/shot_attribute_sl_r6_grade_2026-10-16.md`)

| arm | LL/game vs L0s (SE) | xG overall | ES | PP | PK | tiers / types | **R ES for (CI)** | R ES against (CI) | old Q5-Q1 for / against |
|---|---|---|---|---|---|---|---|---|---|
| L0s | 0 | +0.46% | | | | PASS | -0.30 | 0.43 | |
| **L1x-ot0** | **+0.0467 (0.0181)** | +0.46% | +0.52% | -0.01% | +2.45% | all PASS (max 0.81 pp, PK high) | **1.291 (0.99-1.82) FAIL**, UNDERPOWERED | 0.966 (0.73-1.39) PASS, UNDERPOWERED | 1.330 / 1.037 |

- **Bias checks:** every gated bias check passes, months included. EN is reported: ENF -1.0%, ENA +1.2%.
- **Seed arm:** L1xs2 is identical (floor 0).
- **PP / PK R (reported):** PP 0.23 / 0.15; PK 0.56 / 0.68 (UNDERPOWERED).
- **Per state (reported):** 5v5 +0.67%; 4v4 -4.5% and 3v3 -3.8% (UNDERPOWERED).

**Decision (as pre-registered):**
- L1x-ot0 is **not eligible**: ES "for" R is 1.291, above the 1.2 band. Its CI (0.99-1.82) is wider than the band, so it is labelled UNDERPOWERED, but the point estimate gates (D18 / D32).
- It is not worse than L0s; it is better by 2.6 SE.
- **No arm is selected.** Under SL-R6 / D38, **the round has failed.**
- There is no engine change and no closed loop: step 5 applies only on selection, and sim.py was not touched. There is no SL-R7 without the user.

**Reading:**
- "Against" lands in band on both folds (0.944 fold 1, 0.966 fold 2).
- "For" moves from 0.969 on fold 1 to 1.291 on fold 2. The fixed scale chosen on fold 1 over-responds on the next season. This matches the step-0 finding that the Qa "for" coefficient falls season on season (1.75, 1.50, 1.21; trend z -2.5): a scale set on 2021-23 is too large for 2024-25.
- The arena-free construction removed the arena contamination, but not the per-season decline in the "for" response.
