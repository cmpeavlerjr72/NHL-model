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
