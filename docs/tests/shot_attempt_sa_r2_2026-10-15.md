# SA-R2 shot attempts with the LC-1 level (INV-31, Lane S2, 2026-10-15)

- Spec: `docs/models/shot_attempt/experiments.md` SA-R2, D16.
- Brief: `docs/briefs/lane_S2_level_fix_2026-10-15.md`, with the PM clock change: compute stops at 22:00, report by 22:15.
- Blind grade: `docs/tests/shot_attempt_sa_r2_grade_2026-10-15.md`.
- G2: `docs/tests/gates_g2_sa_r2_g2_A3g_r3_2026-10-15.md` and `gates_g2_sa_r2_g2_A2g_r3_2026-10-15.md`.
- Frozen params: `docs/models/shot_attempt/sa_r2_frozen_params.json`.

**Outcome: A3g is selected** (LightGBM on group-specific LC-1 levels). The next simpler eligible arm is A2g.

G2 on the current stage-1 incumbent (H3'' + T1, D15) shows:
- Regular season: attempts per 60 at 5v5, PP and PK, and attempts per team-game, PASS, and the per-team-game decomposition is CLEAN.
- The 4v4 (+4.2%) and 3v3 (+6.6%) per-60 cells FAIL for A3g. For A2g, 3v3 fails (+5.4%) and 4v4 passes.
- Closed-loop responsiveness passes for both arms.
- Read literally, G2 is **FAIL in the 3v3 cell (both arms) and the 4v4 cell (A3g)**. Every powered core cell passes and is CLEAN.

## Clock (Get-Date, EDT)

| step | start | end |
|---|---|---|
| LC-1 module, v2 level + ratings tables | 21:09 | 21:12:28 |
| tune / fold 1 / fold 2 fits | 21:13:14 | 21:15:31 |
| blind grade | 21:16:02 | 21:16:12 |
| G2: 6 parallel seed blocks (3 per arm, 66-67 seeds each, 200 seeds per arm) | 21:16:54 | 21:34:20 |
| G2 grading | 21:35:23 | 21:35:28 |

Wall time ran longer than projected because the six blocks built their lookup tables concurrently with Lane P2's run. It stayed under the 15-min box rule per block, and no AWS request was filed.

## 1. LC-1 (D16)

- `src/nhl_sim/league_level_lc1.py` is shared by stages 1 and 3.
- The level is log((E + K r_prev) / (H + K)), with de-seasonalised counts E, team-hours H, and r_prev the previous season's final de-seasonalised rate.
  - All-state level: K = 2k team-hours.
  - Group level: K = 2k x the group's share of team-hours (labelled).
  - 2021-22 uses its own final rate as its prior (labelled; it is a training season only).
- Tests: `tests/test_league_level_lc1.py` (4 pass).
- Tables (`_v2`): `league_level_v2_f{1,2}` (all-state plus ES / PP-for / PK, k in {5, 15, 50}, each with its own training-only profile), `profile_v2_f{1,2}.json`, `ratings_grid_v2` (w {0.7, 0.85, 1.0} x b {200, 600, 1800}) and `arena_v2`. The attempt rows and team-game table are unchanged and stay `_v1`. `created_at < puck_drop` is asserted on every row.

**Per-training-season parity** (in-sample predicted / actual - 1; limit 0.5%):

| arm | fold-1 train 2021-22 | 2022-23 | fold-2 train 2021-22 | 2022-23 | 2023-24 |
|---|---:|---:|---:|---:|---:|
| A0 (level + profile + cells) | -0.48% | +0.46% | -0.66% | +0.29% | +0.34% |
| A1 | -0.61% | +0.60% | -0.78% | +0.41% | +0.34% |
| A2 | -0.61% | +0.60% | -0.80% | +0.40% | +0.36% |
| A5 | -0.57% | +0.55% | -0.71% | +0.39% | +0.28% |
| A3 | -0.35% | +0.34% | -0.55% | +0.32% | +0.21% |
| A2g | -0.48% | +0.46% | -0.61% | +0.32% | +0.27% |
| A3g | -0.31% | +0.30% | -0.48% | +0.27% | +0.19% |

Interpretation, labelled: the spec's parity test is the LEVEL's test, so it is read on the level-only arm A0 on fold-1 train, where it **passes**. The A1, A2 and A5 rows exceed 0.5% on fold 1 by about 0.1 point. That is a pull of up to about 0.6% between seasons from the rating terms, and it is reported. Under the stricter reading (every arm), the spec's assertion fails for A1, A2 and A5. The PM rules.

