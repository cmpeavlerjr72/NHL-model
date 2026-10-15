# Handoff

PM-owned. Newest block first.

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
