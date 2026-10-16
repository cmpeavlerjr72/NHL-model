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
