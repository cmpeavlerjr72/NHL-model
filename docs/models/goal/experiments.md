# Goal given shot on goal: experiments (append-only)

Cascade stage 6 (FRAMEWORK_PLAN item 6). Given a shot on goal with its location cell and type, this model decides goal vs save. Every fit uses recorded rows, never stand-in output (D32). Shooter identity is the player layer, which is deferred, so G-R1 is team-level plus the goalie in net. Empty-net shots (no goalie) are not in scope: they belong to stage 8.

**Goalie labelling (D8).** The goalie in net on each shot is a recorded fact and is used offline. In pregame sims the starter comes from the box score, labelled "oracle goalie", until the forward goalie logger has history.

---

## G-R1: goal-decision bake-off (pre-registered 2026-10-16 by the PM, before any run)

### Target and rows

- **Rows:** shots on goal with a goalie in net, excluding the shootout and penalty shots. y = 1 if goal.
- **Gated groups:** 5v5, PP-for, PK. 4v4 / 3v3 are reported with n.

### Conversion level (D23; L27-L31, L35)

The recorded location mix drifted while goals per unblocked attempt held (SL-R1), so per-cell conversion must carry its own as-of level. Constructions, entered as a logit offset per strength group:

| id | construction |
|---|---|
| M0 | last season's final conversion relative to the training cell table |
| E | the D24 recording era |
| M1 | season to date shrunk to M0, K in {500, 2000, 8000} shots on goal |
| M2 | discounted, K = 2000, half-life {30, 60} days |
| O | oracle |

Parity: per genuine-prior training season, the level-only arm C0 is within +/-0.3 pp of save percentage overall and in 5v5. Selection uses the LC-2 / SB-R1 rule.

### Step 0: rating-response trend test (L35; committed before any arm is fit)

For each training season alone, the logistic coefficient on:
- the goalie's as-of save rating;
- the shooting team's as-of finishing rating (goals minus the C0 expectation per shot on goal, road and home pooled; arena distance factor as a separate covariate).

Report each with its SE and a trend z across seasons. If |z| > 2 for a rating, that rating enters the arms with the D32 fixed scale, and the trend is listed. An as-of scale is INV-53, deferred.

### Ratings (as-of, shrunk, relative to the snapshot league mean, L1)

- **Goalie:** saves above C0 expectation per shot on goal. Prior b in {1000, 3000, 10000, 30000} shots, carry w in {0.5, 0.7, 0.85} (heavy shrinkage, FRAMEWORK_PLAN).
- **Team finishing:** the same form, b in {1000, 3000, 10000}.
- **Scale:** each rating enters with a fixed scale s x the fold-1-fitted coefficient, s in {0.25, 0.5, 0.75, 1.0, 1.25}. The (b, w, s) cell is chosen on fold 1 by R closest to 1 (D32 decile slope ratio, goalie and team separately), among cells within 2 SE of the best fold-1 LL.

### Arms

| Arm | Model |
|---|---|
| C0 | level + recorded training goal rate per cell x type x strength group |
| C1 | logistic: C0 offset + home + score bucket + rest (both teams) + arena distance factor + goalie rating + team finishing rating at their fixed scales |
| C2 | LightGBM binary, init_score = logit of C0 (L32), features of C1 minus both ratings (D31), with the two rating offsets added to init_score at their fixed scales; num_leaves {7, 15} x min_data {200, 800}, lr 0.05, early stopping on the fold-1 inner split; in-sample stratum check +/-0.2 pp vs C0 per gated group (L32) |

Complexity: C0 < C1 < C2.

### Metric, floor, decision

- **Primary:** fold-2 Bernoulli LL per game vs C0 (game-block bootstrap SE). Grading is blind, with `scripts/grade_goal.py`.
- **Floor:** a C2 seed-2 retrain; if bit-identical, the floor is 0 (D26).
- **Decision rule:** as in the other stages. Eligibility = every bias check + R in band for goalie and team ratings. C0 is flat for goalies and teams and not adoptable (D24).
- **D13 guard:** the selected arm is in band on fold 1.

