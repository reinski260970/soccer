from datetime import datetime, timezone
from types import SimpleNamespace

from oddswatch import pricing
from oddswatch.selection import Offer, evaluate, pick
from oddswatch.sources import apihockey


def test_reference_only_offer_never_becomes_play():
    o = Offer(
        event="A – B", kickoff="2026-10-07T18:00:00+00:00", market="home",
        selection="A ML", odds=3.0, source="orbit",
        observed_at="2026-10-07T06:00:00+00:00", league="nhl", executable=False,
    )
    c = evaluate(o, 0.5, p_final=0.5)
    assert c.ev > 0
    assert any("nur Referenz" in f for f in c.flags)
    assert pick([c]) == []


def test_apihockey_parses_two_way_moneyline():
    data = {
        "response": [{
            "game": {"teams": {"home": {"name": "Jukurit"}, "away": {"name": "Assat"}}},
            "bookmakers": [
                {"name": "Pinnacle", "bets": [{"name": "Home/Away", "values": [
                    {"value": "Home", "odd": "1.95"}, {"value": "Away", "odd": "1.91"}
                ]}]},
                {"name": "Bet365", "bets": [{"name": "Money Line", "values": [
                    {"value": "Home", "odd": "2.02"}, {"value": "Away", "odd": "1.82"}
                ]}]},
            ],
        }]
    }
    out = apihockey.parse_odds(data)
    assert out["pinnacle"]["home"] == 1.95
    assert out["bet365"]["away"] == 1.82
    ref = apihockey._consensus(out)
    expected = pricing.devig([1.95, 1.91])
    assert abs(ref["home"] - expected[0]) < 1e-9


def test_apihockey_upcoming_fixtures_filters_window_and_finished(monkeypatch):
    t = lambda h: datetime(2026, 10, 22, h, tzinfo=timezone.utc)
    rows = [
        {"id": 1, "start": t(10), "home": "A", "away": "B", "status": "FT"},
        {"id": 2, "start": t(19), "home": "C", "away": "D", "status": "NS"},
        {"id": 3, "start": t(18), "home": "E", "away": "F", "status": "NS"},
        {"id": 4, "start": t(23), "home": "G", "away": "H", "status": "NS"},
    ]
    seen = {}
    def fake(name, season, country=None):
        seen["args"] = (name, season, country)
        return rows, None
    monkeypatch.setattr(apihockey, "league_games", fake)
    out, err = apihockey.upcoming_fixtures("DEL", 2026, t(12), t(20), "Germany")
    assert err is None
    assert [g["id"] for g in out] == [3, 2]
    assert seen["args"] == ("DEL", 2026, "Germany")
