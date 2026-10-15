# Control engine: experiments (append-only)

The Control engine is the yardstick (ARCHITECTURE_DECISIONS D3): a team-rate game model that the event engine must match or beat on fold 2 before it ships. It is not a profit model and gets no market inputs.

---

## R1: Control bake-off (pre-registered 2026-10-15 by the PM, before any run)

### Question

Which team-rate scoring model gives the best calibrated joint distribution of final scores on fold 2, and with what dispersion structure?

### Unit and target

One row per game, regular season and playoffs. The target is the final score excluding the shootout bonus goal: `(home_goals, away_goals)` at the end of regulation plus OT goals. End state REG/OT/SO comes from `data/reference/verified_finals_v1.parquet` (or its independently verified successor from INV-14, if that has landed).

Each game is simulated as a regulation score. If regulation ends tied, it goes to an end-game model (below) that produces OT/SO winners. EN goals are inside the regulation score, because the Control is a reduced-form yardstick and not mechanistic.

### Ratings (shared by all arms)

- As-of ridge team ratings, refit for every game date using only games with puck drop strictly before that date. The `created_at < puck_drop` writer check applies.
- The ridge has a log-rate offence term and a defence term per team, plus a home term. It is a Poisson GLM with an L2 penalty, centred on each snapshot's league mean (LEARNINGS L1).
- Season carry-over: the prior is last season's final fit, shrunk by a carry weight w.
- Lambda and w are tuned on fold 1 only (grid lambda in {1, 3, 10, 30}, w in {0.5, 0.7, 0.9}), then frozen for fold 2.
- Goalie term in arms that use it: the oracle starting goalie's save-talent, from as-of GSAx-free shrunk Sv% (saves / SOG ex-EN, beta-binomial shrinkage to the league mean, prior strength tuned on fold 1). Every result is labelled "oracle goalie" (D8).

### Arms

| Arm | Score model | Goalie term |
|---|---|---|
| A0 | independent Poisson, rates from ratings | no |
| A1 | independent Poisson | yes |
| A2 | bivariate Poisson (shared component lambda3, fitted on fold 1 train) | yes |
| A3 | Poisson with a shared game-level gamma latent (negative-binomial-type overdispersion, one latent per game multiplying both teams' rates; variance parameter fitted on fold 1 train) | yes |
| A4 | A3 plus a back-to-back / rest-days term per team in the rating regression | yes |

End-game model (same for all arms; it is not a bake-off dimension in R1): P(home wins OT/SO | tied) is the as-of historical home OT/SO win rate. The split between OT and SO is the as-of historical rate.

### Folds

- Fold 1: train on games through 2022-23 and test on 2023-24. Used for hyperparameters only.
- Fold 2: train through 2023-24 and test on 2024-25. This is the SELECTION fold.
- 2025-26 stays sealed (INV-15) and 2026-27 is not touched.
- The 2021-22 season is used only as the carry-over prior source.

### Primary metric (fold 2)

Mean log score of the realised joint `(home_goals, away_goals)` under each arm's predicted joint distribution. It is computed from 10,000 seeds per game or analytically where the arm allows. Higher is better.

### Secondary metrics (reported, not deciding)

- ML Brier score and ML calibration by decile (including OT/SO resolution).
- RPS on total goals.
- Per-k cells of P(total = k), k = 0 to 10+, sim against actual (the G5 cell gate).
- Margin SD ratio and total SD ratio, each split into its accuracy and dispersion components (SIM_GUARDRAILS G5 note).
- Home/away score correlation, sim against actual.
- Regulation tie rate, sim against actual.
- Responsiveness: predicted team goals by team-rating quintile against actual goals (a slope, not a flat line).

### Segments (every metric)

overall, by month, by favourite band (|predicted margin| terciles), by home/away, by goalie quintile (A1-A4), playoffs vs regular season (playoffs are reported only and labelled underpowered if n < 300).

### Noise floor

- A paired game bootstrap (2,000 resamples) of the per-game log-score difference between each arm and A0.
- A seed floor from 4 seed-offset reruns of the winning arm, with the simulated components re-drawn.
- An arm beats another only if the 95% bootstrap interval of the difference excludes 0 AND the difference exceeds the larger of the seed-floor SD and 0.001 nats/game.

### Decision rule

- The winner is the arm with the best fold-2 primary metric that beats every simpler arm under the noise-floor rule. The simplicity order is A0 < A1 < A2 < A3 < A4.
- Ties go to the simpler arm.
- The Control is ADOPTED as the yardstick only if the winner also passes G5 cell gates within tolerance on fold 2, OR the failures are listed explicitly as the bar the event engine must clear.
- Nothing is tuned after seeing fold-2 numbers. Any new idea becomes R2.

### Grading

One script, `scripts/grade_control.py`, scores every arm blind. The arm labels are hashed until the table is final. Output goes to `docs/tests/control_r1_<date>.md` plus an appended results block in this file.

### Results

(append below; do not edit above this line)

#### R1 results (graded 2026-10-15 by Lane E; full record `docs/tests/control_r1_2026-10-15.md`)

Fold 2 (train through 2023-24, test 2024-25, 1,398 games), analytic mean log score of the realised (home, away) final score, oracle goalie where used. Frozen on fold 1 only (`r1_frozen_params.json`): lambda 30, w 0.5, goalie kappa 250, lambda3 6.6e-5, phi 1.0e-4, A4 rest ridge 100.

| arm | mean log score | diff vs A0 (95% paired bootstrap) | ML Brier |
|---|---:|---|---:|
| A0 | -3.86446 | - | 0.2411 |
| A1 | -3.86611 | -0.0017 [-0.0077, +0.0042] | 0.2406 |
| A2 | -3.86611 | -0.0017 [-0.0077, +0.0042] | 0.2406 |
| A3 | -3.86613 | -0.0017 [-0.0077, +0.0042] | 0.2406 |
| A4 | -3.86497 | -0.0006 [-0.0083, +0.0070] | 0.2394 |

Seed floor (SD of smoothed simulated estimates, 4 x 10,000 seeds): 0.0018 to 0.0026, above the 0.001 minimum; the analytic metric itself has zero seed variance. Winner under the decision rule: **A0** (nothing beats a simpler arm; A1 = A2 = A3 because the data want no positive dependence). Gate statuses for A0 on fold 2: G5 FAIL (P(total=4) -1.99 pp, 6 -1.03 pp, 10+ +2.16 pp; total SD ratio 1.082; score correlation -0.036 vs actual -0.115), G6 FAIL (home win 52.8% vs 56.5%), G7 FAIL (regulation ties 15.9% vs 20.8%; EN NEEDS-INSTRUMENTATION), G9 FAIL, G1-G4 and G8 NEEDS-INSTRUMENTATION. These failures are the bar the event engine must clear; real home/away scores are negatively correlated (-0.12) so A2/A3 (positive dependence only) could not help. Deviation: A4's first fold-2 run failed numerically (one game lambda 2e4) with a near-unpenalised rest term; the rest-term ridge was then chosen on fold 1 and re-frozen before the final run (record section "Incident"). Grid edges were hit for lambda, w, kappa and the A4 ridge: R2 candidates. No status decision is made here (the PM sets ADOPTED).