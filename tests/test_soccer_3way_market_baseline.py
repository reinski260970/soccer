"""PostgreSQL coverage for the soccer 1X2 three-way no-vig benchmark."""
import math
import os

import pytest


def test_soccer_threeway_market_baseline(monkeypatch):
    if not os.getenv("SPORTS_SQL_TEST_URL"):
        pytest.skip("requires isolated PostgreSQL test database")
    monkeypatch.setenv("SPORTS_DATABASE_URL", os.environ["SPORTS_SQL_TEST_URL"])

    from oddswatch.sql.store import connect, ingest, migrate

    with connect() as conn:
        migrate(conn)
        with conn.transaction(force_rollback=True):
            conn.execute("TRUNCATE sports.events,sports.model_versions CASCADE")
            event = {
                "event_id": "bundesliga:threeway:test",
                "league": "bundesliga",
                "source": "test",
                "source_event_id": "threeway-test",
                "home_team_id": "home",
                "away_team_id": "away",
                "home_name": "Home FC",
                "away_name": "Away FC",
                "kickoff": "2026-10-10T18:00:00Z",
                "season": 2026,
                "season_type": "regular",
                "status": "STATUS_FINAL",
                "home_score": 2,
                "away_score": 1,
                "observed_at": "2026-10-10T20:00:00Z",
            }
            model = {
                "model_id": "soccer-threeway-test",
                "league": "bundesliga",
                "trained_through": "2026-10-09T00:00:00Z",
                "created_at": "2026-10-09T01:00:00Z",
                "method": "test",
                "parameters": {},
                "validation": {"status": "SHADOW"},
                "approved": False,
            }
            probabilities = {"HOME": 0.55, "DRAW": 0.25, "AWAY": 0.20}
            predictions = [
                {
                    "prediction_id": "p-" + side.lower(),
                    "event_id": event["event_id"],
                    "model_id": model["model_id"],
                    "as_of": "2026-10-10T12:00:00Z",
                    "market": "moneyline",
                    "selection": side,
                    "line": 0,
                    "period": "REGULATION",
                    "settlement_rules": "REGULATION",
                    "probability": prob,
                    "quality": "MEDIUM",
                    "features": {},
                }
                for side, prob in probabilities.items()
            ]
            market = {"HOME": 2.00, "DRAW": 3.50, "AWAY": 4.00}
            quotes = [
                {
                    "quote_id": "q-" + side.lower(),
                    "event_id": event["event_id"],
                    "market": "moneyline",
                    "selection": side,
                    "line": 0,
                    "period": "REGULATION",
                    "settlement_rules": "REGULATION",
                    "bookmaker": "pinnacle",
                    "source": "pinnacle",
                    "source_url": None,
                    "observed_at": "2026-10-10T11:55:00Z",
                    "source_time": None,
                    "odds": odd,
                    "commission": 0,
                    "executable": False,
                    "live": False,
                    "liquidity": None,
                }
                for side, odd in market.items()
            ]
            ingest(conn, {
                "events": [event],
                "model_versions": [model],
                "predictions": predictions,
                "odds_snapshots": quotes,
            })

            row = conn.execute(
                "SELECT * FROM sports.forward_market_comparison "
                "WHERE model_id='soccer-threeway-test'"
            ).fetchone()
            assert row is not None
            assert row["market_structure"] == "3WAY"
            assert row["matches"] == 1
            assert row["outcomes"] == 1

            overround = sum(1 / x for x in market.values())
            market_home = (1 / market["HOME"]) / overround
            assert float(row["model_logloss"]) == pytest.approx(-math.log(0.55))
            assert float(row["market_logloss"]) == pytest.approx(-math.log(market_home))
            assert float(row["logloss_gain_vs_market"]) > 0
