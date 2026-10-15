"""Counter-based RNG streams seeded on (seed, game_id, family).

Every simulation (game, seed) owns one 64-bit key per family; a uniform for (key, step, k) is a pure function of
those numbers (SplitMix64 finaliser), so two bake-off arms that share (seed, game_id, family) see identical
draws at identical steps (paired streams), independent of batch layout or of how many sims are in the batch.
"""
from __future__ import annotations

import zlib

import numpy as np

_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
_GOLD = np.uint64(0x9E3779B97F4A7C15)
_S30, _S27, _S31 = np.uint64(30), np.uint64(27), np.uint64(31)
_INV53 = 1.0 / float(1 << 53)

FAMILIES = ("penalty", "penalty_type", "goal", "stoppage", "coincidental")


def family_id(family: str) -> int:
    """Stable 32-bit id of a family name (crc32, not Python's salted hash)."""
    return zlib.crc32(family.encode("utf-8"))


def mix64(x: np.ndarray) -> np.ndarray:
    """SplitMix64 finaliser on uint64 arrays (wrapping arithmetic)."""
    x = np.asarray(x, dtype=np.uint64)
    with np.errstate(over="ignore"):
        z = x + _GOLD
        z = (z ^ (z >> _S30)) * _M1
        z = (z ^ (z >> _S27)) * _M2
        return z ^ (z >> _S31)


def stream_keys(seeds, game_ids, family: str) -> np.ndarray:
    """One uint64 key per simulation for `family`; seeds and game_ids broadcast to the same shape."""
    s = np.asarray(seeds, dtype=np.uint64)
    g = np.asarray(game_ids, dtype=np.uint64)
    f = np.uint64(family_id(family))
    with np.errstate(over="ignore"):
        return mix64(mix64(mix64(s) ^ g) ^ f)


def uniform(keys: np.ndarray, step: int, k: int = 0) -> np.ndarray:
    """U[0,1) per key for counter (step, k). Pure function of (key, step, k)."""
    c = np.uint64((int(step) << 8) | (int(k) & 0xFF))
    with np.errstate(over="ignore"):
        z = mix64(keys ^ mix64(np.asarray(c, dtype=np.uint64)))
    return (z >> np.uint64(11)).astype(np.float64) * _INV53
