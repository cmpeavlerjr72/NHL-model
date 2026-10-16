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
