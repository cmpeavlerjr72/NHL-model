# End game (stage 8): goalie pull and empty net, overtime, shootout; in-game goalie change

Append-only. Step 0: `docs/tests/stage8_step0_audit_2026-10-21.md` (Lane Z, INV-65; training seasons only). Gates: G7 (`docs/gates.yaml`: regulation-tie rate 1.5 pp, shootout share 1.0 pp, EN goals per game 0.03) and the G2 3v3 cell (INV-35). Rule-era flags live in `src/nhl_sim/engine/rules.py` (all seasons are the 3v3-OT era).

## EG-R1: goalie pull + empty-net scoring, the OT 3v3 level, the shootout (pre-registered 2026-10-21 by the PM, before any run; INV-66, INV-35, INV-67)

Three parts, each with its own offline selection, then one closed loop with all three wired. Folds as always: fold 1 trains through 2022-23 and tests 2023-24; fold 2 trains through 2023-24 and tests 2024-25 (selection). Nothing from 2024-25 is read before a part's selection step. Regular season only; playoff OT (5v5 continuous, no shootout) is served by the regulation cascade with the rule flags and is reported as a consistency check, UNDERPOWERED.

### Part A: goalie pull process and empty-net scoring (INV-66)

**Pull detection (data).** The audit's rule: a goalie shift-chart gap confirmed by the pbp goalie-on-ice flag; delayed-penalty pulls are the pulls that end at an opponent penalty call or carry a `DELAYED_PENALTY` event. The lane reuses `scripts/diag_stage8_step0_a_pulls.py`.

**Rows.** Regular-season team-game-seconds from 600 s left in regulation to 0, where the team trails by 1, 2 or 3+, its goalie is in, and no delayed penalty is on. Outcome: the goalie is pulled at this second. Features use the state BEFORE the second (score effects rule). A `pulled_before` flag marks re-pulls.

**Arms.**

| Arm | Model |
|---|---|
| N0 | no pull (the engine today; comparator for the closed loop only) |
| P0 | empirical lookup: sample seconds-left at the first pull from the training-season distribution keyed by (deficit 1 / 2 / 3+, penalty-on); re-pull with the observed re-pull share and lag. Flat, team-agnostic, labelled STAND-IN-grade (adoptable only if P1 fails) |
| P1 | discrete-time hazard per second: logistic on deficit (3 levels) x seconds-left bins (10 s) + penalty-on (trailing team short-handed / on the PP) + pulled_before + home. Fitted on the training seasons |

Step 0 (training seasons, committed before any fit): the per-season median first-pull time by deficit and the per-season pulled time per game, to show whether a level is needed (L27). EG-R1 carries no level; if the fold-2 pulled time per game misses by more than 10%, a level is EG-R2's first item.

**Return and rider rules (deterministic, from the audit, no parameter):** the goalie returns at a tying goal (immediately) and at a goal against (at the goal); re-pulls follow the hazard with `pulled_before` = 1; during the engine's stage-1 delayed-penalty state the trailing-or-leading team's goalie is off (goals in that state are EN-for goals and never EN-against).

**Empty-net scoring once pulled.** The cascade is reused with the team-view states EN_FOR (6v5 attacker, own goalie pulled) and EN_AGAINST (5v6 defender shooting at the empty net): stage 3 hazard at those states if A3g-c carries them, otherwise an as-of M1 K500 attempt level per EN state (labelled stand-in, listed); stage 4 L0s baseline on EN rows (L33); block B0 ES group; miss S0t ES+EN group; goal given SOG at the empty net = an as-of M1 K500 level on EN_AGAINST SOG (no goalie; expected near 0.9); goal given SOG for the pulled team = C1s with the defending goalie. The lane reports which tables carry EN states and which are stand-ins; it invents no mapping.

**Selection (fold 2, blind):** P1 is selected over P0 if its per-team-game LL on the pull rows is better by > 2 SE and every bias check passes: pulled time per game within 10%, first-pull median by deficit within 10 s, share of trailing-by-1 games with a pull within 3 pp, re-pull share within 5 pp. Otherwise P0 if its bias checks pass. Fold 1 is the D13 guard (same checks). Noise floor: a second-seed P1 refit (the logistic is deterministic, so the floor is 0, stated).

