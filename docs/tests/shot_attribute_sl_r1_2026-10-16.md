# SL-R1: shot location x type (cascade stage 4), Lane A, 2026-10-16

- Spec (binding): `docs/models/shot_attribute/experiments.md` SL-R1 (b024504). Brief: `docs/briefs/lane_A_shot_attribute_r1_2026-10-16.md`.
- Step-0 script: `scripts/diag_shot_attribute_step0.py` (training seasons 2021-22..2023-24 only; full tables in `results/shot_attribute_r1/step0_tables.md`, gitignored).

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| lane start | 10:11:21 | |
| step 0 audit | 10:14:40 | 10:14:48 |

## Step 0: data audit (committed before any arm is fitted)

### 0.1 Blocked-shot coordinates: block point, not shot origin

Distance from the goal-line centre (89, 0) in the shooting team's frame, training seasons, penalty shots and shootout excluded:

| kind | n | mean ft | p25 | median | p75 | share < 20 ft | share > 45 ft |
|---|---:|---:|---:|---:|---:|---:|---:|
| BLOCK | 128,048 | 25.9 | 15.2 | 23.0 | 34.0 | 0.406 | 0.093 |
| MISS | 105,235 | 34.8 | 18.0 | 32.5 | 49.2 | 0.281 | 0.306 |
| SOG (incl. goals) | 260,824 | 35.5 | 16.1 | 31.9 | 48.0 | 0.308 | 0.289 |

By shooter position (player_box):

| shooter | BLOCK median | MISS median | SOG median | BLOCK share > 45 ft | MISS share > 45 ft |
|---|---:|---:|---:|---:|---:|
| defencemen | 26.0 | 53.1 | 51.2 | 0.153 | 0.693 |
| forwards | 21.3 | 25.5 | 25.5 | 0.049 | 0.143 |

- Defencemen's unblocked attempts come from the point (median 51-53 ft, 64-69% beyond 45 ft). Their blocked attempts sit at a median of 26 ft, only 15% beyond 45 ft. A shot's origin does not depend on whether it is later blocked by 25 ft. So the block coordinate is the **block point** (where the blocker stood), not the shot origin. The same split holds in every strength state (5v5 BLOCK median 23.3 vs MISS 33.0 / SOG 32.6; PP 21.0 vs 30.4 / 29.4) and every season.
- Blocks by a teammate ("teammate-blocked", 3,620) sit closest of all (median 12.6 ft for forward blockers), which also fits block-point recording.
- The blocker-vs-shooter recorded position check: **NOT AVAILABLE**. Shift charts carry ids and times, no coordinates, and the pbp records one coordinate pair per block.
- **shotType on blocks: recorded on 0.00% of 128,048 blocks** (every season). On SHOT and MISS it is 100%; on GOAL 99.76-99.97%.

### 0.2 Shot-type vocabulary by season (unblocked attempts, % of attempts)

| label | 2021-22 | 2022-23 | 2023-24 | max shift pp | flag |
|---|---:|---:|---:|---:|---|
| wrist | 55.98 | 52.96 | 54.52 | 3.02 | DRIFT (> 2 pp) |
| snap | 12.78 | 15.37 | 14.11 | 2.59 | DRIFT (> 2 pp) |
| slap | 13.52 | 12.11 | 11.75 | 1.41 | |
| backhand | 7.40 | 7.46 | 7.15 | 0.32 | |
| tip-in | 6.92 | 8.52 | 8.81 | 1.60 | |
| deflected | 2.58 | 1.99 | 2.02 | 0.58 | |
| wrap-around | 0.83 | 0.86 | 0.81 | 0.05 | |
| poke | 0 | 0.38 | 0.37 | 0.38 | DRIFT (appears 2022-23) |
| bat | 0 | 0.26 | 0.38 | 0.26 | DRIFT (appears 2022-23) |
| between-legs | 0 | 0.06 | 0.07 | 0.06 | DRIFT (appears 2022-23) |
| cradle | 0 | 0.006 | 0.007 | 0.006 | DRIFT (appears 2022-23) |
| (missing) | 0.002 | 0.018 | 0.015 | 0.02 | |

After the pre-registered six-class collapse (missing type goes to "other", a labelled choice):

