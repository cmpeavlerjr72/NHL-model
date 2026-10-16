"""G-R1 data layer (docs/models/goal/experiments.md G-R1; cascade stage 6, goal given shot on goal; D8, D23, D24, D32).

Rows: shots on goal (SHOT, GOAL) with a goalie in net, from the stage-4 attempt tables
`data/processed/shot_attribute/attempt_attr_v1_*.parquet` (read only; shootout and penalty shots already excluded),
joined to the recorded goalie in net (`goalie_id`, events table, D8: recorded fact, used offline). Excluded: empty-net
shots (team-view st 6, stage 8; the few st-6 rows with a recorded goalie are excluded too and counted) and the few goalie-less SOG recorded in a goalie-in state (counted).
y = 1 if goal.

Strength groups (sg, shooting team's pre-event view): 0 5v5, 1 PP-for, 2 PK, 3 4v4, 4 3v3, 5 EAF (shooting team's
own goalie pulled, opposing goalie in net). Gated: 5v5, PP, PK. 4v4 / 3v3 / EAF reported with n.
Level groups (lg): 5v5 (+ EAF, which takes the 5v5 level, labelled), PP, PK, 4v4, 3v3 (own groups, INV-54 precedent).

C0 cell table: recorded training goal rate per (cell x type = cls 0..77) x sg, shrunk with a fixed pseudo-count K_CELL
toward the pooled-over-groups class rate x the group's goals / expected ratio (labelled construction; the class rate is
itself shrunk to its cell's rate the same way). Fixed a priori, not tuned.

Level (D23): the as-of conversion RELATIVE TO THE TRAINING CELL TABLE, per level group, entered as a logit offset with
coefficient 1:  delta = logit(G_hat) - logit(E_hat), where G = goals, E = summed table probability, per SOG.
  M0   last season's final (G, E) rates, constant all season
  E    D24 recording era (era 2 from 2023-24): pooled training (G, E) of the game's era; an era without training rows
       falls back to the pooled training rates (delta ~ 0)
  M1_K (G_std + K g_prev) / (N_std + K) and (E_std + K e_prev) / (N_std + K), K in {500, 2000, 8000} SOG
  M2   M1 with K = 2000 and the season-to-date counts discounted by 0.5^(gap days / H), H in {30, 60}
  O    oracle: the season's own final rates (diagnostic, never selectable)
The first data season (2021-22) has no prior: its prior is its own final (look-ahead, labelled; never judged).
created_at = 6 h after the last puck drop of the previous game date (LC-2 form), asserted < puck_drop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED
from nhl_sim.shot_attribute.tables import N_CELL, N_CLASS, N_TYPE, TIER_OF_CELL  # read-only use
from nhl_sim.strength_state.tables import assert_pregame

SA = PROCESSED / "shot_attribute"
EV = PROCESSED / "events"
OUT = PROCESSED / "goal"
SEASONS = [20212022, 20222023, 20232024, 20242025]
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
ERA2_FROM = 20232024
SG_NAMES = ("5v5", "PP", "PK", "4v4", "3v3", "EAF")
N_SG = 6
SG_OF_ST = np.array([0, 1, 2, 3, 4, 5, -1], np.int8)    # team-view st 0..6 -> sg (st 6 = empty net, out of scope)
LG_OF_SG = np.array([0, 1, 2, 3, 4, 0], np.int8)
LG_NAMES = ("5v5+EAF", "PP", "PK", "4v4", "3v3")
N_LG = 5
GATED_SG = (0, 1, 2)
K_CELL = 20.0
COLS = ["game_id", "season", "game_type", "sort_order", "t", "team", "is_home", "event", "is_goal", "st", "sc", "period",
        "ptype", "cell", "type6", "cls", "rebound", "rush", "d"]


def logit(p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def era_of(season) -> np.ndarray:
    return np.where(np.asarray(season) >= ERA2_FROM, 2, 1).astype(np.int8)


# ------------------------------------------------------------------------------------------------------ rows
def load_rows(seasons=SEASONS) -> tuple[pd.DataFrame, dict]:
    """In-scope SOG rows with ids and covariates. Returns (rows, info counts)."""
    games = pd.read_parquet(PROCESSED / "block" / "games_v1.parquet")
    arena = pd.read_parquet(SA / "arena_dist_v1.parquet", columns=["game_id", "arena_f"])
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    parts, info = [], {}
    for s in seasons:
        a = pd.read_parquet(SA / f"attempt_attr_v1_{s}.parquet", columns=COLS)
        a = a[a.event.isin(["SHOT", "GOAL"])]
        e = pd.read_parquet(EV / f"events_{s}.parquet", columns=["game_id", "sort_order", "event", "goalie_id"])
        a = a.merge(e, on=["game_id", "sort_order", "event"], how="left", validate="one_to_one")
        n0 = len(a)
        en = (a.st == 6).to_numpy()
        nogo = (~en) & a.goalie_id.isna().to_numpy()
        info[s] = dict(sog=n0, empty_net_st6=int(en.sum()), st6_with_goalie=int(a.goalie_id[en].notna().sum()), goalie_missing_in_goalie_state=int(nogo.sum()),
                       goalie_missing_goals=int((nogo & a.is_goal.to_numpy()).sum()))
        a = a[~en & ~nogo]
        if (a.cls < 0).any():
            raise ValueError("SOG without a location class")
        parts.append(a)
    r = pd.concat(parts, ignore_index=True)
    r = r.merge(games[["game_id", "date", "drop", "home_id", "away_id", "arena"]], on="game_id", how="left",
                validate="many_to_one")
    if r.home_id.isna().any():
        raise ValueError("rows without a game")
    r["team_id"] = np.where(r.team == 0, r.home_id, r.away_id)
    r["opp_id"] = np.where(r.team == 0, r.away_id, r.home_id)
    r["goalie_id"] = r.goalie_id.astype(np.int64)
    r = r.merge(arena, on="game_id", how="left", validate="many_to_one")
    r = r.merge(tg.rename(columns={"b2b": "b2b_own"}), on=["game_id", "team_id"], how="left", validate="many_to_one")
    r = r.merge(tg.rename(columns={"team_id": "opp_id", "b2b": "b2b_opp"}), on=["game_id", "opp_id"], how="left",
                validate="many_to_one")
    for c in ("arena_f", "b2b_own", "b2b_opp"):
        if r[c].isna().any():
            raise ValueError(f"missing {c} on {int(r[c].isna().sum())} rows")
    r["sg"] = SG_OF_ST[r.st.to_numpy()]
    if (r.sg < 0).any():
        raise ValueError("out-of-scope strength state")
    r["lg"] = LG_OF_SG[r.sg.to_numpy()]
    r["tier"] = TIER_OF_CELL[r.cell.to_numpy()]
    r["y"] = r.is_goal.astype(np.int8)
    r["era"] = era_of(r.season.to_numpy())
    r = r.sort_values(["date", "game_id", "sort_order"], kind="stable").reset_index(drop=True)
    return r, info


# ------------------------------------------------------------------------------------------------ cell table
def _shrink(g, n, prior, k=K_CELL):
    return (g + k * prior) / (n + k)


def cell_table(tr: pd.DataFrame) -> np.ndarray:
    """(N_CLASS, N_SG) shrunk recorded goal rate per SOG (see module doc)."""
    cls, sg, y = tr.cls.to_numpy(), tr.sg.to_numpy(), tr.y.to_numpy().astype(float)
    n = np.zeros((N_CLASS, N_SG))
    g = np.zeros((N_CLASS, N_SG))
    np.add.at(n, (cls, sg), 1.0)
    np.add.at(g, (cls, sg), y)
    lg = g.sum() / n.sum()
    cn = n.sum(1).reshape(N_CELL, N_TYPE).sum(1)
    cg = g.sum(1).reshape(N_CELL, N_TYPE).sum(1)
    cell_rate = _shrink(cg, cn, lg)
    cls_rate = _shrink(g.sum(1), n.sum(1), np.repeat(cell_rate, N_TYPE))
    exp_g = (n * cls_rate[:, None]).sum(0)
    mult = np.where(exp_g > 0, g.sum(0) / np.maximum(exp_g, 1e-12), 1.0)
    prior = np.clip(cls_rate[:, None] * mult[None, :], 1e-4, 0.95)
    return _shrink(g, n, prior)


def table_prob(rows: pd.DataFrame, T: np.ndarray) -> np.ndarray:
    return T[rows.cls.to_numpy(), rows.sg.to_numpy()]


# ----------------------------------------------------------------------------------------------------- level
def game_list(rows: pd.DataFrame) -> pd.DataFrame:
    g = rows.groupby("game_id").agg(season=("season", "first"), date=("date", "first"), drop=("drop", "first"))
    return g.reset_index().sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)


def game_counts(rows: pd.DataFrame, p_tab: np.ndarray, games: pd.DataFrame):
    gi = pd.Series(np.arange(len(games)), index=games.game_id.to_numpy())
    ix = gi.reindex(rows.game_id.to_numpy()).to_numpy().astype(np.int64)
    lg = rows.lg.to_numpy()
    G, E, N = (np.zeros((len(games), N_LG)) for _ in range(3))
    np.add.at(G, (ix, lg), rows.y.to_numpy().astype(float))
    np.add.at(E, (ix, lg), p_tab)
    np.add.at(N, (ix, lg), 1.0)
    return G, E, N


def asof_levels(rows: pd.DataFrame, p_tab: np.ndarray, specs: dict, train_seasons) -> tuple[pd.DataFrame, dict]:
    """specs {name: (kind, par)}, kind none / M0 / E / M1 (K) / M2 ((H, K)) / O -> (meta, {name: (G, N_LG) delta})."""
    games = game_list(rows)
    G, E, N = game_counts(rows, p_tab, games)
    seasons = sorted(games.season.unique())
    fin = {}
    for s in seasons:
        m = (games.season == s).to_numpy()
        fin[s] = (G[m].sum(0) / np.maximum(N[m].sum(0), 1), E[m].sum(0) / np.maximum(N[m].sum(0), 1))
    trm = games.season.isin(train_seasons).to_numpy()
    era = era_of(games.season.to_numpy())
    pooled = (G[trm].sum(0) / N[trm].sum(0), E[trm].sum(0) / N[trm].sum(0))
    era_rates = {}
    for e_ in (1, 2):
        m = trm & (era == e_)
        era_rates[e_] = (G[m].sum(0) / N[m].sum(0), E[m].sum(0) / N[m].sum(0)) if m.any() else pooled
    out = {n: np.zeros((len(games), N_LG)) for n in specs}
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    for i, season in enumerate(seasons):
        gp, ep = fin[seasons[i - 1]] if i > 0 else fin[season]
        idx_s = np.flatnonzero((games.season == season).to_numpy())
        dates = games.date.to_numpy()[idx_s]
        st = {n: [np.zeros(N_LG), np.zeros(N_LG), np.zeros(N_LG)] for n in specs}
        prev_date = None
        for d in np.unique(dates):
            ix = idx_s[dates == d]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            gap = 0.0 if prev_date is None else float((pd.Timestamp(d) - pd.Timestamp(prev_date)).days)
            for n, (kind, par) in specs.items():
                sg_, se_, sn_ = st[n]
                if kind == "none":
                    v = np.zeros(N_LG)
                elif kind == "M0":
                    v = logit(gp) - logit(ep)
                elif kind == "O":
                    v = logit(fin[season][0]) - logit(fin[season][1])
                elif kind == "E":
                    gr, er = era_rates[int(era_of(season))]
                    v = logit(gr) - logit(er)
                elif kind in ("M1", "M2"):
                    if kind == "M2":
                        hl, K = par
                        f = 0.5 ** (gap / hl)
                        sg_, se_, sn_ = sg_ * f, se_ * f, sn_ * f
                        st[n] = [sg_, se_, sn_]
                    else:
                        K = par
                    v = logit((sg_ + K * gp) / (sn_ + K)) - logit((se_ + K * ep) / (sn_ + K))
                else:
                    raise ValueError(kind)
                out[n][ix] = v
            for n in specs:
                st[n] = [st[n][0] + G[ix].sum(0), st[n][1] + E[ix].sum(0), st[n][2] + N[ix].sum(0)]
            prev_date = d
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"),
                         "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    assert_pregame(meta)
    return meta, out


def level_frame(meta: pd.DataFrame, D: np.ndarray, name: str) -> pd.DataFrame:
    f = meta[["game_id", "season", "created_at", "puck_drop"]].copy()
    f.insert(1, "construction", name)
    for g in range(N_LG):
        f[f"d_{g}"] = D[:, g]
    return f


def row_delta(rows: pd.DataFrame, level: pd.DataFrame) -> np.ndarray:
    L = level.set_index("game_id")[[f"d_{g}" for g in range(N_LG)]].reindex(rows.game_id.to_numpy()).to_numpy()
    if np.isnan(L).any():
        raise ValueError("rows without a level")
    return L[np.arange(len(rows)), rows.lg.to_numpy()]


def c0_logit(rows: pd.DataFrame, T: np.ndarray, level: pd.DataFrame) -> np.ndarray:
    return logit(table_prob(rows, T)) + row_delta(rows, level)


# --------------------------------------------------------------------------------------------------- ratings
def asof_oe_ratings(rows: pd.DataFrame, p_c0: np.ndarray, key: str, b: float, w: float, sign: float,
                    weighted_centre: bool) -> pd.DataFrame:
    """As-of shrunk observed / expected rating per entity (`key` = goalie_id or team_id), relative to the snapshot
    league mean (L1). For an entity j at a snapshot (games dated strictly earlier, same season):
        r_j = sign * [ log((Y_j + b ebar exp(w prior_j)) / (E_j + b ebar)) - centre ],
    Y = goals, E = summed C0 probability, N = SOG over the entity's rows to date; ebar = league E / N to date (last
    season's at the season start); prior_j = last season's final value of the log ratio (0 for an entity without one);
    b = prior strength in SOG. centre = mean of the log ratio over entities: unweighted over all entities seen so far
    (teams), or weighted by (season-to-date N + last season's N) (goalies; `weighted_centre`).
    -> (game_id, key) -> r, created_at, puck_drop, for every (game, entity) present in rows."""
    x = pd.DataFrame({"game_id": rows.game_id.to_numpy(), "season": rows.season.to_numpy(), "date": rows.date.to_numpy(),
                      "drop": rows["drop"].to_numpy(), "k": rows[key].to_numpy(), "y": rows.y.to_numpy().astype(float),
                      "e": p_c0})
    L = x.groupby(["game_id", "k"], sort=False).agg(season=("season", "first"), date=("date", "first"),
                                                     drop=("drop", "first"), Y=("y", "sum"), E=("e", "sum"),
                                                     N=("y", "size")).reset_index()
    ents = np.sort(L.k.unique())
    eix = pd.Series(np.arange(len(ents)), index=ents)
    L["ei"] = eix.reindex(L.k.to_numpy()).to_numpy()
    out = []
    prev_val = np.zeros(len(ents))
    prev_has = np.zeros(len(ents), bool)
    prev_N = np.zeros(len(ents))
    prev_ebar = float(L.E.sum() / L.N.sum())
    last_drop = None
    for season in sorted(L.season.unique()):
        S = L[L.season == season]
        Y, E, Nn = np.zeros(len(ents)), np.zeros(len(ents)), np.zeros(len(ents))
        pri = np.where(prev_has, prev_val, 0.0)
        seen = prev_has.copy()

        def snap():
            ebar = E.sum() / Nn.sum() if Nn.sum() > 0 else prev_ebar
            lr = np.log((Y + b * ebar * np.exp(w * pri)) / (E + b * ebar))
            if weighted_centre:
                wt = Nn + prev_N
                c = (wt * lr).sum() / wt.sum()
            else:
                c = lr[seen].mean()
            return lr, lr - c

        for d in np.sort(S.date.unique()):
            lr, rel = snap()
            day = S[S.date == d]
            ei = day.ei.to_numpy()
            seen[ei] = True
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            out.append(pd.DataFrame({"game_id": day.game_id.to_numpy(), key: day.k.to_numpy(), "r": sign * rel[ei],
                                     "created_at": created, "puck_drop": pd.to_datetime(day["drop"], utc=True)}))
            np.add.at(Y, ei, day.Y.to_numpy())
            np.add.at(E, ei, day.E.to_numpy())
            np.add.at(Nn, ei, day.N.to_numpy(float))
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        lr, rel = snap()
        played = Nn > 0
        prev_val = np.where(played, rel, 0.0)
        prev_has = played
        prev_N = Nn.copy()
        prev_ebar = E.sum() / Nn.sum()
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    assert_pregame(r)
    return r


def attach_rating(rows: pd.DataFrame, rt: pd.DataFrame, key: str) -> np.ndarray:
    v = rows[["game_id", key]].merge(rt[["game_id", key, "r"]], on=["game_id", key], how="left", validate="many_to_one")
    if v.r.isna().any():
        raise ValueError(f"rows without a {key} rating")
    return v.r.to_numpy()


def rkey(b, w):
    return f"b{int(b)}_w{float(w)}"
