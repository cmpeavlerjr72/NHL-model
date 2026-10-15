# SS-R1 strength-state / penalty bake-off, full report (Lane H, INV-22), 2026-10-15

Spec: `docs/models/strength_state/experiments.md` SS-R1 (commit 976de05), run as written. Worker: Opus. Clock: start 18:43 EDT, last compute 19:40 EDT. Detail files:
- `docs/tests/strength_state_ss_r1_grade_2026-10-15.md`: blind table, reveal, decision rule, all secondary tables.
- `docs/tests/gates_g1_ss_r1_g1_H3_2026-10-15.md` and `..._H2_...`: G1 at 200 seeds, by segment and per team.

## Headline

1. **Engine core.** `src/nhl_sim/engine/` holds GameState, the vectorised PenaltyBox, RuleEra flags, counter-based RNG streams on (seed, game_id, family), the lookup-table sim loop and the replay. There are 26 offline tests in `tests/engine/` and the mapping test in `tests/test_penalty_map.py`; the full suite is 85 passed.
2. **Replay check, 4,201 fold-1 games (2021-22 to 2023-24), 15.3 M seconds.**
   - Gap-aware agreement is **99.993%**, which passes the 99% bar. The random 300-game sample gives 99.995%.
   - Strict carry-forward agreement is **98.13%**. Of the strict misses, 99.65% fall inside ambiguous gaps: two consecutive pbp events with different codes, where the state change cannot be dated, for example a penalty expiring between events. 5.0% of seconds are ambiguous.
   - Reading: the pbp situationCode is event-sampled, so strict carry-forward is not a valid second-level truth. I report both numbers. The PM decides which one the spec's ">= 99%" binds.
3. **Bake-off (fold 2, 1,398 games, 9,270 events).**
   - Hazard: H3 > H2 > H1 > H0, and every step is significant. **Offline winner H3.**
   - Type: **T1** wins.
4. **G1 closed loop, 200 seeds.**
   - H3 passes every toleranced overall cell. PP opportunities are +0.149 per team-game against a tolerance of 0.15; the 50-seed slice was +0.156, a FAIL. This pass is marginal and **compensated** (see Findings).
   - On the RS segment, H3 FAILS PP opportunities (+0.166).
   - H2 passes overall (+0.101) and on RS (+0.119).

## Step 1: engine mechanics (unit-tested)

The hand-built sequences cover:
- minors, which carry across periods;
- a PP goal ending a minor, while a shorthanded goal does not;
- majors, which are never ended by a goal;
- double minors: a goal in the first half restarts the second minor, a goal in the second half ends it;
- the exact-expiry-second convention;
- the 3-skater floor with a stacked queue, and a queued penalty starting after a PP goal;
- a PP goal skipping a major;
- coincidental minors: 4v4 under the 5v5 exception, not ended by a goal, offsetting when not at full strength;
- consecutive service by one player, majors first;
- 3v3 OT: 4v3, 5v3, and holding the extra skater until the next stoppage after an expiry;
- coincidental expiries with no hold;
- carry-over of a regulation penalty into OT;
- playoff OT;
- end states;
- dead sims not ticking;
- box overflow;
- era lookup;
- RNG purity and pairing;
- sim-loop smoke tests.

## Step 2: replay, disagreements and fixes

Rule gaps found and fixed in the engine (no game special-casing):
- **(a) Consecutive service.** Several penalties on one player are served one after another, not concurrently. One example is 2023020140: unsportsmanlike plus hooking on one player gave 5v4 for 4 minutes, where the engine first produced 5v3.
- **(b) OT hold.** The hold now applies only to a team that was outnumbered. Coincidental expiries at 3v3 no longer create a false 4v4 (2022021163).
- **(c) Expiry timing convention.** A penalty due at second s expires before that second's events. Disagreeing seconds: 1,084 with this convention, 1,588 with the alternative. Boundary goals go both ways in the data (2021030242 against 2023020479), so this is a timing-resolution ambiguity, not a rule.

Residual disagreements: 35 runs, 1,084 seconds.

| class | runs | seconds |
|---|---|---|
| other | 27 | 869 |
| OT | 5 | 117 |
| goalie pull next to the gap | 3 | 98 |

Two of the remaining runs were diagnosed:
- 2023020698: a minor and a major at one stoppage behave in pbp like a 2-minute single PP. This looks like a data error or a rescinded major, so it was left as is.
- 2021030242: an exact-boundary goal.

The other runs were not diagnosed one by one. 10 games are below 99% gap-aware agreement.

## Step 3: tables

Tables are in `data/processed/strength_state/*_v1*`, about 330k hazard rows per season. The type rows contain 31,853 minor, 7,238 coincidental, 515 double and 149 major events. Non-target tallies, per season:

| season | misconduct | game misconduct | penalty shot |
|---|---|---|---|
| 2021-22 | 200 | 40 | 36 |
| 2022-23 | 270 | 48 | 55 |
| 2023-24 | 269 | 54 | 50 |
| 2024-25 | 190 | 33 | 32 |

Two further notes:
- The ratings writer enforces `created_at < puck_drop`, and every row passed.
- The mapping test fails on any unmapped type, minutes or description combination.

Feature documentation is in `docs/models/strength_state/features.md`.

**Incident, caught before any fold-2 number existed.** The first build cut rows into 60 s chunks relative to each run's start, and H3 used the row-midpoint clock. Rows end at the whistle of their event, so that clock leaked row length. For example, 60 s chunks starting at a period start have midpoint 30 and y = 0 by construction. The rows were rebuilt on the fixed game-minute grid with a per-row constant minute clock, and fold-1 tuning was redone. All GLM arm differences are invariant to whistle cuts, because their features are constant within constant-state stretches.

