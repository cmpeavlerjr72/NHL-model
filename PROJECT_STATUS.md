# Project status

PM-owned. One SESSION block per PM session, newest first.

## SESSION 2026-10-15 (PM: Opus 5.5)

- Project created. Methodology ported from CBB-clean-sheet and cfb-props-sim (ARCHITECTURE_DECISIONS D1-D4).
- User rule: no Fable anywhere; PM on Opus, workers Opus/Sonnet/Haiku with explicit model on every call (D2).
- Phase P0 started. Lanes dispatched: A (Sonnet) NHL API ingest + data audit; B (Sonnet) lines / props / goalie-confirmation source audit.
- User approved GitHub remote (pushed, verified), HF dataset `mvpeav/nhl-sim-data` (created private) and AWS (D5).
- Lanes A-E all reported and their work was reviewed. P0 closed: INV-1/2/3/8/10/11/14/15. Gate scaffolding is in (INV-17).
- Control R1 ruled: A0 is the yardstick, and its failing gates set the event engine's bar (D9, L17).
- Next session: P2 kickoff (INV-22).
