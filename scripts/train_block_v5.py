"""SB-R5 trainer: block ratings (Ra) with the as-of response scale and the AS-1 floor (docs/models/block/experiments.md SB-R5;
D43, INV-53, INV-62, INV-64; src/nhl_sim/block/scale.py).

Frozen (read, never refit): the Ra ratings (b 1,000, w 0.7), level M1 K500, the fold's SB-R4 B1a fit (non-rating terms W:
score dummies, home, b2b own / opp, arena factor), the SB-R1 B0 coefficients. B0' (comparator) = the engine stand-in (D41 /
INV-54): SB-R1 B0 on 5v5 / PP / PK / EN, own M1 K500 level group + one intercept (fitted on the fold's training rows) for
4v4 and for 3v3. B1a-as = logit B0' + (x - x_bar) . W + s_for,t zf + s_against,t za.

    train_block_v5.py snap      per fold, as-of snapshots for H {45, 90, 180, 365} x P {2000, 10000} with the AS-1 floor
                                (f 0.5) -> data/processed/block/block_scale_v1_f{fold}.parquet (fold 2: training dates only)
    train_block_v5.py parity    step 0 + parity analogue (training seasons only), (H, P) selection
                                -> results/block_sb_r5/select.json, docs/tests/block_sb_r5_parity_2026-10-21.md
    train_block_v5.py checks    in-sample share (fold-2 training rows, judged seasons) and the D28-form guard (fold 1);
                                fold-1 hash-labelled predictions; exits 3 / 4 on a failure
    train_block_v5.py pred2     only after checks passed: fold-2 snapshot extended to 2024-25 (training dates asserted
                                bit-identical), hash-labelled 2024-25 predictions (graded blind by grade_block_v5.py)
Arms: B0p (B0'), B1aas (B1a-as), B1aas2 (spec-identical rerun: the selected cell's snapshot from a within-day shuffled row
order), references B0 (SB-R1, original) and B1a (SB-R4 fixed scale; must reproduce the SB-R4 prediction).
"""
import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import train_block_v4 as V4  # noqa: E402
from nhl_sim.block import data as D  # noqa: E402
from nhl_sim.block import models as BM  # noqa: E402
from nhl_sim.block import scale as SC  # noqa: E402
from nhl_sim.block.data import logit, sigmoid  # noqa: E402
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402

RES = ROOT / "results/block_sb_r5"
R1 = ROOT / "results/block_sb_r1"
R4 = ROOT / "results/block_sb_r4"
SELECT = RES / "select.json"
PARITY_DOC = ROOT / "docs/tests/block_sb_r5_parity_2026-10-21.md"
SALT = "SB-R5-2026-10-21"
ARMS = ("B0p", "B0", "B1a", "B1aas", "B1aas2")
F = V4.F
FIRST = 20212022
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
LEVEL = "M1_K500"
BAND_P = (0.9, 1.1)
TOL_PP = 0.5
N_MIN = 2000
OWN_ST = {3: "4v4", 4: "3v3"}
COMMON = V4.COMMON
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def snap_path(fold):
    return D.OUT / f"block_scale_v1_f{fold}.parquet"


def mdir(fold):
    return "models" if fold == 2 else "fold1/models"


# ------------------------------------------------------------------------------------------------ data
def _state_level(a, gtab, st):
    """M1 K500 as-of league block share on one team-view state's rows (the engine's INV-54 code path)."""
    from nhl_sim.engine.c1s_tables import _state_level as f
    return f(a, gtab, st)


