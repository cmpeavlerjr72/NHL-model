# Lane G: ESPN core lines ingest (2023-24, 2024-25) and DRatings cross-check (INV-23)

Run 2026-10-15 16:57-17:20 EDT. Read-only, generic User-Agent, no credentials. 2025-26 not touched (sealed).
Code: `src/nhl_sim/clients/espn_core_odds.py`, `scripts/pull_lines_espn_core.py`, `src/nhl_sim/lines_espn_core.py`, `scripts/build_lines_espn_core.py`, `src/nhl_sim/dratings.py`, `scripts/pull_dratings_sample.py`, `scripts/crosscheck_espn_dratings.py`. Tests: `tests/test_lines_espn_core.py`, `tests/test_dratings_parser.py` (offline fixtures; the ESPN fixture contains a live item that must be dropped).

## 1. ESPN core pull

- Event ids come from `data/raw/espn_scoreboard/`, mapped to NHL `game_id` by date (+/-1 day) and home/away: 2,798 of 2,798 games mapped (2024-25: 1,312 regular + 86 playoff; 2023-24: 1,312 regular + 88 playoff).
- Pulled 2,798 events, 0 failures, 735 s at 4 threads (about 3.8 req/s with 0.4 s per-thread pause). The 3-minute slice: 400 in 95 s, extrapolated 11-12 min; the full run followed that. Raw cache `data/raw/espn_core_odds/<event_id>.json` (git-ignored).
- Output `data/processed/lines_espn_core_v1.parquet`: 99,072 rows (game x provider x market x side). Columns as briefed plus `provider_id` and `close_ml_vig_ok`. `close_*` is filled only from an explicit `close` object; `current` is never promoted to close.
- Pregame providers: 2024-25 only ESPN BET (id 58). 2023-24 has 14 names: ESPN BET, Bet365, MGM, Titanbets, Unibet, 3 Caesars state variants (plus plain Caesars), DraftKings, SugarHouse, BetfairSportsbook, PointsBet, FanDuel (18 rows).
- 2 playoff games have no pregame item (2023030145, 2023030413).

## 2. Live items dropped (L18)

1,592 live items dropped: 1,503 "ESPN Bet - Live Odds" (id 59) and 89 "Caesars Sportsbook (New Jersey) - Live Odds". Rule: provider id 59 or a name containing "live"/"in-play". The build raises `AmbiguousProviders` on a duplicate pregame provider id within one game; none occurred.

## 3. Coverage (share of games with a value; "ESPN BET" = provider 58 only)

| Season | Market | Any provider open / close | ESPN BET open / close |
|---|---|---|---|
| 2023-24 (1,400) | ml, pl, total | 99.2% / 99.8% | 97.1% / 98.2% |
| 2024-25 (1,398) | ml, pl, total | 100% / 100% | 100% / 100% |

## 4. Vig check (close ML implied-probability sum must be in [1.00, 1.10])

- 2024-25: 1,398 ESPN BET pairs, 0 outliers.
- 2023-24: 7,059 of 14,994 game-provider pairs (2023-24 only) are OUTSIDE the range, sums 0.80 to 0.98. All are non-ESPN-BET books: Bet365 1,324, Titanbets 1,324, Unibet 1,324, DraftKings 1,322, SugarHouse 715, BetfairSportsbook 553, PointsBet 382, Caesars (New Jersey) 115. Raw check, game 2023020010: Bet365 close is +130 / +155 (both sides positive), DraftKings +120 / +160. The raw `close` equals `current` in these items, so the source itself is incoherent. ESPN BET, MGM and the Caesars plain/Colorado/Tennessee variants have 0 outliers. Full list: `data/processed/lines_espn_core_v1_vig_outliers.csv`. Parquet rows carry `close_ml_vig_ok=False` for them. They are flagged, not dropped. Do not use them as closes.
- 2023-24 ML `open` is present for 93-100% of games for every book except FanDuel (18 rows, 0%). Share of 2023-24 closes passing the vig check: ESPN BET 100%, MGM 100%, Caesars plain/Colorado/Tennessee 100%, Caesars NJ 91%, Betfair 56%, SugarHouse 46%, PointsBet 12%, DraftKings 0.1%, Bet365 / Titanbets / Unibet 0%. Use `close_ml_vig_ok`. A multi-book 2023-24 close consensus is therefore thin (about 4 usable book families).

