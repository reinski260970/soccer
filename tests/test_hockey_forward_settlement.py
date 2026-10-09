"""Strict hockey result provenance, safe settlement and forward-quality coverage."""
import os
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from oddswatch.sql.hockey_settlement import nhl_finals, european_final, run
from oddswatch.sql.evaluation import outcome


@pytest.mark.parametrize("rule,market,score,expected", [
    ("INCLUDING_OT", "moneyline", (3, 2), "WIN"),
    ("INCLUDING_OT_SO", "moneyline", (3, 2), "WIN"),
    ("INCLUDING_OT", "total", (3, 2), None),
    ("INCLUDING_OT_SO", "spread", (3, 2), None),
    ("INCLUDING_OT", "moneyline", (2, 2), None),
    ("REGULATION", "moneyline", (3, 2), None),
])
def test_hockey_full_game_market_scope(rule, market, score, expected):
    p = {"period": "FULL_GAME", "settlement_rules": rule,
         "market": market, "selection": "HOME", "line": 5.5}
    assert outcome(p, *score) == expected


def test_nhl_result_parser_rejects_preseason_ties_and_unfinished():
    def event(id_, home, away, status="STATUS_FINAL", kind=2):
        return {"id": id_, "status": {"type": {"name": status}},
                "season": {"type": kind}, "competitions": [{"competitors": [
                    {"homeAway": "home", "team": {"displayName": "Boston Bruins"}, "score": home},
                    {"homeAway": "away", "team": {"displayName": "Detroit Red Wings"}, "score": away},
                ]}]}
    data = {"events": [event("good", "4", "2"), event("tie", "2", "2"),
                       event("pre", "3", "2", kind=1),
                       event("pending", "3", "2", status="STATUS_IN_PROGRESS"),
                       event("missing", None, "2")]}
    assert list(nhl_finals(data)) == ["good"]
    assert nhl_finals(data)["good"]["home_score"] == 4


def test_european_result_requires_unambiguous_regulation_win():
    kickoff = datetime(2026, 10, 9, 15, 30, tzinfo=timezone.utc)
    ev = dict(league="liiga", kickoff=kickoff, home_name="KooKoo",
              away_name="Jukurit")
    r = SimpleNamespace(date=date(2026, 10, 9),
                        home="KooKoo Kouvola", away="Jukurit Mikkeli",
                        reg_home=3, reg_away=1, extra="")
    assert european_final(ev, [r]) == (3, 1)
    assert european_final(ev, [r, r]) is None
    assert european_final(ev, [SimpleNamespace(**{**vars(r), "extra": "SO"})]) is None
    assert european_final(ev, [SimpleNamespace(**{**vars(r), "reg_home": 2,
                                                  "reg_away": 2})]) is None
    assert european_final(ev, [SimpleNamespace(**{**vars(r),
                                                   "home": r.away, "away": r.home})]) is None


def test_postgres_hockey_forward_settlement_and_latest_forecast(monkeypatch):
    if not os.getenv("SPORTS_SQL_TEST_URL"):
        pytest.skip("requires isolated PostgreSQL test database")
    monkeypatch.setenv("SPORTS_DATABASE_URL", os.environ["SPORTS_SQL_TEST_URL"])
    from oddswatch.sql.store import connect, ingest, migrate
    with connect() as conn:
        migrate(conn)
        with conn.transaction(force_rollback=True):
            conn.execute("TRUNCATE sports.events,sports.model_versions CASCADE")
            event = dict(event_id="liiga:oddswatch:test-hockey-forward",
                         league="liiga",source="oddswatch",source_event_id="test-hockey-forward",
                         home_team_id="home-team",away_team_id="away-team",
                         home_name="KooKoo",away_name="Jukurit",
                         kickoff="2026-10-09T15:30:00Z",season=2026,
                         season_type="regular",status="STATUS_SCHEDULED",
                         home_score=None,away_score=None,
                         observed_at="2026-10-09T11:00:00Z")
            model = dict(model_id="hockey-forward-test",league="liiga",
                         trained_through="2026-10-08T00:00:00Z",
                         created_at="2026-10-08T01:00:00Z",method="hockey-test",
                         parameters={},validation={"status": "SHADOW"},
                         approved=False)
            common = dict(event_id=event["event_id"],model_id=model["model_id"],
                          market="moneyline",selection="HOME",line=0,
                          period="FULL_GAME",settlement_rules="INCLUDING_OT",
                          quality="LOW",features={"estimate": True})
            predictions = [
                dict(common,prediction_id="early",as_of="2026-10-09T08:00:00Z",probability=0.55),
                dict(common,prediction_id="late",as_of="2026-10-09T10:00:00Z",probability=0.65),
            ]
            def quote(side, odd):
                return dict(quote_id="q-"+side,event_id=event["event_id"],
                            market="moneyline",selection=side,line=0,
                            period="FULL_GAME",settlement_rules="INCLUDING_OT",
                            bookmaker="pinnacle",source="pinnacle",source_url=None,
                            observed_at="2026-10-09T09:45:00Z",source_time=None,
                            odds=odd,commission=0,executable=False,live=False,liquidity=None)
            ingest(conn,{"events":[event],"model_versions":[model],
                         "predictions":predictions,
                         "odds_snapshots":[quote("HOME",1.85),quote("AWAY",2.05)]})
            finished = SimpleNamespace(date=date(2026, 10, 9),
                                       home="KooKoo Kouvola",away="Jukurit Mikkeli",
                                       reg_home=4,reg_away=2,extra="")
            callbacks = {
                "liiga": lambda year: ([finished],[],None),
                "icehl": lambda year: ([],[],None),
                "shl": lambda year: ([],[],None),
            }
            now = datetime(2026,10,9,20,0,tzinfo=timezone.utc)
            first = run(conn,now=now,fetch_europe=callbacks,
                        fetch_espn=lambda url: {"events": []})
            assert first["events_settled"] == 1
            assert first["predictions_evaluated"] == 2
            assert not first["errors"]
            again = run(conn,now=now,fetch_europe=callbacks,
                        fetch_espn=lambda url: {"events": []})
            assert again["events_settled"] == 0
            assert again["predictions_evaluated"] == 0
            metric = conn.execute(
                "SELECT * FROM sports.model_metrics WHERE model_id='hockey-forward-test'"
            ).fetchone()
            assert metric["evaluated"] == 1  # later snapshot, one actual outcome
            assert float(metric["log_loss"]) == pytest.approx(-__import__("math").log(.65))
            baseline = conn.execute(
                "SELECT * FROM sports.forward_market_comparison WHERE model_id='hockey-forward-test'"
            ).fetchone()
            assert baseline["matches"] == 1
            assert baseline["model_logloss"] is not None
            assert baseline["market_logloss"] is not None
            assert conn.execute(
                "SELECT count(*) AS n FROM sports.raw_payloads WHERE source='liiga-official-regulation-final'"
            ).fetchone()["n"] == 1
