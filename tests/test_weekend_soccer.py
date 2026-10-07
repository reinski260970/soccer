from datetime import date
from types import SimpleNamespace

from oddswatch.weekend_soccer import next_weekend, _status


def test_next_weekend_from_wednesday():
    fri, sun = next_weekend(date(2026, 10, 7))
    assert fri == date(2026, 10, 9)
    assert sun == date(2026, 10, 11)


def test_weekend_shadow_gate_requires_model_ev_and_clv():
    c = SimpleNamespace(p_model=0.50, odds=2.20)
    row = {"clv_to_sharp": 0.03, "signal": None}
    assert _status(c, row) == "SHADOW-PLAY"


def test_weekend_confirmed_drift_is_pass():
    c = SimpleNamespace(p_model=0.60, odds=2.00)
    row = {"clv_to_sharp": 0.08, "signal": {"direction": "DRIFTING"}}
    assert _status(c, row) == "PASS"
