from datetime import date

from oddswatch.m13_research import _dedupe_matches, _resolve_understat
from oddswatch.models.poisson import Match


def test_m13_dedupes_same_fixture_key():
    rows = [
        Match(date(2025, 8, 1), "A", "B", 1, 0, 1.2, 0.8),
        Match(date(2025, 8, 1), "A", "B", 1, 0, 1.2, 0.8),
        Match(date(2025, 8, 2), "C", "D", 0, 0, 0.7, 0.6),
    ]
    out = _dedupe_matches(rows)
    assert len(out) == 2
    assert [(m.home, m.away) for m in out] == [("A", "B"), ("C", "D")]


def test_m13_resolve_exact_by_team_and_date():
    u = Match(date(2026, 3, 1), "Arsenal", "Chelsea", 2, 1, 1.5, 0.9)
    got, kind = _resolve_understat(date(2026, 3, 1), "Arsenal", "Chelsea", 2, 1, [u])
    assert got is u
    assert kind == "exact"


def test_m13_resolve_swap_by_team_and_date():
    u = Match(date(2026, 3, 1), "Arsenal", "Chelsea", 2, 1, 1.5, 0.9)
    got, kind = _resolve_understat(date(2026, 1, 3), "Arsenal", "Chelsea", 2, 1, [u])
    assert got is u
    assert kind == "swap"


def test_m13_excludes_short_positive_lag_without_swap():
    u = Match(date(2024, 4, 14), "Udinese", "Roma", 1, 2, 0.8, 1.3)
    got, kind = _resolve_understat(date(2024, 4, 25), "Udinese", "Roma", 1, 2, [u])
    assert got is None
    assert kind == "suspended_or_shifted"
