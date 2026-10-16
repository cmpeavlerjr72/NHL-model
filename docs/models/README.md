# Models index

Every sub-model gets `docs/models/<model>/{model,features,experiments}.md` per `DOCUMENTATION_STANDARD.md`. Status changes go to `change_ledger.md` in the same commit.

Status vocabulary: SHIPPED / TESTING / BUILDING / VALIDATED-PENDING-SHIP-ACTION / REFUTED / CONFIRMED-INCUMBENT / OPEN / DEFERRED / BANKED.

| Model | Cascade stage | Status | Doc |
|---|---|---|---|
| control | yardstick | CONFIRMED-INCUMBENT (A0, D9) | [model](control/model.md) |
| strength_state | 1 | CONFIRMED-INCUMBENT (provisional, H3''-LC2+T2, D18; INV-34 open) | [model](strength_state/model.md) |
| deployment | 2 | OPEN | - |
| shot_attempt | 3 | CONFIRMED-INCUMBENT (provisional, A3g-c, D20; 3v3 to stage 8, INV-35) | [experiments](shot_attempt/experiments.md) |
| shot_attribute | 4 | BUILDING (SL-R6 failed, D39; SL-R7 granted, D40; L0s engine STAND-IN) | [experiments](shot_attribute/experiments.md) |
| block | 5a | BUILDING (team ratings parked, D34; B0 engine STAND-IN) | [experiments](block/experiments.md) |
| miss | 5b | BUILDING (team terms parked, D37; S0t STAND-IN, not yet in engine) | [experiments](miss/experiments.md) |
| goal | 6 | CONFIRMED-INCUMBENT (provisional, C1s as-of goalie scale, D40; engine wiring INV-60) | [experiments](goal/experiments.md) |
| faceoff_stoppage | 7 | OPEN | - |
| end_game (pull / OT / SO) | 8 | OPEN | - |
