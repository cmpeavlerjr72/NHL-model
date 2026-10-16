# SL-R2: as-of league location-mix level (cascade stage 4), Lane A2, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R2 (and SL-R1, inherited); D23. Brief: `docs/briefs/lane_A2_shot_attribute_r2_2026-10-16.md`.
- Step-0 script: `scripts/diag_shot_attribute_mixlevel_step0.py`; level module `src/nhl_sim/shot_attribute/mix_level.py`; level table `data/processed/shot_attribute/mix_level_v2.parquet` (every construction, per game, 3 level groups x 13 cells; `created_at < puck_drop` asserted). Full parity table: `results/shot_attribute_r2/step0_tables.md` (gitignored), reproduced below.

**Outcome: NO arm is eligible on fold 2, so step 4 (closed-loop G3 and the G2 re-check) was skipped, as the brief requires. The PM rules.**

- **Level:** step 0 selected level E by the fallback rule. No as-of construction passes parity; the oracle does.
- **L0m:** with the level, the mix drift is fixed. L0m passes every bias check: xG_ref per attempt is +1.97%, and every tier and type share is within 1.5 pp. It gains +0.87 nats per game on plain L0 (z = 24), which is 92% of the oracle's gain. But L0m has no team features, so it is flat on responsiveness (0.00 / -0.03) and cannot be eligible.
- **L1m:** over-responds again (1.69 / 1.37), fails PK xG (+3.2%), and loses to L0m by 2.5 SE.
- **L3m:** in the responsiveness band (1.09 / 0.86) and ties L0m on likelihood. It fails ES xG (+3.27%, limit 3%), EN-for xG (-3.39%), and the PP and EN-for tier shares (by up to 2.3 pp). Most of that is an in-sample under-fit on the strength group, not drift (section 4).

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start | 10:50:37 | |
| step 0: levels, parity, selection | 10:53:14 | 10:53:21 |
| step 0 commit (66736da), before any L1m / L3m fit | 10:54 | |
| offset-MNL check vs SL-R1 sklearn L1 (fold 1) | 10:56:01 | 10:59:52 |
| tune: ratings grid (12 L1m fits, 4 processes x 2 threads) | 10:59:57 | 11:08:30 |
| tune: LightGBM grid, first pass (init_score without the class base; discarded, section 1) | 11:08:30 | 11:09:38 |
| tune: LightGBM grid, rerun (grid reused) | 11:10:13 | 11:10:57 |
| fold 2 fits (6 arms, 4 processes) | 11:11:02 | 11:13:47 |
| fold 1 fits | 11:13:50 | 11:15:51 |
| blind grade fold 2 / fold 1 | 11:15:51 | 11:16:34 |
| L3m in-sample diagnostic; full test suite (139 passed, 1 xfailed) + 4 new tests | 11:16:40 | 11:19 |

No compute step came near 15 minutes, so no box request was filed. Step 4 (closed loop) did not run: no arm is eligible.

## Step 0: mix-level constructions (committed before L1m / L3m are fit)

### Construction details (labelled where the spec left a choice)

- Level groups: ES (EN-for and EN-against pooled into it), PP-for, PK. Shares are over the 13 cells of unblocked attempts, all game types, all games dated strictly before the game (created_at = 6 h after the last puck drop of the previous game date, the LC-2 form).
- s_prev = last season's final shares. 2021-22 has no previous season, so its prior is its own final shares (labelled look-ahead); its rows are shown but not judged.
- M1: K in {500, 2000, 8000} pseudo-attempts per level group. M2: K = 2000 (undiscounted prior), season-to-date counts discounted by 0.5^(gap days / H) at each game date, H in {30, 60}.
- E: the pooled shares of the fold's training rows of the same recording era (era 1 = 2021-22 and 2022-23, era 2 = 2023-24 on). Fold 1 has no era-2 training rows, so on fold 1 era-2 games (the 2023-24 test season) fall back to the pooled training shares, i.e. no level (labelled). **There is no recording-era flag in GameState yet** (`engine/rules.py` only has the 3v3-OT rule era); the season-to-era map lives in `mix_level.ERA_OF_SEASON` for now (flag proposed below).
- O: the season's own final shares (oracle; diagnostic, never selectable).
- L0m for parity: L0 fit on the fold's training rows, times exp(log(s_asof / s_train)) on each cell, renormalised (type given cell unchanged). s_train = the pooled training cell share per level group.
- Parity metrics: ES (strength group ES, EN excluded) high-danger share, pred - actual in pp; mean xG_ref per unblocked attempt over all groups, pred / actual - 1, on the fold's own xG_ref table. Tolerances +/-0.5 pp and +/-0.5%.
- "Smallest max |parity|" within a family is read as the larger of |hd| / 0.5 pp and |xG| / 0.5% (labelled; it was not needed: no construction passed).

