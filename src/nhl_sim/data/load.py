"""Single loader for data/processed and data/reference. Every script reads through here (INV-15).

Default behaviour: sealed 2025-26 rows are silently excluded from broad loads, and an explicit request for the
sealed season raises SealedSeasonError. NHL_UNSEAL_2025=1 lifts both (nobody sets it this session).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from nhl_sim.data.seal import SEALED_SEASON, assert_not_sealed, drop_sealed, is_unsealed

ROOT = Path(__file__).resolve().parents[3]
PROCESSED = ROOT / "data" / "processed"
REFERENCE = ROOT / "data" / "reference"
PER_SEASON = ("events", "shifts", "player_box", "goalie_box")


def _norm_seasons(seasons):
    if seasons is None:
        return None
    if isinstance(seasons, (int,)):
        seasons = [seasons]
    seasons = [int(s) for s in seasons]
    assert_not_sealed(seasons, "load request")
    return seasons


def _read_flat(path: Path, seasons, columns=None) -> pd.DataFrame:
    df = pd.read_parquet(path, columns=columns) if columns is None or "season" in columns else \
        pd.read_parquet(path, columns=[*columns, "season"])
    if seasons is not None:
        df = df[df["season"].isin(seasons)]
    df = drop_sealed(df)
    assert_not_sealed(df, str(path.name))
    return df.reset_index(drop=True)


def load_games(seasons=None, columns=None) -> pd.DataFrame:
    return _read_flat(PROCESSED / "games.parquet", _norm_seasons(seasons), columns)


def load_schedule(seasons=None, columns=None) -> pd.DataFrame:
    return _read_flat(PROCESSED / "schedule.parquet", _norm_seasons(seasons), columns)


def load_per_season(name: str, seasons=None, columns=None) -> pd.DataFrame:
    if name not in PER_SEASON:
        raise ValueError(f"unknown per-season table {name!r}")
    seasons = _norm_seasons(seasons)
    files = sorted((PROCESSED / name).glob(f"{name}_*.parquet"))
    parts = []
    for f in files:
        s = int(f.stem.rsplit("_", 1)[1])
        if s == SEALED_SEASON and not is_unsealed():
            continue  # never even opened
        if seasons is not None and s not in seasons:
            continue
        df = pd.read_parquet(f, columns=columns)
        assert_not_sealed(df if "season" in df.columns else [s], f.name)
        parts.append(df)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def load_events(seasons=None, columns=None):
    return load_per_season("events", seasons, columns)


def load_shifts(seasons=None, columns=None):
    return load_per_season("shifts", seasons, columns)


def load_player_box(seasons=None, columns=None):
    return load_per_season("player_box", seasons, columns)


def load_goalie_box(seasons=None, columns=None):
    return load_per_season("goalie_box", seasons, columns)


def load_verified_finals(version: str = "v1", seasons=None, columns=None) -> pd.DataFrame:
    return _read_flat(REFERENCE / f"verified_finals_{version}.parquet", _norm_seasons(seasons), columns)


def load_reference(name: str, seasons=None) -> pd.DataFrame:
    """Any other reference parquet (e.g. gate_targets_<season>). A name carrying the sealed season id is refused."""
    if str(SEALED_SEASON) in name:
        assert_not_sealed(SEALED_SEASON, name)
    df = pd.read_parquet(REFERENCE / f"{name}.parquet")
    if "season" in df.columns:
        df = _read_flat(REFERENCE / f"{name}.parquet", _norm_seasons(seasons))
    return df
