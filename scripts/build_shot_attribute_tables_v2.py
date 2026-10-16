"""SL-R6 step 1a: arena-free as-of shot-quality ratings (docs/models/shot_attribute/experiments.md SL-R6; D32).

Same rating as SL-R1 (shrunk mean xG_ref per unblocked attempt, log ratio to the snapshot league mean, per rating
group ES / PP / PK, for and against, w 0.7, b 1,000, fold-specific xG_ref), built two new ways:

  Qr  road games only: a team's for-rating accumulates only its attempts in games it plays on the road, its
      against-rating only the attempts it allows on the road (both teams' road games at neutral sites count as road,
      as in the arena factor). The as-of rating is still served for every game. League mean = road accumulations.
  Qa  all games; each attempt's xG_ref is looked up at its ARENA-ADJUSTED location before accumulating: recorded
      distance d -> d x exp(-arena_f), with arena_f the as-of arena distance factor of the game's arena
      (arena_dist_v1, past games only); the angle is kept (sx, sy scaled toward the goal-line centre together), the
      cell is re-banded from the adjusted distance, behind-the-net stays behind (labelled reading).

    build_shot_attribute_tables_v2.py ratings   -> data/processed/shot_attribute/sq_ratings_v2_f{1,2}.parquet
created_at < puck_drop asserted on every row.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_shot_attribute_tables import FOLD_SEASONS, OPP_RG, RG, attach_ids, load_rows, team_games  # noqa: E402
from nhl_sim.data.load import PROCESSED  # noqa: E402
from nhl_sim.shot_attribute.tables import BANDS, GOAL_X, N_TYPE, asof_sq_ratings  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

OUT = PROCESSED / "shot_attribute"
W, B = 0.7, 1000
CONS = ("Qr", "Qa")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def adjusted_cls(u: pd.DataFrame, arena_f: np.ndarray) -> np.ndarray:
    dx = GOAL_X - u.sx.to_numpy(float)
    sy = u.sy.to_numpy(float)
    d = np.sqrt(dx ** 2 + sy ** 2) * np.exp(-arena_f)
    ang = np.degrees(np.arctan2(np.abs(sy), np.maximum(dx, 0.0)))
    band = np.searchsorted(np.asarray(BANDS), d, side="right")
    cell = np.where(u.sx.to_numpy(float) > GOAL_X, 12, 2 * band + (ang > 30.0))
    return cell.astype(np.int64) * N_TYPE + u.type6.to_numpy().astype(np.int64)


def longs_for(u, tg, xgcol, road_only):
    out = {}
    for gi_, g in enumerate(RG):
        fo = u[u.grp == gi_].groupby(["game_id", "team_id"]).agg(xf=(xgcol, "sum"), nf=(xgcol, "size"))
        ag = u[u.grp == OPP_RG[gi_]].groupby(["game_id", "opp_id"]).agg(xa=(xgcol, "sum"), na=(xgcol, "size"))
        ag.index = ag.index.set_names(["game_id", "team_id"])
        L = tg.join(fo, on=["game_id", "team_id"]).join(ag, on=["game_id", "team_id"])
        L = L.fillna({"xf": 0.0, "nf": 0, "xa": 0.0, "na": 0})
        if road_only:
            home = L.road.to_numpy() == 0
            L.loc[home, ["xf", "nf", "xa", "na"]] = 0.0
        out[g] = L.sort_values(["date", "game_id"])
    return out


def ratings():
    af = pd.read_parquet(OUT / "arena_dist_v1.parquet", columns=["game_id", "arena_f"])
    from nhl_sim.data.load import load_games
    for f, seas in FOLD_SEASONS.items():
        t0 = time.time()
        x = np.load(OUT / f"xg_ref_v1_f{f}.npy")
        r = attach_ids(load_rows(seas))
        u = r[~r.blocked & (r.grp <= 2)].copy()
        u["xg"] = x[u.cls.to_numpy(), u.grp.to_numpy()]
        u = u.merge(af, on="game_id", how="left", validate="many_to_one")
        if u.arena_f.isna().any():
            raise ValueError("attempts without an arena factor")
        ca = adjusted_cls(u, u.arena_f.to_numpy())
        u["xg_adj"] = x[ca, u.grp.to_numpy()]
        moved = float((ca != u.cls.to_numpy()).mean())
        tg = team_games(seas)
        g = load_games(seas, columns=["game_id", "neutral_site"])
        tg = tg.merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
        tg["road"] = ((tg.is_home == 0) | tg.neutral_site.astype(bool)).astype(np.int8)
        grid = tg[["game_id", "team_id"]].copy()
        for con, (col, road) in {"Qr": ("xg", True), "Qa": ("xg_adj", False)}.items():
            L = longs_for(u, tg, col, road)
            for gname in RG:
                rr = asof_sq_ratings(L[gname], W, B)
                assert_pregame(rr)
                rr = rr.rename(columns={"rf": f"rf_{gname}_{con}", "ra": f"ra_{gname}_{con}"})
                keep = ["game_id", "team_id", f"rf_{gname}_{con}", f"ra_{gname}_{con}"]
                if "created_at" not in grid.columns:
                    keep += ["created_at", "puck_drop"]
                grid = grid.merge(rr[keep], on=["game_id", "team_id"], how="left", validate="one_to_one")
        if grid.drop(columns=["created_at"]).isna().any().any():
            raise ValueError("missing ratings")
        grid.to_parquet(OUT / f"sq_ratings_v2_f{f}.parquet", index=False)
        old = pd.read_parquet(OUT / f"sq_ratings_v1_f{f}.parquet",
                              columns=["game_id", "team_id", "rf_es_w0.7_b1000", "ra_es_w0.7_b1000"])
        j = grid.merge(old, on=["game_id", "team_id"])
        print(now(), f"fold {f}: rows {len(grid)}; attempts re-celled by arena adj {moved:.2%}; SD rf_es Qr "
              f"{grid.rf_es_Qr.std():.4f} Qa {grid.rf_es_Qa.std():.4f} (orig {j['rf_es_w0.7_b1000'].std():.4f}); corr "
              f"with orig rf_es Qr {j.rf_es_Qr.corr(j['rf_es_w0.7_b1000']):.3f} Qa {j.rf_es_Qa.corr(j['rf_es_w0.7_b1000']):.3f}"
              f" ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    print(now(), "start ratings v2", flush=True)
    ratings()
    print(now(), "done", flush=True)
