# EG-R1 part A (INV-66), Lane H8a: goalie pull process. PARTIAL: stopped at step 2, before any fold-2 read

Lane H8a (Opus), 2026-10-21. Spec: `docs/models/end_game/experiments.md` EG-R1 part A plus the Lane H8a execution note.
**Nothing from 2024-25 was read.** `src/nhl_sim/engine/sim.py` is untouched; no engine step has started.

## Why the lane stopped

The spec's selection rule needs an arm that passes every bias check, and one check cannot be passed by any stochastic arm
under the offline method the checks require. **Pulled time per game within 10%** is biased by construction by about
**+10 to +11%**, and the **trailing-by-1 pulled share** by about **-2.6 pp** (tolerance 3 pp). The proof uses
training seasons only:

- **In-sample calibration.** P0 fitted on a season reproduces that season's per-second row hazard exactly (it is the
  empirical hazard). Run through the offline simulator on the same season's actual paths, it gives:

| season (in-sample) | actual engine-rule pulled s/game | P0 in-sample | ratio | trail1 share actual / P0 | medians t1 / t2 / t3 actual -> P0 | re-pull actual / P0 |
|---|---|---|---|---|---|---|
| 2022-23 | 63.93 | 70.58 | **1.104** | 0.593 / 0.567 (-2.7 pp) | 112 / 170 / 249 -> 113 / 168 / 249 | 0.198 / 0.197 |
| 2023-24 | 67.58 | 75.10 | **1.111** | 0.598 / 0.572 (-2.6 pp) | 113 / 175.5 / 272.5 -> 114 / 175 / 270 | 0.218 / 0.205 |

  So the empirical process itself fails the pulled-time check and nearly uses up the trailing-by-1 tolerance. The
  first-pull medians and the re-pull share are unbiased in-sample.
- **Mechanism.** On the actual paths the only returns are the actual goals, and goals into an empty net happen when the
  REAL goalie is out. A simulated pull in a team-game or second where the real team kept its goalie in sees only the
  ordinary goal rate against, so it runs longer. A pull the model misses where the real team pulled loses an early
  return it would have had. Timing noise alone does not do this: replaying the actual episode starts shifted by
  N(0, sigma) gives 1.000 / 0.998 / 0.999 / 1.000 / 1.009 of actual for sigma 0 / 5 / 10 / 20 / 30 s (2023-24). The
  bias comes from which team-games pull, not from when. Episode length depends on the EN cascade (stage 3-6 at the EN
  states), which the offline method cannot supply. Only the closed loop can.
- Under the literal rule both arms fail on fold 1 (D13 guard), and fold 2 would fail them again for the same reason.
  Neither P0 nor P1 can be selected. Reading fold 2 now would spend the holdout on a rule that cannot be passed, so the
  lane stops and reports, per the brief's "if it cannot be run as written, stop and report".

## What was done

**Step 1 (commit 3da15f8, before any fit).** Pull rows per season (`scripts/build_end_game_pull_rows_v1.py`,
`src/nhl_sim/end_game/pull.py`; the audit's detection reused verbatim). Step-0 table:
`docs/tests/end_game_eg_r1_pull_step0_2026-10-21.md`.

| season | engine-rule pulled s/game | literal shift-chart non-DP (window) | bridged | first pull median t1 / t2 / t3+ |
|---|---|---|---|---|
| 2021-22 | 65.5 | 58.6 | 7.3 | 108 / 178 / 250 |
| 2022-23 | 63.9 | 56.1 | 8.6 | 112 / 170 / 249 |
| 2023-24 | 67.6 | 60.0 | 7.9 | 113 / 175.5 / 272.5 |

There is no trend, so a level is not indicated (L27). The re-pull share is 0.222 / 0.198 / 0.218, matching audit 1e.

**Step 2, fits and fold-1 D13 grade (2021-22 + 2022-23 -> 2023-24).** Code: `scripts/train_end_game_pull_v1.py`;
models in `data/processed/end_game/models_v1/`.

- P1 coefficients (fold 2 fit, 1,633,405 rows, 2,707 pulls; Newton, 13 iterations): pk -1.572, pp -0.089,
  pulled_before -0.384, home +0.023. Fold 1 fit: -1.583 / -0.071 / -0.433 / +0.013.
- Fold-1 LL per team-game (1,236 team-games with rows): P1 -4.006, P0 -5.232. **P1 - P0 = +1.226 (SE 0.088, 13.9
  SE).** P0's unsmoothed 1-s hazard puts zero mass on seconds with no training pull. The noise floor is 0 (the
  logistic is deterministic).

