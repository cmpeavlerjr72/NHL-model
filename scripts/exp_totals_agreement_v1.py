"""LT-R1 / INV-25: price-adjusted totals agreement, ESPN BET vs DRatings. Spec: docs/models/lines_totals/experiments.md.
Run: PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/exp_totals_agreement_v1.py
Outputs: results/lt_r1/*.csv, results/lt_r1/*.json (results/ is gitignored); report text is written by hand from these."""
import json, os
import numpy as np, pandas as pd

OUT = "results/lt_r1"; os.makedirs(OUT, exist_ok=True)
VIG_BAND = (1.00, 1.10)   # fixed before any result was read (same band as the D11 ML check)
MIN_LOOKUP_N = 30         # lookup cell (DRatings line) must have >= 30 games to convert into it
TEST = {20232024: "2023-24", 20242025: "2024-25"}
TRAIN = [20212022, 20222023]


def imp(a):
    a = np.asarray(a, float)
    return np.where(a < 0, -a / (-a + 100.0), 100.0 / (a + 100.0))


def american_of_prob(p):
    return -100 * p / (1 - p) if p > .5 else 100 * (1 - p) / p


fin = pd.read_parquet("data/reference/verified_finals_v2.parquet")
fin = fin[fin.verified_v2][["game_id", "season", "game_type", "game_date_local", "home_score", "away_score"]]
fin["T"] = fin.home_score + fin.away_score   # verified finals already add 1 to the shootout winner (checked: all SO |diff| == 1)

dr = pd.read_parquet("data/processed/lines_dratings_v1.parquet")
dn = dr[(dr.market == "total") & (dr.field == "novig_close")].pivot_table(
    index="game_id", columns="side", values=["line", "price"], aggfunc="first")
D = pd.DataFrame({"L_D": dn[("line", "over")], "L_D_u": dn[("line", "under")],
                  "po": imp(dn[("price", "over")]), "pu": imp(dn[("price", "under")])}).reset_index()
assert (D.L_D == D.L_D_u).all()
D["P_D"] = D.po / (D.po + D.pu)          # no-vig P(over | no push) at the DRatings line
D["D_sum"] = D.po + D.pu
D = D.merge(fin, on="game_id", how="inner")

# ---- ESPN BET (provider 58) close total
e = pd.read_parquet("data/processed/lines_espn_core_v1.parquet")
e = e[(e.market == "total") & (e.provider_id == "58")]
eo = e[e.side_or_line == "over"].set_index("game_id"); eu = e[e.side_or_line == "under"].set_index("game_id")
E = pd.DataFrame({"L_E": eo.close_line, "L_E_u": eu.close_line, "pe_o": imp(eo.close_price), "pe_u": imp(eu.close_price),
                  "price_o": eo.close_price, "price_u": eu.close_price}).reset_index()
E.loc[E.price_o.isna(), "pe_o"] = np.nan
E.loc[E.price_u.isna(), "pe_u"] = np.nan

# ================= STEP 1: the -68 =================
s1 = {}
m = E.merge(D[["game_id", "L_D", "season"]], on="game_id")
m = m[m.season.isin(TEST)]
m["gap"] = (m.L_E - m.L_D).round(1)
for g, lab in [(0.0, "equal"), (-0.5, "E lower"), (0.5, "E higher")]:
    x = m[(m.gap == g) & m.price_o.notna()]
    mi = float(x.pe_o.mean())
    s1[lab] = dict(n=int(len(x)), mean_american=float(x.price_o.mean()), median_american=float(x.price_o.median()),
                   mean_implied=mi, american_of_mean_implied=float(american_of_prob(mi)),
                   frac_plus_money=float((x.price_o > 0).mean()), frac_minus=float((x.price_o < 0).mean()),
                   mean_of_minus_only=float(x.price_o[x.price_o < 0].mean()),
                   mean_of_plus_only=float(x.price_o[x.price_o > 0].mean()))
# also the 112-game sample from the 2026-10-15 cross-check
cs = pd.read_csv("data/processed/lines_crosscheck_espn_dratings_v1.csv")
s1["_crosscheck_cols"] = list(cs.columns)
json.dump(s1, open(f"{OUT}/step1_minus68.json", "w"), indent=1, default=float)
print("STEP1", json.dumps(s1, indent=1, default=float))

# ================= STEP 2: lookup from 2021-22 + 2022-23 =================
tr = D[D.season.isin(TRAIN)]
look = {}
for L, g in tr.groupby("L_D"):
    vc = g["T"].value_counts()
    look[float(L)] = dict(n=int(len(g)), pmf={int(k): float(v / len(g)) for k, v in vc.items()})
rows = []
for L, d in sorted(look.items()):
    for k in range(0, 13):
        rows.append(dict(line=L, n=d["n"], k=k, p_T_eq_k=d["pmf"].get(k, 0.0)))
pd.DataFrame(rows).to_csv(f"{OUT}/lookup_pmf.csv", index=False)
print("LOOKUP n by line:", {L: d["n"] for L, d in look.items()})


def convert(pE, LE, LD, cond_line):
    """pE: no-vig P(over | no push) at LE. Returns same quantity at LD using pmf of T given DRatings line cond_line."""
    d = look.get(float(cond_line))
    if d is None or d["n"] < MIN_LOOKUP_N:
        return None
    pm = lambda k: d["pmf"].get(int(k), 0.0)
    S = pE * (1 - pm(LE)) if LE == int(LE) else pE      # unconditional P(T > LE)
    lo, hi = min(LE, LD), max(LE, LD)
    ks = [k for k in range(int(np.floor(lo)) + 1, int(np.floor(hi)) + 1) if lo < k <= hi]
    S = S - sum(pm(k) for k in ks) if LD > LE else S + sum(pm(k) for k in ks)
    if LD == int(LD):
        S = S / (1 - pm(LD))
    return float(S) if 0 <= S <= 1 else float("nan")