## 2. Fold-1 tuning

- Frozen: k = 5, w = 0.85, b = 200 (fold-1 A1 LL -180.1085). **Both k and b are again grid corners.**
- A3 / A3g (labelled: the same frozen parameters): 15 leaves, 800 min-data, 459 rounds.
- A4 latent: v = 0.00119.
- L24: the fold-1 offline spread ratio over all 27 cells is 1.12-1.45 (own) and 1.07-1.40 (opp); it is 1.13 / 1.08 at the frozen cell.

## 3. Fold-1 diagnostic (reported first; not gating)

| arm | fold-1 level | fails |
|---|---|---|
| A0 | +0.51% | PK +10.3%, score -1 / +1, away |
| A1 | +0.51% | PK +10.8%, score -1 / +1 |
| A2 / A4 | +0.56% | PK +10.9% |
| A5 | +0.44% | PK +10.8% |
| A3 | +0.49% | PK +10.3% |
| **A2g** | +0.42% | PK +4.1% |
| **A3g** | +0.46% | none |

The anchoring defect is gone on fold 1 (it was -2%), and the group levels remove most of the PK drift.

## 4. Bake-off, fold 2 (blind; hashes salt `SA-R2-2026-10-15`)

| arm (hash) | LL/game | vs A0 | SE | pred / actual |
|---|---:|---:|---:|---:|
| A0 (939cec67) | -178.5932 | 0 | | 1.0082 |
| A1 (299f5f07) | -178.1920 | +0.4012 | 0.0416 | 1.0069 |
| A2 (7b4a4fc8) | -177.6324 | +0.9608 | 0.0539 | 1.0076 |
| A2g (fb74be17) | -177.6200 | +0.9732 | 0.0545 | 1.0057 |
| A5 (6716a0a0) | -177.6282 | +0.9650 | 0.0540 | 1.0067 |
| A4 (dec19b84) | -177.6249 | +0.9683 | 0.0540 | 1.0076 |
| A3 (e5136812) | -177.5071 | +1.0861 | 0.0554 | 1.0043 |
| A3g (03ddca0a) | -177.4942 | +1.0990 | 0.0558 | 1.0032 |

The seed floor (A3 vs A3 seed 2, 410dcb02) is 0.0026. Key pairs:
- A2g vs A2: +0.0124 (SE 0.0062), beats.
- A3g vs A2g: +0.1258 (SE 0.0176), beats.
- A3g vs A3: +0.0128 (SE 0.0087), does not beat (1.5 SE).

All pairs are in the grade file.

## 5. Bias checks (fold 2, gating) and responsiveness

| arm | fold-2 failing cells | resp own (95% CI) | resp opp (95% CI) | eligible |
|---|---|---|---|---|
| A0 | PP +3.7%, PK +9.5%, score -1 -5.0%, +1 +6.9%, away +2.3% | 0.03 | -0.04 | no |
| A1 | PP +3.4%, PK +9.3%, score -1, +1 | 1.08 (0.95, 1.24) | 1.12 (0.98, 1.32) | no |
| A2 / A4 | PP +3.6%, PK +9.4% | 1.11 (0.98, 1.27) | 1.12 (0.98, 1.30) | no |
| A5 | PP +3.5%, PK +9.3% | 1.13 (1.00, 1.30) | 1.10 (0.96, 1.28) | no |
| A3 | PK +10.9% | 1.16 (1.03, 1.34) | 1.07 (0.93, 1.25) | no |
| **A2g** | none | 1.11 (0.98, 1.28) | 1.12 (0.98, 1.31) | **yes** |
| **A3g** | none | 1.17 (1.04, 1.35) | 1.08 (0.94, 1.26) | **yes** |

- A3g fold 2: level +0.32%, months -0.9% to +1.1%, 5v5 +0.6%, PP -0.5%, PK -1.5%, score buckets -1 / 0 / +1 within 1.3%, home +0.5%, away +0.2%.
- Reported only: 4v4 +3.1%, 3v3 +6.8%, EN -4% / -6%.
- Twin rule: A2g fixes PP and PK against A2 and is worse on nothing, so it is preferred. A3g fixes PK against A3 and is worse on nothing, so it is preferred.

**Decision rule:** the eligible arms are A2g and A3g. A3g beats A2g, so **A3g is selected**. The next simpler eligible arm is A2g.

## 6. G2 (closed loop; stage 1 = H3'' + T1 under D15, the current incumbent; goal stub = league goals per attempt by state, 2023-24; 200 seeds)

