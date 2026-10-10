import math

import pytest

from oddswatch.models.goal_markets import (
    AsianPrice,
    asian_probability,
    goal_markets,
)


def test_synthetic_home_quarter_handicap_counts_half_losses():
    # Exact regulation scores 0-0 (0.2), 1-0 (0.5), 0-1 (0.3).
    matrix = [[0.2, 0.3], [0.5, 0.0]]
    price = asian_probability(matrix, kind="asian_handicap",
                              selection="HOME", line=-0.25)
    assert price.win_fraction == pytest.approx(0.5)
    assert price.lose_fraction == pytest.approx(0.4)
    assert price.push_fraction == pytest.approx(0.1)
    assert price.fair_odds == pytest.approx(1.8)
    assert price.ev(1.8) == pytest.approx(0)


def test_synthetic_over_quarter_total_half_push_half_loss():
    matrix = [[0.0, 0.0, 1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    price = asian_probability(matrix, kind="total",
                              selection="OVER", line=2.25)
    assert price.win_fraction == pytest.approx(0)
    assert price.lose_fraction == pytest.approx(0.5)
    assert price.push_fraction == pytest.approx(0.5)
    assert math.isinf(price.fair_odds)


def test_total_and_handicap_side_symmetry():
    mat, _ = goal_markets(1.6, 1.2)
    o = asian_probability(mat, kind="total", selection="OVER", line=2.5)
    u = asian_probability(mat, kind="total", selection="UNDER", line=2.5)
    assert o.win_fraction + u.win_fraction == pytest.approx(1)
    assert o.fair_odds == pytest.approx(1/o.win_fraction)
    home = asian_probability(mat, kind="asian_handicap", selection="HOME", line=-0.5)
    away = asian_probability(mat, kind="asian_handicap", selection="AWAY", line=0.5)
    assert home.win_fraction + away.win_fraction == pytest.approx(1)
    assert home.ev(home.fair_odds) == pytest.approx(0)


def test_score_distribution_prices_are_coherent():
    m, markets = goal_markets(1.45, 1.20)
    assert sum(map(sum, m)) == pytest.approx(1)
    assert markets["1"] + markets["X"] + markets["2"] == pytest.approx(1)
    assert markets["O2.5"] + markets["U2.5"] == pytest.approx(1)
    assert markets["BTTS_Y"] + markets["BTTS_N"] == pytest.approx(1)
    p = asian_probability(m, kind="total", selection="OVER", line=2.5)
    assert markets["O2.5"] == pytest.approx(p.win_fraction)


@pytest.mark.parametrize("line", [-0.25, 0.0, 0.25, 0.75, 1.25, -1.75])
def test_exact_asian_fair_odds_have_zero_ev(line):
    matrix, _ = goal_markets(1.3, 1.1)
    for selection in ("HOME", "AWAY"):
        p = asian_probability(matrix, kind="asian_handicap",
                              selection=selection, line=line)
        if math.isfinite(p.fair_odds):
            assert p.ev(p.fair_odds) == pytest.approx(0, abs=1e-10)


@pytest.mark.parametrize("line", [2.25, 2.5, 2.75, 3.0, 3.25])
def test_exact_quarter_ou_fair_odds_zero_ev(line):
    matrix, _ = goal_markets(1.8, 1.6)
    for side in ("OVER", "UNDER"):
        p = asian_probability(matrix, kind="total", selection=side, line=line)
        assert p.ev(p.fair_odds) == pytest.approx(0, abs=1e-10)


def test_invalid_market_and_probability_rejected():
    matrix, _ = goal_markets(1.3, 1.1)
    with pytest.raises(ValueError):
        asian_probability(matrix, kind="total", selection="OVER", line=2.3)
    with pytest.raises(ValueError):
        asian_probability(matrix, kind="total", selection="DRAW", line=2.5)
    with pytest.raises(ValueError):
        goal_markets(0, 2)
    with pytest.raises(ValueError):
        goal_markets(1.5, 1.1, rho=-0.5)
    with pytest.raises(ValueError):
        AsianPrice(0.4, 0.5, 0.1).ev(1)