| class | 2021-22 | 2022-23 | 2023-24 | max shift pp |
|---|---:|---:|---:|---:|
| wrist + snap | 68.76 | 68.33 | 68.62 | 0.42 |
| slap | 13.52 | 12.11 | 11.75 | 1.41 |
| backhand | 7.40 | 7.46 | 7.15 | 0.32 |
| tip-in + deflected | 9.49 | 10.51 | 10.83 | 1.02 |
| wrap-around | 0.83 | 0.86 | 0.81 | 0.05 |
| other | 0.002 | 0.72 | 0.84 | 0.72 |

- The wrist vs snap drift (3.0 / 2.6 pp) is absorbed by the collapse, as the spec anticipated. Tip-in vs deflected (1.6 / 0.6 pp, opposite signs) is absorbed too.
- **Reported, not absorbed:** four labels (poke, bat, between-legs, cradle) appear from 2022-23, so "other" moves from 0.002% to 0.72-0.84%. That is a recording-vocabulary change of 0.7 pp in the smallest class, below the 1.5 pp type-share line. The collapse is NOT changed after the audit.
- Slap falls 1.8 pp over the three seasons (13.5 to 11.75). It is under the 2 pp flag but trends (a pooled-season frequency would sit above the last season; L27). Listed for the fold-2 type-share check.

### 0.3 Arena distance bias (unblocked attempts, goalies-in states)

Bias = mean over the arena's games of the per-game mean of (recorded - expected) distance; expected = season league mean + shooting team's road for-offset + defending team's road against-offset (labelled construction). SE = SD of per-game means / sqrt(games). Full per-arena table: `results/shot_attribute_r1/step0_tables.md`.

| season | SD of arena bias across arenas (ft) | mean SE (ft) | share of arena-seasons with abs(z) > 2 | max abs bias (ft) |
|---|---:|---:|---|---:|
| 2021-22 | 1.33 | 0.44 (all) | 36% (all seasons) | 2.69 (all) |
| 2022-23 | 0.94 | | | |
| 2023-24 | 0.71 | | | |

- Arena-season correlation of the bias: 0.62 (2021-22 to 2022-23), **0.10** (2022-23 to 2023-24). The dispersion across arenas is real (36% of arena-seasons beyond 2 SE, against 5% by chance) but it shrinks each season and its persistence collapsed in 2023-24. Expect a past-games arena factor to carry little forward signal on fold 2; L2's venue gate (residual slope <= 0.3 of L0's) is judged on that.
- Neutral-site and outdoor venues (1-4 games each) are their own arenas (labelled, as in SA-R1) and UNDERPOWERED.

### 0.4 Coverage and convention

| | BLOCK | MISS | SOG |
|---|---|---|---|
| missing coordinates | 0 | 0 | 0 |
| (0, 0) coordinates | 0 | 0 | 0 |
| out of range (abs x > 100 or abs y > 42.5) | 0 | 0 | 0 |
| sx > 0 | 99.3-99.8% | 99.0-99.3% | 97.0-97.3% |
| behind the goal line (sx > 89) | 0.02-0.06% | 0.6-1.6% | 0.6-1.4% |
| missing shotType | 100% | 0 | 0.00-0.03% |

`sx, sy`: shooting team attacks +x, goal line at x = 89 (L14). Blocks are owned by the shooting team (L15). The behind-the-line share of unblocked attempts rises from 0.6% (2021-22) to 1.5% (2023-24), a small recording drift in the 13th cell (listed).

### 0.5 Blocks rule outcome: **(b)**

Rule (a) needs block coordinates to be shot origins AND shotType on at least 95% of blocks. Both conditions fail: the coordinates are block points (0.1) and type is recorded on 0% of blocks (0.1). So **rule (b) applies, exactly as written**:

- The SL-R1 target is **unblocked attempts (Fenwick) only**: SHOT, MISS, GOAL (penalty shots and shootout attempts excluded, as in stage 3).
- Cascade order: attempt (stage 3) -> blocked? -> (if unblocked) location x type (stage 4) -> SOG / miss -> goal. The block decision moves to the front of stage 5, and its model may not use location.
- Blocked attempts get no location in the sim. In SL-R1's closed loop the sim draws block first at the empirical block rate by strength group, labelled a stub for stage 5.
- xG_ref, the shot-quality ratings, the bias checks and G3 are all per unblocked attempt.

Nothing found in step 0 makes the spec unworkable as written, so the lane continues to step 2.
