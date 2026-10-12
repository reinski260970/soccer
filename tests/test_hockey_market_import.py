from pathlib import Path

from oddswatch import hockey_market_import as hm


def test_importer_dedupes_and_rejects_conflicts(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text(
        "date,league,home_team,away_team,reg_result,close_home,close_draw,close_away\n"
        "2026-10-01,NHL,Minnesota Wild,Dallas Stars,AWAY,2.10,4.30,2.70\n"
        "2026-10-01,NHL,Minnesota Wild,Dallas Stars,AWAY,2.10,4.30,2.70\n"
        "2026-10-02,NHL,Colorado Avalanche,Winnipeg Jets,HOME,1.79,4.48,3.40\n",
        encoding="utf-8",
    )
    rows, issues = hm.read_market_dir(tmp_path)
    assert len(rows) == 2
    assert not any(x.startswith("CONFLICT") for x in issues)

    q = tmp_path / "b.csv"
    q.write_text(
        "date,league,home_team,away_team,reg_result,close_home,close_draw,close_away\n"
        "2026-10-02,NHL,Colorado Avalanche,Winnipeg Jets,HOME,1.90,4.48,3.40\n",
        encoding="utf-8",
    )
    rows, issues = hm.read_market_dir(tmp_path)
    assert len(rows) == 1
    assert any(x.startswith("CONFLICT") for x in issues)


def test_importer_never_needs_network(monkeypatch, tmp_path):
    p = tmp_path / "a.csv"
    p.write_text(
        "date,league,home_team,away_team,reg_result,close_home,close_draw,close_away\n"
        "2026-10-01,ICEHL,Vienna,Klagenfurt,HOME,2.00,4.00,3.00\n",
        encoding="utf-8",
    )
    # Regression intent: this module has no network path at all.
    assert not hasattr(hm, "requests")
    rows, issues = hm.read_market_dir(tmp_path)
    assert len(rows) == 1
    assert issues == []
