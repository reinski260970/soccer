from datetime import datetime, timedelta, timezone

from oddswatch.scan import Fixture
from oddswatch.selection import Candidate, Offer
from oddswatch.sources.espn import EspnGame, Team
from oddswatch import soccer_steam


def _fixture(now):
    g = EspnGame("s1", "austria", now + timedelta(days=2),
                 Team("Home"), Team("Away"), "STATUS_SCHEDULED")
    fx = Fixture("austria", "soccer", g,
                 {"home": 0.50, "draw": 0.25, "away": 0.25}, "test")
    fx.market_quotes = {
        "home": [
            Offer(g.title, g.kickoff.isoformat(), "home", "Home", 2.00, "pinnacle", now.isoformat(), executable=False),
            Offer(g.title, g.kickoff.isoformat(), "home", "Home", 2.10, "bet365", now.isoformat()),
            Offer(g.title, g.kickoff.isoformat(), "home", "Home", 2.08, "betfair", now.isoformat()),
        ],
        "draw": [
            Offer(g.title, g.kickoff.isoformat(), "draw", "Draw", 3.50, "pinnacle", now.isoformat(), executable=False),
            Offer(g.title, g.kickoff.isoformat(), "draw", "Draw", 3.60, "bet365", now.isoformat()),
            Offer(g.title, g.kickoff.isoformat(), "draw", "Draw", 3.55, "betfair", now.isoformat()),
        ],
        "away": [
            Offer(g.title, g.kickoff.isoformat(), "away", "Away", 4.00, "pinnacle", now.isoformat(), executable=False),
            Offer(g.title, g.kickoff.isoformat(), "away", "Away", 4.20, "bet365", now.isoformat()),
            Offer(g.title, g.kickoff.isoformat(), "away", "Away", 4.10, "betfair", now.isoformat()),
        ],
    }
    return fx


def test_collect_soccer_steam_has_sharp_fair_and_clv():
    now = datetime(2026, 10, 7, 17, tzinfo=timezone.utc)
    fx = _fixture(now)
    recs, meta = soccer_steam.collect([fx])
    assert len(recs) == 3
    row = meta[(fx.game.title, "home")]
    assert row["best_source"] == "Bet365"
    assert row["best_odds"] == 2.10
    assert row["sharp_fair"] > 1.0
    assert row["clv_to_sharp"] > 0


def test_confirmed_drift_blocks_candidate():
    c = Candidate(
        event="Home vs Away", kickoff="2026-10-09T19:00:00+00:00",
        market="home", selection="Home", source="bet365", odds=2.10,
        p_model=0.50, fair_odds=2.0, min_odds=2.06, edge=0.05, ev=0.05,
        stake_eh=0.5, estimate=False, reason="test", observed_at="",
        liquidity=None, league="austria", flags=[],
    )
    state = {("Home vs Away", "home"): {
        "signal": {"direction": "DRIFTING"}
    }}
    soccer_steam.annotate_candidates([c], state)
    assert any("STEAM-" in x for x in c.flags)
