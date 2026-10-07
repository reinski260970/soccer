from oddswatch.m17_4_research import _blend, _calibrate_binary, _choose_gate


def _row(p, opening=2.0, closing=1.90, y=1):
    return {
        "p": p,
        "op": [4.0, 4.0, opening],
        "cl": [4.0, 4.0, closing],
        "y": y,
    }


def test_binary_blend_endpoints():
    assert abs(_blend(0.55, 0.40, 1.0) - 0.55) < 1e-12
    assert abs(_blend(0.55, 0.40, 0.0) - 0.40) < 1e-12
    assert abs(_blend(0.55, 0.40, 0.5) - 0.475) < 1e-12


def test_binary_calibration_stays_probability():
    for p in (0.1, 0.3, 0.5, 0.7, 0.9):
        q = _calibrate_binary(p, 1.1)
        assert 0.0 < q < 1.0


def test_m17_4_gate_accepts_robust_positive_clv():
    a = [_row(0.55) for _ in range(18)]
    b = [_row(0.56, closing=1.88) for _ in range(18)]
    gate, near = _choose_gate({2022: a, 2023: b})
    assert gate is not None
    assert gate["stats"]["bets"] >= 30
    assert gate["stats"]["clv"] > 0
    assert near is not None


def test_m17_4_gate_rejects_negative_clv():
    a = [_row(0.55, closing=2.15) for _ in range(20)]
    b = [_row(0.56, closing=2.20) for _ in range(20)]
    gate, near = _choose_gate({2022: a, 2023: b})
    assert gate is None
    assert near is not None
