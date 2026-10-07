from oddswatch.m17_5_research import _choose_gate


def _row(p, op, cl, y=2):
    return {"p": p, "op": op, "cl": cl, "y": y}


def test_m17_5_gate_accepts_robust_positive_clv():
    y22 = []
    y23 = []
    for i in range(24):
        r = _row([0.24, 0.24, 0.52], [4.0, 4.0, 2.05], [4.0, 4.0, 1.92])
        (y22 if i < 12 else y23).append(r)
    for i in range(24):
        r = _row([0.22, 0.23, 0.55], [4.0, 4.0, 2.00], [4.0, 4.0, 1.88])
        (y22 if i < 12 else y23).append(r)

    gate, near = _choose_gate({2022: y22, 2023: y23})
    assert gate is not None
    assert gate["stats"]["bets"] >= 40
    assert gate["stats"]["clv"] > 0
    assert gate["stats"]["median_clv"] > 0
    assert gate["stats"]["positive_clv_rate"] >= 0.52
    assert near is not None


def test_m17_5_gate_rejects_negative_clv():
    y22 = [_row([0.24, 0.24, 0.52], [4.0, 4.0, 2.05], [4.0, 4.0, 2.20]) for _ in range(24)]
    y23 = [_row([0.22, 0.23, 0.55], [4.0, 4.0, 2.00], [4.0, 4.0, 2.15]) for _ in range(24)]
    gate, near = _choose_gate({2022: y22, 2023: y23})
    assert gate is None
    assert near is not None
