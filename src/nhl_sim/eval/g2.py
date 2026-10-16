"""G2 (shot attempts) for the stage-3 closed loop (SA-R1 spec, docs/models/shot_attempt/experiments.md).

One code path builds per-(game, team) team-view arrays for the real season (attempt rows v1) and for sim output
(results/<tag>/attempts.parquet), then the same functions compute every quantity:
  attempts per 60 by team-view strength state, attempts per team-game (mean, SD, P(k) bands), correlation of home
  and away attempts per game, attempts per 60 by pre-event score bucket, per-team for / against per team-game.
Tolerance: `g2_rate_rel` (relative) on the rate-type quantities (per 60 by state and by score bucket, mean per
team-game); SD ratio, P(k) bands and the correlation are reported NO-TOLERANCE (labelled reading of the spec).
Cells under `min_cell_n` (team-games; team-hours for score buckets) are UNDERPOWERED.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.shot_attempt.tables import SC_NAMES, ST_NAMES

SWAP5 = np.array([0, 2, 1, 3, 4])
BANDS = [(0, 40), (40, 50), (50, 60), (60, 70), (70, 999)]


def real_team_arrays(rows: pd.DataFrame) -> dict:
    """rows: attempt rows (both team views). Returns per (game, team) arrays over 7 states / 7 buckets."""
    rows = rows.sort_values(["game_id", "team"])
    key = rows.game_id.to_numpy() * 2 + rows.team.to_numpy()
    u, inv = np.unique(key, return_inverse=True)
    n = len(u)
    A = np.zeros((n, 7, 7))
    T = np.zeros((n, 7, 7))
    np.add.at(A, (inv, rows.st.to_numpy(), rows.sc.to_numpy()), rows.y.to_numpy())
    np.add.at(T, (inv, rows.st.to_numpy(), rows.sc.to_numpy()), rows.exposure_s.to_numpy())
    gt = rows.groupby(key).game_type.first().reindex(u).to_numpy()
    return dict(game_id=u // 2, team=u % 2, seed=np.zeros(n, int), A=A, T=T, game_type=gt)


def sim_team_arrays(s: pd.DataFrame) -> dict:
    """s: attempts.parquet rows (game_id, seed, game_type, att_h_st*, att_a_st*, att_h_sc*, att_a_sc*, toi_<st>_<sc>).
    The sim records attempts by state and by bucket separately; A[.., st, sc] is not available, so A is returned as
    two marginals (A_st (n, 7) padded with EN = 0, A_sc (n, 7)) and T (n, 7, 7) team view."""
    toi = np.stack([s[f"toi_{a}_{b}"].to_numpy() for a in range(5) for b in range(7)], 1).reshape(-1, 5, 7)
    Th = np.zeros((len(s), 7, 7))
    Th[:, :5] = toi
    Ta = np.zeros((len(s), 7, 7))
    Ta[:, :5] = toi[:, SWAP5][:, :, ::-1]
    def st_(p):
        x = np.zeros((len(s), 7))
        x[:, :5] = np.stack([s[f"att_{p}_st{k}"].to_numpy() for k in range(5)], 1)
        return x
    sc_ = lambda p: np.stack([s[f"att_{p}_sc{k}"].to_numpy() for k in range(7)], 1)  # noqa: E731
    return dict(game_id=np.concatenate([s.game_id.to_numpy()] * 2), team=np.repeat([0, 1], len(s)),
                seed=np.concatenate([s.seed.to_numpy()] * 2), A_st=np.vstack([st_("h"), st_("a")]),
                A_sc=np.vstack([sc_("h"), sc_("a")]), T=np.concatenate([Th, Ta]),
                game_type=np.concatenate([s.game_type.to_numpy()] * 2))


def marginals(d: dict):
    if "A" in d:
        return d["A"].sum(2), d["A"].sum(1)
    return d["A_st"], d["A_sc"]


def select(d: dict, m: np.ndarray) -> dict:
    return {k: v[m] for k, v in d.items()}


def quantities(d: dict) -> dict:
    A_st, A_sc = marginals(d)
    T_st, T_sc = d["T"].sum(2), d["T"].sum(1)
    tot = A_st.sum(1)
    q = {}
    for s in range(7):
        q[("per60_state", ST_NAMES[s])] = A_st[:, s].sum() / max(T_st[:, s].sum(), 1e-9) * 3600
    for c in range(7):
        q[("per60_score", SC_NAMES[c])] = A_sc[:, c].sum() / max(T_sc[:, c].sum(), 1e-9) * 3600
    q[("team_game", "mean")] = tot.mean()
    q[("team_game", "sd")] = tot.std()
    for lo, hi in BANDS:
        q[("team_game_P", f"[{lo},{hi})" if hi < 999 else f">={lo}")] = float(((tot >= lo) & (tot < hi)).mean())
    key = d["game_id"] * 100000 + d["seed"]
    h, a = d["team"] == 0, d["team"] == 1
    oh, oa = np.argsort(key[h]), np.argsort(key[a])
    q[("game", "corr_home_away")] = float(np.corrcoef(tot[h][oh], tot[a][oa])[0, 1])
    return q


def expo_hours_by_score(d):
    return d["T"].sum(1).sum(0) / 3600


def evaluate(sim: dict, real: dict, tol_rel: float, min_n: int) -> pd.DataFrame:
    S, R = quantities(sim), quantities(real)
    n_tg = len(real["game_id"])
    eh = expo_hours_by_score(real)
    out = []
    for k in R:
        grp, cell = k
        sv, rv = S.get(k, np.nan), R[k]
        if grp in ("per60_state", "per60_score", "team_game") and not (grp == "team_game" and cell == "sd"):
            if grp == "per60_state" and cell in ("EN-for", "EN-against"):
                st, note = "UNREACHABLE", "no goalie-pull model (stage 8)"
            else:
                n = eh[list(SC_NAMES).index(cell)] if grp == "per60_score" else n_tg
                rel = sv / rv - 1
                st = "UNDERPOWERED" if n < min_n else ("PASS" if abs(rel) <= tol_rel else "FAIL")
                note = f"n={n:.0f} {'team-hours' if grp == 'per60_score' else 'team-games'}"
            out.append(dict(group=grp, cell=cell, sim=sv, real=rv, rel=sv / rv - 1, tol=tol_rel, status=st, note=note))
        else:
            out.append(dict(group=grp, cell=cell, sim=sv, real=rv, rel=(sv / rv - 1) if rv else np.nan, tol="",
                            status="NO-TOLERANCE", note="SD ratio / P(k) / correlation: reported"))
    return pd.DataFrame(out)


def per_team(d: dict, team_ids: np.ndarray) -> pd.DataFrame:
    """team_ids aligned with d rows. For / against per team-game (sim: mean over seeds)."""
    A_st, _ = marginals(d)
    tot = A_st.sum(1)
    df = pd.DataFrame({"gid": d["game_id"], "seed": d["seed"], "team": d["team"], "team_id": team_ids, "att": tot})
    opp = df.assign(team=1 - df.team)[["gid", "seed", "team", "att"]].rename(columns={"att": "against"})
    df = df.merge(opp, on=["gid", "seed", "team"])
    return df.groupby("team_id").agg(for_pg=("att", "mean"), against_pg=("against", "mean"),
                                     n_team_games=("gid", "nunique"))
