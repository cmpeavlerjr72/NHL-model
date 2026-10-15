import pytest

from nhl_sim.data import load
from nhl_sim.data.seal import SEALED_SEASON, SealedSeasonError, assert_not_sealed

pytestmark = pytest.mark.skipif(not (load.PROCESSED / "games.parquet").exists(), reason="no processed data")


@pytest.fixture(autouse=True)
def _sealed(monkeypatch):
    monkeypatch.delenv("NHL_UNSEAL_2025", raising=False)


def test_assert_not_sealed_variants():
    for obj in (SEALED_SEASON, [20232024, SEALED_SEASON]):
        with pytest.raises(SealedSeasonError):
            assert_not_sealed(obj)
    import pandas as pd
    with pytest.raises(SealedSeasonError):
        assert_not_sealed(pd.DataFrame({"season": [20232024, SEALED_SEASON]}))
    assert_not_sealed([20232024, 20242025])


@pytest.mark.parametrize("fn", ["load_games", "load_events", "load_shifts", "load_player_box", "load_goalie_box",
                                "load_verified_finals", "load_schedule"])
def test_explicit_request_refused(fn):
    with pytest.raises(SealedSeasonError):
        getattr(load, fn)(seasons=[SEALED_SEASON])


def test_games_and_finals_default_exclude_sealed():
    for df in (load.load_games(), load.load_verified_finals(), load.load_schedule()):
        assert SEALED_SEASON not in set(df.season)
        assert 20242025 in set(df.season)


@pytest.mark.parametrize("fn", ["load_events", "load_shifts", "load_player_box", "load_goalie_box"])
def test_per_season_default_exclude_sealed(fn):
    df = getattr(load, fn)(seasons=[20232024, 20242025], columns=None) if False else getattr(load, fn)(columns=["season", "game_id"])
    assert SEALED_SEASON not in set(df.season)
    assert {20212022, 20242025} <= set(df.season)


def test_reference_name_refused():
    with pytest.raises(SealedSeasonError):
        load.load_reference(f"gate_targets_{SEALED_SEASON}")

