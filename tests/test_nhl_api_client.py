import json
from pathlib import Path

import pytest

from nhl_sim.clients.nhl_api import NHLApiClient
from nhl_sim.pbp.event_map import EVENT_MAP, UnknownEventType, map_event

FIX = Path(__file__).parent / "fixtures"


class FakeResp:
    def __init__(self, data, code=200):
        self.data, self.status_code = data, code

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, data):
        self.data, self.calls, self.headers = data, 0, {}

    def get(self, url, timeout=None):
        self.calls += 1
        return FakeResp(self.data)


def test_pbp_cached_after_first_fetch(tmp_path):
    data = json.load(open(FIX / "pbp_2026020107.json", encoding="utf-8"))
    s = FakeSession(data)
    cl = NHLApiClient(cache_dir=tmp_path, session=s)
    assert cl.pbp(2026020107)["id"] == 2026020107
    assert cl.pbp(2026020107)["id"] == 2026020107
    assert s.calls == 1 and cl.n_cached == 1
    assert (tmp_path / "pbp" / "2026020107.json").exists()
    assert "User-Agent" in s.headers


def test_live_game_not_cached(tmp_path):
    data = dict(json.load(open(FIX / "pbp_2026020107.json", encoding="utf-8")), gameState="LIVE")
    s = FakeSession(data)
    cl = NHLApiClient(cache_dir=tmp_path, session=s)
    cl.pbp(1)
    cl.pbp(1)
    assert s.calls == 2


def test_fixture_event_types_all_mapped():
    data = json.load(open(FIX / "pbp_2026020107.json", encoding="utf-8"))
    for p in data["plays"]:
        map_event(p["typeDescKey"])


def test_unknown_event_type_fails():
    with pytest.raises(UnknownEventType):
        map_event("some-new-event-type")
    assert "goal" in EVENT_MAP


def test_empty_shift_chart_not_cached(tmp_path):
    s = FakeSession({"data": [], "total": 0})
    cl = NHLApiClient(cache_dir=tmp_path, session=s)
    cl.shifts(1)
    cl.shifts(1)
    assert s.calls == 2