### Bias checks (fold 2 gates, gates.yaml g4_sv_pp = 0.5 pp; fold 1 diagnostic)

- Save percentage: overall within +/-0.5 pp; per gated group within +/-1.0 pp (n >= 2,000); per location tier within +/-1.0 pp; by month within +/-1.0 pp (n >= 100 games).
- Goals per game from shots on goal (predicted vs actual, regular season): within +/-2%.
- Per goalie (n >= 500 shots on goal): reported; R by goalie-rating decile is the responsiveness gate.
- The G4 cell grid (goalie quintile x team-finishing quintile) is reported with n.

### Closed loop

Deferred. Stages 4 / 5a are stand-ins (D32, D34), and stage 5b is in progress. Once G-R1 selects, the engine replaces the xG_ref goal stub with the selected arm, behind a flag, for a plumbing run, labelled. The gating G4 / G1-goals closed loop waits for a stage-4 incumbent.

### Results

(append below this line)

### G-R1 results (Lane G, 2026-10-16; report `docs/tests/goal_g_r1_2026-10-16.md`)

- Step 1 (3a2105e): level **E** selected (simplest passer, 0.054 pp = oracle; D24 caveat: fold-2 parity in sample). M1 / M2 pass (0.22-0.30), M0 fails (0.57), none fails (0.44).
- Step 0 (f82c103, before any arm fit): goalie per-season coefficient -1.82 / -1.49 / -0.55, trend z +2.35 (TREND listed); team 1.24 / 0.48 / 0.59, z -1.32. Both enter at the D32 fixed scale.
- Fold-1 selection (48b1047): goalie b 3000, w 0.5, s 0.5 (R 1.02); team b 10000, w 0.7, s 1.0 (R 1.01). C2: 15 leaves, min_data 800, 97 rounds; stratum check PASS (<= 0.02 pp gated).
- Fold 2: **no arm eligible; none selected.** Every arm fails save% overall (+0.60 pp), PP (+1.30 pp) and RS goals (-5.2%), all from level E. Fold-2 R for C1 / C2: goalie 0.67 / 0.68 (FAIL, UNDERPOWERED), team 0.95 / 1.02 (in band). C1 vs C0 +0.0050 nats/game (SE 0.0037); C2 vs C0 +0.0013 (SE 0.0047). Floor 0.00091 (fold 1 bit-identical: 0).
- Fold 1: C1 R 1.02 / 1.01 in band; bias fails PK, high tier and goals -5.0%.
- Post-hoc (labelled, not selectable): under M1 K500 the fold-2 C0 goals would be -1.4%, oracle -0.2%. The per-cell conversion keeps rising (D23 drift); E lags.

---

## PM ruling on G-R1 (2026-10-16, D35)

- No arm is eligible. The cause is the level: E was selected through in-sample parity (a PM spec error).
- The goalie step-0 trend (z +2.35) is listed (INV-53).
- The fold-2 goalie R of 0.67 is read again after the level fix.
- Lane G's crossing protocol for the goalie and team grids (goalie first, then team) is accepted.

---

## G-R2: G-R1 with the level re-selected under D35 (pre-registered 2026-10-16 by the PM, before any run)

Everything is frozen from G-R1 except the level: the cell table, rating constructions, (b, w, s) cells, C2 capacity and features, bias checks, R, and the decision rule.

- **Level.** Re-select from G-R1's committed training parity table, with E excluded (D35). Take the simplest passing family. M0 fails (0.57 pp), so the family is M1. Within it, take the K with the smallest max |parity| on genuine-prior seasons (no fold-2 input). Write the choice into the report before any refit.
- **Refit:**
  - C0, C1 and C2 with the new level.
  - The rating selection is not re-run: the fold-1 (b, w, s) cells stay. On fold 1, E equals no level, so it is re-checked only as a diagnostic. If a selected cell's fold-1 R moves outside [0.8, 1.2] under the new level, report it, and the cell is still kept.
