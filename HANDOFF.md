# Handoff

PM-owned. Newest block first.

## SUMMARY FOR USER 2026-10-15 (evening session, 18:40-22:40)

**Headline:** P2 is under way. The engine core is built, and stage 1 (penalties / strength state) is a provisional incumbent: H3'' (a LightGBM penalty hazard) plus the T2 type model. Stage 3 (shot attempts) has a leading arm, A3g, that passes its core checks; two thin strength states, 4v4 and 3v3, still fail. A PM spec error in the league-level construction was found and fixed for attempts (D16).

**Decisions this session**

| # | Decision |
|---|---|
| D12 | SS-R1 is not confirmed. Its G1 pass came from two biases cancelling (season-level drift +10%, delayed penalties -6%) |
| D13 | SS-R2 fixed the delayed-penalty state, but every arm failed the bias checks (January +11%) |
| D14 | SS-R3 added a season-phase profile. H3'' was accepted with the January 2025 bias listed, conditional on a clean G1 |
| D15 | G1 passed CLEAN, so H3'' is the provisional stage-1 incumbent. Team PP use is blocked by INV-29 (the sim over-responds to team ratings) |
| D16 | PM spec error: a league level expressed as a ratio to last season is biased under a trend. LC-1 (an absolute level) replaces it |
| D17 | SA-R2: A3g leads stage 3, but G2 fails at 4v4/3v3. LC-1 fails its parity check for penalties, so stage 1 stays on the old level, with that listed |

Also this session:
- SS-R4: the team ratings are fine.
- SS-R5: the type model T2 replaces T1. It cuts the team-PP over-response by about 2/3, but the drawn-rating spread ratio of 1.25 still fails the 0.8-1.2 band.
- The rules changed at your request: Opus workers are used where the work needs them, with no daily cap. AWS goes through an operator lane (Lane O), and any step projected over 15 min files a box request.

**Needs you**
- Stay logged in to Windows tonight. The DRatings pull (`NHL-Model-dratings-pull`) should finish around midnight, then build its table and unregister itself. The live loggers also need you logged in.

**Open items, in order**
1. INV-32, SA-R3: fix the 4v4/3v3 attempt hazard, merge the T2 engine sibling into `sim.py` behind a flag, and re-run G2 on H3''+T2.
2. INV-33: LC-2 penalty level. Run the parity check first, then re-run SS-R3c and re-measure INV-29.
3. INV-24 close-out: commit the final `lines_dratings_v1.parquet`, push raw to HF, and decide on the 38 SBRO-vs-DRatings puck-line sign mismatches. Then INV-25.
4. INV-16 (weekly pull schedule) and INV-21 (Control R2), both deferred.

**AWS:** the operator chain is built and was smoke-tested on a c7i.large (pytest in 93 s from launch). No requests came in tonight, because every run finished locally in about 17 min or less. Spend was $0.004 of the $60 cap, and zero instances are running (checked 21:51 and by the PM at 21:42). See `docs/ops/aws_operator_O_2026-10-15.md`.

**Worker incidents (disclosed)**
- Lane I stopped Lane H's replay diagnostic (PID 15152) without checking its command line. The replay was re-run by Lane P, and the reported numbers were confirmed exactly (99.993% / 98.134%). A process-control rule is now in the worker rules.
- Lane H4 ran a projected 17-min job locally instead of filing a box request. It cost nothing, and the rule is now "file before launching".
- PM: a spec error in SS-R2's level definition (D16), caught by Lane S.
- Several pushes printed "fatal: Key not valid for use in specified state" (a Windows credential-manager warning). Every push was verified with `git ls-remote`.


## SUMMARY FOR USER 2026-10-15 (end of session)

**Headline:** P0 is done and P1 has its yardstick. 7,100 games are ingested, audited and independently verified, live goalie and market logging is scheduled, and the Control yardstick is set (A0, D9). Next is the P2 event engine.

**Decisions this session**

| # | Decision |
|---|---|
| D1-D2 | CBB methodology; Opus PM, no Fable workers |
| D3 | Event-level engine with a Control yardstick |
| D4, D7 | Lines venues are Kalshi, DKeX and historical closes; no paid odds yet |
| D5 | GitHub, HF `mvpeav/nhl-sim-data`, AWS with a $60 cap per session |
| D6 | NHL API stays primary, for personal research only |
| D8 | Forward loggers; backtests labelled "oracle goalie" |
| D9 | Control A0 is the yardstick; the gates it fails are the event engine's bar |

**Late-session add (16:47-17:20):** deep lines hunt (F1/F2 Sonnet, F3 Opus). Free open/close lines now exist for every season (D10). The ESPN core 2023-25 ingest is done (D11). The ML cross-check vs DRatings passes; totals differ by ESPN BET's choice of main line, so DRatings is the consensus total source.

**Needs you**
- Keep Windows logged in during game days so `NHL-Model-live-log` runs (09:00-23:30, every 30 min).
- Later, for INV-19: decide on a fold-2 (2024-25) closing-line source once the market scorecard matters.

**Open items, in order**
1. INV-22: P2 kickoff in a FRESH PM session. Spec GameState and the strength-state/penalty sub-model, with an Opus worker for the engine core.
2. INV-24: full DRatings + SBRO pulls, run unattended (about 70 min/season), then INV-25.
3. INV-16: schedule the weekly resumable `pull_games.py`, which re-tries the shift-chart gaps.
4. INV-21: Control R2 (deferred).

**Worker incidents (disclosed)**
- Lane A: one audit run hung (missing `__main__` guard); the worker killed only its own process tree. The blocked-shot owner was mis-assigned at first and rebuilt before the audit.
- Lane D: the first ESPN launch got 403 (User-Agent); the worker stopped only its own processes and cached nothing.
- Lane E: the A4 arm blew up numerically on the first fold-2 pass. The repair was chosen on fold 1 before any fold-2 scores existed, and it is disclosed in the R1 doc.
- PM: two worker-written User-Agent strings contained the user's email and were sent to NHL API, Daily Faceoff, Kalshi and DKeX for about 1.5 hours. Removed; the string is generic now. The old string remains in git history (private repo).

## (earlier, superseded) SUMMARY FOR USER 2026-10-15

**Headline:** NHL-Model scaffolded with the CBB rules (Opus PM, no Fable). Two P0 lanes running: data ingest/audit and lines-source audit.

**Done with you**
- GitHub remote `cmpeavlerjr72/NHL-model` connected, pushed and verified.
- HF dataset `mvpeav/nhl-sim-data` created (private); AWS approved, $60/session cap confirmed.

**Needs you**
- Possibly a fresh DraftKings Predictions HAR capture (Lane B will say which pages).

**Open items, in order**
1. Lane A report -> PM reviews audit, writes gate reference / Control engine specs.
2. Lane B report -> PM decides lines sources (D4 follow-up).

**Worker incidents (disclosed)**
- PM (2026-10-15): two worker-written User-Agent strings contained the user's email and were sent to NHL API, Daily Faceoff, Kalshi and DKeX for about 1.5 hours. Removed; the string is generic now. The old string remains in git history (private repo).
