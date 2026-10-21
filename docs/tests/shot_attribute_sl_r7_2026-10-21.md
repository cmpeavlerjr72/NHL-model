# SL-R7: L1x-ot0 with the as-of response scale on Qa (cascade stage 4, Lane A7, 2026-10-21)

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R7 (inherits SL-R6 / D38, SL-R4); D40, INV-59, INV-53. Brief: `docs/briefs/lane_A7_shot_attribute_r7_2026-10-21.md`.
- Code: `src/nhl_sim/shot_attribute/scale.py` (as-of two-slope estimator), `tests/test_shot_attribute_asof_scale.py` (6 pass), `scripts/train_shot_attribute_v7.py` (snap / parity / insample / fold1 / guard / pred2), `scripts/diag_shot_attribute_r7_insample_burnin.py`.
- Snapshots: `data/processed/shot_attribute/sq_scale_v1_f{1,2}.parquet` (d3961a3). Step 0 + parity: `docs/tests/shot_attribute_sl_r7_parity_2026-10-21.md` (37ed8c0). Outputs: `results/shot_attribute_r7/` (gitignored).

**Outcome: STOPPED at step 3. The inherited in-sample stratum check fails at 4v4: L1x-as is +0.62% vs L0s (n 4,334; limit 0.5%). The whole miss comes from the 2021-22 burn-in jump of the as-of scale (2021-10-12 to 10-25). Without the 2021-22 burn-in season, every stratum is within 0.09%. The D28 guard passes. Nothing on 2024-25 was predicted or read. No engine change, no closed loop. sim.py was not touched.**

## Clock (local, -04:00)

| step | start | end |
|---|---|---|
| lane start (brief, rules, spec, template read) | 11:47:21 | |
| tests + first snapshot attempt (series diverged in the burn-in; fixed, see step 1) | 11:52:29 | 12:03:40 |
| second attempt: |t| bound too loose, every date directly evaluated (369 s per cell); stopped my own PIDs 13664 / 19716 | 12:06:41 | 12:16:33 |
| snapshots, 8 cells x 2 folds + checks | 12:18:19 | 12:19:49 |
| commit d3961a3 (step 1) | 12:20 | |
| step 0 + parity | 12:20:29 | 12:21:14 |
| commit 37ed8c0 (step 2) | 12:21 | |
| in-sample check (FAIL, exit 3), fold-1 predictions, D28 guard (PASS) | 12:21:55 | 12:22:19 |
| burn-in diagnostic | 12:22:47 | 12:22:52 |

The whole grid takes about 90 s locally, so no box request was filed.

## Step 1: construction, numerics, leakage

- **Model.** L1x-as on non-EN rows: logit = log L0s levelled (M1 K500) + the fold's frozen SL-R6 L1x-ot0 W terms (home / score / rest, score zero on OT rows) + (s_for,t zf + s_against,t za) c. EN rows get L0s levelled. Nothing is refit. W and L0s are read from `results/shot_attribute_r6_d38[/fold1]/models`; a refit of L0s matches to 1e-12.
- **Units.** zf / za are Qa divided by its SD over the fold's 2021-22 in-scope rows: fold 1 0.02223 / 0.01961, fold 2 0.02242 / 0.01945.
- **Estimator (as specified).** All non-EN unblocked attempts dated before the game date, weights 0.5^(age/H). The pair is shrunk to the previous date's pair with prior precision P x the per-attempt Fisher information matrix, and solved by Newton from the previous pair, using the G-R3 stationarity condition (Ibar re-read at each iterate). Start (0, 0); created_at = the previous date's last drop + 6 h, asserted < puck_drop.
- **Construction fixes made before any result was read** (each is a solver issue, not a change to the estimator):
  1. **Collinear early ratings.** On 2021-10-14 the window ratings are near zero and collinear (det I 5e-27), so the 2x2 solve was singular. Directions with no information keep s_prev (eigen-restricted step). This is G-R3's 0/0 carry-forward in 2-D.
  2. **Burn-in jump.** Because the prior precision scales with the near-zero information, the specified estimate jumps on the first days (raw up to about 500-2,800) and settles by 2021-10-25. Pure Newton overshot there, so a step that does not reduce the Newton decrement is halved; full steps are taken everywhere else.
