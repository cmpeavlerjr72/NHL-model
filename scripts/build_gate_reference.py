"""Write data/reference/gate_targets_{season}.parquet: G5/G6/G7/G9 quantities computable from finals, plus G1
(strength-state TOI, PP opportunities, PIM, minors ended by a PP goal) from the mechanics replay of the real
penalty / goal sequence (nhl_sim.eval.g1; added for SS-R1).
Usage: build_gate_reference.py [season_id ...]   (default: every non-sealed season present)"""
import sys

import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import REFERENCE, load_verified_finals  # noqa: E402
from nhl_sim.eval import g1  # noqa: E402
from nhl_sim.eval.gates import real_games, targets_table  # noqa: E402


def main():
    seasons = [int(s) for s in sys.argv[1:]] or sorted(load_verified_finals("v2").season.unique())
    for s in seasons:
        real = real_games(s)
        t = targets_table(real, s)
        t = pd.concat([t, g1.targets_rows(g1.real_frame(s), s)], ignore_index=True)
        t.to_parquet(REFERENCE / f"gate_targets_{s}.parquet")
        a = t[(t.segment == "all") & (t.metric.isin(["total_mean", "total_sd", "home_win", "reg_tie_rate", "so_rate",
                                                      "en_goals_per_game", "score_corr"]))]
        print(s, "games", len(real), {f"{r.metric}": round(r.value, 4) for r in a.itertuples()})


if __name__ == "__main__":
    main()
