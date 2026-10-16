# Forward live loggers (D8)

Read-only. Anonymous GETs only: no logins, no orders, no account endpoints, no credentials. Built from Lane B probes (`docs/ops/probes/laneB_*.py`). Why they exist: none of the three sources has usable history, so every day not logged is lost.

## What runs

`scripts/chain_live_log.py` runs three independent loggers in sequence (one failing does not stop the others; exit code non-zero if any failed). Needs only `requests` (stdlib otherwise); uses `.venv\Scripts\python.exe`.

| Logger | Source | Per-run requests | Normalised row |
|---|---|---|---|
| `scripts/log_goalies.py` | Daily Faceoff `/starting-goalies` `__NEXT_DATA__` | 1 page fetch | game_date, game_start_utc, side, team, opponent, goalie, status (Confirmed/Likely/Unconfirmed/null), source_ts, source_name, fetched_at |
| `scripts/log_kalshi_nhl.py` | Kalshi public v2 `/series` + `/markets?status=open` for every `KXNHL*` series (paged) | ~80, 0.3 s spacing | series, event_ticker, ticker, title, strike_type, floor/cap_strike, yes/no bid/ask, last, volume, volume_24h, open_interest, open/close/expected_expiration time, fetched_at |
| `scripts/log_dkex_nhl.py` | DKeX board, league 42133, 11 subcategories | 11, 0.5 s spacing, percent-encoded query, CFB header recipe | subcategory, event, market, selection, outcome_type, participant, line, price_american, price_decimal, implied_pct, fetched_at |

Shared code: `src/nhl_sim/live/` (`common.py` helpers, one module per source). Tests: `tests/test_live_loggers.py` (offline, fixtures in `tests/fixtures/`).

Notes: Kalshi includes futures series (`KXNHL*` such as conference winners) because the filter is by ticker prefix; filter downstream. User-Agent (checked 2026-10-16, `src/nhl_sim/live/common.py` `UA`): `NHL-Model-research/0.1 (personal read-only research)`. It contains no email address (an earlier version of this doc said it did; that was wrong). ESPN returned 403 to a descriptive custom UA, so the ESPN scripts use a generic browser string; if any other source starts returning 403, try a plain UA first.

## Output layout

Per run, per source, under `data/raw/live/<source>/<YYYY-MM-DD>/` (`<source>` = goalies, kalshi, dkex; the date is the LOCAL calendar date of the run):

- `<source>_<YYYYMMDDTHHMMSSZ>.json.gz`: raw payload wrapped as `{fetched_at, source, payload}` (UTC in filename and inside). Never overwritten (existing file raises).
- `<source>_rows_<date>.jsonl`: append-only normalised rows for the day (every row carries `fetched_at`).
- Status: one line per run appended to `logs/live/<source>.log` (`<utc> OK rows=N raw=...` or `FAIL <error>`). A failed run exits 1, appends a FAIL line, and touches no data file.

`data/raw` and `logs` are gitignored; `data/raw` syncs to HF via `scripts/hf_sync_data.py`.

## Scheduled task

`NHL-Model-live-log`: daily trigger 09:00 repeating every 30 min for 14 h 30 min (last run 23:30 local), hidden, `MultipleInstances = IgnoreNew` (no overlap), `StartWhenAvailable`, 25 min execution limit. Principal is the current user with `LogonType Interactive` (no stored password), so it runs only while the user is logged on.

Register (idempotent, replaces only this task):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\devuser\NHL-Model\scripts\register_live_log_task.ps1
```

Remove:

```powershell
Unregister-ScheduledTask -TaskName NHL-Model-live-log -Confirm:$false
```

Inspect: `Get-ScheduledTask NHL-Model-live-log`, `Get-ScheduledTaskInfo NHL-Model-live-log`, `Get-Content logs\live\*.log -Tail 5`.

The task points at `.venv\Scripts\python.exe` (owned by Lane A). If that venv is rebuilt, re-run the registration script; to avoid the dependency, edit the script's `$py` to any Python 3.12 with `requests`.
No other scheduled task is touched by this setup (CBB/CFB tasks are unrelated).

## Weekly NHL API pull (D2, INV-16)

`NHL-Model-weekly-pull`: Monday 06:00 local, hidden, `MultipleInstances = IgnoreNew`, `StartWhenAvailable`, 2 h execution limit, `LogonType Interactive` (runs only while the user is logged on; with `StartWhenAvailable` a missed run starts at the next opportunity). Runs `scripts/chain_weekly_pull.py`: (1) `pull_schedule.py --out data/processed/schedule_weekly.parquet` (a versioned sibling; the shared `schedule.parquet` is never rewritten), (2) `pull_games.py --schedule data/processed/schedule_weekly.parquet` (cache-first: only new finals and games whose shift chart was empty are requested, 4 workers, backoff). Log: `logs/weekly_pull_<YYYY-MM-DD>.log` (appended). Exit code non-zero if a step failed.

Register / remove:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\devuser\NHL-Model\scripts\register_weekly_pull_task.ps1
Unregister-ScheduledTask -TaskName NHL-Model-weekly-pull -Confirm:$false
```

Inspect: `Get-ScheduledTaskInfo NHL-Model-weekly-pull`. Empty shift charts are not cached, so each run re-requests them; the 105 known gaps (57 in 2024-25, 2025-04-08 to 04-15; 48 in 2026-27, 2026-09-30 to 10-07) were still empty on 2026-10-16. Rebuilding processed tables (`build_tables.py`) is a separate manual step.