def fold_data(fold, test):
    """Rows of the fold (training seasons; + the test season if `test`), level offsets, B0', frozen W, units, offsets.
    Fold 2 without `test` never loads a 2024-25 row."""
    key = (fold, test)
    if key in _CACHE:
        return _CACHE[key]
    tr_s, te_s = F[fold]
    seasons = tr_s + ([te_s] if test else [])
    a = D.load_attempts(seasons)
    games = pd.read_parquet(D.OUT / "games_v1.parquet")
    rt = pd.read_parquet(D.OUT / "ratings_r4_Ra.parquet")
    af = pd.read_parquet(D.OUT / "arena_v1.parquet")
    r = D.assemble(a, games, rt, af, 0.7, 1000)
    r = pd.concat([r[r.season.isin(tr_s)], r[r.season == te_s]], ignore_index=True)
    ntr = int(r.season.isin(tr_s).sum())
    tr = r.iloc[:ntr]
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == LEVEL]
    s_train = D.share_table(tr)
    off = D.row_offset(r, L, s_train)
    # ---- B0 (SB-R1, frozen) and B0' (INV-54 groups), both from the stored / engine construction
    b0 = json.loads((R1 / mdir(fold) / "B0.json").read_text())
    p_b0 = BM.predict_b0(b0, r, off)
    p_b0p = p_b0.copy()
    aa = a[a.game_id.isin(games.game_id)]
    groups = {}
    for st, nm in OWN_ST.items():
        lev = _state_level(aa, games, st)
        x = tr[tr.st == st]
        s_tr = float(x.blocked.mean())
        o = logit(lev.reindex(x.game_id.to_numpy()).to_numpy()) - logit(s_tr)
        w, nit = BM.fit_logit_offset(np.ones((len(x), 1)), x.blocked.to_numpy(), o, n_free=1)
        k = (r.st == st).to_numpy()
        lv = lev.reindex(r.game_id.to_numpy()[k]).to_numpy()
        if np.isnan(lv).any():
            raise ValueError(f"rows without a {nm} level")
        p_b0p[k] = sigmoid(w[0] + logit(lv) - logit(s_tr))
        groups[nm] = dict(coef=float(w[0]), s_train=s_tr, n_train=int(len(x)))
    # ---- frozen SB-R4 B1a (fold) non-rating terms, centred at the fold's training mean
    b1a = json.loads((R4 / mdir(fold) / "B1a.json").read_text())
    Xn = V4.design_nr(r)[:, BM.N_L0:]
    W = np.asarray(b1a["coef"])[BM.N_L0:]
    xbar = Xn[:ntr].mean(0)
    A = logit(p_b0p) + (Xn - xbar) @ W
    ins = (r.season == FIRST).to_numpy()
    sd = (float(r.own_r[ins].std()), float(r.opp_r[ins].std()))
    r["drop"] = pd.read_parquet(D.OUT / "games_v1.parquet", columns=["game_id", "drop"]).set_index("game_id") \
        ["drop"].reindex(r.game_id.to_numpy()).to_numpy()
    if r["drop"].isna().any():
        raise ValueError("rows without a puck drop")
    zf, za = r.own_r.to_numpy(float) / sd[0], r.opp_r.to_numpy(float) / sd[1]
    out = dict(r=r, ntr=ntr, off=off, p_b0=p_b0, p_b0p=p_b0p, groups=groups, b1a=b1a, W=W, xbar=xbar, A=A, sd=sd,
               zf=zf, za=za, iref=SC.info_ref(A[ins], zf[ins], za[ins]), tr_s=tr_s, te_s=te_s, test=test)
    _CACHE[key] = out
    return out


def p_as(Dd, sf, sa):
    return sigmoid(Dd["A"] + sf * Dd["zf"] + sa * Dd["za"])


def floor_of(Dd):
    return (SC.F_FLOOR, Dd["iref"])


def _cell(args):
    date, drop, A, y, zf, za, H, P, fl = args
    t0 = time.time()
    f = SC.asof_scale(date, drop, A, y, zf, za, H, P, floor=fl)
    f.insert(0, "cell", SC.skey(H, P))
    f.insert(1, "H", H)
    f.insert(2, "P", P)
    return f, round(time.time() - t0, 1)


