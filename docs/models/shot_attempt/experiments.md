# Shot-attempt generation: experiments (append-only)

Cascade stage 3 (FRAMEWORK_PLAN section 1). This model decides when each team takes a shot attempt (Corsi event: on goal, missed, blocked, or goal), given strength state, score state, the teams and home ice. Where the attempt comes from, its type, its outcome and who takes it are stages 4-6 and player attribution. Stage 2 (deployment) is deferred (Lane H recommendation, D15), so SA-R1 is team-level. On-ice-unit ratings are a later refinement arm.

---

## SA-R1: shot-attempt hazard bake-off (pre-registered 2026-10-15 by the PM, before any run)

### Question

Which attempt-hazard model gives the best held-out likelihood of when attempts occur and for which team, without level, seasonal, strength-state or score-state bias, and with team responsiveness that matches reality (neither flat nor too steep, L24)?

### Unit and target

- **Rows:** one row per (game, team, interval), on the fixed one-minute grid Lane H settled on in SS-R1. Rows are cut at every change of strength state and pre-event score state, and exposure is in seconds. The target is the count of that team's shot attempts: `shot-on-goal`, `missed-shot`, `blocked-shot` and `goal` events, owned by the shooting team. Blocks are attributed to the shooting team (L15).
- **Exclusions:** penalty shots and shootout attempts are excluded from the target and tallied in the report. Rows with a goalie pulled are included, with the goalie state as a feature level. The delayed-penalty pull uses the L20 convention: those seconds keep the pre-signal state.
- **Strength state** is from the shooting team's view: 5v5, PP (5v4, 5v3, 4v3), PK, 4v4, 3v3, EN-for (own goalie pulled), EN-against.

### Shared inputs (every arm)

- The **in-season league level** and **season-phase profile**, rebuilt for attempts using the SS-R3 method:
  - a training-only profile;
  - a de-seasonalised as-of level, k tuned on fold 1 from {15, 50, 150};
  - fixed offsets;
  - no season dummies (L21, L22).
- **As-of team ratings**, with puck drop strictly after the data used, and the `created_at < puck_drop` writer check:
  - attempts-for and attempts-against per 60, separately for even strength (5v5 + 4v4 + 3v3), PP-for and PK;
  - log rates relative to the snapshot's league mean (L1);
  - gamma-Poisson shrinkage, with prior strength from {600, 1800, 5400} team-minutes and carry weight w from {0.5, 0.7, 0.85, 1.0}, both tuned on fold 1 only.
  - **L24 guard:** tuning picks the pair that maximises fold-1 likelihood, but the fold-1 offline quintile-spread ratio (below) is reported for every grid cell.

### Arms

