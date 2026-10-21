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

---

## PM ruling on SB-R3 and the user decision (2026-10-16, D32)

- The cause is diagnosed: the ratings carry arena scorer recording, and the pooled rating response over-responds on the next season.
- Responsiveness now gates on the decile slope ratio R (D32).
- B0 is the engine stand-in.
- Next is SB-R4 (below).

---

## SB-R4: arena-free block ratings at a fixed, spread-tuned scale (pre-registered 2026-10-16 by the PM, before any run; D32)

Everything not listed is as in SB-R1: level M1 (K = 500), bias checks, grading, the floor, and the arena factor (it stays a feature in every arm, so arena recording is modelled once, there). Responsiveness gates on R (D32).

### Rating constructions (as-of, b 1,000, w 0.7, log-odds relative to the snapshot league mean)

| id | construction |
|---|---|
| Rr | road games only, for both ratings |
| Ra | all games, each game's counts adjusted by the as-of arena factor of the game's arena before accumulating |

### Step 0 (training seasons only; committed before step 1)

For B1-style fits on each training season alone, the rating coefficients per construction (incumbent SB-R1 ratings, Rr, Ra), with SEs. The question is whether the per-season response is flat across seasons for Rr / Ra. Report it; there is no decision here.

### Arms

The rating enters as a fixed-scale offset: s x (standardised rating). The scale s is not refit. It is chosen on fold 1 over s in {0.25, 0.5, 0.75, 1.0, 1.25} x the fold-1-fitted coefficient: the s whose fold-1 R (for and against) is closest to 1, among values with fold-1 LL within 2 SE of the best.

| Arm | Model |
|---|---|
| B1r | B0 + home + score + rest + arena factor + Rr at its fixed scale |
| B1a | the same with Ra |
| B2x | the booster from SB-R1, init_score = logit of the better of B1r / B1a on fold 1 by the s-rule criterion; no rating features in the trees |

Complexity: B0 < B1r = B1a < B2x. B1r and B1a are equal in complexity, so if both are eligible the one with higher fold-2 LL wins; a tie within 2 SE goes to Rr (fewer inputs).

### Decision

As SB-R1, with R for responsiveness. The D13 guard: the selected arm is also in band (R) on fold 1. On selection, the arm replaces the B0 stand-in in the engine (separate closed-loop step).

### Results

(append below this line)

### SB-R4 results (Lane B4, 2026-10-16; report `docs/tests/block_sb_r4_2026-10-16.md`)

- Step 0 (committed f697689 before any step-1 fit). Rr / Ra remove the arena content (corr with the arena factor 0.19 / 0.14 -> -0.06 / -0.01 and 0.01 / 0.02). The per-season "against" coefficient still falls (Rr 1.18 / 1.05 / 0.83, Ra 1.09 / 0.98 / 0.81; trend z -2.3 / -2.1); "for" is non-monotone and UNDERPOWERED per season.
- Fold-1 s grid (committed cf2633d): Rr s = 1.0 (R 0.749 / 1.292), Ra s = 1.0 (R 0.807 / 1.201); B2x base Ra.
- Fold 2: no arm eligible; none selected. Every block-share bias check passes.

  | arm | LL vs B0 | R for / against | arena slope gate |
  |---|---|---|---|
  | B1r | +0.060 | 1.49 / 1.52 | FAIL (2.05 SE) |
  | B1a | +0.070 | 1.21 / 1.33 | pass |
  | B2x | +0.095 | 1.18 / 1.36 | pass |

  - Floor 0.00055. "Against" R CIs exclude the band (powered); "for" R is UNDERPOWERED (CI 0.73-3.1).
- Fold 1: B1a 0.807 / 1.201, B2x 0.786 / 1.153, B1r 0.749 / 1.292 (B1r also fails the arena gate).

---

## PM ruling on SB-R4 (2026-10-16, D34)

- No arm is eligible. The per-season "against" response still declines after the arena content is removed.
- Block team ratings are parked.
- B0 stays the engine STAND-IN.
- An as-of response scale is deferred (INV-53).
- The 4v4 / 3v3 level groups go into the stand-in (INV-54).

---

## SB-R5: block ratings with the as-of response scale (pre-registered 2026-10-21 by the PM, before any run; D43, INV-53, INV-64)

