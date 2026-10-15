"""Summarise data/processed/espn_lines_coverage.csv into a markdown table (stdout)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "processed" / "espn_lines_coverage.csv")
df["has_line"] = df.provider.notna() & (df.has_ml | df.has_pl | df.has_total)
labels = {20232024: "2023-24", 20242025: "2024-25", 20252026: "2025-26 (comparison only)"}
rows = []
for s, g in df.groupby("season"):
    games = g.game_id.nunique()
    gl = g[g.provider.notna()].groupby("game_id")[["has_ml", "has_pl", "has_total", "has_open", "has_close", "has_line"]].max()
    pct = lambda col: f"{100 * gl[col].sum() / games:.1f}%"
    provs = g.provider.value_counts().to_dict()
    both = (gl.has_open & gl.has_close).sum()
    rows.append(f"| {labels[s]} | {games} | {pct('has_line')} | {pct('has_ml')} | {pct('has_pl')} | {pct('has_total')} | "
                f"{pct('has_open')} | {pct('has_close')} | {100 * both / games:.1f}% | {provs} |")
print("| Season | Games | Any line | ML | PL | Total | Open | Close | Open+Close | Provider rows |")
print("|---|---|---|---|---|---|---|---|---|---|")
print("\n".join(rows))
print()
# by month for 2023-24 / 2024-25: any-line coverage
sch = pd.read_parquet(ROOT / "data" / "processed" / "schedule.parquet")[["game_id", "game_date_local"]]
m = df.merge(sch, on="game_id")
m["month"] = m.game_date_local.str[:7]
gl = m.groupby(["season", "month", "game_id"]).has_line.max().reset_index()
t = gl.groupby(["season", "month"]).has_line.agg(["sum", "count"])
t["pct"] = (100 * t["sum"] / t["count"]).round(1)
print(t.to_string())
