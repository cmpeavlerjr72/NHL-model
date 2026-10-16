"""SS-R3 / Lane H4 (INV-28) steps 3-4: D14 clean-pass decomposition of PP opportunities (sim minus actual) and the
closed-loop responsiveness table. Reads results/ss_r3_g1_<arm>/strength_toi.parquet (200 seeds) and the fold-2
offline rows + predictions of the same arm. Writes results/ss_r3_g1_decomp_<arm>.md and .json.

  PPO_x = f_x * E_x   (E = penalty-taking events per team-game incl. coincidental, f = PP opportunities per event)
  dPPO  = f_a (E_pred_reach - E_a_reach)            (a)  hazard level on reachable states, offline rows (actual path)
        + f_a (-E_a_other)                           (a') actual events in state 'other' (trailing-team pulls) that
                                                          the sim cannot visit (no goalie-pull model yet)
        + f_a sum_st (T_sim,st - T_act,st) lam_st    (b)  state-visit: time per strength state (hours per team-game,
                                                          team view) differences x offline mean predicted rate in st
        + f_a [(E_s - E_pred_reach) - (b)]           (d)  remainder of the sim-path event difference (score / penalty
                                                          differential / clock mix on the sim path)
        + (f_s - f_a) E_s                            (c)  PP opportunities per event: coincidental / type mix, stacked
                                                          (overlapping) penalties that start no new advantage
  an exact identity. Verdict: FAIL if the total is outside the gate tolerance; COMPENSATED if the total is inside it
  but some single component exceeds the tolerance in absolute value while an opposite-signed component exists to
  cancel it; CLEAN otherwise.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.eval import g1 as G1  # noqa: E402

R3 = Path("results/strength_state_r3")
TEST = 20242025
ST = ["5v5", "PP-for (incl 5v3)", "PK (incl 3v5)", "4v4", "3v3"]


def team_view(d):
    """per (game, seed) frame with game_type -> team-game arrays (home block then away block)."""
    h = np.stack([d.toi_5v5_s, d.toi_pp_home_s, d.toi_pp_away_s, d.toi_4v4_s, d.toi_3v3_s], 1) / 3600.0
    a = np.stack([d.toi_5v5_s, d.toi_pp_away_s, d.toi_pp_home_s, d.toi_4v4_s, d.toi_3v3_s], 1) / 3600.0
    return dict(T=np.vstack([h, a]), ppo=np.concatenate([d.ppo_home, d.ppo_away]).astype(float),
                pen=np.concatenate([d.pen_home, d.pen_away]).astype(float),
                gt=np.concatenate([d.game_type, d.game_type]))


def decompose(rows_seg, mu_seg, S, A, tol):
    ms, ma = S["sel"], A["sel"]
    ntg = ma.sum()
    stv = rows_seg.st.to_numpy()
    reach = stv <= 4
    expo_h = rows_seg.exposure_s.to_numpy() / 3600.0
    y = rows_seg.y.to_numpy()
    E_pred = mu_seg[reach].sum() / ntg
    E_ar = y[reach].sum() / ntg
    E_ao = y[~reach].sum() / ntg
    E_a = A["pen"][ma].mean()
    E_s = S["pen"][ms].mean()
    PPO_a, PPO_s = A["ppo"][ma].mean(), S["ppo"][ms].mean()
    f_a, f_s = PPO_a / E_a, PPO_s / E_s
    lam = np.array([mu_seg[reach & (stv == k)].sum() / max(1e-9, expo_h[reach & (stv == k)].sum()) for k in range(5)])
    Ts, Ta = S["T"][ms].mean(0), A["T"][ma].mean(0)
    b_expl = float(((Ts - Ta) * lam).sum())
    comp = {
        "(a) hazard level, reachable states (offline pred - actual events)": f_a * (E_pred - E_ar),
        "(a') actual events in unreachable state 'other' (sim cannot visit)": f_a * (-E_ao),
        "(b) state-visit: (sim time per state - actual) x hazard": f_a * b_expl,
        "(d) remainder (sim-path hazard mix: score / pen-diff / clock)": f_a * ((E_s - E_pred) - b_expl),
        "(c) PP opps per event (coincidental / type mix, stacked penalties)": (f_s - f_a) * E_s,
    }
    tot = PPO_s - PPO_a
    assert abs(sum(comp.values()) - tot) < 1e-9 + 1e-6 * abs(tot), (sum(comp.values()), tot)
    vals = list(comp.values())
    canc = []
    for k, v in comp.items():
        if abs(v) > tol:
            opp = [(k2, v2) for k2, v2 in comp.items() if np.sign(v2) == -np.sign(v) and v2 != 0]
            canc.append((k, v, opp))
    if abs(tot) > tol:
        verdict = "FAIL"
    elif any(opp for _, _, opp in canc):
        verdict = "COMPENSATED"
    else:
        verdict = "CLEAN"
    state_tab = pd.DataFrame({"T_sim (h/team-game)": Ts, "T_act": Ta, "dT": Ts - Ta,
                              "lam (events/h, offline pred)": lam,
                              "contribution (events/team-game)": (Ts - Ta) * lam}, index=ST)
    ev = dict(PPO_a=PPO_a, PPO_s=PPO_s, E_a=E_a, E_s=E_s, E_pred_reach=E_pred, E_a_reach=E_ar, E_a_other=E_ao, f_a=f_a,
              f_s=f_s, n_team_games_actual=int(ntg), total=tot, tol=tol, verdict=verdict, b_expl=b_expl)
    return comp, ev, state_tab, canc


def quint(x, q=5):
    return pd.qcut(x, q, labels=False, duplicates="drop")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="H3")
    ap.add_argument("--tag", default=None)
    A_ = ap.parse_args()
    arm = A_.arm
    tag = A_.tag or f"ss_r3_g1_{arm}"
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())["g1_pp_opps"]
    rows = pd.read_parquet(R3 / "fold2_rows.parquet")
    labels = json.loads((R3 / "labels_sealed.json").read_text())
    mu = np.load(R3 / f"fold2_haz_{labels[arm]}.npy")
    real = G1.real_frame(TEST)
    gt = load_games([TEST], columns=["game_id"])  # noqa: F841 (existence check)
    s = pd.read_parquet(Path("results") / tag / "strength_toi.parquet")
    s = s.merge(real[["game_id", "game_type"]], on="game_id")
    S, A = team_view(s), team_view(real)
    nseed = s.seed.nunique()
    L = [f"# D14 decomposition and responsiveness, {arm}'' (SS-R3 offsets), fold 2, {nseed} seeds", ""]
    out = {}
    for name, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        S["sel"] = (S["gt"] == f) if f else np.ones(len(S["gt"]), bool)
        A["sel"] = (A["gt"] == f) if f else np.ones(len(A["gt"]), bool)
        m = (rows.game_type == f).to_numpy() if f else np.ones(len(rows), bool)
        comp, ev, st_tab, canc = decompose(rows[m], mu[m], S, A, tol)
        out[name] = dict(ev, components=comp)
        L += [f"## {name} (actual team-games n = {ev['n_team_games_actual']}; tolerance {tol})", "",
              f"PP opps / team-game: actual {ev['PPO_a']:.4f}, sim {ev['PPO_s']:.4f}, sim - actual {ev['total']:+.4f}. "
              f"Events / team-game: actual {ev['E_a']:.4f} (offline rows: reachable {ev['E_a_reach']:.4f} + 'other' "
              f"{ev['E_a_other']:.4f}), offline predicted on reachable states {ev['E_pred_reach']:.4f}, sim "
              f"{ev['E_s']:.4f}. PP opps per event: actual {ev['f_a']:.4f}, sim {ev['f_s']:.4f}.", "",
              pd.Series(comp, name="PP opps / team-game").to_frame().assign(
                  pct_of_actual=lambda d: 100 * d.iloc[:, 0] / ev["PPO_a"]).round(4).to_markdown(floatfmt=".4f"), "",
              f"Sum of components = {sum(comp.values()):+.4f} (identity check passed). (b) explained part "
              f"{ev['b_expl']:+.4f} events/team-game before scaling by f_a.", "",
              st_tab.round(4).to_markdown(floatfmt=".4f"), ""]
        if not canc:
            L.append(f"- No single component exceeds the tolerance ({tol}) in absolute value.")
        for k, v, opp in canc:
            L.append(f"- Component over tolerance: {k} = {v:+.4f}; opposite-signed components: "
                     + (", ".join(f"{k2} {v2:+.4f}" for k2, v2 in opp) or "none") + ".")
        L += [f"- **Verdict ({name}): {ev['verdict']}**", ""]
    # ---- type mix behind (c)
    tr_ = pd.read_parquet("data/processed/strength_state/type_rows_v2.parquet")
    tr_ = tr_[tr_.season == TEST]
    act = tr_.cls.value_counts(normalize=True)
    sim_n = {c: float(s[[f"n_{c}_home", f"n_{c}_away"]].sum().sum()) for c in ("minor", "double", "major", "coinc")}
    ssum = sum(sim_n.values())
    L += ["## Type mix behind (c) (overall)", "",
          pd.DataFrame({"actual share of penalty-taking events": [act.get("minor", 0), act.get("double", 0),
                                                                  act.get("major", 0), act.get("coincidental", 0)],
                        "sim share": [sim_n["minor"] / ssum, sim_n["double"] / ssum, sim_n["major"] / ssum,
                                      sim_n["coinc"] / ssum]},
                       index=["minor", "double", "major", "coincidental"]).round(4).to_markdown(floatfmt=".4f"), ""]
    # ---- responsiveness
    tg = rows.groupby(["game_id", "team"]).agg(taken_own=("taken_own", "first"), drawn_opp=("drawn_opp", "first"),
                                               game_type=("game_type", "first")).reset_index()
    off = pd.DataFrame({"game_id": rows.game_id.to_numpy(), "team": rows.team.to_numpy(), "pen_off_pred": mu,
                        "pen_off_act": rows.y.to_numpy()}).groupby(["game_id", "team"]).sum().reset_index()
    tg = tg.merge(off, on=["game_id", "team"], how="left")
    sm = s.groupby("game_id")[["ppo_home", "ppo_away", "pen_home", "pen_away"]].mean().add_suffix("_sim")
    rl = real.set_index("game_id")[["ppo_home", "ppo_away", "pen_home", "pen_away"]]
    tg = tg.join(sm, on="game_id").join(rl, on="game_id")
    h = tg.team == 0
    tg["own_ppo_sim"] = np.where(h, tg.ppo_home_sim, tg.ppo_away_sim)
    tg["opp_ppo_sim"] = np.where(h, tg.ppo_away_sim, tg.ppo_home_sim)
    tg["own_ppo_act"] = np.where(h, tg.ppo_home, tg.ppo_away)
    tg["opp_ppo_act"] = np.where(h, tg.ppo_away, tg.ppo_home)
    tg["pen_sim"] = np.where(h, tg.pen_home_sim, tg.pen_away_sim)
    tg["pen_act"] = np.where(h, tg.pen_home, tg.pen_away)
    L += ["## Responsiveness (closed loop, fold 2, RS + PO; sim = mean over seeds per team-game)", "",
          "Quintiles are over team-games (the as-of rating of that game; Q0 low .. Q4 high). 'PP opps conferred' is the "
          "opponent's PP opportunities, i.e. those created by this team's penalties, the quantity the team-taken and "
          "opponent-drawn ratings drive in the hazard (literal choice, labelled); 'own PP opps' is the other "
          "direction. n = team-games per quintile.", ""]
    slopes = {}
    for col, nm in (("taken_own", "team taken-rating quintile"), ("drawn_opp", "opponent drawn-rating quintile")):
        tg["q"] = quint(tg[col])
        g = tg.groupby("q").agg(n=("pen_act", "size"), rating=(col, "mean"), penalties_actual=("pen_act", "mean"),
                                penalties_sim=("pen_sim", "mean"), penalties_offline_pred=("pen_off_pred", "mean"), ppo_conferred_actual=("opp_ppo_act", "mean"),
                                ppo_conferred_sim=("opp_ppo_sim", "mean"), own_ppo_actual=("own_ppo_act", "mean"),
                                own_ppo_sim=("own_ppo_sim", "mean"))
        g["conferred sim/actual"] = g.ppo_conferred_sim / g.ppo_conferred_actual
        sl_a = np.polyfit(g.rating, g.ppo_conferred_actual, 1)[0]
        sl_s = np.polyfit(g.rating, g.ppo_conferred_sim, 1)[0]
        sp_a = g.ppo_conferred_actual.iloc[-1] - g.ppo_conferred_actual.iloc[0]
        sp_s = g.ppo_conferred_sim.iloc[-1] - g.ppo_conferred_sim.iloc[0]
        slopes[nm] = dict(slope_actual=float(sl_a), slope_sim=float(sl_s), ratio=float(sl_s / sl_a),
                          spread_actual_Q5_Q1=float(sp_a), spread_sim_Q5_Q1=float(sp_s), spread_ratio=float(sp_s / sp_a))
        se = 1.3 / np.sqrt(g.n.mean())
        L += [f"### by {nm}", "", g.round(4).to_markdown(floatfmt=".4f"), "",
              f"Slope of PP opps conferred on the rating (quintile means): actual {sl_a:.3f}, sim {sl_s:.3f} "
              f"(sim/actual {sl_s / sl_a:.2f}); Q5-Q1 spread actual {sp_a:.3f}, sim {sp_s:.3f}, **spread ratio {sp_s / sp_a:.2f}**. Actual quintile-mean SE is about {se:.3f} (PP-opps SD ~1.3, "
              f"n ~{int(g.n.mean())} per quintile).", ""]
    out["responsiveness_slopes"] = slopes
    Path(f"results/{tag}_decomp.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(f"results/{tag}_decomp.json").write_text(json.dumps(out, indent=1, default=float))
    print("\n".join(L))


if __name__ == "__main__":
    main()