- **Numerical method (labelled).**
  - Window sums use exact decay recursion. Each row's score and information come from its cumulant series in t (order 20).
  - The series is used only while the exact max |t| over the window (convex hull of the z points) is at most 0.5 x pi / range(c). Otherwise the iterate is evaluated directly on the rows; that happens only on dates up to 2021-10-25.
  - Checks (`results/shot_attribute_r7/snap_check.json`): a direct-evaluation Newton step at 8 dates x 3 cells per fold agrees to 6e-17 (fold 1) and 1.8e-15 (fold 2). Series order 14 vs 20 differ by at most 1.8e-14.
- **Tests (6 pass).**
  - Flipping every outcome and rating on or after a date leaves s on and before it bit-identical (series and direct), and changes s after it.
  - The first date equals the prior; created_at < first drop.
  - Shuffling rows within a day: |diff| < 1e-10.
  - Series = direct to 1e-9.
  - All-zero-rating dates carry the prior.
  - Near-zero burn-in ratings: the production path falls back to direct evaluation and matches the reference to 1e-8.

## Step 0 and parity (training seasons only; full tables in the parity doc)

- **The trend is tracked.** SL-R6 step-0 Qa "for" falls 1.75 / 1.50 / 1.21. The season-alone MLE under the SL-R7 offset is 1.70 / 1.52 / 1.22 (raw). The as-of "for" pair falls from about 1.5-1.6 (2022-23) to 1.03-1.32 at the end of 2023-24; shorter H tracks faster.
- **Parity analogue: no cell passes [0.9, 1.1].** Every cell over-responds on "for": R 1.14-1.25 on the three season cells. "Against" is 0.89-1.24. The season-own MLE itself gives "for" R 1.17 on 2022-23 (post-hoc, in sample).
  - The as-of scale tracks the likelihood slope. SL-R6's fixed scale was 0.75 x that slope, chosen for R near 1, and the spec drops that multiplier.
  - The SL-R6 fixed scale gets 0.92 / 0.89 (fold 1, 2022-23), 0.92 / 0.87 and 1.01 / 0.96 (fold 2).
- **Selected H45 P10000** by the fallback rule (max |log R| 0.1727; H45 P2000 is 0.00004 behind). Its per-season R (for / against):
  - fold 1, 2022-23: 1.181 / 0.932;
  - fold 2, 2022-23: 1.189 / 0.893;
  - fold 2, 2023-24: 1.143 / 1.012.

## Step 3: in-sample stratum check (fold-2 training rows, all seasons): FAIL

| stratum | n | L1x-as vs L0s | L1x-ot0 (SL-R6) vs L0s | excl. 2021-22 (reported) |
|---|---|---|---|---|
| 5v5 | 287,840 | +0.18% | +0.02% | +0.02% |
| PP | 53,097 | +0.06% | +0.08% | +0.08% |
| PK | 9,170 | +0.05% | +0.05% | +0.09% |
| **4v4** | 4,334 | **+0.62% FAIL** | +0.12% | +0.08% |
| 3v3 | 3,752 | -0.30% | -0.02% | -0.09% |
| 4v4 reg | 4,137 | +0.61% FAIL | +0.10% | +0.06% |
| 3v3 OT | 3,749 | -0.30% | -0.02% | -0.09% |

- EN rows are bit-identical to L0s.
- The 5v5 tier shifts (all rows) are +0.11 / -0.20 / +0.09 pp; excluding 2021-22 they are +0.02 / -0.05 / +0.03 pp.
- LL per attempt on the training rows: L0s -3.1821, L1x-ot0 -3.1794, **L1x-as -3.1918**. The burn-in rows are badly mispredicted.

**Cause** (`diag_shot_attribute_r7_insample_burnin.py`, training rows only). Per state, L1x-as minus L0s:

