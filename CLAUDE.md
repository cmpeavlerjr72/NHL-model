# CLAUDE.md

Event-level Monte Carlo simulation engine for the NHL: game scores, game markets (moneyline, puck line, totals), and player props (shots on goal, goals, assists, points, goalie saves).
New project (started 2026-10-15), following the methodology of `C:\Users\devuser\CBB-clean-sheet` and `C:\Users\devuser\cfb-props-sim`. Mine both repos' `docs/LEARNINGS.md`, `docs/SIM_GUARDRAILS.md` and postmortems before re-learning a lesson.

Read in order: `PROJECT_STATUS.md` -> `docs/FRAMEWORK_PLAN.md` -> `ARCHITECTURE_DECISIONS.md` -> `docs/SIM_GUARDRAILS.md` -> `docs/LEARNINGS.md` -> `docs/models/README.md` -> `docs/BOARD.md` -> `HANDOFF.md`.

## Standing rule: PM / worker split, NO FABLE (user rule, 2026-10-15)

Opus 5.5 is the project manager (the main session): writes specs and briefs, reviews bake-off tables and gate reports, makes decisions, writes the decision docs. Worker agents do the reading, coding, and analysis:

- **Opus**: engine core and cascade sub-models only. At most 1 Opus worker per day.
- **Sonnet**: pipelines, ingest, graders, bake-off runners, audits.
- **Haiku**: lookups and summaries.

**No agent in this project runs on Fable** (user is at the end of the weekly Fable allowance). Every Agent call passes `model` explicitly (`opus`, `sonnet` or `haiku`); never rely on inheritance. `.claude/settings.json` sets `CLAUDE_CODE_SUBAGENT_MODEL=opus` as a backstop. Workers may not spawn sub-workers unless the brief grants it, and then only on Sonnet/Haiku.

Keep tool-heavy work out of the PM context. Worker rules for the current session: `docs/ops/worker_rules_*.md` (newest binds).

## Standing rule: token budget

PM sessions stay short; start a fresh session per phase and write a `session-resume-<date>.md` memory before ending. 2-3 concurrent workers maximum. No speculative follow-on rounds: one chained brief per question. Stop for the day once ~15% of the weekly allowance has been spent in the session.

## Standing rule: bake-off before any choice

No model class, distribution family, sampling scheme, feature bundle, or anchor rating is adopted because it is convenient or familiar. Every choice is a pre-registered comparison of multiple candidates on walk-forward holdouts:

- The spec (candidates, features, folds, primary metric, segment breakdowns, noise floor, decision rule) is written to `docs/models/<model>/experiments.md` and committed BEFORE the experiment runs.
- Folds: fold 1 trains through 2022-23 and tests 2023-24; fold 2 trains through 2023-24 and tests 2024-25. Fold 2 is the selection metric. The 2025-26 season is sealed (enforced in code) until a sub-model has been selected on fold 2. 2026-27 is live.
- One grading script scores every arm blind. A winner must beat a spec-identical retrain under another seed (the noise floor). Ties go to the simpler model.
- An offline winner ships only after a paired-seed sim run shows no gate regressed.
- `experiments.md` is append-only. Status changes go to `docs/models/change_ledger.md` in the same commit.

## Standing rule: no hand tuning on engine output

No post-hoc multipliers, caps, clips, offsets, calibration curves, or blends on sim output. If the engine's output has to be adjusted to resemble reality, the engine is wrong and the responsible sub-model must be found and fixed. Exact wording and the cautionary inventories: `docs/SIM_GUARDRAILS.md` core principle, and the CFB/CBB guardrails it cites. Decision-layer probability calibration is allowed only walk-forward, clearly labelled, and never to hide a sim-level defect.

## Standing rule: bottom-up the cascade

Build and gate the smallest unit first: strength-state / penalty process, then shot-attempt generation, then shot location and type, then shot-on-goal / block / miss, then goal given shot (shooter x goalie), then rebounds and faceoffs, then clock and end-game (goalie pull, OT, shootout), then game aggregates, then player attribution (deployment and usage), then markets. Never accept a downstream stage that compensates for a known upstream bias. A passing aggregate over a biased sub-model is a failure.

## Standing rule: matchup-specific, not league-average

Every sub-model must show responsiveness: predictions bucketed by team, player, or goalie prior quintile must slope with actuals, not sit flat at the mean. Check explicitly when evaluating any new model.

## Standing rule: multi-level evidence

Every finding and every fix shows overall, per-game, per-team, per-strength-state (5v5 / PP / PK / 4v4 / 3v3 / empty net), per-goalie, and per-player (when relevant) evidence. Aggregate-only proof is insufficient. Underpowered cells are labelled underpowered, never presented as signal or absence of signal.

## Standing rule: profitability frame, with an accuracy-first phase

