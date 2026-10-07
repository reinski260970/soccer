import oddswatch.m17_12_research as m17


def test_m17_12_carry_grid_contains_no_reset_and_decay():
    assert (1.0, 1.0) in m17.CARRY_GRID
    assert any(f < 1.0 and s < 1.0 for f, s in m17.CARRY_GRID)
    assert all(0.0 <= f <= 1.0 and 0.0 <= s <= 1.0 for f, s in m17.CARRY_GRID)


def test_m17_12_selects_carry_only_by_early_logloss(monkeypatch):
    scores = {
        (1.00, 1.00): 0.99,
        (0.65, 0.85): 0.95,
        (0.40, 0.75): 0.93,
        (0.20, 0.60): 0.94,
        (0.00, 0.50): 0.96,
    }

    def fake_build(matches, odds_rows, shots, fast, slow):
        return ([{"score": scores[(fast, slow)]}], {}, {})

    def fake_hyper(data):
        return {"cv_logloss": data[0]["score"], "l2": 1.0, "calib": 1.0}

    monkeypatch.setattr(m17, "_build_with_carry", fake_build)
    monkeypatch.setattr(m17, "_early_hyper", fake_hyper)

    best, candidates = m17._select_carry([], [], {})
    assert best is not None
    assert best[0]["fast_carry"] == 0.40
    assert best[0]["slow_carry"] == 0.75
    assert len(candidates) == len(m17.CARRY_GRID)
