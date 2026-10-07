from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy import select

from oddswatch import sql_store
from oddswatch.scan import Fixture
from oddswatch.selection import Candidate, Offer
from oddswatch.sources.espn import EspnGame, Team


def _candidate(game, league="nhl"):
    return Candidate(
        event=game.title,
        kickoff=game.kickoff.isoformat(),
        market="away",
        selection=f"{game.away.name} Sieg (inkl. OT)",
        source="betfair",
        odds=2.10,
        p_model=0.52,
        fair_odds=1 / 0.52,
        min_odds=1.03 / 0.52,
        edge=0.092,
        ev=0.092,
        stake_eh=0.5,
        estimate=False,
        reason="test PLAY",
        observed_at=datetime.now(timezone.utc).isoformat(),
        liquidity=None,
        p_ref=0.49,
        p_final=0.52,
        ref="test:1:away",
        league=league,
        flags=[],
    )


def test_every_pick_is_mirrored_as_play(monkeypatch, tmp_path):
    monkeypatch.setenv("SPORTS_DATABASE_URL", f"sqlite:///{tmp_path / 'sports.db'}")
    game = EspnGame(
        "g1", "nhl", datetime(2026, 10, 7, tzinfo=timezone.utc),
        Team("Home"), Team("Away"), "STATUS_SCHEDULED",
    )
    offer = Offer(
        game.title, game.kickoff.isoformat(), "away", "Away Sieg (inkl. OT)",
        2.10, "betfair", datetime.now(timezone.utc).isoformat(), ref="test:1:away", league="nhl",
    )
    fx = Fixture(
        "nhl", "nhl", game, {"home": 0.48, "away": 0.52}, "test",
        ref_probs={"home": 0.51, "away": 0.49}, offers={"away": [offer]}, model="points-test",
    )
    assert sql_store.sync_scan([fx], [_candidate(game)]) == 1
    with sql_store.engine().connect() as conn:
        ps = list(conn.execute(select(sql_store.plays)).mappings())
        sig = list(conn.execute(select(sql_store.signals)).mappings())
        pred = list(conn.execute(select(sql_store.predictions)).mappings())
        oq = list(conn.execute(select(sql_store.odds)).mappings())
    assert len(ps) == 1 and ps[0]["result"] == "pending"
    assert len(sig) == 1 and sig[0]["status"] == "PLAY"
    assert len(pred) == 2
    assert len(oq) == 1


def test_market_grading():
    assert sql_store.grade_market("home", 3, 1) is True
    assert sql_store.grade_market("away", 3, 1) is False
    assert sql_store.grade_market("draw", 2, 2) is True
    assert sql_store.grade_market("O2.5", 2, 1) is True
    assert sql_store.grade_market("U2.5", 1, 1) is True
    assert sql_store.grade_market("O3.0", 2, 1) is None
    assert sql_store.grade_market("BTTS_YES", 2, 1) is True
    assert sql_store.grade_market("BTTS_NO", 2, 0) is True


def test_settlement_updates_play_and_clv(monkeypatch, tmp_path):
    monkeypatch.setenv("SPORTS_DATABASE_URL", f"sqlite:///{tmp_path / 'sports.db'}")
    game = EspnGame(
        "g2", "nhl", datetime(2026, 10, 7, tzinfo=timezone.utc),
        Team("Home"), Team("Away"), "STATUS_SCHEDULED",
    )
    fx = Fixture("nhl", "nhl", game, {"home": 0.48, "away": 0.52}, "test", model="test")
    sql_store.sync_scan([fx], [_candidate(game)])

    final = EspnGame(
        "g2", "nhl", game.kickoff, Team("Home"), Team("Away"), "STATUS_FINAL",
        home_score=2, away_score=3,
        ref_line={"ml_home": 1.90, "ml_away": 2.00},
    )
    from oddswatch.sources import espn
    monkeypatch.setattr(espn, "scoreboard_day", lambda league, day: ([final], None))

    out = sql_store.settle_pending()
    assert out["settled"] == 1
    with sql_store.engine().connect() as conn:
        p = conn.execute(select(sql_store.plays)).mappings().first()
    assert p["result"] == "win"
    assert p["pnl_eh"] == 0.55
    assert p["closing_fair_odds"] is not None
    assert p["clv"] is not None
