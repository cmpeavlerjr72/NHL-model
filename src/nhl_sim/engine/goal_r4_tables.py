"""G-R4 engine tables (Lane G4, 2026-10-21): the selected goal arm C1s-sap behind a default-off flag.

C1s-sap = C1s non-score terms (unchanged: the C1s `game_logit` / `cls_logit` of `c1s_tables.goal_c1s_tables`, same
frozen fold-2 coefficients, as-of goalie scale, team finishing, ORACLE GOALIE) + an as-of score term per game and
period that replaces the pooled C1s score dummies:

  sc_game[g, per, sc7] = d_t(date_g)[bucket(sc7)] + T[bucket(sc7), per]     per = 0 / 1 / 2 (P1 / P2 / P3)
  sc_game[g, 3, sc7]   = d_t(date_g)[bucket(sc7)]                           per = 3 (OT: no period interaction)
  d_t   the as-of four-bucket deviations (tied = 0) of `data/processed/goal/score_dev_v1_f2.parquet`, cell H90 P2000
        (G-R4 step 2), the snapshot of the game date (created_at < puck_drop asserted when it was written)
  T     the C1s-sap centred period interactions (results/goal_g_r4/fold2/models/C1s-sap.json `term_table`)
The flag: attr["goal"]["sc_game"] present (sim.goal_prob adds sc_game[g, per, sc] instead of sc_logit[sc]); absent =
the C1s path, bit-identical. EAF (sg 5) carries no score term, as offline.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.engine import c1s_tables as CT
from nhl_sim.goal import score_asof as SA

ROOT = Path(__file__).resolve().parents[3]
R4 = ROOT / "results/goal_g_r4"
SNAP = ROOT / "data/processed/goal/score_dev_v1_f2.parquet"
GOAL_R4_LABEL = "goal: C1s-sap (G-R4: as-of score-bucket deviations H90 P2000 + pooled period interactions)"


def _sap_parts():
    sel = json.loads((R4 / "select.json").read_text())["selected"]
    m = json.loads((R4 / "fold2" / "models" / "C1s-sap.json").read_text())
    if m.get("arm") != "C1s-sap" or m.get("cell") != sel:
        raise ValueError("C1s-sap model file / selected cell mismatch")
    T = np.asarray(m["term_table"], np.float64)
    if T.shape != (5, 3):
        raise ValueError("C1s-sap term_table must be (5, 3)")
    S = pd.read_parquet(SNAP)
    S = S[S.cell == sel]
    return sel, T, S


def sc_game_table(games: np.ndarray) -> tuple[np.ndarray, dict]:
    """(G, 4, 7) served score term per game x period index x team-view score bucket sc7."""
    from nhl_sim.data.load import PROCESSED
    sel, T, S = _sap_parts()
    gtab = pd.read_parquet(PROCESSED / "block" / "games_v1.parquet").set_index("game_id").loc[np.asarray(games)]
    Dg = SA.attach_dev(gtab.date.to_numpy(), S)                          # (G, 4), DEV_B order
    dev5 = np.zeros((len(games), 5))
    dev5[:, list(SA.DEV_B)] = Dg
    b7 = SA.BUCKET_OF_SC
    out = np.zeros((len(games), 4, 7))
    for per in range(4):
        out[:, per, :] = dev5[:, b7] + (T[b7, per][None, :] if per < 3 else 0.0)
    return out, dict(cell=sel, term_table=T.tolist(), snapshot=str(SNAP.relative_to(ROOT)))


def goal_r4_tables(games: np.ndarray, goalie_against: np.ndarray | None = None, P: dict | None = None,
                   scg: np.ndarray | None = None) -> tuple[dict, dict]:
    """-> (attr["goal"] dict with the flag key sc_game, info). sc_logit is zeroed: the score term is sc_game."""
    goal, info = CT.goal_c1s_tables(games, goalie_against, P)
    if scg is None:
        scg, sinfo = sc_game_table(games)
    else:
        sinfo = {}
    goal = dict(goal, sc_logit=np.zeros(7), sc_game=scg, label=GOAL_R4_LABEL)
    return goal, dict(info, label=GOAL_R4_LABEL, score=sinfo)


def served_logit(goal, gi, team, st, sc, cls, per):
    """The engine lookup (sim.goal_prob with the flag), written out for the offline check."""
    return goal["cls_logit"][cls, st] + goal["game_logit"][gi, team, st] + goal["sc_game"][gi, per, sc]


def goal_r4_parity(games, goal, P: dict | None = None, use_engine: bool = True) -> dict:
    """Served C1s-sap probability vs the offline fold-2 C1s-sap prediction (G-R4 file), starter rows on the engine's
    own table, relief rows through the same builder with the relief goalie in the defending slot (as goal_parity)."""
    from nhl_sim.engine import sim as SIM
    P = CT._goal_parts(games) if P is None else P
    lab = json.loads((R4 / "fold2" / "labels_sealed.json").read_text())["C1s-sap"]
    rows = pd.read_parquet(R4 / "fold2" / "fold2_rows.parquet",
                           columns=["game_id", "team_id", "goalie_id", "is_home", "sg", "sc", "period", "cell", "type6", "y"])
    pred = np.load(R4 / "fold2" / f"fold2_pred_{lab}.npy").astype(np.float64)
    m = (rows.sg <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = CT._gpos(games, r.game_id.to_numpy())
    team = np.where(r.is_home.to_numpy() == 1, 0, 1)
    st = r.sg.to_numpy().astype(np.int64)
    sc = r.sc.to_numpy().astype(np.int64)
    per = np.minimum(r.period.to_numpy().astype(np.int64) - 1, 3)
    cls = r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64)

    def serve(gx, ii):
        if use_engine:
            AS = dict(goal_cls=gx["cls_logit"], goal_game=gx["game_logit"], goal_sc=gx["sc_logit"],
                      goal_sc_game=gx["sc_game"])
            return SIM.goal_prob(AS, gi[ii], team[ii], st[ii], sc[ii], cls[ii], per[ii])
        return 1.0 / (1.0 + np.exp(-served_logit(gx, gi[ii], team[ii], st[ii], sc[ii], cls[ii], per[ii])))
    starter = goal["goalie_id"][gi, team] == r.goalie_id.to_numpy()
    allr = np.arange(len(r))
    served = serve(goal, allr)
    d = np.abs(served - p)
    out = dict(n_rows=int(len(r)), n_starter_rows=int(starter.sum()), n_relief_rows=int((~starter).sum()),
               max_abs_diff_starter=float(d[starter].max()), n_eaf_rows_not_served=int((~m).sum()), engine=use_engine)
    todo = np.flatnonzero(~starter)
    dmax = 0.0
    while todo.size:
        ga = goal["goalie_id"].copy()
        key = pd.DataFrame({"g": gi[todo], "t": team[todo], "k": r.goalie_id.to_numpy()[todo]}).drop_duplicates(["g", "t"])
        ga[key.g.to_numpy(), key.t.to_numpy()] = key.k.to_numpy()
        gx, _ = goal_r4_tables(games, ga, P, scg=goal["sc_game"])
        hit = ga[gi[todo], team[todo]] == r.goalie_id.to_numpy()[todo]
        ii = todo[hit]
        dmax = max(dmax, float(np.abs(serve(gx, ii) - p[ii]).max()))
        todo = todo[~hit]
    out["max_abs_diff_relief_own_goalie"] = dmax
    out["max_abs_diff"] = max(out["max_abs_diff_starter"], dmax)
    b = SA.bucket(r)
    out["by_bucket"] = [dict(bucket=SA.B_NAMES[k], n=int((b == k).sum()), actual=float(r.y[b == k].mean()),
                             offline=float(p[b == k].mean()), served=float(served[b == k].mean())) for k in range(5)]
    return out