### Parity per genuine-prior training season (L0m)

| fold | construction | season | ES high-danger pred / act % | hd pp | xG pred / act - 1 | PP xG | PK xG | pass |
|---|---|---|---|---:|---:|---:|---:|---|
| 1 | none (L0) | 2022-23 | 14.65 / 14.79 | -0.14 | -1.19% | -2.38% | +0.54% | no |
| 1 | M0 | 2022-23 | 14.52 / 14.79 | -0.27 | -2.49% | -4.83% | +0.68% | no |
| 1 | E | 2022-23 | 14.65 / 14.79 | -0.14 | -1.19% | -2.38% | +0.54% | no |
| 1 | M1 K500 | 2022-23 | 14.51 / 14.79 | -0.28 | -0.83% | -1.63% | +0.44% | no |
| 1 | M1 K2000 | 2022-23 | 14.52 / 14.79 | -0.27 | -0.98% | -2.14% | +0.59% | no |
| 1 | M1 K8000 | 2022-23 | 14.54 / 14.79 | -0.24 | -1.27% | -3.06% | +0.65% | no |
| 1 | M2 H30 | 2022-23 | 14.68 / 14.79 | -0.10 | -0.76% | -2.48% | +0.67% | no |
| 1 | M2 H60 | 2022-23 | 14.62 / 14.79 | -0.16 | -0.82% | -2.25% | +0.64% | no |
| 1 | **O (oracle)** | 2022-23 | 14.78 / 14.79 | -0.01 | +0.08% | -0.11% | +0.40% | yes |
| 2 | none (L0) | 2022-23 / 2023-24 | 14.02 / 14.79; 14.00 / 12.75 | -0.77 / +1.25 | -2.04% / +2.30% | | | no |
| 2 | M0 | 2022-23 / 2023-24 | | -0.27 / **+2.01** | -2.33% / **+4.39%** | -4.79% / -0.93% | +0.90% / +5.66% | no |
| 2 | E | 2022-23 / 2023-24 | | -0.14 / -0.00 | -1.17% / +0.49% | -2.50% / +0.65% | +0.61% / -0.02% | no |
| 2 | M1 K500 | 2022-23 / 2023-24 | | -0.28 / +0.13 | -0.85% / +1.30% | -1.76% / -0.22% | +0.54% / +2.88% | no |
| 2 | M1 K2000 | 2022-23 / 2023-24 | | -0.27 / +0.24 | -0.98% / +1.44% | -2.24% / -0.34% | +0.73% / +3.96% | no |
| 2 | M1 K8000 | 2022-23 / 2023-24 | | -0.24 / **+0.50** | -1.25% / +1.81% | -3.12% / -0.54% | +0.84% / +4.97% | no |
| 2 | M2 H30 | 2022-23 / 2023-24 | | -0.10 / +0.33 | -0.77% / +1.34% | -2.58% / -0.28% | +0.83% / +4.63% | no |
| 2 | M2 H60 | 2022-23 / 2023-24 | | -0.16 / +0.29 | -0.83% / +1.36% | -2.36% / -0.29% | +0.80% / +4.32% | no |
| 2 | **O (oracle)** | 2022-23 / 2023-24 | | -0.01 / -0.00 | -0.04% / +0.49% | -0.37% / +0.65% | +0.32% / -0.02% | yes |

Summary over the genuine-prior cells (fold 1: 2022-23; fold 2: 2022-23 and 2023-24):

| construction | all pass | max abs hd pp | max abs xG | max parity / tol |
|---|---|---:|---:|---:|
| M0 | no | 2.01 | 4.39% | 8.77 |
| E | no | 0.14 | **1.19%** | 2.39 |
| M1 K500 | no | 0.28 | 1.30% | 2.59 |
| M1 K2000 | no | 0.27 | 1.44% | 2.88 |
| M1 K8000 | no | 0.50 | 1.81% | 3.62 |
| M2 H30 | no | 0.33 | 1.34% | 2.68 |
| M2 H60 | no | 0.29 | 1.36% | 2.71 |
| O (oracle) | **yes** | 0.01 | 0.49% | 0.99 |
| none (plain L0) | no | 1.25 | 2.30% | 4.60 |

### Selection: **E** (fallback rule)

