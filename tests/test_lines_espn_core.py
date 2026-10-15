import json
from pathlib import Path

import pytest

from nhl_sim.lines_espn_core import AmbiguousProviders, implied, parse_event, vig_outliers

FIX = Path(__file__).parent / "fixtures" / "espn_core_odds_401688304.json"


def _rows():
    import pandas as pd
    rows, info = parse_event(json.loads(FIX.read_text(encoding="utf-8")), 2024020001, 20242025)
    return pd.DataFrame(rows), info


def test_live_item_dropped():
    df, info = _rows()
    assert info["n_items"] == 2 and info["n_live_dropped"] == 1
    assert info["live_names"] == ["ESPN Bet - Live Odds"]
    assert set(df.provider) == {"ESPN BET"}
    assert not df.close_price.isin([-3000, 1000]).any()


def test_values():
    df, _ = _rows()
    ml = df[df.market == "ml"].set_index("side_or_line")
    assert (ml.loc["away", "open_price"], ml.loc["away", "close_price"]) == (-170, -185)
    assert (ml.loc["home", "open_price"], ml.loc["home", "close_price"]) == (145, 155)
    pl = df[df.market == "pl"].set_index("side_or_line")
    assert (pl.loc["away", "open_line"], pl.loc["away", "close_line"]) == (-1.5, -1.5)
    assert (pl.loc["away", "open_price"], pl.loc["away", "close_price"]) == (140, 130)
    tot = df[df.market == "total"].set_index("side_or_line")
    assert (tot.loc["over", "open_line"], tot.loc["over", "close_line"]) == (6.5, 5.5)
    assert (tot.loc["over", "open_price"], tot.loc["over", "close_price"]) == (120, -130)
    assert len(df) == 6


def test_vig_in_range():
    df, _ = _rows()
    out, series = vig_outliers(df)
    assert out.empty and 1.0 < series.vig_sum.iloc[0] < 1.10
    assert implied(-185) == pytest.approx(185 / 285)


def test_duplicate_pregame_provider_is_ambiguous():
    raw = json.loads(FIX.read_text(encoding="utf-8"))
    raw["items"] = [raw["items"][0], raw["items"][0]]
    with pytest.raises(AmbiguousProviders):
        parse_event(raw, 1, 20242025)