## 5. DRatings cross-check (2024-25 sample)

- 112 completed regular-season games, 7 index pages spread over 2024-10-15 to 2025-04-08 (Oct 16, Nov 16, Dec 16, Jan 23, Feb 9, Mar 16, Apr 16), all matched to a `game_id` and to ESPN BET rows. Raw pages in `data/raw/dratings/` (git-ignored). Fetched with request starts at least 3 s apart (3 workers, because the server took 7+ s per response). Per-game rows: `data/processed/lines_crosscheck_espn_dratings_v1.csv`, summary JSON beside it.
- DRatings ML probability = its own "No-Vig Odds" column (home side), compared with ESPN BET close, vig removed.

| Metric | n | Result |
|---|---|---|
| ML close no-vig home prob, |diff| | 112 | mean 0.0071, **median 0.0057**, p95 ~0.017, max 0.0270 |
| Same, median of 10 per-book no-vig probs | 112 | mean 0.0059, median 0.0043, max 0.0267 |
| ML open no-vig, |diff| (offshore open) | 112 | mean 0.0120, median 0.0083, max 0.2024 |
| Total line, close (mode of the 10 DRatings books vs ESPN BET) | 112 | **54.5% identical** (61/112) |
| Total line, close (DRatings no-vig column) | 112 | 55.4% |
| Total line, open | 112 | 56.3% |
| Puck line (away side line), close | 112 | 96.4% identical |
| Puck line, open | 112 | 95.5% |

Pre-set tolerance: median |ML diff| <= 0.02 AND total-line agreement >= 85%.

**Verdict: FAIL** (ML passes with a median of 0.0057, but total-line agreement is 54.5% against 85%).

### Diagnosis of the total-line failure

- Every disagreement is exactly 0.5 goal (diff counts DRatings minus ESPN: -0.5 x26, 0 x61, +0.5 x25). It is not a parsing error: the 10 DRatings books agree on one line in 83 of 112 games, and the other 29 differ by one step among themselves.
- ESPN BET picks a different "main" total and adjusts the price: when ESPN's line is 0.5 lower than DRatings, its over price averages -131; when 0.5 higher, +109; when equal, -68. So the two sources agree after price adjustment and differ in which half-goal total each calls "the" line.
- Agreement is best late in the season (April 87.5%, March 68.8%, Feb 66.7%, Jan 52.2%, Oct-Dec 37.5%), consistent with ESPN BET's early-season line selection differing more from the offshore/Vegas consensus.
- Consequence: ESPN BET totals must not be treated as the market consensus line. If a total is used for CLV or grading, either use price-adjusted comparisons (convert to a common line) or take the DRatings consensus. ML closes and puck lines are consistent between the sources.
- Caveats: "Open" on DRatings is a single value per book group and its provenance is unknown; the ML open max of 0.20 is one game and should be inspected before anyone uses opens. Sample is 112 games of 1,398 (8%); Oct-Dec has 48 games, one sampled page per month.

## 6. Not done / PARTIAL

- Nothing unfinished in scope. 2023-24 multi-book usefulness is poor (see section 4).
- Resume commands (all cached, idempotent): `PYTHONPATH=src .venv/Scripts/python.exe scripts/pull_lines_espn_core.py` then `scripts/build_lines_espn_core.py`; `scripts/pull_dratings_sample.py 16` then `scripts/crosscheck_espn_dratings.py`.
