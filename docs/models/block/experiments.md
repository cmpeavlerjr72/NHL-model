# Block decision: experiments (append-only)

Cascade stage 5, first step (D23). Given a shot attempt from stage 3, this model decides whether it is blocked, before any location or type is drawn (stage 4 applies to unblocked attempts only). The model may not use shot location or type, because block coordinates are block points (D23). Misses and shots on goal of the unblocked attempts are the next stage-5 step.

---

## SB-R1: block-decision bake-off (pre-registered 2026-10-16 by the PM, before any run)

### Target and rows

- **Rows:** one per non-shootout, non-penalty-shot attempt (the stage-3 target set). y = 1 if `blocked-shot`.
- **Excluded** from the gates: EN-for and EN-against rows (empty net). They are reported only.
- **Strength group:** ES (5v5, 4v4, 3v3), PP-for, PK, from the shooting team's view, pre-event.

### Level (lessons L13, L27, L28, L29, L31: block recording drifts; blocks per game went 27 -> 34)

Use an as-of league block share per strength group, entered as a logit offset with coefficient 1. The constructions, with the oracle row:

| id | construction |
|---|---|
| M0 | last season's final share |
| E | the D24 recording era (era 2 from 2023-24; GameState flag) |
| M1 | season to date shrunk to M0, K in {500, 2000, 8000} attempts |
| M2 | the discounted form, K = 2000, half-life {30, 60} days |
| O | oracle (season's own final share) |

**Parity:** per genuine-prior training season, the level-only arm B0's block share within +/-0.3 pp, overall and in ES. Selection uses the LC-2 / SL-R2 rule: simplest passer, else the smallest max |parity| with ties within 0.1 pp to the simpler, failure listed, proceed.

### Arms

| Arm | Model | Features |
|---|---|---|
| B0 | level only | selected level x strength group x period type |
| B1 | logistic | B0 offset + score bucket (SA-R1 set) + home + rest / b2b + shooting team's as-of blocked-against rating + defending team's as-of blocks-for rating (per strength group; shrunk log-odds relative to the snapshot league mean, L1; prior b in {300, 1000, 3000} attempts, carry w in {0.5, 0.7, 0.85, 1.0}, tuned on fold 1 under the explicit L24 rule from SL-R2) + as-of arena block-recording factor (home arena's block share vs the both-teams expectation, past games only) |
| B2 | LightGBM binary | B1 features + clock + period; init_score = logit of B0 (L32); num_leaves {7, 15} x min_data {200, 800}, lr 0.05, early stopping on a time-ordered fold-1 inner split; seed-2 retrain for the floor |

Complexity: B0 < B1 < B2. In-sample stratum check for B2 before any holdout (L32): its block share per strength group on training rows is within +/-0.2 pp of B0's.

### Metric, floor, decision

- **Primary:** fold-2 Bernoulli LL per game vs B0, paired SE from a 1,000-resample game-block bootstrap.
- **Grading:** blind, with `scripts/grade_block.py`.
- **Decision rule:** as in stage 3 / stage 4. Beat a simpler arm by > 2 SE and > the seed floor; eligibility = all bias checks + the responsiveness band; ties go to the simpler arm.

### Bias checks (fold 2 gates; fold 1 diagnostic)

- Block share: overall within +/-1.0 pp; per strength group within +/-1.5 pp (n >= 2,000); by month within +/-2.0 pp (n >= 100 games).
- Per arena: reported, UNDERPOWERED below 1,500 attempts.
- The regression of the arena residual on the arena factor is reported with its SE. It gates only for B1 and B2: the slope must not differ from 0 by more than 2 SE.

### Responsiveness (ES)

Bucket by quintile of each rating, separately (shooting team blocked-against; defending team blocks-for). The predicted Q5-Q1 spread of block share over the actual spread must lie in [0.8, 1.2].

### Closed loop

Deferred. The engine's block-first stub (SL-R1 / SL-R3) is replaced by the selected arm in a separate step, after stage 4's closed loop lands, so that two lanes do not edit `sim.py` at once. That step's gate: blocked and unblocked attempts per 60 by strength state within the G2 tolerance, and CLEAN.

### Results

(append below this line)

### SB-R1 results (Lane B, 2026-10-16; report `docs/tests/block_sb_r1_2026-10-16.md`)

- Level: M1 K500 selected (simplest passer; M0 1.245 pp, E 0.817 pp fail parity; oracle 0.010). Ratings w 0.7, b 1000 (L24 in-band); B2 7 leaves / min_data 200 / 310 rounds. B2 stratum check passed.
- Fold 2: B1 +0.071 and B2 +0.096 nats/game vs B0 (SE 0.013 / 0.014; floor 0.0006); all block-share bias checks pass for B0, B1, B2 (overall +0.33 to +0.36 pp). B1 / B2 ES responsiveness 1.59 / 1.49 and 1.38 / 1.43 FAIL the band; B0 flat. **No arm eligible; none selected.** Fold 1: B1 eligible (0.83 / 1.18), B2 fails arena gate.

---

## PM ruling on SB-R1 (2026-10-16, D27)

- The level M1 (K = 500) is accepted.
- No arm is eligible: B0 is flat, and B1 / B2 over-respond on fold 2.
- The rating over-response is cross-cutting (penalties, stage 4, blocks). D27 changes how prior strength is chosen for every as-of rating.

---

## SB-R2: calibrated-spread rating shrinkage (pre-registered 2026-10-16 by the PM, before any run; D27)

Everything not listed is as in SB-R1: the level M1 (K = 500), features, B2 structure and its tuned booster parameters, bias checks, responsiveness band, grading, and the noise floor.

### Change

- **Rating grid:** prior b in {1000, 3000, 10000, 30000} attempts x carry w in {0.5, 0.7, 0.85}.
- **Selection on fold 1:** the cell minimising max(|log for-ratio|, |log against-ratio|) of the ES spread ratios, among cells with fold-1 LL within 2 SE (game-block bootstrap) of the best cell. Ties within 0.02 go to the larger b.
- **Reporting:** the fold-1 table of LL and both ratios for every cell.
- **Booster:** B2 is refit with the selected ratings. The booster hyperparameters stay as frozen in SB-R1.

### Decision

As SB-R1: eligibility = every bias check + the ES responsiveness band on fold 2. B2 must beat B1, and B1 must beat B0, by > 2 SE and > the floor.

The "for" spread is near 1 pp in actual terms, with a CI on its ratio of 0.90-6.7. Where the ratio CI is wider than the band, the cell is labelled UNDERPOWERED, but the point estimate still gates (as D18).

### Results

(append below this line)

### SB-R2 results (Lane B2, 2026-10-16; report `docs/tests/block_sb_r2_2026-10-16.md`)

- Fold-1 selection (committed db8880f before any fold-2 fit): 6 of 12 cells within 2 SE of the best-LL cell (b 3000, w 0.5); minimum max|log spread ratio| 0.190 at b 1000, w 0.7 (no other cell within 0.02). Stronger shrinkage did not bring the against-ratio toward 1 (1.11 at b 1000 up to 1.79 at b 30000 w 0.85), because the B1 coefficient is refit on the standardised rating. Selected cell = SB-R1's cell, so fold-2 results are identical to SB-R1.
- Fold 2: B1 +0.071 and B2 +0.096 nats/game vs B0 (SE 0.013 / 0.014; floor 0.0006); every block-share bias check passes. ES responsiveness B1 1.59 / 1.49, B2 1.38 / 1.43 FAIL the band (against CI 1.06-2.17 excludes it); B0 flat. **No arm eligible; none selected.** Fold 1: B1 eligible, B2 fails the arena gate.

---

## PM ruling on SB-R2 (2026-10-16, D29)

- No arm is eligible. The fold-2 results are identical to SB-R1.
- D27 is corrected: shrinkage cannot damp a refitted coefficient.
- Next is SB-R3 (below), which diagnoses first and then runs response-side arms.

---

## SB-R3: why the fitted block response does not transfer, then response-side arms (pre-registered 2026-10-16 by the PM, before any run; D29)

Everything not listed is as in SB-R1: level M1 (K = 500), features, the B2 booster parameters, bias checks, responsiveness band, grading, and the floor. Ratings stay b 1000, w 0.7.

### Step 0: diagnosis (training seasons and fold-1 test only; written into the report and committed before step 1)

1. **Per-season actual ES spread.** For each of 2021-22 to 2023-24, by quintile of the as-of rating (for and against): the actual Q5-Q1 block-share spread with a bootstrap CI.
   - Is the actual spread shrinking over seasons? (Fold 2's actual spread is not read here.)
2. **Coefficient by fold.** B1's rating coefficients fitted on fold-1 train vs fold-2 train, with SEs.
3. **Within-season persistence.** By month of the season: the slope of the realised block share on the as-of rating (this is the coefficient that would be calibrated for that month). Pooled over the training seasons, with SEs.
   - Is the full-season fitted coefficient driven by late-season rows, where ratings are mature, and then applied to all rows?
4. **Arena-factor interplay.** The rating coefficients with and without the arena factor.

### Step 1: arms (B1 structure; only the rating response varies)

| Arm | Rating response |
|---|---|
| B1 | as SB-R1 (reference) |
| B1p | coefficient = training-season time-forward persistence: the slope of realised block share in games t+1..t+20 on the as-of rating at t, estimated across training seasons only. It enters as a fixed offset scale, and is not refit |
| B1m | coefficient varies by as-of rating maturity: interaction of rating x log(1 + rating exposure in games), refit |

- B2p is B2 with B1p's fixed-scale rating offsets in its init_score. The trees get no rating features.
- Complexity order: B0 < B1p < B1 < B1m < B2p.

### Decision

As SB-R1: eligibility = every fold-2 bias check + the ES responsiveness band; > 2 SE and > the floor to beat a simpler arm. This is the third block round, so the D13 guard applies: the selected arm must also be in band on fold 1.

### Results

(append below this line)

### SB-R3 results (Lane B3, 2026-10-16; report `docs/tests/block_sb_r3_2026-10-16.md`)

- Step 0 (committed a12cde2 before any step-1 fit). The B1 coefficients are stable across folds: own 0.53 / 0.63, opp 0.99 / 0.94. Fitted per season alone, the defending-team ("against") response falls every training season (1.06 / 0.96 / 0.85), and so does the arena coefficient (0.75 / 0.57 / 0.20). The slope rises with rating maturity ("against" 0.72 at 0-9 games, 1.13 at 40-59), and this part is the same in every season. Cause: a pooled-season slope applied under a trend (L27 acting on a slope), plus a constant early-season over-response. Time-forward persistence (fold 2: 0.71 / 0.98) is no smaller than B1's coefficients, so step 0 predicted, before any fit, that B1p would not help.
- Fold 2: no arm eligible; none selected. Every bias check passes for every arm.

  | arm | LL vs B0 | ES "for" / "against" |
  |---|---|---|
  | B1p | +0.070 | 1.80 / 1.54 |
  | B1 | +0.071 | 1.59 / 1.49 |
  | B1m | +0.072 | 1.54 / 1.47 |
  | B2p | +0.095 | 1.74 / 1.57 |

  - Floor 0.0025. B2p beats B1 by +0.024 (SE 0.008).
- Fold 1: B1 and B1m are in band (0.83 / 1.18); B1p and B2p fail on "against" (1.24 / 1.23); B2p also fails the arena gate.
- Post-hoc, after the blind grade and never used to select: the 2024-25 ES row-level slope on the rating is 0.43 (SE 0.14) for "for" and 0.80 (SE 0.10) for "against", against B1's 0.64 / 0.98. The slope ratios are 1.50 / 1.22. The Q5-Q1 endpoint metric magnifies "against" (1.49), because actual Q4 is above Q5.
