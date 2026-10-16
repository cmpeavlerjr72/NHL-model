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
