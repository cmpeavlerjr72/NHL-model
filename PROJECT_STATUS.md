# Project status

PM-owned. One SESSION block per PM session, newest first.

## SESSION 2026-10-21 (PM: Fable 5.1, user's choice for this session; workers Opus / Sonnet)

- Rulings D41-D43. Stage 4 L1x-as (as-of response scale on Qa) is CONFIRMED-INCUMBENT (provisional), joining stage 1 H3''-LC2 + T2, stage 3 A3g-c and stage 6 C1s.
- Engine: goal C1s (oracle goalie), miss stand-in S0t, L0s on M1 K500, B0 with own 4v4 / 3v3 groups, and L1x-as behind a default-off flag. Plumbing loop save % 90.06 vs 89.94; SL-R7 closed loop G3 PASS, G2 re-check PASS.
- Stand-ins still in the engine: block B0, miss S0t. Stages 7-8 absent.
- INV-53 (as-of response scale) is the standing fix for a drifting rating response (D43). New: INV-61 (live "for" R drift monitor), INV-62 (prior floor for the burn-in spike).
- LEARNINGS L37-L38.
- Next session: switch the L1x-as flag on in the default table set; INV-62; SB-R5 (blocks with the as-of scale); stage 8.

## SESSION 2026-10-16 (PM: Opus 5.5)

- Rulings D18-D40. Stage 1 H3''-LC2 + T2, stage 3 A3g-c and stage 6 C1s are CONFIRMED-INCUMBENT (provisional).
- Stand-ins in the engine: stage 4 L0s, block B0, miss S0t (S0t not wired yet).
- Lines: INV-24/25/38 closed. DRatings v2 has puck-line flags. Totals agreement passes.
- Data hygiene: INV-16/18 closed. The weekly pull is scheduled.
- New rules:
  - responsiveness is the slope ratio R (D32);
  - the era level E is not selectable (D35);
  - the stand-in selection rule (D40);
  - the stage-4 stop rule (D30).
- LEARNINGS L29-L36.
- Next session: SL-R7 (INV-59) and engine lane INV-60.

## SESSION 2026-10-15 (PM: Opus 5.5)

- Project created. Methodology ported from CBB-clean-sheet and cfb-props-sim (ARCHITECTURE_DECISIONS D1-D4).
- User rule: no Fable anywhere; PM on Opus, workers Opus/Sonnet/Haiku with explicit model on every call (D2).
- Phase P0 started. Lanes dispatched: A (Sonnet) NHL API ingest + data audit; B (Sonnet) lines / props / goalie-confirmation source audit.
- User approved GitHub remote (pushed, verified), HF dataset `mvpeav/nhl-sim-data` (created private) and AWS (D5).
- Lanes A-E all reported and their work was reviewed. P0 closed: INV-1/2/3/8/10/11/14/15. Gate scaffolding is in (INV-17).
- Control R1 ruled: A0 is the yardstick, and its failing gates set the event engine's bar (D9, L17).
- Next session: P2 kickoff (INV-22).
