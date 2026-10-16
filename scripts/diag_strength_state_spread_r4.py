"""SS-R4 step 1 (INV-29) diagnosis: offline quintile spread ratio of the incumbent H3'' (and H2'') on fold 1 and fold 2.
spread ratio = (predicted Q5 - Q1) / (actual Q5 - Q1), penalties taken per 60 by team-game quintile of the rating
(own taken-rating; opponent drawn-rating). Quintiles are cut on team-games (rank, as in grade_strength_state.py).
Phases (regular season, game_type 2): Oct-Nov, Dec-Jan, Feb-Apr; 'PO' = playoffs (reported, underpowered).
Importable: spread_table(rows, mu, mask) is reused by the SS-R4 arm runner.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402

NB, SEED = 500, 20261015
PHASES = {"Oct-Nov": (10, 11), "Dec-Jan": (12, 1), "Feb-Apr": (2, 3, 4)}


def add_phase(rows):
    g = load_games(sorted(rows.season.unique()), columns=["game_id", "game_date_local"])
    d = rows.merge(g, on="game_id", how="left")
    m = pd.to_datetime(d.game_date_local).dt.month
    ph = np.full(len(d), "other", object)
    for k, ms in PHASES.items():
        ph[m.isin(ms).to_numpy()] = k
    ph[(d.game_type != 2).to_numpy()] = "PO"
    return ph


def spread_table(rows, mu, mask=None, nb=NB):
    """-> dict col -> (ratio, se, pred_spread, actual_spread, n_team_games, per-quintile frame)."""
    r = rows.assign(mu=mu)
    if mask is not None:
        r = r[np.asarray(mask)]
    tg = r.groupby(["game_id", "team"]).agg(pred=("mu", "sum"), actual=("y", "sum"), expo=("exposure_s", "sum"),
                                            taken=("taken_own", "first"), drawn_opp=("drawn_opp", "first")).reset_index()
    games = np.sort(tg.game_id.unique())
    gpos = np.searchsorted(games, tg.game_id.to_numpy())
    G = len(games)
    rng = np.random.default_rng(SEED)
    w = rng.multinomial(G, np.ones(G) / G, size=nb).astype(float)  # bootstrap game weights
    out = {}
    for col in ("taken", "drawn_opp"):
        q = (pd.qcut(tg[col].rank(method="first"), 5, labels=False)).to_numpy()
        M = {k: np.zeros((G, 5)) for k in ("pred", "actual", "expo")}
        for k in M:
            np.add.at(M[k], (gpos, q), tg[k].to_numpy())
        def ratio(P, A, E):
            pp, aa = P / E * 3600, A / E * 3600
            return (pp[..., 4] - pp[..., 0]), (aa[..., 4] - aa[..., 0])
        ps, as_ = ratio(M["pred"].sum(0), M["actual"].sum(0), M["expo"].sum(0))
        bp = np.einsum("bg,gq->bq", w, M["pred"]); ba = np.einsum("bg,gq->bq", w, M["actual"])
        be = np.einsum("bg,gq->bq", w, M["expo"])
        bps, bas = ratio(bp, ba, be)
        br = bps / bas
        fr = pd.DataFrame({"pred_per60": M["pred"].sum(0) / M["expo"].sum(0) * 3600,
                           "actual_per60": M["actual"].sum(0) / M["expo"].sum(0) * 3600})
        out[col] = dict(ratio=float(ps / as_), se=float(np.nanstd(br, ddof=1)), pred_spread=float(ps),
                        actual_spread=float(as_), n_team_games=len(tg), q=fr)
    return out


def main():
    base = Path("results/strength_state_r3")
    lab = json.loads((base / "labels_sealed.json").read_text())
    f2 = pd.read_parquet(base / "fold2_rows.parquet")
    f1 = pd.read_parquet(base / "fold1" / "rows_r3.parquet")
    gt = load_games([20212022, 20222023, 20232024, 20242025], columns=["game_id", "game_type"])
    f1 = f1.merge(gt, on="game_id", how="left") if "game_type" not in f1 else f1
    f2 = f2.merge(gt, on="game_id", how="left") if "game_type" not in f2 else f2
    sets = {("fold1", "H3''"): (f1, np.load(base / "fold1" / "pred_r3_H3.npy")),
            ("fold1", "H2''"): (f1, np.load(base / "fold1" / "pred_r3_H2.npy")),
            ("fold2", "H3''"): (f2, np.load(base / f"fold2_haz_{lab['H3']}.npy")),
            ("fold2", "H2''"): (f2, np.load(base / f"fold2_haz_{lab['H2']}.npy"))}
    recs = []
    for (fold, arm), (rows, mu) in sets.items():
        ph = add_phase(rows)
        for name, mask in [("all", np.ones(len(rows), bool))] + [(p, ph == p) for p in list(PHASES) + ["PO"]]:
            t = spread_table(rows, mu, mask)
            for col, lbl in (("taken", "own taken"), ("drawn_opp", "opp drawn")):
                recs.append(dict(fold=fold, arm=arm, phase=name, rating=lbl, ratio=t[col]["ratio"], se=t[col]["se"],
                                 pred_spread=t[col]["pred_spread"], actual_spread=t[col]["actual_spread"],
                                 n_team_games=t[col]["n_team_games"]))
    df = pd.DataFrame(recs)
    out = Path("results/strength_state_r4")
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "diag_spread_incumbent.csv", index=False)
    print(df.to_string(float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
