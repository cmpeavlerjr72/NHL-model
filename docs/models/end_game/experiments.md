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
