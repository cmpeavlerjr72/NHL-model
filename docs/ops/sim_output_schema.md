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

## `results/<tag>/strength_toi.parquet` (optional; G1): one row per game x seed

Added 2026-10-15 by SS-R1 (Lane H). Strength is the penalty-derived skater count (a pulled goalie does not create a state; EN time is its own column). Seconds are played game seconds (shootout excluded).

| column | type | meaning |
|---|---|---|
| `game_id`, `seed` | int64, int32 | as in games.parquet |
| `toi_5v5_s`, `toi_4v4_s`, `toi_3v3_s` | int32 | seconds at equal strength 5/4/3 skaters a side |
| `toi_pp_home_s`, `toi_pp_away_s` | int32 | seconds with the home (away) team holding a skater advantage (= the other team's PK time) |
| `toi_5v3_s` | int32 | seconds at 5v3 or 3v5 (also inside the PP columns) |
| `toi_en_s` | int32 | seconds with a goalie pulled (0 until a goalie-pull model exists: STUB-DEPENDENT) |
| `played_s` | int32 | played seconds |
| `ppo_home`, `ppo_away` | int16 | PP opportunities: transitions into a skater advantage for that team |
| `pen_home`, `pen_away` | int16 | penalty-taking events (SS-R1 target definition; a coincidental stoppage counts once for each team) |
| `pim` | int32 | penalty minutes of strength penalties (incl. cancelled coincidental ones; misconducts excluded) |
| `n_{minor,double,major,coinc}_{home,away}` | int16 | penalty-taking events by type |
| `minors_{home,away}`, `minors_pp_ended_{home,away}` | int32 | minors assessed and minors ended early by a PP goal |
| `coinc_4v4` | int16 | coincidental stoppages that produced 4v4 (5v5 exception) |

`scripts/eval_gates.py` grades G1 from this file when present (`nhl_sim.eval.g1`); real G1 targets are the `gate == "G1"` rows of `gate_targets_{season}` built by `scripts/build_gate_reference.py` from the mechanics replay of the real penalty / goal / stoppage sequence.

## Gates and what they need

| gate | input | status today |
|---|---|---|
| G5 dispersion (P(total=k) cells, SD ratios, score correlation, KS) | games | graded |
| G6 home ice (win %, goal differential) | games | graded |
| G7 end game (regulation-tie, shootout rate; EN goals/game) | games (+ EN columns) | graded; EN needs `*_en_goals` |
| G9 accuracy (total/margin bias, calibration slope; overall only for now) | games | graded |
| G1 | strength_toi (above) | graded when present (SS-R1) |
| G2-G4, G8 | event-level (shot rates, xG, saves) and players | NEEDS-INSTRUMENTATION |
| G10 market leak screen | lines | out of scope |

Status rule per gate: any FAIL gives FAIL; else any missing input gives NEEDS-INSTRUMENTATION; else all checks under `min_cell_n` (games in the segment) gives UNDERPOWERED; else PASS. Tolerances only from `docs/gates.yaml`. Targets: `data/reference/gate_targets_{season}.parquet` (long format: season, segment all/RS/PO, gate, metric, key, value, n_games), built by `scripts/build_gate_reference.py`.