- No selectable construction passes. The rule then takes the smallest max |xG_ref parity|: E at 1.19%. M1 K500 (1.30%), M2 H30 (1.34%) and M2 H60 (1.36%) lie within 0.2% of it, and E is the simplest of those (M0 < E < M1 < M2). **Selected: E.** The failure is listed, as the LC-2 rule requires: every as-of construction fails xG parity by 0.8-1.8%; only the oracle passes.
- **The oracle passes both lines** (max 0.01 pp, 0.49%). So the residual under the as-of constructions is the level's (lag), not the arm's. With the oracle level, xG parity is within 0.5% in every season. The L0 type and within-group composition do not carry a mix error.
- **Caveat on E, for the PM (labelled, the spec is followed as written):** E's parity is in-sample on every judged cell. Fold 2's era 2 has a single training season (2023-24), so E on 2023-24 *is* that season's own shares, identical to the oracle (-0.00 pp, +0.49%). Era 1 pools 2021-22 and 2022-23, so E on 2022-23 includes the season itself. E's max (1.19%) comes from the within-era-1 spread, not from forecasting. The as-of constructions are genuinely out-of-sample. On the fold-2 test season, E = the 2023-24 final shares, the same value as M0 for 2024-25. So the fold-2 test of E is a test of "last season's shares" applied to a season inside the same era. On fold 1 every training season is era 1, so s_asof = s_train and **E is identical to plain L0 on fold 1** (offset 0 everywhere, including the 2023-24 fallback); the fold-1 E rows above equal the fold-1 none rows.
- Where the as-of constructions miss: 2022-23 under-predicted (-0.8% to -1.3%; the mix moved toward the slot from 2021-22, with PP -1.6% to -3.1%), and 2023-24 over-predicted (+1.3% to +1.8%; the era step). PK on 2023-24 is +2.9% to +5.0% for every as-of construction (PK mix stepped too and the PK group is small, so season-to-date catches up slowly). Short memory helps: K500 and H30 track best.

Next: fit L0m, L1m and L3m (+ seed 2) with level E.

## 1. Build and fit (step 2)

New versioned files:

- `src/nhl_sim/shot_attribute/models_m.py` (the levelled arms);
- `scripts/train_shot_attribute_v2.py`;
- `scripts/run_shot_attribute_g3_v2.py` (written, not run);
- `tests/test_shot_attribute_mix_level.py` (4 synthetic tests).

Changes to existing files:

- `scripts/grade_shot_attribute.py` gained `--round r2`. The r1 path is unchanged and is still the default.
- `lookup.attr_table` gained an optional `predict=` callable. The default (None) keeps SL-R1 behaviour. The 139 existing tests pass, including the lookup and engine-parity tests.

Frozen params are in `docs/models/shot_attribute/sl_r2_frozen_params.json`; results are in `results/shot_attribute_r2/` (gitignored).

**How the level enters each arm:** as an offset off = log(s_E / s_train) on the cell, with coefficient 1, in training and in prediction.

- **L0m:** L0 times exp(off), renormalised.
- **L1m:** the offset sits inside the cell softmax. It is fit by an offset-aware multinomial logit with SL-R1's objective. P(type | cell) is SL-R1's model, unlevelled.
  - Check: with a zero offset on fold 1, the fit reproduces SL-R1's sklearn L1 to max |dP| 4.6e-7 (LL -3.2489175 vs -3.2489209).
- **L3m:** LightGBM with init_score = log(training class frequency) + the offset on each class's cell. The class-frequency base is what LightGBM's boost_from_average starts from, and supplying any init_score switches that off. The base is stored as `models/L3m.base.json`.
  - **My first tune pass used init_score = offset only**, so the boosting started from uniform. That gave inner logloss 3.2579 at 82-84 rounds, against SL-R1's 3.2358.
  - I caught it before any fold-2 fit and added the base. No fold-2 number existed when this was fixed.
  - The rerun reproduces SL-R1 exactly: 15 leaves, 800 min-data, 35 rounds, inner logloss 3.235843.

**On fold 1, level E is zero everywhere**, because every fold-1 training season is era 1. So the fold-1 tuning equals SL-R1's tuning, and the fold-1 diagnostic grade equals SL-R1's arms.

**Ratings tuning (explicit L24 rule).** The fold-1 L1m grid reproduces SL-R1's grid to 1e-5 (`results/shot_attribute_r2/ratings_grid_fold1.json`).

- **Selected: w = 0.7, b = 1,000.** LL -3.248917; spread ratios 1.191 / 1.119.
- Unconstrained LL-best cell: w = 1.0, b = 300. LL -3.248847; spread ratios 1.214 / 1.151, out of band.
- In-band cells: (0.5, 1000) and (0.7, 1000).

