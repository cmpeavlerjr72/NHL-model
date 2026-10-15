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

## D6 (2026-10-15): NHL API stays primary, personal-use posture

Decision: keep `api-web.nhle.com` / `api.nhle.com/stats` as the primary source despite NHL.com's site terms barring scraping (no published terms for the stats API; Lane B audit). Personal research only: polite rate, disk cache, never re-fetched, never redistributed (the HF dataset stays private).
Reason: user decision 2026-10-15.
Status: ADOPTED; risk recorded in `docs/ops/data_sources.md`.

## D7 (2026-10-15): No paid historical odds yet

Decision: do not buy The Odds API now. Backtests grade on accuracy first; free ESPN pickcenter and Kalshi `/historical` are used wherever they cover. Revisit once the Control engine exists.
Reason: user decision 2026-10-15; CLAUDE.md accuracy-first phase.
Status: ADOPTED.

## D8 (2026-10-15): Forward logging, and "oracle goalie" backtests

Decision: scheduled read-only loggers capture Daily Faceoff goalie status (with fetched_at), Kalshi NHL market snapshots and DKeX NHL board snapshots from today forward. 2021-26 backtests use box-score starters and are labelled "oracle goalie" (no bulk pregame goalie history exists).
Reason: Lane B audit; user approved scheduled tasks 2026-10-15.
Status: ADOPTED.
