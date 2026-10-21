"""INV-60 / INV-57 / INV-54 engine tables (Lane E2, 2026-10-21): builders for the four default-off engine flags and the
served-vs-offline parity helpers. Fold 2 (train 2021-22..2023-24, test 2024-25); nothing here reads 2025-26 (every
loader goes through nhl_sim.data.load / the per-season processed tables, which carry the seal).

  stage-4 L0s, level M1 K500 (INV-57, D35)   STAND-IN. state_pdf (7, 2, 78) = the fold-2 L0s table (SL-R6 D38 run,
      results/shot_attribute_r6_d38/models/L0s.json, identical to the SL-R4 table); game_mult (G, 3, 78) =
      s_M1K500[g, level group, cell] / s_train[level group, cell] (mix_level_v2.parquet, SL-R6 D35 level), per class.
  block B0 with own 4v4 / 3v3 groups (INV-54, D34)   STAND-IN. (G, 5, 2) by team-view state x period type.
      5v5 / PP / PK: the SB-R1 B0 fit and its M1 K500 level, unchanged (ES level group still pools 5v5 + 4v4 + 3v3 + EN,
      as in the B0 fit). 4v4 and 3v3: each its own M1 K500 as-of league block share, computed by the SAME code
      (nhl_sim.block.data.asof_levels) on that state's rows, as a logit offset logit(s_asof) - logit(s_train) with
      coefficient 1, plus one intercept fitted under it on the fold-2 training rows of that state (the B0 fitting code,
      block.models.fit_logit_offset). Construction choice (labelled): one intercept per new group, pooled over period
      type, because 3v3 has 3 regulation training rows (0 blocks: no MLE) and the two new groups keep one form.
  miss S0t (D37)   STAND-IN. (G, 3, 2, 78) = sigmoid(base[class, group] + logit(s_M2H30[g, tier x group]) -
      logit(s_train[tier x group]) + coef[group x ptype]) (results/miss_sm_r2/models/S0t.json; level_tier_v2 M2_H30).
  goal C1s (D40)   CONFIRMED-INCUMBENT (provisional). cls_logit (78, 5) = logit cell table (cell_table_f2, sg 0..4);
      game_logit (G, 2, 5) = C1s sg intercept + level M1 K500 delta[g, lg] + home / b2b own / b2b opp / arena_f coefs +
      s_t c_t t_r[g, team] (team finishing, fixed scale) + s(date_g) z[g, goalie] (as-of goalie scale H90 P2000,
      z = g_r / SD_REF), goalie = the box-score STARTER of the defending team (ORACLE GOALIE, D8);
      sc_logit (7,) = the C1s score dummies (tied = 0). EAF (sg 5) is unreachable until stage 8 and not served.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.engine import sim as SIM

F2_TRAIN = [20212022, 20222023, 20232024]
TEST = 20242025
LEVEL = "M1_K500"

L0S_LABEL = ("STAND-IN (D32): stage-4 L0s (SL-R4 table) levelled by the M1 K500 as-of mix level (D35, INV-57); "
             "EN rows on the baseline; flat, not adoptable")
BLOCK_LABEL = ("STAND-IN (D32): block B0 = SB-R1 B0 (strength group x period type) + M1 K500 as-of league block-share "
               "level; 4v4 / 3v3 own level groups and intercepts (INV-54); flat, not adoptable")
MISS_LABEL = ("STAND-IN (D37): miss S0t = tier level M2 H30 x cell x type x group (SM-R2); flat in team, not adoptable")
GOAL_LABEL = "goal: C1s (provisional, D40)"
ORACLE_LABEL = ("ORACLE GOALIE (D8): the box-score starting goalie of each team faces every shot on goal of the game; "
                "no in-game goalie change (stage 8)")
STAND_IN = {"attr": L0S_LABEL, "block": BLOCK_LABEL, "miss": MISS_LABEL}

L_RES = Path("results/shot_attribute_r6_d38")
B_RES = Path("results/block_sb_r1")
M_RES = Path("results/miss_sm_r2")
G_RES = Path("results/goal_g_r3")
G_R1 = Path("results/goal_g_r1")


def _gpos(games, ids):
    games = np.asarray(games)
    p = np.searchsorted(games, ids)
    if not (games[np.minimum(p, len(games) - 1)] == ids).all():
        raise ValueError("offline rows outside the engine game list")
    return p


# =========================================================================================== stage-4 L0s, M1 K500
def l0s_m1k500_tables(games: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """-> (state_pdf (7, 2, 78) unlevelled L0s, game_mult (G, 3, 78), info)."""
    from nhl_sim.shot_attribute import mix_level as ML
    from nhl_sim.shot_attribute import models as M
    from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE
    m = json.loads((L_RES / "models" / "L0s.json").read_text())
    if m.get("arm") != "L0s":
        raise ValueError("not an L0s model file")
    state_pdf = np.asarray(m["p"], np.float64).reshape(7, 2, N_CELL * N_TYPE)
    tr = M.load_rows(F2_TRAIN)
    u = tr[~tr.blocked]
    s_train = ML.share_table(u)                                         # (3, 13)
    L = pd.read_parquet(M.SA / "mix_level_v2.parquet")
    L = L[L.construction == LEVEL].set_index("game_id")
    cols = [f"s_{g}_{c}" for g in range(3) for c in range(N_CELL)]
    S = L[cols].reindex(np.asarray(games)).to_numpy()
    if np.isnan(S).any():
        raise ValueError("games without an M1 K500 mix level")
    S = S.reshape(len(games), 3, N_CELL)
    gm = np.repeat(S / s_train[None], N_TYPE, axis=2)
    return state_pdf, gm, dict(level=LEVEL, s_train=s_train.tolist(), n_train_unblocked=int(len(u)))


def l0s_parity(games, state_pdf, gm) -> dict:
    """Engine-served class probabilities (increments of sim.class_cdf) vs the offline fold-2 L0s levelled by M1 K500
    (SL-R6 D38 prediction file), every unblocked fold-2 row incl. EN (served the baseline with the ES level group)."""
    lab = json.loads((L_RES / "labels_sealed.json").read_text())["L0s"]
    rows = pd.read_parquet(L_RES / "fold2_rows.parquet", columns=["game_id", "st", "ptype"])
    pred = np.load(L_RES / f"fold2_pred_{lab}.npy").astype(np.float64)
    gi = _gpos(games, rows.game_id.to_numpy())
    st = rows.st.to_numpy().astype(np.int64)
    rg = np.array([0, 1, 2, 0, 0, 0, 0])[st]
    AS = dict(state_pdf=state_pdf, game_mult=gm)
    served = np.zeros_like(pred)
    for pt in (0, 1):
        k = rows.ptype.to_numpy() == pt
        reach = k & (st <= 4)
        served[reach] = np.diff(SIM.class_cdf(AS, None, gi[reach], None, st[reach], None, None, 3600 * pt), axis=1,
                                prepend=0.0)
        en = k & (st > 4)                              # EN states: same formula, ES level group (unreachable in the sim)
        if en.any():
            row = np.cumsum(state_pdf[st[en], pt] * gm[gi[en], rg[en]], 1)
            served[en] = np.diff(row / row[:, -1:], axis=1, prepend=0.0)
    d = np.abs(served - pred).max(1)
    out = dict(n_rows=int(len(rows)), max_abs_diff=float(d.max()),
               max_abs_diff_reachable=float(d[st <= 4].max()), n_en_rows=int((st > 4).sum()))
    return out


# ================================================================================================ block B0 (INV-54)
def _state_level(a, games_tab, st):
    """M1 K500 as-of league block share on the rows of one team-view state, by nhl_sim.block.data.asof_levels (the code
    of the ES / PP / PK groups), the state's rows placed in level group 0. -> Series game_id -> share."""
    from nhl_sim.block import data as D
    x = a[a.st == st].assign(grp=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)        # groups 1 / 2 are empty here (0 / 0), unused
        meta, S = D.asof_levels(x, games_tab, {LEVEL: ("M1", 500)})
    return pd.Series(S[LEVEL][:, 0], index=meta.game_id.to_numpy())