# ================= STEP 3: agreement test =================
A = D.merge(E, on="game_id", how="left")
A = A[A.season.isin(TEST)].copy()
cnt = {}
for s, lab in TEST.items():
    a = A[A.season == s]; c = dict(games_dratings=int(len(a)))
    have = a.L_E.notna() & a.pe_o.notna() & a.pe_u.notna()
    c["espn_missing_total_or_price"] = int((~have).sum())
    sm = a.pe_o + a.pe_u
    c["espn_vig_outside_band"] = int((have & ((sm < VIG_BAND[0]) | (sm > VIG_BAND[1]))).sum())
    c["espn_over_under_line_mismatch"] = int((have & (a.L_E != a.L_E_u)).sum())
    c["dratings_novig_sum_not_1_info"] = int(((a.D_sum < 0.999) | (a.D_sum > 1.001)).sum())
    cnt[lab] = c
A["ok"] = (A.L_E.notna() & A.pe_o.notna() & A.pe_u.notna() & (A.L_E == A.L_E_u)
           & ((A.pe_o + A.pe_u) >= VIG_BAND[0]) & ((A.pe_o + A.pe_u) <= VIG_BAND[1]))
A["P_E"] = A.pe_o / (A.pe_o + A.pe_u)
A["gap"] = (A.L_E - A.L_D).round(1)
A["bucket"] = np.where(~A.ok, "excluded", np.where(A.gap == 0, "equal",
                       np.where(A.gap.abs().isin([0.5, 1.0]), "converted", "gt1.0")))
A["P_E_conv"] = np.where(A.bucket == "equal", A.P_E, np.nan)
A["P_E_conv_altcond"] = np.where(A.bucket == "equal", A.P_E, np.nan)
for i, r in A[A.bucket == "converted"].iterrows():
    v = convert(r.P_E, r.L_E, r.L_D, r.L_D)
    A.loc[i, "P_E_conv"] = np.nan if v is None else v
    v2 = convert(r.P_E, r.L_E, r.L_D, r.L_E)
    A.loc[i, "P_E_conv_altcond"] = np.nan if v2 is None else v2
A.loc[(A.bucket == "converted") & A.P_E_conv.isna(), "bucket"] = "converted_no_lookup"
A["diff"] = A.P_E_conv - A.P_D
A["diff_alt"] = A.P_E_conv_altcond - A.P_D
A["month"] = pd.to_datetime(A.game_date_local).dt.strftime("%Y-%m")
A["over_nopush"] = np.where(A["T"] > A.L_D, 1.0, np.where(A["T"] < A.L_D, 0.0, np.nan))
A["over_nopush_E"] = np.where(A["T"] > A.L_E, 1.0, np.where(A["T"] < A.L_E, 0.0, np.nan))
A.to_csv(f"{OUT}/agreement_rows.csv", index=False)


def stats(x, col="diff"):
    d = x[col].dropna()
    if len(d) == 0:
        return dict(n=0)
    return dict(n=int(len(d)), median_abs=float(d.abs().median()), mean_signed=float(d.mean()),
                se_mean=float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan"),
                p90_abs=float(d.abs().quantile(.9)))


res = {"counts": cnt, "bucket_counts": {}, "pass": {}}
tabs = []
for s, lab in TEST.items():
    a = A[A.season == s]
    res["bucket_counts"][lab] = {k: int(v) for k, v in a.bucket.value_counts().items()}
    res["bucket_counts"][lab + " gap counts (ok rows)"] = {str(k): int(v) for k, v in a[a.ok].gap.value_counts().sort_index().items()}
    for b in ["equal", "converted"]:
        st = stats(a[a.bucket == b])
        st["pass"] = bool(st["n"] > 0 and st["median_abs"] <= 0.02 and abs(st["mean_signed"]) <= 0.01)
        if b == "converted":
            st["sensitivity_cond_on_L_E_not_for_pass_rule"] = stats(a[a.bucket == b], "diff_alt")
        res["pass"][f"{lab}|{b}"] = st
    sub = a[a.bucket.isin(["equal", "converted"])]
    for kind in ["month", "L_D", "gap", "L_E"]:
        for (k, b), gg in sub.groupby([kind, "bucket"]):
            t = stats(gg); t.update(season=lab, by=kind, key=str(k), bucket=b); tabs.append(t)
pd.DataFrame(tabs).to_csv(f"{OUT}/breakdowns.csv", index=False)

cal = []


def calrow(season, name, x, pcol, ycol):
    x = x.dropna(subset=[pcol, ycol]); r = x[ycol].mean()
    cal.append(dict(season=season, source=name, n=len(x), mean_P=x[pcol].mean(), over_rate=r,
                    se=np.sqrt(r * (1 - r) / len(x))))


for s, lab in TEST.items():
    a = A[A.season == s]
    calrow(lab, "DRatings @L_D (all games)", a, "P_D", "over_nopush")
    calrow(lab, "ESPN BET @L_E (ok rows)", a[a.ok], "P_E", "over_nopush_E")
    sub = a[a.bucket.isin(["equal", "converted"])]
    calrow(lab, "ESPN converted @L_D (equal+converted)", sub, "P_E_conv", "over_nopush")
    calrow(lab, "DRatings @L_D (same games)", sub, "P_D", "over_nopush")
cal = pd.DataFrame(cal); cal["z"] = (cal.mean_P - cal.over_rate) / cal.se
cal.to_csv(f"{OUT}/calibration.csv", index=False)
res["pass_overall"] = bool(all(v["pass"] for v in res["pass"].values()))
json.dump(res, open(f"{OUT}/summary.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float)); print(cal.to_string())
