"""SS-R5 step 1: fold-1 replication and stop condition. Coincidental share of a team's penalty events and actual PP
opportunities conferred per penalty, by quintile of the team's as-of taken-rating (ratings_grid_v2 w=1.0 b=1800, the
hazard's rating; quintiles cut on team-games by rank within the group), with game-block bootstrap 95% CIs.
Groups: each season 2021-22..2024-25, the fold-1 training seasons pooled, and fold 1 test (2023-24).
Stop condition (spec): the 2023-24 Q5-minus-Q1 coincidental-share difference has a 95% CI that includes 0.
PP opps conferred = the opponent's PP opportunities (mechanics replay, G1.real_frame) divided by the team's penalties.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.eval import g1 as G1  # noqa: E402
from nhl_sim.strength_state import models_r5 as R5  # noqa: E402

OUT = Path("results/strength_state_r5")
NB, SEED = 2000, 20261015


def real(season):
    p = OUT / f"real_frame_{season}.parquet"
    if p.exists():
        return pd.read_parquet(p)
    t0 = time.time()
    f = G1.real_frame(season)
    f.to_parquet(p, index=False)
    print(time.strftime("%H:%M:%S"), "real_frame", season, f"{time.time() - t0:.0f}s", flush=True)
    return f


def team_games(seasons):
    t = pd.read_parquet(R5.SS / "type_rows_v2.parquet", columns=["game_id", "team", "cls", "season"])
    t = t[t.season.isin(seasons)]
    tg = pd.read_parquet(R5.SS / "team_game_v2.parquet")
    tg = tg[tg.season.isin(seasons)].assign(team=lambda d: 1 - d.is_home)
    rt = R5.team_ratings(150)[["game_id", "team_id", "taken"]].rename(columns={"taken": "trate"})
    tg = tg.drop(columns=["taken"]).merge(rt, on=["game_id", "team_id"], how="left")
    ev = t.assign(co=(t.cls == "coincidental").astype(int)).groupby(["game_id", "team"]).agg(
        n=("co", "size"), co=("co", "sum")).reset_index()
    d = tg.merge(ev, on=["game_id", "team"], how="left").fillna({"n": 0, "co": 0})
    rf = pd.concat([real(s) for s in seasons])
    rf = rf.set_index("game_id")
    h = d.team == 0
    d["opp_ppo"] = np.where(h, rf.loc[d.game_id, "ppo_away"].to_numpy(), rf.loc[d.game_id, "ppo_home"].to_numpy())
    d["gtype"] = rf.loc[d.game_id, "game_type"].to_numpy()
    return d[["game_id", "season", "team_id", "team", "trate", "n", "co", "opp_ppo", "gtype"]]


def quint_stats(d, nb=NB):
    """-> frame per quintile (share, ppo/pen) and Q5-Q1 differences with bootstrap CIs (game blocks)."""
    q = pd.qcut(d.trate.rank(method="first"), 5, labels=False).to_numpy()
    games = np.sort(d.game_id.unique())
    gpos = np.searchsorted(games, d.game_id.to_numpy())
    G = len(games)
    M = {c: np.zeros((G, 5)) for c in ("n", "co", "opp_ppo", "trate")}
    cnt = np.zeros((G, 5))
    for c in M:
        np.add.at(M[c], (gpos, q), d[c].to_numpy())
    np.add.at(cnt, (gpos, q), 1)
    w = np.random.default_rng(SEED).multinomial(G, np.ones(G) / G, size=nb).astype(float)

    def stats(wt):
        s = {c: wt @ M[c] for c in M}
        s["cnt"] = wt @ cnt
        share = s["co"] / s["n"]
        ppp = s["opp_ppo"] / s["n"]
        return share, ppp, s["n"] / s["cnt"], s["trate"] / s["cnt"]

    sh, pp, pen, rat = stats(np.ones(G))
    bsh, bpp, _, _ = (np.array(x) for x in zip(*[stats(wi)[:2] + (0, 0) for wi in w]))
    res = pd.DataFrame({"mean_taken_rating": rat, "penalties_per_team_game": pen, "coinc_share": sh,
                        "coinc_se": bsh.std(0, ddof=1), "ppo_conf_per_pen": pp, "ppo_se": bpp.std(0, ddof=1),
                        "n_team_games": cnt.sum(0)})
    dd = {"coinc_Q5-Q1": (sh[4] - sh[0], np.percentile(bsh[:, 4] - bsh[:, 0], [2.5, 97.5])),
          "ppo_per_pen_Q5-Q1": (pp[4] - pp[0], np.percentile(bpp[:, 4] - bpp[:, 0], [2.5, 97.5]))}
    return res, dd


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    seasons = [20212022, 20222023, 20232024, 20242025]
    d = team_games(seasons)
    groups = {"2021-22": [20212022], "2022-23": [20222023], "fold-1 train pooled (2021-22+2022-23)": [20212022, 20222023],
              "2023-24 (fold 1 test)": [20232024], "2024-25 (fold 2 test, R4 gradient)": [20242025]}
    L, J = [], {}
    for name, ss in groups.items():
        for sel, lab in ((d.season.isin(ss), "RS+PO"), (d.season.isin(ss) & (d.gtype == 2), "RS only")):
            res, dd = quint_stats(d[sel])
            L += [f"### {name} [{lab}]", "", res.round(4).to_markdown(floatfmt=".4f"), ""]
            for k, (v, ci) in dd.items():
                L.append(f"- {k}: {v:+.4f}, 95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
            L.append("")
            J[f"{name} [{lab}]"] = {k: dict(diff=float(v), lo=float(ci[0]), hi=float(ci[1])) for k, (v, ci) in dd.items()}
            res.to_csv(OUT / f"fold1_rep_{name.split(' ')[0]}_{lab.replace(' ', '').replace('+', '')}.csv", index=False)
    (OUT / "fold1_replication.md").write_text("\n".join(L), encoding="utf-8")
    (OUT / "fold1_replication.json").write_text(json.dumps(J, indent=1))
    print("\n".join(L))
    c = J["2023-24 (fold 1 test) [RS+PO]"]["coinc_Q5-Q1"]
    stop = c["lo"] <= 0 <= c["hi"]
    print("STOP CONDITION (2023-24 RS+PO coincidental share Q5-Q1 CI includes 0):", stop, c)


if __name__ == "__main__":
    main()