- **Grade:** blind on fold 2, then the bias checks, R, the fold-1 guard and the decision, as G-R1.
- **If selected:** the engine gets the arm behind a flag as a labelled plumbing run (no gate), per G-R1's closed-loop note, after Lane A6 releases `sim.py`.

### Results

(append below this line)

### G-R2 results (Lane G2, 2026-10-16; report `docs/tests/goal_g_r2_2026-10-16.md`)

- Level re-selected from training parity (b66843e): **M1 K500** (0.240 pp; E excluded D35). Ratings, cells and C2 capacity frozen from G-R1.
- C2 in-sample stratum check FAILS on PK (fold 1 +0.239 pp, fold 2 +0.215 pp); C2 fitted and graded anyway, marked ineligible (disclosed deviation: the trainer was to stop).
- Fold 2: bias clean for every arm (C1 save% +0.05 pp, PP +0.55, goals +0.30%). **No arm eligible**: C1 goalie R 0.70 (CI 0.42-2.36, UNDERPOWERED, FAIL), team R 1.00. C1 vs C0 +0.0058 (SE 0.0039); C2 +0.0019 (0.0048); floor 0.00249. None selected.
- Fold 1: C1 R 1.03 / 1.05 in band, bias clean; C2 R goalie 1.21.

---

## PM ruling on G-R2 (2026-10-16, D36)

- The D35 level (M1 K500) clears every bias check: save% +0.05 pp, goals +0.3%.
- No arm is selected:
  - C1's goalie R is 0.70, below the band. The point estimate gates (D18), even though it is UNDERPOWERED (CI 0.42-2.36).
  - C1 vs C0 is +0.0058 (SE 0.0039), short of 2 SE.
- C0 is the stage-6 stand-in. It is flat in goalie and team, and labelled.
- Lane G2's deviation is accepted as disclosed: C2 was graded despite failing its in-sample PK stratum check (+0.24 pp), and marked ineligible.
- The goalie response trend (step-0 z +2.35) and the blocks result (D34) point to the same missing construction: an as-of response scale. INV-53 is promoted, and G-R3 tests it on the goalie.

---

## G-R3: as-of goalie response scale (pre-registered 2026-10-16 by the PM, before any run; INV-53)

Everything not listed is frozen from G-R2: level M1 K500, cell table, rating constructions and (b, w) cells, team finishing at its fixed scale, bias checks, R, grading, floor. Only C1-type arms; no booster (D31).

### Construction

The goalie rating enters as s_t x (standardised as-of goalie rating), where s_t is an as-of estimate of the goalie-rating logistic coefficient:
- **Estimation window:** all shots on goal before the game date (across seasons), weighted by 0.5^(age in days / H).
- **Fit:** a one-parameter logistic slope with the C0 + team offsets fixed, shrunk toward the previous day's s with a prior of strength P shots.
- **Snapshot:** s_t is computed per game date, with `created_at < puck_drop`.
- **Grid:** H in {90, 180, 365} days x P in {2000, 10000}.

### Parity analogue (training seasons only; out of sample by construction, since s_t is as-of)

Per genuine-prior training season (both folds), the goalie R of the arm C1s must lie in [0.9, 1.1].
- Selection: the simplest passer (larger H, then larger P, counts as simpler).
- Otherwise: the smallest max |log R|, listed, then proceed.
- Also report the per-season fixed-scale R from G-R2's C1 for comparison.

### Arms

| Arm | Model |
|---|---|
| C0 | stand-in comparator |
| C1 | G-R2's C1 (reference) |
| C1s | C1 with the as-of goalie scale |

### Decision

- **Eligible:** every fold-2 bias check passes and both R values are in band.
- **Selected:** eligible and beats C0 by > 2 SE and > the floor.
- **D13 guard:** in band on fold 1.

