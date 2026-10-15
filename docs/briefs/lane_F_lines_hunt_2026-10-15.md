# Lane F brief: deep hunt for free historical NHL opening/closing lines (INV-19)

Two parallel workers, both on Sonnet: F1 (live web/API endpoints) and F2 (datasets/archives/exchanges). Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-15.md`. Prior work, which you must not redo: `docs/ops/lines_sources_audit_2026-10-15.md`, `docs/ops/data_sources.md`, `docs/tests/espn_lines_coverage_2026-10-15.md`.
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Goal

Find free sources of NHL moneyline, puck line and total odds for past games. Opening AND closing lines are wanted; a closing line alone is fine. The priority is 2024-25 (ESPN's pickcenter is empty for it); 2021-24 coverage is a bonus. Almost every scores site displays game odds, so one of them probably serves them from an endpoint we can read. The job is to find it and prove it with real data.

## Clock (hard)

- Run `Get-Date` at start. HARD STOP for research at **17:15 EDT**.
- The report must be committed and pushed by **17:20 EDT**.
- An early report with proven finds beats a late exhaustive one.

## Proof standard for each candidate

For each candidate, record all of the following:
- the exact URL/endpoint pattern;
- one real request for a 2024-25 game, ideally 2025-01-15 or another mid-season date, plus one earlier season if quick;
- which books are returned and whether open/close or a timestamp history exists;
- how game ids map (date + teams is fine);
- terms/robots verdict;
- rough requests needed for a full season.

Save one small sample response per working source in `data/samples_laneF/<source>/`. Write probe scripts in `docs/ops/probes/laneF{1,2}_*.py`.

## Hard limits

- Read-only.
- No logins, no account creation, no paid plans, no CAPTCHA solving, no bypassing paywalls or bot protection.
- Respect robots.txt and terms. Record a verdict, and don't use a source that bans automated access.
- Keep request volume small (probes only, not bulk pulls).
- Use a generic User-Agent with no personal info. Never include an email address.
- You may NOT spawn sub-agents.
- Stage only your own files.

## F1: live web/API endpoints (sites that show odds next to scores)

Probe at least:
- **ESPN core API:** `sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{id}/competitions/{id}/odds`, plus any `/odds/{provider}/history/0/movement` sub-resources. These are different from the site-API pickcenter Lane B used. Use 2024-25 ESPN event ids; Lane D's cache in `data/raw/espn/` and Lane E's `data/raw/espn_scoreboard/` already have them (read-only).
- **Action Network:** public scoreboard JSON, e.g. `api.actionnetwork.com/web/v1/scoreboard/nhl?date=YYYYMMDD` or similar, which has historically carried opening and closing lines by book.
- **Sportsbook Review (SBR) odds pages:** `sportsbookreview.com/betting-odds/nhl-hockey/?date=YYYY-MM-DD`, and moneyline/puck line/totals variants. These are Next.js, so look for `__NEXT_DATA__` with opener and closing.
- **Covers.com** NHL matchups/odds by date, and team "past results" pages that carry closing lines.
- **Others:** Yahoo Sports scoreboard odds, CBS Sports, Fox Sports (bifrost API), theScore, OddsShark (team odds history / database pages), VegasInsider, Rotowire/Rotogrinders, Scores And Odds, Oddstrader, Pickswise, BetMGM/Caesars/FanDuel public "event" APIs (these usually only cover live events), NHL.com's own gamecenter odds (api-web has a `/partner-game/` odds endpoint for current games; check whether it serves past games).

## F2: datasets, archives, exchanges

Probe at least:
- **SportsbookReviewsOnline:** NHL historical odds Excel archive. Which seasons are there, does it have open and close, and is it still downloadable?
- **Kaggle:** NHL odds datasets. Read the listings and metadata only; do not log in or download behind auth.
- **GitHub:** repos or releases containing NHL odds CSVs or scrapers, e.g. SBR scrapers, "nhl odds history", "hockey betting dataset".
- **Hugging Face:** datasets with NHL odds.
- **Betfair Exchange:** historical data free BASIC tier (ice hockey, 1-minute last traded price). Requirements only; do not register.
- **Polymarket:** NHL markets history via the gamma/clob APIs, if they exist for 2024-25.
- **Other exchanges:** Kalshi `/historical` before 2025-04, which Lane B saw start at 2025-04; confirm with one older ticker.
- **Wayback Machine:** CDX snapshots of SBR/Covers/OddsShark NHL odds pages for 2024-25 dates. What fraction of dates is captured?
- **Academic/open data:** the Princeton DSS dataset access, Zenodo, Dataverse, OSF ("NHL betting odds").
- **Pinnacle:** closing-line datasets shared publicly, such as archived Pinnacle API dumps.

## Output

- F1 writes `docs/ops/lines_hunt_F1_2026-10-15.md`; F2 writes `docs/ops/lines_hunt_F2_2026-10-15.md`.
- Each doc ranks the sources by: 2024-25 coverage, open/close availability, number of books, terms OK, and effort to bulk-pull.

## Report

Under 300 words:
- the top 3 sources with their proof (sample path, books, open/close, season coverage);
- dead ends in one line each;
- commit hash.
