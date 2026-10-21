"""SL-R7 L1x-as engine tables (engine/sim.py attr["l1x"]; docs/models/shot_attribute/experiments.md SL-R7, D42).

Served class logits per unblocked attempt (non-EN team-view states 0..4):
  log state_pdf[st, ptype] + log game_mult[g, rg]                   (L0s levelled by M1 K500: engine.c1s_tables)
  + game_logit[g, team, rg] = (is_home - xbar) W_home + (b2b_own - xbar) W_b2b_own + (b2b_opp - xbar) W_b2b_opp
                              + (s_for,t zf + s_against,t za) c[:, rg]
  + sc_logit[ptype, sc7]    = sum_k ((sc == k) - xbar_k) W_sc_k on regulation rows; 0 on OT rows (L1x-ot0, D38)
W / xbar: the frozen SL-R6 L1x-ot0 fold-2 fit; (s_for,t, s_against,t): the selected cell's committed per-date snapshot
(data/processed/shot_attribute/sq_scale_v1_f2.parquet), keyed by the game date; zf = own Qa "for" of the row's rating
group / SD, za = the opponent's Qa "against" of the opposing rating group / SD (shot_attribute.tables RATING_GROUP /
OPP_RATING_GROUP); c = models_x.qdir(xG_ref fold 2) of the group.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED, load_games
from nhl_sim.shot_attribute import models as M
from nhl_sim.shot_attribute import models_x as MX
from nhl_sim.shot_attribute.tables import N_CLASS, OPP_RATING_GROUP

R6 = Path("results/shot_attribute_r6_d38")
R7 = Path("results/shot_attribute_r7")
SNAP = M.SA / "sq_scale_v1_f2.parquet"
LABEL = "stage 4: L1x-as (SL-R7, D42; L1x-ot0 + as-of Qa scale H45 P10000 on L0s M1 K500)"
GRP = ("es", "pp", "pk")


def l1xas_tables(games: np.ndarray) -> tuple[dict, dict]:
    games = np.asarray(games, np.int64)
    m = json.loads((R6 / "models" / "L1x.json").read_text())
    if not (m.get("ot0") is True and m.get("construction") == "Qa"):
        raise ValueError("expected the SL-R6 L1x-ot0 (Qa) fold-2 model")
    W, xbar = np.asarray(m["W"], np.float64), np.asarray(m["xbar"], np.float64)
    if W.shape != (len(MX.FEATS), N_CLASS):
        raise ValueError("W shape")
    sel = json.loads((R7 / "select.json").read_text())["selected"]
    sc = pd.read_parquet(SNAP)
    sc = sc[sc.cell == sel]
    sd_f, sd_a = float(sc.sd_for.iloc[0]), float(sc.sd_against.iloc[0])
    C = MX.qdir(np.load(M.SA / "xg_ref_v1_f2.npy"))                  # (78, 5)
    g = load_games(None, columns=["game_id", "home_id", "away_id", "game_date_local"]).set_index("game_id").loc[games]
    dkey = pd.to_datetime(g.game_date_local).to_numpy("datetime64[D]")
    idx = pd.to_datetime(sc.date).to_numpy("datetime64[D]")
    sf = pd.Series(sc.s_for.to_numpy(), index=idx).reindex(dkey).to_numpy()
    sa = pd.Series(sc.s_against.to_numpy(), index=idx).reindex(dkey).to_numpy()
    q = pd.read_parquet(M.SA / "sq_ratings_v2_f2.parquet").set_index(["game_id", "team_id"])
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    b2b = tg.set_index(["game_id", "team_id"]).b2b
    team = np.stack([g.home_id.to_numpy(), g.away_id.to_numpy()], 1).astype(np.int64)

    def at(frame, col, j):
        return frame[col].reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float)
    rf = np.stack([np.stack([at(q, f"rf_{x}_Qa", j) for x in GRP], 1) for j in (0, 1)], 1)    # (G, 2, 3)
    ra = np.stack([np.stack([at(q, f"ra_{x}_Qa", j) for x in GRP], 1) for j in (0, 1)], 1)
    B = np.stack([b2b.reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float) for j in (0, 1)], 1)
    for nm, v in (("scale", sf), ("scale", sa), ("Qa", rf), ("Qa", ra), ("b2b", B)):
        if np.isnan(v).any():
            raise ValueError(f"games without {nm}")
    F = MX.FEATS
    wi = {f: F.index(f) for f in F}
    gl = np.zeros((len(games), 2, 3, N_CLASS))
    for j in (0, 1):
        base = ((1.0 - j) - xbar[wi["is_home"]]) * W[wi["is_home"]] \
            + (B[:, j, None] - xbar[wi["b2b_own"]]) * W[wi["b2b_own"]] \
            + (B[:, 1 - j, None] - xbar[wi["b2b_opp"]]) * W[wi["b2b_opp"]]
        for rg in range(3):
            zf = rf[:, j, rg] / sd_f
            za = ra[:, 1 - j, OPP_RATING_GROUP[rg]] / sd_a
            gl[:, j, rg] = base + (sf * zf + sa * za)[:, None] * C[:, rg][None, :]
    scl = np.zeros((2, 7, N_CLASS))
    for s7 in range(7):
        for k in (0, 1, 2, 4, 5, 6):
            f = f"sc{k}"
            scl[0, s7] += (float(s7 == k) - xbar[wi[f]]) * W[wi[f]]
    return dict(game_logit=gl, sc_logit=scl, label=LABEL), dict(cell=sel, sd=(sd_f, sd_a), label=LABEL)


def l1xas_parity(games, state_pdf, gm, l1x) -> dict:
    """Engine-served class probabilities (increments of sim.class_cdf) vs the offline SL-R7 L1x-as fold-2 prediction
    file, every reachable (st <= 4) unblocked fold-2 row; EN rows are served L0s offline and are unreachable."""
    from nhl_sim.engine import sim as SIM
    lab = json.loads((R7 / "labels_sealed.json").read_text())["L1xas"]
    rows = pd.read_parquet(R7 / "fold2_rows.parquet", columns=["game_id", "team", "st", "ptype", "sc"])
    pred = np.load(R7 / f"fold2_pred_{lab}.npy").astype(np.float64)
    pos = pd.Series(np.arange(len(games)), index=np.asarray(games)).reindex(rows.game_id.to_numpy()).to_numpy()
    if np.isnan(pos).any():
        raise ValueError("rows of games not in the engine order")
    gi = pos.astype(np.int64)
    st = rows.st.to_numpy().astype(np.int64)
    AS = dict(state_pdf=state_pdf, game_mult=gm, l1x_game=l1x["game_logit"], l1x_sc=l1x["sc_logit"],
              l1x_base=np.log(state_pdf), l1x_lgm=np.log(gm))
    d = np.zeros(len(rows))
    for pt in (0, 1):
        for team in (0, 1):
            k = (rows.ptype.to_numpy() == pt) & (rows.team.to_numpy() == team) & (st <= 4)
            if k.any():
                cdf = SIM.class_cdf(AS, None, gi[k], team, st[k], rows.sc.to_numpy().astype(np.int64)[k], None, 3600 * pt)
                d[k] = np.abs(np.diff(cdf, axis=1, prepend=0.0) - pred[k]).max(1)
    reach = st <= 4
    return dict(n_rows=int(reach.sum()), max_abs_diff=float(d[reach].max()), n_en_rows_not_served=int((~reach).sum()),
                note="offline file is float32 (rounding about 3e-8)")
