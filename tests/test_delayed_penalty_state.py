"""SS-R2 change 1: a penalty that follows a delayed-penalty signal gets the PRE-signal state (not 'other'), and the
seconds between the signal and the whistle are exposure in that state. A trailing-team pull with no signal keeps
'other'. v1 behaviour (delayed_fix=False) is unchanged."""
import numpy as np
import pandas as pd

from nhl_sim.strength_state.tables import season_rows
from nhl_sim.strength_state.timeline import EV_COLS

GID = 2024020001


def _ev(rows):
    out = []
    for so, (ev, t, home, code, pen) in enumerate(rows):
        r = dict(game_id=GID, season=20242025, game_type=2, sort_order=so, event=ev,
                 period=min(t // 1200 + 1, 3), period_type="REG", game_time_s=t, owner_is_home=home,
                 situation_code=code, pen_type=None, pen_desc=None, pen_minutes=np.nan, pen_committed_by=np.nan,
                 pen_served_by=np.nan, home_score_pre=0, away_score_pre=0)
        if pen:
            r.update(pen_type="MIN", pen_desc="tripping", pen_minutes=2.0, pen_committed_by=8470000 + so)
        out.append(r)
    return pd.DataFrame(out)[EV_COLS]


def _game(extra):
    base = [("PERIOD_START", 0, None, "1551", False), ("FACEOFF", 0, None, "1551", False)]
    tail = [("PERIOD_END", 1200, None, "1551", False), ("PERIOD_START", 1200, None, "1551", False),
            ("PERIOD_END", 2400, None, "1551", False), ("PERIOD_START", 2400, None, "1551", False),
            ("PERIOD_END", 3600, None, "1551", False), ("GAME_END", 3600, None, "1551", False)]
    return _ev(sorted(base + extra + tail, key=lambda r: r[1]))   # stable: sort order follows the clock


def _row_of_penalty(rows, types, team):
    r = types[types.team == team].iloc[0].row
    return rows[(rows.row == r) & (rows.team == team)].iloc[0]


# signal against HOME at 100 s; AWAY pulls its goalie (code 0651 = away goalie out, 6 away skaters); whistle and
# home penalty at 110 s. The pbp stamps the signal itself with the post-pull code (seen in the data).
DELAYED = [("SHOT", 90, False, "1551", False), ("DELAYED_PENALTY", 100, True, "0651", False),
           ("SHOT", 105, False, "0651", False), ("PENALTY", 110, True, "0651", True),
           ("FACEOFF", 110, None, "1541", False)]


def test_penalty_after_signal_gets_pre_signal_state():
    ev = _game(DELAYED)
    rows1, types1, _, _ = season_rows(ev, delayed_fix=False)
    rows2, types2, _, tl = season_rows(ev, delayed_fix=True)
    assert len(types1) == len(types2) == 1
    assert int(types1.iloc[0].st) == 5                     # v1: 'other' (goalie pulled)
    assert int(types2.iloc[0].st) == 0                     # v2: 5v5, the state at the signal
    r = _row_of_penalty(rows2, types2, 0)
    assert int(r.st) == 0 and int(r.y) == 1
    # the seconds 100..109 are 5v5 exposure for both teams, no 'other' second remains
    assert int(rows2[rows2.st == 5].exposure_s.sum()) == 0
    assert int(rows1[(rows1.st == 5)].exposure_s.sum()) == 2 * 10
    assert tl["delayed_changed_s"] == 10
    assert rows1.exposure_s.sum() == rows2.exposure_s.sum()
    assert rows1.y.sum() == rows2.y.sum() == 1


def test_trailing_pull_without_signal_keeps_other():
    ev = _game([("SHOT", 3500, False, "0651", False), ("PENALTY", 3510, True, "0651", True),
                ("FACEOFF", 3510, None, "0641", False)])
    _, types2, _, _ = season_rows(ev, delayed_fix=True)
    assert int(types2.iloc[0].st) == 5


def test_pull_before_signal_stays_pulled():
    # away pulled at 3500 (trailing), signal against home at 3505, penalty at 3510: the pre-signal state is 'other'
    ev = _game([("SHOT", 3500, False, "0651", False), ("DELAYED_PENALTY", 3505, True, "0651", False),
                ("PENALTY", 3510, True, "0651", True), ("FACEOFF", 3510, None, "0641", False)])
    _, types2, _, _ = season_rows(ev, delayed_fix=True)
    assert int(types2.iloc[0].st) == 5
