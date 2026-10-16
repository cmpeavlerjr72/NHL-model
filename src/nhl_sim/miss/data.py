"""SM-R1 data layer (docs/models/miss/experiments.md SM-R1; cascade stage 5b, miss vs on-goal decision; D23).

Rows: one per UNBLOCKED, non-shootout, non-penalty-shot attempt (event SHOT, MISS, GOAL) from the stage-4 attempt tables
`data/processed/shot_attribute/attempt_attr_v1_*.parquet` (read only). y = 1 if the attempt is a MISS (the NHL feed's
`missed-shot`, which includes posts and crossbars). A goal counts as on goal.

Everything here reuses the SB-R1 / SB-R4 construction family (`nhl_sim.block.data`, read only) through thin wrappers that
swap the target: the block code reads the column `blocked`, so the wrappers pass a frame whose `blocked` column is the miss
indicator (on unblocked rows the true block flag is all False, so nothing is lost). Level groups ES (+EN), PP, PK; level =
as-of league MISS SHARE per level group, entered as a logit offset logit(s_asof) - logit(s_train), coefficient 1.

Ratings: the shooting team's ROAD-ONLY as-of miss rating (Rr construction of SB-R4: a team's home games are not accumulated;
neutral-site games count as road for both teams), b 1000 / w 0.7 as in SB-R4 (inherited, not tuned here), log-odds relative
to the snapshot league mean. Arena factor: as-of miss-recording factor (block's `build_arena` with d := miss, c = 1200,
inherited), past games only. created_at < puck_drop is asserted on every table.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.block import data as D
from nhl_sim.data.load import PROCESSED
from nhl_sim.strength_state.tables import assert_pregame

SA = PROCESSED / "shot_attribute"
OUT = PROCESSED / "miss"
SEASONS = D.SEASONS
W_, B_ = 0.7, 1000
logit, sigmoid = D.logit, D.sigmoid
COLS = ["game_id", "season", "game_type", "sort_order", "t", "team", "is_home", "event", "blocked", "is_goal", "st", "grp",
        "sc", "period", "ptype", "cell", "type6", "cls", "rebound", "rush"]


def load_rows(seasons=SEASONS) -> pd.DataFrame:
    """Unblocked rows with y = miss."""
    a = pd.concat([pd.read_parquet(SA / f"attempt_attr_v1_{s}.parquet", columns=COLS) for s in seasons], ignore_index=True)
    a = a[~a.blocked].reset_index(drop=True)
    a["y"] = (a.event == "MISS").astype(np.int8)
    if (a.cls < 0).any():
        raise ValueError("unblocked row without a joint class")
    return a


def _b(a: pd.DataFrame) -> pd.DataFrame:
    """Frame for the block-code wrappers: `blocked` := miss."""
    return a.assign(blocked=a.y.astype(bool))


def game_table() -> pd.DataFrame:
    return D.game_table()


def asof_levels(a, games, specs):
    return D.asof_levels(_b(a), games, specs)


def share_table(a) -> np.ndarray:
    return D.share_table(_b(a))


def era_level(a_train, games) -> np.ndarray:
    return D.era_level(_b(a_train), games)


level_frame = D.level_frame
row_offset = D.row_offset


def build_arena(a, games) -> pd.DataFrame:
    af = D.build_arena(_b(a), games)
    assert_pregame(af)
    return af


def build_ratings_road(a, games) -> pd.DataFrame:
    """Road-only as-of miss ratings (SB-R4 Rr construction on the miss target), groups ES / PP / PK. Columns carry the SB-R1
    names (`rf_es_w0.7_b1000`, ...) so block.data.assemble consumes them. rf = the team's own (shooting) miss rating,
    ra = the rating of misses against (unused by SM-R1)."""
    r = D.attach_ids(_b(a), games)
    r = r[r.grp <= 2].assign(y=lambda x: x.blocked.astype(float))
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet",
                         columns=["game_id", "season", "date", "drop", "team_id"])
    tg = tg[tg.season.isin(SEASONS)].reset_index(drop=True)
    gm = games[["game_id", "home_id", "away_id", "neutral_site"]]
    tg = tg.merge(gm, on="game_id", how="left", validate="many_to_one")
    tg["is_road"] = (tg.team_id == tg.away_id) | tg.neutral_site.astype(bool)
    grid = tg[["game_id", "team_id"]].copy()
    first = True
    k = D.wkey(W_, B_)
    for gi_, g in enumerate(D.RG):
        fo = r[r.grp == gi_].groupby(["game_id", "team_id"]).agg(xf=("y", "sum"), nf=("y", "size"))
        ag = r[r.grp == D.OPP_RG[gi_]].groupby(["game_id", "opp_id"]).agg(xa=("y", "sum"), na=("y", "size"))
        ag.index = ag.index.set_names(["game_id", "team_id"])
        L = tg.join(fo, on=["game_id", "team_id"]).join(ag, on=["game_id", "team_id"])
        L = L.fillna({"xf": 0.0, "nf": 0, "xa": 0.0, "na": 0})
        keep = L.is_road.to_numpy()
        for c in ("xf", "nf", "xa", "na"):
            L[c] = np.where(keep, L[c], 0.0)
        L = L.sort_values(["date", "game_id"])
        rr = D.asof_block_ratings(L, W_, B_)
        assert_pregame(rr)
        rr = rr.rename(columns={"rf": f"rf_{g}_{k}", "ra": f"ra_{g}_{k}"})
        cols = ["game_id", "team_id", f"rf_{g}_{k}", f"ra_{g}_{k}"]
        if first:
            cols += ["created_at", "puck_drop"]
            first = False
        grid = grid.merge(rr[cols], on=["game_id", "team_id"], how="left", validate="one_to_one")
    if grid.drop(columns=["created_at"]).isna().any().any():
        raise ValueError("missing ratings")
    return grid


def assemble(a, games, ratings, arena) -> pd.DataFrame:
    """Rows with own_r (shooting team's miss-for rating at the row's rating group), opp_r (defending team's against rating,
    reported only), own_rf_es, b2b, arena_f, clock, l0, y."""
    return D.assemble(_b(a), games, ratings, arena, W_, B_)