def build_snap(fold, test, procs):
    Dd = fold_data(fold, test)
    with ProcessPoolExecutor(procs) as ex:
        r = Dd["r"]
        arr = (r.date.to_numpy(), r["drop"].to_numpy(), Dd["A"], r.y.to_numpy(float), Dd["zf"], Dd["za"])
        res = list(ex.map(_cell, [arr + (H, P, floor_of(Dd)) for H, P in SC.GRID_ORDER]))
    Fr = pd.concat([x[0] for x in res], ignore_index=True)
    secs = {SC.skey(H, P): x[1] for (H, P), x in zip(SC.GRID_ORDER, res)}
    Fr["sd_for"], Fr["sd_against"] = Dd["sd"]
    Fr["floor_f"] = SC.F_FLOOR
    smap = dict(zip(pd.to_datetime(Dd["r"].date).to_numpy("datetime64[D]"), Dd["r"].season))
    Fr["season"] = [smap[d] for d in pd.to_datetime(Fr.date).to_numpy("datetime64[D]")]
    return Fr, secs


# ------------------------------------------------------------------------------------------------ step 1: snapshots
def cmd_snap(a):
    RES.mkdir(parents=True, exist_ok=True)
    info = {}
    for fold in (1, 2):
        t0 = time.time()
        test = fold == 1                       # fold 1's test season (2023-24) is a fold-2 training season
        Dd = fold_data(fold, test)
        print(now(), f"fold {fold}: {len(Dd['r']):,} rows, sd {Dd['sd']}, I_ref {Dd['iref'].tolist()}, "
              f"groups {Dd['groups']}, inputs {time.time() - t0:.0f} s", flush=True)
        Fr, secs = build_snap(fold, test, a.procs)
        assert not (fold == 2 and (Fr.season == F[2][1]).any())
        Fr.to_parquet(snap_path(fold), index=False)
        info[fold] = dict(n_rows=len(Dd["r"]), n_dates=int(Fr.date.nunique()), sd=Dd["sd"], iref=Dd["iref"].tolist(),
                          groups=Dd["groups"], secs=secs, elapsed=round(time.time() - t0),
                          seasons=sorted(int(s) for s in Fr.season.unique()))
        print(now(), f"fold {fold} written {snap_path(fold)} {secs}", flush=True)
    (RES / "snap_info.json").write_text(json.dumps(info, indent=1, default=float))


# ------------------------------------------------------------------------------------------------ step 0 + parity
def es_R(r, p, n_boot=200):
    es = (r.grp == 0).to_numpy()
    x = r[es]
    out = {}
    for nm, col in (("for", "own_rf_es"), ("against", "opp_ra_es")):
        q = slope_ratio(p[es], x.y.to_numpy(float), x[col].to_numpy(float), np.ones(es.sum()), x.game_id.to_numpy(),
                        n_buckets=10, n_boot=n_boot)
        out[nm] = dict(R=q["R"], ci=q["ci"])
    return out


