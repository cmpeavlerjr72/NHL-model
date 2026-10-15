import gzip
import json
from pathlib import Path

import pytest

from nhl_sim.live import common, dkex, goalies, kalshi

FX = Path(__file__).parent / "fixtures"


def test_goalies_parse_and_normalise():
    nd = json.load(open(FX / "df_next_data_2026-10-15.json"))
    html = '<html><script id="__NEXT_DATA__" type="application/json">' + json.dumps(nd) + "</script></html>"
    payload = goalies.parse_html(html)
    rows = goalies.normalise(payload, "2026-10-15T18:00:00Z")
    assert len(rows) == 2 * len(payload["data"]) > 0
    r = rows[0]
    assert r["side"] == "home" and r["goalie_name"] and r["fetched_at"] == "2026-10-15T18:00:00Z"
    assert {x["status"] for x in rows} <= {"Confirmed", "Likely", "Unconfirmed", None}
    assert any(x["status"] == "Likely" and x["source_ts"] for x in rows)


def test_goalies_missing_next_data():
    with pytest.raises(RuntimeError):
        goalies.parse_html("<html></html>")


def test_kalshi_normalise():
    ms = json.load(open(FX / "kalshi_markets_KXNHLTOTAL.json"))["markets"]
    rows = kalshi.normalise({"series": {"KXNHLTOTAL": ms}}, "t")
    assert len(rows) == len(ms)
    assert rows[0]["ticker"] and rows[0]["yes_bid"] is not None and rows[0]["floor_strike"] == 8.5


def test_dkex_normalise_and_url():
    j = json.load(open(FX / "dkex_4525.json"))
    rows = dkex.normalise({"subcategories": {"4525": {k: j[k] for k in ("events", "markets", "selections")}}}, "t")
    assert len(rows) == len(j["selections"])
    assert all("−" not in (r["price_american"] or "") for r in rows)
    assert any(r["line"] == 6.5 and r["outcome_type"] == "Over" for r in rows)
    assert "%27" in dkex._url("4525") and " " not in dkex._url("4525")


def test_failed_run_keeps_earlier_files(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(common, "LOG_DIR", tmp_path / "logs")
    ok = common.run_logger("t", lambda: {"a": 1}, lambda p, f: [{"x": 1, "fetched_at": f}])
    assert ok == 0
    files = sorted((tmp_path / "raw").rglob("*"))
    before = {p: p.read_bytes() for p in files if p.is_file()}
    assert len(before) == 2

    def boom():
        raise RuntimeError("down")

    assert common.run_logger("t", boom, lambda p, f: []) == 1
    assert {p: p.read_bytes() for p in (tmp_path / "raw").rglob("*") if p.is_file()} == before
    log = (tmp_path / "logs" / "t.log").read_text().splitlines()
    assert log[0].split()[1] == "OK" and log[1].split()[1] == "FAIL"
    raw = next(p for p in before if p.suffix == ".gz")
    assert json.load(gzip.open(raw, "rt"))["fetched_at"].endswith("Z")
