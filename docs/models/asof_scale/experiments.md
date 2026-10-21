# As-of response scale (INV-53): shared construction experiments

Append-only. The as-of response scale is the standing construction for any rating whose step-0 per-season coefficient trends (D43, L35, L37). Instances: goalie (`src/nhl_sim/goal/scale.py`, G-R3, H90 P2000), stage-4 Qa (`src/nhl_sim/shot_attribute/scale.py`, SL-R7, H45 P10000). This file holds the experiments on the construction itself; each application is pre-registered in its own model's `experiments.md`.

## AS-1: prior-precision floor for the burn-in start-up spike (pre-registered 2026-10-21 by the PM, before any run; INV-62, D42, L38)

### Problem

The prior precision is P x Ibar_t (the per-event Fisher information at the current iterate). On the first dates of the burn-in season the ratings have near-zero spread, Ibar_t is near zero, the prior has no strength, and the slopes spike (SL-R7: raw 500-680 for two weeks; the burn-in 4v4 stratum +20%). Later season starts carry the slopes forward and show no spike.

### Construction

Let I_ref be Ibar evaluated at s = 0 over every in-scope row of the burn-in season (2021-22) of the fold, with the ratings in their standard units (the fold's 2021-22 SD). It is a fixed matrix per fold (a scalar for a one-slope scale), computed once, and it is not a tuned quantity.

The prior precision on date t becomes P x Ibar_t when lambda_min(Ibar_t) >= f x lambda_min(I_ref), and P x (Ibar_t + f x I_ref) otherwise. The floor binds only while the window carries less than a fraction f of the steady-state information; on every later date the construction is unchanged, so the judged-season snapshots are bit-identical to the unfloored ones unless the floor binds there.

Grid: f in {0.05, 0.10, 0.25, 0.50}.

### Selection (training seasons only; no fold-2 row is touched)

For each existing instance (goalie H90 P2000 on both folds; stage-4 H45 P10000 on both folds):
1. Re-run the snapshots for each f. Record, per fold: the max |s_t| (raw units, per direction) over the burn-in season; the max |s_t| over the judged training seasons; whether the judged-season snapshot is bit-identical to the unfloored one (and if not, the max |delta s| and the dates).
2. **Selected f:** the smallest f for which, on every instance and fold, the burn-in max |s_t| is at most 3 x the judged-season max |s_t| AND the judged-season snapshots are bit-identical. The same f is used for every instance (one construction).
3. If no f satisfies both, stop and report; the PM rules. No instance's incumbent snapshot is replaced in this experiment: the floored snapshots are written as versioned siblings (`*_v2_f{fold}.parquet`), and the incumbents stay as they are until a PM ruling.
4. Leakage tests (the flip test, the first-date test, the within-day shuffle) pass on the floored construction for both instances.
5. The burn-in in-sample check of SL-R7 (4v4 and every other stratum, 2021-22 rows included) is re-stated under the floored stage-4 snapshot and reported; it does not gate anything (2021-22 is never judged or served), it shows whether the spike is gone.

### Results

(append below this line)
