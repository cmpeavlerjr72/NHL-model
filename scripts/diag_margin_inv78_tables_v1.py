"""INV-78 (Lane D2, 2026-10-21): the engine DEFAULT table set rebuilt from the FOLD-1 artefacts (train 2021-22 + 2022-23,
test 2023-24). DIAGNOSIS ONLY: nothing here is fitted except the T2 penalty-type table (see below); no committed table,
`sim.py` or `defaults.py` is touched. Every component is checked, served by the ENGINE's own lookup functions
(sim.block_prob / miss_prob / goal_prob / class_cdf), against the committed fold-1 offline prediction file of its round.

  stage 1  H3''-LC2 hazard: results/strength_state_lc2/fold1/models/H3_fold2.txt (the fold-1 fit; the file name is the
           trainer's), team rows from fold1/rows.parquet (season_f = 2022-23); T2 types: NO fold-1 T2 file was committed,
           so T2 is refit by the committed code (strength_state.models_r5.fit, arm T2) on the fold-1 training seasons,
           exactly as exp_strength_state_r5_types.py did for its fold-1 information line (LABELLED: refit);
           coincidental / stub tables of 2022-23.
  stage 3  A3g-c fold 1 (results/shot_attempt_r3/fold1/models, SA-R3 frozen params, tv v2, level lc1g) via
           shot_attempt.lookup.attempt_table(fold=1); 3v3 OT level via end_game.ot_level.served_att_lam(fold=1).
  stage 4  L0s M1 K500 (shot_attribute_r6_d38/fold1/models/L0s.json; s_train on 2021-22 + 2022-23) + L1x-as
           (fold1/models/L1x.json, sq_scale_v1_f1, sq_ratings_v2_f1, xg_ref_v1_f1, cell H45 P10000).
  block    B0' (SB-R1 fold-1 B0 + INV-54 4v4 / 3v3 groups fitted on the fold-1 training rows) + B1a-as (fold-1 SB-R4 B1a
           terms centred at the fold-1 training mean, block_scale_v1_f1, cell H90 P2000) via train_block_v5.fold_data(1).
  miss     S0t fold 1 (miss_sm_r2/fold1/models/S0t.json, level M2 H30, s_train on fold-1 training rows).
  goal     C1s fold 1 (goal_g_r3/fold1/models/C1s.json, *_f1 tables), ORACLE GOALIE (2023-24 box-score starters).

    diag_margin_inv78_tables_v1.py build   -> results/diag_margin_inv78_v1/fold1_tables.npz + fold1_parity.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nhl_sim.engine import c1s_tables as CT  # noqa: E402
from nhl_sim.engine import sim as SIM  # noqa: E402

OUT = ROOT / "results" / "diag_margin_inv78_v1"
F1_TRAIN = [20212022, 20222023]
TEST1, LAST1 = 20232024, 20222023
TOL = 1e-6


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def log(*a):
    print(now(), *a, flush=True)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _lab(d, k):
    return json.loads((d / "labels_sealed.json").read_text())[k]


def _gpos(games, ids):
    return CT._gpos(games, ids)


# ============================================================================================ stage 1 (H3''-LC2 + T2)
def stage1(games_expected=None):
    from nhl_sim.strength_state import lookup as LK
    from nhl_sim.strength_state import models_r5 as R5
    import lightgbm as lgb
    d = ROOT / "results/strength_state_lc2/fold1"
    rows = pd.read_parquet(d / "rows.parquet")
    if set(rows.season.unique()) != {TEST1}:
        raise ValueError("fold-1 stage-1 rows must be 2023-24 only")
    tr = rows.groupby(["game_id", "team"]).agg(season=("season", "first"), taken_own=("taken_own", "first"),
                                               drawn_opp=("drawn_opp", "first"), is_home=("is_home", "first"),
                                               b2b_own=("b2b_own", "first"), b2b_opp=("b2b_opp", "first"),
                                               level=("level", "first")).reset_index()
    tr["season_f"] = np.minimum(tr.season, LAST1)
    games = np.sort(tr.game_id.unique())
    cache = OUT / "lam_H3_lc2_fold1.npy"
    t0 = time.time()
    if cache.exists():
        lam = np.load(cache, mmap_mode="r")
    else:
        lam = LK.hazard_table_v3("H3", lgb.Booster(model_file=str(d / "models" / "H3_fold2.txt")), tr)
        np.save(cache, lam)
        lam = np.load(cache, mmap_mode="r")
    log(f"stage 1 hazard {lam.shape} ({time.time() - t0:.0f}s)")
    # parity: served hazard (per hour) x exposure vs the offline fold-1 H3 prediction on the fold-1 rows
    pred = np.load(d / "pred_H3.npy").astype(np.float64)
    gi = _gpos(games, rows.game_id.to_numpy())
    minute = np.minimum(rows.t0.to_numpy() // 60, lam.shape[2] - 1).astype(np.int64)
    st = rows.st.to_numpy().astype(np.int64)
    ok = st < lam.shape[3]
    v = np.asarray(lam[gi[ok], rows.team.to_numpy()[ok], minute[ok], st[ok], rows.sc.to_numpy()[ok],
                       rows.pdiff.to_numpy()[ok]], np.float64)
    cand = {"per hour x exposure": v * rows.exposure_s.to_numpy()[ok] / 3600.0, "per hour": v}
    par = {k: float(np.max(np.abs(c - pred[ok]) / np.maximum(pred[ok], 1e-12))) for k, c in cand.items()}
    log("stage 1 hazard parity (max rel diff):", par)
    # T2 refit on the fold-1 training seasons (no committed fold-1 T2 file); k_off irrelevant to T2 (no off term)
    tmeta = json.loads((ROOT / "results/strength_state_r5/T2_fold2.json").read_text())
    k = tmeta["k_off"]
    t_tr = R5.type_frame(F1_TRAIN, LAST1, k)
    m = R5.fit(t_tr, "T2")
    if m["seasons_ref"] != F1_TRAIN:
        raise ValueError(f"T2 refit seasons {m['seasons_ref']}")
    types = R5.team_type_table(m, tr, k, LAST1)
    smp, pim = LK.coinc_table(LAST1)
    p1 = ROOT / "results/strength_state_r1" / f"stub_tables_{LAST1}.json"
    if p1.exists():
        stub = json.loads(p1.read_text())
    else:
        st_ = LK.stub_tables(LAST1)
        stub = {kk: (vv.tolist() if hasattr(vv, "tolist") else vv) for kk, vv in st_.items()}
    tables = dict(lam=lam, types=types, coinc_smp=smp, coinc_pim=pim, goal_rate=np.asarray(stub["goal_rate"]),
                  stop_rate_ot=float(stub["stop_rate_ot"]))
    info = dict(hazard_parity_rel=par, n_rows=int(ok.sum()), n_rows_not_engine_state=int((~ok).sum()),
                t2_refit=dict(seasons_ref=m["seasons_ref"], n_type_rows=int(len(t_tr)), label="REFIT (no committed fold-1 T2 file)"),
                stub_source=str(p1) if p1.exists() else "computed in memory")
    return tables, games, info


# ============================================================================================ stage 3 (A3g-c + OT level)
def stage3(games):
    from nhl_sim.shot_attempt.lookup import attempt_table
    from nhl_sim.end_game import ot_level as OL
    G2 = load_mod("g2run", "run_shot_attempt_g2.py")
    G2.RES = ROOT / "results/shot_attempt_r3/fold1"
    G2.ROUND.update(TV="v2", LEVEL="sa_r3")
    fz = json.loads((ROOT / "docs/models/shot_attempt/sa_r3_frozen_params.json").read_text())
    cache = OUT / "att_lam_A3g-c_fold1.npy"
    t0 = time.time()
    if cache.exists():
        att = np.load(cache)
    else:
        att = attempt_table("A3g-c", G2.load_arm("A3g-c"), pd.DataFrame({"game_id": games, "season": TEST1}), fz,
                            fold=1, tv="v2", level=G2.arm_level("A3g-c"))
        np.save(cache, att)
    log(f"stage 3 table {att.shape} ({time.time() - t0:.0f}s)")
    # parity vs the offline fold-1 A3g-c prediction (rows of results/shot_attempt_r3/fold1)
    rows = pd.read_parquet(ROOT / "results/shot_attempt_r3/fold1/rows.parquet")
    pred = np.load(ROOT / "results/shot_attempt_r3/fold1/pred_A3g-c.npy").astype(np.float64)
    par = {}
    try:
        gi = _gpos(games, rows.game_id.to_numpy())
        Ma = att.shape[2]
        st = rows.st.to_numpy().astype(np.int64)
        ok = st <= 4
        mcol = "t0" if "t0" in rows else "minute"
        mi = np.minimum(rows[mcol].to_numpy()[ok] // (60 if mcol == "t0" else 1), Ma - 1).astype(np.int64)
        v = att[gi[ok], rows.team.to_numpy()[ok], mi, st[ok], rows.sc.to_numpy()[ok]].astype(np.float64)
        for k_, c in {"per hour x exposure": v * rows.exposure_s.to_numpy()[ok] / 3600.0, "per hour": v}.items():
            par[k_] = float(np.max(np.abs(c - pred[ok]) / np.maximum(pred[ok], 1e-12)))
        par["n_rows"] = int(ok.sum())
    except Exception as ex:  # noqa: BLE001
        par["error"] = repr(ex)
    log("stage 3 parity:", par)
    # ot_level.served_delta reads the frozen A3g-c cell from the FOLD-2 model file for any fold (A3GC_CELL is a fixed
    # path); for fold 1 the frozen cell is the fold-1 A3g-c file's (listed in the report; module not edited).
    OL.A3GC_CELL = str(ROOT / "results/shot_attempt_r3/fold1/models/A3g-c.json")
    new, oinfo = OL.served_att_lam(att, games, 1)
    opar = OL.served_parity(new, games, 1)
    log(f"ot3v3 fold-1 parity: max rel diff {opar['max_rel_diff']:.3e} over {opar['n_rows']:,} rows")
    if not opar["max_rel_diff"] <= TOL:
        raise RuntimeError(f"served 3v3 != offline: {opar}")
    return new, dict(a3gc_parity=par, ot3v3_parity=opar, ot3v3=dict((k, v) for k, v in oinfo.items() if np.isscalar(v)))


# ============================================================================================ stage 4: L0s M1 K500 + L1x-as
def l0s_f1(games):
    from nhl_sim.shot_attribute import mix_level as ML
    from nhl_sim.shot_attribute import models as M
    from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE
    R6 = ROOT / "results/shot_attribute_r6_d38/fold1"
    m = json.loads((R6 / "models" / "L0s.json").read_text())
    state_pdf = np.asarray(m["p"], np.float64).reshape(7, 2, N_CELL * N_TYPE)
    tr = M.load_rows(F1_TRAIN)
    u = tr[~tr.blocked]
    s_train = ML.share_table(u)
    L = pd.read_parquet(M.SA / "mix_level_v2.parquet")
    L = L[L.construction == CT.LEVEL].set_index("game_id")
    S = L[[f"s_{g}_{c}" for g in range(3) for c in range(N_CELL)]].reindex(np.asarray(games)).to_numpy()
    if np.isnan(S).any():
        raise ValueError("games without an M1 K500 mix level")
    gm = np.repeat(S.reshape(len(games), 3, N_CELL) / s_train[None], N_TYPE, axis=2)
    return state_pdf, gm


def l1xas_f1(games):
    from nhl_sim.data.load import PROCESSED, load_games
    from nhl_sim.shot_attribute import models as M
    from nhl_sim.shot_attribute import models_x as MX
    from nhl_sim.shot_attribute.tables import N_CLASS, OPP_RATING_GROUP
    from nhl_sim.shot_attribute import serve_l1xas as SV
    games = np.asarray(games, np.int64)
    m = json.loads((ROOT / "results/shot_attribute_r6_d38/fold1/models/L1x.json").read_text())
    if not (m.get("ot0") is True and m.get("construction") == "Qa"):
        raise ValueError("expected the SL-R6 L1x-ot0 (Qa) fold-1 model")
    W, xbar = np.asarray(m["W"], np.float64), np.asarray(m["xbar"], np.float64)
    sel = json.loads((ROOT / "results/shot_attribute_r7/select.json").read_text())["selected"]
    sc = pd.read_parquet(M.SA / "sq_scale_v1_f1.parquet")
    sc = sc[sc.cell == sel]
    sd_f, sd_a = float(sc.sd_for.iloc[0]), float(sc.sd_against.iloc[0])
    C = MX.qdir(np.load(M.SA / "xg_ref_v1_f1.npy"))
    g = load_games(None, columns=["game_id", "home_id", "away_id", "game_date_local"]).set_index("game_id").loc[games]
    dkey = pd.to_datetime(g.game_date_local).to_numpy("datetime64[D]")
    idx = pd.to_datetime(sc.date).to_numpy("datetime64[D]")
    sf = pd.Series(sc.s_for.to_numpy(), index=idx).reindex(dkey).to_numpy()
    sa = pd.Series(sc.s_against.to_numpy(), index=idx).reindex(dkey).to_numpy()
    q = pd.read_parquet(M.SA / "sq_ratings_v2_f1.parquet").set_index(["game_id", "team_id"])
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    b2b = tg.set_index(["game_id", "team_id"]).b2b
    team = np.stack([g.home_id.to_numpy(), g.away_id.to_numpy()], 1).astype(np.int64)

    def at(frame, col, j):
        return frame[col].reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float)
    GRP = SV.GRP
    rf = np.stack([np.stack([at(q, f"rf_{x}_Qa", j) for x in GRP], 1) for j in (0, 1)], 1)
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
            scl[0, s7] += (float(s7 == k) - xbar[wi[f"sc{k}"]]) * W[wi[f"sc{k}"]]
    return dict(game_logit=gl, sc_logit=scl, label=SV.LABEL + " [FOLD 1]")


def l1xas_parity_f1(games, sp, gm, lx):
    R7 = ROOT / "results/shot_attribute_r7/fold1"
    rows = pd.read_parquet(R7 / "fold1_rows.parquet", columns=["game_id", "team", "st", "ptype", "sc"])
    pred = np.load(R7 / f"fold1_pred_{_lab(R7, 'L1xas')}.npy").astype(np.float64)
    gi = _gpos(games, rows.game_id.to_numpy())
    st = rows.st.to_numpy().astype(np.int64)
    AS = dict(state_pdf=sp, game_mult=gm, l1x_game=lx["game_logit"], l1x_sc=lx["sc_logit"], l1x_base=np.log(sp),
              l1x_lgm=np.log(gm))
    d = np.zeros(len(rows))
    for pt in (0, 1):
        for team in (0, 1):
            k = (rows.ptype.to_numpy() == pt) & (rows.team.to_numpy() == team) & (st <= 4)
            if k.any():
                cdf = SIM.class_cdf(AS, None, gi[k], team, st[k], rows.sc.to_numpy().astype(np.int64)[k], None, 3600 * pt)
                d[k] = np.abs(np.diff(cdf, axis=1, prepend=0.0) - pred[k]).max(1)
    return dict(n_rows=int((st <= 4).sum()), max_abs_diff=float(d[st <= 4].max()))


# ============================================================================================ block B0' + B1a-as
def block_f1(games):
    """B0' (fold-1 SB-R1 B0 on 5v5 / PP / PK + INV-54 4v4 / 3v3 groups fitted on the fold-1 training rows) and B1a-as,
    from train_block_v5.fold_data(1, test=True): the code that wrote the fold-1 offline predictions."""
    TB = load_mod("tb5", "train_block_v5.py")
    Dd = TB.fold_data(1, True)
    return TB, Dd


def block_tables_f1(games):
    from nhl_sim.block import data as D
    from nhl_sim.block.data import logit, sigmoid
    from nhl_sim.block.models import fit_logit_offset
    from nhl_sim.block import scale as SC
    from nhl_sim.data.load import PROCESSED
    from nhl_sim.shot_attribute.tables import OPP_RATING_GROUP
    from nhl_sim.block import serve_b1aas as SB
    games = np.asarray(games, np.int64)
    B1 = ROOT / "results/block_sb_r1"
    sel = json.loads((B1 / "step0.json").read_text())["selected"]
    if sel != CT.LEVEL:
        raise ValueError("B0 level")
    coef = np.asarray(json.loads((B1 / "fold1/models/B0.json").read_text())["coef"], np.float64)
    gl = pd.read_parquet(D.OUT / "games_v1.parquet", columns=["game_id"])
    a_tr = D.load_attempts(F1_TRAIN).merge(gl, on="game_id")
    s_train = D.share_table(a_tr)
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == CT.LEVEL].set_index("game_id")[["s_0", "s_1", "s_2"]].reindex(games)
    if L.isna().any().any():
        raise ValueError("games without an M1 K500 level")
    off = logit(L.to_numpy()) - logit(s_train)[None]
    pbg = np.zeros((len(games), 5, 2))
    for rg in range(3):
        for pt in range(2):
            pbg[:, rg, pt] = sigmoid(coef[rg * 2 + pt] + off[:, rg])
    gtab = pd.read_parquet(D.OUT / "games_v1.parquet")
    a = D.load_attempts(D.SEASONS)
    a = a[a.game_id.isin(gtab.game_id)]
    tr = a[a.season.isin(F1_TRAIN)]
    groups = {}
    for st, nm in ((3, "4v4"), (4, "3v3")):
        lev = CT._state_level(a, gtab, st)
        x = tr[tr.st == st]
        s_tr = float(x.blocked.mean())
        o = logit(lev.reindex(x.game_id.to_numpy()).to_numpy()) - logit(s_tr)
        w, nit = fit_logit_offset(np.ones((len(x), 1)), x.blocked.to_numpy(), o, n_free=1)
        Lg = lev.reindex(games).to_numpy()
        if np.isnan(Lg).any():
            raise ValueError(f"games without a {nm} level")
        pbg[:, st, :] = sigmoid(w[0] + logit(Lg) - logit(s_tr))[:, None]
        groups[nm] = dict(coef=float(w[0]), s_train=s_tr, n_train=int(len(x)))
    # B1a-as fold 1: frozen fold-1 SB-R4 B1a non-rating terms centred at the fold-1 training mean (train_block_v5)
    TB, Dd = block_f1(games)
    W, xbar = np.asarray(Dd["W"], np.float64), np.asarray(Dd["xbar"], np.float64)
    sd_f, sd_a = Dd["sd"]
    fz = json.loads(SB.FROZEN.read_text())
    snap = pd.read_parquet(TB.snap_path(1))
    snap = snap[snap.cell == fz["cell"]]
    gt = gtab.set_index("game_id").loc[games]
    sf, sa = SC.attach_scale(gt.date.to_numpy(), snap)
    team = np.stack([gt.home_id.to_numpy(), gt.away_id.to_numpy()], 1).astype(np.int64)
    rt = pd.read_parquet(D.OUT / "ratings_r4_Ra.parquet").set_index(["game_id", "team_id"])
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    b2b = tg.set_index(["game_id", "team_id"]).b2b
    af = pd.read_parquet(D.OUT / "arena_v1.parquet").set_index("game_id").arena_f.reindex(games).to_numpy(float)
    k = D.wkey(0.7, 1000)

    def at(series, j):
        return series.reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float)
    rf = np.stack([np.stack([at(rt[f"rf_{x}_{k}"], j) for x in D.RG], 1) for j in (0, 1)], 1)
    ra = np.stack([np.stack([at(rt[f"ra_{x}_{k}"], j) for x in D.RG], 1) for j in (0, 1)], 1)
    Bb = np.stack([at(b2b, j) for j in (0, 1)], 1)
    for nm, v in (("ratings", rf), ("ratings", ra), ("b2b", Bb), ("arena", af), ("scale", sf)):
        if np.isnan(v).any():
            raise ValueError(f"missing {nm}")
    xs, Ws = xbar[:6], W[:6]
    glg = np.zeros((len(games), 2, 5))
    for j in (0, 1):
        o = 1 - j
        lin = ((1 - j) - xbar[6]) * W[6] + (Bb[:, j] - xbar[7]) * W[7] + (Bb[:, o] - xbar[8]) * W[8] \
            + (af - xbar[9]) * W[9] - xs @ Ws
        for st in range(5):
            rg = SB.ST_RGRP[st]
            glg[:, j, st] = lin + sf * rf[:, j, rg] / sd_f + sa * ra[:, o, OPP_RATING_GROUP[rg]] / sd_a
    scl = np.zeros(7)
    scl[list(SB.SC_COLS)] = Ws
    b1 = dict(game_logit=glg, sc_logit=scl, label=SB.LABEL + " [FOLD 1]")
    return pbg, b1, dict(groups=groups, groups_trainer=Dd.get("groups"), s_train=s_train.tolist(), sd=list(Dd["sd"]))


def block_parity_f1(games, pbg, b1):
    res = ROOT / "results/block_sb_r5/fold1"
    rows = pd.read_parquet(res / "fold1_rows.parquet", columns=["game_id", "team", "st", "sc", "t", "ptype"])
    pred = np.load(res / f"fold1_pred_{_lab(res, 'B1aas')}.npy").astype(np.float64)
    m = (rows.st <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = _gpos(games, r.game_id.to_numpy())
    AS = dict(p_block_game=pbg, b1aas_base=np.log(pbg) - np.log1p(-pbg), b1aas_game=b1["game_logit"], b1aas_sc=b1["sc_logit"])
    served = np.zeros(len(r))
    st, sc, tm, pt = (r[c].to_numpy().astype(np.int64) for c in ("st", "sc", "team", "ptype"))
    for team in (0, 1):
        for t_ in (0, 1):
            k = (tm == team) & (pt == t_)
            served[k] = SIM.block_prob(AS, gi[k], st[k], 3600 * t_, team, sc[k])
    d = np.abs(served - p)
    return dict(n_rows=int(len(r)), max_abs_diff=float(d.max()),
                by_state={nm: float(d[st == s_].max()) for s_, nm in enumerate(("5v5", "PP", "PK", "4v4", "3v3"))})


# ============================================================================================ miss S0t
def miss_f1(games):
    from nhl_sim.miss import data as M
    from nhl_sim.miss import tier as T
    from nhl_sim.shot_attribute.tables import N_CLASS, N_TYPE, TIER_OF_CELL
    MR = ROOT / "results/miss_sm_r2"
    sel = json.loads((MR / "step1.json").read_text())["selected"]
    m = json.loads((MR / "fold1/models/S0t.json").read_text())
    base, coef = np.asarray(m["base"], np.float64), np.asarray(m["coef"], np.float64)
    tr = M.load_rows(F1_TRAIN)
    s_train = T.share_table(tr)
    L = pd.read_parquet(M.OUT / "level_tier_v2.parquet")
    L = L[L.construction == sel].set_index("game_id")[[f"s_{c}" for c in range(T.NC)]]
    S = L.reindex(np.asarray(games)).to_numpy()
    if np.isnan(S).any():
        raise ValueError("games without a miss level")
    tier = np.repeat(TIER_OF_CELL.astype(np.int64), N_TYPE)
    out = np.zeros((len(games), 3, 2, N_CLASS))
    for g in range(3):
        col = 3 * tier + g
        lev = M.logit(S[:, col]) - M.logit(s_train[col])[None]
        for pt in (0, 1):
            out[:, g, pt] = M.sigmoid(base[:, g][None] + lev + coef[g * 2 + pt])
    return out


def miss_parity_f1(games, pmg):
    res = ROOT / "results/miss_sm_r2/fold1"
    rows = pd.read_parquet(res / "fold1_rows.parquet", columns=["game_id", "st", "grp", "ptype", "cell", "type6"])
    pred = np.load(res / f"fold1_pred_{_lab(res, 'S0t')}.npy").astype(np.float64)
    m = (rows.st <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = _gpos(games, r.game_id.to_numpy())
    st = r.st.to_numpy().astype(np.int64)
    cls = r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64)
    served = np.zeros(len(r))
    for t_ in (0, 1):
        k = r.ptype.to_numpy() == t_
        served[k] = SIM.miss_prob(dict(p_miss=pmg), gi[k], st[k], 3600 * t_, cls[k])
    return dict(n_rows=int(len(r)), max_abs_diff=float(np.abs(served - p).max()))


# ============================================================================================ goal C1s
def goal_parts_f1(games):
    from nhl_sim.goal import data as GD
    from nhl_sim.data.load import PROCESSED
    s1 = json.loads((CT.G_R1 / "select.json").read_text())
    mdl = json.loads((CT.G_RES / "fold1" / "models" / "C1s.json").read_text())
    s3 = json.loads((CT.G_RES / "select.json").read_text())
    if mdl.get("arm") != "C1s" or mdl.get("cell") != s3["selected"]:
        raise ValueError("C1s fold-1 model / cell mismatch")
    coef = np.asarray(mdl["coef"], np.float64)
    T = np.load(GD.OUT / "cell_table_f1.npy")
    lv = pd.read_parquet(GD.OUT / "level_v1_f1.parquet")
    lv = lv[lv.construction == CT.LEVEL].set_index("game_id")[[f"d_{g}" for g in range(GD.N_LG)]]
    games = np.asarray(games)
    delta = lv.reindex(games).to_numpy()
    gtab = pd.read_parquet(PROCESSED / "block" / "games_v1.parquet").set_index("game_id").loc[games]
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    b2b = tg.set_index(["game_id", "team_id"]).b2b
    team = np.stack([gtab.home_id.to_numpy(), gtab.away_id.to_numpy()], 1).astype(np.int64)
    B = np.stack([b2b.reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float) for j in (0, 1)], 1)
    af = pd.read_parquet(GD.SA / "arena_dist_v1.parquet", columns=["game_id", "arena_f"]).set_index("game_id") \
        .arena_f.reindex(games).to_numpy(float)
    RT = pd.read_parquet(GD.OUT / "ratings_team_v1_f1.parquet")
    tcol = GD.rkey(*s1["team_cell"])
    rt = RT.set_index(["game_id", "team_id"])[tcol]
    TR = np.stack([rt.reindex(pd.MultiIndex.from_arrays([games, team[:, j]])).to_numpy(float) for j in (0, 1)], 1)
    RG = pd.read_parquet(GD.OUT / "ratings_goalie_v1_f1.parquet")
    gcol = GD.rkey(*s1["goalie_cell"])
    sc = pd.read_parquet(GD.OUT / "goalie_scale_v1_f1.parquet")
    sc = sc[sc.cell == s3["selected"]]
    smap = pd.Series(sc.s.to_numpy(), index=pd.to_datetime(sc.date).to_numpy("datetime64[D]"))
    s_date = smap.reindex(pd.to_datetime(gtab.date).to_numpy("datetime64[D]")).to_numpy()
    for nm, v in (("level", delta), ("b2b", B), ("arena_f", af), ("team rating", TR), ("goalie scale", s_date)):
        if np.isnan(v).any():
            raise ValueError(f"games without a {nm}")
    return dict(coef=coef, T=T, delta=delta, team=team, B=B, af=af, TR=TR, s_date=s_date, spec=s1["spec"],
                sd_ref=float(mdl["sd_ref"]), RG=RG.set_index(["game_id", "goalie_id"])[gcol], cell=s3["selected"],
                gcol=gcol, tcol=tcol)


def goal_f1(games, P):
    st_ = CT.starters(games, season=TEST1)
    g, _ = CT.goal_c1s_tables(games, goalie_against=st_[:, ::-1].copy(), P=P)
    g["label"] = CT.GOAL_LABEL + " [FOLD 1]"
    return g


def goal_parity_f1(games, goal, P):
    res = CT.G_RES / "fold1"
    rows = pd.read_parquet(res / "fold1_rows.parquet",
                           columns=["game_id", "team_id", "goalie_id", "is_home", "sg", "sc", "cell", "type6"])
    pred = np.load(res / f"fold1_pred_{_lab(res, 'C1s')}.npy").astype(np.float64)
    m = (rows.sg <= 4).to_numpy()
    r, p = rows[m].reset_index(drop=True), pred[m]
    gi = _gpos(games, r.game_id.to_numpy())
    team = np.where(r.is_home.to_numpy() == 1, 0, 1)
    if not (P["team"][gi, team] == r.team_id.to_numpy()).all():
        raise ValueError("team slot mismatch")
    st, sc = r.sg.to_numpy().astype(np.int64), r.sc.to_numpy().astype(np.int64)
    cls = r.cell.to_numpy().astype(np.int64) * 6 + r.type6.to_numpy().astype(np.int64)
    AS = dict(goal_cls=goal["cls_logit"], goal_game=goal["game_logit"], goal_sc=goal["sc_logit"])
    served = SIM.goal_prob(AS, gi, team, st, sc, cls)
    starter = goal["goalie_id"][gi, team] == r.goalie_id.to_numpy()
    d = np.abs(served - p)
    return dict(n_rows=int(len(r)), n_starter_rows=int(starter.sum()), max_abs_diff_starter=float(d[starter].max()),
                relief_rows_mean_abs_diff_served_starter=float(d[~starter].mean()) if (~starter).any() else None)


# ============================================================================================ all
def build_all():
    OUT.mkdir(parents=True, exist_ok=True)
    from nhl_sim.shot_attempt.lookup import goal_stub
    from nhl_sim.shot_attribute.tables import N_TYPE
    t0 = time.time()
    tables, games, s1info = stage1()
    att, s3info = stage3(games)
    tables["att_lam"] = att
    tables["p_goal"] = goal_stub(LAST1)
    sp, gm = l0s_f1(games)
    lx = l1xas_f1(games)
    par = dict(l1xas=l1xas_parity_f1(games, sp, gm, lx))
    log("L1x-as fold-1 parity", par["l1xas"])
    pbg, b1, binfo = block_tables_f1(games)
    par["block_b1aas"] = block_parity_f1(games, pbg, b1)
    log("B1a-as fold-1 parity", par["block_b1aas"])
    pmg = miss_f1(games)
    par["miss"] = miss_parity_f1(games, pmg)
    log("S0t fold-1 parity", par["miss"])
    P = goal_parts_f1(games)
    goal = goal_f1(games, P)
    par["goal"] = goal_parity_f1(games, goal, P)
    log("C1s fold-1 parity", par["goal"])
    xg = np.load(ROOT / "data/processed/shot_attribute/xg_ref_v1_f1.npy")[:, :3]
    from nhl_sim.engine.defaults import DEFAULT_STAND_IN
    attr = dict(state_pdf=sp, game_mult=gm, l1x=lx, p_block_game=pbg, p_miss_game=pmg, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(DEFAULT_STAND_IN), block_b1aas=b1)
    tables["attr"] = attr
    bad = {k: v["max_abs_diff" if "max_abs_diff" in v else "max_abs_diff_starter"] for k, v in par.items()
           if not v.get("max_abs_diff", v.get("max_abs_diff_starter", 1.0)) <= TOL}
    info = dict(stage1=s1info, stage3=s3info, parity=par, block=binfo, bad=bad, seconds=time.time() - t0)
    return tables, games, info


def cmd_build(_a):
    tables, games, info = build_all()
    (OUT / "fold1_parity.json").write_text(json.dumps(info, indent=1, default=float))
    log("parity failures:", info["bad"] or "none", f"({info['seconds']:.0f}s)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    a = ap.parse_args()
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    {"build": cmd_build}[a.cmd](a)
