"""A failed scheduled CLV capture must not report GitHub Actions success."""
from types import SimpleNamespace

import pytest

from oddswatch import surebet_values
from oddswatch.sql import valuebet


def test_clv_feed_error_is_fatal(monkeypatch):
    monkeypatch.setattr(
        surebet_values.surebet, "fetch_valuebets",
        lambda **kwargs: ([], "provider unavailable"),
    )
    with pytest.raises(RuntimeError, match="Valuebet-CLV Feed-Fehler"):
        surebet_values.run_clv_snapshot()


def test_clv_database_error_is_fatal(monkeypatch):
    candidate = SimpleNamespace(bookmaker="bet365", back=True)
    monkeypatch.setattr(
        surebet_values.surebet, "fetch_valuebets",
        lambda **kwargs: ([candidate], None),
    )

    def bad_snapshot(values):
        raise ValueError("database not available")

    monkeypatch.setattr(valuebet, "snapshot_open_candidates", bad_snapshot)
    with pytest.raises(RuntimeError, match="Valuebet-CLV SQL-Fehler: ValueError"):
        surebet_values.run_clv_snapshot()


def test_clv_snapshot_success(monkeypatch):
    candidate = SimpleNamespace(bookmaker="bet365", back=True)
    monkeypatch.setattr(
        surebet_values.surebet, "fetch_valuebets",
        lambda **kwargs: ([candidate], None),
    )
    monkeypatch.setattr(valuebet, "snapshot_open_candidates", lambda values: {"created": 1})
    monkeypatch.setattr(valuebet, "capture_sampled_clv", lambda: {"closed": [], "no_close": 1})
    lines = surebet_values.run_clv_snapshot()
    assert any("Snapshot:" in line for line in lines)
    assert any("NO_CLOSE=1" in line for line in lines)