| Arm | Model | Features |
|---|---|---|
| A0 | piecewise-constant | level + profile offsets x strength state x period type |
| A1 | Poisson GLM | A0 + own attempts-for rating + opponent attempts-against rating (for the row's strength group) + home + rest/back-to-back (both teams) |
| A2 | A1 + score effects | A1 + pre-event score diff bucket {<=-3, -2, -1, 0, +1, +2, >=+3} x period (1, 2, 3, OT) + last-5-min-of-3rd flag x score bucket |
| A5 | A2 + venue | A2 + as-of home-venue recording factor: a shrunk log ratio of total attempts recorded in that arena to the attempts expected from both teams' ratings, built only from past games (arena scorer bias) |
| A4 | A2 + shared pace latent | A2 with a per-game gamma latent shared by both teams; its variance is fitted on fold-1 train, and it is graded by the exact per-game negative-multinomial likelihood (L2) |
| A3 | LightGBM Poisson | A5 features + continuous game clock; num_leaves {7, 15}, min_data_in_leaf {200, 800}, lr 0.05, early stopping on a time-ordered fold-1 inner split |

Complexity order, simplest first: A0 < A1 < A2 < A5 < A4 < A3.

Score-diff features are pre-event only. They are fed from engine state in the closed loop, so the closed-loop gate is mandatory (L3).

### Folds

As in CLAUDE.md. Fold 1 is for tuning only. Fold 2 (2024-25) is the selection fold. 2025-26 stays sealed and 2026-27 is not touched.

### Primary metric (fold 2)

The per-game joint log-likelihood of all of that game's row counts for both teams, as a difference vs A0. For the independent-Poisson arms this is the sum of the row Poisson log-likelihoods; for A4 it is the exact shared-latent marginal. One grading script, `scripts/grade_shot_attempt.py`, grades with arm labels hashed.

### Noise floor and decision rule

- **Noise floor:** a game-block bootstrap (1,000 resamples) of paired per-game differences, plus the A3 second-seed retrain.
- **Beating a simpler arm:** an arm beats a simpler arm only if it wins by more than 2 SE and by more than the seed floor.
- **Eligibility:** only arms that pass every bias check AND the offline responsiveness band can be selected.
- **Selection:** the selected arm is the most complex eligible arm that beats every simpler eligible arm.

### Bias checks (fold 2 gates; fold 1 is reported as a diagnostic)

| Check | Pass |
|---|---|
| Level, overall | predicted / actual within +/-2% |
| By month (n >= 100 games) | within +/-5% |
| By strength state (5v5, PP, PK; 4v4, 3v3 and EN reported) | within +/-3% |
| By pre-event score diff bucket (n >= 300 team-games of exposure) | within +/-4% |
| Home vs away | within +/-2% each |

Thresholds are tighter than stage 1's because attempts are about 35x as frequent as penalties.

### Responsiveness band (L24, offline, fold 2)

- Bucket rows by the own attempts-for rating quintile and, separately, by the opponent attempts-against rating quintile, within 5v5.
- Spread ratio = (predicted Q5 - Q1 attempts per 60) / (actual Q5 - Q1).
- **Pass:** the ratio is in [0.8, 1.2] for both ratings. The bootstrap CI of the ratio is reported.

### Closed-loop gate (G2; mandatory for the selected arm and the next simpler eligible arm)

- **Engine:** the stage-1 incumbent (H3'' + T1, D15) drives the strength-state timeline. Attempts come from the arm under test.
- **Goal stub (labelled):** goal given attempt is a league per-season, per-strength-state rate from fold-2 TRAIN data, with no team terms. It is not graded, and it lets the score evolve so that score effects are exercised. Score-state cells are exercised, but they are re-validated when stage 6 lands.
- **Run size:** fold 2 at >= 200 seeds, with a 100-vs-200 check.
- **G2 quantities vs actual** (extend `build_gate_reference.py` / `eval_gates.py`):
  - attempts per 60 by strength state (tolerance `g2_rate_rel`);
  - attempts per team-game: mean, SD and P(k) bands;
  - correlation of home and away attempts per game;
  - attempts by pre-event score diff bucket (score effects);
  - per-team for/against, with n and labels.

  Report the regular season, the playoffs and overall separately; playoff cells under `min_cell_n` are UNDERPOWERED.
- **Closed-loop responsiveness:** the quintile spread ratio is in [0.8, 1.2].
- **Clean-pass decomposition (D14 method):** for attempts per team-game and per 60 by state, split the residual into hazard level, state visits, score-state visits and remainder. The verdict is CLEAN / COMPENSATED / FAIL, and a pass must be CLEAN.

### Results

(append below this line)

#### SA-R1 run, 2026-10-15 (Lane S, INV-30)

- Tables `data/processed/shot_attempt/*_v1*`. Fold-2 test: 1,398 games, 213,898 rows, 167,020 attempts. Exclusions are tallied: 30 penalty-shot and 508 shootout attempts in 2024-25. Tests `tests/test_shot_attempt_tables.py` (unmapped type raises; L20 delayed state).
- Frozen on fold 1: k = 15, w = 0.85, prior strength 600 (k and b are grid corners). A3: 7 leaves, min_data 800, 765 rounds. A4 latent v = 0.00115. The fold-1 spread ratio is reported for all 36 cells (1.14-1.61; over-responsive everywhere, least at b = 600).
- Fold-2 primary metric vs A0 (nats/game, SE): A1 +0.402 (0.044), A2 +0.965 (0.056), A5 +0.964 (0.056), A4 +0.989 (0.056), A3 +1.062 (0.058). The seed floor is 0.0013.
  - A5 does not beat A2 (-0.001, SE 0.002).
  - A4 beats A2 (+0.024, SE 0.004).
  - A3 beats A4 (+0.074, SE 0.022).
- Bias checks, fold 2: **FAIL for every arm.**
  - The overall level is -4.99% to -5.07% (+/-2%).
  - Five of seven powered months fail.
  - 5v5 is -5.5%.
  - PK is +3.2% to +3.4%, failing in A0-A4; it passes in A3.
  - Score buckets -1 and 0 fail in every arm, and +1 also fails in A3.
  - Home and away fail.
- Offline responsiveness, fold 2 (5v5): A1 1.04 / 1.13, A2 1.07 / 1.15, A5 1.08 / 1.14, A3 1.09 / 1.09 pass; A0 0.03 / -0.04 fails.
- **Decision rule: no eligible arm, so NO arm is selected.** G2 was not run (step 3 blocked by the rule).
- Diagnosis (fold 1 only): the SS-R3-method level is a ratio to the previous season's final rate. Pooled as a fixed offset, it mis-anchors the cells, and the test season inherits the earlier season-to-season ratios (attempts +2.3%, +4.5%). An anchored level (a ratio to a fixed reference season) moves fold-1 A0 from -2.03% to +0.22%.
- A separate fold-1 drift is not carried by any all-state level: PK +8% to +11%, PP -1% to -4.5%.
- Report: `docs/tests/shot_attempt_sa_r1_2026-10-15.md`; grade: `docs/tests/shot_attempt_sa_r1_grade_2026-10-15.md`.
- Step 3 is blocked by the rule, so no G2 was run. The code it needs is built and tested for a future selection:
  - engine attempt variant (default-off `att_lam`, `tests/engine/test_sim_attempts.py`);
  - lookup with parity across A0-A5 and A3 (sample error at most 1.8e-9 against the 0.5% limit, `tests/test_shot_attempt_lookup.py`);
  - G2 runner, decomposition and closed-loop responsiveness (`scripts/run_shot_attempt_g2.py`, `src/nhl_sim/eval/g2.py`);
  - G2 targets sibling `data/reference/gate_targets_g2_20242025.parquet`.
- A 4-seed smoke run on A2 (plumbing only, not a gate) ran end to end.

---

## PM ruling on SA-R1 (2026-10-15, D16)

- The result is accepted as reported: no arm is eligible, and G2 was correctly not run. A3 leads offline (+1.062 vs A0). The responsiveness band passes for A1-A3 (1.04-1.16). The arena factor adds nothing (A5 vs A2 -0.001).
- **The root cause is a PM spec error**, the SS-R2 level definition reused here. The level is a ratio to the previous season, and cells pooled over training seasons absorb the mean of those seasons' rates. So under any trend the test-season prediction is biased by the gap between that mean and last season's rate. Attempts rose (+2.3%, +4.5%), which gives -5%. The level is replaced by LC-1 in every stage.

## SA-R2: shot attempts with the corrected level (pre-registered 2026-10-15 by the PM, before any run)

### Changes vs SA-R1 (everything else is identical, including features, folds, metric, noise floor, decision rule, bias-check thresholds, responsiveness band and the G2 spec)

1. **Corrected league level LC-1 (D16).** The level is the log of the ABSOLUTE as-of de-seasonalised league rate. It is the season-to-date rate before this game date, divided by the profile, and gamma-shrunk toward the previous season's final de-seasonalised rate with strength k. It enters with coefficient 1 in training and in test alike, so cells and other terms are multipliers on the current league level. No ratio to the previous season is used anywhere. Its parity test asserts that, on fold-1 train, the mean predicted rate equals the actual rate within 0.5% in EACH training season separately.
2. **Grid extended** (SA-R1 corners): k in {5, 15, 50}, prior strength b in {200, 600, 1800}, w in {0.7, 0.85, 1.0}. Tuned on fold 1 only.
3. **Strength-group level arms**, for the fold-1 PK drift of +8-11%. A2g and A3g are A2 and A3 with three separate LC-1 levels, one each for ES, PP-for and PK, each with its own profile. The g arm is preferred over its twin only if it passes a bias check the twin fails, or beats it by > 2 SE, and is not worse on any other check.

### Arms

A0, A1, A2, A5, A4, A3 (all refit with LC-1), plus A2g and A3g. The complexity order is A0 < A1 < A2 < A2g < A5 < A4 < A3 < A3g.

### Fold-1 diagnostic (reported first)

Overall, by-month and by-state bias on fold 1 for every arm. The fold-2 checks gate.

### Results

(append below this line)

#### SA-R2 run, 2026-10-15 (Lane S2, INV-31)

- LC-1 (`src/nhl_sim/league_level_lc1.py`, tables `_v2`).
- Parity, level arm A0 on fold-1 train: -0.48% / +0.46%, PASS. This is a labelled reading. A1, A2 and A5 exceed the limit at about 0.6%, and fold-2 train A0 2021-22 is -0.66%. Both are reported.
- Frozen: k = 5, w = 0.85, b = 200 (k and b are corners). A3 / A3g: 15 leaves, 800 min-data, 459 rounds. v = 0.00119.
- Fold-1 diagnostic: level +0.4% to +0.6% in every arm. PK runs +10% to +11% except A2g (+4.1%) and A3g (pass).
- Fold 2 vs A0 (nats/game, SE): A1 +0.401 (0.042), A2 +0.961 (0.054), A2g +0.973 (0.055), A5 +0.965, A4 +0.968, A3 +1.086 (0.055), A3g +1.099 (0.056). The seed floor is 0.0026.
- Fold-2 bias: only A2g and A3g pass every check. The other arms fail PK (+9% to +11%), and A0-A5 also fail PP (+3.4% to +3.7%). Responsiveness passes for A1-A3g (1.07-1.17).
- Twin rule: A2g and A3g are preferred.
- **Selected: A3g; next simpler eligible arm: A2g.**
- G2 (200 seeds, stage 1 = H3'' + T1, the D15 incumbent at launch) for A3g in the regular season:
  - 5v5 +0.4%, PP -0.5%, PK -2.1%, attempts per team-game -0.9%: all PASS.
  - **4v4 +4.2% and 3v3 +6.6%: FAIL.**
  - Per-team-game decomposition: CLEAN (EN -1.69 against 5v5 time +0.97, both inside the 1.78 tolerance).
  - Closed-loop responsiveness: 1.135 / 1.121, PASS.
  - A2g: 3v3 +5.4% FAIL, 4v4 passes, otherwise the same.
- Step 4 was not triggered: SS-R3c stopped at its parity assertion.
- Report: `docs/tests/shot_attempt_sa_r2_2026-10-15.md`.

---

## PM ruling on SA-R2 (2026-10-15, D17)

- **A3g is the offline-selected arm.** Only the group-level arms pass every fold-2 bias check: A3g's overall level is +0.32%, it beats A2g by +0.126 (7 SE), and its responsiveness ratio is 1.135 / 1.121. LC-1 fixed the level, and the fold-1 bias is now +0.4% to +0.6%.
- **G2 fails.** The core regular-season cells pass and the run is CLEAN, but 4v4 (+4.2%) and 3v3 (+6.6%) attempts per 60 fail the tolerance.
  - The spec gates "attempts per 60 by strength state" in G2. Offline, those states were report-only, but the closed-loop gate binds as written, so they gate.
  - 3v3 drives regular-season OT, which decides G7.
- **Status.** shot_attempt stays TESTING, with A3g as the leading arm. It is not yet the incumbent.
- **Next (SA-R3, to be pre-registered next session).** A fix for the 4v4/3v3 hazard, with the over-prediction already visible offline. Candidates: separate 4v4 and 3v3 levels, and/or an OT-specific term. SA-R3 also re-runs G2 on H3'' + T2 (this G2 used T1, because T2 lived only in an engine sibling).
- **Watch item for stage 8.** About -1.7 attempts per team-game come from empty-net time the engine cannot visit, offset by about +1.0 from extra 5v5 time. Each is inside tolerance and the literal verdict is CLEAN, but this pair is re-checked once the goalie-pull model lands.

---

## SA-R3: thin-state (4v4 / 3v3) attempt hazard, then G2 on H3''+T2 (pre-registered 2026-10-16 by the PM, before any run; D17, INV-32)

SA-R2's A3g over-predicts 4v4 (+3.1%) and 3v3 (+6.8%) attempts per 60 OFFLINE, and G2 fails both cells closed-loop (+4.2% / +6.6%) with the hazard-level component dominant. This is the third stage-3 respec, so the D13 forking-paths guard applies: a fix counts only if it also improves the fold-1 thin-state bias.

### Arms (everything not listed is A3g as frozen in SA-R2: LC-1 levels, k = 5, w = 0.85, b = 200, 15 leaves, 800 min-data, 459 rounds)

| id | change vs A3g |
|---|---|
| A3g | reference (refit only to confirm reproduction) |
| A3g-s | separate LC-1 levels and profiles for 4v4 and 3v3 (five groups: ES-5v5, PP-for, PK, 4v4, 3v3; EN keeps the ES level). Group prior K scaled by exposure share, as in SA-R2 |
| A3g-c | A3g plus a fixed log-offset cell for 4v4 and for 3v3: log(training actual / training A3g prediction) per state, gamma-shrunk to 0 with strength b_c expected attempts, b_c in {50, 200, 800} tuned on fold 1 by LL |
| A2g-c | A2g with the same cells (the next-simpler twin) |

Complexity order: A2g-c < A3g < A3g-c < A3g-s. 3v3 in the regular season is OT only, so the 3v3 cell is the OT term; no separate OT feature is added.

### Metric, noise floor, decision rule

- Primary: fold-2 LL per game vs A3g (nats/game, paired SE); noise floor = A3g refit under seed 2.
- Thin-state bias gate (offline, fold 2): 4v4 and 3v3 attempts per 60 within the `docs/gates.yaml` G2 tolerance, with the cell SE reported (3v3 runs about 25 team-hours per season; label UNDERPOWERED where the SE exceeds the tolerance, but the cell still gates, as D17 ruled). The fold-1 thin-state bias must improve on A3g's in the same direction (D13 guard).
- Every SA-R2 check still passes (overall level, PP, PK, monthly, responsiveness band).
- Select the simplest arm that passes all of the above and whose LL is not worse than A3g by > 2 SE. If none passes, report; the PM rules. No SA-R4 is pre-authorised.

### Engine merge and G2

1. Merge the T2 per-team penalty-type table from the engine sibling `sim_ss_r5.py` into `sim.py` behind a default-off flag (one engine, no forks). Parity tests: flag off = current `sim.py` output bit-identical on a fixed seed set; flag on = `sim_ss_r5.py` output bit-identical on the same seeds. Then `sim_ss_r5.py` is retired (left in place, marked superseded).
2. G2 (200 seeds, gates.yaml unchanged) on stage 1 = H3'' + T2 (the incumbent at launch, old level under D15), for the selected arm and A3g. Report the full G2 table and the per-team-game and by-state decompositions as in SA-R2, plus 100-vs-200 seed stability. The EN watch item (D17) is reported, not gated.

### Results

(append below this line)
