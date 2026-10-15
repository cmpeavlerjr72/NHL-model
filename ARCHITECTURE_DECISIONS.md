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

## D9 (2026-10-15): Control R1 ruling: A0 is the yardstick

Decision: A0 (independent Poisson, as-of ridge ratings, unpenalised home term, no goalie term) is the yardstick. No richer arm beat it beyond the noise floor on fold 2 (all diffs vs A0 have 95% intervals spanning 0). Under the R1 decision rule it is adopted with its gate failures listed as the bar the event engine must clear:

| Gate | Control A0 (fold 2) | Actual 2024-25 |
|---|---|---|
| G5 total SD ratio | 1.082 | 0.95-1.05 band |
| G5 home/away score correlation | -0.036 | -0.115 |
| G5 P(total=4) | off 1.99 pp | - |
| G7 regulation-tie rate | 15.9% | 20.8% |
| G6/G9 home win | 52.8% | 56.5% |

A4 is the variant repaired after a numerical blow-up on the first fold-2 pass. The repair was chosen on fold 1 and no fold-2 scores were computed before it, and it is disclosed in `docs/tests/control_r1_2026-10-15.md`. It did not win either way.
Reason: `docs/tests/control_r1_2026-10-15.md`, commits d2ed7fa..56ff992.
Status: ADOPTED (yardstick). Control R2 (extend edge-hit grids; a dependence family allowing negative correlation and excess ties) is DEFERRED (INV-21). The event engine is the priority.

## D10 (2026-10-15): Historical lines sources (resolves INV-19)

Decision, for each season (all free, read-only, polite crawl):

| Season | Primary | Second source (cross-check / multi-book) |
|---|---|---|
| 2021-22, 2022-23 | SportsbookReviewsOnline season HTML (consensus open/close ML and total, close PL) | DRatings per-game pages (open + 10-book close) |
| 2023-24 | ESPN core API `/odds` (9-12 books, open/close ML) | DRatings |
| 2024-25 (fold 2) | ESPN core API `/odds`, ESPN BET pregame item only (open/close ML, PL, total) | DRatings (open + 10-book close incl. Circa, South Point) |
| 2025-26 (sealed) | ESPN core / ESPN site pickcenter (DK open+close) | free `minmaxxxer/nhl-closing-odds-2025-26` |

- ESPN core returns a second "ESPN Bet - Live Odds" item holding in-game prices. Ingest keeps ONLY the pregame provider item and fails if it is ambiguous.
- Not used, because terms or robots forbid them: SBR live pages (ToS bans bots), Action Network API (robots Disallow /), OddsPortal.
- Sign-up options are recorded for the user and are not needed now: OddsPapi free key (timestamped ticks, depth unknown), API-Sports.
- Before any ROI is read, the primary and second sources must agree within tolerance on overlapping games (L10-style two-source verification).

Reason: Lane F1/F2/F3 hunt, `docs/ops/lines_hunt_F{1,2,3}_2026-10-15.md` (2a28c22, e3d1190, ece8f09). PM spot-check: ESPN core sample 2025-01-15 shows ML open -170/+145, close -185/+155, total 6.5 -> 5.5.
Status: ADOPTED. Supersedes the "no free 2024-25 source" finding in INV-19. D7 (no paid odds) stands.
