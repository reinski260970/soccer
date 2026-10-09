from datetime import datetime, timezone

from oddswatch import period_totals, surebet_values
from oddswatch.sources import surebet


def _value(sport, tournament, period, condition="22.5", bet_type="over"):
    return surebet.SurebetValue(
        id="1",
        sport=sport,
        tournament=tournament,
        teams=("Home", "Away"),
        kickoff=datetime(2026, 10, 12, 18, 0, tzinfo=timezone.utc),
        selection="x",
        market="x",
        odds=1.95,
        probability=None,
        overvalue=None,
        bet_type=bet_type,
        condition=condition,
        period=period,
        base="overall",
    )


def test_surebet_parses_american_football_first_half_total():
    data = {
        "records": [{
            "id": "1",
            "sport_id": "American football",
            "tournament": "NFL",
            "teams": ["ARI Cardinals", "LA Chargers"],
            "time": 1791835200000,
            "prongs": [{
                "bk": "bet365",
                "value": 1.91,
                "sport_id": "American football",
                "tournament": "NFL",
                "teams": ["ARI Cardinals", "LA Chargers"],
                "time": 1791835200000,
                "type": {
                    "type": "over",
                    "condition": "22.5",
                    "period": "1h",
                    "base": "overall",
                    "back": True,
                },
            }],
        }]
    }
    rows = surebet.parse(data)
    assert len(rows) == 1
    v = rows[0]
    assert v.sport == "American football"
    assert "Gesamt-Punkte" in v.selection
    assert "1. Halbzeit" in v.market


def test_period_kind_routes_exact_sports():
    assert surebet_values._period_kind(_value("Basketball", "NBA", "q1")) == "q1"
    assert surebet_values._period_kind(_value("Basketball", "NBA", "1h")) == "1h"
    assert surebet_values._period_kind(_value("American football", "NFL", "1h")) == "1h"
    assert surebet_values._period_kind(_value("American football", "NFL", "period1")) == "q1"
    assert surebet_values._period_kind(_value("Hockey", "NHL", "p1", "1.5")) == "p1"


def test_period_total_fair_uses_independent_period_model(monkeypatch):
    def fake(*args, **kwargs):
        return (
            period_totals.PeriodFair(
                fair_odds=1.80,
                probability=1/1.80,
                expected_total=23.4,
                sample_games=350,
                model="NFL 1h PointsModel",
            ),
            None,
            [],
        )
    monkeypatch.setattr(period_totals, "fair_total", fake)

    v = _value("American football", "NFL", "1h")
    fair, p, ev, note = surebet_values._period_total_fair(v, {})
    assert fair == 1.80
    assert abs(p - 1/1.80) < 1e-12
    assert abs(ev - ((1/1.80) * 1.95 - 1)) < 1e-12
    assert "350" in note


def test_euro_basketball_period_does_not_use_nba_model():
    v = _value("Basketball", "EuroLeague", "q1", "41.5")
    fair, p, ev, note = surebet_values._period_total_fair(v, {})
    assert fair is None and p is None and ev is None
    assert "nur NBA" in note


def test_empty_value_audit_does_not_send_telegram(monkeypatch):
    monkeypatch.setattr(surebet, "fetch_valuebets", lambda **kwargs: ([], None))
    sent = []
    monkeypatch.setattr(surebet_values.telegram, "send", lambda txt: sent.append(txt))
    lines = surebet_values.run(send=True, limit=10)
    assert sent == []
    assert any("nichts gesendet" in x for x in lines)


def test_nfl_feed_failure_does_not_block_core_candidates(monkeypatch):
    core = _value("Basketball", "NBA", "q1", "55.5")
    calls = []

    def fake_fetch(*, sports, books, limit):
        calls.append(tuple(sports))
        if tuple(sports) == ("American football",):
            return [], "HTTP 403"
        return [core], None

    monkeypatch.setattr(surebet, "fetch_valuebets", fake_fetch)
    values, warnings, err = surebet_values._fetch_candidate_values(25)

    assert values == [core]
    assert err is None
    assert any("NFL-Feed" in w and "403" in w for w in warnings)
    assert ("Football", "Hockey", "Basketball") in calls
    assert ("American football",) in calls


def test_surebet_normalizes_nfl_sport_variants():
    assert surebet.canonical_sport("American Football") == "American football"
    assert surebet.canonical_sport("american-football") == "American football"
    assert surebet.canonical_sport("NFL") == "American football"