def cmd_parity(a):
    t0 = time.time()
    rows, traj, mle = [], [], []
    for fold in (1, 2):
        Dd = fold_data(fold, fold == 1)
        r, ntr = Dd["r"], Dd["ntr"]
        tr = r.iloc[:ntr].reset_index(drop=True)
        assert set(tr.season.unique()) == set(Dd["tr_s"])
        Fs = pd.read_parquet(snap_path(fold))
        Ft = Fs[Fs.season.isin(Dd["tr_s"])]
        A, zf, za, y = Dd["A"][:ntr], Dd["zf"][:ntr], Dd["za"][:ntr], tr.y.to_numpy(float)
        p_b1a = V4.predict_fixed(Dd["b1a"], tr, Dd["off"][:ntr])
        for s in Dd["tr_s"]:
            k = (tr.season == s).to_numpy()
            sm = SC.fit_once(A[k], y[k], zf[k], za[k])
            mle.append(dict(fold=fold, season=s, s_for_raw=sm[0] / Dd["sd"][0], s_against_raw=sm[1] / Dd["sd"][1]))
            if s not in JUDGED[fold]:
                continue
            xk = tr[k].reset_index(drop=True)
            q = es_R(xk, p_b1a[k])
            rows.append(dict(fold=fold, season=s, arm="B1a fixed (SB-R4)", cell="s 1.0 x fold-1 c",
                             R_for=q["for"]["R"], for_ci=q["for"]["ci"], R_against=q["against"]["R"], against_ci=q["against"]["ci"]))
            q = es_R(xk, sigmoid(A[k] + sm[0] * zf[k] + sm[1] * za[k]))
            rows.append(dict(fold=fold, season=s, arm="season-own MLE (post-hoc diagnostic)", cell="-",
                             R_for=q["for"]["R"], for_ci=q["for"]["ci"], R_against=q["against"]["R"], against_ci=q["against"]["ci"]))
        for H, P in SC.GRID_ORDER:
            cell = SC.skey(H, P)
            sc = Ft[Ft.cell == cell]
            sf, sa = SC.attach_scale(tr.date.to_numpy(), sc)
            pa = sigmoid(A + sf * zf + sa * za)
            for s in JUDGED[fold]:
                k = (tr.season == s).to_numpy()
                q = es_R(tr[k].reset_index(drop=True), pa[k])
                rows.append(dict(fold=fold, season=s, arm="B1a-as", cell=cell, H=H, P=P, R_for=q["for"]["R"],
                                 for_ci=q["for"]["ci"], R_against=q["against"]["R"], against_ci=q["against"]["ci"]))
            for s, g in sc.groupby("season"):
                rec = dict(fold=fold, cell=cell, season=s)
                for d_, col, u in (("for", "s_for", Dd["sd"][0]), ("against", "s_against", Dd["sd"][1])):
                    v = g[col].to_numpy() / u
                    rec.update({f"{d_}_first": v[0], f"{d_}_mid": v[len(v) // 2], f"{d_}_last": v[-1],
                                f"{d_}_min": v.min(), f"{d_}_max": v.max()})
                rec["floor_dates"] = int(g.floor_binds.sum())
                rec["n_eff_last"] = float(g.n_eff.iloc[-1])
                traj.append(rec)
            print(now(), f"fold {fold} {cell} done", flush=True)
    T = pd.DataFrame(rows)
    T["max_abs_logR"] = np.maximum(np.abs(np.log(T.R_for)), np.abs(np.log(T.R_against)))
    T["both_in"] = T.R_for.between(*BAND_P) & T.R_against.between(*BAND_P)
    A_ = T[T.arm == "B1a-as"]
    cs = A_.groupby("cell").agg(H=("H", "first"), P=("P", "first"), max_abs_logR=("max_abs_logR", "max"),
                                all_in=("both_in", "all"), R_for_min=("R_for", "min"), R_for_max=("R_for", "max"),
                                R_against_min=("R_against", "min"), R_against_max=("R_against", "max"))
    cs = cs.loc[[SC.skey(H, P) for H, P in SC.GRID_ORDER]]
    passers = [c for c in cs.index if cs.loc[c, "all_in"]]
    if passers:
        sel, how = passers[0], "simplest passer (larger H, then larger P)"
    else:
        sel, how = cs.max_abs_logR.idxmin(), ("no passer: smallest max |log R| over both directions and all judged "
                                              "seasons (listed), proceed")
    H, P = int(cs.loc[sel, "H"]), int(cs.loc[sel, "P"])
    J, Mx = pd.DataFrame(traj), pd.DataFrame(mle)
    out = dict(selected=sel, H=H, P=P, rule=how, passers=passers, table=T.to_dict("records"),
               summary=cs.reset_index().to_dict("records"), trajectory=J.to_dict("records"), season_mle=Mx.to_dict("records"),
               generated=now(), elapsed_s=round(time.time() - t0))
    SELECT.write_text(json.dumps(out, indent=1, default=float))
    s0 = json.loads((R4 / "step0.json").read_text())
    ra = [c for c in s0["coef"] if c["construction"] == "Ra"]
    fl = [f for f in s0["flat"] if f["construction"] == "Ra"]
    info = json.loads((RES / "snap_info.json").read_text())

    def fci(v):
        return f"{v[0]:.2f}-{v[1]:.2f}"
    Ts = T.assign(for_ci=T.for_ci.map(fci), against_ci=T.against_ci.map(fci))[
        ["fold", "season", "arm", "cell", "R_for", "for_ci", "R_against", "against_ci", "max_abs_logR", "both_in"]]
    Lx = ["# SB-R5 step 0 and parity analogue, (H, P) selection (Lane B5, 2026-10-21)", "",
          f"Generated {now()} ({time.time() - t0:.0f} s) by `scripts/train_block_v5.py parity`. Committed BEFORE any fold-2 "
          "prediction. Training seasons only (fold 1: 2021-22, 2022-23 (+ its 2023-24 test dates in the snapshot); fold 2: "
          "2021-22 to 2023-24). No 2024-25 row, prediction or s_t value has been computed or read.", "",
          "## Construction (spec SB-R5; code `src/nhl_sim/block/scale.py`, tests `tests/test_block_asof_scale.py`)", "",
          "- B1a-as: logit p = logit B0' + (x - x_bar) . W + s_for,t zf + s_against,t za, on every row (SB-R1 scope, EN rows "
          "included as in the SB-R4 B1a fit). B0' is the engine stand-in (SB-R1 B0 on 5v5 / PP / PK / EN; own M1 K500 level "
          "group and intercept for 4v4 and 3v3, fitted on the fold's training rows by the engine's INV-54 code). W is the "
          "fold's FROZEN SB-R4 B1a non-rating terms (6 score dummies, home, b2b own / opp, arena factor), centred at their "
          "mean over the fold's training rows (the SL-R7 template's (x - x_bar) . W; B1a's own intercepts are replaced by B0').",
          "- zf = own_r / SD, za = opp_r / SD (Ra ratings of the row's rating group: shooting team's blocked-against, "
          "defending team's blocks-for); SD over the fold's 2021-22 rows: " + "; ".join(
              f"fold {f_} {info[str(f_)]['sd'][0]:.5f} / {info[str(f_)]['sd'][1]:.5f}" for f_ in (1, 2)) + ".",
          "- The pair: two-slope binary logistic on every attempt dated before the game date, weights 0.5^(age/H), offset "
          "fixed; shrunk to the previous date's pair with prior precision P x Ibar (the per-attempt Fisher information at "
          f"the current iterate), with the AS-1 floor f = {SC.F_FLOOR} (P x (Ibar + f I_ref) while lambda_min(Ibar) < "
          "f lambda_min(I_ref); I_ref = Ibar at s = 0 over the fold's 2021-22 rows); the SL-R7 Newton solver. Start (0, 0); "
          "2021-22 burn-in; created_at = previous date's last drop + 6 h, asserted < puck_drop.",
          "- INV-54 groups (fold-fitted intercepts): " + "; ".join(
              f"fold {f_} " + ", ".join(f"{k} {v['coef']:+.4f} (n {v['n_train']:,})" for k, v in info[str(f_)]["groups"].items())
              for f_ in (1, 2)) + ".",
          "- Parity R: D32 decile slope ratio on ES rows of that training season, deciles of the shooting team's ES Ra "
          "rating (for) / the defending team's (against); CI = 200-resample game bootstrap. W and B0' are fitted on the "
          "fold's training rows (in sample, as in SL-R7 / G-R3); the slope pair is as-of, so R is out of sample for the scale.", "",
          "## Step 0: the trend the as-of pair must track", "",
          "SB-R4 step-0 Ra coefficients (B1-style fits, raw rating units, cluster SEs; `results/block_sb_r4/step0.json`):", "",
          "| rating | fit | coef | SE |", "|---|---|---|---|"]
    for c in ra:
        if c["feature"] in ("own_r", "opp_r"):
            Lx.append(f"| {'for (own_r)' if c['feature'] == 'own_r' else 'against (opp_r)'} | {c['fit']} | {c['coef']:.3f} | "
                      f"{c['se_cluster']:.3f} |")
    Lx += ["", "Trend per season: " + "; ".join(f"{'for' if f_['feature'] == 'own_r' else 'against'} "
                                                f"{f_['trend_per_season']:+.3f} (z {f_['trend_z']:+.2f})" for f_ in fl) + ".", "",
           "Season-alone MLE of the pair under the B1a-as offset (P = 0; raw units = z units / SD):", "",
           Mx.to_markdown(index=False, floatfmt=".4f"), "",
           "As-of pair over training dates, per cell and season (raw units; first / mid / last game date of the season, min / "
           "max; floor_dates = dates where the AS-1 floor binds; n_eff = summed window weight on the last date):", "",
           J.to_markdown(index=False, floatfmt=".4f"), "",
           "## Parity analogue (judged training seasons; band [0.9, 1.1] on both R)", "",
           Ts.to_markdown(index=False, floatfmt=".4f"), "",
           "Per cell (B1a-as, all three judged season cells, both directions):", "",
           cs.to_markdown(floatfmt=".4f"), "",
           f"- **Selected: {sel} (H {H}, P {P})**: {how}. Passers: {passers or 'none'}.",
           "- The season-own-MLE rows are a post-hoc diagnostic (in sample), used for no choice.", ""]
    PARITY_DOC.write_text("\n".join(Lx), encoding="utf-8")
    print(Ts.to_string(), flush=True)
    print(cs.to_string(), flush=True)
    print(now(), "selected", sel, how, flush=True)


# ------------------------------------------------------------------------------------------------ predictions
def selected():
    return json.loads(SELECT.read_text())


def shuffled_snapshot(Dd, H, P):
    r = Dd["r"]
    p = np.random.default_rng(2).permutation(len(r))
    return SC.asof_scale(r.date.to_numpy()[p], r["drop"].to_numpy()[p], Dd["A"][p], r.y.to_numpy(float)[p],
                         Dd["zf"][p], Dd["za"][p], H, P, floor=floor_of(Dd))


def arm_preds(Dd, Fs, part, rerun=False):
    """Every arm on the training ('train') or test ('test') rows of the fold."""
    S = selected()
    r, ntr = Dd["r"], Dd["ntr"]
    sl = slice(0, ntr) if part == "train" else slice(ntr, len(r))
    x = r.iloc[sl].reset_index(drop=True)
    sf, sa = SC.attach_scale(x.date.to_numpy(), Fs[Fs.cell == S["selected"]])
    out = {"B0p": Dd["p_b0p"][sl], "B0": Dd["p_b0"][sl], "B1a": V4.predict_fixed(Dd["b1a"], x, Dd["off"][sl]),
           "B1aas": sigmoid(Dd["A"][sl] + sf * Dd["zf"][sl] + sa * Dd["za"][sl])}
    info = {}
    if rerun:
        F2 = shuffled_snapshot(Dd, S["H"], S["P"])
        sf2, sa2 = SC.attach_scale(x.date.to_numpy(), F2)
        out["B1aas2"] = sigmoid(Dd["A"][sl] + sf2 * Dd["zf"][sl] + sa2 * Dd["za"][sl])
        info["snap_shuffle_max_abs"] = float(max(np.abs(sf2 - sf).max(), np.abs(sa2 - sa).max()))
    return x, out, info


def share_table_cmp(x, P, a, b, scope_mask=None):
    rows = []
    m0 = np.ones(len(x), bool) if scope_mask is None else scope_mask
    cells = [("overall ES+PP+PK", (x.grp <= 2).to_numpy())]
    cells += [(f"group {['ES', 'PP', 'PK'][g]}", (x.grp == g).to_numpy()) for g in range(3)]
    cells += [(f"group {['ES', 'PP', 'PK'][g]} {'OT' if pt else 'reg'}", ((x.grp == g) & (x.ptype == pt)).to_numpy())
              for g in range(3) for pt in (0, 1)]
    names = ("5v5", "PP", "PK", "4v4", "3v3", "ENF", "ENA")
    cells += [(f"state {names[s]} (reported)", (x.st == s).to_numpy()) for s in range(7)]
    for nm, m in cells:
        m = m & m0
        n = int(m.sum())
        if n == 0:
            continue
        rows.append(dict(cell=nm, n=n, actual_pct=100 * x.y.to_numpy()[m].mean(), **{f"{k}_pct": 100 * P[k][m].mean() for k in (a, b)},
                         diff_pp=100 * (P[a][m].mean() - P[b][m].mean())))
    return pd.DataFrame(rows)


def write_preds(fold, Dd, Fs):
    out = RES if fold == 2 else RES / "fold1"
    out.mkdir(parents=True, exist_ok=True)
    x, P, info = arm_preds(Dd, Fs, "test", rerun=True)
    # reference reproduction: B0 = SB-R1 / SB-R4 B0 file, B1a = SB-R4 B1a file (float32 storage)
    d4 = R4 if fold == 2 else R4 / "fold1"
    lab4 = json.loads((d4 / "labels_sealed.json").read_text())
    rows4 = pd.read_parquet(d4 / f"fold{fold}_rows.parquet", columns=["game_id", "t"])
    assert (rows4.game_id.to_numpy() == x.game_id.to_numpy()).all() and (rows4.t.to_numpy() == x.t.to_numpy()).all()
    for arm in ("B0", "B1a"):
        ref = np.load(d4 / f"fold{fold}_pred_{lab4[arm]}.npy")
        info[f"{arm}_vs_sb_r4_max_abs"] = float(np.abs(P[arm].astype(np.float32) - ref).max())
    rows = x.assign(off=Dd["off"][Dd["ntr"]:])[COMMON].copy()
    for col in ("own_r", "opp_r", "own_rf_es", "opp_ra_es"):
        rows[f"{col}_Ra"] = x[col].to_numpy()
    rows.to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for arm in ARMS:
        p = np.asarray(P[arm], np.float64)
        if p.shape != (len(x),) or not np.isfinite(p).all():
            raise ValueError(f"{arm}: bad probabilities")
        np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p)
    (out / "labels_sealed.json").write_text(json.dumps({a_: label(a_) for a_ in ARMS}))
    (out / "pred_info.json").write_text(json.dumps(info, indent=1))
    return x, P, info


