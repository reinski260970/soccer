from datetime import date

from oddswatch.sources import mongo_venue


def test_season_labels():
    assert mongo_venue.season_label("calendar", date(2026, 10, 22)) == "2026"
    assert mongo_venue.season_label("split", date(2026, 10, 22)) == "2026/2027"
    assert mongo_venue.season_label("split", date(2027, 3, 1)) == "2026/2027"


def test_aggregate_home_away():
    rows = []
    for i in range(3):
        rows.append({"Home": "Malmo FF", "Away": f"X{i}", "HG": 2, "AG": 0})   # 3 Heimsiege
        rows.append({"Home": f"Y{i}", "Away": "Malmo FF", "HG": 1, "AG": 1})   # 3 Auswärts-Remis
    rows.append({"Home": "Malmo FF", "Away": "Z", "HG": "x", "AG": 1})          # kaputte Zeile
    pr = {p.team: p for p in mongo_venue.aggregate(rows)}
    m = pr["Malmo FF"]
    assert (m.home_gp, m.home_gf_pg, m.home_ga_pg, m.home_ppg) == (3, 2.0, 0.0, 3.0)
    assert (m.away_gp, m.away_gf_pg, m.away_ga_pg, m.away_ppg) == (3, 1.0, 1.0, 1.0)
    assert m.source == "mongo"
    assert "X0" not in pr                # zu wenige Spiele


def test_unmapped_and_missing_secret(monkeypatch):
    assert mongo_venue.team_homeaway("XXX")[1]
    monkeypatch.delenv("MONGO_SOCCER", raising=False)
    monkeypatch.delenv("MONGODB_URI", raising=False)
    rows, err = mongo_venue.team_homeaway("SWE")
    assert rows == [] and "MONGO_SOCCER" in err
