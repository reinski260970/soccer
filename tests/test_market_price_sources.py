from datetime import datetime, timezone
from types import SimpleNamespace

from oddswatch import pricing
from oddswatch.selection import Offer, evaluate, pick
from oddswatch.sources import apihockey, kalshi


def test_reference_only_offer_never_becomes_play():
    o = Offer(
        event="A – B", kickoff="2026-10-07T18:00:00+00:00", market="home",
        selection="A ML", odds=3.0, source="polymarket",
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


def test_kalshi_side_and_prices():
    game = SimpleNamespace(
        home=SimpleNamespace(aliases=lambda: ["Boston Bruins"]),
        away=SimpleNamespace(aliases=lambda: ["New York Rangers"]),
    )
    m = {
        "yes_sub_title": "Boston Bruins",
        "no_sub_title": "New York Rangers",
        "yes_ask_dollars": "0.5400",
        "no_ask_dollars": "0.4800",
    }
    assert kalshi._market_side(m, game) == ("home", "away")
    assert kalshi._ask(m, "yes") == 0.54
    assert kalshi._ask(m, "no") == 0.48
