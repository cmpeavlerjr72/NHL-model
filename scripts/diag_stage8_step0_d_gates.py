"""Stage 8 step 0, part D: restate G7 targets for the training seasons and match them to pbp-derived numbers (item 6)."""
from diag_stage8_step0_common import *

G = games()
EV = load_events(SEASONS, columns=["game_id", "season", "game_type", "event", "period_type", "goalie_id", "strength_state", "game_time_s"])
gl = EV[(EV.event == "GOAL") & (EV.period_type != "SO")]
rows = []
for s in SEASONS:
    T = load_reference(f"gate_targets_{s}")
    for seg, gt_ in (("all", None), ("RS", 2), ("PO", 3)):
        g = G[(G.season == s)] if gt_ is None else G[(G.season == s) & (G.game_type == gt_)]
        d = gl[(gl.season == s)] if gt_ is None else gl[(gl.season == s) & (gl.game_type == gt_)]
        mine = {"reg_tie_rate": (g.end_state_box != "REG").mean(), "ot_rate": (g.end_state_box == "OT").mean(), "so_rate": (g.end_state_box == "SO").mean(),
                "en_goals_per_game": d.goalie_id.isna().sum() / len(g)}
        mine_alt = {"en_goals_per_game": (d.strength_state == "EN_AGAINST").sum() / len(g)}
        for m, v in mine.items():
            r = T[(T.segment == seg) & (T.metric == m)]
            ref = float(r.value.iloc[0]) if len(r) else np.nan
            rows.append(dict(season=SLAB[s], segment=seg, metric=m, gate_target=ref, pbp_derived=v, diff=v - ref, n_games=len(g),
                             alt_EN_AGAINST_flag=mine_alt.get(m, np.nan), match="OK" if abs(v - ref) < 5e-4 else "MISMATCH"))
R = pd.DataFrame(rows)
txt = ["\n### 6. G7 quantities restated for the training seasons (gate_targets_<season>.parquet) vs pbp-derived\n",
       "Tolerances in `docs/gates.yaml`: regulation tie rate 1.5 pp, shootout share 1.0 pp, EN goals per game 0.03. `reg_tie_rate` is the share of games not decided in regulation (OT or SO); `ot_rate` is the share decided in OT (not SO). `en_goals_per_game` = non-shootout goals with no goalie id (goals into an empty net), both teams. 'match' = within 0.0005 of the gate target.\n",
       md(R, 4)]
(OUT / "part_d.md").write_text("\n".join(txt), encoding="utf-8")
print(R[R.match != "OK"])
print("n rows", len(R))
