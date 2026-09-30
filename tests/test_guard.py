from datetime import datetime, timezone

from oddswatch import guard
from oddswatch.news import Target
from oddswatch.sources import apifootball

ODDS = {"response": [{"bookmakers": [
    {"id": 4, "name": "Pinnacle", "bets": [
        {"name": "Match Winner", "values": [{"value": "Home", "odd": "1.34"}, {"value": "Draw", "odd": "5.01"},
                                            {"value": "Away", "odd": "9.02"}]},
        {"name": "Goals Over/Under", "values": [{"value": "Over 2.5", "odd": "1.94"},
                                                {"value": "Under 2.5", "odd": "1.89"}]}]},
    {"id": 8, "name": "Bet365", "bets": [
        {"name": "Match Winner", "values": [{"value": "Home", "odd": "1.38"}, {"value": "Draw", "odd": "4.33"},
                                            {"value": "Away", "odd": "9.00"}]}]},
    {"id": 3, "name": "Betfair", "bets": [
        {"name": "Match Winner", "values": [{"value": "Home", "odd": "1.33"}, {"value": "Draw", "odd": "4.75"},
                                            {"value": "Away", "odd": "9.50"}]}]},
    {"id": 1, "name": "10Bet", "bets": []}]}]}


def _t(market="away", status="PLAY", odds=11.7):
    return Target(status, "nations", "Switzerland – Slovenia", "2026-10-03T18:45+00:00", market,
                  "Slovenia Sieg (90 Min.)", odds, 10.5, 10.8, ["Switzerland", "SUI"], ["Slovenia", "SVN"])


def test_parse_odds_keys():
    b = apifootball.parse_odds(ODDS)
    assert set(b) == {"Pinnacle", "Bet365", "Betfair"}
    assert b["Pinnacle"]["O2.5"] == 1.94 and b["Pinnacle"]["U2.5:no"] == 1.89
    assert b["Bet365"] == {"home": 1.38, "draw": 4.33, "away": 9.0}


def test_assess_playable_and_against():
    b = apifootball.parse_odds(ODDS)
    a = guard.assess(_t("away"), b)
    assert 9.02 < a["fair"] < 11 and a["best"] == ("Betfair", 9.5)
    assert not a["playable"]  # 9,50 < spielbar ab (fair × 1,03)
    assert guard.assess(_t("away", odds=9.0), b)["against"]
    assert not guard.assess(_t("away", status="WATCH", odds=9.0), b)["against"]
    b["Bet365"]["away"] = 12.0
    a = guard.assess(_t("away"), b)
    assert a["playable"] and a["best"] == ("Bet365", 12.0)
    assert any("SPIELBAR bei Bet365" in x for x in guard.alert_text(_t(), a, "play"))


def test_assess_needs_pinnacle_and_totals():
    b = apifootball.parse_odds(ODDS)
    assert guard.assess(_t("home"), {"Bet365": b["Bet365"]}) is None
    a = guard.assess(_t("U2.5:no"), b)
    assert a["prices"] == {} and not a["playable"] and abs(a["p"] + guard.fair_prob(b["Pinnacle"], "O2.5") - 1) < 1e-9


def test_find_fixture_excludes_youth_by_kickoff():
    fx = [apifootball.ApiFixture(1, datetime(2026, 10, 13, 12, tzinfo=timezone.utc), "Arsenal U19", "Lille U19", "UYL"),
          apifootball.ApiFixture(2, datetime(2026, 10, 13, 19, tzinfo=timezone.utc), "Arsenal", "Lille", "UCL")]
    ko = datetime(2026, 10, 13, 19, tzinfo=timezone.utc)
    assert apifootball.find_fixture(fx, ["Arsenal", "ARS"], ["Lille", "LILL"], ko).id == 2
    assert apifootball.find_fixture(fx, ["Chelsea"], ["Lille"], ko) is None


def test_run_without_key(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "STATUS", tmp_path / "status.txt")
    for k in ("APIKEY", "API_FOOTBALL_KEY", "API_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert "nicht gesetzt" in guard.run(send=False)[0]
    assert "nicht gesetzt" in (tmp_path / "status.txt").read_text(encoding="utf-8")
