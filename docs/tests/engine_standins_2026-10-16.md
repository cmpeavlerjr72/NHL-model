# Lane E: D32 engine stand-ins (block B0, stage-4 L0s) and the plumbing closed loop (2026-10-16)

> **STAND-IN / PLUMBING. NOTHING IN THIS REPORT GATES.** Both stand-ins are flat baselines and cannot be adopted (D24, D32). They exist so stage 5 can be built and tested in the closed loop. No offline fit may use stand-in sim output.

Brief: `docs/briefs/lane_E_engine_standins_2026-10-16.md`. Rules: `CLAUDE.md`, `docs/ops/worker_rules_2026-10-16.md`. Decisions: D23, D24, D26-D32.

## Clock (wall clock, -04:00)

| step | start | end |
|:--|:--|:--|
| lane start | 12:15:16 | |
| flag-off parity fixture recorded with the pre-change engine (3ce7112) | 12:17:44 | 12:17:57 |
| engine tests (tests/engine, 80) | 12:20:20 | 12:21:40 |
| closed loop: 4 parallel blocks of 50 seeds, 2 threads each | 12:22:55 | 12:30:35 |
| measured slice: 25 seeds per block in 250-258 s, so about 8.5 min projected for 200 seeds (under 15 min, so no box request) | 12:22:57 | 12:27:14 |
| grading (G2 + G3 + per 60) | 12:30:49 | 12:30:55 |
| full test suite (183 passed, 1 xfailed) | 12:31:09 | 12:33:28 |

## 1. Engine (`src/nhl_sim/engine/sim.py`; one engine, two default-off flags inside `tables["attr"]`)

