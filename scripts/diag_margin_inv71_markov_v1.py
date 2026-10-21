"""INV-71 (Lane D1, 2026-10-21): analytic attribution of the regulation tie excess. DIAGNOSIS ONLY (no table touched).

A symmetric margin Markov chain, one-second steps from 0-0 to 55:00, in which the team in score bucket b (trail2+,
trail1, tied, lead1, lead2+) scores at the per-team-hour goal rate lambda[period, b] (all non-EN states). Rates come
from grade.json (item 2: the closed-loop sim and the real 2024-25 rates). The chain is validated by reproducing the
sim's own and the real tie rates at 20:00 / 40:00 / 55:00; then the sim rates are divided, bucket by bucket and period by
period, by the served / actual factors of the offline conversion chain (chain.json: B0 block, S0t miss, C1s goal | SOG,
stage-4 xG, full chain), one component at a time. The change in the 55:00 tie rate is the share each component explains.
These are DIAGNOSTIC counterfactuals on rates, never a fix.

    diag_margin_inv71_markov_v1.py   -> results/diag_margin_inv71_v1/markov.json
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "diag_margin_inv71_v1"
BUCK = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
MMAX = 12


def chain(lam, T_end=3300, snaps=(1200, 2400, 3300)):
    """lam: (3 periods, 5 buckets) goals per team-hour. Returns {t: P(home margin = m), m = -MMAX..MMAX}."""
    m = np.arange(-MMAX, MMAX + 1)
    P = np.zeros(len(m))
    P[MMAX] = 1.0
    out = {}
    for t in range(T_end):
        p = min(t // 1200, 2)
        L = lam[p] / 3600.0
        lead = np.where(m == 1, L[3], L[4])
        trail = np.where(m == 1, L[1], L[0])
        ph = np.where(m > 0, lead, np.where(m < 0, np.where(m == -1, L[1], L[0]), L[2]))   # home scores
        pa = np.where(m > 0, trail, np.where(m < 0, np.where(m == -1, L[3], L[4]), L[2]))  # away scores
        new = P * (1 - ph - pa)
        new[1:] += (P * ph)[:-1]
        new[:-1] += (P * pa)[1:]
        P = new
        if t + 1 in snaps:
            out[t + 1] = P.copy()
    return out


def absdist(P):
    m = np.abs(np.arange(-MMAX, MMAX + 1))
    return [float(P[m == 0].sum()), float(P[m == 1].sum()), float(P[m == 2].sum()), float(P[m >= 3].sum())]


def main():
    G = json.loads((OUT / "grade.json").read_text())
    C = json.loads((OUT / "chain.json").read_text())
    it2 = G["item2"]
    lam_sim = np.array([it2[f"all non-EN states | P{p}"]["sim_g60"] for p in (1, 2, 3)])
    lam_real = np.array([it2[f"all non-EN states | P{p}"]["real_g60"] for p in (1, 2, 3)])
    i1 = G["item1_rs"]
    obs_sim = {lab: i1[lab]["sim"]["abs"][0] for lab in ("20:00", "40:00", "55:00")}
    obs_real = {lab: i1[lab]["real (no goalie-out goals)"]["abs"][0] for lab in ("20:00", "40:00", "55:00")}

    # component factors served / actual per period x bucket
    fac = {k: np.ones((3, 5)) for k in ("block (B0)", "miss (S0t)", "goal|SOG (C1s)", "stage 4 (L1x-as xG)", "full chain")}
    for p in (1, 2, 3):
        t = C[f"all non-EN states, P{p}"]["table"]
        for j, b in enumerate(BUCK):
            pba = t["actual block %"][b] / 100
            pbs = t["block s/a"][b] * pba
            ma = t["actual miss|unb %"][b] / 100
            ms = t["miss s/a (S0t)"][b] * ma
            fac["block (B0)"][p - 1, j] = (1 - pbs) / (1 - pba)
            fac["miss (S0t)"][p - 1, j] = (1 - ms) / (1 - ma)
            fac["goal|SOG (C1s)"][p - 1, j] = t["goal|SOG s/a (C1s)"][b]
            fac["stage 4 (L1x-as xG)"][p - 1, j] = t["xG/unb s/a (stage 4)"][b]
            fac["full chain"][p - 1, j] = t["goal/attempt s/a (full chain)"][b]
    fac["block + miss + C1s"] = fac["block (B0)"] * fac["miss (S0t)"] * fac["goal|SOG (C1s)"]
    # level-neutral versions: remove each period's mean factor so only the score SHAPE is corrected
    res = {"validation": {}, "cf": {}}
    cs, cr = chain(lam_sim), chain(lam_real)
    for T, lab in zip((1200, 2400, 3300), ("20:00", "40:00", "55:00")):
        res["validation"][lab] = dict(sim_obs=obs_sim[lab], sim_chain=absdist(cs[T])[0], real_obs=obs_real[lab],
                                      real_chain=absdist(cr[T])[0])
    print("validation (tie rate):")
    for lab, v in res["validation"].items():
        print(f"  {lab}: sim obs {v['sim_obs']:.4f} chain {v['sim_chain']:.4f} | real obs {v['real_obs']:.4f} chain {v['real_chain']:.4f}")
    gap = absdist(cs[3300])[0] - absdist(cr[3300])[0]
    print(f"chain gap at 55:00: {gap:+.4f}")
    for name, f in fac.items():
        for mode in ("shape+level", "shape only"):
            ff = f.copy()
            if mode == "shape only":
                # divide by the period's exposure-free mean factor weighted by the real goals in each bucket
                for p in (1, 2, 3):
                    gl = np.array(C[f"all non-EN states, P{p}"]["table"]["goals"][b] for b in BUCK) if False else \
                        np.array([C[f"all non-EN states, P{p}"]["table"]["goals"][b] for b in BUCK])
                    ff[p - 1] = ff[p - 1] / (gl * ff[p - 1]).sum() * gl.sum()
            cf = chain(lam_sim / ff)
            t55 = absdist(cf[3300])[0]
            t40 = absdist(cf[2400])[0]
            res["cf"][f"{name} | {mode}"] = dict(tie40=t40, tie55=t55, d55=t55 - absdist(cs[3300])[0],
                                                share=(absdist(cs[3300])[0] - t55) / gap, abs55=absdist(cf[3300]))
            r = res["cf"][f"{name} | {mode}"]
            print(f"  CF sim rates / {name:22s} [{mode:11s}]: tie 40:00 {t40:.4f}  55:00 {t55:.4f}  "
                  f"(change {r['d55']:+.4f}, share of chain gap {r['share']:+.2f})")
    # the same with the real rates swapped in bucket groups (which states carry the gap)
    for grp, idx in (("tied rates", [2]), ("trailing rates", [0, 1]), ("leading rates", [3, 4]), ("all P1 rates", None)):
        lam = lam_sim.copy()
        if idx is None:
            lam[0] = lam_real[0]
        else:
            lam[:, idx] = lam_real[:, idx]
        t55 = absdist(chain(lam)[3300])[0]
        res["cf"][f"swap real {grp}"] = dict(tie55=t55, share=(absdist(cs[3300])[0] - t55) / gap)
        print(f"  swap in real {grp:15s}: tie 55:00 {t55:.4f} share {res['cf'][f'swap real {grp}']['share']:+.2f}")
    res["factors"] = {k: v.round(4).tolist() for k, v in fac.items()}
    res["lam_sim"], res["lam_real"] = lam_sim.tolist(), lam_real.tolist()
    (OUT / "markov.json").write_text(json.dumps(res, indent=1))
    print("wrote", OUT / "markov.json")


if __name__ == "__main__":
    main()
