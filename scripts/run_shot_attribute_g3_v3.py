"""SL-R3 closed loop: G3 and the G2 re-check for a levelled shot-attribute arm, with the level E applied IN THE ENGINE
from the GameState recording-era flag (docs/models/shot_attribute/experiments.md SL-R3; D24). Versioned copy of
run_shot_attribute_g3_v2.py. Changes: the lookup serves the arm's UNLEVELLED joint probabilities (attr["pdf"]) and the
level as attr["era_mult"][era, rating group, class] = exp(log(s_E[era] / s_train)) on the class's cell; simulate gets
seasons= so GameState.rec_era is set (rules.recording_era, 2023-24 boundary fixed); arms L0m (SL-R2 model, plumbing)
and L3b (SL-R3 model, gate); a served-vs-trained parity check (lookup + era level vs the arm's levelled prediction on
the real fold-2 rows) before any seed runs; paths and report names. Grading is unchanged.

Engine: stage 1 = H3''-LC2 + T2 (D18; `run_shot_attempt_g2.stage1_tables("lc2t2")`, per_team_types=True); stage 3 =
A3g-c (D20; cached results/shot_attempt_r3/att_lam_A3g-c_fold2.npy); stage 4 = the arm under test through the
default-off `attr` variant of engine/sim.py. Under step-0 rule (b): each attempt is first blocked at the empirical
block rate by strength group of 2023-24 (the last fold-2 training season; LABELLED STUB for stage 5); an unblocked
attempt draws its cell x type class from the arm's lookup; the goal is a draw at xG_ref (fold-2 table; LABELLED STUB
goal model, SOG / miss / goal in one draw). No goalie pull (EN unreachable), shootout skipped.

    run_shot_attribute_g3_v3.py table --arm L0m              (build + cache the lookup, era level, parity check)
    run_shot_attribute_g3_v3.py sim   --arm L0m --seed0 0 --nseeds 50 [--tag sl_r3_g3_L0m]
    run_shot_attribute_g3_v3.py grade --arm L0m [--tag sl_r3_g3_L0m]
        -> docs/tests/gates_g3_sl_r3_<arm>_2026-10-16.md (G3) and docs/tests/gates_g2_sl_r3_<arm>_2026-10-16.md (G2 re-check)
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.engine.rules import RECORDING_ERAS, era_for_season, recording_era  # noqa: E402
from nhl_sim.engine.sim import simulate  # noqa: E402
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import models_m as MM  # noqa: E402
from nhl_sim.shot_attribute import models_b as MM3  # noqa: E402
from nhl_sim.shot_attribute.lookup import attr_table  # noqa: E402
from nhl_sim.shot_attribute.tables import (N_CELL, N_TYPE, TIER_NAMES, TIER_OF_CELL, TYPE_NAMES)  # noqa: E402

RES = Path("results/shot_attribute_r2")            # SL-R2: L0m model, fold-2 rows (ratings), step-0 selection
RES3 = Path("results/shot_attribute_r3")           # SL-R3: L3b model, lookup caches
FROZEN = Path("docs/models/shot_attribute/sl_r2_frozen_params.json")
LEVELS = M.SA / "mix_level_v2.parquet"
TEST, LAST_TRAIN = 20242025, 20232024
ST5 = ("5v5", "PP", "PK", "4v4", "3v3")
ST_RGRP = np.array([0, 1, 2, 0, 0])
NB, BSEED = 1000, 20261016


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def g2mod():
    spec = importlib.util.spec_from_file_location("g2run", ROOT / "scripts" / "run_shot_attempt_g2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RES = Path("results/shot_attempt_r3")
    mod.FROZEN = Path("docs/models/shot_attempt/sa_r3_frozen_params.json")
    mod.ROUND.update(TV="v2", LEVEL="sa_r3")
    return mod


def load_model(arm):
    if arm == "L0m":
        return json.loads((RES / "models" / "L0m.json").read_text())
    if arm in ("L3b", "L3bs2"):
        import lightgbm as lgb
        return (lgb.Booster(model_file=str(RES3 / "models" / f"{arm}.txt")),
                json.loads((RES3 / "models" / "L0.json").read_text()))
    raise ValueError(f"SL-R3 closed loop serves L0m or L3b, not {arm}")


def train_shares():
    tr = M.load_rows([20212022, 20222023, 20232024])
    return tr[~tr.blocked]


def era_mult_table(u_train):
    """(3, 3, 78): [recording era, rating group ES / PP-for / PK, class] = exp(log(s_E[era, lg] / s_train[lg])) on the
    class's cell; s_E[era] = pooled shares of the fold-2 training rows of that era (SL-R2 level E); row 0 unused (NaN)."""
    s_train = ML.share_table(u_train)
    era_tr = recording_era(u_train.season.to_numpy())
    em = np.full((max(RECORDING_ERAS) + 1, 3, N_CELL * N_TYPE), np.nan)
    for e in RECORDING_ERAS:
        s_e = ML.share_table(u_train[era_tr == e])
        em[e] = np.repeat(s_e / s_train, N_TYPE, axis=1)      # level group = rating group for ES / PP / PK
    return em, s_train


