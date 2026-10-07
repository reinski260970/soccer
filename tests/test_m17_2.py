from oddswatch.m17_2_research import _choose_gate


def _row(p, op, cl, y=2):
    return {
        "p": p,
        "op": op,
        "cl": cl,
        "y": y,
    }


def test_m17_2_robust_away_gate_can_validate_tune():
    rows22 = []
    rows23 = []
    for i in range(20):
        # Away model EV >2%; opening 2.0, closing 1.90 => positive CLV.
        r = _row([0.20, 0.25, 0.55], [4.0, 4.0, 2.0], [4.0, 4.0, 1.90])
        (rows22 if i < 10 else rows23).append(r)
    # Need >=30 total and >=8 each year.
    for i in range(20):
        r = _row([0.19, 0.25, 0.56], [4.0, 4.0, 2.0], [4.0, 4.0, 1.88])
        (rows22 if i < 10 else rows23).append(r)

    gate, near = _choose_gate({2022: rows22, 2023: rows23})
    assert gate is not None
    assert gate["side"] == "away"
    assert gate["cap"] == 2.5
    assert gate["stats"]["bets"] >= 30
    assert gate["stats"]["clv"] > 0
    assert near is not None


def test_m17_2_rejects_negative_clv():
    rows = [
        _row([0.25, 0.25, 0.50], [4.0, 4.0, 2.0], [4.0, 4.0, 2.20])
        for _ in range(40)
    ]
    gate, near = _choose_gate({2022: rows[:20], 2023: rows[20:]})
    assert gate is None
    assert near is not None
    assert any("clv<=0" in x or "mean_clv<=0" in x for x in near["fails"])
