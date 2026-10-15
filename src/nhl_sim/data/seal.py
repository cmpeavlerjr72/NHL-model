"""2025-26 season seal (INV-15). Season ids are 8-digit NHL ids (20252026)."""
from __future__ import annotations

import os
from collections.abc import Iterable

SEALED_SEASON = 20252026
UNSEAL_ENV_VAR = "NHL_UNSEAL_2025"


class SealedSeasonError(RuntimeError):
    """Raised when sealed 2025-26 data is requested without NHL_UNSEAL_2025=1."""


def is_unsealed() -> bool:
    return os.environ.get(UNSEAL_ENV_VAR, "") == "1"


def _seasons(obj) -> set[int]:
    if hasattr(obj, "columns") and hasattr(obj, "__getitem__"):
        if "season" not in obj.columns:
            return set()
        return {int(s) for s in obj["season"].dropna().unique()}
    if isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
        return {int(s) for s in obj}
    return {int(obj)}


def assert_not_sealed(obj, context: str = "") -> None:
    """Raise if a season id, iterable of ids, or DataFrame with a `season` column touches 2025-26."""
    if is_unsealed():
        return
    if SEALED_SEASON in _seasons(obj):
        where = f" ({context})" if context else ""
        raise SealedSeasonError(f"season {SEALED_SEASON} (2025-26) is sealed{where}; "
                                f"{UNSEAL_ENV_VAR}=1 is the deliberate override.")


def drop_sealed(df):
    """Return df without sealed rows (no-op when unsealed or no season column)."""
    if is_unsealed() or "season" not in df.columns:
        return df
    return df[df["season"] != SEALED_SEASON].reset_index(drop=True)