## Step 4: bake-off

Frozen on fold 1:
- Rating carry-over w = 0.7 and prior strength 1,800 team-minutes. This is the corner of the pre-registered grid, and the grid was not extended.
- LightGBM: num_leaves 7, min_data_in_leaf 800, 490 rounds.

Fold 2, log-likelihood per game vs H0:

| arm | LL/game vs H0 | predicted events (actual 9,270) |
|---|---|---|
| H0 | 0 | 10,229 |
| H1 | +0.052 (SE 0.010) | 10,229 |
| H2 | +0.510 (SE 0.032) | 10,178 |
| H3 | +0.932 (SE 0.038) | 10,227 |

- H3 vs H2: +0.422 (SE 0.032). The H3 seed floor is 0.0067. Every comparison clears 2 SE, and the H3 comparisons also clear the seed floor.
- Type: T1 minus T0 is +0.046 nats/game (SE 0.012).

Secondary evidence for H3 (grade file):
- Responsiveness slope by own taken-rating quintile is 0.85; by opponent drawn-rating quintile it is 1.10. Both slope.
- The per-team predicted-actual correlation is 0.84, with all 32 teams UNDERPOWERED.
- Every segment over-predicts by about 10% (level drift, Findings 1).
- Team-game calibration by decile is inverted when evaluated on the real path. This is a path-conditioning effect (PK time and positive penalty differential lower the hazard after penalties), and the G1 dispersion check covers it.

## Step 5: G1 (fold 2, 200 seeds, 4 x ~250 s per arm locally; seed 100 vs 200 shifts <= 0.01)

| cell | real | H3 sim | H3 status | H2 sim | H2 status |
|---|---|---|---|---|---|
| TOI 5v5 (min/game) | 50.50 | 49.97 | PASS | 50.09 | PASS |
| TOI PP total | 9.03 | 9.38 | PASS | 9.26 | PASS |
| TOI 4v4 | 0.73 | 0.85 | PASS | 0.85 | PASS |
| TOI 5v3/3v5 | 0.146 | 0.160 | PASS | 0.160 | PASS |
| TOI 3v3 | 0.53 | 0.42 | STUB-DEPENDENT (OT frequency from stub goals) | 0.42 | STUB-DEPENDENT |
| TOI EN | 1.06 | 0 | STUB-DEPENDENT (no goalie pull) | 0 | STUB-DEPENDENT |
| PP opps / team-game, mean | 2.584 | 2.733 | PASS (+0.149, tol 0.15) | 2.686 | PASS |
| PP opps / team-game, SD | 1.267 | 1.394 | PASS | 1.381 | PASS |
| PP opps mean, RS segment | 2.564 | 2.730 | FAIL | 2.683 | PASS |
| PIM / game | 15.13 | 15.79 | NO-TOLERANCE | 15.45 | NO-TOLERANCE |
| share of minors ended by a PP goal | 0.214 | 0.202 | STUB-DEPENDENT | 0.203 | STUB-DEPENDENT |
| P(k), per team (corr 0.66 / 0.69) | | | NO-TOLERANCE / UNDERPOWERED | | |

PP/PK and 5v5 TOI are partly stub-driven, because PP minors end on stub goals. Score-state terms are exercised by the stub goals but not validated; they are re-gated at stage 6.

**Literal rule outcome.** The winner H3 passes overall G1, so H3 is selected (provisional, status TESTING).

## Findings (proposed LEARNINGS text for the PM)

1. **Season-level drift.** 2024-25 had 3.32 penalty-taking events per team-game against 3.61 in 2023-24 (-8%). A season feature mapped to the last training season over-predicts by +10% in every arm.
2. **Delayed-penalty reverse causality.** 6.4% of events have pre-event state 'other' (goalie pulled), and about 80% of those follow a delayed-penalty signal against the penalised team. The goalie pull is caused by the penalty itself. The sim never visits 'other', so it loses about 6% of events.
3. **The G1 PP-opportunity pass is compensated.** Findings 1 and 2 partly cancel (+10% and about -6%). Under the guardrail "a passing aggregate over a biased sub-model is a failure", I recommend not confirming H3. The next experiment should be SS-R2, pre-registered with both fixes: take the pre-event state at the delayed-penalty signal, and add an as-of in-season league level.

## Proposed gates.yaml text (PM-owned)

`g1_pim_per_game: 0.75`, `g1_pp_goal_share_pp: 2.0`, `g1_ppo_pk_pp: 1.5`. These are placeholders for PIM per game, the share of minors ended by a PP goal, and P(PP opps = k) cells, which have no tolerance today.

## Schema

`docs/ops/sim_output_schema.md` adds `strength_toi.parquet`. `scripts/eval_gates.py` grades G1 from it, and `build_gate_reference.py` adds G1 rows (G5-G9 rows unchanged, verified).

## Resume / reproduce

```
.venv/Scripts/python.exe scripts/diag_strength_state_replay.py
.venv/Scripts/python.exe scripts/build_strength_state_tables.py
.venv/Scripts/python.exe scripts/build_gate_reference.py 20242025
.venv/Scripts/python.exe scripts/train_strength_state_v1.py tune
.venv/Scripts/python.exe scripts/train_strength_state_v1.py fold2
.venv/Scripts/python.exe scripts/grade_strength_state.py
.venv/Scripts/python.exe scripts/run_strength_state_g1.py --arm H3 --seeds 200
.venv/Scripts/python.exe scripts/run_strength_state_g1.py --arm H2 --seeds 200
```

Nothing is PARTIAL. AWS was not used: the PM's Lane O note arrived after the G1 runs (about 17 min each, run in parallel) had finished locally.
