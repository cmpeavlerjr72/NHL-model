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

### Clock after D42 (-04:00)

| step | start | end |
|---|---|---|
| in-sample restated (insample_d42), commit 3de175b | 12:26:20 | 12:26:29 |
| grader `--round r7`, fold-1 grade + D13 guard | 12:27:28 | 12:27:43 |
| pred2 (fold-2 predictions), blind fold-2 grade | 12:27:49 | 12:28:17 |
| engine flag, `serve_l1xas.py`, parity fixture (from 80f0b2e via git show), tests | 12:28 | 12:34:10 |
| closed loop: smoke run (2 seeds, 15 s), then 4 blocks x 50 seeds, 2 threads each | 12:36:01 | 12:43:12 |
| measured slice: 25 seeds per block in 188-192 s, so about 6.5 min for 200 seeds (under 15 min, local) | 12:36:44 | 12:39:59 |
| closed-loop grade (G3, G2 re-check) | 12:43:28 | 12:43:34 |

### Fold 1 (2023-24): D13 guard, D40 harmonised form: PASS

Grade: `docs/tests/shot_attribute_sl_r7_grade_fold1_2026-10-21.md`.

| arm | LL/game vs L0s (SE) | xG overall | R ES for | R ES against |
|---|---|---|---|---|
| L0s | 0 | +1.13% | 0.43 | 0.21 |
| L1x-ot0 (SL-R6 ref) | +0.0347 (0.0204) | +1.15% | 0.969 | 0.945 |
| **L1x-as** | +0.0324 (0.0212) | +1.14% | **1.105** | **1.001** |

- The D28 guard passes (L1x-as minus L0s).
- R is in band.
- L1x-as is not worse than L0s by more than 2 SE.
- Reported: the absolute SL-R1 bias read fails the PK tier cells (+1.61 / -2.27 pp). L0s fails them too (+1.57 / -2.18): this is the fold-1 level read, as in SL-R6. The guard is the D28 form.

### Fold 2 (2024-25, blind): 119,924 unblocked attempts, 1,398 games

Grade: `docs/tests/shot_attribute_sl_r7_grade_2026-10-21.md`. Every label was scored before `labels_sealed.json` was opened.

| arm | LL/game vs L0s (SE) | xG overall | ES | PP | PK | tiers / types | R ES for (CI) | R ES against (CI) | old Q5-Q1 for / against |
|---|---|---|---|---|---|---|---|---|---|
| L0s | 0 | +0.46% | | | | PASS | -0.30 | 0.43 | |
| L1x-ot0 (reference) | +0.0467 (0.0181) | +0.46% | | | | PASS | 1.291 (0.99-1.82) FAIL | 0.966 (0.73-1.39) | 1.330 / 1.037 |
| **L1x-as** | **+0.0463 (0.0182)** | +0.45% | +0.51% | -0.02% | +2.41% | all PASS (max tier 0.81 pp PK high; max type 0.93 pp tip) | **1.182 (0.91-1.67) PASS, UNDERPOWERED** | **1.138 (0.87-1.63) PASS, UNDERPOWERED** | 1.207 / 1.218 |

- **The reference reproduces SL-R6 exactly.**
  - The prediction file is identical (max |diff| 0).
  - LL +0.0467 (SE 0.0181) and R 1.291 / 0.966, as in SL-R6.
- **Seed floor 0.** L1x-as2 recomputes the snapshot from shuffled rows; its predictions match within 1.1e-16.
- **L1x-as vs L1x-ot0:** -0.0003 nats/game (SE 0.0021). The as-of scale costs no likelihood.
- **Months:** every powered month is within 1.9%.
- **Reported only:**
  - EN: ENF -1.0%, ENA +1.2%.
  - PP R 0.20 / 0.17 and PK R 0.51 / 0.80, both UNDERPOWERED.
  - Per state: 5v5 +0.66%, PP -0.02%, PK +2.41%; 4v4 -4.5% and 3v3 -3.8% (UNDERPOWERED).
- **Decision (D40 harmonised):**
  - L1x-as is **eligible**: every bias check passes, ES R is in [0.8, 1.2] on the point estimates, and the D13 guard passes.
  - It is **not worse than L0s by more than 2 SE**: it is better by 2.5 SE.
  - **Selected: L1x-as.**
  - Listed: the "for" R of 1.182 sits 0.018 inside the line, and both CIs are wider than the band (UNDERPOWERED).

### Engine wiring (on top of 80f0b2e; default-off flag `attr["l1x"]`)

