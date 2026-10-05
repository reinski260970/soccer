from datetime import date

from oddswatch.m13_research import _dedupe_matches
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