def block_b0g_table(games: np.ndarray) -> tuple[np.ndarray, dict]:
    """-> (p_block_game (G, 5, 2) by team-view state x period type, info). See the module doc."""
    from nhl_sim.block import data as D
    from nhl_sim.block.data import logit, sigmoid
    from nhl_sim.block.models import fit_logit_offset
    from nhl_sim.engine import standins as SI
    pbg3, binfo = SI.block_b0_table(games)                      # SB-R1 B0 + M1 K500, (G, 3, 2): unchanged for st 0..2
    gtab = pd.read_parquet(D.OUT / "games_v1.parquet")
    a = D.load_attempts(D.SEASONS)
    a = a[a.game_id.isin(gtab.game_id)]
    meta, S = D.asof_levels(a, gtab, {LEVEL: ("M1", 500)})     # code-identity check: recompute ES / PP / PK levels
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == LEVEL].set_index("game_id")[["s_0", "s_1", "s_2"]].reindex(meta.game_id.to_numpy())
    es_dev = float(np.abs(S[LEVEL] - L.to_numpy()).max())
    if es_dev > 1e-12:
        raise ValueError(f"recomputed ES / PP / PK level differs from level_v1 ({es_dev})")
    tr = a[a.season.isin(F2_TRAIN)]
    out = np.zeros((len(games), 5, 2))
    out[:, :3] = pbg3
    info = dict(b0=binfo, es_level_recompute_max_dev=es_dev, groups={})
    for st, nm in ((3, "4v4"), (4, "3v3")):
        lev = _state_level(a, gtab, st)
        x = tr[tr.st == st]
        s_tr = float(x.blocked.mean())
        off = logit(lev.reindex(x.game_id.to_numpy()).to_numpy()) - logit(s_tr)
        w, nit = fit_logit_offset(np.ones((len(x), 1)), x.blocked.to_numpy(), off, n_free=1)
        Lg = lev.reindex(np.asarray(games)).to_numpy()
        if np.isnan(Lg).any():
            raise ValueError(f"games without a {nm} level")
        p = sigmoid(w[0] + logit(Lg) - logit(s_tr))
        out[:, st, 0] = p
        out[:, st, 1] = p
        info["groups"][nm] = dict(coef=float(w[0]), s_train=s_tr, n_train=int(len(x)), n_train_blocked=int(x.blocked.sum()),
                                  n_iter=nit, n_train_by_ptype=x.groupby("ptype").size().to_dict())
    return out, info


