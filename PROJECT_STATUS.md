# Project status

PM-owned. One SESSION block per PM session, newest first.

## SESSION 2026-10-21 (PM: Fable 5.1, user's choice for this session; workers Opus / Sonnet)

- Rulings D41-D53. CONFIRMED-INCUMBENT (provisional): stage 1 H3''-LC2 + T2, stage 3 A3g-c (+ own 3v3 OT level, D50), stage 4 L1x-as (D43), stage 5 block B1a-as (D52), stage 6 C1s (D40; C1s-sap selected offline in G-R4, closed loop pending, D53).
- Engine: default set serves L1x-as + C1s + B0 / S0t (D44); B1a-as, the 3v3 level, the pull process P1, the shootout S1 and the goal flag sc_game are wired behind flags; INV-77 (Lane E4) switches B1a-as and the 3v3 level on and reads G5b.
- Stand-ins left: miss S0t, EN levels (no stage-3 EN states). Stages 7 and 8 not accepted; INV-71 margin compression located in goal conversion by score state (D48).
- The as-of response scale (INV-53) with the AS-1 prior floor (D44) is the standing fix for a drifting rating response; it fixed goalie, stage 4 and blocks.
- LEARNINGS L37-L39.
- Next session: E4's G5b read, then EG-R2 (INV-72), INV-70, INV-68 / INV-69.

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
