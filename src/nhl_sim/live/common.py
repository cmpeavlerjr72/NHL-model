"""Shared helpers for the forward loggers.

Read-only: anonymous GETs only. Every run writes a NEW timestamped raw snapshot and APPENDS to the
day's normalised jsonl; nothing earlier is ever deleted or overwritten.
Day directories use the LOCAL calendar date of the run (the schedule is local); fetched_at is UTC.
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import time
from pathlib import Path
from typing import Callable

import requests

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw" / "live"
LOG_DIR = ROOT / "logs" / "live"
UA = "NHL-Model-research/0.1 (personal read-only research; contact cmpeavlerjr@gmail.com)"


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_z(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def file_stamp(t: dt.datetime) -> str:
    return t.strftime("%Y%m%dT%H%M%SZ")


def http_get_json(url: str, *, params=None, headers=None, retries: int = 4, timeout: int = 30,
                  session: requests.Session | None = None) -> dict:
    """GET with exponential backoff on network errors, 429 and 5xx. Raises on final failure."""
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    get = (session or requests).get
    last: Exception | None = None
    for i in range(retries):
        try:
            r = get(url, params=params, headers=h, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code} {url}")
            if r.status_code not in (429, 500, 502, 503, 504):
                break
        except (requests.RequestException, ValueError) as e:
            last = e
        time.sleep(2 ** i)
    raise RuntimeError(f"GET failed after retries: {last}")


def save_raw(source: str, payload, fetched_at: dt.datetime, day: str) -> Path:
    """Write payload wrapped with fetched_at to a new gz json file. Refuses to overwrite."""
    d = RAW_DIR / source / day
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{source}_{file_stamp(fetched_at)}.json.gz"
    if p.exists():
        raise FileExistsError(p)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        json.dump({"fetched_at": iso_z(fetched_at), "source": source, "payload": payload}, f)
    return p


def append_rows(source: str, rows: list[dict], day: str) -> Path:
    d = RAW_DIR / source / day
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{source}_rows_{day}.jsonl"
    with open(p, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def write_status(source: str, ok: bool, msg: str, fetched_at: dt.datetime) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{iso_z(fetched_at)} {'OK' if ok else 'FAIL'} {msg}".replace("\n", " ")
    with open(LOG_DIR / f"{source}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_logger(source: str, fetch: Callable[[], object], normalise: Callable[[object, str], list[dict]]) -> int:
    """fetch() -> raw payload; normalise(payload, fetched_at_iso) -> rows. Returns process exit code."""
    t = utc_now()
    day = dt.datetime.now().strftime("%Y-%m-%d")
    try:
        payload = fetch()
        rows = normalise(payload, iso_z(t))
        if not rows:
            raise RuntimeError("zero normalised rows")
        raw = save_raw(source, payload, t, day)
        append_rows(source, rows, day)
        write_status(source, True, f"rows={len(rows)} raw={raw.name}", t)
        print(f"{source} OK rows={len(rows)} raw={raw}")
        return 0
    except Exception as e:  # noqa: BLE001 - any failure -> non-zero, earlier files untouched
        write_status(source, False, f"{type(e).__name__}: {e}", t)
        print(f"{source} FAIL {type(e).__name__}: {e}")
        return 1
