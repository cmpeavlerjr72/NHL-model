# SL-R3: baseline-started booster, era flag in GameState, closed loop (cascade stage 4), Lane A3, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R3 (inherits SL-R2 / SL-R1); D24. Brief: `docs/briefs/lane_A3_shot_attribute_r3_2026-10-16.md`.

**Outcome: L3b FAILS the L32 in-sample stratum check, on EN-for, so the spec's stop applies. Nothing on fold 2 was predicted or read, and step 4 (the L3b gate loop) did not run.**

- **Era flag:** in GameState and read by the engine. Every unlevelled path stays bit-identical to HEAD (27cffc0).
- **L0m plumbing loop:** ran at 200 seeds. This is plumbing, not a gate.

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start | 11:22:06 | |
| parity fixture recorded from the pre-change engine (27cffc0), before any engine edit | 11:23:52 | 11:24:00 |
| engine tests after the change (63 engine tests) | 11:24:54 | 11:25:50 |
| L0m lookup + served-vs-trained parity | 11:28:01 | 11:28:03 |
| L0m closed loop, 4 parallel blocks of 50 seeds (measured slice: 25 seeds per block in 182-193 s) | 11:28:09 | 11:35:07 |
| L3b tune (fold 1, 8 cells) | 11:29:02 | 11:31:11 |
| L3b fold-2 fits (L3b, L3bs2) | 11:31:18 | 11:31:46 |
| L32 in-sample check, fold 2: **FAIL** | 11:31:50 | 11:32:09 |
| fold-1 in-sample check (diagnostic, training rows only) | 11:32:25 | 11:32:52 |
| G3 + G2 grade of the L0m loop | 11:35:16 | 11:35:24 |
| full test suite: 162 passed, 1 xfailed | 11:35:51 | 11:37:49 |

The measured slice projected about 7 minutes for 200 seeds, well under 15, so no box request was filed.

## 1. Era flag (step 1)

**Code changes:**
- `engine/rules.py`: `RECORDING_ERA_BOUNDARY = 20232024` and `recording_era(season)`, which returns 1 before 2023-24 and 2 from then on. The boundary is fixed per D24, not fitted.
- `engine/state.py`: `GameState(..., season=None)` sets `rec_era` per sim. It is None unless seasons are passed.
- `engine/sim.py`: `simulate(..., seasons=None)`. There is a new levelled stage-4 path, used when `attr` holds `pdf` + `era_mult`:
  - the lookup serves the arm's **unlevelled** joint probabilities;
  - the engine multiplies them by `era_mult[GameState.rec_era, rating group, class]`, where era_mult = exp(log(s_E[era] / s_train)) on the class's cell;
  - it then renormalises and draws.
  - This is exact for L0m and for an init_score booster, because softmax(raw + log L0 + off) is the unlevelled softmax times exp(off), renormalised.
- `mix_level.ERA_OF_SEASON` is now derived from `recording_era`, so there is a single definition.
- `lookup.attr_table(..., as_pdf=False)`: the default is unchanged.

**Parity: `tests/engine/test_sim_era_flag.py`, 20 tests, all pass.**
- The fixture `tests/fixtures/sim_era_flag_parity.json` was recorded from the unedited engine at 27cffc0. Seven cases cover the stage-4 option off (stub, attempts, T2, real incumbent) and the SL-R1 unlevelled cdf path (synthetic, T2, real). Each is run with and without `seasons=`, and all are sha256-identical to HEAD.
- With a unit era_mult and pdf = the increments of a float64 cdf, the levelled path reproduces the cdf path bit for bit.
- The engine reads the era from GameState: a multiplier on era 1 moves only the era-1 games, and an all-era-2 run equals the unit run exactly.
- A missing `seasons=` raises an error.
- The full suite passes: 162 passed, 1 xfailed.

**Served vs trained check, L0m** (`results/shot_attribute_r3/lookup_parity_L0m.json`):
- The lookup pdf x era_mult[era 2], renormalised, against `predict_arm_m("L0m")` with the E_f2 offset, on all 116,716 fold-2 ES / PP / PK rows: max |dP| = 4.1e-9.
- era_mult[2] against the step-0 parquet E_f2 level: max relative difference 0.

## 2. L0m closed loop: PLUMBING, not a gate (step 2)

**Setup:**
- `scripts/run_shot_attribute_g3_v3.py`.
- Stage 1 is H3''-LC2 + T2; stage 3 is A3g-c.
- Block-first stub (2023-24 block share by group: ES 0.2876, PP 0.2677, PK 0.1164) and the xG_ref goal stub.
- Era 2 comes from GameState; 1,398 games x 200 seeds.
- Reports: `docs/tests/gates_g3_sl_r3_L0m_2026-10-16.md` and `docs/tests/gates_g2_sl_r3_L0m_2026-10-16.md`.

**G3 (overall; regular season / playoffs in the report):**