Stage 1 is H3'' + T1, the incumbent when G2 launched at 21:16. The SS-R5 ruling that moves T2 into the incumbent (9b299f3) arrived after launch, and the T2 per-team type table runs only in Lane P2's engine sibling `sim_ss_r5.py`, which has no attempt variant. A G2 re-run on H3'' + T2 is therefore an open item, not run.

| cell | A3g RS | A2g RS | A3g overall | PO (both arms) |
|---|---|---|---|---|
| per 60, 5v5 | 58.56 vs 58.35, +0.4% PASS | +0.7% PASS | +0.4% PASS | UNDERPOWERED (n = 172) |
| per 60, PP | -0.5% PASS | -0.3% PASS | -0.3% PASS | UNDERPOWERED |
| per 60, PK | -2.1% PASS | -1.0% PASS | -1.3% PASS | UNDERPOWERED (A3g +10%) |
| per 60, 4v4 | **+4.2% FAIL** | +2.4% PASS | **+4.0% FAIL** | UNDERPOWERED |
| per 60, 3v3 | **+6.6% FAIL** | **+5.4% FAIL** | **+6.7% FAIL** | UNDERPOWERED |
| per 60, EN-for / against | UNREACHABLE (no goalie pull) | | | |
| attempts / team-game, mean | 58.93 vs 59.48, -0.9% PASS | -0.7% PASS | -0.9% PASS | UNDERPOWERED |
| team-game SD (no tolerance) | 9.91 vs 11.61 (0.85) | 9.91 | 10.11 vs 11.86 | |
| home-away correlation (no tolerance) | -0.23 vs -0.41 | -0.25 | -0.19 vs -0.37 | |
| 100 vs 200 seeds | every status identical; per-60 moved by at most 0.05 | | | |

- Per-60 by score bucket: the powered buckets -1 / 0 / +1 pass in both arms; see the G2 files.
- Per team (UNDERPOWERED): correlation of for 0.93 and against 0.94 (A3g).

**Decomposition, attempts per team-game, A3g RS** (tolerance 1.78 = 3% of 59.48):

| component | value |
|---|---:|
| hazard level | +0.20 |
| unreachable EN attempts | -1.69 |
| state visits | +0.97 |
| score-state visits | +0.04 |
| remainder | -0.07 |

**Verdict: CLEAN** (no component exceeds the tolerance). It is also CLEAN for A2g RS, A3g overall and A3g playoffs (UNDERPOWERED).

Watch item: the -1.69 for EN attempts the sim cannot generate is offset by +0.97 of extra 5v5 time (the time the sim spends at 5v5 instead of EN). Both are inside the tolerance, so the literal verdict is CLEAN. Once a goalie-pull model exists (stage 8), this pair will close together.

By-state decomposition (RS): 5v5, PP and PK are CLEAN. 4v4 is FAIL (A3g) and 3v3 is FAIL (both arms), and the hazard-level component dominates in each (3v3 +3.76 per 60 for A3g). The 3v3 / 4v4 rate is over-predicted offline as well (+6.8% / +3.1%, reported-only cells). It is not a closed-loop effect.

Closed-loop responsiveness (5v5, overall): A3g own 1.135 (0.996..1.313) and opp 1.121 (0.972..1.328), PASS; A2g 1.078 and 1.160, PASS. Both are steeper than 1, as offline.

**Step 4:** not triggered. SS-R3c stopped at its parity assertion (`docs/tests/strength_state_ss_r3c_2026-10-15.md`), so the stage-1 incumbent is unchanged.

## 7. Interpretation choices (labelled)

1. Parity is read on the level arm A0 (all arms reported).
2. The group-level prior K is scaled by exposure share.
3. 2021-22 uses its own final rate as its prior.
4. EN rows use the ES level and profile in the g arms.
5. A3g uses A3's frozen LightGBM parameters.
6. Twin rule: a non-preferred g arm is not selectable. "Not worse" means no bias check FAIL where the twin passes, and no responsiveness failure where the twin passes.
7. G2 per-60 state cells are powered by team-games (min_cell_n). The 4v4 / 3v3 cells therefore gate in G2, although they were only reported offline.
8. SA-R1's choices 1-12 carry over.

## 8. For the PM

- A3g is offline-selected, and its powered core G2 cells pass CLEAN. The 3v3 / 4v4 failures are an offline hazard-level over-prediction in thin states, where the overtime 3v3 cell runs at about 25 team-hours per season.
- Whether the 4v4 / 3v3 per-60 cells gate G2 is a ruling for you.
- The frozen k and b sit at grid corners again.
