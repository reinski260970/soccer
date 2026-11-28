"""Regression tests for chronological information sets in historical soccer."""
from datetime import date, timedelta

import pytest

from oddswatch.m17_17_research import build_regime_dataset
from oddswatch.models.poisson import Match


def _historical_set(a_goals):
    start = date(2022, 8, 1)
    matches = []
    for i in range(7):
        day = start + timedelta(days=i)
        matches.append(Match(day, "A", "B", 1, 0, 1.25, 0.75))
        matches.append(Match(day, "C", "D", 2, 1, 1.60, 1.05))
    target_day = start + timedelta(days=7)
    matches.append(Match(target_day, "A", "B", a_goals, 3 - a_goals,
                         0.2 + a_goals, 3.2 - a_goals))
    matches.append(Match(target_day, "C", "D", 1, 1, 1.5, 1.5))
    odds = [(2022, m.date, m.home, m.away,
             m.home_goals, m.away_goals,
             [2.1, 3.25, 3.6], [2.0, 3.3, 3.9])
            for m in matches]
    shots = {(2022, m.home, m.away): (12.0, 9.0, 5.0, 3.0)
             for m in matches}
    return matches, odds, shots, target_day


def test_same_day_match_outcome_never_enters_other_prematch_features():
    normal = _historical_set(3)
    upset = _historical_set(0)
    rows_a = build_regime_dataset(*normal[:3])
    rows_b = build_regime_dataset(*upset[:3])
    date_a, date_b = normal[3], upset[3]
    feature_a = next(r["x"] for r in rows_a if r["date"] == date_a
                     and r["home"] == "C")
    feature_b = next(r["x"] for r in rows_b if r["date"] == date_b
                     and r["home"] == "C")
    assert feature_a == feature_b


def test_m1717_fails_closed_if_proxy_sees_validation_year(monkeypatch, tmp_path):
    from oddswatch import m17_17_research as research
    monkeypatch.setattr(research, "mongo_coverage", lambda: {})
    monkeypatch.setattr(research, "train_proxy",
                        lambda years: {"train_seasons": [2017, 2020],
                                       "n": 2000, "rmse": 0.25})
    with pytest.raises(RuntimeError, match="xG-proxy leakage"):
        research.run(tmp_path / "invalid.json")
