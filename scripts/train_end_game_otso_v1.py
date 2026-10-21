"""EG-R1 parts B and C (Lane H8b): 3v3 OT attempt level (INV-35) and the shootout (INV-67), offline.

    train_end_game_otso_v1.py ot_parity     training-season parity table + selection (no 2024-25 read)
    train_end_game_otso_v1.py ot_fold2      fold-2 parity of the selected level (reads 2024-25 3v3 rows; AFTER the commit)
    train_end_game_otso_v1.py so_fold1      shootout S1 mechanics inputs + S2 fold-1 s-grid (training seasons only)
    train_end_game_otso_v1.py so_fold2      blind fold-2 S1 bias checks and S2 vs S1 (reads 2024-25; AFTER the commit)

Outputs: results/end_game_otso_v1/ (gitignored) and docs/tests/end_game_eg_r1_otso_*.md pieces written by the
subcommands; every table is also printed.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.end_game import ot_level as OL  # noqa: E402

OUT = ROOT / "results" / "end_game_otso_v1"
OUT.mkdir(parents=True, exist_ok=True)
SLAB = {20212022: "2021-22", 20222023: "2022-23", 20232024: "2023-24", 20242025: "2024-25"}


def md(df, nd=4):
    return df.round(nd).to_markdown(index=False)


def ot_parity():
    seasons = [20212022, 20222023, 20232024]                  # training seasons only: 2024-25 is not loaded
    games = OL.game_table(seasons)
    rows = OL.load_rows(seasons)
    assert rows.season.max() <= 20232024
    res = {}
    tabs = []
    for fold in (1, 2):
        tr = OL.TRAIN[fold]
        specs = {**{k: v for k, v in OL.GRID.items()}, "E": ("E", None), "O": ("O", None)}
        gm = games[games.season.isin(tr)]
        meta, lev = OL.asof_levels(rows[rows.season.isin(tr)], gm, specs, train_seasons=tr)
        par = OL.level_parity(rows, meta, lev, OL.JUDGED[fold])
        par.insert(0, "fold", fold)
        tabs.append(par)
        sel = OL.select_level(par, OL.JUDGED[fold])
        res[fold] = sel
        np.savez(OUT / f"ot_levels_fold{fold}_train.npz", game_id=meta.game_id.to_numpy(), **lev)
    T = pd.concat(tabs, ignore_index=True)
    T["season"] = T.season.map(SLAB)
    T["pass_0.5pp"] = T.parity.abs() <= OL.TOL
    T["pred_per_team_hour"] = T.predicted / T.team_hours
    T["actual_per_team_hour"] = T.actual / T.team_hours
    T.to_csv(OUT / "ot_parity_training.csv", index=False)
    (OUT / "ot_selection.json").write_text(json.dumps(res, indent=1))
    print(md(T[["fold", "season", "level", "actual", "predicted", "parity", "pass_0.5pp", "team_hours",
                "games_with_3v3", "actual_per_team_hour", "pred_per_team_hour"]]))
    print(json.dumps(res, indent=1))
    # SE of the season-level count (Poisson) for context
    ctx = T[T.level == "O"][["season", "actual"]].drop_duplicates()
    ctx["poisson_se_rel"] = 1 / np.sqrt(ctx.actual)
    print(md(ctx))
    doc = ["# EG-R1 part B: 3v3 attempt level, training-season parity (Lane H8b, 2026-10-21)", "",
           "Training seasons only (2021-22 .. 2023-24); the 2024-25 rows were not loaded. Level = attempts per team-hour, "
           "regular-season 3v3 team-view rows, both teams. Parity = predicted / actual - 1 per genuine-prior training "
           "season; limit 0.5% (SA-R2 form). E and O are reported, never selectable (D35, L29). 2021-22 is burn-in "
           "(its prior is its own final rate) and is never judged.", "",
           md(T[["fold", "season", "level", "actual", "predicted", "parity", "pass_0.5pp", "team_hours",
                 "games_with_3v3", "actual_per_team_hour", "pred_per_team_hour"]]), "",
           "Poisson relative SE of the season's 3v3 attempt count (the floor under any parity read):", "", md(ctx), "",
           "Selection (rule in the experiments.md H8b execution note):", "", "```", json.dumps(res, indent=1), "```", "",
           "No construction passes the 0.5% limit in any judged season (the sampling error of a season's own count is "
           "about 2.6%, five times the limit). The fallback rule applies. Fold 2 (the served fold): the smallest max "
           "|parity| is M1 K500 (1.92%), 0.13 pp better than M1 K2000 and M2 H30, so **M1 K500 is selected**. Fold 1 "
           "(D13 guard): K2000 0.87%, K500 0.90%, within the 0.1 pp tie; the same M1 K500 is carried on fold 1 for "
           "consistency (labelled). The 2023-24 over-prediction (+1.9%) is the as-of level lagging a falling 3v3 "
           "attempt rate (55.7 vs 56.9 per team-hour); E (the era mean) is in-sample on 2023-24 and not selectable."]
    (ROOT / "docs" / "tests" / "end_game_eg_r1_otso_ot_parity_2026-10-21.md").write_text("\n".join(doc), encoding="utf-8")


def ot_fold2():
    """Fold-2 (2024-25) parity of the selected level M1 K500, plus the other grid members and O for reference."""
    sel = json.loads((OUT / "ot_selection.json").read_text())["2"]["selected"]
    seasons = [20212022, 20222023, 20232024, 20242025]
    games = OL.game_table(seasons)
    rows = OL.load_rows(seasons)
    specs = {**OL.GRID, "E": ("E", None), "O": ("O", None)}
    meta, lev = OL.asof_levels(rows, games, specs, train_seasons=OL.TRAIN[2])
    par = OL.level_parity(rows, meta, lev, [20242025])
    par["season"] = par.season.map(SLAB)
    par["per_team_hour_actual"] = par.actual / par.team_hours
    par["per_team_hour_pred"] = par.predicted / par.team_hours
    r = rows[rows.season == 20242025]
    par["goals"] = int(r.y_goal.sum())
    par["poisson_se_rel"] = 1 / np.sqrt(par.actual)
    par["selected"] = par.level == sel
    par["within_poisson_se"] = par.parity.abs() <= par.poisson_se_rel
    print(md(par))
    par.to_csv(OUT / "ot_parity_fold2.csv", index=False)
    # served form: A3g(row, old level) x exp(L_new - L_old) x exp(refit 3v3 cell), against the A3g-c table
    lev = OL.selected_level(2, sel)
    cell, info = OL.training_cell(2, lev)
    tr, te = OL.frames_3v3(2)
    bst = OL.booster(2)
    old_cell = json.loads((ROOT / "results/shot_attempt_r3/models/A3g-c.json").read_text())["cell"][4]
    mu_old, _ = OL.swapped_prediction(te, bst, pd.Series(te.level.to_numpy(), index=te.game_id.to_numpy()).groupby(level=0).first(), old_cell)
    mu_new, dl = OL.swapped_prediction(te, bst, lev, cell)
    y = te.y.to_numpy(float)
    rows_ = []
    for nm, mu in (("A3g-c (shared ES level, cell %.4f)" % old_cell, mu_old), ("own %s level, refit cell %.4f" % (sel, cell), mu_new)):
        rows_.append(dict(arm=nm, actual=y.sum(), predicted=mu.sum(), bias=mu.sum() / y.sum() - 1,
                          per60_combined_pred=2 * mu.sum() / (te.exposure_s.sum() / 3600), per60_combined_actual=2 * y.sum() / (te.exposure_s.sum() / 3600),
                          poisson_se_rel=1 / np.sqrt(y.sum())))
    served = pd.DataFrame(rows_)
    print(md(served))
    print("training cell", cell, info)
    served.to_csv(OUT / "ot_served_offline_fold2.csv", index=False)
    json.dump(dict(cell=cell, old_cell=old_cell, **info), open(OUT / "ot_cell_fold2.json", "w"))
    doc = ["# EG-R1 part B: fold-2 parity and offline served bias of the 3v3 level (Lane H8b, 2026-10-21)", "",
           "Read AFTER the training parity table and the selection were committed (e977e74). Fold 2 = 2024-25 regular season, "
           "3v3 team-view rows, both teams. Parity is of the level alone (reported); the gate is the closed-loop G2 3v3 cell.", "",
           md(par), "",
           "Offline served form on the same rows (A3g booster x exp(L_new - L_old) x exp(cell); the cell is the SA-R3 "
           "recipe refit on the fold-2 TRAINING rows with the own level in place; with the old level the same code "
           "reproduces the frozen A3g-c cell to 1e-12):", "", md(served), "",
           "Training diagnostics of the refit cell: " + json.dumps(info) + f"; frozen A3g-c cell {old_cell:.5f}, refit cell {cell:.5f}.",
           "", "UNDERPOWERED note: about 1,370 attempts and 160 goals in the season; the Poisson count error is 2.7%."]
    (ROOT / "docs" / "tests" / "end_game_eg_r1_otso_ot_fold2_2026-10-21.md").write_text(chr(10).join(doc), encoding="utf-8")
    return par


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ot_parity", "ot_fold2", "so_fold1", "so_fold2"])
    a = ap.parse_args()
    {"ot_parity": ot_parity, "ot_fold2": ot_fold2}[a.cmd]()
