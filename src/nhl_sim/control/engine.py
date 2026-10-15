"""Control R1 engine (INV-6): as-of ridge Poisson team ratings + score models A0-A4. Spec: docs/models/control/experiments.md R1.

Season ids are NHL ids (20212022). ARI and UTA are one franchise index. Reads data only through nhl_sim.data.load.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import gammaln

from nhl_sim.data.load import load_goalie_box, load_verified_finals

SEASONS = [20212022, 20222023, 20232024, 20242025]
N = 18        # final-score grid 0..17
NR = 17       # regulation grid 0..16
GK_SCALE = 100.0


# ----------------------------------------------------------------------------- data
@dataclass
class Data:
    g: pd.DataFrame          # one row per game, sorted by (date, game_id)
    teams: list[str]


def build_data() -> Data:
    f = load_verified_finals("v2", seasons=SEASONS).copy()
    f["home"] = f.home.replace({"UTA": "ARI"})
    f["away"] = f.away.replace({"UTA": "ARI"})
    teams = sorted(set(f.home) | set(f.away))
    ix = {t: i for i, t in enumerate(teams)}
    so_h = ((f.end_state == "SO") & (f.home_score > f.away_score)).astype(int)
    so_a = ((f.end_state == "SO") & (f.away_score > f.home_score)).astype(int)
    g = pd.DataFrame({"game_id": f.game_id, "season": f.season, "gtype": f.game_type, "date": f.game_date_local,
                      "h": f.home.map(ix), "a": f.away.map(ix), "hg": f.home_score - so_h, "ag": f.away_score - so_a,
                      "end_state": f.end_state, "home_win": f.home_score > f.away_score})
    ot_h = (g.end_state == "OT") & (g.hg > g.ag)
    ot_a = (g.end_state == "OT") & (g.ag > g.hg)
    g["reg_h"] = g.hg - ot_h.astype(int)
    g["reg_a"] = g.ag - ot_a.astype(int)
    g = g.sort_values(["date", "game_id"]).reset_index(drop=True)

    # starters (oracle: post-game flag) and their as-of cumulative save counts
    gb = load_goalie_box(SEASONS, columns=["game_id", "is_home", "player_id", "starter", "shots_against", "saves"])
    st = gb[gb.starter].drop_duplicates(["game_id", "is_home"])
    hs = st[st.is_home].set_index("game_id").player_id
    as_ = st[~st.is_home].set_index("game_id").player_id
    g["h_gk"] = g.game_id.map(hs)
    g["a_gk"] = g.game_id.map(as_)
    sa = gb.groupby(["game_id", "player_id"])[["shots_against", "saves"]].sum()
    cum: dict[int, list[float]] = {}
    lg = [0.0, 0.0]
    cols = {k: np.zeros(len(g)) for k in ("h_sv", "h_sa", "a_sv", "a_sa", "lg_sv")}
    dates = g.date.to_numpy()
    i = 0
    while i < len(g):
        j = i
        while j < len(g) and dates[j] == dates[i]:
            j += 1
        for k in range(i, j):          # features use only games before this date
            for side in ("h", "a"):
                pid = g.at[k, f"{side}_gk"]
                c = cum.get(pid, [0.0, 0.0])
                cols[f"{side}_sv"][k], cols[f"{side}_sa"][k] = c[0], c[1]
            cols["lg_sv"][k] = lg[0] / lg[1] if lg[1] > 0 else 0.9
        for k in range(i, j):          # then add today's games
            for side in ("h", "a"):
                pid = g.at[k, f"{side}_gk"]
                try:
                    r = sa.loc[(g.at[k, "game_id"], pid)]
                except KeyError:
                    continue
                c = cum.setdefault(pid, [0.0, 0.0])
                c[0] += r.saves
                c[1] += r.shots_against
                lg[0] += r.saves
                lg[1] += r.shots_against
        i = j
    for k, v in cols.items():
        g[k] = v

    # rest: back-to-back (played the previous calendar day) and long rest (>=4 days), previous season included
    last: dict[int, pd.Timestamp] = {}
    d = pd.to_datetime(g.date)
    rest = {k: np.zeros(len(g)) for k in ("h_b2b", "a_b2b", "h_long", "a_long")}
    for k in range(len(g)):
        for side in ("h", "a"):
            t = g.at[k, side]
            if t in last:
                days = (d[k] - last[t]).days
                rest[f"{side}_b2b"][k] = float(days == 1)
                rest[f"{side}_long"][k] = float(days >= 4)
    # update after reading: need strictly earlier games only, so recompute with a second pass in date order
    last = {}
    rest = {k: np.zeros(len(g)) for k in rest}
    for k in range(len(g)):
        for side in ("h", "a"):
            t = g.at[k, side]
            if t in last:
                days = (d[k] - last[t]).days
                rest[f"{side}_b2b"][k] = float(days == 1)
                rest[f"{side}_long"][k] = float(days >= 4)
        for side in ("h", "a"):
            last[g.at[k, side]] = d[k]
    for k, v in rest.items():
        g[k] = v

    # as-of end-game rates (all earlier dates, prior-smoothed): P(home wins | OT/SO), OT share of OT/SO
    ph = np.zeros(len(g))
    qo = np.zeros(len(g))
    n_ot = n_so = hw = 0
    i = 0
    while i < len(g):
        j = i
        while j < len(g) and dates[j] == dates[i]:
            j += 1
        n = n_ot + n_so
        ph[i:j] = (hw + 5) / (n + 10)
        qo[i:j] = (n_ot + 3) / (n + 6)
        for k in range(i, j):
            if g.at[k, "end_state"] in ("OT", "SO"):
                n_ot += g.at[k, "end_state"] == "OT"
                n_so += g.at[k, "end_state"] == "SO"
                hw += bool(g.at[k, "home_win"])
        i = j
    g["p_home_tie"] = ph
    g["q_ot"] = np.where(g.gtype == 3, 1.0, qo)   # playoffs have no shootout (rule)
    return Data(g, teams)


# ----------------------------------------------------------------------------- ratings
DESIGNS = {"base": [], "gk": ["z"], "gkrest": ["z", "own_b2b", "opp_b2b", "own_long", "opp_long"]}


def team_rows(g: pd.DataFrame, T: int, design: str, kappa: float):
    """Design matrix for the 2 team-rows per game (home row then away row). Columns: mu, home, extras, off(T), def(T)."""
    n = len(g)
    ex = DESIGNS[design]
    p = 2 + len(ex) + 2 * T
    X = np.zeros((2 * n, p))
    X[:, 0] = 1.0
    X[0::2, 1] = 1.0
    rr = np.arange(n)
    X[2 * rr, 2 + len(ex) + g.h.to_numpy()] = 1.0
    X[2 * rr + 1, 2 + len(ex) + g.a.to_numpy()] = 1.0
    X[2 * rr, 2 + len(ex) + T + g.a.to_numpy()] = 1.0
    X[2 * rr + 1, 2 + len(ex) + T + g.h.to_numpy()] = 1.0
    if "z" in ex:
        lg = g.lg_sv.to_numpy()
        def shrunk(sv, sa):
            sv_rate = np.divide(sv, sa, out=np.full_like(sv, np.nan), where=sa > 0)
            return (np.nan_to_num(sv_rate * sa, nan=0.0) + kappa * lg) / (sa + kappa)
        zh = (lg - shrunk(g.a_sv.to_numpy(), g.a_sa.to_numpy())) * GK_SCALE   # home row faces away starter
        za = (lg - shrunk(g.h_sv.to_numpy(), g.h_sa.to_numpy())) * GK_SCALE
        X[0::2, 2 + ex.index("z")] = zh
        X[1::2, 2 + ex.index("z")] = za
    for nm, a_, b_ in (("own_b2b", "h_b2b", "a_b2b"), ("opp_b2b", "a_b2b", "h_b2b"),
                       ("own_long", "h_long", "a_long"), ("opp_long", "a_long", "h_long")):
        if nm in ex:
            X[0::2, 2 + ex.index(nm)] = g[a_].to_numpy()
            X[1::2, 2 + ex.index(nm)] = g[b_].to_numpy()
    y = np.empty(2 * n)
    y[0::2] = g.hg.to_numpy()
    y[1::2] = g.ag.to_numpy()
    return X, y


def _newton(X, y, pen, m, th0, iters=30):
    if len(y) == 0:
        return m.copy()
    th = th0.copy()
    for _ in range(iters):
        eta = np.clip(X @ th, -4, 4) if len(y) else np.zeros(0)
        mu = np.exp(eta)
        A = (X * mu[:, None]).T @ X + np.diag(pen)
        z = eta + (y - mu) / mu
        b = (X * mu[:, None]).T @ z + pen * m
        new = np.linalg.solve(A, b)
        done = np.max(np.abs(new - th)) < 1e-7
        th = new
        if done:
            break
    return th


def _center(th, T, k):
    o = 2 + k
    mo, md = th[o:o + T].mean(), th[o + T:o + 2 * T].mean()
    th = th.copy()
    th[o:o + T] -= mo
    th[o + T:o + 2 * T] -= md
    th[0] += mo + md
    return th


class Chain:
    """Season-by-season ridge chain for one (design, lambda, carry w, kappa)."""

    def __init__(self, data: Data, design: str, lam: float, w: float, kappa: float = 500.0):
        self.d, self.design, self.lam, self.w, self.kappa = data, design, lam, w, kappa
        self.T = len(data.teams)
        self.k = len(DESIGNS[design])
        self.p = 2 + self.k + 2 * self.T
        self._final: dict[int, np.ndarray] = {}
        self._X: dict[int, tuple] = {}

    def _season(self, s):
        if s not in self._X:
            gs = self.d.g[self.d.g.season == s].reset_index(drop=True)
            self._X[s] = (gs, *team_rows(gs, self.T, self.design, self.kappa))
        return self._X[s]

    def _prior(self, s):
        prev = SEASONS.index(s) - 1
        if prev < 0:
            th = np.zeros(self.p)
            th[0] = np.log(3.0)
            return th, np.zeros(self.p)
        thp = self.final(SEASONS[prev])
        m = thp.copy()
        o = 2 + self.k
        m[o:] = self.w * thp[o:]
        return thp, m

    def _pen(self):
        pen = np.full(self.p, float(self.lam))
        pen[:2 + self.k] = 1e-3
        return pen

    def final(self, s):
        if s not in self._final:
            gs, X, y = self._season(s)
            _, m = self._prior(s)
            th = _center(_newton(X, y, self._pen(), m, m), self.T, self.k)
            self._final[s] = th
        return self._final[s]

    def asof(self, s) -> pd.DataFrame:
        """As-of predictions for every game of season s (fit uses only games on earlier dates)."""
        gs, X, y = self._season(s)
        _, m = self._prior(s)
        pen = self._pen()
        dates = gs.date.to_numpy()
        lam_h = np.zeros(len(gs)); lam_a = np.zeros(len(gs))
        strength = np.zeros((len(gs), 2))
        th = m.copy()
        i = 0
        o = 2 + self.k
        while i < len(gs):
            j = i
            while j < len(gs) and dates[j] == dates[i]:
                j += 1
            nr = 2 * i       # rows from games strictly before this date
            th = _center(_newton(X[:nr], y[:nr], pen, m, th if nr else m), self.T, self.k)
            eta = X[2 * i:2 * j] @ th
            lam_h[i:j] = np.exp(eta[0::2])
            lam_a[i:j] = np.exp(eta[1::2])
            net = th[o:o + self.T] - th[o + self.T:o + 2 * self.T]   # off minus def (def high = leaky)
            strength[i:j, 0] = net[gs.h.to_numpy()[i:j]]
            strength[i:j, 1] = net[gs.a.to_numpy()[i:j]]
            i = j
        out = gs[["game_id"]].copy()
        out["lam_h"], out["lam_a"] = lam_h, lam_a
        out["net_h"], out["net_a"] = strength[:, 0], strength[:, 1]
        return out


# ----------------------------------------------------------------------------- score models
def _pois(lam: np.ndarray, n: int) -> np.ndarray:
    k = np.arange(n)
    return np.exp(-lam[:, None] + k * np.log(np.maximum(lam[:, None], 1e-12)) - gammaln(k + 1))


def reg_pmf(arm: str, lh, la, par: dict) -> np.ndarray:
    """Regulation-score pmf, shape (G, NR, NR), renormalised on the grid."""
    lh, la = np.asarray(lh, float), np.asarray(la, float)
    if arm in ("A0", "A1"):
        P = _pois(lh, NR)[:, :, None] * _pois(la, NR)[:, None, :]
    elif arm == "A2":
        l3 = np.minimum(par["lambda3"], 0.95 * np.minimum(lh, la))
        l1, l2 = lh - l3, la - l3
        p1, p2, p3 = _pois(l1, NR), _pois(l2, NR), _pois(l3, NR)
        P = np.zeros((len(lh), NR, NR))
        for z in range(NR):
            a = np.zeros_like(p1); b = np.zeros_like(p2)
            a[:, z:] = p1[:, :NR - z]
            b[:, z:] = p2[:, :NR - z]
            P += p3[:, z, None, None] * a[:, :, None] * b[:, None, :]
    elif arm in ("A3", "A4"):
        r = 1.0 / max(par["phi"], 1e-9)
        x = np.arange(NR)[None, :, None]
        y = np.arange(NR)[None, None, :]
        s = (r + lh + la)[:, None, None]
        lp = (gammaln(r + x + y) - gammaln(r) - gammaln(x + 1) - gammaln(y + 1) + r * np.log(r / s)
              + x * np.log(lh[:, None, None] / s) + y * np.log(la[:, None, None] / s))
        P = np.exp(lp)
    else:
        raise ValueError(arm)
    return P / P.sum(axis=(1, 2), keepdims=True)


def final_pmf(reg: np.ndarray, q_ot, p_home) -> tuple[np.ndarray, np.ndarray]:
    """Apply the end-game model. Returns (final pmf (G,N,N) with OT goal and no SO goal, P(home wins))."""
    G = reg.shape[0]
    F = np.zeros((G, N, N))
    F[:, :NR, :NR] = reg
    k = np.arange(NR)
    tie = reg[:, k, k]
    q = np.asarray(q_ot)[:, None]
    ph = np.asarray(p_home)[:, None]
    F[:, k, k] = tie * (1 - q)
    F[:, k + 1, k] += tie * q * ph
    F[:, k, k + 1] += tie * q * (1 - ph)
    hi = np.triu(np.ones((N, N)), 1).astype(bool)      # a > h
    lo = np.tril(np.ones((N, N)), -1).astype(bool)     # h > a
    pw = F[:, lo].sum(1) + (tie * (1 - q) * ph).sum(1)
    return F, pw


def fit_lambda3(arm_rates, reg_h, reg_a) -> float:
    from scipy.optimize import minimize_scalar
    lh, la = arm_rates
    def nll(l3):
        P = reg_pmf("A2", lh, la, {"lambda3": l3})
        return -np.log(np.maximum(P[np.arange(len(lh)), reg_h, reg_a], 1e-300)).sum()
    return float(minimize_scalar(nll, bounds=(0.0, 1.0), method="bounded", options={"xatol": 1e-4}).x)


def fit_phi(arm_rates, reg_h, reg_a) -> float:
    from scipy.optimize import minimize_scalar
    lh, la = arm_rates
    def nll(lphi):
        P = reg_pmf("A3", lh, la, {"phi": np.exp(lphi)})
        return -np.log(np.maximum(P[np.arange(len(lh)), reg_h, reg_a], 1e-300)).sum()
    r = minimize_scalar(nll, bounds=(np.log(1e-4), np.log(1.0)), method="bounded", options={"xatol": 1e-3})
    return float(np.exp(r.x))


def logscore(F: np.ndarray, hg, ag) -> np.ndarray:
    hg, ag = np.minimum(hg, N - 1), np.minimum(ag, N - 1)
    return np.log(np.maximum(F[np.arange(len(hg)), hg, ag], 1e-12))


def sample_final(arm, lh, la, q_ot, p_home, par, n_seeds, seed):
    """Draw n_seeds (home_goals, away_goals, end_state, home_win) per game from the arm's distribution."""
    rng = np.random.default_rng(seed)
    reg = reg_pmf(arm, lh, la, par)
    G = len(lh)
    flat = reg.reshape(G, -1).cumsum(1)
    u = rng.random((G, n_seeds))
    idx = np.array([np.searchsorted(flat[i], u[i]) for i in range(G)]).clip(0, NR * NR - 1)
    h, a = idx // NR, idx % NR
    tied = h == a
    ot = tied & (rng.random((G, n_seeds)) < np.asarray(q_ot)[:, None])
    so = tied & ~ot
    hw_tie = rng.random((G, n_seeds)) < np.asarray(p_home)[:, None]
    h = h + (ot & hw_tie)
    a = a + (ot & ~hw_tie)
    home_win = np.where(tied, hw_tie, h > a)
    es = np.where(so, "SO", np.where(ot, "OT", "REG"))
    return h, a, es, home_win


