# Handoff

PM-owned. Newest block first.

## SUMMARY FOR USER 2026-10-15

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
- none yet
- PM (2026-10-15): two worker-written User-Agent strings contained the user's email and were sent to NHL API, Daily Faceoff, Kalshi and DKeX for about 1.5 hours. Removed; the string is generic now. The old string remains in git history (private repo).