The objective is profitability against lines (Kalshi, DraftKings Predictions exchange "DKeX", historical closes for backtests). Until a lines source is validated, grade primarily on score and stat accuracy (goal-total distribution, margin, win probability, per-stat calibration), and add the market scorecard (calibration vs de-vigged market, ROI by edge bucket at real odds, CLV cross-check) wherever lines exist. An edge that beats the close but cannot predict line movement is presumed leaked. Settle at the posted line, never the de-vigged line. Grade against verified finals (shootout handled per market rules), never against pbp-accumulated totals. No paid data without asking the user. No live orders or trades are placed by any agent.

## Standing rule: backtests must be honest

- Every backtest row must satisfy `created_at < puck_drop`, enforced in code.
- Every external feature (any rating or xG feed) passes the leak test before entering a feature table: change-form correlation with own-game margin, |corr| <= 0.15.
- Grading truth (finals, OT/SO outcome, player box lines) is verified against a second source before any grade is trusted.
- Starting goalie used in a backtest must be the goalie KNOWN pregame (projected/confirmed at the time), not the box-score starter, or the backtest is labelled "oracle goalie".
- A seed-count study fixes the minimum seeds before any ROI number is read.

## Modeling rules

- Every rating feature is expressed relative to its own snapshot's league mean. Raw levels are banned.
- Home/away is a first-class feature in every scoring-stage model; audit each model's feature list for it. Rest / back-to-back is a first-class candidate feature.
- Rates per 60 by strength state, not counts.
- Score effects are real in hockey (trailing teams out-shoot leaders). Any score-state feature must use the state BEFORE the event, and any model consuming engine-produced state needs a closed-loop gate (CBB L23/L27: a post-event `score_diff` tripled margin variance).
- Ties resolve through the OT (3v3) and shootout models, never discarded.
- RNG seeded on (seed, game_id, family). Paired bake-off arms share aligned streams.
- Rule-era flags live in GameState, not baked into sub-models.
- One engine. Variants live behind default-off flags over a shared core. No forks.
- Sim loop uses lookup tables and vectorized NumPy, never live model calls. Pin thread-count env vars in any container.

## Data rules

- Primary source: the public NHL API (`api-web.nhle.com`, `api.nhle.com/stats`): schedule, play-by-play with shot coordinates, shift charts, boxscores, rosters. Poll politely (rate limit, retry with backoff, cache raw JSON; never re-fetch what is on disk).
- Third-party data (MoneyPuck, Natural Stat Trick, Evolving-Hockey, etc.) only after its terms are checked and recorded in `docs/ops/data_sources.md`. Do not scrape sites whose terms or robots forbid it.
- Bulk data (`data/raw`, `results`) is gitignored and synced to the private HF dataset `mvpeav/nhl-sim-data` (token: `HF_TOKEN` in the gitignored `.env`, never printed or committed). `data/processed` and `data/reference` are tracked except model-artifact directories over 20 MB, which sync to HF.

## Compute

Home box first. AWS is approved by the user (2026-10-15) for heavy sim / sweep runs: only a designated OPERATOR lane touches AWS, via box requests in `docs/ops/box_queue/`; spot instances only; every instance is terminated and the termination verified with `describe-instances` before the lane reports; spend cap per session is set in that session's worker rules (default $60 unless the user says otherwise). Never leave an instance idle.

## Git practice

Remote: `https://github.com/cmpeavlerjr72/NHL-model.git`, branch `main`. Commit and push after every meaningful change. Verify pushes with `git ls-remote origin main` (quiet pushes can swallow rejections). Tracked files stay under 50MB. Never commit `.env` or any API key.

## Scripts convention

`scripts/` is flat and prefix-named: `pull_ build_ train_ run_ exp_ diag_ grade_ leak_ chain_ inv{N}_`. Trainers are versioned filenames (`train_x_v2.py`), never overwritten. `src/nhl_sim/` is the small tested core (game state, engine, deployment/usage allocation, lookups, clients).

## Worker discipline

Workers run concurrently on one machine. Never kill, restart, or signal a process you did not start (`Stop-Process python` is banned); restart only your own PID. Never overwrite a data file another worker may be reading; write a versioned sibling and let the PM switch. Report any interruption you caused.
Every PM wake re-reads the whole PM context, so:
- A worker never ends its turn while its own job is still running. It waits in-turn: a blocking foreground wait with a timeout of at most 10 min, repeated.
- Before reporting, it stops every background child it started, so exactly one completion notice reaches the PM.
- Workers never edit a PM-owned doc (`CLAUDE.md`, `PROJECT_STATUS.md`, `HANDOFF.md`, `ARCHITECTURE_DECISIONS.md`, `docs/FRAMEWORK_PLAN.md`, `docs/SIM_GUARDRAILS.md`, `docs/LEARNINGS.md`, `docs/BOARD.md`); they propose text in their report or write a sibling file.
- Full report goes to a file under `docs/tests/` or `docs/ops/`; the message back to the PM is under 400 words.
- The PM chains follow-up steps into one brief instead of launching a series of workers. Corrections go into a fresh brief, never mid-task.

## Windows

Set `PYTHONIOENCODING=utf-8` before running scripts that print non-ASCII. Use `.venv/Scripts/python.exe` (Python 3.12).