def unlevelled_predict(arm, model):
    """Row predictor WITHOUT the level (offset 0): the engine multiplies by era_mult[rec_era] and renormalises."""
    if arm == "L0m":
        return lambda r: M.predict_l0(model, r)
    booster, l0 = model
    return lambda r: MM3.predict_l3b(booster, l0, r, np.zeros((len(r), N_CELL)))


def levelled_predict(arm, model, s_train):
    """The arm's levelled prediction exactly as trained / graded (the SL-R2 E_f2 level from the step-0 parquet)."""
    Ldf = pd.read_parquet(LEVELS)
    Ldf = Ldf[Ldf.construction == "E_f2"]
    if arm == "L0m":
        return lambda r: MM.predict_arm_m("L0m", model, r, ML.row_offset(r, Ldf, s_train))
    booster, l0 = model
    return lambda r: MM3.predict_l3b(booster, l0, r, ML.row_offset(r, Ldf, s_train))


def build_table(arm, games):
    """-> (pdf, imap, era_mult), cached; asserts served == trained on the real fold-2 rows (ES / PP / PK groups)."""
    RES3.mkdir(parents=True, exist_ok=True)
    cache = RES3 / f"attr_pdf_{arm}_fold2.npz"
    if json.loads((RES / "step0.json").read_text())["selected"] != "E":
        raise ValueError("SL-R3 inherits level E")
    u_tr = train_shares()
    em, s_train = era_mult_table(u_tr)
    if cache.exists():
        z = np.load(cache)
        if not (z["games"] == games).all():
            raise ValueError("cached attribute table is for another game list")
        return z["pdf"], z["imap"], em
    fz = json.loads(FROZEN.read_text())
    m = load_model(arm)
    gdf = pd.DataFrame({"game_id": games, "season": TEST})
    t0 = time.time()
    pdf, imap = attr_table(arm, m[0] if arm.startswith("L3") else m, gdf, 2, fz["w"], fz["prior_strength_attempts"],
                           predict=unlevelled_predict(arm, m), as_pdf=True)
    print(now(), f"lookup {pdf.shape} ({time.time() - t0:.0f}s)", flush=True)
    # parity: served (pdf x era_mult[rec_era], renormalised) vs the arm's levelled prediction on the real test rows
    r = M.attach_features(M.load_rows([TEST]), 2, fz["w"], fz["prior_strength_attempts"])
    r = r[r.grp <= 2].reset_index(drop=True)
    gpos = np.searchsorted(games, r.game_id.to_numpy())
    if not (games[np.minimum(gpos, len(games) - 1)] == r.game_id.to_numpy()).all():
        raise ValueError("test rows outside the lookup game list")
    minute = np.minimum(r.clock.to_numpy(), 99)
    era = recording_era(r.season.to_numpy())
    served = pdf[gpos, r.team.to_numpy(), imap[minute], r.grp.to_numpy(), r.sc.to_numpy()].astype(np.float64)
    served *= em[era, r.grp.to_numpy()]
    served /= served.sum(1, keepdims=True)
    trained = levelled_predict(arm, m, s_train)(r)
    reg = r.period.to_numpy() <= 4
    d = np.abs(served - trained).max(1)
    par = dict(arm=arm, n_rows=int(len(r)), max_abs_dP_all=float(d.max()), max_abs_dP_period_le4=float(d[reg].max()),
               n_rows_dP_gt_1e5=int((d > 1e-5).sum()),
               era_mult_era2_range=[float(np.nanmin(em[2])), float(np.nanmax(em[2]))])
    Ldf = pd.read_parquet(LEVELS)
    Ldf = Ldf[Ldf.construction == "E_f2"].set_index("game_id").reindex(games)
    cols = [f"s_{g}_{c}" for g in range(3) for c in range(N_CELL)]
    sE = Ldf[cols].to_numpy().reshape(len(games), 3, N_CELL)
    par["level_check_max_rel_vs_E_f2_parquet"] = float(np.abs(sE / s_train[None] / em[2][None, :, ::N_TYPE] - 1).max())
    print(now(), "parity", par, flush=True)
    (RES3 / f"lookup_parity_{arm}.json").write_text(json.dumps(par, indent=1))
    if par["max_abs_dP_period_le4"] > 1e-5 or par["level_check_max_rel_vs_E_f2_parquet"] > 1e-9:
        raise RuntimeError(f"served != trained: {par}")
    np.savez(cache, pdf=pdf, imap=imap, games=games)
    return pdf, imap, em


