# Architecture decisions

PM-owned, append-only. Each decision: date, decision, reason, evidence, status.

## D1 (2026-10-15): Methodology inherited from CBB-clean-sheet

Decision: adopt the CBB-clean-sheet rules (bake-offs, no hand tuning, bottom-up cascade, multi-level evidence, honest backtests, worker discipline) for the NHL project.
Reason: user instruction; those rules were written from the CFB-Monte and CBB-Monte postmortems.
Status: ADOPTED.

## D2 (2026-10-15): PM is Opus 5.5; no Fable workers

Decision: the PM runs on Opus 5.5. Workers run on Opus (engine core, at most 1 per day), Sonnet (pipelines, graders, audits) or Haiku (lookups). No agent uses Fable. Every Agent call names its model explicitly.
Reason: user rule 2026-10-15, weekly Fable allowance nearly exhausted. Revisit only on the user's word.
Status: ADOPTED.

## D3 (2026-10-15): Event-level engine with a Control yardstick

Decision: the served engine will be an event-level Monte Carlo (FRAMEWORK_PLAN section 1); a team-rate Control engine is built first as its yardstick. Every sub-model inside it is chosen by bake-off.
Reason: player props need deployment and usage inside simulated game states; the Control engine guards against complexity that does not pay.
Status: ADOPTED (shape only; components OPEN).

## D4 (2026-10-15): Lines venues

Decision: grade against Kalshi, DKeX and historical closing lines (source TBD by audit). Read-only; no agent places orders.
Reason: user answer 2026-10-15.
Status: ADOPTED; historical source OPEN.

## D5 (2026-10-15): Hosting and compute

Decision: GitHub `cmpeavlerjr72/NHL-model` (main); private HF dataset `mvpeav/nhl-sim-data` for bulk data; AWS spot compute approved, operator-lane only, per-session spend cap $60 (user-confirmed).
Reason: user approval 2026-10-15.
Status: ADOPTED.
