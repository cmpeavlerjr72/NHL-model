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
