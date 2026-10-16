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
| INV-22 | P2 kickoff: event-engine GameState + strength-state/penalty sub-model spec (Opus worker, engine core) | P2 | CLOSED | Opus (Lane H) | PROOF: engine core + 26 rule tests, replay 99.993% gap-aware; SS-R1 graded (1b3abfe); H3 not confirmed (compensated G1), D12 |
| INV-26 | SS-R2: penalty hazard with delayed-penalty state + in-season league level (pre-registered, D12) | P2 | CLOSED | Opus (Lane H2) | PROOF: 9b14319; H3' offline winner, all arms fail bias checks (Jan +11%), G1 not run; D13 |
| INV-27 | SS-R3: season-phase profile + de-seasonalised level; G1 if bias checks pass (D13) | P2 | CLOSED | Sonnet (Lane H3) | PROOF: f1e6399; level fixed (+1.45%), fold-1 months pass, fold-2 Jan +8.6% narrow fail; D14 accepts H3'' conditional on G1 |
| INV-28 | Closed-loop G1 for H3'' (+ H2'' comparator): engine offset lookup, parity test, clean-pass decomposition (D14) | P2 | CLOSED | Sonnet (Lane H4) | PROOF: b513691; RS G1 PASS, CLEAN; D15 provisional incumbent |
| INV-29 | Penalty rating over-response (closed-loop quintile spread 1.5-1.8x actual): pre-registered shrinkage/interaction fix, fold-1 responsiveness check; blocks team-level PP use (D15) | P3-blocker | IN PROGRESS | Sonnet (Lane P2) | SS-R4 stopped (ratings fine, d01e082); locus = type model; SS-R5 brief docs/briefs/lane_P2_penalty_type_2026-10-15.md |
| INV-30 | Stage 3 kickoff: shot-attempt generation spec + bake-off (score effects pre-event, strength state from stage-1 engine) | P2 | CLOSED | Opus (Lane S) | PROOF: d379f58/c9542c8; no arm eligible (level -5%), PM spec defect found; D16 |
| INV-31 | SA-R2 (LC-1 level, strength-group levels, G2) then SS-R3c (stage-1 re-level, G1) (D16) | P2 | IN PROGRESS | Opus (Lane S, continued) | brief docs/briefs/lane_S2_level_fix_2026-10-15.md |
| INV-23 | Lines ingest: ESPN core 2023-24 + 2024-25 (pregame item only); DRatings cross-check | P1 | CLOSED | Sonnet | PROOF: 2,798 events, 0 failures, 1,592 live items dropped, `lines_espn_core_v1.parquet` (55f86d6). Cross-check ML PASS, PL 96.4%, total FAIL (54.5%), ruled in D11 |
| INV-24 | SBRO 2021-23 + full DRatings pull 2021-25 (consensus total line source) | P1 | IN PROGRESS | Sonnet (Lane I) | D10/D11; about 70 min/season at 3 s/request, run unattended; brief docs/briefs/lane_I_lines_pulls_2026-10-15.md |
| INV-25 | Price-adjusted totals agreement test ESPN BET vs DRatings (no-vig P(over) at a common line); explain the '-68' mean price | P1 | OPEN | | pre-register before any totals CLV (D11) |
