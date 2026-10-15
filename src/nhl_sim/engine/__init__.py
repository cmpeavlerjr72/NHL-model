"""Event-level GameState engine (cascade stage 1: clock, periods, penalty box, strength state).

One engine: variants live behind default-off flags in `RuleEra`. The sim loop is vectorised NumPy over
(games x seeds) and reads lookup tables only; no live model calls.
"""
