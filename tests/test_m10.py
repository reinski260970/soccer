from oddswatch.m10_research import choose_gate


def _row(season, pm, po, pc, win, odds):
    y = [False, False, False]
    y[0] = win
    if not win:
        y[1] = True
    return (season, pm, po, pc, y, odds)


def test_m10_requires_both_tuning_seasons_positive_clv():
    rows = []
    # 2023: artificially positive CLV regime
    for _ in range(40):
        rows.append(_row(
            2023,
            [0.62, 0.22, 0.16],
            [0.50, 0.28, 0.22],
            [0.58, 0.24, 0.18],
            True,
            [2.05, 3.5, 5.0],
        ))
    # 2024: same model edge but negative CLV, so no robust gate may pass.
    for _ in range(40):
        rows.append(_row(
            2024,
            [0.62, 0.22, 0.16],
            [0.50, 0.28, 0.22],
            [0.45, 0.30, 0.25],
            True,
            [2.05, 3.5, 5.0],
        ))
    cfg, stats = choose_gate(rows, 1.0, {2023, 2024})
    assert cfg is None
    assert stats is None
