from datetime import date, datetime, timezone

from oddswatch import period_totals
from oddswatch.models.ratings import Game


def _games(n=320):
    out = []
    for i in range(n):
        # Give the model enough variation to estimate total variance.
        hp = 27 + (i % 7) - 3
        ap = 25 + ((i * 3) % 9) - 4
        out.append(Game(
            date(2026, 1 + (i % 8), 1 + (i % 27)),
            "Home" if i % 2 == 0 else "Away",
            "Away" if i % 2 == 0 else "Home",
            hp,
            ap,
            False,
        ))
    return out


def test_points_period_fair_from_synthetic_history(monkeypatch):
    hist = _games()
    monkeypatch.setattr(
        period_totals,
        "history",
        lambda sport, period, as_of, cache: (hist, []),
    )
    pf, err, issues = period_totals.fair_total(
        "nba", "q1", "Home", "Away",
        datetime(2026, 10, 20, tzinfo=timezone.utc),
        53.5, True, {},
    )
    assert err is None
    assert issues == []
    assert pf is not None
    assert pf.sample_games == len(hist)
    assert pf.fair_odds > 1.0
    assert 0.0 < pf.probability < 1.0
    assert pf.expected_total > 0


def test_period_total_quarter_line_settlement():
    pmf = [(50, 0.25), (51, 0.25), (52, 0.25), (53, 0.25)]
    over = period_totals._fair_from_pmf(pmf, 51.25, True)
    under = period_totals._fair_from_pmf(pmf, 51.25, False)
    assert over is not None and under is not None
    assert over[0] > 1.0
    assert under[0] > 1.0


def test_period_points_extracts_q1_half_and_p1():
    from oddswatch.sources.espn import EspnGame, Team
    g = EspnGame(
        "g", "nba",
        datetime(2026, 10, 20, tzinfo=timezone.utc),
        Team("Home"), Team("Away"), "STATUS_FINAL",
        home_score=100, away_score=90,
        home_periods=(24, 26, 25, 25),
        away_periods=(20, 22, 23, 25),
    )
    assert period_totals._period_points(g, "q1") == (24, 20)
    assert period_totals._period_points(g, "1h") == (50, 42)
    assert period_totals._period_points(g, "p1") == (24, 20)