def cmd_checks(a):
    """In-sample (fold-2 training rows; judged seasons gate, all rows reported) and the D28-form guard (fold 1, 2023-24)."""
    res = {}
    D2 = fold_data(2, False)
    F2s = pd.read_parquet(snap_path(2))
    assert not (F2s.season == F[2][1]).any()
    x, P, _ = arm_preds(D2, F2s, "train")
    judged = (x.season != FIRST).to_numpy()
    T_j = share_table_cmp(x, P, "B1aas", "B0p", judged)
    T_a = share_table_cmp(x, P, "B1aas", "B0p")
    gate = T_j[T_j.cell.str.startswith(("overall", "group")) & (T_j.n >= N_MIN)]
    ok_in = bool((gate.diff_pp.abs() <= TOL_PP).all())
    allcells = T_j[T_j.cell.str.startswith(("overall", "group"))]
    res["insample"] = dict(rule=f"B1a-as minus B0' mean predicted block share within +/-{TOL_PP} pp, by strength group x "
                                "period type (and group, overall), fold-2 judged training seasons 2022-23 + 2023-24, "
                                f"cells with n >= {N_MIN} gate", pass_=ok_in,
                           all_group_cells_within=bool((allcells.diff_pp.abs() <= TOL_PP).all()),
                           judged=T_j.to_dict("records"), all_rows=T_a.to_dict("records"))
    print(T_j.to_string(), flush=True)
    print(now(), "in-sample", "PASS" if ok_in else "FAIL", flush=True)
    # D28-form guard on fold 1 (test 2023-24)
    D1 = fold_data(1, True)
    F1s = pd.read_parquet(snap_path(1))
    x1, P1, info1 = write_preds(1, D1, F1s)
    T_g = share_table_cmp(x1, P1, "B1aas", "B0p")
    gg = T_g[T_g.cell.str.startswith("overall") | T_g.cell.isin(["group ES", "group PP", "group PK"])]
    ok_g = bool((gg.diff_pp.abs() <= TOL_PP).all())
    res["guard"] = dict(rule=f"fold 1 (2023-24): B1a-as minus B0' block share within +/-{TOL_PP} pp overall and by "
                             "strength group", pass_=ok_g, table=T_g.to_dict("records"), pred_info=info1)
    print(T_g.to_string(), flush=True)
    print(now(), "guard", "PASS" if ok_g else "FAIL", info1, flush=True)
    (RES / "checks.json").write_text(json.dumps(res, indent=1, default=float))
    if not ok_in:
        raise SystemExit(3)
    if not ok_g:
        raise SystemExit(4)