| state | n actual | xG/att sim | actual | rel | tiers (high / med / low pp) |
|---|---:|---:|---:|---:|---|
| 5v5 | 95,924 | 0.0601 | 0.0584 | +2.92% PASS | +0.52 / +0.04 / -0.56 PASS |
| PP | 15,819 | 0.1004 | 0.1009 | -0.52% PASS | RS: +0.29 / -1.02 / +0.73 PASS |
| PK | 2,602 | 0.0702 | 0.0683 | +2.83% PASS | RS: +1.07 / **-1.63** / +0.56 |
| 4v4 | 1,242 | 0.0616 | 0.0693 | **-11.1%** | **-1.41 / -14.5 / +15.9** |
| 3v3 | 1,129 | 0.0824 | 0.0872 | **-5.6%** | **+2.33 / -10.4 / +8.06** |
| all reachable | 116,716 | 0.0659 | 0.0648 | +1.76% PASS | +0.52 / -0.39 / -0.13 PASS |

- **Decomposition, overall:** sim minus actual is +0.0011. State visits contribute -0.0001 and the attribute mix +0.0012. Verdict: **CLEAN** (regular season CLEAN). Playoffs **FAIL**: 5v5 +7.0% (n 6,165), i.e. the offline playoff segment (+5.5% in SL-R2) carried into the loop.
- **4v4 and 3v3 fail by construction.** The pre-registered strength group ES pools 5v5 + 4v4 + 3v3, and 5v5 is 96% of it. So the sim serves the 5v5 mix at 4v4 / 3v3, while the actual 4v4 / 3v3 mix is far more medium-distance (54% / 60% vs 39%). Every arm in SL-R1..R3 shares this grouping. It needs a spec change (split 4v4 / 3v3 out of ES), not a tuning.
- **Responsiveness:** 0.01 / -0.02, FAIL. That is expected: L0m has no team terms.
- **Per team** (UNDERPOWERED): corr 0.16; 20 / 32 teams within 3%.
- **Goals:** sim 5.61 per game against 5.54 actual in reachable states.

**G2 re-check (vs INV-36, the same stage 1 + 3 under the old goal stub):**
- **5v5, PP, PK and team-game mean are all PASS and CLEAN, unchanged.**
- **Regular-season 4v4 per 60 moves from +2.82% PASS to +3.08% FAIL** (tolerance 3%). Its decomposition goes from CLEAN to FAIL (1.50 vs tolerance 1.46). It is PASS at 100 seeds, and |200 - 100| = 0.098. The overall 4v4 stays PASS (+2.80%).
  - This is a marginal flip of a cell that was already at the edge. The new goal stub changes score paths and hence 4v4 visits. It is not a strict "every non-3v3 cell still PASS".
- 3v3 was FAIL before and is still FAIL (+7.7%, was +5.2%). The playoff PK decomposition FAIL is pre-existing.

## 3. L3b (step 3)

### Tuning (fold 1; E is zero on fold 1; inner split = last 20% of fold-1 training games by date)

- The inner L0 baseline is fit on inner-training rows only (labelled). L0m baseline inner log loss: 3.236166.

| leaves | min data | lr | rounds | inner log loss |
|---:|---:|---:|---:|---:|
| 15 | 200 | 0.05 | 2 | 3.245479 |
| 15 | 200 | 0.02 | 40 | 3.236012 |
| 15 | 800 | 0.05 | 13 | 3.234309 |
| **15** | **800** | **0.02** | **31** | **3.234040** |
| 31 | 200 | 0.05 | 2 | 3.244562 |
| 31 | 200 | 0.02 | 35 | 3.237183 |
| 31 | 800 | 0.05 | 7 | 3.235004 |
| 31 | 800 | 0.02 | 20 | 3.234345 |

- **Selected: 15 leaves, 800 min-data, lr 0.02, 31 rounds.** That is 0.0021 nats per attempt under the L0m start. For reference, SL-R2's L3m reached 3.235843.
- Frozen params: `docs/models/shot_attribute/sl_r3_frozen_params.json`.
- The fold-2 L0 table equals SL-R2's L0m table exactly.
- **L3bs2 (seed 2) is bit-identical to L3b.** The configuration has no stochastic element (no bagging or feature fraction, `deterministic=True`). The seed floor is therefore 0 and carries no information.

### L32 in-sample check (fold-2 training rows): FAIL, so stop

| group | n | L0m xG/att (vs actual) | L3b vs L0m | tiers high / med / low (pp vs L0m) | pass (+/-0.5%) |
|---|---:|---|---:|---|---|
| ES | 295,926 | 0.06222 (+0.00%) | +0.04% | +0.02 / -0.02 / +0.00 | yes |
| PP | 53,097 | 0.09793 (-0.00%) | -0.08% | -0.08 / +0.09 / -0.01 | yes |
| PK | 9,170 | 0.07309 (+0.04%) | +0.42% | +0.05 / +0.21 / -0.27 | yes |
| **ENF** | 5,721 | 0.08245 (-0.07%) | **-0.87%** | -0.37 / +0.06 / +0.31 | **no** |
| ENA | 2,145 | 0.60931 (+0.15%) | +0.03% | +0.18 / +0.05 / -0.23 | yes |

