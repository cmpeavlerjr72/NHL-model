"""Gate scaffolding (INV-17): sim-output contract, real-world gate targets, and the G1-G9 evaluator.

The same `summarize` function computes every game-level quantity for real finals and for sim output, so a
definition change cannot make the two sides disagree. See docs/ops/sim_output_schema.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from nhl_sim.data.seal import assert_not_sealed

TOTAL_K = list(range(0, 11))          # 0..9, 10 = "10+"
MARGIN_M = list(range(-5, 6))         # clipped at +-5
REQUIRED_COLS = ["game_id", "seed", "home_goals", "away_goals", "end_state", "home_win"]
OPT_COLS = ["home_en_goals", "away_en_goals"]
STATES = {"REG", "OT", "SO"}


# --------------------------------------------------------------------------- real finals
def real_games(season: int, version: str = "v2") -> pd.DataFrame:
    """Per-game real targets (goals exclude the shootout bonus goal) with EN goals from the events table."""
    from nhl_sim.data.load import load_events, load_verified_finals
    assert_not_sealed(season, "real_games")
    f = load_verified_finals(version, seasons=[season])
    so_h = ((f.end_state == "SO") & (f.home_score > f.away_score)).astype(int)
    so_a = ((f.end_state == "SO") & (f.away_score > f.home_score)).astype(int)
    out = pd.DataFrame({"game_id": f.game_id, "season": f.season, "game_type": f.game_type,
                        "game_date_local": f.game_date_local, "home": f.home, "away": f.away,
                        "home_goals": f.home_score - so_h, "away_goals": f.away_score - so_a,
                        "end_state": f.end_state, "home_win": f.home_score > f.away_score})
    ev = load_events([season], columns=["game_id", "event", "period_type", "goalie_id", "owner_is_home"])
    en = ev[(ev.event == "GOAL") & (ev.period_type != "SO") & ev.goalie_id.isna()]
    c = en.groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0)
    c = c.rename(columns={True: "home_en_goals", False: "away_en_goals"})
    out = out.merge(c.reset_index(), on="game_id", how="left")
    for col in OPT_COLS:
        out[col] = out.get(col, 0)
        out[col] = out[col].fillna(0).astype(int)
    return out


# --------------------------------------------------------------------------- summaries
def summarize(df: pd.DataFrame) -> dict[tuple[str, str, str], float]:
    """Game-level quantities for G5/G6/G7/G9 from a frame with the sim-output columns (real or sim, any n rows)."""
    h, a = df.home_goals.to_numpy(float), df.away_goals.to_numpy(float)
    tot, mar = h + a, h - a
    r: dict[tuple[str, str, str], float] = {}
    tk = np.minimum(tot, 10).astype(int)
    for k in TOTAL_K:
        r[("G5", "total_p", f"k={k}")] = float(np.mean(tk == k))
    mk = np.clip(mar, -5, 5).astype(int)
    for m in MARGIN_M:
        r[("G5", "margin_p", f"m={m}")] = float(np.mean(mk == m))
    r[("G5", "total_mean", "")] = float(tot.mean())
    r[("G5", "margin_mean", "")] = float(mar.mean())
    r[("G5", "total_sd", "")] = float(tot.std())
    r[("G5", "margin_sd", "")] = float(mar.std())
    r[("G5", "score_corr", "")] = float(np.corrcoef(h, a)[0, 1]) if h.std() > 0 and a.std() > 0 else float("nan")
    r[("G6", "home_win", "")] = float(df.home_win.mean())
    r[("G6", "goal_diff", "")] = float(mar.mean())
    es = df.end_state.to_numpy()
    r[("G7", "reg_tie_rate", "")] = float(np.mean(es != "REG"))
    r[("G7", "ot_rate", "")] = float(np.mean(es == "OT"))
    r[("G7", "so_rate", "")] = float(np.mean(es == "SO"))
    if all(c in df.columns for c in OPT_COLS) and not df[OPT_COLS].isna().any().any():
        r[("G7", "en_goals_per_game", "")] = float((df.home_en_goals + df.away_en_goals).mean())
    return r


SEGMENTS = {"all": lambda d: d, "RS": lambda d: d[d.game_type == 2], "PO": lambda d: d[d.game_type == 3]}


def targets_table(real: pd.DataFrame, season: int) -> pd.DataFrame:
    rows = []
    for seg, fn in SEGMENTS.items():
        d = fn(real)
        if len(d) == 0:
            continue
        for (g, m, k), v in summarize(d).items():
            rows.append(dict(season=season, segment=seg, gate=g, metric=m, key=k, value=v, n_games=len(d)))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- sim-output contract
def load_sim_output(results_dir: str | Path) -> tuple[pd.DataFrame, dict]:
    d = Path(results_dir)
    g = pd.read_parquet(d / "games.parquet")
    meta = json.loads((d / "run_meta.json").read_text()) if (d / "run_meta.json").exists() else {}
    miss = [c for c in REQUIRED_COLS if c not in g.columns]
    if miss:
        raise ValueError(f"sim output missing required columns {miss}")
    bad = ~g.end_state.isin(STATES)
    if bad.any():
        raise ValueError(f"unknown end_state values {sorted(g.end_state[bad].unique())}")
    so = g.end_state == "SO"
    if (g.home_goals[so] != g.away_goals[so]).any():
        raise ValueError("SO rows must have tied goals (goals exclude the shootout bonus goal)")
    nso = ~so
    if (g.home_win[nso] != (g.home_goals[nso] > g.away_goals[nso])).any() or \
       (g.home_goals[nso] == g.away_goals[nso]).any():
        raise ValueError("REG/OT rows need a goal winner consistent with home_win")
    if meta.get("sealed_touched"):
        raise ValueError("run_meta says sealed_touched=true; refusing to grade")
    return g, meta


# --------------------------------------------------------------------------- gate evaluation
def load_tolerances(path="docs/gates.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text())


def _chk(name, sim, real, tol, kind, n, min_n, extra=""):
    """kind: 'abs' (|sim-real|<=tol) or 'ratio' (tol=(lo,hi))."""
    if sim is None or (isinstance(sim, float) and np.isnan(sim)):
        return dict(check=name, sim=sim, real=real, tol=str(tol), status="NEEDS-INSTRUMENTATION", n=n, note=extra)
    if kind == "abs":
        ok = abs(sim - real) <= tol
        val = sim - real
    else:
        val = sim / real
        ok = tol[0] <= val <= tol[1]
    st = "UNDERPOWERED" if n < min_n else ("PASS" if ok else "FAIL")
    return dict(check=name, sim=sim, real=real, tol=str(tol), status=st, n=n, note=extra or f"stat={val:.4f}")


def _gate_status(checks):
    ss = [c["status"] for c in checks]
    if "FAIL" in ss:
        return "FAIL"
    if "NEEDS-INSTRUMENTATION" in ss:
        return "NEEDS-INSTRUMENTATION"
    if ss and all(s == "UNDERPOWERED" for s in ss):
        return "UNDERPOWERED"
    return "PASS"


def ks_total_p(sim_tot: np.ndarray, real_tot: np.ndarray) -> tuple[float, float]:
    """KS statistic between sim and real total-goal ECDFs; p uses effective n = n_real (sim is a model, not a sample)."""
    from scipy.stats import kstwo
    ks = np.arange(0, 40)
    d = float(np.max(np.abs(np.array([(sim_tot <= k).mean() - (real_tot <= k).mean() for k in ks]))))
    n = len(real_tot)
    return d, float(kstwo.sf(d, n))


def evaluate(sim: pd.DataFrame, real: pd.DataFrame, targets: pd.DataFrame, tol: dict, segment="all") -> dict:
    """Returns {gate: {status, checks}} for G1..G9 on one segment (default overall)."""
    mn = int(tol["min_cell_n"])
    t = targets[targets.segment == segment]
    n = int(t.n_games.iloc[0]) if len(t) else 0
    R = {(r.gate, r.metric, r.key): r.value for r in t.itertuples()}
    seg_real = SEGMENTS[segment](real)
    sim = sim[sim.game_id.isin(seg_real.game_id)]
    S = summarize(sim.merge(seg_real[["game_type"]].assign(game_id=seg_real.game_id), on="game_id", how="left"))
    out: dict = {}

    c5 = []
    for k in TOTAL_K:
        c5.append(_chk(f"P(total={k})", S[("G5", "total_p", f"k={k}")], R[("G5", "total_p", f"k={k}")],
                       tol["g5_total_cell_pp"] / 100, "abs", n, mn))
    for m, nm in (("total_sd", "total SD ratio"), ("margin_sd", "margin SD ratio")):
        c5.append(_chk(nm, S[("G5", m, "")], R[("G5", m, "")], (tol["g5_sd_ratio_lo"], tol["g5_sd_ratio_hi"]), "ratio", n, mn))
    c5.append(_chk("score correlation", S[("G5", "score_corr", "")], R[("G5", "score_corr", "")], tol["g5_corr"], "abs", n, mn))
    d, p = ks_total_p(np.minimum(sim.home_goals + sim.away_goals, 10).to_numpy(),
                      np.minimum(seg_real.home_goals + seg_real.away_goals, 10).to_numpy())
    c5.append(dict(check="KS total goals (p, n_eff=n_real)", sim=p, real=None, tol=f">={tol['g5_ks_p']}",
                   status="UNDERPOWERED" if n < mn else ("PASS" if p >= tol["g5_ks_p"] else "FAIL"), n=n, note=f"D={d:.4f}"))
    out["G5"] = c5
    out["G6"] = [
        _chk("home win %", S[("G6", "home_win", "")], R[("G6", "home_win", "")], tol["g6_win_pp"] / 100, "abs", n, mn),
        _chk("home goal diff", S[("G6", "goal_diff", "")], R[("G6", "goal_diff", "")], tol["g6_goal_diff"], "abs", n, mn)]
    out["G7"] = [
        _chk("regulation tie rate", S[("G7", "reg_tie_rate", "")], R[("G7", "reg_tie_rate", "")], tol["g7_reg_tie_pp"] / 100, "abs", n, mn),
        _chk("shootout rate", S[("G7", "so_rate", "")], R[("G7", "so_rate", "")], tol["g7_shootout_pp"] / 100, "abs", n, mn),
        _chk("EN goals / game", S.get(("G7", "en_goals_per_game", "")), R.get(("G7", "en_goals_per_game", "")), tol["g7_en_goals_per_game"], "abs", n, mn)]
    # G9 accuracy: biases vs targets, calibration slope of actual on per-game predicted mean
    pg = sim.groupby("game_id").agg(ph=("home_goals", "mean"), pa=("away_goals", "mean")).reset_index()
    j = pg.merge(seg_real[["game_id", "home_goals", "away_goals"]], on="game_id")
    pm, am = (j.ph - j.pa).to_numpy(), (j.home_goals - j.away_goals).to_numpy()
    pt, at = (j.ph + j.pa).to_numpy(), (j.home_goals + j.away_goals).to_numpy()
    c9 = [_chk("total bias", S[("G5", "total_mean", "")], R[("G5", "total_mean", "")], tol["g9_total_bias"], "abs", n, mn),
          _chk("margin bias", S[("G5", "margin_mean", "")], R[("G5", "margin_mean", "")], tol["g9_margin_bias"], "abs", n, mn)]
    for nm, x, y in (("margin slope (actual on pred)", pm, am), ("total slope (actual on pred)", pt, at)):
        sl = float(np.polyfit(x, y, 1)[0]) if x.std() > 1e-9 else float("nan")
        c9.append(_chk(nm, sl, 1.0, (tol["g9_slope_lo"], tol["g9_slope_hi"]), "ratio", n, mn,
                       "slope near 1 = calibrated spread; noisy at n~1400"))
    out["G9"] = c9
    for g in ("G1", "G2", "G3", "G4", "G8"):
        out[g] = [dict(check="needs event-level / player-level sim output", sim=None, real=None, tol="", status="NEEDS-INSTRUMENTATION", n=0, note="")]
    return {g: dict(status=_gate_status(c), checks=c) for g, c in sorted(out.items())}
