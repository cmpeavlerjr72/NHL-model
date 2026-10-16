"""SA-R1 tables: (1) an unmapped attempt event type (or event / typeDescKey combination) raises; (2) the L20
delayed-penalty state: an attempt inside a delayed-penalty signal window keeps the PRE-signal state (not EN-for),
while a trailing-team pull without a signal stays EN-for / EN-against; (3) penalty shots and shootout attempts are
excluded and tallied."""
import numpy as np
import pandas as pd
import pytest

from nhl_sim.shot_attempt.tables import SA_EV_COLS, UnmappedAttemptEvent, check_event_types, season_rows

GID = 2024020001
HOME, AWAY = 7, 1
TDK = {"SHOT": "shot-on-goal", "MISS": "missed-shot", "BLOCK": "blocked-shot", "GOAL": "goal",
       "DELAYED_PENALTY": "delayed-penalty", "PENALTY": "penalty", "FACEOFF": "faceoff", "PERIOD_START": "period-start",
       "PERIOD_END": "period-end", "GAME_END": "game-end", "STOPPAGE": "stoppage"}


def _ev(rows):
    out = []
    for so, (ev, t, home, code, pen) in enumerate(rows):
        team = None if home is None else (HOME if home else AWAY)
        r = dict(game_id=GID, season=20242025, game_type=2, sort_order=so, event=ev, period=min(t // 1200 + 1, 3),
                 period_type="REG", game_time_s=t, owner_is_home=home, situation_code=code, pen_type=None,
                 pen_desc=None, pen_minutes=np.nan, pen_committed_by=np.nan, pen_served_by=np.nan, home_score_pre=0,
                 away_score_pre=0, type_desc_key=TDK.get(ev, ev.lower()), shooting_team_id=np.nan,
                 owner_team_id=np.nan if team is None else float(team))
        if ev in ("SHOT", "MISS", "BLOCK", "GOAL"):
            r["shooting_team_id"] = float(team)
        if pen:
            r.update(pen_type="MIN", pen_desc="tripping", pen_minutes=2.0, pen_committed_by=8470000 + so)
        out.append(r)
    return pd.DataFrame(out)[SA_EV_COLS]


def _game(extra):
    base = [("PERIOD_START", 0, None, "1551", False), ("FACEOFF", 0, None, "1551", False)]
    tail = [("PERIOD_END", 1200, None, "1551", False), ("PERIOD_START", 1200, None, "1551", False),
            ("PERIOD_END", 2400, None, "1551", False), ("PERIOD_START", 2400, None, "1551", False),
            ("PERIOD_END", 3600, None, "1551", False), ("GAME_END", 3600, None, "1551", False)]
    return _ev(sorted(base + extra + tail, key=lambda r: r[1]))


def _row_holding(rows, team, t):
    r = rows[(rows.team == team) & (rows.t0 <= t) & (rows.t0 + rows.exposure_s > t)]
    assert len(r) == 1
    return r.iloc[0]


def _row_with_attempt(rows, team):
    r = rows[(rows.team == team) & (rows.y > 0)]
    assert len(r) == 1
    return r.iloc[0]


def test_unmapped_event_type_raises():
    ev = _game([("SHOT", 90, False, "1551", False)])
    check_event_types(ev)                                    # mapped: fine
    bad = ev.copy()
    bad.loc[bad.event == "SHOT", "event"] = "WRAPAROUND_SHOT"
    with pytest.raises(UnmappedAttemptEvent):
        check_event_types(bad)
    with pytest.raises(UnmappedAttemptEvent):
        season_rows(bad)
    bad2 = ev.copy()
    bad2.loc[bad2.event == "SHOT", "type_desc_key"] = "missed-shot"   # event / typeDescKey disagree
    with pytest.raises(UnmappedAttemptEvent):
        check_event_types(bad2)


# signal against HOME at 100 s; AWAY pulls its goalie (code 0651); away attempts at 105 inside the window; whistle
# and home penalty at 110. The pbp stamps the signal with the post-pull code (seen in the data).
DELAYED = [("SHOT", 90, False, "1551", False), ("DELAYED_PENALTY", 100, True, "0651", False),
           ("MISS", 105, False, "0651", False), ("PENALTY", 110, True, "0651", True),
           ("FACEOFF", 110, None, "1541", False)]


def test_delayed_penalty_attempt_keeps_pre_signal_state():
    ev = _game(DELAYED)
    rows_fix, _, _, info = season_rows(ev, delayed_fix=True)
    rows_raw, _, _, _ = season_rows(ev, delayed_fix=False)
    assert int(rows_fix.y.sum()) == int(rows_raw.y.sum()) == 2
    # the attempt at 105 (row holding 104): 5v5 under the L20 convention, EN-for without it
    a_fix, a_raw = _row_holding(rows_fix, 1, 104), _row_holding(rows_raw, 1, 104)
    assert int(a_raw.y) == 1 and int(a_fix.y) == 2      # fix: no state change at the signal, one 5v5 row 60..119
    assert int(a_fix.st) == 0
    assert int(a_raw.st) == 5                                # EN-for (own goalie pulled)
    assert int(rows_fix[rows_fix.st >= 5].exposure_s.sum()) == 0
    assert int(rows_raw[(rows_raw.team == 1) & (rows_raw.st == 5)].exposure_s.sum()) == 10
    assert int(rows_raw[(rows_raw.team == 0) & (rows_raw.st == 6)].exposure_s.sum()) == 10
    assert info["delayed_changed_s"] == 10
    # after the penalty: away on the PP (team view PP = 1), home PK
    pp = rows_fix[(rows_fix.team == 1) & (rows_fix.t0 >= 110) & (rows_fix.t0 < 230)]
    assert set(pp.st.unique()) == {1}


def test_trailing_pull_without_signal_is_en():
    # the pull is first visible on the faceoff at 3490 (pbp codes are event-sampled), the attempt follows at 3500
    ev = _game([("FACEOFF", 3490, None, "0651", False), ("SHOT", 3500, False, "0651", False),
                ("STOPPAGE", 3530, None, "0651", False),
                ("FACEOFF", 3530, None, "1551", False)])
    rows, _, _, _ = season_rows(ev, delayed_fix=True)
    a = _row_with_attempt(rows, 1)
    assert int(a.st) == 5
    assert int(rows[(rows.team == 0) & (rows.st == 6)].exposure_s.sum()) > 0


def test_penalty_shot_and_shootout_excluded():
    ev = _game([("SHOT", 90, False, "1551", False), ("GOAL", 500, True, "0101", False)])
    so = ev.iloc[[0]].assign(event="SHOT", type_desc_key="shot-on-goal", period_type="SO", game_time_s=3900,
                             owner_is_home=True, shooting_team_id=float(HOME), owner_team_id=float(HOME),
                             situation_code="0101", sort_order=999)
    rows, _, tally, _ = season_rows(pd.concat([ev, so], ignore_index=True))
    assert int(rows.y.sum()) == 1 and int(rows.y_goal.sum()) == 0
    assert tally["penalty_shot_attempts"] == 1 and tally["penalty_shot_goals"] == 1
    assert tally["shootout_attempts"] == 1
