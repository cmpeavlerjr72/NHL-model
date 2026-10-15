# Investigate board

PM-owned. Items are never deleted. Closing an item requires a PROOF block: what changed, before/after numbers, and why the fix logic is sound. Status: OPEN / ASSIGNED(<lane>) / BLOCKED / CLOSED / DEFERRED.

| ID | Title | Phase | Status | Owner | Notes |
|---|---|---|---|---|---|
| INV-1 | NHL API ingest 2021-22 -> live: schedule, pbp, shifts, boxscores, rosters (raw cache) | P0 | ASSIGNED(A) | Sonnet | brief `docs/briefs/lane_A_ingest_2026-10-15.md` |
| INV-2 | Data audit: coverage, event vocabulary, coordinates, shift coverage, verified finals | P0 | ASSIGNED(A) | Sonnet | same brief, chained |
| INV-3 | Lines-source audit: historical closes, Kalshi NHL, DKeX (HAR), goalie confirmations, third-party terms | P0 | CLOSED | Sonnet | PROOF: `docs/ops/lines_sources_audit_2026-10-15.md`, register `docs/ops/data_sources.md` (55dae7f); decisions D6-D8 |
| INV-4 | GitHub remote + HF dataset for bulk data | P0 | CLOSED | PM | PROOF: remote `cmpeavlerjr72/NHL-model` push verified via ls-remote (eb3d750); HF dataset `mvpeav/nhl-sim-data` created private=True; AWS approved (D5) |
| INV-9 | `scripts/hf_sync_data.py` (port from CBB) for data/raw + results | P0 | ASSIGNED(PM) | Sonnet->PM | PORT DONE 147e3cd: 12 offline tests pass, live probe push/pull/delete byte-identical; remaining: PM runs first raw push after Lane A |
| INV-5 | Gate reference builder + eval_gates.py | P1 | OPEN | | after INV-2 |
| INV-6 | Control engine (team-rate yardstick) bake-off spec | P1 | OPEN | | PM writes spec after INV-2 |
| INV-7 | Seed-noise study | P1 | OPEN | | after Control |
| INV-8 | Starting-goalie pregame source with timestamps (honest backtests) | P0/P4 | ASSIGNED(D) | Sonnet | Daily Faceoff forward logger; history = oracle goalie (D8) |
| INV-10 | Forward loggers (goalies, Kalshi, DKeX) + Task Scheduler | P0 | ASSIGNED(D) | Sonnet | brief `docs/briefs/lane_D_loggers_2026-10-15.md` |
| INV-11 | ESPN pickcenter coverage, all weeks 2023-24 and 2024-25 | P0 | ASSIGNED(D) | Sonnet | chained in lane D |
| INV-12 | Kalshi fee schedule verification (fee PDF 429'd) | P4 | OPEN | | CFB figure 0.07*P*(1-P) unverified for NHL |
| INV-13 | Odds API purchase decision | P1 | DEFERRED | user | D7: revisit after Control engine |