Everything not listed is frozen from SB-R4 / SB-R1: the Ra rating construction (arena-adjusted, all games, b 1,000, w 0.7, log-odds relative to the snapshot league mean), the level M1 K500, the fitted home / score / rest terms and the arena factor (frozen from the fold's SB-R4 B1a fit), the bias checks, the arena slope gate (within 2 SE), R (D32), grading, the floor. Rr is dropped (SB-R4: it fails the arena gate). No booster (D31). The SB-R4 fixed multiplier is not used; the as-of scale replaces it.

### Comparator

**B0'**: the B0 stand-in as served by the engine since D41: level M1 K500 with own level groups for 4v4 and 3v3 (INV-54). The original SB-R1 B0 (pooled ES) is reported alongside for continuity.

### Construction (the SL-R7 template on a binary logistic)

The ratings enter as s_for,t x z_for + s_against,t x z_against on the logit, where z are the Ra ratings standardised by their fold's 2021-22 SD (unit only), and (s_for,t, s_against,t) is the as-of pair:
- **Window:** every in-scope attempt (the SB-R1 row scope) dated before the game date, across seasons, weighted 0.5^(age in days / H).
- **Fit:** the two-slope logistic with the offset fixed at logit B0' + the frozen SB-R4 B1a non-rating terms (home, score, rest, arena factor), shrunk to the previous date's pair with prior precision P x Ibar_t, **with the AS-1 floor at the selected f** (INV-62). Start (0, 0); 2021-22 is burn-in, never judged or served. `created_at` = the previous date's last puck drop + 6 h, asserted < puck_drop.
- **Leakage tests** as in SL-R7, in `tests/test_block_asof_scale.py`.
- **Grid:** H in {45, 90, 180, 365} days x P in {2000, 10000}.

### Step 0 (training seasons only; committed before step 2)

Re-state SB-R4's per-season Ra coefficients (for, against, with SEs) as the trend the as-of pair must track; add the per-date s_t path per cell (training dates only).

### Parity analogue (judged training seasons only; fold 1: 2022-23; fold 2: 2022-23 and 2023-24)

The "for" R and "against" R of B1a-as must both lie in [0.9, 1.1]. Selection: the simplest passer (larger H, then larger P). Otherwise the smallest max |log R| over both directions and all judged seasons, listed. Also report the per-season R of SB-R4's fixed-scale B1a and the labelled season-own-MLE diagnostic. Committed before any fold-2 row is predicted.

### Arms

| Arm | Model |
|---|---|
| B0' | stand-in comparator (M1 K500, INV-54 groups) |
| B1a | SB-R4's fixed-scale arm (reference; must reproduce the SB-R4 fold-2 grade on the original B0) |
| B1a-as | B0' + frozen terms + the as-of pair on Ra |

### Checks before fold 2 (stop if any fails)

- In-sample block share by strength group x period type on the judged training seasons: B1a-as within 0.5 pp of B0'.
- The D28-form guard on fold 1: B1a-as minus B0' block share within 0.5 pp overall and by strength group.

### Decision (D40 harmonised rule)

- **Eligible:** every fold-2 bias check passes (the SB-R1 block-share checks), the arena slope gate passes, "for" R and "against" R are in [0.8, 1.2] (point estimates gate; CIs listed, UNDERPOWERED when they contain 1 on both sides), and the D13 guard holds on fold 1 (R in band, not worse than B0' by > 2 SE, bias clean).
- **Selected:** eligible and not worse than B0' by > 2 SE on fold 2 (LL per game).
- On selection: wire B1a-as into the engine behind a default-off flag (flag off bit-identical to HEAD; the per-date pair served from the committed snapshot), replacing B0 when on, then run the closed loop (200 seeds, fold 2, with the engine's other incumbents): blocked share by strength state vs actual within the SB-R1 bias bands, blocked and unblocked attempts per 60 by state, a team-decile R on the sim block share (D32 helper), and the G3 / G2 re-checks unchanged within noise. Nothing in the loop is tuned.
- If B1a-as is not selected, blocks stay on the B0 stand-in and the PM reports; the next step is a PM ruling, not an automatic round.

### Results

(append below this line)

### SB-R5 results (Lane B5, 2026-10-21; report `docs/tests/block_sb_r5_2026-10-21.md`)

- AS-1 floor f = 0.5 (D44). Snapshots `block_scale_v1_f{1,2}`. Parity analogue: no cell in [0.9, 1.1]; the fallback selects **H90 P2000** (max |log R| 0.138; the 2022-23 "against" R is 1.15). This was committed (b04dabd) before any fold-2 prediction.
- Both checks before fold 2 pass:
  - in-sample, B1a-as minus B0' within 0.10 pp by strength group on the judged seasons (every group x period cell within 0.49 pp);
  - D28-form guard on fold 1, overall +0.08 pp.
- Fold-1 D13 guard: PASS (R 0.981 / 0.994, +0.0957 nats/game vs B0', SE 0.0124, bias clean).
- Fold 2: **B1a-as is selected (D40).**
  - +0.0701 nats/game vs B0' (SE 0.0113).
  - ES R "for" 0.986 (CI 0.60-2.54), "against" 0.999 (CI 0.78-1.35); both UNDERPOWERED.
  - Every block-share bias check passes: overall +0.34 pp; ES +0.25, PP +0.95, PK +0.22.
  - Arena slope +4.6 (SE 5.4), PASS.
  - The SB-R4 B1a reference reproduces exactly (+0.0699 vs B0, R 1.213 / 1.328).
- Engine wiring and the closed loop are PENDING. The PM's sim.py order is H8a -> H8b -> B5, and no `engine_otso` commit appeared by 14:48.
  - The serving table (`block/serve_b1aas.py`) matches the offline prediction to 1.1e-16.
- **Engine and closed loop (resumed after `engine_otso`, commit marker `engine_b1aas`).**
  - Flag `attr["block_b1aas"]` is default off. Flag-off output is bit-identical to HEAD 0838766 on 16 fixture cases. Served vs offline: 1.67e-16.
  - 200-seed fold-2 loop (default set + flag; pull and shootout off): block share by state passes the SB-R1 bands. Overall +0.35 pp; ES +0.25, PP +0.97, PK +0.27; 4v4 -0.40 and 3v3 -0.14 (UNDERPOWERED).
  - Team-decile R on the sim block share: 0.979 / 1.012 (UNDERPOWERED).
  - G3 PASS and unchanged vs the paired B0' loop (deltas < 0.01). G2 unchanged; 3v3 +5.4% is listed as before.
