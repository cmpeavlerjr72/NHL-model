# Miss vs on goal: experiments (append-only)

Cascade stage 5, second step (D23). Given an unblocked attempt with its location cell and type (stage 4), this model decides missed vs on goal. Goal given on-goal is stage 6. Every fit uses recorded rows, never stand-in output (D32).

---

## SM-R1: miss-decision bake-off (pre-registered 2026-10-16 by the PM, before any run)

### Target and rows

- **Rows:** one per unblocked, non-shootout, non-penalty-shot attempt (`missed-shot`, `shot-on-goal`, `goal`). y = 1 if `missed-shot`.
- A goal counts as on goal. A shot hitting the post or crossbar is a miss in the NHL feed, which is reported here as a share.
- **Gated rows:** 5v5, PP-for and PK. 4v4 / 3v3 are reported with n and gate at stage 8 for 3v3 (INV-35); 4v4 is reported. EN-for and EN-against are reported only (D28).

### Level (lessons L13, L27-L31)

The miss share rose 27% -> 35% over 2021-25 (SL-R1). An as-of level per strength group enters as a logit offset. Constructions:

| id | construction |
|---|---|
| M0 | last season's final share |
| E | the D24 recording era |
| M1 | season to date shrunk to M0, K in {500, 2000, 8000} |
| M2 | discounted, K = 2000, half-life {30, 60} days |
| O | oracle (season's own final share) |

Parity: per genuine-prior training season, level-only arm S0 within +/-0.3 pp overall and 5v5. Selection uses the LC-2 / SB-R1 rule.

### Arms

| Arm | Model |
|---|---|
| S0 | level + recorded cell x type x strength-group frequency, from training rows (the location-conditional baseline) |
| S1 | logistic: S0 offset + home + score bucket + rest + as-of arena miss-recording factor + shooting team's road-only miss rating at a fixed, spread-tuned scale (D32 construction, s-grid {0.25, 0.5, 0.75, 1.0, 1.25} x the fitted coefficient, chosen on fold 1 by R closest to 1 among s within 2 SE of the best LL) |
| S2 | LightGBM binary, init_score = logit of S0 (L32); features S1's minus the rating (no rating in the trees, D31); EN rows get S0 only (L33); num_leaves {7, 15} x min_data {200, 800}, lr 0.05, early stopping on the fold-1 inner split |

Complexity: S0 < S1 < S2. In-sample stratum check for S2 (+/-0.2 pp vs S0 per gated group) before any holdout.

### Metric, floor, decision

- **Primary:** fold-2 Bernoulli LL per game vs S0 (game-block bootstrap SE). Grading is blind, with `scripts/grade_miss.py`.
- **Floor:** an S2 seed-2 retrain; if bit-identical, the floor is 0 (D26).
- **Decision rule:** as in the other stages. Eligibility = every bias check + R in band (D32) for the shooting-team rating; > 2 SE and > the floor to beat a simpler arm. S0 is flat for teams and not adoptable (D24), but it is the stand-in if nothing is eligible.
- **D13 guard:** the selected arm has R in band on fold 1.

### Bias checks (fold 2 gates; fold 1 diagnostic)

- Miss share: overall within +/-1.0 pp; per gated group within +/-1.5 pp (n >= 2,000); per location tier (high / medium / low danger) within +/-1.5 pp; by month within +/-2.0 pp (n >= 100 games).
- Per arena: reported; the residual-on-factor slope is within 2 SE of 0 for S1 / S2.

### Closed loop

Deferred to a separate engine step. Stage 4 is still on its stand-in, so the closed-loop gate (SOG per 60 by strength state within the G2 tolerance, CLEAN) runs once a stage-4 incumbent exists. A plumbing run on the stand-ins is allowed, labelled.

### Results

(append below this line)

### SM-R1 results (Lane M, 2026-10-16; report `docs/tests/miss_sm_r1_2026-10-16.md`)

- Level M1 K500 by fallback (max parity 0.321 pp vs 0.3; E excluded from selection by D35; oracle 0.138). Fold-1 s-grid (committed dcdffd4 before any fold-2 fit): s = 0.75, c = 0.717, R 0.94.
- Fold 2: S1 +0.0218 and S2 +0.0175 nats/game vs S0 (SE 0.0064 / 0.0037; floor 0.00106). Every bias check passes except the low-danger tier (S0 -1.72, S1 -1.74, S2 -1.75 pp; the 2024-25 drift is concentrated in low-danger cells). S1 ES R 1.03 (0.78-1.50, UNDERPOWERED) and arena slope PASS; S2 R 0.39 and arena slope FAIL. **No adoptable arm eligible; S0 stays the stand-in.**
- Fold 1: S1 R 0.94 but arena gate FAIL (+13.7, SE 6.5) and no LL gain (-0.0049, SE 0.0082).
- Post / crossbar share of misses 6.3 / 6.4 / 6.3 / 8.4% (2021-22 to 2024-25).

---

## PM ruling on SM-R1 (2026-10-16)

- No arm is eligible. S1 fails only the low-danger tier (-1.74 pp, limit 1.5) and is otherwise clean (R 1.03, UNDERPOWERED).
- **D35 check.** Lane M read fold 2 before the correction arrived. The selection was M1 K500, not E, and E failed parity anyway, so the corrected rule selects the same level. The fold-2 read stands as valid.
- **Cause.** The 2024-25 miss-share drift is tier-specific: low-danger tier 31.6 -> 35.3%, high-danger 29.0 -> 30.9%. The single per-group level shifts every cell equally.
- S1 shows no fold-1 LL gain over S0 and fails the fold-1 arena gate. It would fail the D13 guard, so SM-R2 requires the guard explicitly.
- **Accepted as labelled:**
  - S1 and S2 fit on gated rows only;
  - S0 base-table K = 20;
  - the rating and arena priors inherited from SB-R4.
- The post / crossbar share rose 6.3% -> 8.4% in 2024-25, another sign of a recording change. Listed.

---

## SM-R2: tier-specific miss level (pre-registered 2026-10-16 by the PM, before any run)

Everything not listed is as in SM-R1: cells, rating construction and the s-rule, arena factor, bias checks, R, grading and floor.

### Level

An as-of miss level per (strength group in {5v5, PP, PK}) x (danger tier in {high, medium, low}). Constructions M0 / M1 (K in {500, 2000, 8000}, scaled by the tier's share of attempts) / M2, plus the oracle. E is reported, not selectable (D35).
- Parity per genuine-prior training season and per tier within +/-0.5 pp.
- Selection uses the SB-R1 rule with the D35 exclusion.

### Arms

| Arm | Model |
|---|---|
| S0t | tier level + cell x type x group table |
| S1t | S0t offset + S1's features (home, score, rest, arena factor, road-only rating at a fixed scale, s re-selected on fold 1 by the D32 rule under the new level) |

There is no booster arm (D31).

### Decision

- S1t is eligible if every fold-2 bias check passes and R is in band.
- **D13 guard, binding:** on fold 1, S1t has R in band, passes the arena gate, and is not worse than S0t by > 2 SE.
- It is selected if eligible, guarded, and not worse than S0t by > 2 SE on fold 2. S0t is flat; if nothing is selected, it replaces S0 as the stand-in.

### Results

(append below this line)

### SM-R2 results (Lane M2, 2026-10-16; report `docs/tests/miss_sm_r2_2026-10-16.md`)

- Tier level: no as-of construction passes the 0.5 pp parity (best M2_H30 0.696; E 1.16 not selectable; oracle 0.43). Fallback selects M2_H30. Fold-1 s re-selection (372436c, before any fold-2 fit): s = 0.75, c = 0.7156, R 0.94.
- Fold 2: S1t +0.0214 nats/game vs S0t (SE 0.0064; floor 0, no seed-dependent arm). Every bias check passes for both arms, tiers high / medium / low -0.87 / -0.24 / -1.00 pp for S1t (the SM-R1 low-tier failure is cleared). S1t ES R 1.04 (0.79-1.50, UNDERPOWERED), arena slope -7.1 (SE 6.5) PASS: **eligible**. S0t R 0.40.
- D13 guard (fold 1): S1t R 0.94, LL -0.0048 (SE 0.0083), bias clean, but arena slope +13.5 (SE 6.3) FAILS (limit 12.6). **Guard fails; no arm selected; S0t replaces S0 as the stand-in.**

---

## PM ruling on SM-R2 (2026-10-16, D37)

- Nothing is selected: S1t fails the binding fold-1 D13 guard (the arena slope flips sign, and there is no fold-1 LL gain).
- S0t is the stand-in. Miss team terms are parked.

---

## SM-R3: score-state term on the miss stand-in (pre-registered 2026-10-21 by the PM, before any run; D48, INV-75, INV-71)

Everything not listed is frozen from SM-R2 / D37: the tier level (M2 H30 by group x tier), the S0t cell x type x group table, EN rows served from their own group, the bias checks, grading, floor 0. Team terms stay parked. The arms here are stand-in-grade (flat in team) and are labelled STAND-IN in the engine whatever is selected.

### Problem (INV-71)

S0t has no score term; the real miss share has a stable score gradient (the same in all four seasons per the diagnosis), which contributes about 5% of the 55:00 tie-rate gap. Score state is the state BEFORE the attempt.

### Step 0 (training seasons only; committed before any fit)

Per-season logistic score-bucket coefficients (relative to tied) on top of S0t with SEs, and a trend z per bucket (L35). If any |z| > 2, the round stops after this commit and reports: an as-of construction would be needed, pre-registered separately.

### Arms

| Arm | Model |
|---|---|
| S0t | the incumbent stand-in (reference) |
| S0t-s | S0t + pooled score-bucket dummies (trail 2+, trail 1, tied, lead 1, lead 2+; tied reference), fitted on the training seasons |
| S0t-sp3 | S0t-s with a separate set of bucket dummies in the third period (and OT rows served the baseline, L33) |

### Checks before fold 2 (stop if any fails)

- In-sample miss share by group x tier within 0.5 pp of S0t on the judged training seasons.
- D28-form guard on fold 1: arm minus S0t miss share within 0.5 pp overall and per group.

### Decision (fold 2, blind)

- **Eligible:** every SM-R2 bias check passes (overall, group, tier, month), miss share by score bucket within +/-1 pp of actual on fold 2 and on the fold-1 D13 guard.
- **Selected:** eligible and better than S0t by > 2 SE on LL per attempt; S0t-sp3 over S0t-s only if better by > 2 SE. Otherwise S0t stays.
- On selection: engine flag (default off; flag off bit-identical; served 1e-6), after the sim.py order of D48; the closed loop is shared with G-R4's (G5b) and is run by whichever lane wires last.

### Results

(append below this line)