## 2. Blind grade, fold 2 (selection; 2024-25, 119,924 unblocked attempts, 1,398 games)

The full tables are in `docs/tests/shot_attribute_sl_r2_grade_2026-10-16.md`: per group, month, tier, type, responsiveness with CIs, arena, segments and per team. Every label was scored before `labels_sealed.json` was opened. L0 (no level) and L0o (oracle level) were graded blind alongside, as labelled references that cannot be selected. Bold = fails its gate.

| arm | LL / game vs L0m (SE) | xG overall | ES | PP | PK | ENF | tier fails | type | resp ES for / against | eligible |
|---|---|---|---|---|---|---|---|---|---|---|
| L0m | 0 | +1.97% | +2.63% | -0.54% | +2.86% | +0.39% | none | PASS | **0.00 / -0.03** | no |
| L1m | -0.096 (0.038) | +1.94% | +2.65% | -0.67% | **+3.22%** | -0.57% | none | PASS | **1.69 / 1.37** | no |
| L3m | -0.024 (0.041) | +1.99% | **+3.27%** | -2.33% | +2.53% | **-3.39%** | **PP medium -2.29 / low +2.31; ENF medium +1.61 / low -1.91** | PASS | 1.09 / 0.86 | no |
| L3ms2 | -0.019 (0.041) | +1.97% | **+3.27%** | | | **-3.43%** | **PP / ENF as L3m** | PASS | 1.10 / 0.88 | (noise floor) |
| L0 (ref., no level) | **-0.873 (0.037)** | **+3.91%** | **+5.65%** | | **+7.01%** | | **8 cells, e.g. high +1.68** | PASS | **0.00 / -0.03** | not selectable |
| L0o (ref., oracle level) | +0.075 (0.011) | +0.71% | +0.91% | +0.06% | -0.53% | -0.91% | none | PASS | **0.00 / -0.03** | not selectable |

**Decision rule.**

- Seed floor |L3m - L3ms2| = 0.0054 nats per game.
- Pairwise: L3m vs L1m +0.072 (SE 0.042); L1m vs L0m -0.096 (SE 0.038, z -2.5); L3m vs L0m -0.024 (SE 0.041).
- **No arm passes every bias check AND the responsiveness band, so none is eligible and none is selected.**
  - L0m passes every bias check (every month PASS, max +3.3% in November; ES high tier +0.53 pp) but has no team terms.
  - L3m has the responsiveness but not the bias checks.
- On likelihood, nothing beats L0m. The team shot-quality ratings still add no out-of-sample value: L1m is worse by 2.5 SE and L3m ties.

**The level works.**

- It moves xG_ref from +3.91% to +1.97% and the ES high tier from +1.78 pp to +0.53 pp, and gains 0.87 nats per game.
- The oracle level reaches +0.71% and gains a further 0.075 per game (z 6.9). So E, which on 2024-25 is the 2023-24 shares, recovers 92% of the oracle's gain.
- The remaining +1.3% is the drift continuing within era 2 (ES high-danger share 12.75% -> 12.23%).

**Responsiveness is real in the data.** Actual ES xG per attempt by own-rating quintile is 0.0575 / 0.0578 / 0.0591 / 0.0596 / 0.0605. A flat arm fails it, and L1m's linear rating terms over-shoot it (on fold 2, again).

**Arena** (reported, not gated, D23): the residual slope on the arena factor is -7.8 ft per unit for L0m (jackknife SE 10.1), +0.1 for L1m (6.9) and +6.1 for L3m (7.6). All are indistinguishable from 0.

**Segments** (no gate; L0m and L3m are nearly identical):

- Rebound attempts: predicted 0.068 vs actual 0.117 xG; high tier 13.5% vs 29.5%. This belongs to the rebound stage.
- Rush: 0.084 vs 0.052.
- 3v3 OT: L0m -5.6%, L3m -11.2%.
- Playoffs: +5.5% (L0m) / +5.3% (L3m).
- Regular season: +1.7% / +1.8%.
- Per-team tables are in the grade file.

## 3. Fold 1 (diagnostic; 2023-24 test)

