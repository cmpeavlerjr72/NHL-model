"""SB-R5 B1a-as engine tables (docs/models/block/experiments.md SB-R5; frozen params docs/models/block/sb_r5_frozen_params.json).

Served block probability per attempt (goalie-in team-view states 0..4):
  logit p = logit B0'[g, st, ptype]                              (engine.c1s_tables.block_b0g_table, INV-54)
            + game_logit[g, team, st] = (is_home - xbar) W_home + (b2b_own - xbar) W_b2b_own + (b2b_opp - xbar) W_b2b_opp
                                        + (arena_f[g] - xbar) W_arena - xbar_sc . W_sc
                                        + s_for,t zf[g, team, rg(st)] + s_against,t za[g, opp, og(rg)]
            + sc_logit[sc7] = W_sc[sc7] (0 for the tied reference bucket 3)
W / xbar: the fold-2 SB-R4 B1a non-rating terms, centred at the fold-2 training mean; (s_for,t, s_against,t): the selected
cell's committed per-date snapshot (block_scale_v1_f2.parquet), keyed by the game date; zf = the shooting team's Ra
rating of the row's rating group / SD, za = the defending team's Ra rating of the opposing rating group / SD.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.block import data as D
from nhl_sim.block import scale as SC
from nhl_sim.data.load import PROCESSED
from nhl_sim.shot_attribute.tables import OPP_RATING_GROUP

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / "docs/models/block/sb_r5_frozen_params.json"
LABEL = "block: B1a-as (SB-R5; B0' INV-54 + frozen SB-R4 B1a terms + as-of Ra scale H90 P2000, AS-1 floor f 0.5)"
ST_RGRP = np.array([0, 1, 2, 0, 0], np.int64)
SC_COLS = (0, 1, 2, 4, 5, 6)


def b1aas_tables(games: np.ndarray, pbg5: np.ndarray | None = None) -> tuple[dict, dict]:
    """games: sorted fold-2 game ids (engine order). pbg5: the engine's B0' table (G, 5, 2); built if None.
    -> (dict(base_logit (G, 5, 2), game_logit (G, 2, 5), sc_logit (7,)), info)."""
    games = np.asarray(games, np.int64)
    fz = json.loads(FROZEN.read_text())
    W, xbar = np.asarray(fz["W"]), np.asarray(fz["xbar"])
    if pbg5 is None:
        from nhl_sim.engine.c1s_tables import block_b0g_table
        pbg5, _ = block_b0g_table(games)
    base = D.logit(np.asarray(pbg5, np.float64))
    snap = pd.read_parquet(ROOT / fz["snapshot"])
    snap = snap[snap.cell == fz["cell"]]
    gt = pd.read_parquet(D.OUT / "games_v1.parquet").set_index("game_id").loc[games]
    sf, sa = SC.attach_scale(gt.date.to_numpy(), snap)
    team = np.stack([gt.home_id.to_numpy(), gt.away_id.to_numpy()], 1).astype(np.int64)
    rt = pd.read_parquet(D.OUT / "ratings_r4_Ra.parquet").set_index(["game_id", "team_id"])
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    b2b = tg.set_index(["game_id", "team_id"]).b2b
    af = pd.read_parquet(D.OUT / "arena_v1.parquet").set_index("game_id").arena_f.reindex(games).to_numpy(float)
    k = D.wkey(0.7, 1000)

    def at(series, j):
        return series.reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float)
    rf = np.stack([np.stack([at(rt[f"rf_{x}_{k}"], j) for x in D.RG], 1) for j in (0, 1)], 1)    # (G, 2, 3)
    ra = np.stack([np.stack([at(rt[f"ra_{x}_{k}"], j) for x in D.RG], 1) for j in (0, 1)], 1)
    B = np.stack([at(b2b, j) for j in (0, 1)], 1)
    for nm, v in (("ratings", rf), ("ratings", ra), ("b2b", B), ("arena", af), ("scale", sf)):
        if np.isnan(v).any():
            raise ValueError(f"missing {nm}")
    sd_f, sd_a = fz["sd"]
    xs, Ws = xbar[:6], W[:6]
    gl = np.zeros((len(games), 2, 5))
    for j in (0, 1):
        o = 1 - j
        lin = ((1 - j) - xbar[6]) * W[6] + (B[:, j] - xbar[7]) * W[7] + (B[:, o] - xbar[8]) * W[8] \
            + (af - xbar[9]) * W[9] - xs @ Ws
        for st in range(5):
            rg = ST_RGRP[st]
            og = OPP_RATING_GROUP[rg]
            gl[:, j, st] = lin + sf * rf[:, j, rg] / sd_f + sa * ra[:, o, og] / sd_a
    sc_logit = np.zeros(7)
    sc_logit[list(SC_COLS)] = Ws
    return dict(base_logit=base, game_logit=gl, sc_logit=sc_logit), dict(label=LABEL, cell=fz["cell"], n_games=len(games))


def served(T: dict, gi, team, st, sc, t) -> np.ndarray:
    """Reference lookup (the engine's formula): per attempt game index, shooting team (0 home), team-view state 0..4,
    score bucket sc7, game second t."""
    z = T["base_logit"][gi, st, (np.asarray(t) >= 3600).astype(np.int64)] + T["game_logit"][gi, team, st] + T["sc_logit"][sc]
    return 1.0 / (1.0 + np.exp(-z))


def engine_parity(games: np.ndarray, pbg5: np.ndarray, T: dict, res: Path = ROOT / "results/block_sb_r5") -> dict:
    """The ENGINE's served block probability (sim.block_prob with the SB-R5 flag on, from the B0' table pbg5 and the
    b1aas tables T) vs the offline fold-2 B1a-as prediction on every goalie-in row (team-view states 0..4)."""
    from nhl_sim.engine import sim as SIM
    lab = json.loads((res / "labels_sealed.json").read_text())["B1aas"]
    rows = pd.read_parquet(res / "fold2_rows.parquet", columns=["game_id", "team", "st", "sc", "t", "ptype"])
    pred = np.load(res / f"fold2_pred_{lab}.npy").astype(np.float64)
    m = (rows.st <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = np.searchsorted(games, r.game_id.to_numpy())
    if not (np.asarray(games)[np.minimum(gi, len(games) - 1)] == r.game_id.to_numpy()).all():
        raise ValueError("offline rows outside the engine game list")
    pbg = np.asarray(pbg5, np.float64)
    AS = dict(p_block_game=pbg, b1aas_base=np.log(pbg) - np.log1p(-pbg), b1aas_game=T["game_logit"], b1aas_sc=T["sc_logit"])
    served = np.zeros(len(r))
    st, sc, tm, pt = (r[c].to_numpy().astype(np.int64) for c in ("st", "sc", "team", "ptype"))
    for team in (0, 1):
        for t_ in (0, 1):
            k = (tm == team) & (pt == t_)
            served[k] = SIM.block_prob(AS, gi[k], st[k], 3600 * t_, team, sc[k])
    d = np.abs(served - p)
    names = ("5v5", "PP", "PK", "4v4", "3v3")
    by = [dict(state=names[s_], n=int((st == s_).sum()), served=float(served[st == s_].mean()),
               max_abs_diff=float(d[st == s_].max())) for s_ in range(5)]
    return dict(n_rows=int(len(r)), max_abs_diff=float(d.max()), by_state=by)