def cmd_table(a):
    G2 = g2mod()
    _, games, _ = G2.stage1_tables("lc2t2")
    build_table(a.arm, games)


def block_stub():
    """Empirical block share by rating group (ES / PP-for / PK) in the last fold-2 training season, per team-view state."""
    r = M.load_rows([LAST_TRAIN])
    r = r[r.grp <= 2]
    pb = r.groupby("grp").blocked.mean().reindex(range(3)).to_numpy()
    return pb[ST_RGRP], pb


def cmd_sim(a):
    out = Path("results") / a.tag
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.tag, a.seed0, a.nseeds, flush=True)
    G2 = g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(Path("results/shot_attempt_r3/att_lam_A3g-c_fold2.npy"))
    from nhl_sim.shot_attempt.lookup import goal_stub
    tables["p_goal"] = goal_stub(LAST_TRAIN)            # unused under the attr variant; required by the engine
    t0 = time.time()
    pdf, imap, em = build_table(a.arm, games)
    pbs, pb = block_stub()
    xg = np.load(Path("data/processed/shot_attribute/xg_ref_v1_f2.npy"))[:, :3]
    tables["attr"] = dict(pdf=pdf, era_mult=em, interval_of_minute=imap, p_block=pbs, xg=xg, n_type=N_TYPE)
    print(now(), f"attr pdf {pdf.shape} + era level ({time.time() - t0:.0f}s); p_block ES/PP/PK {np.round(pb, 4)}", flush=True)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    parts = []
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        o = simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0, per_team_types=True,
                     seasons=np.full(len(games), TEST))
        es = np.array(["", "REG", "OT", "SO"])[o["end_state"]]
        if (es == "").any():
            raise RuntimeError("unfinished sims")
        cols = {"game_id": games[o["game_idx"]], "seed": o["seed"].astype(np.int32), "home_goals": o["score"][:, 0],
                "away_goals": o["score"][:, 1], "end_state": es,
                "home_win": np.where(es == "SO", o["so_home_win"], o["score"][:, 0] > o["score"][:, 1]),
                "played_s": o["played_s"]}
        for p, ti in (("h", 0), ("a", 1)):
            for k in range(5):
                cols[f"att_{p}_st{k}"] = o["att_st"][:, ti, k]
                cols[f"fen_{p}_st{k}"] = o["attr_fen"][:, ti, k]
                cols[f"xg_{p}_st{k}"] = o["attr_xg"][:, ti, k].astype(np.float32)
                cols[f"gl_{p}_st{k}"] = o["attr_goals"][:, ti, k]
                for c in range(N_CELL):
                    cols[f"cell_{p}_st{k}_{c}"] = o["attr_cell"][:, ti, k, c].astype(np.int16)
                for c in range(N_TYPE):
                    cols[f"type_{p}_st{k}_{c}"] = o["attr_type"][:, ti, k, c].astype(np.int16)
            for k in range(7):
                cols[f"att_{p}_sc{k}"] = o["att_sc"][:, ti, k]
        for s_ in range(5):
            for c in range(7):
                cols[f"toi_{s_}_{c}"] = o["toi_st_sc"][:, s_, c]
        parts.append(pd.DataFrame(cols))
        print(now(), f"seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    pd.concat(parts, ignore_index=True).to_parquet(out / f"part_{a.seed0:04d}.parquet", index=False)
    (out / f"meta_{a.seed0:04d}.json").write_text(json.dumps(dict(
        arm="A3g-c", attr_arm=a.arm, round="SA-R3", stage1=G2.S1_LABEL["lc2t2"], stage3="A3g-c (D20)",
        stage4=f"{a.arm} (SL-R3; level E applied in the engine from GameState.rec_era), rule (b)", rec_era=2, block="STUB: empirical block share by group, 2023-24 " + str(np.round(pb, 5).tolist()),
        goals="STUB: xG_ref (fold-2 table) per sampled cell x type x group", p_goal=tables["p_goal"].tolist(),
        goalie_pull="none (EN unreachable)", shootout="skipped", fold=2, season=TEST, sealed_touched=False,
        seed0=a.seed0, nseeds=a.nseeds)))
    print(now(), "done", flush=True)


# --------------------------------------------------------------------------- G3 grading
def actual_frame():
    r = M.load_rows([TEST])
    g = load_games([TEST], columns=["game_id", "home_id", "away_id", "game_type"])
    r = r.drop(columns="game_type").merge(g.drop(columns="season"), on="game_id", how="left", validate="many_to_one")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    xg = np.load(Path("data/processed/shot_attribute/xg_ref_v1_f2.npy"))
    u = r[~r.blocked].copy()
    u["xg"] = xg[u.cls.to_numpy(), u.grp.to_numpy()]
    return r, u


def sim_long(s):
    """Per (game, seed, team, st): attempts, unblocked, xG sum, goals, cell counts, type counts."""
    recs = []
    for p, ti in (("h", 0), ("a", 1)):
        for k in range(5):
            d = pd.DataFrame({"game_id": s.game_id.to_numpy(), "seed": s.seed.to_numpy(), "team": ti, "st": k,
                              "game_type": s.game_type.to_numpy(), "att": s[f"att_{p}_st{k}"].to_numpy(),
                              "fen": s[f"fen_{p}_st{k}"].to_numpy(), "xg": s[f"xg_{p}_st{k}"].to_numpy(np.float64),
                              "gl": s[f"gl_{p}_st{k}"].to_numpy()})
            C = np.stack([s[f"cell_{p}_st{k}_{c}"].to_numpy() for c in range(N_CELL)], 1)
            for t_ in range(3):
                d[f"tier{t_}"] = C[:, TIER_OF_CELL == t_].sum(1)
            for c in range(N_TYPE):
                d[f"type{c}"] = s[f"type_{p}_st{k}_{c}"].to_numpy()
            recs.append(d)
    return pd.concat(recs, ignore_index=True)


def act_long(r, u):
    a = r[r.st <= 4].groupby(["game_id", "team", "st"]).size().rename("att")
    x = u[u.st <= 4]
    f = x.groupby(["game_id", "team", "st"]).agg(fen=("xg", "size"), xg=("xg", "sum"), gl=("is_goal", "sum"))
    for t_ in range(3):
        f[f"tier{t_}"] = x.assign(v=(TIER_OF_CELL[x.cell.to_numpy()] == t_)).groupby(["game_id", "team", "st"]).v.sum()
    for c in range(N_TYPE):
        f[f"type{c}"] = x.assign(v=(x.type6 == c)).groupby(["game_id", "team", "st"]).v.sum()
    d = pd.concat([a, f], axis=1).fillna(0).reset_index()
    gt = r.groupby("game_id").game_type.first()
    d["game_type"] = d.game_id.map(gt)
    d["seed"] = 0
    return d


def g3_tables(S, A, nseed, rel_tol, mix_pp, min_n):
    """xG per unblocked attempt and tier shares by state; decomposition into state visits vs attribute mix."""
    rows, tiers = [], []
    agg = lambda d: d.groupby("st")[["att", "fen", "xg", "gl", "tier0", "tier1", "tier2"] + [f"type{c}" for c in range(N_TYPE)]].sum()  # noqa: E731
    sa, aa = agg(S), agg(A)
    for k in range(5):
        if k not in aa.index or aa.loc[k, "fen"] == 0:
            continue
        xs, xa = sa.loc[k, "xg"] / sa.loc[k, "fen"], aa.loc[k, "xg"] / aa.loc[k, "fen"]
        n = int(aa.loc[k, "fen"])
        rel = xs / xa - 1
        rows.append(dict(state=ST5[k], n_actual_unblocked=n, xg_sim=xs, xg_act=xa, rel=rel,
                         block_share_sim=1 - sa.loc[k, "fen"] / sa.loc[k, "att"], block_share_act=1 - aa.loc[k, "fen"] / aa.loc[k, "att"],
                         goals_per_fen_sim=sa.loc[k, "gl"] / sa.loc[k, "fen"], goals_per_fen_act=aa.loc[k, "gl"] / aa.loc[k, "fen"],
                         status="UNDERPOWERED" if n < min_n else ("PASS" if abs(rel) <= rel_tol else "FAIL")))
        for t_ in range(3):
            ps, pa = sa.loc[k, f"tier{t_}"] / sa.loc[k, "fen"] * 100, aa.loc[k, f"tier{t_}"] / aa.loc[k, "fen"] * 100
            tiers.append(dict(state=ST5[k], tier=TIER_NAMES[t_], n=n, sim_pct=ps, act_pct=pa, diff_pp=ps - pa,
                              status="UNDERPOWERED" if n < min_n else ("PASS" if abs(ps - pa) <= mix_pp else "FAIL")))
    T = pd.DataFrame(rows).set_index("state")
    xs_all, xa_all = sa.xg.sum() / sa.fen.sum(), aa.xg.sum() / aa.fen.sum()
    tot = pd.DataFrame([dict(state="all reachable", n_actual_unblocked=int(aa.fen.sum()), xg_sim=xs_all, xg_act=xa_all,
                             rel=xs_all / xa_all - 1, block_share_sim=1 - sa.fen.sum() / sa.att.sum(),
                             block_share_act=1 - aa.fen.sum() / aa.att.sum(), goals_per_fen_sim=sa.gl.sum() / sa.fen.sum(),
                             goals_per_fen_act=aa.gl.sum() / aa.fen.sum(),
                             status="PASS" if abs(xs_all / xa_all - 1) <= rel_tol else "FAIL")]).set_index("state")
    T = pd.concat([T, tot])
    for t_ in range(3):
        ps, pa = sa[f"tier{t_}"].sum() / sa.fen.sum() * 100, aa[f"tier{t_}"].sum() / aa.fen.sum() * 100
        tiers.append(dict(state="all reachable", tier=TIER_NAMES[t_], n=int(aa.fen.sum()), sim_pct=ps, act_pct=pa,
                          diff_pp=ps - pa, status="PASS" if abs(ps - pa) <= mix_pp else "FAIL"))
    ty = pd.DataFrame({"type": TYPE_NAMES, "sim_pct": [sa[f"type{c}"].sum() / sa.fen.sum() * 100 for c in range(N_TYPE)],
                       "act_pct": [aa[f"type{c}"].sum() / aa.fen.sum() * 100 for c in range(N_TYPE)]})
    ty["diff_pp"] = ty.sim_pct - ty.act_pct
    # decomposition of xG per unblocked attempt (all reachable): state visits x actual within-state xG + attribute mix
    ks = [k for k in range(5) if k in aa.index and aa.loc[k, "fen"] > 0]
    ws = np.array([sa.loc[k, "fen"] for k in ks]) / sa.fen.sum()
    wa = np.array([aa.loc[k, "fen"] for k in ks]) / aa.fen.sum()
    xs_k = np.array([sa.loc[k, "xg"] / max(sa.loc[k, "fen"], 1e-9) for k in ks])
    xa_k = np.array([aa.loc[k, "xg"] / aa.loc[k, "fen"] for k in ks])
    comp = {"state visits (sim - actual unblocked share by state) x actual xG": float(((ws - wa) * xa_k).sum()),
            "attribute mix within state (sim weights)": float((ws * (xs_k - xa_k)).sum())}
    tol = rel_tol * xa_all
    over = [(c, v) for c, v in comp.items() if abs(v) > tol]
    cf = any(any(np.sign(v2) == -np.sign(v) and v2 != 0 for c2, v2 in comp.items() if c2 != c) for c, v in over)
    verdict = "FAIL" if abs(xs_all - xa_all) > tol else ("COMPENSATED" if cf else "CLEAN")
    return T, pd.DataFrame(tiers).set_index(["state", "tier"]), ty, comp, xs_all - xa_all, tol, verdict


def per_team(S, A, ids_s, ids_a, min_n, rel_tol, mix_pp):
    def agg(d, ids, nseed):
        d = d.assign(team_id=ids)
        g = d.groupby("team_id")[["fen", "xg", "tier0", "tier1", "tier2"]].sum()
        g["n_per_seed"] = g.fen / nseed
        return g
    s = agg(S, ids_s, S.seed.nunique())
    a = agg(A, ids_a, 1)
    T = pd.DataFrame({"n_actual_unblocked": a.fen.astype(int), "xg_sim": s.xg / s.fen, "xg_act": a.xg / a.fen})
    T["rel"] = T.xg_sim / T.xg_act - 1
    for t_ in range(3):
        T[f"{TIER_NAMES[t_]}_diff_pp"] = (s[f"tier{t_}"] / s.fen - a[f"tier{t_}"] / a.fen) * 100
    T["status"] = "UNDERPOWERED (team-level, labelled)"
    T["would_pass_xg"] = T.rel.abs() <= rel_tol
    T["would_pass_tiers"] = (T[[f"{n}_diff_pp" for n in TIER_NAMES]].abs() <= mix_pp).all(axis=1)
    return T


def responsiveness(S, A, gid_s, gid_a):
    """Closed-loop ES xG per unblocked attempt by own ES shot-quality-for / opponent ES against rating quintile."""
    rows = pd.read_parquet(RES / "fold2_rows.parquet", columns=["game_id", "team", "own_rf_es", "opp_ra_es"])
    tg = rows.groupby(["game_id", "team"]).first()
    es = [0, 3, 4]
    s = S[S.st.isin(es)].groupby(["game_id", "team"])[["fen", "xg"]].sum()
    a = A[A.st.isin(es)].groupby(["game_id", "team"])[["fen", "xg"]].sum()
    j = tg.join(s.add_suffix("_s")).join(a.add_suffix("_a")).dropna().reset_index()
    games = np.sort(j.game_id.unique())
    gp = np.searchsorted(games, j.game_id.to_numpy())
    G = len(games)
    W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
    out = {}
    for c in ("own_rf_es", "opp_ra_es"):
        q = pd.qcut(j[c].rank(method="first"), 5, labels=False).to_numpy()
        Mx = {}
        for v in ("fen_s", "xg_s", "fen_a", "xg_a"):
            X = np.zeros((G, 5))
            np.add.at(X, (gp, q), j[v].to_numpy())
            Mx[v] = X

        def ratio(Wt):
            sm = (Wt @ Mx["xg_s"]) / (Wt @ Mx["fen_s"])
            am = (Wt @ Mx["xg_a"]) / (Wt @ Mx["fen_a"])
            return (sm[..., 4] - sm[..., 0]) / (am[..., 4] - am[..., 0]), sm, am
        rt, sm, am = ratio(np.ones(G))
        br, _, _ = ratio(W)
        lo, hi = np.percentile(br, [2.5, 97.5])
        out[c] = dict(ratio=float(rt), lo=float(lo), hi=float(hi), status="PASS" if 0.8 <= rt <= 1.2 else "FAIL",
                      sim_q=np.round(sm, 5).tolist(), act_q=np.round(am, 5).tolist())
    return out


def cmd_grade(a):
    out = Path("results") / a.tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    gt = load_games([TEST], columns=["game_id", "game_type", "home_id", "away_id"])
    s = s.merge(gt[["game_id", "game_type"]], on="game_id")
    nseed = s.seed.nunique()
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())
    rel, mix, min_n = float(tol["g3_xg_rel"]), float(tol["g3_mix_pp"]), int(tol["min_cell_n"])
    r, u = actual_frame()
    S = sim_long(s)
    A = act_long(r, u)
    gi = gt.set_index("game_id")
    L = [f"# G3 closed loop (SL-R3{', PLUMBING, not a gate' if a.arm == 'L0m' else ''}): {a.tag}, stage-4 arm {a.arm}, fold 2 (2024-25), {s.game_id.nunique()} games x {nseed} seeds", "",
         f"Generated {now()} by `scripts/run_shot_attribute_g3_v3.py`. Level E is applied in the engine from GameState.rec_era (era 2). Stage 1 = H3''-LC2 + T2; stage 3 = A3g-c; stage 4 = {a.arm} "
         "(rule (b): unblocked attempts only). Block = LABELLED STUB (empirical 2023-24 block share by group); goals = "
         "LABELLED STUB (xG_ref draw per sampled cell x type x group). No goalie pull (EN UNREACHABLE; the actual side "
         "is restricted to the reachable states 5v5 / PP / PK / 4v4 / 3v3), shootout skipped. Tolerances g3_xg_rel "
         f"{rel}, g3_mix_pp {mix}; cells with n < {min_n} actual unblocked attempts UNDERPOWERED.", ""]
    summ = {}
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        Ss = S if f is None else S[S.game_type == f]
        Aa = A if f is None else A[A.game_type == f]
        T, TT, TY, comp, tot, tl, verdict = g3_tables(Ss, Aa, nseed, rel, mix, min_n)
        L += [f"## {nm}", "", "### xG_ref per unblocked attempt by team-view state", "", T.to_markdown(floatfmt=".4f"), "",
              "### Location tier shares (%)", "", TT.to_markdown(floatfmt=".3f"), "",
              "### Type shares (%), reported", "", TY.set_index("type").to_markdown(floatfmt=".3f"), "",
              f"### Decomposition of xG per unblocked attempt (sim - actual {tot:+.5f}; tolerance {tl:.5f})", "",
              pd.Series(comp, name="xG per attempt").to_frame().to_markdown(floatfmt="+.5f"), "",
              f"- **Verdict ({nm}): {verdict}**", ""]
        summ[nm] = dict(states=T.reset_index().to_dict("records"), tiers=TT.reset_index().to_dict("records"),
                        types=TY.to_dict("records"), decomposition=comp, verdict=verdict)
    ids_s = np.where(S.team == 0, gi.home_id.reindex(S.game_id).to_numpy(), gi.away_id.reindex(S.game_id).to_numpy())
    ids_a = np.where(A.team == 0, gi.home_id.reindex(A.game_id).to_numpy(), gi.away_id.reindex(A.game_id).to_numpy())
    PT = per_team(S, A, ids_s, ids_a, min_n, rel, mix)
    rp = responsiveness(S, A, None, None)
    L += ["## Closed-loop responsiveness (ES xG_ref per unblocked attempt, team-game quintiles; band [0.8, 1.2])", ""]
    for c, v in rp.items():
        L += [f"- by {c}: spread ratio {v['ratio']:.3f} (95% CI {v['lo']:.3f}..{v['hi']:.3f}) **{v['status']}**; "
              f"sim {v['sim_q']} vs actual {v['act_q']}"]
    L += ["", f"## Per team (UNDERPOWERED, labelled; corr of xG per attempt sim vs actual {np.corrcoef(PT.xg_sim, PT.xg_act)[0, 1]:.2f}; "
          f"{int(PT.would_pass_xg.sum())}/{len(PT)} within 3%, {int(PT.would_pass_tiers.sum())}/{len(PT)} tiers within 1.5 pp)", "",
          PT.to_markdown(floatfmt=".4f"), ""]
    gl = s[["home_goals", "away_goals"]].sum(axis=1).mean()
    ga = A.gl.sum() / A.game_id.nunique()
    gen = u[u.st > 4].is_goal.sum() / A.game_id.nunique()
    L += [f"## Goals (reported, not gated; stub goal model): sim goals per game ex-shootout {gl:.3f}; actual goals "
          f"per game in reachable states {ga:.3f} (+ {gen:.3f} in EN states, unreachable in the sim)", ""]
    rep = Path(f"docs/tests/gates_g3_sl_r3_{a.arm}_2026-10-16.md")
    rep.write_text("\n".join(L) + "\n", encoding="utf-8")
    summ["responsiveness"] = rp
    summ["per_team"] = dict(n_within_xg=int(PT.would_pass_xg.sum()), n_within_tiers=int(PT.would_pass_tiers.sum()), n=len(PT),
                            corr=float(np.corrcoef(PT.xg_sim, PT.xg_act)[0, 1]))
    summ["sim_goals_per_game"] = float(gl)
    (out / "g3_summary.json").write_text(json.dumps(summ, indent=1, default=float))
    print(now(), "wrote", rep, flush=True)
    # G2 re-check through the stage-3 grader (same code path as INV-36)
    G2 = g2mod()
    ns = argparse.Namespace(arm="A3g-c", tag=a.tag, round="SA-R3", stage1="lc2t2",
                            report=f"docs/tests/gates_g2_sl_r3_{a.arm}_2026-10-16.md")
    G2.cmd_grade(ns)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["table", "sim", "grade"])
    ap.add_argument("--arm", required=True)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    a.tag = a.tag or f"sl_r3_g3_{a.arm}"
    {"table": cmd_table, "sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
