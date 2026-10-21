# EG-R1 part A (INV-66), Lane H8a: goalie pull process + EN cascade, engine wiring, plumbing loop

Lane H8a (Opus), 2026-10-21. Spec: `docs/models/end_game/experiments.md` EG-R1 part A, the Lane H8a execution note, and
the D45 ruling. Part A loop only: OT is the stage-1 3v3 OT, the shootout is the 50 / 50 stub, there are no rebounds
(parts B / C are Lane H8b), and the goalie is the ORACLE GOALIE (D8).

## Summary

- **Selected: P1** (fold 2, blind; D45 rule). LL is +0.888 per team-game vs P0 (SE 0.075, 11.9 SE). Gated offline
  checks pass: first-pull median trail1 114 vs 120 s, trail2 175 vs 185 s, re-pull share 0.200 vs 0.220. D13 fold-1
  guard PASS. The trail3+ median is listed (252 vs 255.5, n 98, UNDERPOWERED).
- **Engine flag `tables["pull"]`** (default off). Flag off is bit-identical to HEAD d5e387a on 16 fixture cases, and the
  200-seed pull-off loop is bit-identical (file sha256) to Lane E3's loop. Every served EN component matches its offline
  prediction within 3e-8. 173 engine tests pass (147 existing + 26 new).
- **Closed loop (200 seeds, fold 2), pull on:**
  - Gate (D45) pulled time per game: **66.0 vs 77.8 s, -15.2%, FAIL** (tolerance 10%).
  - Gate (D45) trailing-by-1 pulled share: **0.599 vs 0.608, -0.9 pp, PASS** (tolerance 3 pp).
  - G7 EN goals per game: **0.345 vs 0.406, FAIL** (tolerance 0.03).
  - G7 regulation-tie rate: **0.2376 vs 0.2082, FAIL**. With the pull off it was 0.2045 and passed.
  - G7 shootout share: **0.0726 vs 0.0551, FAIL**.
  - G1 and G3 unchanged. G2: the 4v4 cell crosses its band (+2.8% -> +3.2%, listed INV-42).
- No fix was applied inside the round (spec).

## Step 2: fold-2 selection (`train_end_game_pull_v1.py`; grades `docs/tests/end_game_eg_r1_pull/grade_fold{1,2}.json`, `select.json`)

| fold 2 (test 2024-25, RS) | actual | P0 | P1 | gate |
|---|---|---|---|---|
| LL per team-game (1,182 team-games with rows) | | -5.236 | -4.348 | P1 - P0 +0.888, SE 0.075 |
| first-pull median trail1 (n 444) | 120.0 | 113 | 114 | 10 s: PASS / PASS |
| first-pull median trail2 (n 309) | 185.0 | 175 | 175 | 10 s: PASS / PASS |
| first-pull median trail3+ (n 98, UNDERPOWERED) | 255.5 | 255 | 252 | listed |
| re-pull share | 0.220 | 0.208 | 0.200 | 5 pp: PASS / PASS |
| pulled s/game (offline; ratio to in-sample P0 85.7, diagnostic) | 77.8 | 76.5 (0.893) | 77.6 (0.906) | closed loop |
| trailing-by-1 share (offline; pp vs in-sample P0 0.585, diagnostic) | 0.608 | 0.576 (-0.9) | 0.577 (-0.8) | closed loop |

The in-sample P0 calibration sits at about 1.10 of actual in every season (fold 1: 75.2 vs 67.6). On fold 2 both arms
are at 0.89-0.91 of it: they pull less than the 2024-25 teams did. **2024-25 pulled earlier and longer:** actual
pulled time is 77.8 s per game against 63.9-67.6 s in the three training seasons (+18% on their mean), and the medians
are 120 / 185 s against 108-113 / 170-178 s. The spec carries no level in EG-R1. A fold-2 pulled-time miss of more
than 10% makes a level EG-R2's first item (step 0 showed no trend inside the training seasons, so the jump is a
single-season move; L23 applies).

Noise floor 0: P1 is a deterministic logistic.

## Step 3: EN inventory and stand-in levels (`docs/tests/end_game_eg_r1_en_levels_2026-10-21.md`, `src/nhl_sim/end_game/en.py`)

