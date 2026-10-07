from oddswatch.m17_10_research import _previous_season_prior


def test_m17_10_previous_season_prior_uses_y_minus_1_only():
    rows = []
    rows += [{"season": 2019, "y": 0}] * 50
    rows += [{"season": 2019, "y": 1}] * 20
    rows += [{"season": 2019, "y": 2}] * 30
    rows += [{"season": 2018, "y": 2}] * 100

    p = _previous_season_prior(rows, 2020)

    # Laplace-smoothed 2019-only counts -> [51, 21, 31] / 103.
    assert abs(p[0] - 51 / 103) < 1e-12
    assert abs(p[1] - 21 / 103) < 1e-12
    assert abs(p[2] - 31 / 103) < 1e-12


def test_m17_10_previous_season_prior_falls_back_when_sparse():
    rows = [{"season": 2019, "y": 0}] * 10 + [{"season": 2018, "y": 2}] * 90
    p = _previous_season_prior(rows, 2020)
    assert p[2] > p[0]
