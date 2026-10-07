from oddswatch.m17_3_research import _blend, _choose_gate


def _row(p_away, opening=2.0, closing=1.90, y=2):
    return {
        "p": [0.22, 0.23, p_away],
        "op": [4.0, 4.0, opening],
        "cl": [4.0, 4.0, closing],
        "y": y,
    }


def test_blend_respects_local_weight():
    local = [0.20, 0.25, 0.55]
    pooled = [0.30, 0.30, 0.40]
    assert _blend(local, pooled, 1.0) == local
    assert _blend(local, pooled, 0.0) == pooled
    mid = _blend(local, pooled, 0.5)
    assert abs(mid[2] - 0.475) < 1e-12


def test_m17_3_gate_requires_robust_positive_clv():
    a = [_row(0.55) for _ in range(18)]
    b = [_row(0.56, closing=1.88) for _ in range(18)]
    gate, near = _choose_gate({2022: a, 2023: b})
    assert gate is not None
    assert gate["side"] == "away"
    assert gate["stats"]["bets"] >= 30
    assert gate["stats"]["clv"] > 0
    assert near is not None


def test_m17_3_gate_rejects_negative_clv():
    a = [_row(0.55, closing=2.15) for _ in range(20)]
    b = [_row(0.56, closing=2.20) for _ in range(20)]
    gate, near = _choose_gate({2022: a, 2023: b})
    assert gate is None
    assert near is not None
