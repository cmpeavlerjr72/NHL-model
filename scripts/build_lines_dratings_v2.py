"""INV-38 / D21: lines_dratings_v2 = v1 + per-game pl_sign_suspect / pl_sign_ambiguous flags (close and open versions).
Flag only: no sign is rewritten, v1 is untouched. Rows keep v1 columns; the game-level flags are broadcast to every row.
Close: PL favourite = sign of the modal AWAY close PL line (negative = away favourite) vs favourite from the book-median
no-vig close ML home prob (same definition as crosscheck_sbro_dratings.py). Pick'em (|p-0.5| <= 0.005) -> ambiguous, not suspect.
Open: modal AWAY open PL line vs mean over groups of no-vig open ML home prob."""
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.dratings import nov_vig_home  # noqa: E402

PICKEM_TOL = 0.005


def mode(xs):
    xs = [x for x in xs if x is not None and x == x]
    return Counter(xs).most_common(1)[0][0] if xs else None


def classify(pl_away_line, p_home, tol=PICKEM_TOL):
    """-> (suspect, ambiguous). Missing inputs or a zero line -> (False, False)."""
    if pl_away_line is None or p_home is None or pl_away_line != pl_away_line or p_home != p_home or pl_away_line == 0:
        return False, False
    if abs(p_home - 0.5) <= tol + 1e-12:
        return False, True
    pl_fav_home = pl_away_line > 0  # away +1.5 -> home is the -1.5 favourite
    ml_fav_home = p_home > 0.5
    return pl_fav_home != ml_fav_home, False


def game_flags(d):
    ml = d[d.market == "ml"]
    probs = []
    for grp in ("offshore", "vegas"):
        a = ml[(ml.group == grp) & (ml.side == "away") & (ml.field == "close")].set_index("book").price
        h = ml[(ml.group == grp) & (ml.side == "home") & (ml.field == "close")].set_index("book").price
        for b in a.index.intersection(h.index):
            if pd.notna(a[b]) and pd.notna(h[b]):
                probs.append(nov_vig_home(a[b], h[b]))
    p_close = st.median(probs) if probs else None
    op = []
    for grp in ("offshore", "vegas"):
        a = ml[(ml.group == grp) & (ml.side == "away") & (ml.field == "open")].price
        h = ml[(ml.group == grp) & (ml.side == "home") & (ml.field == "open")].price
        if len(a) and len(h) and pd.notna(a.iloc[0]) and pd.notna(h.iloc[0]):
            op.append(nov_vig_home(a.iloc[0], h.iloc[0]))
    p_open = st.mean(op) if op else None
    pl = d[(d.market == "pl") & (d.side == "away")]
    l_close = mode(pl[pl.field == "close"].line.tolist())
    l_open = mode(pl[pl.field == "open"].line.tolist())
    s, a = classify(l_close, p_close)
    so, ao = classify(l_open, p_open)
    return dict(dr_pl_away_close_mode=l_close, dr_ml_home_close_nv=p_close, pl_sign_suspect=s, pl_sign_ambiguous=a,
                dr_pl_away_open_mode=l_open, dr_ml_home_open_nv=p_open, pl_sign_suspect_open=so, pl_sign_ambiguous_open=ao)


def main():
    v1 = pd.read_parquet(ROOT / "data/processed/lines_dratings_v1.parquet")
    fl = pd.DataFrame([dict(game_id=int(g), **game_flags(d)) for g, d in v1.groupby("game_id")])
    fl.to_csv(ROOT / "data/processed/lines_dratings_v2_pl_flags.csv", index=False)
    v2 = v1.merge(fl[["game_id", "pl_sign_suspect", "pl_sign_ambiguous", "pl_sign_suspect_open", "pl_sign_ambiguous_open"]],
                  on="game_id", how="left")
    assert len(v2) == len(v1)
    v2.to_parquet(ROOT / "data/processed/lines_dratings_v2.parquet", index=False)
    print(len(fl), "games;", int(fl.pl_sign_suspect.sum()), "suspect;", int(fl.pl_sign_ambiguous.sum()), "ambiguous")


if __name__ == "__main__":
    main()