| segment | 5v5 | PP | PK | 4v4 | 3v3 |
|---|---|---|---|---|---|
| 2021-22 through 10-25 (burn-in jump; max raw s about 500-680) | +7.7% (5,843) | -1.0% | -1.0% | **+20.3% (116)** | -10.3% (105) |
| 2021-22 after 10-25 | +0.03% | +0.10% | +0.03% | +0.10% | +0.12% |
| 2022-23 | +0.04% | +0.09% | +0.17% | -0.01% | -0.22% |
| 2023-24 | -0.01% | +0.08% | +0.01% | +0.17% | +0.07% |

So the specified start (s = 0 with a prior relative to near-zero information) gives a two-week transient that the inherited check judges, although the spec calls 2021-22 burn-in, never judged. Every judged season is clean.

## D28 guard (fold 1, L1x-as minus L0s, 2023-24): PASS

- xG: overall +0.011%, ES -0.007%, PP +0.075%, PK -0.003%, every gated month within 0.12%.
- Tiers within 0.09 pp, types within 0.08 pp. No FAIL row.
- Level read (reported): xG overall +1.14% for both arms. **Fold-1 R for 1.105, against 1.001** (L0s 0.43 / 0.21).
- Prediction checks:
  - the L1x-ot0 reference reproduces the SL-R6 fold-1 prediction file exactly (max |diff| 0);
  - L1x-as2 (snapshot recomputed from shuffled rows) differs from L1x-as by at most 1.1e-16, so the floor is 0.

## Not done

- No fold-2 prediction, grade or decision. `grade_shot_attribute.py --round r7` is not written.
- No fold-1 LL grade.
- No engine wiring, no closed loop.

Resume, if the PM rules the check on judged seasons: `train_shot_attribute_v7.py pred2` (with the insample gate restated), then a `--round r7` grader (arms L0s / L1xas, refs L1x, seed L1xas / L1xas2, D32 R) on fold 1 and then fold 2.

## Proposals for the PM (no decision taken here)

1. **Read the inherited check on judged seasons only** (2022-23 and 2023-24, or all rows after the 2021-10-25 transient). The spec already says 2021-22 is never judged. This would be a D28 / D38-type ruling made before any holdout read. Under it every stratum passes (max 0.09%; 0.22% on the post-transient split).
2. **Construction alternative:** serve L0s (s = 0) until the window holds a minimum information. That is a new choice, so it is not recommended inside this round.
3. **Report the round as failed.**
4. **Listed whichever way the PM rules:** the parity table shows the as-of scale tracks the likelihood slope, whose "for" R is about 1.15-1.2 on every training season (fold-1 R 1.105). Fold 2's "for" R gate at 1.2 is therefore close. This is a reading of the training seasons only, not a fold-2 number.

**Proposed LEARNINGS candidate:** a prior "of P events" expressed as P x the per-event Fisher information has no strength when the ratings carry no spread (season openings). An as-of slope then jumps on the first days. Either the burn-in is excluded from every check, or the prior needs an absolute floor.

## Resume after D42

### In-sample check restated on the judged training seasons (D42): PASS

`train_shot_attribute_v7.py insample_d42` (12:26:20 to 12:26:29). The gate is read on fold-2 training rows from 2022-23 onward; all rows are reported. Output: `results/shot_attribute_r7/insample.json` (basis D42); the all-rows result is kept as `insample_all_rows_pre_d42.json`.

| stratum (2022-23 + 2023-24) | n | L1x-as vs L0s | high / medium / low pp |
|---|---|---|---|
| 5v5 | 191,646 | +0.017% | +0.018 / -0.054 / +0.036 |
| PP | 36,193 | +0.081% | +0.036 / -0.018 / -0.018 |
| PK | 6,073 | +0.092% | +0.050 / -0.086 / +0.035 |
| 4v4 | 2,817 | +0.079% | +0.033 / -0.038 / +0.005 |
| 3v3 | 2,408 | -0.089% | -0.022 / -0.020 / +0.043 |
| 4v4 reg / 3v3 OT | 2,667 / 2,406 | +0.063% / -0.090% | |

- Not gated (n < 2,000): 5v5 OT -0.91% (n 620), PK OT, 4v4 OT, PP OT.
- EN rows are bit-identical to L0s.
- The burn-in spike (2021-10-12 to 10-25) is listed as a construction defect and is not fixed in this round (D42).
