"""INV-18: 2021-22 types shootout attempts as shot-on-goal / missed-shot / goal (no failed-shot-attempt);
the period_type == 'SO' exclusion must catch all of them, and SO winners must match the boxscore."""
from pathlib import Path

import pandas as pd
import pytest

from nhl_sim.shot_attempt.tables import attempt_events

P = Path(__file__).resolve().parents[1] / "data" / "processed"
EV, GM = P / "events" / "events_20212022.parquet", P / "games.parquet"


@pytest.mark.skipif(not (EV.exists() and GM.exists()), reason="processed tables absent")
def test_2021_22_shootout_excluded_and_winner_matches_box():
    ev = pd.read_parquet(EV)
    tg, tally = attempt_events(ev)
    assert tally["shootout_attempts"] == 747
    so_ids = set(ev[ev.period_type == "SO"].game_id)
    # no target row may sit in a period-5 timestamp of an SO game beyond OT end
    assert tally["failed_shot_attempt_events"] == 0
    att = ev[ev.event.isin(["SHOT", "MISS", "BLOCK", "GOAL"]) & (ev.period_type == "SO")]
    assert len(att) == 747 and att.event.ne("BLOCK").all()
    g = pd.read_parquet(GM).set_index("game_id")
    goals = att[att.event == "GOAL"]
    for gid, x in goals.groupby("game_id"):
        h = int(x.owner_is_home.astype(bool).sum()); a = len(x) - h
        assert h != a and (h > a) == (g.loc[gid, "home_score_box"] > g.loc[gid, "away_score_box"])
    assert so_ids == set(g[(g.season == 20212022) & (g.end_state_box == "SO")].index)
