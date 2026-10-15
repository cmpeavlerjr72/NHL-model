"""Small cached client for the public NHL API.

Endpoints: api-web.nhle.com/v1 (schedule, play-by-play, boxscore, roster) and
api.nhle.com/stats/rest/en (shift charts). Raw JSON is cached under
``data/raw/nhl_api/<endpoint>/<key>.json``; a completed game is never re-fetched.
"""
from __future__ import annotations

import json
import random
import threading
import time
from pathlib import Path

import requests

WEB = "https://api-web.nhle.com/v1"
STATS = "https://api.nhle.com/stats/rest/en"
USER_AGENT = "NHL-Model research client (cmpeavlerjr@gmail.com)"
MAX_CONCURRENT = 4
FINAL_STATES = {"OFF", "FINAL"}

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE = ROOT / "data" / "raw" / "nhl_api"


class NHLApiError(RuntimeError):
    pass


class NHLApiClient:
    def __init__(self, cache_dir: Path | str = DEFAULT_CACHE, max_concurrent: int = MAX_CONCURRENT,
                 retries: int = 6, timeout: float = 30.0, session: requests.Session | None = None):
        self.cache_dir = Path(cache_dir)
        self.sem = threading.BoundedSemaphore(min(max_concurrent, MAX_CONCURRENT))
        self.retries = retries
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.n_network = 0
        self.n_cached = 0

    # ---- cache -----------------------------------------------------------
    def _path(self, endpoint: str, key: str) -> Path:
        return self.cache_dir / endpoint / f"{key}.json"

    def _read(self, endpoint: str, key: str):
        p = self._path(endpoint, key)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        return None

    def _write(self, endpoint: str, key: str, data) -> None:
        p = self._path(endpoint, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp%d" % threading.get_ident())
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        tmp.replace(p)

    # ---- http ------------------------------------------------------------
    def _get(self, url: str):
        last = None
        for attempt in range(self.retries):
            with self.sem:
                try:
                    r = self.session.get(url, timeout=self.timeout)
                    self.n_network += 1
                except requests.RequestException as e:  # network error
                    r, last = None, e
            if r is not None:
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 404:
                    raise NHLApiError(f"404 {url}")
                last = NHLApiError(f"HTTP {r.status_code} {url}")
            time.sleep(min(60.0, 1.5 * 2 ** attempt) * (0.75 + 0.5 * random.random()))
        raise NHLApiError(f"failed after {self.retries} tries: {url}: {last}")

    def _cached_get(self, endpoint: str, key: str, url: str, is_final=lambda d: True):
        d = self._read(endpoint, key)
        if d is not None:
            self.n_cached += 1
            return d
        d = self._get(url)
        if is_final(d):
            self._write(endpoint, key, d)
        return d

    # ---- endpoints -------------------------------------------------------
    def schedule_week(self, date: str, today: str | None = None):
        """Schedule for the week containing ``date`` (YYYY-MM-DD). Cached only if the
        whole week is >=3 days in the past (scores/states are then final)."""
        today = today or time.strftime("%Y-%m-%d", time.gmtime())

        def final(d):
            end = d.get("gameWeek", [{}])[-1].get("date", "9999")
            return (np_days(today) - np_days(end)) >= 3

        return self._cached_get("schedule", date, f"{WEB}/schedule/{date}", final)

    def pbp(self, game_id: int):
        return self._cached_get("pbp", str(game_id), f"{WEB}/gamecenter/{game_id}/play-by-play",
                                lambda d: d.get("gameState") in FINAL_STATES)

    def boxscore(self, game_id: int):
        return self._cached_get("boxscore", str(game_id), f"{WEB}/gamecenter/{game_id}/boxscore",
                                lambda d: d.get("gameState") in FINAL_STATES)

    def shifts(self, game_id: int):
        # no state field; callers only request shifts for final games.
        return self._cached_get("shifts", str(game_id),
                                f"{STATS}/shiftcharts?cayenneExp=gameId={game_id}",
                                lambda d: d.get("total", 0) > 0)  # empty charts are re-tried next run

    def roster(self, team: str, season: int):
        return self._cached_get("roster", f"{team}_{season}", f"{WEB}/roster/{team}/{season}")


def np_days(s: str) -> int:
    import datetime as dt
    return dt.date.fromisoformat(s).toordinal()