| stage | served at EN-for (st 5) / EN-against (st 6) | parity, served vs offline (fold 2) |
|---|---|---|
| 3 attempts | **STAND-IN** as-of M1 K500 attempt level per EN state (A3g-c has no EN state) | per-season parity below |
| block | **B0's own ENF / ENA intercepts** with the ES level (`p_block_en`) | 1.5e-8 over 4,720 rows |
| 4 class | L0s baseline rows 5 / 6 x the ES-group level (L1x-as offline does the same, L33) | 3.0e-8 over 3,208 rows |
| miss | **S0t's own ENF / ENA columns** with the ES level group (`p_miss_en`) | 3.0e-8 over 3,208 rows |
| goal EN-for | C1s EAF (sg 5, 5v5 level group, score dummies zero on EAF rows, defending starter) | 1.1e-16 over 1,487 starter rows |
| goal EN-against | **STAND-IN** as-of M1 K500 goal per SOG into an empty net (1.0 in the data) | parity below |
| pull hazard | P1 lookup [deficit, 10-s bin, pen, pulled_before, home] | 0 over 523,057 rows |

**Correction to the spec text.** The spec said "block B0 ES group; miss S0t ES+EN group". The offline B0 and S0t models
carry their own ENF / ENA groups (B0: one-hot strength group x period type over ES / PP / PK / ENF / ENA; S0t: base
and coefficient columns 3 / 4), both on the ES level group. Serving the ES group would have been an invented mapping
and failed parity by 0.28 (block) and 0.53 (miss), so the engine serves the models' own EN groups.

EN levels, predicted / actual per season (2021-22 is burn-in): EN-for attempts 0.981 / 0.966 / 1.004 (2022-23 /
2023-24 / 2024-25); EN-against attempts 0.953 / 1.023 / 0.935 (about 900-1,130 attempts per season, Poisson SE about
3%); goal share at the empty net 1.002 / 0.998 / 1.000. EN-for attempts trend up (132 -> 143 -> 158 per hour), so
the M1 level runs low under the trend (L27).

## Step 4: engine (`src/nhl_sim/engine/sim.py`, `state.py`; `tests/engine/test_sim_pull.py`)

- **GameState** (per team) gains `pulled`, `pulled_before`, `last_return`, the re-pull counters and `track_pull`
  (default False). The return rules sit in `goal()`: the goalie returns at a goal against and at the team's own tying
  goal, nowhere else. At the end of regulation the engine raises if a goalie is still out in a tied game.
- **sim.py, flag `tables["pull"]`.**
  - The pull draw happens at the start of each second in the last 600 s of regulation, before that second's draws,
    for teams trailing before the second (stream `pull`).
  - EN team-view states 5 / 6 run through stage 3 (stand-in levels), block, class, miss and goal as in the table above.
  - Stage 1 keeps reading the penalty-derived strength.
  - Recording arrays have 7 states when the flag is on.
  - Outputs add the pull counters and the `pull_model` / `pull_stand_in` markers.
  - The RS-trained hazard is also served in playoff regulation (labelled).
- **Tests (26 new).**
  - The flag-off fixture (recorded from d5e387a before the edit) passes on all 16 cases.
  - Return at a goal against; return at the own tying goal; no return at a non-tying goal for; track_pull off changes
    nothing.
  - **The goalie-out state never persists past a tying goal** (monkeypatched GameState.goal over a full synthetic sim).
  - Synthetic P1 / P0 runs visit the EN states, keep goals == score and carry the markers; the flag refuses an incomplete
    cascade; the served hazard equals the offline hazard for P1 and P0 (< 1e-6).
- The delayed-penalty test was dropped (D45): the engine has no delayed-penalty state (INV-70).

## Step 5: 200-seed fold-2 loop (`scripts/run_end_game_pull_v1.py`; pull on vs a paired pull-off run)

Clock: pull on 14:08:43-14:14:24, pull off 14:14:37-14:20:16 (4 x 50 seeds, 2 threads each, about 5.5 min each); grades
14:20-14:21. Below 15 min, so no box request.

**EN table (regular season; actual = the same detection rule, engine-rule non-DP episodes):**

