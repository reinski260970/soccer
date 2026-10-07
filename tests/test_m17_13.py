from oddswatch.m17_13_research import (
    _quantile,
    _entry_stats_uncertainty,
)


def _row(u, y=2):
    return {
        "p": [0.25, 0.25, 0.50],
        "op": [4.0, 4.0, 2.20],
        "cl": [4.0, 4.0, 2.00],
        "y": y,
        "structural_uncertainty": u,
        "home_structural_uncertainty": u / 2,
        "away_structural_uncertainty": u,
    }


def test_m17_13_quantile_interpolates():
    vals = [0.1, 0.2, 0.3, 0.4]
    assert abs(_quantile(vals, 0.5) - 0.25) < 1e-12


def test_m17_13_uncertainty_filter_is_pre_match_gate():
    rows = [_row(0.10), _row(0.40)]
    s = _entry_stats_uncertainty(
        rows,
        edge=0.05,
        cap=3.0,
        side="away",
        max_uncertainty=0.20,
    )
    assert s["bets"] == 1
    assert s["clv"] > 0
