"""Write data/reference/gate_targets_{season}.parquet: G5/G6/G7/G9 quantities computable from finals, plus G1
(strength-state TOI, PP opportunities, PIM, minors ended by a PP goal) from the mechanics replay of the real
penalty / goal sequence (nhl_sim.eval.g1; added for SS-R1), and G2 (shot attempts; SA-R1) into the sibling
gate_targets_g2_{season}.parquet.
Usage: build_gate_reference.py [season_id ...]   (default: every non-sealed season present)"""
import sys

import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import REFERENCE, load_verified_finals  # noqa: E402
from nhl_sim.eval import g1  # noqa: E402
from nhl_sim.eval.gates import real_games, targets_table  # noqa: E402


def g2_targets(season):
    """SA-R1: G2 real quantities (shot attempts, nhl_sim.eval.g2) per segment, written to a versioned SIBLING file
    gate_targets_g2_<season>.parquet (the shared gate_targets file is not rewritten). Needs the attempt rows."""
    from nhl_sim.eval import g2 as G2
    from nhl_sim.shot_attempt.models import SA, load_rows
    if not (SA / f"attempt_rows_v1_{season}.parquet").exists():
        return
    R = G2.real_team_arrays(load_rows([season]))
    out = []
    for seg, f in (("all", None), ("RS", 2), ("PO", 3)):
        m = (R["game_type"] == f) if f else slice(None)
        d = G2.select(R, m) if f else R
        if len(d["game_id"]) == 0:
            continue
        for (grp, cell), v in G2.quantities(d).items():
            out.append(dict(season=season, segment=seg, gate="G2", metric=grp, key=cell, value=float(v),
                            n_team_games=len(d["game_id"])))
    pd.DataFrame(out).to_parquet(REFERENCE / f"gate_targets_g2_{season}.parquet")


def main():
    seasons = [int(s) for s in sys.argv[1:]] or sorted(load_verified_finals("v2").season.unique())
    for s in seasons:
        real = real_games(s)
        t = targets_table(real, s)
        t = pd.concat([t, g1.targets_rows(g1.real_frame(s), s)], ignore_index=True)
        t.to_parquet(REFERENCE / f"gate_targets_{s}.parquet")
        g2_targets(s)
        a = t[(t.segment == "all") & (t.metric.isin(["total_mean", "total_sd", "home_win", "reg_tie_rate", "so_rate",
                                                      "en_goals_per_game", "score_corr"]))]
        print(s, "games", len(real), {f"{r.metric}": round(r.value, 4) for r in a.itertuples()})


if __name__ == "__main__":
    main()