If C1s is not selected, stage 6 stays on the C0 stand-in. The PM then reports the goalie gap to the user, because goalie-saves props depend on it.

### Results

(append below this line)

### G-R3 results (Lane G3, 2026-10-16; report `docs/tests/goal_g_r3_2026-10-16.md`)

- Step 1 (252e539): s_t snapshots for the 6-cell grid, with a leakage test (`tests/test_goal_asof_scale.py`): s on a date is bit-identical when every later outcome is flipped. Unit z = g_r / SD of 2021-22; start s = 0 (2021-22 burn-in, labelled).
- Step 2 (252e539, before any fold-2 prediction): **no cell passes** the [0.9, 1.1] parity analogue; every cell over-responds (max |log R| H365 0.50, H180 0.37, H90 0.16; P makes no difference). **Selected H90 P2000** by the fallback rule. Per-season C1s R: 1.15 / 1.13 / 1.18. G-R2's fixed C1: 0.70 / 0.69 / 1.13.
- Fold 2 (blind): **C1s is eligible but not selected.** Bias is clean (save% +0.06 pp, PP +0.56, RS goals +0.23%). Goalie R is 0.98 (CI 0.57-2.67, UNDERPOWERED) and team R 0.99, both in band. Its LL vs C0 is +0.0052 (SE 0.0042), short of 2 SE. Floor 0.00249 (frozen). C1 reproduces G-R2 (goalie R 0.70).
- Fold 1: C1s R 1.08 / 1.05, bias clean, +0.0079 (SE 0.0043). D13 guard: not applicable.
- Stage 6 stays on the C0 stand-in, per the spec.

---

## PM ruling on G-R3 and the user decision (2026-10-16, D40)

- The selection rule is harmonised with stage 4: eligible, and not worse than the flat stand-in by > 2 SE.
- C1s is selected: as-of goalie scale H90 P2000, team finishing at a fixed scale, level M1 K500.
- Status: CONFIRMED-INCUMBENT (provisional).
- Listed: LL +1.2 SE, goalie R UNDERPOWERED, the parity fallback, and the step-0 trend.
- The engine wiring and closed loop are INV-60.

---

## G-R4: score-state terms of the goal model (pre-registered 2026-10-21 by the PM, before any run; D48, INV-74, INV-71)

Everything not listed is frozen from G-R3 / D40: level M1 K500, the as-of goalie scale (H90 P2000; the AS-1 floor leaves its served dates unchanged, D44), team finishing at its fixed scale, home, rest, the arena distance factor, the bias checks, R, grading, floor. Only the score-state terms change. No booster (D31).

### Problem (INV-71, `docs/tests/margin_diagnosis_inv71_2026-10-21.md`)

C1s carries pooled score-bucket dummies (trail 2+, trail 1, tied, lead 1, lead 2+; tied is the reference). On both holdouts the served tied conversion is under-predicted (0.968 / 0.973 of actual) and trailing is over-predicted relative to tied; the real trailing-by-1 vs tied conversion ratio drifts 1.038 -> 0.968 over four seasons, so pooled dummies lag a trend (L27). This explains about half of the 55:00 tie-rate gap. Score state is the state BEFORE the shot (modeling rule).

### Arms

| Arm | Model |
|---|---|
| C1s | the incumbent (reference; must reproduce G-R3) |
| C1s-sa | the four score-bucket log-odds deviations (relative to tied) estimated as-of: the AS-1 floored as-of estimator generalised to four dummies, offset fixed at C0 + goalie (as-of scale) + team + home + rest + arena, rows weighted 0.5^(age / H), shrunk to the previous date's values with prior P SOG, start 0, burn-in 2021-22 never judged or served, `created_at < puck_drop`, leakage tests. Grid H in {90, 180, 365} x P in {2000, 10000} |
| C1s-sp | pooled score bucket x period (P1 / P2 / P3) dummies, fitted on the training seasons (tied-P1 reference) |
| C1s-sap | C1s-sa plus pooled period-interaction deviations (bucket x period minus bucket main effect) on top |

