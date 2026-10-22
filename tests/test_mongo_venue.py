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
    rows, err = mongo_venue.from_mongo("SWE")
    assert rows == [] and "MONGO_SOCCER" in err


def test_football_data_primary(monkeypatch):
    from oddswatch import fetch
    head = "Country,League,Season,Date,Time,Home,Away,HG,AG,Res\n"
    body = "".join(f"Sweden,Allsvenskan,2026,0{i+1}/09/2026,18:00,Malmo FF,X{i},2,0,H\n"
                   f"Sweden,Allsvenskan,2026,1{i}/09/2026,18:00,Y{i},Malmo FF,1,1,D\n" for i in range(3))
    monkeypatch.setattr(fetch, "get", lambda url, **kw: (head + body, None))
    monkeypatch.setattr(mongo_venue, "season_label", lambda fmt, today=None: "2026")
    rows, err = mongo_venue.team_homeaway("SWE")
    assert err is None and rows[0].team == "Malmo FF" and rows[0].source == "football-data"
