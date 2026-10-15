# Investigate board

PM-owned. Items are never deleted. Closing an item requires a PROOF block: what changed, before/after numbers, and why the fix logic is sound. Status: OPEN / ASSIGNED(<lane>) / BLOCKED / CLOSED / DEFERRED.

| ID | Title | Phase | Status | Owner | Notes |
|---|---|---|---|---|---|
| INV-1 | NHL API ingest 2021-22 -> live: schedule, pbp, shifts, boxscores, rosters (raw cache) | P0 | CLOSED | Sonnet | PROOF: 7,100 final games x (pbp, box, shifts), 0 failures, 22 tests pass (2e0e420); raw on HF |
| INV-2 | Data audit: coverage, event vocabulary, coordinates, shift coverage, verified finals | P0 | CLOSED | Sonnet | PROOF: `docs/tests/data_audit_nhl_api_2026-10-15.md` (2e0e420). Residuals split out to INV-14..16 |
| INV-14 | Independent (non-NHL) finals check, ESPN | P0 | CLOSED | Sonnet | PROOF: ESPN scoreboard, 5,706/5,706 unsealed games match score + end state (202e4dc); `verified_finals_v2` |
| INV-15 | 2025-26 seal enforced in code at read time | P0 | CLOSED | Sonnet | PROOF: `src/nhl_sim/data/seal.py` + single loader; 14 tests pass (67bc87c) |
| INV-16 | Shift-chart gaps (57 games 2024-25 post 04-08; 48 early 2026-27) + weekly resumable pull | P0 | OPEN | | re-try is automatic; needs scheduling |
| INV-17 | Gate reference builder + eval_gates + sim output schema | P1 | CLOSED | Sonnet | PROOF: schema doc, gate_targets for 5 seasons, eval_gates.py, 7 tests (dabdee1); G1-G4/G8 NEEDS-INSTRUMENTATION until the event engine |
| INV-18 | 2021-22 shootout typing | P0 | OPEN | | audit open item |
| INV-3 | Lines-source audit: historical closes, Kalshi NHL, DKeX (HAR), goalie confirmations, third-party terms | P0 | CLOSED | Sonnet | PROOF: `docs/ops/lines_sources_audit_2026-10-15.md`, register `docs/ops/data_sources.md` (55dae7f); decisions D6-D8 |
| INV-4 | GitHub remote + HF dataset for bulk data | P0 | CLOSED | PM | PROOF: remote `cmpeavlerjr72/NHL-model` push verified via ls-remote (eb3d750); HF dataset `mvpeav/nhl-sim-data` created private=True; AWS approved (D5) |
| INV-9 | `scripts/hf_sync_data.py` (port from CBB) for data/raw + results | P0 | CLOSED | Sonnet->PM | PROOF: port 147e3cd (12 tests, live round-trip byte-identical); first raw + results push 2026-10-15, `status` = 0 files outstanding |
| INV-5 | Gate reference builder + eval_gates.py | P1 | CLOSED | PM | merged into INV-17 |
| INV-6 | Control engine (team-rate yardstick) bake-off | P1 | CLOSED | Sonnet | PROOF: `docs/tests/control_r1_2026-10-15.md` (56ff992); A0 adopted as yardstick, D9 |
| INV-7 | Seed-noise study | P1 | OPEN | | after Control |
| INV-8 | Starting-goalie pregame source with timestamps (honest backtests) | P0/P4 | CLOSED | Sonnet | PROOF: Daily Faceoff logger live, 22 rows/run with status + fetched_at (8d552ba); history = oracle goalie (D8) |
| INV-10 | Forward loggers (goalies, Kalshi, DKeX) + Task Scheduler | P0 | CLOSED | Sonnet | PROOF: `NHL-Model-live-log` fired 15:00 and 15:30, LastTaskResult 0; ~3.9k Kalshi + ~5.85k DKeX rows/run; 5 tests pass (8d552ba). PM removed user email from User-Agents |
| INV-11 | ESPN pickcenter coverage, all weeks 2023-24 and 2024-25 | P0 | CLOSED | Sonnet | PROOF: `docs/tests/espn_lines_coverage_2026-10-15.md` (f56669e): 2023-24 single Unibet line 100%, 2024-25 0%, 2025-26 DK open+close 71% |
| INV-19 | Historical closes for 2024-25 (fold 2) | P1 | CLOSED | Sonnet x2 + Opus | PROOF: ESPN core `/odds` 2024-25 open+close ML/PL/total on 73/73 sampled games (2a28c22), PM spot-check; DRatings second source (ece8f09); D10 |
| INV-20 | Kalshi logger rows include futures series; filter to game/prop markets downstream | P4 | OPEN | | |
| INV-12 | Kalshi fee schedule verification (fee PDF 429'd) | P4 | OPEN | | CFB figure 0.07*P*(1-P) unverified for NHL |
| INV-13 | Odds API purchase decision | P1 | DEFERRED | user | D7: revisit after Control engine |
| INV-21 | Control R2: extend edge-hit grids (lambda, w, goalie kappa, rest ridge); a dependence family allowing negative correlation / excess ties | P1 | DEFERRED | | D9 |
| INV-22 | P2 kickoff: event-engine GameState + strength-state/penalty sub-model spec (Opus worker, engine core) | P2 | IN PROGRESS | Opus (Lane H) | SS-R1 pre-registered in docs/models/strength_state/experiments.md; brief docs/briefs/lane_H_strength_state_2026-10-15.md |
| INV-23 | Lines ingest: ESPN core 2023-24 + 2024-25 (pregame item only); DRatings cross-check | P1 | CLOSED | Sonnet | PROOF: 2,798 events, 0 failures, 1,592 live items dropped, `lines_espn_core_v1.parquet` (55f86d6). Cross-check ML PASS, PL 96.4%, total FAIL (54.5%), ruled in D11 |
| INV-24 | SBRO 2021-23 + full DRatings pull 2021-25 (consensus total line source) | P1 | IN PROGRESS | Sonnet (Lane I) | D10/D11; about 70 min/season at 3 s/request, run unattended; brief docs/briefs/lane_I_lines_pulls_2026-10-15.md |
| INV-25 | Price-adjusted totals agreement test ESPN BET vs DRatings (no-vig P(over) at a common line); explain the '-68' mean price | P1 | OPEN | | pre-register before any totals CLV (D11) |
