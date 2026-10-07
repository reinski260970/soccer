from oddswatch.m17_16_research import _tune_gate_2022, _validate_gate_2023


def _row(p_away=0.55, opening=2.0, closing=1.90, y=2):
    return {
        "p": [0.20, 0.25, p_away],
        "op": [4.0, 4.0, opening],
        "cl": [4.0, 4.0, closing],
        "y": y,
    }


def test_m17_16_tunes_only_on_2022_rows():
    rows = [_row() for _ in range(30)]
    gate, near = _tune_gate_2022(rows)
    assert gate is not None
    assert gate["side"] == "away"
    assert gate["stats_2022"]["bets"] >= 20
    assert near is not None


def test_m17_16_2023_validation_rejects_negative_clv():
    rows_2022 = [_row() for _ in range(30)]
    gate, _ = _tune_gate_2022(rows_2022)
    bad_2023 = [_row(closing=2.20) for _ in range(20)]
    ok, stats = _validate_gate_2023(bad_2023, gate)
    assert not ok
    assert stats["clv"] < 0
    assert stats["fails"]


def test_m17_16_2023_validation_accepts_robust_positive_clv():
    rows_2022 = [_row() for _ in range(30)]
    gate, _ = _tune_gate_2022(rows_2022)
    good_2023 = [_row(closing=1.88) for _ in range(20)]
    ok, stats = _validate_gate_2023(good_2023, gate)
    assert ok
    assert stats["clv"] > 0