def cmd_pred2(a):
    ck = json.loads((RES / "checks.json").read_text())
    assert ck["insample"]["pass_"] and ck["guard"]["pass_"], "checks not passed"
    S = selected()
    old = pd.read_parquet(snap_path(2))
    Dd = fold_data(2, True)
    Fr, secs = build_snap(2, True, a.procs)
    tr_dates = Fr.season != F[2][1]
    dev = {}
    for cell in Fr.cell.unique():
        n_ = Fr[(Fr.cell == cell) & tr_dates].reset_index(drop=True)
        o_ = old[old.cell == cell].reset_index(drop=True)
        assert len(n_) == len(o_) and (n_.date.to_numpy() == o_.date.to_numpy()).all(), cell
        d = np.abs(n_[["s_for", "s_against"]].to_numpy() - o_[["s_for", "s_against"]].to_numpy())
        dev[cell] = dict(max_abs=float(d.max()), n_dates_differing=int((d.max(1) > 0).sum()))
    # the training-date inputs are identical (checked); a longer row array changes BLAS summation blocking, so the
    # training-date pairs agree to rounding, not bit-for-bit (labelled numerical fact; tolerance 1e-10)
    assert max(v["max_abs"] for v in dev.values()) < 1e-10, dev
    (RES / "pred2_snap_dev.json").write_text(json.dumps(dev, indent=1))
    Fr.to_parquet(snap_path(2), index=False)
    print(now(), "fold-2 snapshot extended to 2024-25; training dates vs step-1 snapshot", dev, secs, flush=True)
    x, P, info = write_preds(2, Dd, Fr)
    print(now(), "fold-2 predictions written", S["selected"], info, flush=True)


def cmd_freeze(a):
    """Frozen fold-2 serving parameters of the selected arm -> docs/models/block/sb_r5_frozen_params.json."""
    S = selected()
    Dd = fold_data(2, False)
    out = dict(arm="B1a-as", spec="SB-R5", cell=S["selected"], H=S["H"], P=S["P"], floor_f=SC.F_FLOOR,
               iref=Dd["iref"].tolist(), sd=list(Dd["sd"]), W=Dd["W"].tolist(), xbar=Dd["xbar"].tolist(),
               W_names=["sc0", "sc1", "sc2", "sc4", "sc5", "sc6", "is_home", "b2b_own", "b2b_opp", "arena_f"],
               groups=Dd["groups"], snapshot="data/processed/block/block_scale_v1_f2.parquet",
               b0="results/block_sb_r1/models/B0.json", b1a="results/block_sb_r4/models/B1a.json")
    (ROOT / "docs/models/block/sb_r5_frozen_params.json").write_text(json.dumps(out, indent=1))
    print(out, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snap", "parity", "checks", "pred2", "freeze"])
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"snap": cmd_snap, "parity": cmd_parity, "checks": cmd_checks, "pred2": cmd_pred2, "freeze": cmd_freeze}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
