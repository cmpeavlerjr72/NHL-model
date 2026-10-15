# Sim output schema (gate contract), 2026-10-15

Any engine (Control, event engine) writes `results/<tag>/` so that `scripts/eval_gates.py --results results/<tag> --season <id>` can grade it. Reader/validator: `nhl_sim.eval.gates.load_sim_output`.

## `results/<tag>/games.parquet` (required): one row per game x seed

| column | type | meaning |
|---|---|---|
| `game_id` | int64 | NHL game id |
| `seed` | int32 | simulation index (0..n_seeds-1) |
| `home_goals`, `away_goals` | int16 | goals through regulation + OT, empty-net goals included, shootout bonus goal EXCLUDED (so an SO game has tied goals) |
| `end_state` | str | `REG`, `OT` or `SO` |
| `home_win` | bool | home team wins the game (goal winner for REG/OT, shootout winner for SO) |
| `home_en_goals`, `away_en_goals` | int16, optional | empty-net goals scored by each side (inside `*_goals`). Absent for the reduced-form Control; G7 EN check then reports NEEDS-INSTRUMENTATION |

Validation (reader raises): required columns present; `end_state` in {REG, OT, SO}; SO rows have tied goals; REG/OT rows are untied with `home_win` equal to `home_goals > away_goals`.
Real finals use the identical definition (`nhl_sim.eval.gates.real_games`: `verified_finals_v2` score minus the SO bonus goal).

## `results/<tag>/run_meta.json` (recommended)

`engine_tag`, `fold`, `season`, `n_seeds`, `sealed_touched` (must be false or absent; true makes the grader refuse), free-form notes (for example `oracle_goalie: true`).

## `results/<tag>/players.parquet` (optional, not yet consumed): one row per game x seed x player

`game_id, seed, player_id, team ('home'|'away'), position, toi_s, sog, goals, assists, saves` (goalies carry `saves`, skaters `sog`). G8 needs it (NEEDS-INSTRUMENTATION until present).

## Gates and what they need

| gate | input | status today |
|---|---|---|
| G5 dispersion (P(total=k) cells, SD ratios, score correlation, KS) | games | graded |
| G6 home ice (win %, goal differential) | games | graded |
| G7 end game (regulation-tie, shootout rate; EN goals/game) | games (+ EN columns) | graded; EN needs `*_en_goals` |
| G9 accuracy (total/margin bias, calibration slope; overall only for now) | games | graded |
| G1-G4, G8 | event-level (strength-state TOI, shot rates, xG, saves) and players | NEEDS-INSTRUMENTATION |
| G10 market leak screen | lines | out of scope |

Status rule per gate: any FAIL gives FAIL; else any missing input gives NEEDS-INSTRUMENTATION; else all checks under `min_cell_n` (games in the segment) gives UNDERPOWERED; else PASS. Tolerances only from `docs/gates.yaml`. Targets: `data/reference/gate_targets_{season}.parquet` (long format: season, segment all/RS/PO, gate, metric, key, value, n_games), built by `scripts/build_gate_reference.py`.
