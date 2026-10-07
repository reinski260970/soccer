from oddswatch.m17_8_research import _class_prior, _shrink, _prob_diagnostics


def test_m17_8_shrink_zero_keeps_model_probability():
    p = [0.50, 0.30, 0.20]
    prior = [0.40, 0.30, 0.30]
    out = _shrink(p, prior, 0.0)
    assert all(abs(a - b) < 1e-12 for a, b in zip(out, p))


def test_m17_8_shrink_one_uses_training_prior():
    p = [0.50, 0.30, 0.20]
    prior = [0.40, 0.30, 0.30]
    out = _shrink(p, prior, 1.0)
    assert all(abs(a - b) < 1e-12 for a, b in zip(out, prior))
    assert abs(sum(out) - 1.0) < 1e-12


def test_m17_8_class_prior_is_training_only_empirical_distribution():
    rows = [
        {"y": 0},
        {"y": 0},
        {"y": 1},
        {"y": 2},
    ]
    prior = _class_prior(rows)
    # Laplace-smoothed counts: [3, 2, 2] / 7.
    assert abs(prior[0] - 3.0 / 7.0) < 1e-12
    assert abs(prior[1] - 2.0 / 7.0) < 1e-12
    assert abs(prior[2] - 2.0 / 7.0) < 1e-12
    assert abs(sum(prior) - 1.0) < 1e-12


def test_m17_8_probability_diagnostics_reports_class_gap():
    rows = [
        {"p": [0.50, 0.30, 0.20], "y": 0},
        {"p": [0.40, 0.30, 0.30], "y": 2},
    ]
    d = _prob_diagnostics(rows)
    assert d["n"] == 2
    assert abs(d["avg_pred"][0] - 0.45) < 1e-12
    assert abs(d["actual_rate"][0] - 0.50) < 1e-12
    assert abs(d["gap_pred_minus_actual"][0] + 0.05) < 1e-12
