from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy import select

from oddswatch import bookmaker, ceo_runner, sql_store
from oddswatch.scan import Fixture
from oddswatch.selection import Offer
from oddswatch.sources.espn import EspnGame, Team


def _offer(source: str, odds: float, executable: bool) -> Offer:
    return Offer(
        event="A – B",
        kickoff="2026-10-08T18:00:00+00:00",
        market="home",
        selection="A ML",
        odds=odds,
        source=source,
        observed_at="2026-10-07T08:00:00+00:00",
        ref=f"{source}:1",
        league="nhl",
        executable=executable,
    )


def test_reference_quote_is_kept_for_comparison_but_not_play():
    fx = SimpleNamespace(
        offers={"home": [_offer("pinnacle", 2.05, False), _offer("bet365", 2.10, True)]},
        market_quotes={},
    )
    bookmaker._capture_and_filter_market_quotes([fx])
    assert [o.source for o in fx.market_quotes["home"]] == ["pinnacle", "bet365"]
    assert [o.source for o in fx.offers["home"]] == ["bet365"]


def test_market_quote_text_always_shows_decimal_odds():
    fx = SimpleNamespace(
        market_quotes={
            "home": [_offer("pinnacle", 2.05, False), _offer("bet365", 2.10, True)],
            "away": [
                Offer("A – B", "2026-10-08T18:00:00+00:00", "away", "B ML",
                      1.85, "pinnacle", "2026-10-07T08:00:00+00:00",
                      ref="pinnacle:2", league="nhl", executable=False)
            ],
        }
    )
    txt = ceo_runner._market_quote_text(fx)
    assert "1 2.10 bet365[E]" in txt
    assert "2 1.85 pinnacle[R]" in txt


def test_sql_stores_reference_and_executable_quotes(tmp_path, monkeypatch):
    db = tmp_path / "sports.db"
    monkeypatch.setenv("SPORTS_DATABASE_URL", f"sqlite:///{db}")
    game = EspnGame(
        "g1", "nhl", datetime(2026, 10, 8, 18, tzinfo=timezone.utc),
        Team("A"), Team("B"), "STATUS_SCHEDULED"
    )
    fx = Fixture("nhl", "nhl", game, {"home": .52, "away": .48}, "test")
    fx.market_quotes = {
        "home": [_offer("pinnacle", 2.05, False), _offer("bet365", 2.10, True)]
    }
    fx.offers = {"home": [fx.market_quotes["home"][1]]}
    sql_store.sync_scan([fx], [])
    with sql_store.engine().connect() as conn:
        rows = conn.execute(select(sql_store.odds.c.source, sql_store.odds.c.executable)).all()
    assert set(rows) == {("pinnacle", False), ("bet365", True)}