### Part B: overtime (INV-35)

- **3v3 attempt level.** An own as-of level for 3v3 attempts (M1 K500, per 60, both teams, OT rows only) replaces the shared ES level for 3v3 in the served A3g-c table. Per-training-season parity on the SA-R2 rule; the oracle row is reported (L29). Constructions in the grid: M1 K500, M1 K2000, M2 H30; E is not selectable (D35). Selected by the SA-R2 rule.
- **4v3 / 3v4 / 4v4 in OT** are served by the regulation PP / PK / 4v4 cascade with the OT period type (labelled; the audit's 68 and 12 goals are UNDERPOWERED). OT penalties come from the stage-1 hazard as served today.
- **Sudden death.** Regular-season OT ends at the first goal; the lane confirms the engine does this and adds a test.
- **Gate (closed loop):** the G2 3v3 cell within its band; the OT-goal share of tied games within 3 pp of actual (UNDERPOWERED: about 290 OT games on fold 2); OT winner home share reported.

### Part C: shootout (INV-67)

| Arm | Model |
|---|---|
| S0 | the 50 / 50 winner stub (today's engine) |
| S1 | rules mechanics (3 rounds, then sudden death, alternating; the home team shoots first with the as-of share of that choice) with a constant per-attempt success p = an as-of M1 K500 level over attempts (about 0.31); attempts independent |
| S2 | S1 + shooter rating (as-of, shrunk, b = 50 attempts, w 0.7, relative to the snapshot mean) at a fixed spread-tuned scale (D27 form); offline only, because the shooter order is chosen in game and the engine cannot serve it this round |

**Selection (fold 2, blind):** S1 replaces S0 if its bias checks pass: per-attempt success within 2 pp, share of shootouts past round 3 within 5 pp, winner home share within 5 pp (all UNDERPOWERED on about 90 shootouts; labelled). S2 is a signal check for the player layer: report its per-attempt LL vs S1 with SE, and the shooter R (D32), expected UNDERPOWERED; nothing is served from S2.

### Closed loop (after all three parts are wired)

200 seeds, fold 2, the default engine set (D43 / INV-63) plus the selected pull arm, the EN cascade, the 3v3 level and S1, oracle goalie. Report:
- G7: regulation-tie rate, shootout share, EN goals per game (the three gate the round);
- the EN table: pulled time per game, EN goals for and against per game, goals in the last 2 min of regulation by deficit, re-pull share, all vs actual;
- the OT table: 3v3 attempts / SOG / goals per 60, OT-goal vs shootout split, OT winner home share;
- G1, G2, G3 re-checks (unchanged within noise is the requirement; the pull process changes late-regulation states and must not move G1);
- G5 and G6 (total and margin distributions, score correlation) as a first full read, labelled "stage 7 absent"; the PM rules on whether they gate.

**Decision.** Stage 8 is CONFIRMED-INCUMBENT (provisional) if G7 passes on all three quantities and G1-G3 are unchanged within noise. A G7 failure is reported with its decomposition (pull timing vs EN scoring vs OT split); no fix is applied inside the round. In-game goalie changes (INV-68) and stage 7 (INV-69) are separate rounds.

### Results

(append below this line)

#### Lane H8b execution note for parts B and C (2026-10-21, written before any H8b run; no spec change)

Fixes only the details the spec leaves to the lane.
- **3v3 level units.** Rows: stage-3 attempt rows, team view st = 3v3, regular season (both team views; counts = team attempts, exposure = team-hours; per 60 combined = 2 x per team-hour). M1 K = prior attempts at the previous season's final 3v3 rate: shrunk = (n + K) / (h + K / r_prev). M2 H30 = M1 with K = 2000 and n, h discounted by 0.5^(gap days / 30) per date (the SL-R2 form). E = era pooled training rate (reported, not selectable). O = season's own final rate. No season-phase profile (not identifiable on 3v3). One value per game, from earlier-dated games only, `created_at` < `puck_drop` asserted. 2021-22 prior = its own final rate (labelled, never judged).
- **Parity rule (SA-R2 / LC-2 form).** |predicted / actual - 1| <= 0.5% per genuine-prior training season (fold 1: 2022-23; fold 2: 2022-23 and 2023-24). Selection = the simplest passer; simplicity order M1 K2000 < M1 K500 < M2 H30 (larger K is nearer the prior-only level). If none passes: the smallest max |parity|, ties within 0.1 pp to the simpler, failure listed, proceed (the SB-R1 / SA-R2 fallback). The selection reads training seasons only; the 2024-25 3v3 rows are first loaded by the `ot_fold2` step, after the parity table is committed. A Poisson 1/sqrt(n) per-season count error is printed alongside, because with about 1,500 3v3 attempts per season a 0.5% limit is below the sampling error of the season's own rate.
- **Served form.** Served 3v3 attempt rate = the A3g-c served rate x exp(L_new - L_old), L_old = the level the A3g-c table used for 3v3 rows (the SA-R2 ES-group level + profile, `league_level_v2_f2`), L_new = the selected own level (per team-hour, log). The A3g-c 3v3 cell is retained as frozen (-1.3% to -1.6%); this is stated, not tuned. The gate is the closed-loop G2 3v3 cell.
- **S1 inputs.** Per-attempt success p: as-of M1 K500 over shootout attempts (K attempts at the previous season's final success rate; n, h replaced by goals, attempts). Home-shoots-first share: the same form over shootouts. Shootout goals / attempts from the audit's rule (SO events SHOT, MISS, GOAL, FAILED_SHOT_ATTEMPT; 2021-22 non-goal typing differs, goals are unaffected). S2 (offline): shooter log-odds rating, w 0.7, b 50 attempts, shrunk, relative to the snapshot mean, entered at a fixed scale s (the D27 form) with the fold-1 s-grid {0.5, 0.75, 1.0, 1.25, 1.5} x the standardised rating; fold-1 selection by LL on 2023-24; goalie term absent (audit: no goalie signal).

#### Lane H8a execution note for part A (2026-10-21, written before any fit; training seasons only read; no spec change)

Fixes only the details the spec leaves to the lane. Code `src/nhl_sim/end_game/pull.py`, rows `scripts/build_end_game_pull_rows_v1.py`, step 0 `docs/tests/end_game_eg_r1_pull_step0_2026-10-21.md`.
- **Episodes follow the engine's return rules.** The spec's rules (return at a tying goal and at a goal against, nowhere else) define the engine's goalie state, so a data pull episode starts at a non-DP shift-gap start while trailing in the last 600 s and runs to the first goal against / tying goal (that second included) or the end of regulation. A shift-chart return that is neither (stoppage, non-tying goal for, in play) does not end the episode; those goalie-in seconds are "bridged" and counted: 7.3 / 8.6 / 7.9 s per game on 2021-22 / 2022-23 / 2023-24 (about 12% of the engine-rule time; step-0 table). The engine-rule time per game is the like-for-like target of the pulled-time bias check; the literal shift-chart time (58.6 / 56.1 / 60.0 s) is reported beside it. Rows are the goalie-in seconds in engine terms (team trailing before the second, not in an episode, no DP pull of either team covering the second); `pulled_before` = an episode of this team ended earlier in the window (so a re-pull is the audit's 1e re-pull after a goal against).
- **Pull at a goal second.** A pull whose shift gap starts at the same clock second as a goal (the faceoff after it) is assigned to the next second, whose pre-event score is the post-goal score; the engine draws the pull at the start of a second, before that second's attempts.
- **Penalty-on.** pk = own skaters < opponent's, pp = own > opponent's, from the last event before the second with the team's goalie in (the audit's pre-pull state). 4v4 / 3v3 count as neither.
- **P0 as a hazard.** "Sample the first-pull time from the training distribution keyed by (deficit, penalty-on)" is served and scored as its exact discrete hazard: first-pull hazard per (deficit 1 / 2 / 3+, penalty-on, second) = first pulls / at-risk rows at that second (pulled_before = 0 rows); re-pull hazard per second since the return = re-pulls / at-risk rows at that lag (pulled_before = 1 rows). No smoothing.
- **P1 fit.** Logistic with one-hot deficit x 10-s bin (180 cells) + pk + pp + pulled_before + home, Newton on the aggregated cells, with a Gaussian prior of SD 10 on every coefficient as a numerical guard for cells with no pull (negligible on populated cells; fixed before the fit, not tuned).
- **Scoring.** Per-team-game LL = sum of the Bernoulli log-likelihood over the team-game's rows, every hazard clipped to [1e-6, 1 - 1e-6] (both arms). Paired difference P1 - P0 per team-game; SE = SD / sqrt(n team-games). Arm labels are hashed in the grade table until it is final.
- **Bias checks by the offline pull simulator.** On the actual test-season paths (score before each second, penalty state, DP-on, actual goal seconds), 200 replications per team-game (seeded), the engine's return rules: pulled time per game (engine-rule; literal reported), first-pull median by deficit at the start, share of trailing-by-1 team-games with a pull (team-games with at least one row second at deficit 1: share with an episode starting at deficit 1), re-pull share (episodes ended by a goal against followed by another episode). Fold 1 (train 2021-22 + 2022-23, test 2023-24) is the D13 guard with the same checks.
- **Delayed-penalty rider: the engine has no stage-1 delayed-penalty state.** Stage 1 applies a penalty at the second it is drawn (SS-R2 change 1 put the signal-to-whistle seconds into the pre-signal state, L20; the 6v5 itself was logged as a stage-8 candidate). The rider is wired as a GameState flag (the penalised team cannot score while it is on, the other team's goalie is off, so a goal in that state is EN-for and never EN-against) with its test, but stage 1 never sets it in the loop. So the DP pulled time (audit 1h: 11 to 12 s per game) and its EN-for goals (23 to 24 per season, 1g) are absent from the closed loop. Listed, not invented.
- **EN cascade inputs.** Stage-3 A3g-c has no EN states, so the EN attempt rates are as-of M1 K500 levels per EN state (K = 500 attempts at the previous season's final rate; 2021-22 prior = its own final rate, burn-in, never judged) on the stage-3 attempt rows (`attempt_rows_v1`, team-view st 5 EN-for / 6 EN-against; these use the pbp goalie state with the L20 fix, so unlogged DP pulls remain inside st 5 / 6: listed). Goal per SOG at the empty net: the same M1 K500 form on st-6 shots on goal (`attempt_attr_v1`). Stage 4 L0s baseline rows 5 / 6 with the ES-group level (L33), block B0 ES group, miss S0t ES group, C1s EAF (sg 5, 5v5 level group) for the pulled team's shots with the defending starter. All served with their offline predictions checked.
- **Playoffs and stage 1 under a pull.** The RS-trained hazard is also served in playoff regulation (labelled, UNDERPOWERED check). Stage 1 keeps reading the penalty-derived strength during a pull (no 'other' state served; SS-R2).

#### Part A results, Lane H8a (2026-10-21): PARTIAL, stopped at step 2 before any fold-2 read (`docs/tests/end_game_eg_r1_pull_2026-10-21.md`)

- The pulled-time bias check is biased by construction under the offline method: P0 fitted in-sample (the exact empirical hazard) gives 1.104 / 1.111 of the actual engine-rule pulled time on 2022-23 / 2023-24, and the trailing-by-1 share -2.7 / -2.6 pp. Cause: on actual paths the returns are actual goals, which are endogenous to the real pull. Timing jitter alone gives at most 1.009. No arm can pass the 10% band, so the selection rule cannot be met; the lane stopped and reports for a ruling. Medians and re-pull share are unbiased in-sample.
- Fold-1 D13 grade (2023-24): P1 - P0 LL +1.226 per team-game (SE 0.088); pulled time P0 +10.5%, P1 +12.6% (both FAIL; 0.995 / 1.013 of the in-sample calibration); medians t1 / t2 PASS, t3+ FAIL (n 80, UNDERPOWERED); trail1 share P0 FAIL, P1 PASS; re-pull PASS.
- Not done: fold-2 grade and selection, EN cascade, engine wiring, closed loop.

---

## PM ruling on the EG-R1 part A stop (2026-10-21, D45)

- The offline pulled-time and trailing-by-1 share gates were a PM construction defect (offline replay returns the goalie only at actual goals). Both move to the closed loop (10%, 3 pp), where EN scoring supplies the returns; offline they are reported relative to the in-sample P0 calibration.
- Medians, re-pull share and the LL rule stand. Trailing-by-3+ median is UNDERPOWERED, listed.
- The delayed-penalty rider cannot be wired: the engine has no stage-1 delayed-penalty state (INV-70). The loop gate is on non-delayed-penalty pulled time.
- Fold-1 D13 guard PASSES for P1 under the restated rule. Resume at step 2.

### EG-R1 part A results after D45

(append below this line)

#### Lane H8a, part A after D45 (2026-10-21; `docs/tests/end_game_eg_r1_pull_2026-10-21.md`)

- **Selected: P1** (fold 2, blind). LL +0.888 per team-game vs P0 (SE 0.075). Gated checks pass: medians trail1 114 vs 120 s, trail2 175 vs 185 s; re-pull 0.200 vs 0.220. D13 fold-1 guard PASS. trail3+ 252 vs 255.5 (n 98, UNDERPOWERED, listed). Offline pulled time is 0.906 of the in-sample P0 calibration (diagnostic).
- **EN inventory.** A3g-c has no EN state, so EN attempts are a STAND-IN as-of M1 K500 level per EN state. EN-against goal per SOG is a STAND-IN M1 K500 level (1.0). Block and miss serve B0's and S0t's own ENF / ENA groups on the ES level; the spec's "ES group" wording does not match the offline models, and the ES group would fail parity by 0.28 / 0.53. Stage 4 is the L0s baseline on EN rows (L33). EN-for goals are C1s EAF. Every served-vs-offline parity is <= 3e-8.
- **Engine.** Flag `tables["pull"]` (default off) is bit-identical to d5e387a on 16 cases. The pull-off 200-seed loop is bit-identical (sha256) to Lane E3's loop. 26 new tests pass, including the goalie-out state never persisting past a tying goal. Full suite: 312 passed, 1 xfailed.
- **Closed loop (200 seeds, fold 2, pull on, part A only).**
  - Pulled time per game 66.0 vs 77.8 s, **-15.2% FAIL**.
  - Trailing-by-1 share 0.599 vs 0.608, **PASS**.
  - G7: EN goals 0.345 vs 0.406 **FAIL**; regulation-tie 0.2376 vs 0.2082 **FAIL** (pull off 0.2045); shootout 0.0726 vs 0.0551 **FAIL**.
  - G1 / G3 unchanged (PASS). G2 4v4 +2.8% -> +3.2% (listed INV-42).
- **Decomposition.**
  - EN scoring per pulled second matches actual (EN-against 18.8 vs 18.5 per hour). The EN-goal miss is pull timing: 2024-25 pulled earlier than any training season (77.8 s vs 63.9-67.6 s per game; medians 120 / 185 vs about 111 / 175 s). That is a level, EG-R2's first item per the spec.
  - The tie-rate rise comes from the trailing team's 6v5 scoring (tying goals while pulled 0.069 vs 0.054 per game). The pull-off engine already matched the actual tie rate without any 6v5, which points to an upstream compensating bias (G5 margins too narrow). Not fixed here.
- **Missing by construction:** delayed-penalty pulls, 10.6 s per game (INV-70). Not produced: last-2-min goals by deficit.

#### Lane H8b, parts B and C and the stage-8 closed loop (2026-10-21; generated tables in `docs/tests/end_game_eg_r1_otso_*_2026-10-21.md`, gates in `docs/tests/gates_g*_end_game_otso_v1_*`)

**Headline.**

| item | result |
|---|---|
| 3v3 level selected | **M1 K500** by the fallback (no construction passes the 0.5% parity limit; training max parity 1.92% vs a Poisson count error of 2.6-2.7%); fold-2 level parity +1.28% (SE 2.7%) |
| 3v3 offline served bias, fold 2 | A3g-c +5.4% -> **+0.36%** (SE 2.7%) |
| 3v3 closed-loop G2 cell | **+0.65% PASS** (100 seeds +0.95%); +5.42% FAIL in the Lane H8a loop; 4v4 +3.22% FAIL unchanged (INV-42) |
| S1 fold-2 bias checks (all UNDERPOWERED) | success -1.8 pp PASS; winner home share -3.2 pp PASS; past round 3 **+9.6 pp FAIL** (limit 5 pp; binomial SE 4.9 pp; fold 1 -0.4 pp PASS) |
| S2 vs S1 (offline) | -0.0003 nats/attempt, SE 0.0021; shooter R 2.37 (CI 0.41 to inf); dispersion 1.15: no detectable shooter signal, UNDERPOWERED |
| Closed loop G7 (RS) | regulation tie 0.2374 vs 0.2066 **FAIL** (+3.08 pp); shootout share 0.0810 vs 0.0587 **FAIL** (+2.23 pp); EN goals per game 0.3449 vs 0.3994 **FAIL** (-0.0545) |
| G1-G3 | no status change vs the Lane H8a pull-on loop except the 3v3 G2 cell (FAIL -> PASS); vs the pull-off loop also 4v4 (+2.8% -> +3.2%) and the +1 score bucket PASS -> FAIL, both already in the H8a pull-on loop (the pull flag, not this lane) |

**Part B.**
- Order of work: training parity table and selection committed (e977e74) before any 2024-25 row was loaded; fold-2 parity and offline served bias after (fc75118).
- Grid M1 K500 / M1 K2000 / M2 H30; per genuine-prior season the level-only parity is 0.9% (2022-23) and 1.9-2.0% (2023-24) for all three; E 0.5% / 0.0% (in-sample), oracle 0. A season's own 3v3 count (1,340-1,520 attempts) has a Poisson error of 2.6-2.7%, five times the limit, so none can pass. Fallback: M1 K500 on fold 2 (1.92% vs 2.05% / 2.04%); fold 1 K2000 0.87% vs K500 0.90% is inside the 0.1 pp tie, M1 K500 carried on both folds (labelled).
- Served form: A3g-c served rate x exp(L_new - L_old), the 3v3 cell refit on the training rows with the own level in place (SA-R3 recipe, b_c 50; the same code reproduces the frozen cell to 1e-12 with the old level). Cell -0.0133 -> -0.0153. Other states bit-identical; served vs offline on all 1,690 fold-2 3v3 rows max relative difference 1.2e-7 (float32). Old failure: the shared ES level drifts up while 3v3 is flat (55.2 actual attempts per team-hour vs 58.2 served).
- Step 3 (code check, nothing to fix in `sim.py`): `GameState.goal` ends every game in overtime at the first goal (END_OT; regular-season 3v3 and playoff 5v5 alike); no OT goal by 3900 s ends the regular season in a shootout (END_SO); playoff OT continues in 1200 s periods with no shootout. OT skaters come from the same box machinery (4v3, 3v4, 5v3 after penalties; a post-expiry hold can leave 4v4 until the next stoppage); `team_view_state` maps them to the regulation PP / PK / 4v4 / 3v3 states, the clock index is the OT minute (60-64) and the period type is 4. The A3g-c table is finite and positive for every state at minutes 60-99. Tests: `tests/test_end_game_otso.py`.

**Part C.**
- Mechanics: three rounds, alternating, early termination when decided, sudden death in complete rounds; past round 3 matches the closed form P(level after six) = 0.3456 at p = 0.31 over 200,000 draws.
- Fold 1 (committed d493ff7 before fold 2): as-of p 0.317-0.323, home-first 0.80-0.85. D13 guard on 2023-24 (82 shootouts): success +2.8 pp (limit 2, FAIL, SE 1.8), past round 3 -0.4 pp PASS, winner home share -8.6 pp (limit 5, FAIL, SE 5.4), all UNDERPOWERED. S2 s-grid 0.5-1.5: LL flat (within 0.0006 nats/attempt, SE 0.0008-0.0024); D27 picks s = 1.25 (R 0.98).
- Fold 2 (blind, 77 shootouts, 513 attempts), S1: success 0.3294 actual vs 0.3114 (-1.81 pp, limit 2, PASS); past round 3 0.2468 vs 0.3424 (+9.56 pp, limit 5, **FAIL**, 1.95 SE, UNDERPOWERED; training pooled 33%); winner home share 0.5325 vs 0.5001 (-3.23 pp, limit 5, PASS). One of three checks fails, so under the rule as written S1 is not formally selected over S0; S0 cannot be graded on rounds or success, and on winner home share both sit at 50%. The PM rules. S2 vs S1 -0.0003 (SE 0.0021), R 2.37 (CI 0.41 to inf), shooter dispersion 1.15 (33 shooters): UNDERPOWERED, nothing served.

**Engine.** Flag `tables["shootout"]` (default off) plays S1 for the sims that end level after OT (stream seed, game_id, "shootout"; outputs so_n_att / so_goals_home / so_goals_away / so_home_first / shootout_model). Flag off bit-identical to HEAD 6ac4389 on all 16 `l1xas_parity_cases` (fixture `tests/fixtures/sim_otso_flag_parity.json`, recorded before the edit). The 3v3 level is a table builder (`defaults.att_table(games, ot3v3=True)`, served vs offline < 1e-6 checked before use), not an engine branch. Recording added for the loop (pull flag only): `late_goals`. Full suite 334 passed, 1 xfailed.

**Closed loop (200 seeds, fold 2, oracle goalie; pull P1 + EN cascade of Lane H8a + own 3v3 level + S1).** Wall clock 2026-10-21 14:47:10-14:54:35 (3 processes x 67 / 67 / 66 seeds, 2 threads each; under 15 min, no box request), grade 14:55. Regular season unless marked.

OT table (RS, all seeds):

| metric | sim | actual | diff (pp) | note |
|:--|--:|--:|--:|:--|
| regulation tie rate | 0.2374 | 0.2066 | +3.08 | G7: within 1.5 pp |
| shootout share of all games | 0.0810 | 0.0587 | +2.23 | G7: within 1.0 pp |
| OT-goal share of tied games | 0.6588 | 0.7159 | -5.71 | gate within 3 pp (UNDERPOWERED, about 290 tied games) |
| OT winner home share | 0.5224 | 0.5412 | -1.88 | reported |
| shootout winner home share | 0.5008 | 0.5325 | -3.17 | reported, 77 actual shootouts |

3v3 per 60 (both teams): attempts 111.18 sim vs 110.46 actual (+0.65%); goals 13.20 vs 13.15 (+0.33%); SOG 65.38 sim (no 2024-25 actual computed here; the step-0 audit pooled 2021-24 figure is 73.4, so the sim is about 11% lower; SOG given attempt at 3v3 is the block B0 / miss S0t stand-ins, G3 3v3 is reported FAIL, not investigated here); 3v3 clock 13.62 h per season sim vs 12.39 h actual (+9.9%, from the extra ties).

Shootout table (sim 21,253 shootouts over 200 seeds; actual 77, UNDERPOWERED):

| metric | sim | actual |
|:--|--:|--:|
| per-attempt success | 0.3112 | 0.3294 |
| share past round 3 | 0.343 | 0.2468 |
| winner home share | 0.5008 | 0.5325 |
| home team shoots first | 0.9082 | 0.9091 |
| mean attempts | 7.18 | 6.66 |

Goals in the last 2 minutes of regulation by the scorer's state before the goal (per RS game, EN goals included; pbp seconds 3481-3600 map to sim seconds 3480-3599): leading 0.2651 sim vs 0.3232 actual; tied 0.0365 vs 0.0244; trailing by 1 0.0635 vs 0.0503; trailing by 2+ 0.0759 vs 0.0625; all 0.4410 vs 0.4604.

EN table (from the H8a recorder, RS): pulled time 66.0 vs 77.8 s per game (-15.2%, D45 FAIL); trailing-by-1 pulled share 0.599 vs 0.608 (PASS); first-pull medians 110 / 174 / 257 vs 120 / 185 / 255.5 s; re-pull share 0.272 vs 0.220; EN-against goals 0.345 vs 0.399 per game, EN-for 0.152 vs 0.171, EN attempts 2.83 for / 0.83 against per game.

G7 decomposition (RS): shootout share = tie rate x (1 - OT-goal share of tied games). Sim 0.2374 x 0.3412 = 0.0810; with the actual tie rate 0.2066 x 0.3412 = 0.0705 (+1.18 pp over actual); with the actual OT split 0.2374 x 0.2841 = 0.0675 (+0.88 pp). Of the +2.23 pp shootout excess about 1.2 pp is the OT split (65.9% of tied games end on an OT goal vs 71.6% actual in 2024-25; training pooled 67.6%, per season 64.6-69.9%; SE 2.7 pp: UNDERPOWERED, not an established defect) and about 1.0 pp the tie-rate excess. The tie-rate excess (+3.08 pp) equals the Lane H8a pull-on loop (0.2376 all games); their pull-off loop sat on the actual (0.2045): it enters with the 6v5 state (tying goals while pulled 0.069 vs 0.054 per game; upstream margin compression, INV-71), not with OT or the shootout. EN goals (-0.0545 per game) follow the pull-timing level (Lane H8a part, unchanged). The 3v3 level removed a compensating bias: with the old +5.4% 3v3 rate more OT goals were scored and the all-games shootout share was 0.0726, now 0.0760; the 3v3 rate itself is right, so the shootout gap needs the tie rate and the OT split, not the 3v3 level.

G2 grader note: the 3v3 line is labelled COMPENSATED (hazard level +2.98, remainder -2.59), because its hazard-level component reads the cached OLD A3g-c offline predictions (`results/shot_attempt_r3/fold2_haz_*.npy`), not the re-levelled table. With the re-levelled offline prediction the hazard component is +0.36% and the total +0.65%; the label is a grader artefact.

G1-G3 re-check (`results/end_game_otso_v1/gate_compare.csv`, cell by cell vs the Lane H8a pull-on and pull-off loops): G1 21 cells no status change (largest delta 1.1 min per game, the EN time vs pull-off; 0.011 vs pull-on); G3 24 / 56 cells no status change (max delta 0.13 / 0.03); G2 60 cells: 3v3 FAIL -> PASS (this lane); vs pull-off also 4v4 and the +1 score bucket PASS -> FAIL, identical in the H8a pull-on loop.

G5 / G6 first full read, **stage 7 absent** (the PM rules whether they gate), RS: G5 FAIL: P(total=4) 0.0994 vs 0.1151, P(6) 0.1246 vs 0.1357, P(7) 0.1752 vs 0.1562 outside 0.01; total SD ratio 1.034 and margin SD ratio 0.969 PASS; score correlation -0.045 vs -0.110 FAIL; KS p 0.89. G6 FAIL: home win 0.5377 vs 0.5625 (-2.5 pp, tolerance 1.5), home goal diff 0.219 vs 0.316 (tolerance 0.08).

**Decision (per the spec).** Stage 8 is NOT CONFIRMED-INCUMBENT: G7 fails on all three quantities. Decomposition: pull timing (EN goals; Lane H8a), the 6v5 tie excess (upstream, INV-71), a possibly-noise OT split (UNDERPOWERED). No fix applied inside the round. Part B passes its closed-loop gate (G2 3v3 +0.65%); the OT-goal share of tied games misses by 5.7 pp (limit 3 pp, UNDERPOWERED). Part C: S1 fails one underpowered check on fold 2, wired default off.

**Proposals for PM-owned text.** (1) LEARNINGS: a 3v3 level that is right on its own removed a compensating bias in the shootout share; G7 needs the tie rate fixed upstream before the OT split can be read; the OT-goal share moves 64.6-71.6% across seasons, so a 3 pp gate on 290 games is below its sampling error. (2) INV-35 can close on the 3v3 cell; the OT-goal share stays open, UNDERPOWERED. (3) The S1 success and round checks cannot discriminate at 77 shootouts; a pooled multi-season check would. (4) Grader: read the re-levelled offline 3v3 prediction in the G2 decomposition.

**Not done.** Delayed-penalty pulls (INV-70) and the pull-timing level (EG-R2): Lane H8a / PM. Faceoffs and rebounds: stage 7. S2 is not servable (the shooter order is chosen in game). The standalone report file `docs/tests/end_game_eg_r1_otso_2026-10-21.md` was not written (the Write tool refused report files in this session); this results block holds the narrative.
