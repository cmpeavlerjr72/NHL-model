"""SS-R1 penalty mapping (L13 pattern): every pen_type / pen_desc / pen_minutes combination in the loadable seasons
must be mapped; an unmapped combination fails. Also checks the per-stoppage resolution rules on hand-built bundles."""
import pytest

from nhl_sim.data import load
from nhl_sim.strength_state.events import _resolve
from nhl_sim.strength_state.penalty_map import UnmappedPenalty, classify, classify_frame


def test_known_and_unknown():
    assert classify("MIN", "tripping", 2.0) == "minor"
    assert classify("MIN", "high-sticking-double-minor", 4.0) == "double"
    assert classify("MAT", "match-penatly-10-minutes", 10.0) == "major"
    assert classify("PS", "ps-hooking-on-breakaway", 0.0) == "ps"
    with pytest.raises(UnmappedPenalty):
        classify("MIN", "a-new-infraction", 2.0)
    with pytest.raises(UnmappedPenalty):
        classify("MIN", "tripping", 3.0)


@pytest.mark.skipif(not (load.PROCESSED / "events").exists(), reason="no processed data")
def test_every_combination_in_data_is_mapped(monkeypatch):
    monkeypatch.delenv("NHL_UNSEAL_2025", raising=False)
    ev = load.load_events(columns=["event", "pen_type", "pen_desc", "pen_minutes"])
    p = ev[ev.event == "PENALTY"]
    classify_frame(p)   # raises on the first unmapped combination


def test_resolution_rules():
    # one minor each: coincidental, 5v5-exception flag, nothing left
    c, rem = _resolve([(1, 0, "minor", 10), (2, 1, "minor", 20)])
    assert c["smp"] and rem == []
    # fighting majors cancel; an extra roughing minor on one side stays
    c, rem = _resolve([(1, 0, "major", 10), (2, 1, "major", 20), (3, 0, "minor", 11)])
    assert c is not None and not c["smp"] and rem == [(3, 0, "minor", 11)]
    # double minor vs minor: one unit cancels, a minor remains
    c, rem = _resolve([(1, 0, "double", 10), (2, 1, "minor", 20)])
    assert rem == [(1, 0, "minor", 10)]
    # minor vs major: no cross-category cancellation
    c, rem = _resolve([(1, 0, "minor", 10), (2, 1, "major", 20)])
    assert c is None and len(rem) == 2
