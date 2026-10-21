"""EG-R1 part A (INV-66, Lane H8a): empty-net scoring inputs and the engine's tables["pull"] builder.

Inventory of the served tables at the EN team-view states (5 EN-for = own goalie pulled, 6 EN-against = shooting at
the empty net):
  stage 3 A3g-c      NO EN states (G, 2, M, 5, 7)  -> STAND-IN: as-of M1 K500 attempt level per EN state (this module)
  stage 4 L0s / L1x  L0s state_pdf rows 5 / 6 (the baseline, L33); L1x-as serves EN rows as the L0s baseline x the
                     ES-group M1 K500 level (SL-R7 offline does the same)
  block B0           own ENF / ENA groups (one-hot intercepts) on the ES level -> p_block_en (G, 2, 2) (not in the engine's
                     (G, 5, 2) table, which serves 5v5 / PP / PK / 4v4 / 3v3)
  miss S0t           own ENF / ENA groups (base / coef columns 3 / 4) on the ES level group -> p_miss_en (G, 2, 2, 78)
  goal C1s           EN-for = sg 5 EAF (5v5 level group), defending starter; EN-against: none (no goalie)
                     -> STAND-IN: as-of M1 K500 level of goal per SOG on st-6 SOG (this module; 1.0 in the data)
M1 K500 = (n + K s_prev) / (d + K) per game date from the season's earlier dates (K = 500 attempts for the attempt
rate, with d in attempt units d = exposure x s_prev; K = 500 SOG for the goal share), s_prev = the previous season's
final value; 2021-22 prior = its own final value (burn-in, never judged). created_at < puck_drop asserted.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED
from nhl_sim.end_game import pull as PL
from nhl_sim.strength_state.tables import assert_pregame

K = 500.0
SEASONS = [20212022, 20222023, 20232024, 20242025]
SA = PROCESSED / "shot_attempt"
SATTR = PROCESSED / "shot_attribute"
MOD = PROCESSED / "end_game" / "models_v1"
EN_ATT_LABEL = ("STAND-IN (EG-R1 part A): EN attempt rates = as-of M1 K500 league level per EN state (EN-for / "
                "EN-against attempts per team-hour, stage-3 attempt rows st 5 / 6); flat, no team terms")
EN_GOAL_LABEL = ("STAND-IN (EG-R1 part A): goal per SOG into an empty net = as-of M1 K500 league level on st-6 SOG")
PULL_LABEL = "goalie pull: P1 hazard (EG-R1 part A, selected on fold 2 after D45)"


def _games(seasons):
    g = pd.read_parquet(PROCESSED / "block" / "games_v1.parquet")
    g = g[g.season.isin(seasons)]
    return g.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)


def _asof(games, num, den, kind):
    """M1 K500 per game. num / den: per-game counts (attempts, exposure s) or (goals, SOG). -> (value, meta)."""
    seasons = sorted(games.season.unique())
    final = {s: num[(games.season == s).to_numpy()].sum() / den[(games.season == s).to_numpy()].sum() for s in seasons}
    v = np.zeros(len(games))
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    for i, s in enumerate(seasons):
        prev = final[seasons[i - 1]] if i > 0 else final[s]
        ix_s = np.flatnonzero((games.season == s).to_numpy())
        dates = games.date.to_numpy()[ix_s]
        n = d = 0.0
        for dt in np.unique(dates):
            ix = ix_s[dates == dt]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            if kind == "rate":                       # K attempts at the prior rate: (n + K) / (d + K / prev)
                v[ix] = (n + K) / (d + K / prev)
            else:                                    # share: (n + K prev) / (d + K)
                v[ix] = (n + K * prev) / (d + K)
            n += num[ix].sum(); d += den[ix].sum()
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"), "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    m2 = meta[meta.created_at.notna()]
    assert_pregame(m2.rename(columns={}))
    return v, final, meta


def en_levels(seasons=SEASONS) -> tuple[pd.DataFrame, dict]:
    """-> (per game: lam_ef, lam_ea attempts per team-HOUR, p_en_goal; plus counts), info with finals."""
    games = _games(seasons)
    idx = pd.Index(games.game_id)
    out = pd.DataFrame({"game_id": games.game_id, "season": games.season})
    info = {}
    for st, nm in ((5, "ef"), (6, "ea")):
        x, e = np.zeros(len(games)), np.zeros(len(games))
        for s in seasons:
            r = pd.read_parquet(SA / f"attempt_rows_v1_{s}.parquet", columns=["game_id", "st", "exposure_s", "y"])
            r = r[r.st == st].groupby("game_id")[["y", "exposure_s"]].sum()
            p = idx.get_indexer(r.index)
            ok = p >= 0
            x[p[ok]] += r.y.to_numpy()[ok]; e[p[ok]] += r.exposure_s.to_numpy()[ok]
        v, fin, meta = _asof(games, x, e, "rate")
        out[f"lam_{nm}"] = v * 3600.0
        out[f"att_{nm}"], out[f"exp_{nm}_s"] = x, e
        info[nm] = {str(k): float(f * 3600) for k, f in fin.items()}
    g, n = np.zeros(len(games)), np.zeros(len(games))
    for s in seasons:
        a = pd.read_parquet(SATTR / f"attempt_attr_v1_{s}.parquet", columns=["game_id", "st", "event", "is_goal"])
        a = a[(a.st == 6) & a.event.isin(["SHOT", "GOAL"])].groupby("game_id").is_goal.agg(["sum", "size"])
        p = idx.get_indexer(a.index); ok = p >= 0
        g[p[ok]] += a["sum"].to_numpy()[ok]; n[p[ok]] += a["size"].to_numpy()[ok]
    v, fin, meta = _asof(games, g, n, "share")
    out["p_en_goal"], out["en_goals"], out["en_sog"] = v, g, n
    info["en_goal"] = {str(k): float(f) for k, f in fin.items()}
    out = out.merge(meta[["game_id", "created_at", "puck_drop"]], on="game_id")
    return out, info


def parity(L: pd.DataFrame) -> pd.DataFrame:
    """Per-season predicted / actual: attempts (level x exposure) and EN-against goals per SOG."""
    rows = []
    for s, x in L.groupby("season"):
        r = dict(season=int(s))
        for nm in ("ef", "ea"):
            r[f"{nm}_pred_over_actual"] = float((x[f"lam_{nm}"] / 3600 * x[f"exp_{nm}_s"]).sum() / x[f"att_{nm}"].sum())
            r[f"{nm}_n_attempts"] = int(x[f"att_{nm}"].sum())
        r["en_goal_pred_over_actual"] = float((x.p_en_goal * x.en_sog).sum() / x.en_goals.sum())
        r["en_sog"] = int(x.en_sog.sum())
        r["judged"] = s != 20212022
        rows.append(r)
    return pd.DataFrame(rows)


# ===================================================================================== engine tables["pull"]
def goal_eaf(games, goal_info=None):
    """C1s EAF (sg 5) columns in the C1s engine form: cls (78,), game (G, 2); goalie = the defending starter."""
    from nhl_sim.engine import c1s_tables as CT
    from nhl_sim.goal.data import logit
    P = CT._goal_parts(games)
    st_ = CT.starters(games)
    z = CT._goalie_z(P, games, st_[:, ::-1].copy())
    c = P["coef"]
    gl = np.zeros((len(games), 2))
    for j in (0, 1):
        common = (c[12] * (1 - j) + c[13] * P["B"][:, j] + c[14] * P["B"][:, 1 - j] + c[15] * P["af"]
                  + P["spec"]["s_t"] * P["spec"]["c_t"] * P["TR"][:, j] + P["s_date"] * z[:, j])
        gl[:, j] = c[5] + P["delta"][:, 0] + common             # sg 5 EAF, level group 0 (5v5 + EAF)
    return logit(P["T"][:, 5]), gl, P


def pull_tables(games: np.ndarray, season: int = 20242025, arm: str | None = None) -> tuple[dict, dict]:
    """tables["pull"] for the engine, in engine game order. arm: the selected arm (default: select.json)."""
    sel = json.loads((MOD / "select.json").read_text())
    arm = arm or sel["selected"]
    m = json.loads((MOD / f"fold2_{arm}.json").read_text())
    if arm == "P1":
        hz = dict(kind="P1", table=PL.p1_table(m))
    else:
        h0, h1 = PL.p0_tables(m)
        hz = dict(kind="P0", h_first=h0, h_repull=h1)
    L, linfo = en_levels()
    Lg = L.set_index("game_id").reindex(np.asarray(games))
    if Lg.lam_ef.isna().any():
        raise ValueError("games without an EN level")
    cls, gl, _ = goal_eaf(games)
    pbe, binfo = block_en_table(games)
    pme, minfo = miss_en_table(games)
    t = dict(hazard=hz, en_lam=np.stack([Lg.lam_ef.to_numpy(), Lg.lam_ea.to_numpy()], 1), p_block_en=pbe, p_miss_en=pme,
             p_en_goal=Lg.p_en_goal.to_numpy(), eaf_cls=cls, eaf_game=gl,
             label=PULL_LABEL if arm == "P1" else f"goalie pull: {arm}",
             stand_in={"en_attempts": EN_ATT_LABEL, "en_goal": EN_GOAL_LABEL},
             note="no delayed-penalty state (INV-70); stage 1 reads the penalty-derived strength during a pull")
    return t, dict(arm=arm, levels=linfo, n_games=len(games), block_en=binfo, miss_en=minfo)


def block_en_table(games):
    """(G, 2, 2) = B0's ENF / ENA groups x period type with the ES M1 K500 level offset (the SB-R1 B0 form; the engine's
    (G, 5, 2) table carries 5v5 / PP / PK / 4v4 / 3v3 only)."""
    from nhl_sim.block import data as D
    from nhl_sim.block.data import logit, sigmoid
    from nhl_sim.engine import standins as SI
    _, info = SI.block_b0_table(np.asarray(games))
    coef, s_train = np.asarray(info["coef"]), np.asarray(info["s_train"])
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == SI.LEVEL_NAME].set_index("game_id")["s_0"].reindex(np.asarray(games)).to_numpy()
    off = logit(L) - logit(s_train[0])
    out = np.zeros((len(games), 2, 2))
    for j, g in enumerate((3, 4)):
        for pt in (0, 1):
            out[:, j, pt] = sigmoid(coef[g * 2 + pt] + off)
    return out, dict(groups="ENF, ENA (B0 own intercepts, ES level)", coef=coef[6:].tolist())


def miss_en_table(games):
    """(G, 2, 2, 78) = S0t's ENF / ENA groups x period type x class, level group ES (as CT.miss_s0t_table)."""
    from nhl_sim.engine import c1s_tables as CT
    from nhl_sim.miss import data as M
    from nhl_sim.miss import tier as T
    from nhl_sim.shot_attribute.tables import N_CLASS, N_TYPE, TIER_OF_CELL
    sel = json.loads((CT.M_RES / "step1.json").read_text())["selected"]
    m = json.loads((CT.M_RES / "models" / "S0t.json").read_text())
    base, coef = np.asarray(m["base"], np.float64), np.asarray(m["coef"], np.float64)
    tr = M.load_rows(CT.F2_TRAIN)
    s_train = T.share_table(tr)
    L = pd.read_parquet(M.OUT / "level_tier_v2.parquet")
    L = L[L.construction == sel].set_index("game_id")[[f"s_{c}" for c in range(T.NC)]]
    S = L.reindex(np.asarray(games)).to_numpy()
    tier = np.repeat(TIER_OF_CELL.astype(np.int64), N_TYPE)
    col = 3 * tier + 0                                                 # level group ES for the EN groups
    lev = M.logit(S[:, col]) - M.logit(s_train[col])[None]
    out = np.zeros((len(games), 2, 2, N_CLASS))
    for j, g in enumerate((3, 4)):
        for pt in (0, 1):
            out[:, j, pt] = M.sigmoid(base[:, g][None] + lev + coef[g * 2 + pt])
    return out, dict(groups="ENF, ENA (S0t own base / coef, ES level group)", level=sel)