| fold-1 check (2023-24) | actual | P0 | P1 | tolerance |
|---|---|---|---|---|
| pulled s/game (engine rule) | 67.58 | 74.70 (+10.5%) FAIL | 76.11 (+12.6%) FAIL | 10% |
| first median trail1 | 113.0 | 111 PASS | 112 PASS | 10 s |
| first median trail2 | 175.5 | 176 PASS | 176 PASS | 10 s |
| first median trail3+ (n 80, UNDERPOWERED) | 272.5 | 250 FAIL | 247 FAIL | 10 s |
| trailing-by-1 pulled share | 0.598 | 0.566 FAIL | 0.569 PASS | 3 pp |
| re-pull share | 0.218 | 0.211 PASS | 0.198 PASS | 5 pp |

Against the in-sample calibration (P0 fitted on 2023-24 itself: 75.10), the out-of-sample arms are at 0.995 (P0) and
1.013 (P1). P1 in-sample is at 1.148 on both seasons, about 4 pp above P0 in-sample. The likely cause is its constant
`pulled_before` term: real re-pulls bunch at short lags (median 14 s), and P1 spreads them over the remaining time.
This is reported only; P1's form is pre-registered.

Reproduce: `diag_end_game_pull_offline_bias_v1.py --season 20222023|20232024` (calibration and jitter, about 1 min);
`train_end_game_pull_v1.py fit --fold 1|2`, `grade --fold 1`.

## Proposed re-spec (for the PM; not applied)

1. Judge pulled time per game and the trailing-by-1 share in the closed loop, where returns come from the EN cascade,
   against the same 10% / 3 pp bands. Offline, report them only relative to the in-sample empirical-hazard calibration
   (ratio of arm to P0 in-sample, both on the judged season).
2. Keep the offline gates that are unbiased in-sample: first-pull medians by deficit (trail3+ is UNDERPOWERED,
   n of about 80 per season) and re-pull share. Keep the LL rule (> 2 SE).
3. Optional: since P1's re-pull term misfits the lag shape, a P1' with a lag-since-return term (bins) could be
   pre-registered. This is not needed for selection.

Under (1)-(2), fold 1 would read: P1 passes trail1 / trail2 medians and re-pull; trail3+ fails by 25.5 s on n = 80
(UNDERPOWERED).

## Not done

- Fold-2 blind grade and selection: resume with `train_end_game_pull_v1.py grade --fold 2` (needs
  `build_end_game_pull_rows_v1.py build --seasons 20242025`), then `select`, under whatever rule the PM sets.
- Step 3 (EN table inventory and as-of M1 K500 EN levels), step 4 (engine wiring), step 5 (200-seed loop), step 6
  results. Step 3 does not depend on the ruling.
- The `engine_pull` commit marker was not made. `sim.py` is untouched, so the PM can release `sim.py` to Lane H8b now.

## Other findings for the ruling

- **The engine has no stage-1 delayed-penalty state** (penalties apply at the second they are drawn; SS-R2 / L20).
  The spec's delayed-penalty rider can be wired only as a flag that stage 1 never sets. DP pulled time (11-12 s per
  game) and DP EN-for goals (about 24 per season) would be absent from the loop. Listed in the execution note.
- **Bridged time.** The return rule (back only at a tying goal or goal against) makes engine-rule pulled time about
  12% longer than the literal shift-chart goalie-out time (7-9 s per game; goalies return for a stoppage and leave
  again). EN exposure in the engine would be about 12% longer than real goalie-out time unless the EN rates are read
  per engine-rule second.

Clock: start 13:32; step 1 13:41-13:43 (builds 13-29 s per season); fits 13:46-13:47 (1 s each); fold-1 grade
13:47 (35 s); diagnostics 13:48-13:50. No step came near 15 minutes, so no box request was filed.
