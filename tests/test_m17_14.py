from oddswatch.m17_14_research import _poisson_1x2


def test_m17_14_poisson_probabilities_sum_to_one():
    p = _poisson_1x2(1.6, 1.1)
    assert abs(sum(p) - 1.0) < 1e-12
    assert all(0.0 < x < 1.0 for x in p)


def test_m17_14_equal_xg_is_symmetric_home_away():
    p = _poisson_1x2(1.3, 1.3)
    assert abs(p[0] - p[2]) < 1e-12


def test_m17_14_higher_home_xg_raises_home_probability():
    neutral = _poisson_1x2(1.2, 1.2)
    stronger = _poisson_1x2(2.0, 1.2)
    assert stronger[0] > neutral[0]
    assert stronger[2] < neutral[2]
