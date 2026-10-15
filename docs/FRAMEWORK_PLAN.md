# Framework plan

PM-owned. Created 2026-10-15. The 2026-27 NHL regular season is already under way, so Phase 3 has a live-season target; nothing ships live until it passes the gates.

## 0. What we are building

One event-level Monte Carlo engine that plays each game many times (seeds) from the pregame state and produces:

- game markets: moneyline (incl. OT/SO), regulation 3-way, puck line +/-1.5, totals, team totals, period markets;
- player props: shots on goal, goals, assists, points, blocks, goalie saves / goals against;
- all from the SAME simulated games, so props carry game-script correlation without a separate correlation model.

## 1. Engine shape (provisional; every component is a bake-off)

GameState (arrays over games x seeds): period, clock, score, strength state (skaters per side, goalie in/out), penalty timers, players on ice (line/pair index), faceoff location, fatigue/shift timers.

Per event step, a cascade of sub-models:

1. **Strength-state process**: penalty draws (by team, game state), PP expiry, coincidental minors, PP goals ending minors.
2. **Deployment**: which F line / D pair / PP unit / PK unit is on the ice (from shift-chart-derived deployment model + pregame line projections).
3. **Shot-attempt generation**: hazard of a shot attempt for each side given on-ice units, strength state, score state (pre-event), home, rest.
4. **Shot attributes**: location/danger zone, type, rebound / rush flags, shooter (usage among on-ice skaters).
5. **Attempt outcome**: blocked / missed / on goal.
6. **Goal given shot on goal**: shooter finishing x goalie save talent x shot quality.
7. **Faceoffs and stoppages**: zone starts, whistle rate.
8. **End game**: goalie pull (trailing margin x time x team tendency), 3v3 OT, shootout.

Ratings/priors: team and player rates built as-of each date, centred on league mean; goalie save talent with heavy shrinkage. Candidate anchors (own ridge ratings vs public xG-based ratings) are bake-off arms.

A cheap **Control engine** (team goal rates -> correlated Poisson / bivariate model) is built first as the yardstick the event engine must match or beat on G5/G9.

## 2. Phases

| Phase | Goal | Exit criterion |
|---|---|---|
| P0 Foundations | Repo, rules, data ingest (NHL API 2021-22 -> live), data audit, verified finals, lines-source audit | Audit doc committed; verified finals table; lines-source decision by PM |
| P1 Control + gates | Control engine, gate reference tables, `eval_gates.py`, grading scripts, seed-noise study | Control graded on fold 1/2 with a full gate report |
| P2 Event engine | Bottom-up sub-models in cascade order, each a pre-registered bake-off; closed-loop engine | Engine beats Control on fold 2 with no gate regressed |
| P3 Player layer + props | Deployment, usage, goalie layer; prop graders | G8 passes; props graded vs available lines |
| P4 Live ops | Daily chain (schedule, lines, goalie confirmations, injuries, sim, publish), Kalshi/DKeX edge boards (read-only) | Two weeks of live paper-graded slates, CLV tracked |

## 3. Data plan

- NHL API: schedule, play-by-play (shot coordinates, event types), shift charts, boxscores, rosters, standings. Seasons 2021-22 through live (2021-22 is train-only context; folds per CLAUDE.md).
- Lines: historical closes for 2023-25 backtests (source to be audited), Kalshi NHL markets (live), DKeX via HAR-derived access (user can supply a fresh HAR), all read-only.
- Goalie confirmations / projected lineups: source to be audited (must be timestamped pregame for honest backtests).

## 4. Open questions for the PM

- Lines source for historical backtests (P0 Lane B).
- Shift-chart coverage and quality by season (P0 Lane A).
- Whether third-party xG feeds are usable under their terms, or we build our own xG (default: build our own; any external xG is a bake-off arm only).