- Level E is zero on fold 1. So L0m = L0, and L1m / L3m reproduce SL-R1's L1 / L3.
- xG overall: L0m +2.57%, L1m +2.59%, L3m +2.35%.
- LL vs L0m: L1m -0.123 (0.039), L3m -0.505 (0.048).
- Responsiveness follows SL-R1's pattern: L1m 1.19 / 1.12, L3m 0.68 / 0.81.
- **The fold-1 diagnostic cannot test level E** (labelled, as the spec anticipated).
- The oracle on fold 1 (2023-24's own shares) gives xG +0.47% and +1.81 nats per game over L0m. That is the size of the 2023-24 era step that E would capture once the era has training rows.

## 4. Diagnosis: L3m under-fits the strength-group mix in-sample

L3m's PP and ENF failures are not drift. On its own fold-2 TRAINING rows (in-sample), L3m's predicted mix is already off:

| group | L3m in-sample xG rel | L3m in-sample tier pp (high / med / low) | L0m in-sample xG rel |
|---|---:|---|---:|
| ES | +0.45% | +0.12 / +0.12 / -0.24 | 0.00% |
| PP | **-2.00%** | -0.55 / **-1.24** / **+1.79** | 0.00% |
| PK | -0.33% | -0.48 / +0.49 / -0.01 | +0.04% |
| ENF | **-3.36%** | -0.52 / +1.31 / -0.79 | -0.07% |

- **Mechanism (my reading).**
  - The booster starts from the pooled class frequency, which is ES-dominated (82% of rows).
  - It stops after 35 rounds at learning rate 0.05 (early stopping on overall log loss over 78 classes). So the group-specific mix is only partly learned.
  - PP rows stay pulled toward the ES mix: too few medium-distance attempts and too many long ones.
  - The same sign shows in SL-R1's L3 (PP -4.73%).
- **ES.** Out of sample, L3m's ES +3.27% is roughly this in-sample +0.45% plus the level residual that L0m also shows on ES (+2.63%). So without the under-fit, ES would sit near the 3% line, not clearly inside it.
- **What this means.** This is a fitting defect of the L3 construction. It is not a reason to add post-hoc corrections. A structural fix needs a new pre-registered arm (proposal in section 7).

## 5. Step 4 (closed loop): NOT RUN

There is no eligible arm, so G3 and the G2 re-check were skipped, as the brief requires.

`scripts/run_shot_attribute_g3_v2.py` is ready but has NOT been run:

- It serves the levelled arm through `attr_table(..., predict=)` with the step-0 level.
- It writes `docs/tests/gates_g3_sl_r2_<arm>_2026-10-16.md` and `gates_g2_sl_r2_<arm>_...`.

To resume for an arm X once it is eligible:

1. Measure a 3-minute slice first.
2. Run `.venv/Scripts/python.exe scripts/run_shot_attribute_g3_v2.py sim --arm X --seed0 0 --nseeds 200`.
3. Then run `... grade --arm X`.

## 6. Interpretation choices (labelled)

1. The ES parity metric uses strength group ES (EN excluded). xG parity is over all unblocked attempts.
2. "Smallest max |parity|" within a family = max(|hd| / 0.5 pp, |xG| / 0.5%). It was not used, since nothing passed.
3. L0m is levelled at prediction only. It is a saturated table fit without the offset, so its baseline is s_train by construction. L1m and L3m carry the offset in training too.
4. L3m init_score = log training class frequency + offset. This restores LightGBM's default start (section 1).
5. L3m keeps SL-R1's L3 feature list, including the arena factor. The spec says "L3 + level", and D23 dropped only the venue arm and its gate.
6. The E level needs a recording-era flag, which is not in GameState yet. For now the map lives only in `mix_level.ERA_OF_SEASON`.
7. L0 and L0o were graded blind as non-selectable references, so the level's value and the oracle ceiling are on the same scale (L29).

## 7. Proposed text for PM-owned docs (not edited)

**LEARNINGS candidate L32:** *A gradient-boosted multiclass model that starts from the pooled class frequency and stops early under-fits the subgroups. The SL-R1 / SL-R2 L3 (78 classes, 35 rounds at lr 0.05) was off in-sample on PP (-2.0% xG, low tier +1.8 pp) and EN-for (-3.4%), because its rows were pulled toward the ES-dominated pooled mix. For the sim: when a booster refines a stratified baseline, start it from that baseline (init_score = log of the stratum frequency), and check in-sample calibration by stratum before reading any out-of-sample bias.*

**Recommendations for the PM** (SL-R3; needs pre-registration; not run):

1. **New arm L3b:** LightGBM with init_score = log L0m (group x period type, levelled). The trees then model only the team, score and clock deviations. Optionally add L1b = L0m + the rating terms only (no score or b2b terms), as a minimal responsive arm.
2. **Level E:** keep it or revisit it. E's parity was in-sample, and its 2024-25 residual is +1.3% xG against the oracle's +0.7%.
3. **Responsiveness gate:** rule on whether a team-blind arm's 0.00 responsiveness should keep the stage closed. L0m is the only arm that passes every bias check.
4. **Era flag:** add a recording-era flag to GameState if E stays.
