from pathlib import Path

from oddswatch.sources import ceskyhokej

PAGE = (Path(__file__).parent / "fixtures" / "ceskyhokej_p1.html").read_text(encoding="utf-8")
KNOWN = {"České Budějovice", "Sparta Prague", "Liberec", "Plzeň", "Pardubice", "Hradec Králové",
         "Kladno", "Mladá Boleslav", "Třinec", "Olomouc", "Vítkovice", "Karlovy Vary", "Brno", "Litvínov"}


def test_parses_regulation_scores_and_extra_time():
    rs = ceskyhokej.parse_page(PAGE)
    assert len(rs) >= 40
    r = rs["179798"]
    assert (r.home, r.away, r.reg_home, r.reg_away, r.extra) == ("Pardubice", "Hradec Králové", 3, 5, "")
    ot = rs["179799"]   # 2:3 nach Verlängerung -> 60 Min. 2:2
    assert (ot.reg_home, ot.reg_away, ot.extra) == (2, 2, "OT")


def test_upcoming_games_skipped_and_names_canonical():
    rs = ceskyhokej.parse_page(PAGE)
    assert "179886" not in rs            # 22.10. noch ohne Ergebnis
    assert {n for r in rs.values() for n in (r.home, r.away)} <= KNOWN


def test_shootout_marker():
    block = ('<a href="/game/detail/1" class="game-item"><div class="team-names">A - B <span>SN</span></div>'
             '<h4 class="h4">Rytíři Kladno</h4><h4 class="h4">Mountfield HK, a.s.</h4>'
             '<div class="game-info"><p>2:2, 1:0, 0:1 - 0:1</p><p><small>02. 10. 2026, 18:00</small></p></div></a>')
    r = ceskyhokej.parse_page(block)["1"]
    assert (r.home, r.away, r.reg_home, r.reg_away, r.extra) == ("Kladno", "Hradec Králové", 3, 3, "SO")
