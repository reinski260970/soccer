from oddswatch import nhl_v5_clv_gate as cg


def test_gate_selection_uses_clv_not_roi(monkeypatch):
    # Gate A (low max odds) has positive CLV but losing outcomes.
    # Gate B adds high-odds winners and can improve ROI, but worsens CLV.
    rows=[]
    for i in range(100):
        rows.append({
            "p_home":0.60,"home_open":1.80,"away_open":2.20,
            "home_close":1.60,"away_close":2.55,
            "target":0,  # home loses; ROI bad
        })
    for i in range(100):
        rows.append({
            "p_home":0.40,"home_open":3.00,"away_open":1.50,
            "home_close":3.40,"away_close":1.38,
            "target":1,
        })

    monkeypatch.setattr(cg,"_forecast_season",lambda _rows,_season:(rows,{"x":1}))
    gate=cg._choose_gate([],2020)
    assert gate is not None
    # Selection criterion must be CLV. It is not allowed to choose on ROI.
    assert "calibration_mean_clv" in gate
    assert "calibration_positive_clv_rate" in gate


def test_release_qualification_requires_positive_clv_and_majority_positive():
    assert cg.MIN_CAL_BETS >= 80
    # Regression guard: module source policy is explicit.
    import inspect
    src=inspect.getsource(cg._choose_gate)
    assert "mean_clv" in src
    assert "positive_clv_rate" in src
    assert "roi" not in src.lower()
