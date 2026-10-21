"""Shared loaders for the stage 7-8 step-0 audit (INV-65). Training seasons only; reads through nhl_sim.data.load."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
from nhl_sim.data.load import (load_events, load_games, load_shifts, load_goalie_box, load_reference)

SEASONS = [20212022, 20222023, 20232024]   # fold-2 holdout 2024-25 and sealed 2025-26 are never requested
SLAB = {20212022: "2021-22", 20222023: "2022-23", 20232024: "2023-24"}
GT = {2: "RS", 3: "PO"}
OUT = ROOT / "results" / "stage8_step0"
OUT.mkdir(parents=True, exist_ok=True)


def md(df, floatfmt=3):
    return df.to_markdown(floatfmt=f".{floatfmt}f") if len(df) else "(empty)\n"


def games():
    g = load_games(SEASONS)
    assert set(g.season.unique()) <= set(SEASONS)
    return g