- In-sample log loss per attempt: L0m -3.18405, L3b -3.16691.
- **Fold 1 (diagnostic, training rows only): the same failure.** ENF is -0.58% and PK +0.22%. Everything else is within 0.15%. `results/shot_attribute_r3/fold1/insample.json`.

**Diagnosis** (`results/shot_attribute_r3/enf_diag.txt`, fold-2 training rows):
- The L32 fix worked for what it targeted. PP is now -0.08% in-sample, where SL-R2's L3m was -2.0%. ENF went from -3.36% to -0.87%. ES is +0.04%.
- The remaining ENF shift has a different mechanism: **cross-stratum transfer of the score and clock deviations.**
  - Every EN-for row is late and trailing.
  - In ES, late trailing attempts really are lower quality than the L0m stratum mean: actual is -6.9% (down 2) and -8.7% (down 1) vs L0m. The shared trees learn part of that (-1.3% to -1.5%).
  - Those same score / clock splits are applied to ENF rows, giving -0.9% in both trailing buckets.
  - ENF's actual is flat against its own L0m mean (-0.1% / -0.3%).
  - With 800 minimum rows per leaf and 31 rounds at lr 0.02, the trees do not isolate the 5.7k ENF rows through `grp`.
- So L3b over-generalises the ES score effect into a stratum where it does not hold. It also under-learns the ES effect itself: it captures only 15-22% of the late-trailing gap.

### Not done (spec stop)

- No fold-2 predictions, no blind grade, no bias checks, no responsiveness, no decision, and no L3b closed loop.
- `train_shot_attribute_v3.py pred2` refuses to run while `insample.json` has `pass_all: false`.
- Fold-1 test predictions were not made either.
- The grader has no `--round r3` yet; it would be needed only if a later round reaches grading.

## 4. Interpretation choices (labelled)

1. The inner-split L0 (the tuning baseline) is fit on inner-training rows only, so the validation rows do not feed their own init.
2. The in-sample check is on all five strength groups, as written. No n threshold is stated in the spec, and ENF (5,721) exceeds the bias-check n >= 2,000 anyway.
3. ENF is unreachable in the sim until stage 8 (goalie pull). The spec still gates it, so the stop is applied.
4. G2 4v4 is reported as a marginal FAIL at 200 seeds, not explained away.

## 5. Proposed text for PM-owned docs (not edited)

**LEARNINGS candidate L33:** *Starting a booster from the stratum baseline fixes the mix under-fit, not cross-stratum leakage. SL-R3's L3b (init = log L0m) holds ES / PP in-sample to within 0.1%. But the score and clock deviations it learns from ES (where late trailing attempts are 7-9% lower in xG) also land on EN-for rows, which are all late and trailing, and shift them by -0.9% while their actual is flat. For the sim: when a stratum is defined by the very features the trees split on (EN by score and clock), either interact the deviation features with the stratum or exclude that stratum from the shared trees, and check in-sample calibration per stratum x feature bucket, not only per stratum.*

**Recommendations for the PM** (each needs pre-registration; none was run):
1. **Strength grouping:** split 4v4 and 3v3 out of ES for the location model. The closed loop shows -14.5 pp medium at 4v4 and -10.4 pp at 3v3, from pooling. This applies to every arm.
2. **L3b successor:** one of the following.
   - (a) EN rows use the L0m baseline only: they get no tree deviations, since EN is unreachable until stage 8 anyway.
   - (b) Separate boosters per strength group.
   - (c) Interaction constraints that tie score / clock splits to `grp`.
   - Option (a) is the simplest, and makes the ENF in-sample check trivially exact.
3. **Seed floor:** with a deterministic booster the seed-2 retrain is identical. A meaningful noise floor needs bagging, or a different noise-floor definition (e.g. a game-block bootstrap only).
4. **G2 4v4** sits at the 3% edge. It should be watched once the goal model replaces the stub.

## Files

- Engine and core: `src/nhl_sim/engine/{rules,state,sim}.py`, `src/nhl_sim/shot_attribute/{lookup,mix_level,models_b}.py`.
- Scripts: `scripts/train_shot_attribute_v3.py`, `scripts/run_shot_attribute_g3_v3.py`, `scripts/diag_engine_era_parity_fixture.py`.
- Tests: `tests/engine/test_sim_era_flag.py`, `tests/engine/era_parity_cases.py`, `tests/fixtures/sim_era_flag_parity.json`.
- Params: `docs/models/shot_attribute/sl_r3_frozen_params.json`.
- Gate reports: `docs/tests/gates_g3_sl_r3_L0m_2026-10-16.md`, `docs/tests/gates_g2_sl_r3_L0m_2026-10-16.md`.
- Results (gitignored): `results/shot_attribute_r3/` and `results/sl_r3_g3_L0m/`.