| quantity | sim | actual | |
|---|---|---|---|
| pulled s per game (D45 gate, 10%) | 66.0 | 77.8 (literal shift-chart 70.5) | **-15.2% FAIL** |
| trailing-by-1 pulled share (D45 gate, 3 pp) | 0.599 | 0.608 | **-0.9 pp PASS** |
| first-pull median trail1 / trail2 / trail3+ | 110 / 174 / 257 | 120 / 185 / 255.5 | |
| re-pull share | 0.272 | 0.220 | closed-loop value, above offline 0.200 |
| episodes per game | 0.743 | 0.768 | |
| EN-against goals per game (pbp EN_AGAINST) | 0.345 | 0.399 | |
| EN-for goals per game | 0.152 | 0.171 | |
| EN-against goals per pulled hour | 18.8 | 18.5 | EN scoring per second matches |
| EN-for goals per pulled hour | 8.3 | 7.9 | |
| tying goals while pulled per game | 0.069 | 0.054 | |
| goal-against returns per game | 0.344 | 0.402 | |

- **Missing by construction (INV-70):** delayed-penalty pulls are 10.6 s per game on 2024-25 RS (shift rule), with 14
  pull-ending goals for. They are absent from the engine. EN-against goals are unaffected.
- **Not produced:** the spec's "goals in the last 2 min of regulation by deficit" (the engine does not record goal
  times).

**G7** (all 1,398 games; `docs/tests/gates_g1g5g7_end_game_pull_{on,off}_v1_2026-10-21.md`):

| check | pull on | pull off | actual | tolerance |
|---|---|---|---|---|
| regulation-tie rate | 0.2376 FAIL | 0.2045 PASS | 0.2082 | 1.5 pp |
| shootout share | 0.0726 FAIL | 0.0625 PASS | 0.0551 | 1.0 pp |
| EN goals per game | 0.3451 FAIL | 0 FAIL | 0.4063 | 0.03 |

**Decomposition of the G7 failures.**
1. **EN goals.** The miss comes from pull timing, not EN scoring. EN-against goals per pulled second match within
   2%, and pulled time is short by 15%. Fold-2 pulls came earlier than any training season.
2. **Tie rate.** The pull adds the trailing team's 6v5 scoring (8.3 goals per pulled hour against about 3 at 5v5), so
   ties rise 3.3 pp, and tying goals while pulled are 0.069 vs 0.054 per game despite 15% less pulled time. The
   pull-off engine already matched the actual tie rate without any 6v5. That points to a compensating bias upstream:
   G5 shows sim margins too narrow (SD ratio 0.87 in Lane E3's loop), meaning too many one-goal games late. A passing
   aggregate over a biased sub-model is a failure, so the pull-off G7 tie "pass" should not be read as clean. Stage 7
   (INV-69), the score-state late-game rates and the OT / SO parts (Lane H8b) all feed this cell, and it is not fixed
   here.

**G1 / G2 / G3 re-checks (pull on vs paired pull off = E3's loop, bit-identical):**

- **G1** (RS + PO): PASS, unchanged. TOI 5v5 50.29 vs 50.26 (actual 50.50); PP total 9.18 vs 9.17; PP opportunities per
  team-game 2.670 vs 2.666 (actual 2.584). TOI EN 1.10 min (actual pbp 1.06; reported).
- **G2** (RS):
  - 5v5 +0.49% (off +0.31%), PP -0.53% (-0.59%), PK -2.11% (-2.19%): all PASS.
  - 4v4 +3.21% FAIL (off +2.84% PASS; listed INV-42); 3v3 +5.42% (+5.31%; listed INV-35).
  - Team-game mean -2.5% (off -1.0%) PASS. This counts states 0-4 only: the part files carry no EN columns, so the
    1.83 EN attempts per team-game drop out of the sim mean, while the actual mean includes EN attempts. With them
    added the sim is +0.6%. This is a grader artefact, reported.
- **G3** (overall): PASS on both runs. All reachable +0.41% (off +0.34%), 5v5 +0.65% (+0.66%), PP -0.03% (-0.03%), PK
  +2.18% (+2.21%).

## Not done / listed

- The delayed-penalty state (INV-70) and its 10.6 s per game; goals-by-deficit in the last 2 min; a pull-timing level
  (EG-R2 item per spec); P1's re-pull lag misfit (closed-loop re-pull share 0.272 vs 0.220; D45 listed it).
- Results are not on HF.

## Earlier stop (kept for the record)

Before D45, the lane stopped at step 2 because the offline pulled-time check was biased by construction: in-sample P0
gave 1.104 / 1.111 of actual on 2022-23 / 2023-24. Diagnostic: `scripts/diag_end_game_pull_offline_bias_v1.py`; jitter
replay within 1.009. Commits 3da15f8, 938f2a9.
