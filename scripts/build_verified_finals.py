"""Cross-check final scores and REG/OT/SO across schedule, boxscore and pbp-accumulated goals.
Writes data/reference/verified_finals_v1.parquet and prints every disagreement."""
from pathlib import Path

import pandas as pd

g = pd.read_parquet("data/processed/games.parquet")
ev = pd.concat([pd.read_parquet(f, columns=["game_id", "event", "period_type", "goalie_id", "owner_is_home"])
                for f in sorted(Path("data/processed/events").glob("events_*.parquet"))])
en = ev[(ev.event == "GOAL") & (ev.period_type != "SO") & ev.goalie_id.isna()]
g = g.merge(en.groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0)
            .rename(columns={True: "en_goals_home", False: "en_goals_away"}).reset_index(), on="game_id", how="left")
g[["en_goals_home", "en_goals_away"]] = g[["en_goals_home", "en_goals_away"]].fillna(0).astype(int)
g["end_state_sched"] = g["last_period_type_sched"]
g["home_score"], g["away_score"] = g.home_score_box, g.away_score_box
g["end_state"] = g.end_state_box

dis = []
# empty-net goals: goals scored BY home with no goalie in net count against the away goalie sum
g["away_en_goals_scored_on_home"] = g.en_goals_away   # scored by away, against home net
g["home_en_goals_scored_on_away"] = g.en_goals_home
for _, r in g.iterrows():
    f = []
    if (r.home_score_sched, r.away_score_sched) != (r.home_score_box, r.away_score_box):
        f.append("score_sched_vs_box")
    if (r.home_score_pbp, r.away_score_pbp) != (r.home_score_box, r.away_score_box):
        f.append("score_pbp_vs_box")
    if r.end_state_sched != r.end_state_box:
        f.append("end_state_sched_vs_box")
    if r.end_state_pbp != r.end_state_box:
        f.append("end_state_pbp_vs_box")
    # secondary: skater goal sum + goalie GA should equal non-shootout goals
    so_h = int(r.end_state_box == "SO" and r.home_score_box > r.away_score_box)
    so_a = int(r.end_state_box == "SO" and r.away_score_box > r.home_score_box)
    if (r.home_goals_playersum, r.away_goals_playersum) != (r.home_score_box - so_h, r.away_score_box - so_a):
        f.append("playersum_vs_box")
    if (r.home_ga_goaliesum + r.away_en_goals_scored_on_home, r.away_ga_goaliesum + r.home_en_goals_scored_on_away) != (r.away_score_box - so_a, r.home_score_box - so_h):
        f.append("goaliesum_vs_box")
    dis.append(",".join(f))
g["disagreements"] = dis
primary = g.disagreements.str.contains("sched|pbp_vs_box", regex=True)
g["verified"] = ~g.disagreements.str.contains("score_|end_state_", regex=True)
g["n_sources"] = 3
cols = ["game_id", "season", "game_type", "game_date_local", "puck_drop_utc", "home", "away", "home_score",
        "away_score", "end_state", "home_score_sched", "away_score_sched", "home_score_pbp", "away_score_pbp",
        "end_state_sched", "end_state_pbp", "verified", "disagreements"]
out = g[cols]
Path("data/reference").mkdir(parents=True, exist_ok=True)
out.to_parquet("data/reference/verified_finals_v1.parquet")
print("games", len(out), "verified", int(out.verified.sum()), "primary-source disagreements", int(primary.sum()))
print("any-flag counts:")
print(g.disagreements.str.split(",").explode().value_counts().to_string())
bad = out[out.disagreements != ""]
pd.set_option("display.width", 250)
print(bad.drop(columns=["puck_drop_utc"]).to_string())
