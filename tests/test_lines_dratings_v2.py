import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_lines_dratings_v2 import classify  # noqa: E402


def test_agree_and_disagree():
    assert classify(1.5, 0.60) == (False, False)   # home fav both
    assert classify(-1.5, 0.40) == (False, False)  # away fav both
    assert classify(1.5, 0.40) == (True, False)
    assert classify(-1.5, 0.60) == (True, False)


def test_pickem_ambiguous():
    assert classify(1.5, 0.504) == (False, True)
    assert classify(-1.5, 0.496) == (False, True)
    assert classify(1.5, 0.506) == (False, False)


def test_missing():
    assert classify(None, 0.6) == (False, False)
    assert classify(1.5, None) == (False, False)
    assert classify(float("nan"), 0.6) == (False, False)
