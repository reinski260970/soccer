from oddswatch.m14_research import fit_proxy, proxy_xg, _features


def test_m14_features():
    x = _features(10, 4, 5, True)
    assert x == [1.0, 4.0, 6.0, 5.0, 1.0]


def test_m14_proxy_fit_recovers_positive_signal():
    rows = []
    for i in range(1200):
        sot = float(i % 7)
        off = float((i * 3) % 10)
        cor = float((i * 5) % 8)
        home = float(i % 2)
        x = [1.0, sot, off, cor, home]
        y = 0.20 + 0.28*sot + 0.04*off + 0.02*cor + 0.08*home
        rows.append((x, y))
    p = fit_proxy(rows, ridge=0.01)
    assert p["n"] == 1200
    assert p["rmse"] < 0.02
    assert p["beta"][1] > 0.20
    assert p["beta"][2] > 0.0
    assert p["beta"][3] >= 0.0


def test_m14_proxy_xg_is_bounded():
    p = {"beta": [0.1, 0.3, 0.04, 0.02, 0.05]}
    assert 0.05 <= proxy_xg(p, 12, 5, 4, True) <= 5.5
