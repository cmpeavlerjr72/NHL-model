"""SB-R4 rating constructions (docs/models/block/experiments.md SB-R4, D32): arena-free as-of block ratings.

  Rr  road games only, for both ratings: a team's counts from its HOME games (non-neutral) are not accumulated; neutral-site
      games count as road for both teams (as build_arena does).
  Ra  all games, each game's blocked counts (for and against) divided by exp(arena_f) of the game's arena, where arena_f is the
      as-of block-recording factor of arena_v1 (past games only), before accumulating. Attempt counts are unchanged.
Everything else (b 1000, w 0.7, log-odds relative to the snapshot league mean, created_at < puck_drop) is data.asof_block_ratings.
Output columns carry the SB-R1 names (`rf_es_w0.7_b1000`, ...), so data.assemble() consumes them unchanged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block import data as D
from nhl_sim.data.load import PROCESSED
from nhl_sim.strength_state.tables import assert_pregame

W_, B_ = 0.7, 1000


def build_ratings_variant(a: pd.DataFrame, games: pd.DataFrame, arena: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode not in ("Rr", "Ra"):
        raise ValueError(mode)
    r = D.attach_ids(a, games)
    r = r[r.grp <= 2].assign(y=lambda x: x.blocked.astype(float))
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet",
                         columns=["game_id", "season", "date", "drop", "team_id"])
    tg = tg[tg.season.isin(D.SEASONS)].reset_index(drop=True)
    gm = games[["game_id", "home_id", "away_id", "neutral_site"]]
    tg = tg.merge(gm, on="game_id", how="left", validate="many_to_one")
    tg["is_road"] = (tg.team_id == tg.away_id) | tg.neutral_site.astype(bool)
    tg = tg.merge(arena[["game_id", "arena_f"]], on="game_id", how="left", validate="many_to_one")
    if tg.arena_f.isna().any():
        raise ValueError("games without an arena factor")
    longs = {}
    for gi_, g in enumerate(D.RG):
        fo = r[r.grp == gi_].groupby(["game_id", "team_id"]).agg(xf=("y", "sum"), nf=("y", "size"))
        ag = r[r.grp == D.OPP_RG[gi_]].groupby(["game_id", "opp_id"]).agg(xa=("y", "sum"), na=("y", "size"))
        ag.index = ag.index.set_names(["game_id", "team_id"])
        L = tg.join(fo, on=["game_id", "team_id"]).join(ag, on=["game_id", "team_id"])
        L = L.fillna({"xf": 0.0, "nf": 0, "xa": 0.0, "na": 0})
        if mode == "Rr":
            keep = L.is_road.to_numpy()
            for c in ("xf", "nf", "xa", "na"):
                L[c] = np.where(keep, L[c], 0.0)
        else:
            adj = np.exp(-L.arena_f.to_numpy())
            L["xf"] = L.xf.to_numpy() * adj
            L["xa"] = L.xa.to_numpy() * adj
        longs[g] = L.sort_values(["date", "game_id"])
    grid = tg[["game_id", "team_id"]].copy()
    first = True
    for g in D.RG:
        rr = D.asof_block_ratings(longs[g], W_, B_)
        assert_pregame(rr)
        k = D.wkey(W_, B_)
        rr = rr.rename(columns={"rf": f"rf_{g}_{k}", "ra": f"ra_{g}_{k}"})
        keep = ["game_id", "team_id", f"rf_{g}_{k}", f"ra_{g}_{k}"]
        if first:
            keep += ["created_at", "puck_drop"]
            first = False
        grid = grid.merge(rr[keep], on=["game_id", "team_id"], how="left", validate="one_to_one")
    if grid.drop(columns=["created_at"]).isna().any().any():
        raise ValueError("missing ratings")
    return grid