def en_parity(games: np.ndarray, attr: dict, pull: dict) -> dict:
    """Engine-served vs offline fold-2 predictions on the EN rows (max |diff|): hazard (served lookup vs
    pull.hazard on the fold-2 pull rows), C1s EAF (sg 5, starter rows), block B0 (st 5 / 6), miss S0t (st 5 / 6),
    stage-4 class row (L0s baseline x ES level on st 5 / 6, through sim.class_cdf with the L1x-as attr)."""
    from nhl_sim.engine import sim as SIM
    from nhl_sim.engine import c1s_tables as CT
    out = {}
    g = np.asarray(games)
    # hazard
    sel = json.loads((MOD / "select.json").read_text())
    m = json.loads((MOD / f"fold2_{sel['selected']}.json").read_text())
    rows = pd.read_parquet(PROCESSED / "end_game" / "pull_rows_v1_20242025.parquet")
    PS = dict(kind=pull["hazard"]["kind"], table=pull["hazard"].get("table"), h_first=pull["hazard"].get("h_first"),
              h_repull=pull["hazard"].get("h_repull"), reg_end=3600)
    served = np.concatenate([SIM.pull_hazard(PS, x.dcat.to_numpy(), int(s), x.pen.to_numpy(), x.pb.to_numpy(),
                                             x.is_home.to_numpy(), x.lag.to_numpy()) for s, x in rows.groupby("s")])
    order = np.concatenate([x.index.to_numpy() for _, x in rows.groupby("s")])
    off = PL.hazard(m, rows.dcat, rows.s, rows.pen, rows.pb, rows.is_home, rows.lag)[order]
    out["hazard"] = dict(n_rows=int(len(rows)), max_abs_diff=float(np.abs(served - off).max()))
    # C1s EAF
    lab = json.loads((CT.G_RES / "fold2" / "labels_sealed.json").read_text())["C1s"]
    r = pd.read_parquet(CT.G_RES / "fold2" / "fold2_rows.parquet", columns=["game_id", "goalie_id", "is_home", "sg", "sc", "cell", "type6", "y"])
    pred = np.load(CT.G_RES / "fold2" / f"fold2_pred_{lab}.npy").astype(np.float64)
    k = (r.sg == 5).to_numpy()
    r, p = r[k].reset_index(drop=True), pred[k]
    gi = CT._gpos(g, r.game_id.to_numpy())
    team = np.where(r.is_home.to_numpy() == 1, 0, 1)
    starter = attr["goal"]["goalie_id"][gi, team] == r.goalie_id.to_numpy()
    cls = r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64)
    AS = dict(goal_cls=attr["goal"]["cls_logit"], goal_game=attr["goal"]["game_logit"], goal_sc=attr["goal"]["sc_logit"],
              en=dict(eaf_cls=pull["eaf_cls"], eaf_game=pull["eaf_game"], p_en_goal=pull["p_en_goal"]))
    ENd = dict(p_block_en=pull["p_block_en"], p_miss_en=pull["p_miss_en"])
    sv = SIM.goal_prob(AS, gi, team, np.full(len(r), 5), r.sc.to_numpy().astype(np.int64), cls)
    d = np.abs(sv - p)
    out["goal_eaf"] = dict(n_rows=int(len(r)), n_starter=int(starter.sum()), max_abs_diff=float(d[starter].max()),
                           relief_rows_mean_abs_diff=float(d[~starter].mean()) if (~starter).any() else None,
                           served_mean=float(sv.mean()), actual=float(r.y.mean()))
    # block B0 on EN rows
    lab = json.loads((CT.B_RES / "labels_sealed.json").read_text())["B0"]
    r = pd.read_parquet(CT.B_RES / "fold2_rows.parquet", columns=["game_id", "st", "ptype", "y"])
    pred = np.load(CT.B_RES / f"fold2_pred_{lab}.npy").astype(np.float64)
    k = (r.st >= 5).to_numpy()
    r, p = r[k].reset_index(drop=True), pred[k]
    gi = CT._gpos(g, r.game_id.to_numpy())
    sv = np.zeros(len(r))
    for t_ in (0, 1):
        kk = r.ptype.to_numpy() == t_
        sv[kk] = SIM.block_prob(dict(p_block_game=attr["p_block_game"], en=ENd), gi[kk], r.st.to_numpy()[kk].astype(np.int64), 3600 * t_)
    out["block"] = dict(n_rows=int(len(r)), max_abs_diff=float(np.abs(sv - p).max()),
                        by_state={int(s): dict(served=float(sv[r.st == s].mean()), actual=float(r.y[r.st == s].mean())) for s in (5, 6)})
    # miss S0t on EN rows
    lab = json.loads((CT.M_RES / "labels_sealed.json").read_text())["S0t"]
    r = pd.read_parquet(CT.M_RES / "fold2_rows.parquet", columns=["game_id", "st", "ptype", "cell", "type6", "y"])
    pred = np.load(CT.M_RES / f"fold2_pred_{lab}.npy").astype(np.float64)
    k = (r.st >= 5).to_numpy()
    r, p = r[k].reset_index(drop=True), pred[k]
    gi = CT._gpos(g, r.game_id.to_numpy())
    cls = r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64)
    sv = np.zeros(len(r))
    for t_ in (0, 1):
        kk = r.ptype.to_numpy() == t_
        sv[kk] = SIM.miss_prob(dict(p_miss=attr["p_miss_game"], en=ENd), gi[kk], r.st.to_numpy()[kk].astype(np.int64), 3600 * t_, cls[kk])
    out["miss"] = dict(n_rows=int(len(r)), max_abs_diff=float(np.abs(sv - p).max()),
                       by_state={int(s): dict(served=float(sv[r.st == s].mean()), actual=float(r.y[r.st == s].mean())) for s in (5, 6)})
    # stage-4 class on EN rows (L0s offline prediction file), served through the L1x-as attr
    lab = json.loads((CT.L_RES / "labels_sealed.json").read_text())["L0s"]
    r = pd.read_parquet(CT.L_RES / "fold2_rows.parquet", columns=["game_id", "st", "ptype"])
    pred = np.load(CT.L_RES / f"fold2_pred_{lab}.npy").astype(np.float64)
    k = (r.st >= 5).to_numpy()
    r, p = r[k].reset_index(drop=True), pred[k]
    gi = CT._gpos(g, r.game_id.to_numpy())
    A4 = dict(state_pdf=attr["state_pdf"], game_mult=attr["game_mult"], l1x_base=np.log(attr["state_pdf"]),
              l1x_game=np.asarray(attr["l1x"]["game_logit"]), l1x_sc=np.asarray(attr["l1x"]["sc_logit"]),
              l1x_lgm=np.log(attr["game_mult"]))
    sv = np.zeros_like(p)
    for t_ in (0, 1):
        kk = r.ptype.to_numpy() == t_
        if kk.any():
            st = r.st.to_numpy()[kk].astype(np.int64)
            sv[kk] = np.diff(SIM.class_cdf(A4, None, gi[kk], 0, st, np.full(kk.sum(), 3), 0, 3600 * t_), axis=1, prepend=0.0)
    out["class"] = dict(n_rows=int(len(r)), max_abs_diff=float(np.abs(sv - p).max()))
    return out
