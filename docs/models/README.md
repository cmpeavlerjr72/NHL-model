# Models index

Every sub-model gets `docs/models/<model>/{model,features,experiments}.md` per `DOCUMENTATION_STANDARD.md`. Status changes go to `change_ledger.md` in the same commit.

Status vocabulary: SHIPPED / TESTING / BUILDING / VALIDATED-PENDING-SHIP-ACTION / REFUTED / CONFIRMED-INCUMBENT / OPEN / DEFERRED / BANKED.

| Model | Cascade stage | Status | Doc |
|---|---|---|---|
| control | yardstick | CONFIRMED-INCUMBENT (A0, D9) | [model](control/model.md) |
| strength_state | 1 | CONFIRMED-INCUMBENT (provisional, H3''-LC2+T2, D18; INV-34 open) | [model](strength_state/model.md) |
| deployment | 2 | OPEN | - |
| shot_attempt | 3 | CONFIRMED-INCUMBENT (provisional, A3g-c, D20; 3v3 to stage 8, INV-35) | [experiments](shot_attempt/experiments.md) |
| shot_attribute | 4 | BUILDING (SL-R6 running; L0s engine STAND-IN, D32) | [experiments](shot_attribute/experiments.md) |
| block | 5a | BUILDING (SB-R4 running; B0 engine STAND-IN, D32) | [experiments](block/experiments.md) |
| miss | 5b | BUILDING (SM-R1 pre-registered) | [experiments](miss/experiments.md) |
| shot_attributes | 4 | OPEN | - |
| attempt_outcome | 5 | OPEN | - |
| goal_given_sog | 6 | OPEN | - |
| faceoff_stoppage | 7 | OPEN | - |
| end_game (pull / OT / SO) | 8 | OPEN | - |
