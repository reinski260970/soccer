from datetime import date
from types import SimpleNamespace

from oddswatch.m17_17_research import (
    _gap_from_previous_membership,
    _regime_features,
    _season_membership,
)


def _m(d, h, a):
    return SimpleNamespace(date=d, home=h, away=a)


def test_m17_17_membership_is_season_scoped():
    ms = [
        _m(date(2023, 8, 1), "A", "B"),
        _m(date(2024, 8, 1), "A", "C"),
    ]
    m = _season_membership(ms)
    assert "B" in m[2023]
    assert "B" not in m[2024]
    assert "C" not in m[2023]
    assert "C" in m[2024]


def test_m17_17_gap_detects_absence_from_previous_topflight_season():
    membership = {
        2022: {"A", "B"},
        2023: {"A", "C"},
        2024: {"A", "B"},
    }
    assert _gap_from_previous_membership("A", 2024, membership) == 0
    assert _gap_from_previous_membership("B", 2024, membership) == 1


def test_m17_17_regime_features_use_pre_match_current_season_counts():
    membership = {
        2023: {"A", "B"},
        2024: {"A", "C"},
    }
    season_games = {"A": 3, "C": 1}
    x = _regime_features("A", "C", 2024, season_games, membership)
    assert len(x) == 11
    assert abs(x[0] - 0.3) < 1e-12
    assert abs(x[1] - 0.1) < 1e-12
    assert x[5] == 1.0
    assert x[6] == 0.0
    assert x[4] > 0.0
