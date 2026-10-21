# Project status

PM-owned. One SESSION block per PM session, newest first.

## SESSION 2026-10-21 (PM: Fable 5.1, user's choice for this session; workers Opus / Sonnet)

- Rulings D41-D54. CONFIRMED-INCUMBENT (provisional): stage 1 H3''-LC2 + T2, stage 3 A3g-c (+ own 3v3 OT level, D50), stage 4 L1x-as (D43), stage 5 block B1a-as (D52), stage 6 C1s (D40; G-R4's C1s-sap failed its closed loop, D54).
- Engine default set (D54): H3''-LC2 + T2, A3g-c with the 3v3 OT level, B1a-as, L1x-as, S0t stand-in, C1s (oracle goalie). Flags off: pull P1, shootout S1, goal sc_game. G2 and G3 pass in the default loop; G5b (55:00 tie) fails by +3.05 pp (2 SE = 2.1 pp).
- Stand-ins left: miss S0t, EN levels (no stage-3 EN states). Stages 7 and 8 not accepted; INV-71 margin compression located in goal conversion by score state (D48).
- The as-of response scale (INV-53) with the AS-1 prior floor (D44) is the standing fix for a drifting rating response; it fixed goalie, stage 4 and blocks.
- LEARNINGS L37-L39.
- Next session: Lane D2's INV-78 report first, then EG-R2 (INV-72), INV-70, INV-68 / INV-69.

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