- **Block B0 stand-in** (on when `attr["p_block_game"]` is present). It is a table of shape (G, 3, 2), indexed by game, rating group (ES / PP / PK of the team-view state) and period type (`t >= 3600`, which is the attempt tables' `ptype`).
  - Each value is sigmoid(B0 coef[group x period type] + logit(s_M1K500[game, level group]) - logit(s_train[level group])). These are the SB-R1 fold-2 B0 fit and the M1 K500 as-of level (D27).
  - 4v4 and 3v3 use the ES group, the same as in B0's training rows.
  - With the flag off, the empirical `p_block[st]` stub is unchanged.
- **Stage-4 L0s stand-in** (on when `attr["state_pdf"]` is present). It is the unlevelled SL-R4 L0s table, shape (7 states, 2 period types, 78), indexed [team-view state, period type].
  - The level E is applied from `GameState.rec_era` through `era_mult`, using the same code as the SL-R3 levelled path. `era_mult` is required.
  - EN rows 5 / 6 hold the baseline (L33). They become reachable at stage 8.
- **Shared served-value functions.** `block_prob` and `class_cdf` are the functions the draw itself calls, so the tests check the values the engine actually serves.
- **Labels are required.** Each flag must carry a label in `attr["stand_in"]`, otherwise the engine raises `ValueError`. When labels are present, the output carries `stand_in`, an array of "component: label" strings.
- **Runner checks.** The runner writes `stand_in = 1` in every part file and copies the marker into the meta / run_meta. The grader refuses part files without it. The STAND-IN banner is in both gate report headers.
- **Table builders and parity helpers:** `src/nhl_sim/engine/standins.py` (labels `BLOCK_LABEL` / `ATTR_LABEL`).

## 2. Tests (`tests/engine/test_sim_standins.py`; 17 tests, all pass)

**Flag off, bit-identical to HEAD (3ce7112).** Every output array matches by sha256 on 10 cases. The fixture `tests/fixtures/sim_standin_flag_parity.json` was recorded before the edit by `scripts/diag_engine_standin_parity_fixture.py`. The cases are:
- the 7 SL-R3 era cases, including the real incumbent and the SL-R1 cdf path;
- 3 new cases on the levelled pdf path, which earlier fixtures did not cover.

The existing attr / era / T2 parity tests also still pass.

**Flag on, served values match offline within 1e-6** (real tables):

| stand-in | rows checked | max abs difference |
|:--|--:|--:|
| B0 block probability | 162,300 goalie-in fold-2 rows | 1.49e-8 |
| L0s class probabilities | 119,924 unblocked fold-2 rows, all 7 states incl. 2,316 EN-for and 892 EN-against | 1.21e-8 |

The residual is float32 storage of the offline predictions.

**Flag on, wiring.**
- A B0 table that is constant over games and period type reproduces the empirical-stub run bit for bit.
- An L0s table whose 4v4 / 3v3 rows equal 5v5 reproduces the levelled pdf path bit for bit.

**Schema.**
- The `stand_in` marker is present and names both components.
- An unlabelled stand-in is refused, for each component.
- L0s without a level is refused.
- Flag-off output has no marker.

**Full suite:** 183 passed, 1 xfailed.

## 3. Plumbing closed loop (200 seeds, fold 2 2024-25, 1,398 games)

Command: `scripts/run_engine_standins_v1.py sim --seed0 {0,50,100,150} --nseeds 50`, then `... grade`.

Configuration:
- stage 1 = H3''-LC2 + T2;
- stage 3 = A3g-c;
- block = B0 STAND-IN;
- stage 4 = L0s STAND-IN;
- goals = xG_ref stub;
- no goalie pull, shootout skipped.

Full tables:
- `docs/tests/gates_g2_standins_plumbing_2026-10-16.md` (G2, all cells, RS / PO / overall, 100 vs 200 seeds, decompositions);
- `docs/tests/gates_g3_standins_plumbing_2026-10-16.md` (G3 by state, tiers, types, per team, blocked / unblocked per 60).

All PASS / FAIL words below are the gate code's labels, read as reference only.

### G2 attempts per 60 by state, regular season (reference tolerance 3%)

| state | sim | actual | rel | label |
|:--|--:|--:|--:|:--|
| 5v5 | 58.55 | 58.35 | +0.35% | PASS |
| PP | 101.11 | 101.62 | -0.51% | PASS |
| PK | 14.02 | 14.32 | -2.11% | PASS |
| 4v4 (listed, INV-42) | 50.10 | 48.62 | +3.03% | FAIL (marginal; PASS at 100 seeds; L0m loop +3.08%) |
| 3v3 (listed, INV-35) | 59.29 | 55.23 | +7.34% | FAIL (L0m loop +7.74%) |

- **Per team-game:** sim 59.05 vs actual 59.48, verdict CLEAN.
- **Comparison with the SL-R3 L0m loop.** 5v5, PP and PK per 60 are within 0.02 pp of the L0m loop. Stage 3 is unchanged and the block / stage-4 tables only change the goal path, so this is as expected.

### Blocked and unblocked attempts per 60 by state, regular season (sim vs actual)

| state | blocked/60 sim | blocked/60 actual | rel | unblocked/60 sim | unblocked/60 actual | rel | block share sim / actual |
|:--|--:|--:|--:|--:|--:|--:|:--|
| 5v5 | 17.15 | 16.89 | +1.5% | 41.41 | 41.46 | -0.1% | 29.28 / 28.95% |
| PP | 26.44 | 25.56 | +3.4% | 74.67 | 76.06 | -1.8% | 26.15 / 25.15% |
| PK | 1.75 | 1.74 | +0.8% | 12.26 | 12.58 | -2.5% | 12.50 / 12.13% |
| 4v4 | 14.38 | 11.51 | +24.9% | 35.71 | 37.11 | -3.8% | 28.71 / 23.68% (n 1,529) |
| 3v3 | 12.34 | 9.68 | +27.4% | 46.95 | 45.55 | +3.1% | 20.81 / 17.53% (n 1,369) |

- **4v4 / 3v3 block shares.** B0 serves 4v4 and 3v3 the ES block share of their period type, because B0 has no separate 4v4 / 3v3 strata. Their actual shares are 5 and 3 pp lower. This is a construction limit of the stand-in; it is not tuned here.
- **Playoffs.** Shares are listed in the G3 doc; the cells are small.

### G3 xG_ref per unblocked attempt by state, regular season (reference tolerance 3%)

| state | n actual | sim | actual | rel |
|:--|--:|--:|--:|--:|
| 5v5 | 89,759 | 0.0600 | 0.0585 | +2.46% |
| PP | 14,711 | 0.1004 | 0.1009 | -0.56% |
| PK | 2,433 | 0.0702 | 0.0690 | +1.81% |
| 4v4 | 1,167 | 0.0667 | 0.0702 | -5.04% |
| 3v3 | 1,129 | 0.0849 | 0.0872 | -2.69% |
| all reachable | 109,199 | 0.0660 | 0.0649 | +1.64% |

- **Decomposition (RS and overall): CLEAN.**
- **Tiers.** 5v5 / PP are within 1.03 pp. PK medium is -1.65 pp. 4v4 medium / low are -5.6 / +6.9 pp, and 3v3 medium is -9.1 pp: L0s shrinks those cells toward 5v5 (K 500). The 4v4 xG gap improved from -12.2% under L0m to -5.0%.
- **Playoffs 5v5 xG +5.7%** (FAIL label). This carries over from the offline playoff segment, as in SL-R3.
- **Per team:** the correlation of sim and actual xG per attempt is 0.13. This is expected against a flat stand-in, and all team cells are UNDERPOWERED.
- **Goals per game (stub):** sim 5.59 vs 5.54 actual in reachable states (+0.49 EN goals per game, unreachable).
- **Responsiveness (D32 R):** not computed. Both stand-ins are flat, and the helper belongs to Lane R.

## Not done / notes

- The results in `results/standins_plumbing_v1` (gitignored) are not synced to HF. The loop is reproducible from the commit in about 9 min.
- The `stand_in` output key exists only when a stand-in is on. That keeps flag-off output bit-identical, including its key set, to HEAD.
- **Stage 5 must not be fit on this loop's output** (D32). Stage-5 fits use recorded rows. A stage-5 SOG / miss model consuming `attr` output would get stand-in unblocked attempts in the closed loop only.

## Proposed BOARD / STATUS text (PM-owned; not edited)

"Lane E (2026-10-16): D32 stand-ins wired behind default-off flags (block B0 `p_block_game`, stage-4 L0s `state_pdf`). Flag-off is bit-identical to 3ce7112, served values match offline within 1.5e-8, and the output carries a `stand_in` marker. The 200-seed plumbing loop ran clean except for listed cells: G2 4v4 +3.03% (INV-42) and 3v3 +7.3% (INV-35); B0 over-blocks 4v4 / 3v3 by 5 / 3 pp (ES pooled), a stand-in limit for SB-R4 to note."
