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
