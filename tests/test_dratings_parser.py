from pathlib import Path

from nhl_sim import dratings as D

FIX = Path(__file__).parent / "fixtures" / "dratings_game_FLA_BOS.html"


def test_cells():
    assert D.cell("-201") == (None, -201.0)
    assert D.cell("-1½+132") == (-1.5, 132.0)
    assert D.cell("+1½-148") == (1.5, -148.0)
    assert D.cell("o5½-103") == (5.5, -103.0)
    assert D.cell("+185.6") == (None, 185.6)


def test_game_page():
    g = D.parse_game(FIX.read_text(encoding="utf-8", errors="replace"))
    assert g["start_utc"].startswith("2025-03-11")
    ml = {t["group"]: t for t in g["markets"]["ml"]}
    assert ml["offshore"]["rows"][0][0] == "Florida" and ml["offshore"]["rows"][0][1][0] == "-200"
    assert ml["vegas"]["rows"][1][1][1] == "+180"
    tot = g["markets"]["total"][0]["rows"][0][1]
    assert D.cell(tot[1].replace("�", "½")) == (5.5, -103.0)
    p = D.nov_vig_home(-201, 178)
    assert 0.34 < p < 0.36