def b0g_offline(games, info, rows) -> np.ndarray:
    """Row-wise offline B0g prediction for 4v4 / 3v3 rows (sigmoid(coef + logit(level of the row's game) -
    logit(s_train))), evaluated without the engine table."""
    from nhl_sim.block import data as D
    from nhl_sim.block.data import logit, sigmoid
    gtab = pd.read_parquet(D.OUT / "games_v1.parquet")
    a = D.load_attempts(D.SEASONS)
    a = a[a.game_id.isin(gtab.game_id)]
    p = np.full(len(rows), np.nan)
    for st, nm in ((3, "4v4"), (4, "3v3")):
        k = (rows.st == st).to_numpy()
        lev = _state_level(a, gtab, st).reindex(rows.game_id.to_numpy()[k]).to_numpy()
        g = info["groups"][nm]
        p[k] = sigmoid(g["coef"] + logit(lev) - logit(g["s_train"]))
    return p


def b0g_parity(games, pbg5, info) -> dict:
    """Served (sim.block_prob on the (G, 5, 2) table) vs offline: SB-R1 B0 fold-2 prediction on 5v5 / PP / PK rows
    (unchanged), the row-wise B0g prediction on 4v4 / 3v3 rows. Also the served mean vs actual by state, before
    (SB-R1 B0 as served by the (G, 3, 2) table) and after."""
    lab = json.loads((B_RES / "labels_sealed.json").read_text())["B0"]
    rows = pd.read_parquet(B_RES / "fold2_rows.parquet", columns=["game_id", "grp", "st", "ptype", "y"])
    pred = np.load(B_RES / f"fold2_pred_{lab}.npy").astype(np.float64)
    m = (rows.st <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = _gpos(games, r.game_id.to_numpy())
    st = r.st.to_numpy().astype(np.int64)
    pt = r.ptype.to_numpy()
    served, before = np.zeros(len(r)), np.zeros(len(r))
    for t_ in (0, 1):
        k = pt == t_
        served[k] = SIM.block_prob(dict(p_block_game=pbg5), gi[k], st[k], 3600 * t_)
        before[k] = SIM.block_prob(dict(p_block_game=pbg5[:, :3]), gi[k], st[k], 3600 * t_)
    off = p.copy()
    k34 = st >= 3
    off[k34] = b0g_offline(games, info, r[k34].reset_index(drop=True))
    d = np.abs(served - off)
    old = np.abs(before - p)
    by = []
    for s_, nm in enumerate(("5v5", "PP", "PK", "4v4", "3v3")):
        k = st == s_
        by.append(dict(state=nm, n=int(k.sum()), actual=float(r.y[k].mean()), served_before=float(before[k].mean()),
                       served_after=float(served[k].mean()), max_abs_diff=float(d[k].max())))
    return dict(n_rows=int(len(r)), max_abs_diff=float(d.max()), max_abs_diff_st012_vs_sb_r1=float(d[~k34].max()),
                before_vs_sb_r1_max=float(old.max()), by_state=by)


# ======================================================================================================= miss S0t
def miss_s0t_table(games: np.ndarray) -> tuple[np.ndarray, dict]:
    """-> (p_miss_game (G, 3, 2, 78) = [game, rating group ES / PP / PK, period type, class], info)."""
    from nhl_sim.miss import data as M
    from nhl_sim.miss import tier as T
    from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE, TIER_OF_CELL
    sel = json.loads((M_RES / "step1.json").read_text())["selected"]
    m = json.loads((M_RES / "models" / "S0t.json").read_text())
    base, coef = np.asarray(m["base"], np.float64), np.asarray(m["coef"], np.float64)
    if base.shape != (N_CLASS, 5) or coef.shape != (10,):
        raise ValueError("S0t: base (78, 5), coef (grp x ptype = 10)")
    tr = M.load_rows(F2_TRAIN)
    s_train = T.share_table(tr)                                         # (9,) col = 3 tier + level group
    L = pd.read_parquet(M.OUT / "level_tier_v2.parquet")
    L = L[L.construction == sel].set_index("game_id")[[f"s_{c}" for c in range(T.NC)]]
    S = L.reindex(np.asarray(games)).to_numpy()
    if np.isnan(S).any():
        raise ValueError(f"games without a {sel} miss level")
    tier = np.repeat(TIER_OF_CELL.astype(np.int64), N_TYPE)            # (78,)
    out = np.zeros((len(games), 3, 2, N_CLASS))
    for g in range(3):
        col = 3 * tier + g
        lev = M.logit(S[:, col]) - M.logit(s_train[col])[None]          # (G, 78)
        for pt in (0, 1):
            out[:, g, pt] = M.sigmoid(base[:, g][None] + lev + coef[g * 2 + pt])
    return out, dict(level=sel, s_train=s_train.tolist(), n_train=int(len(tr)))


def miss_parity(games, pmg) -> dict:
    """Engine-served miss probability (sim.miss_prob) vs the offline fold-2 S0t prediction on every goalie-in unblocked
    row (EN rows are not served before stage 8; counted)."""
    lab = json.loads((M_RES / "labels_sealed.json").read_text())["S0t"]
    rows = pd.read_parquet(M_RES / "fold2_rows.parquet", columns=["game_id", "st", "grp", "ptype", "cell", "type6", "y"])
    pred = np.load(M_RES / f"fold2_pred_{lab}.npy").astype(np.float64)
    m = (rows.st <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = _gpos(games, r.game_id.to_numpy())
    st = r.st.to_numpy().astype(np.int64)
    cls = (r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64))
    served = np.zeros(len(r))
    for t_ in (0, 1):
        k = r.ptype.to_numpy() == t_
        served[k] = SIM.miss_prob(dict(p_miss=pmg), gi[k], st[k], 3600 * t_, cls[k])
    d = np.abs(served - p)
    by = [dict(state=nm, n=int((st == s_).sum()), actual=float(r.y[st == s_].mean()), served=float(served[st == s_].mean()))
          for s_, nm in enumerate(("5v5", "PP", "PK", "4v4", "3v3"))]
    return dict(n_rows=int(len(r)), max_abs_diff=float(d.max()), n_en_rows_not_served=int((~m).sum()), by_state=by)


# ======================================================================================================== goal C1s
def starters(games: np.ndarray, season: int = TEST) -> np.ndarray:
    """(G, 2) box-score starting goalie of [home, away] (ORACLE GOALIE, D8)."""
    from nhl_sim.data.load import load_games, load_goalie_box
    gb = load_goalie_box(seasons=[season], columns=["game_id", "team_id", "player_id", "starter"])
    gb = gb[gb.starter.astype(bool)]
    if gb.duplicated(["game_id", "team_id"]).any():
        raise ValueError("more than one starter for a team-game")
    gm = load_games([season], columns=["game_id", "home_id", "away_id"]).set_index("game_id").loc[np.asarray(games)]
    s = gb.set_index(["game_id", "team_id"]).player_id
    out = np.zeros((len(games), 2), np.int64)
    for j, c in enumerate(("home_id", "away_id")):
        v = s.reindex(pd.MultiIndex.from_arrays([np.asarray(games), gm[c].to_numpy()])).to_numpy()
        if pd.isna(v).any():
            raise ValueError(f"{int(pd.isna(v).sum())} team-games without a starter")
        out[:, j] = v.astype(np.int64)
    return out


def _goal_parts(games: np.ndarray):
    """Model pieces of C1s fold 2 (frozen files of G-R1..G-R3) and per-game inputs, in engine game order."""
    from nhl_sim.goal import data as GD
    from nhl_sim.data.load import PROCESSED
    s1 = json.loads((G_R1 / "select.json").read_text())
    s3 = json.loads((G_RES / "select.json").read_text())
    mdl = json.loads((G_RES / "fold2" / "models" / "C1s.json").read_text())
    if mdl.get("arm") != "C1s" or mdl.get("cell") != s3["selected"]:
        raise ValueError("C1s model file / selected cell mismatch")
    coef = np.asarray(mdl["coef"], np.float64)
    if coef.shape != (16,):
        raise ValueError("C1s coef: sg 6 | sc 6 | is_home, b2b_own, b2b_opp, arena_f")
    T = np.load(GD.OUT / "cell_table_f2.npy")
    lv = pd.read_parquet(GD.OUT / "level_v1_f2.parquet")
    lv = lv[lv.construction == LEVEL].set_index("game_id")[[f"d_{g}" for g in range(GD.N_LG)]]
    delta = lv.reindex(np.asarray(games)).to_numpy()
    gtab = pd.read_parquet(PROCESSED / "block" / "games_v1.parquet").set_index("game_id").loc[np.asarray(games)]
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    b2b = tg.set_index(["game_id", "team_id"]).b2b
    team = np.stack([gtab.home_id.to_numpy(), gtab.away_id.to_numpy()], 1).astype(np.int64)
    B = np.stack([b2b.reindex(pd.MultiIndex.from_arrays([np.asarray(games), team[:, j]])).to_numpy(float) for j in (0, 1)], 1)
    arena = pd.read_parquet(GD.SA / "arena_dist_v1.parquet", columns=["game_id", "arena_f"]).set_index("game_id")
    af = arena.arena_f.reindex(np.asarray(games)).to_numpy(float)
    RT = pd.read_parquet(GD.OUT / "ratings_team_v1_f2.parquet")
    tcol = GD.rkey(*s1["team_cell"])
    rt = RT.set_index(["game_id", "team_id"])[tcol]
    TR = np.stack([rt.reindex(pd.MultiIndex.from_arrays([np.asarray(games), team[:, j]])).to_numpy(float) for j in (0, 1)], 1)
    RG = pd.read_parquet(GD.OUT / "ratings_goalie_v1_f2.parquet")
    gcol = GD.rkey(*s1["goalie_cell"])
    sc = pd.read_parquet(GD.OUT / "goalie_scale_v1_f2.parquet")
    sc = sc[sc.cell == s3["selected"]]
    smap = pd.Series(sc.s.to_numpy(), index=pd.to_datetime(sc.date).to_numpy("datetime64[D]"))
    s_date = smap.reindex(pd.to_datetime(gtab.date).to_numpy("datetime64[D]")).to_numpy()
    for nm, v in (("level", delta), ("b2b", B), ("arena_f", af), ("team rating", TR), ("goalie scale", s_date)):
        if np.isnan(v).any():
            raise ValueError(f"games without a {nm}")
    return dict(coef=coef, T=T, delta=delta, team=team, B=B, af=af, TR=TR, s_date=s_date, spec=s1["spec"],
                sd_ref=float(mdl["sd_ref"]), RG=RG.set_index(["game_id", "goalie_id"])[gcol], cell=s3["selected"],
                gcol=gcol, tcol=tcol)


def _goalie_z(P, games, goalie):
    """(G, 2) z = g_r / SD_REF of goalie[g, j] (as-of rating of that goalie in game g)."""
    g = np.asarray(games)
    z = np.stack([P["RG"].reindex(pd.MultiIndex.from_arrays([g, goalie[:, j]])).to_numpy(float) for j in (0, 1)], 1)
    if np.isnan(z).any():
        raise ValueError(f"{int(np.isnan(z).sum())} (game, goalie) without an as-of goalie rating")
    return z / P["sd_ref"]


def goal_c1s_tables(games: np.ndarray, goalie_against: np.ndarray | None = None, P: dict | None = None) -> tuple[dict, dict]:
    """-> (attr["goal"] dict, info). goalie_against[g, team] = the goalie facing `team`'s shots (default: the other
    team's box-score starter, ORACLE GOALIE)."""
    from nhl_sim.goal.data import logit
    P = _goal_parts(games) if P is None else P
    if goalie_against is None:
        st_ = starters(games)
        goalie_against = st_[:, ::-1].copy()
    c = P["coef"]
    cls_logit = logit(P["T"][:, :5])                                    # (78, 5), sg 0..4
    z = _goalie_z(P, games, goalie_against)
    lg = np.array([0, 1, 2, 3, 4])                                      # sg 0..4 -> level group (EAF unserved)
    G = len(games)
    gl = np.zeros((G, 2, 5))
    for j in (0, 1):
        common = (c[12] * (1 - j) + c[13] * P["B"][:, j] + c[14] * P["B"][:, 1 - j] + c[15] * P["af"]
                  + P["spec"]["s_t"] * P["spec"]["c_t"] * P["TR"][:, j] + P["s_date"] * z[:, j])
        for sg in range(5):
            gl[:, j, sg] = c[sg] + P["delta"][:, lg[sg]] + common
    sc_logit = np.array([c[6], c[7], c[8], 0.0, c[9], c[10], c[11]])
    goal = dict(cls_logit=cls_logit, game_logit=gl, sc_logit=sc_logit, goalie_id=np.asarray(goalie_against, np.int64),
                label=GOAL_LABEL, oracle_goalie=ORACLE_LABEL)
    info = dict(label=GOAL_LABEL, scale_cell=P["cell"], sd_ref=P["sd_ref"], team_cell=P["tcol"], goalie_cell=P["gcol"],
                spec=P["spec"], coef=c.tolist(), level=LEVEL)
    return goal, info


def goal_parity(games, goal, P: dict | None = None) -> dict:
    """Engine-served C1s probability (sim.goal_prob) vs the offline fold-2 C1s prediction (G-R3 file).
    Starter rows (the goalie in net = the defending team's box-score starter): the engine's own table. Relief rows: the
    same builder with the relief goalie in the defending slot (the engine never serves these: oracle starter, no in-game
    change); both must agree with offline within 1e-6. Also reports what the starter table gives on relief rows."""
    P = _goal_parts(games) if P is None else P
    lab = json.loads((G_RES / "fold2" / "labels_sealed.json").read_text())["C1s"]
    rows = pd.read_parquet(G_RES / "fold2" / "fold2_rows.parquet",
                           columns=["game_id", "team_id", "goalie_id", "is_home", "sg", "sc", "cell", "type6", "y"])
    pred = np.load(G_RES / "fold2" / f"fold2_pred_{lab}.npy").astype(np.float64)
    m = (rows.sg <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = _gpos(games, r.game_id.to_numpy())
    team = np.where(r.is_home.to_numpy() == 1, 0, 1)
    if not (P["team"][gi, team] == r.team_id.to_numpy()).all():
        raise ValueError("team slot mismatch")
    st = r.sg.to_numpy().astype(np.int64)
    sc = r.sc.to_numpy().astype(np.int64)
    cls = r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64)
    AS = dict(goal_cls=goal["cls_logit"], goal_game=goal["game_logit"], goal_sc=goal["sc_logit"])
    served = SIM.goal_prob(AS, gi, team, st, sc, cls)
    starter = goal["goalie_id"][gi, team] == r.goalie_id.to_numpy()
    d = np.abs(served - p)
    out = dict(n_rows=int(len(r)), n_starter_rows=int(starter.sum()), n_relief_rows=int((~starter).sum()),
               max_abs_diff_starter=float(d[starter].max()),
               relief_rows_served_starter_mean_abs_diff=float(d[~starter].mean()) if (~starter).any() else None,
               n_eaf_rows_not_served=int((~m).sum()))
    # relief rows through the same builder with the relief goalie in the slot (possibly several passes)
    rel = np.flatnonzero(~starter)
    dmax = 0.0
    todo = rel
    while todo.size:
        ga = goal["goalie_id"].copy()
        key = pd.DataFrame({"g": gi[todo], "t": team[todo], "k": r.goalie_id.to_numpy()[todo], "i": todo})
        first = key.drop_duplicates(["g", "t"])
        ga[first.g.to_numpy(), first.t.to_numpy()] = first.k.to_numpy()
        gx, _ = goal_c1s_tables(games, ga, P)
        AX = dict(goal_cls=gx["cls_logit"], goal_game=gx["game_logit"], goal_sc=gx["sc_logit"])
        hit = ga[gi[todo], team[todo]] == r.goalie_id.to_numpy()[todo]
        ii = todo[hit]
        sv = SIM.goal_prob(AX, gi[ii], team[ii], st[ii], sc[ii], cls[ii])
        dmax = max(dmax, float(np.abs(sv - p[ii]).max()))
        todo = todo[~hit]
    out["max_abs_diff_relief_own_goalie"] = dmax
    out["max_abs_diff"] = max(out["max_abs_diff_starter"], dmax)
    by = []
    for s_, nm in enumerate(("5v5", "PP", "PK", "4v4", "3v3")):
        k = st == s_
        by.append(dict(state=nm, n=int(k.sum()), actual_goal_rate=float(r.y[k].mean()), offline=float(p[k].mean()),
                       served=float(served[k].mean())))
    out["by_state"] = by
    return out
