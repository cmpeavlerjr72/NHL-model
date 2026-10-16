# SL-R6: arena-free shot-quality ratings, L1x fixed-scale quality tilt on L0s (cascade stage 4, Lane A6, 2026-10-16)

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R6 (inherits SL-R4 / R3 / R2 / R1); D28, D32. Brief: `docs/briefs/lane_A6_shot_attribute_r6_2026-10-16.md`.
- Code: `scripts/build_shot_attribute_tables_v2.py` (Qr / Qa ratings), `src/nhl_sim/shot_attribute/models_x.py` (L1x), `scripts/train_shot_attribute_v6.py` (step 0, fold-1 grid, fits, checks, predictions).

## Clock (date, EDT)

| step | start | end |
|---|---|---|
| lane start (brief read) | 12:18:31 | |
| Qr / Qa ratings build (both folds) | 12:21:22 | 12:21:40 |
| step 0, first attempt (serial, untuned optimiser; killed by my own 590 s timeout, discarded) | 12:24:02 | 12:33:52 |
| step 0 (15 fits, 5 parallel workers) | 12:36:01 | 12:42:10 |

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
