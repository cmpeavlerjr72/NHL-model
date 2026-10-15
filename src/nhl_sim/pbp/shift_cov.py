import numpy as np


def game_cov(args):
    gid, shg, evg, tid_home = args
    out = dict(game_id=gid, has_shifts=len(shg) > 0)
    if len(shg) == 0:
        return out
    T = 3600
    skat = shg[(shg.position != "G") & shg.start_s.notna() & shg.end_s.notna()]
    nopos = shg.position.isna().sum()
    out["shift_rows_no_position"] = int(nopos)
    hk = np.zeros(T + 2)
    ak = np.zeros(T + 2)
    for team_is_home, arr in ((True, hk), (False, ak)):
        d = skat[(skat.team_id == tid_home) == team_is_home]
        s = np.clip(d.start_s.values.astype(int), 0, T)
        e = np.clip(d.end_s.values.astype(int), 0, T)
        np.add.at(arr, s, 1)
        np.add.at(arr, e, -1)
    hk, ak = np.cumsum(hk)[:T], np.cumsum(ak)[:T]
    e = evg[evg.situation_code.notna() & (evg.game_time_s < T)].sort_values("sort_order")
    gt_ = e.game_time_s.values
    idx = np.searchsorted(gt_, np.arange(T) + 0.5, side="right") - 1
    ok = idx >= 0
    idx = np.clip(idx, 0, None)
    hs_, as_ = e.home_skaters.values[idx], e.away_skaters.values[idx]
    gin = (e.home_goalie.values[idx] == 1) & (e.away_goalie.values[idx] == 1)
    ok &= True
    # cap: a goalie-pulled period has 6 skaters; compare skater counts directly
    match = (hk == hs_) & (ak == as_) & ok
    v55 = (hs_ == 5) & (as_ == 5) & gin & ok
    out.update(n_sec=int(ok.sum()), n_match=int(match.sum()), n_55=int(v55.sum()),
               n_55_match=int((match & v55).sum()),
               n_either_ge5_each=int(((hk >= 5) & (ak >= 5) & ok).sum()))
    return out


