from oddswatch.m17_9_research import _class_bias


def test_m17_9_neutral_class_bias_is_identity():
    p = [0.48, 0.27, 0.25]
    out = _class_bias(p, 1.0, 1.0)
    assert all(abs(a - b) < 1e-12 for a, b in zip(out, p))


def test_m17_9_draw_and_away_bias_renormalize():
    p = [0.50, 0.25, 0.25]
    out = _class_bias(p, 1.10, 1.05)
    assert abs(sum(out) - 1.0) < 1e-12
    assert out[1] > p[1]
    assert out[2] > p[2]
    assert out[0] < p[0]