Complexity order: C1s < C1s-sa < C1s-sp < C1s-sap. Ties within 2 SE go to the simpler arm.

### Step 0 (training seasons only; committed before any arm is fit)

Per-season pooled-dummy coefficients with SEs (the trend the as-of levels must track), and the per-season served / actual conversion by bucket relative to tied for C1s.

### Parity analogue for C1s-sa (judged training seasons only; committed before any fold-2 read)

Served / actual conversion by score bucket, relative to tied, within +/-3% on every judged season (fold 1: 2022-23; fold 2: 2022-23, 2023-24). Selection: the simplest passer (larger H, then larger P). Otherwise the smallest max |log ratio|, listed.

### Checks and decision (fold 2, blind)

- **Eligible:** every G-R3 bias check passes (save % by group, tier, month), goalie and team R in band, the fold-1 D13 guard holds (same checks), AND the new check: served / actual conversion by score bucket relative to tied within +/-3% on fold 2 and on fold 1.
- **Selected:** eligible and not worse than C1s by > 2 SE on LL per SOG; among eligible arms, the simplest whose LL is within 2 SE of the best. Floor 0 (deterministic logistic; stated).
- On selection: the engine serves the selected arm behind a default-off flag (flag off bit-identical; served vs offline 1e-6), after the sim.py order of D44 / D48. Closed loop (200 seeds, fold 2, pull off): G4 unchanged within noise; the team-standardised goal O/E by score bucket within 1 SE of real; and the new gate **G5b**: at 55:00 with the pull off, vs actual with goalie-out goals removed, the tie share within 1.5 pp and |margin| cells (0, 1, 2, 3+) within 1.5 pp (`docs/gates.yaml`).
- If no arm is eligible, the goal model stays C1s and the PM rules; nothing downstream absorbs the gap.

### Results

(append below this line)

### G-R4 results (Lane G4, 2026-10-21; report `docs/tests/goal_g_r4_2026-10-21.md`): STOPPED after step 3, fold 2 unread

- Step 0 (1be71d3, training seasons only): four bucket deviations on the frozen C1s non-score logit; fold-2 trend z lead1 +2.69 (0.011, 0.059, 0.125), others |z| <= 1.01; trail1 flat on training seasons (0.068, 0.048, 0.050).
- Step 2 (0838766, before any fold-2 read): C1s-sa snapshots for the 6-cell grid, AS-1 floor f 0.5 (never binds), leakage tests; parity: no cell within +/-3% on every judged season; **selected H90 P2000** by the fallback (max |log ratio| 0.044, listed).
- Step 3 (fold 1, 2023-24): C1s reproduces G-R3 (max |diff| 0). All non-C0 arms pass the G-R3 bias checks and R; LL per SOG vs C1s: C1s-sa +0.000009 (SE 0.000044), C1s-sp -0.000083 (0.000051), C1s-sap -0.000067 (0.000064). Bucket ratio vs tied (trail2+ / trail1 / lead1 / lead2+): C1s 1.068 / 1.027 / 0.948 / 1.014; C1s-sa 1.040 / 1.009 / 1.011 / 1.004; C1s-sp 1.067 / 1.028 / 0.948 / 1.016; C1s-sap 1.040 / 1.010 / 1.013 / 1.006. **Every arm fails the D13 guard on the +/-3% check**, so no arm can be eligible.
- Cause (labelled parametric redraw from each arm's own probabilities): SD of a one-season bucket ratio about 0.032; a calibrated model passes all four buckets within +/-3% with probability 0.20-0.22 per season; the 95% band is +/-7.6-8.0%. Stopped before step 4 (the D45 pattern) for a PM restatement of the check; fold 2 unread; no engine step. Resume commands in the report.
