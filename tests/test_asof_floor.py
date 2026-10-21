"""AS-1 (INV-62): prior-precision floor for the as-of response scale, both instances.

- floor=None reproduces the pre-AS-1 modules (git 16f877f) bit-for-bit;
- leakage tests on the floored construction: the flip test, the first-date test, the within-day shuffle;
- the floor binds on the near-zero-rating start and not once the ratings carry spread.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nhl_sim.goal import scale as GS
from nhl_sim.shot_attribute import scale as QS

ROOT = Path(__file__).resolve().parents[1]
PRE = "16f877f"
K = 12
F = 0.5


def _old(rel, name, tmp_path):
    try:
        src = subprocess.run(["git", "show", f"{PRE}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout
    except Exception:  # pragma: no cover
        pytest.skip("git history not available")
    p = tmp_path / f"{name}.py"
    p.write_bytes(src)
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------ goalie (1 slope)
def _gframe(seed=0, n_days=40, per_day=300, ramp=True):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-10-07", periods=n_days, freq="D")
    date = np.repeat(days.strftime("%Y-%m-%d").to_numpy(), per_day)
    drop = pd.to_datetime(np.repeat(days, per_day)).tz_localize("UTC") + pd.Timedelta(hours=23)
    k = np.repeat(np.arange(n_days), per_day)
    z = rng.normal(size=len(date)) * (np.minimum(1.0, (k / 10.0) ** 2) if ramp else 1.0)   # spread grows from 0
    off = np.full(len(date), -2.3)
    y = (rng.random(len(date)) < 1 / (1 + np.exp(-(off - 0.4 * z)))).astype(float)
    return date, drop, y, off, z


def _gfloor(off, z):
    return (F, GS.info_ref(None, off, z / np.abs(z).std()))


def test_goalie_none_matches_pre_as1(tmp_path):
    old = _old("src/nhl_sim/goal/scale.py", "goal_scale_pre_as1", tmp_path)
    date, drop, y, off, z = _gframe()
    for H, P in ((90, 2000), (365, 10000)):
        a = GS.asof_scale(date, drop, y, off, z, H=H, P=P)
        b = old.asof_scale(date, drop, y, off, z, H=H, P=P)
        assert list(a.columns) == list(b.columns)
        np.testing.assert_array_equal(a.s.to_numpy(), b.s.to_numpy())
        np.testing.assert_array_equal(a.n_eff.to_numpy(), b.n_eff.to_numpy())


def test_goalie_floor_uses_only_earlier_shots():
    date, drop, y, off, z = _gframe()
    fl = (F, GS.info_ref(None, off[-3000:], z[-3000:]))
    base = GS.asof_scale(date, drop, y, off, z, H=90, P=2000, floor=fl)
    cut = "2022-10-27"
    later = date >= cut
    y2, z2 = y.copy(), z.copy()
    y2[later] = 1 - y2[later]
    z2[later] = -z2[later]
    alt = GS.asof_scale(date, drop, y2, off, z2, H=90, P=2000, floor=fl)
    keep = (base.date <= pd.Timestamp(cut)).to_numpy()
    np.testing.assert_array_equal(base.s[keep].to_numpy(), alt.s[keep].to_numpy())
    assert not np.allclose(base.s[~keep].to_numpy(), alt.s[~keep].to_numpy())


def test_goalie_floor_first_date_shuffle_and_binding():
    date, drop, y, off, z = _gframe(1)
    fl = (F, GS.info_ref(None, off[-3000:], z[-3000:]))
    f = GS.asof_scale(date, drop, y, off, z, H=90, P=2000, floor=fl)
    assert f.s.iloc[0] == GS.S0 and f.n_before.iloc[0] == 0
    m = f.created_at.notna()
    assert (f.created_at[m] < f.first_drop[m]).all()
    assert f.floor_binds.iloc[2:5].all() and not f.floor_binds.iloc[-5:].any()
    unf = GS.asof_scale(date, drop, y, off, z, H=90, P=2000)
    assert np.abs(f.s.iloc[:10]).max() < np.abs(unf.s.iloc[:10]).max()     # the start-up spike is damped
    p = np.random.default_rng(5).permutation(len(date))
    g = GS.asof_scale(date[p], drop[p], y[p], off[p], z[p], H=90, P=2000, floor=fl)
    np.testing.assert_allclose(f.s.to_numpy(), g.s.to_numpy(), rtol=0, atol=1e-10)


# ------------------------------------------------------------------------------------------------ stage 4 (2 slopes)
def _qframe(seed=0, n_days=40, per_day=300, ramp=True):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2022-10-07", periods=n_days, freq="D")
    date = np.repeat(days.strftime("%Y-%m-%d").to_numpy(), per_day)
    drop = pd.to_datetime(np.repeat(days, per_day)).tz_localize("UTC") + pd.Timedelta(hours=23)
    n = len(date)
    Cg = rng.normal(0, 1.0, (3, K))
    Cg -= Cg.mean(1, keepdims=True)
    C = Cg[rng.integers(0, 3, n)]
    A = rng.normal(0, 0.7, (n, K))
    k = np.repeat(np.arange(n_days), per_day)
    sc = np.minimum(1.0, (k / 10.0) ** 2) if ramp else 1.0
    zf, za = rng.normal(size=n) * sc, rng.normal(size=n) * sc
    Z = A + (0.06 * zf - 0.04 * za)[:, None] * C
    p = np.exp(Z - Z.max(1, keepdims=True))
    p /= p.sum(1, keepdims=True)
    y = (p.cumsum(1) < rng.random(n)[:, None]).sum(1)
    return date, drop, A, C, y, zf, za


def _s(f):
    return f[["s_for", "s_against"]].to_numpy()


def test_stage4_none_matches_pre_as1(tmp_path):
    old = _old("src/nhl_sim/shot_attribute/scale.py", "sq_scale_pre_as1", tmp_path)
    date, drop, A, C, y, zf, za = _qframe(3, n_days=25, per_day=200)
    for H, P in ((45, 10000), (365, 2000)):
        for fn in ("asof_scale", "asof_scale_exact"):
            a = getattr(QS, fn)(date, drop, A, C, y, zf, za, H=H, P=P)
            b = getattr(old, fn)(date, drop, A, C, y, zf, za, H=H, P=P)
            assert list(a.columns) == list(b.columns)
            np.testing.assert_array_equal(_s(a), _s(b))
            np.testing.assert_array_equal(a.n_exact.to_numpy(), b.n_exact.to_numpy())


def _qfloor(A, C, zf, za):
    return (F, QS.info_ref(A[-3000:], C[-3000:], zf[-3000:], za[-3000:]))


def test_stage4_floor_uses_only_earlier_attempts():
    date, drop, A, C, y, zf, za = _qframe()
    fl = _qfloor(A, C, zf, za)
    for fn in (QS.asof_scale, QS.asof_scale_exact):
        base = fn(date, drop, A, C, y, zf, za, H=90, P=2000, floor=fl)
        cut = "2022-10-27"
        later = date >= cut
        y2, zf2, za2 = y.copy(), zf.copy(), za.copy()
        y2[later] = K - 1 - y2[later]
        zf2[later], za2[later] = -zf2[later], -za2[later]
        alt = fn(date, drop, A, C, y2, zf2, za2, H=90, P=2000, floor=fl)
        keep = (base.date <= pd.Timestamp(cut)).to_numpy()
        np.testing.assert_array_equal(_s(base)[keep], _s(alt)[keep])
        assert not np.allclose(_s(base)[~keep], _s(alt)[~keep])


def test_stage4_floor_first_date_shuffle_binding_and_series():
    date, drop, A, C, y, zf, za = _qframe(1)
    fl = _qfloor(A, C, zf, za)
    f = QS.asof_scale(date, drop, A, C, y, zf, za, H=45, P=10000, floor=fl)
    assert (_s(f)[0] == 0.0).all() and f.n_before.iloc[0] == 0
    m = f.created_at.notna()
    assert (f.created_at[m] < f.first_drop[m]).all()
    assert f.floor_binds.iloc[2:5].all() and not f.floor_binds.iloc[-5:].any()
    p = np.random.default_rng(5).permutation(len(date))
    g = QS.asof_scale(date[p], drop[p], A[p], C[p], y[p], zf[p], za[p], H=45, P=10000, floor=fl)
    np.testing.assert_allclose(_s(f), _s(g), rtol=0, atol=1e-10)
    e = QS.asof_scale_exact(date, drop, A, C, y, zf, za, H=45, P=10000, floor=fl)
    np.testing.assert_allclose(_s(f), _s(e), rtol=0, atol=1e-9)