- **`src/nhl_sim/engine/sim.py`.**
  - When `attr["l1x"]` is present, the class row is softmax(log state_pdf[st, ptype] + log game_mult[g, rg] + game_logit[g, team, rg] + sc_logit[ptype, sc7]).
  - The flag requires the L0s state_pdf and game_mult. It refuses an "attr" stand-in label, because L1x-as replaces the stand-in.
  - The output carries `attr_model`.
- **`src/nhl_sim/shot_attribute/serve_l1xas.py`** builds the tables:
  - frozen W of the SL-R6 L1x-ot0 fold-2 fit;
  - s_t from the committed snapshot (H45 P10000), keyed by game date;
  - Qa from `sq_ratings_v2_f2`, b2b from `team_game_v2`;
  - score terms zero on OT.
- **Flag off is bit-identical** (sha256 of every output array) to the engine at 80f0b2e. That covers 16 cases: E2's 13, plus the full INV-60 stack switched on, synthetic and real. Fixture: `tests/fixtures/sim_l1xas_flag_parity.json`, made by `scripts/diag_engine_l1xas_parity_fixture.py`, which reads the pre-change engine with `git show`.
- **Tests.** `tests/engine/test_sim_l1xas.py` passes. Wiring:
  - zero logits reproduce the L0s draws;
  - the served row equals the softmax (atol 1e-14);
  - the OT row is used at t >= 3600;
  - refusals work.

  The whole `tests/engine` suite plus the scale tests: 134 passed.
- **Served vs offline:** max |diff| 1.5e-8 over 116,716 reachable fold-2 rows. The offline file is float32, and the served s_t is the snapshot value itself. E2's components re-checked: block 1.5e-8, miss 3.0e-8, goal 1.1e-16.

### Closed loop (200 seeds, fold 2, 1,398 games)

Command: `scripts/run_shot_attribute_g3_v4.py sim --seed0 {0,50,100,150} --nseeds 50`, then `grade`.

Stack:
- stage 1 H3''-LC2 + T2;
- stage 3 A3g-c;
- block B0 STAND-IN (own 4v4 / 3v3);
- **stage 4 L1x-as**;
- miss S0t STAND-IN;
- goal C1s with ORACLE GOALIE;
- stages 7-8 absent.

Reports: `docs/tests/gates_g3_sl_r7_L1xas_2026-10-21.md` and `docs/tests/gates_g2_sl_r7_L1xas_2026-10-21.md`.

- **G3 (overall slice): PASS.** xG per unblocked attempt, sim vs actual:

  | cell | xG rel | tiers |
  |---|---|---|
  | all reachable | +0.34% | within 0.38 pp |
  | 5v5 | +0.66% | within 0.32 pp |
  | PP | -0.03% | within 0.20 pp |
  | PK | +2.21% | within 0.78 pp |

  - Reported: 4v4 -4.85% and 3v3 -3.68% xG (n 1,242 / 1,129). The 4v4 / 3v3 tier mix is off by 5.5-8.7 pp on medium; these are the L0s 4v4 / 3v3 type-given-cell and shrink cells (D28 list), not the tilt.
  - Block share and goals per unblocked attempt are within 0.9 pp / 0.2 pp.
  - Per team (UNDERPOWERED): xG corr 0.82; 29 of 32 teams within 3%.
- **Closed-loop ES responsiveness (reported, not a pre-registered gate).** Units are (game, team), with Qa ES deciles.
  - "For": R 1.243 (CI 0.95-1.85, UNDERPOWERED), against 1.182 offline.
  - "Against": R 1.126 (CI 0.86-1.66).
  - The gap from the offline R is sim noise plus the per-unit weighting. It is listed as a watch item with "for" just outside the band.
- **G2 re-check: every gated cell passes.** 5v5 +0.4%, PP -0.4%, PK -1.4%, team-game mean -1.0%, score buckets within 2.8%, responsiveness 1.147 / 1.111.
  - 4v4 +2.6% is listed (INV-42) and passes.
  - 3v3 +5.3% FAIL is listed (INV-35), the same as E2's plumbing loop (+5.4%).
  - The playoffs slice is UNDERPOWERED.
- **Stage 5b / 6 by state** (reported, stand-in miss, oracle goalie): in the G3 report.

### Outcome after D42

**L1x-as is selected and the closed loop passes.** Per SL-R4 / SL-R7, shot_attribute becomes **CONFIRMED-INCUMBENT (provisional)**. L1x-as replaces the L0s STAND-IN in the engine when `attr["l1x"]` is on; the flag stays default off until the PM switches it.

Listed:
- the 2021-22 burn-in spike (D42);
- the parity fallback (no cell in [0.9, 1.1]);
- fold-2 "for" R 1.182 (UNDERPOWERED);
- closed-loop "for" R 1.243 (reported);
- 4v4 / 3v3 mix (reported, UNDERPOWERED).
