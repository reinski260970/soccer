import oddswatch.m17_19_ensemble_research as m19

def _row(pb=0.56,ph=0.55,p=0.555,opening=2.0,closing=1.90,y=2,gap=0.01):
    return {
        "p_base":[0.20,0.24,pb],
        "p_hgb":[0.21,0.24,ph],
        "p":[0.205,0.24,p],
        "op":[4.0,4.0,opening],
        "cl":[4.0,4.0,closing],
        "y":y,
        "model_gap":gap,
    }

def test_alpha_grid_keeps_structural_model_primary():
    assert 0.0 in m19.ALPHA_GRID
    assert max(m19.ALPHA_GRID) <= 0.60

def test_entry_requires_component_agreement():
    good=[_row() for _ in range(25)]
    s=m19._entry_stats(good,0.02,2.5,0.05)
    assert s["bets"]==25
    disagree=[_row(gap=0.10) for _ in range(25)]
    s2=m19._entry_stats(disagree,0.02,2.5,0.05)
    assert s2["bets"]==0

def test_entry_requires_both_models_positive_ev():
    rows=[_row(ph=0.49,p=0.53,gap=0.04) for _ in range(25)]
    s=m19._entry_stats(rows,0.02,2.5,0.05)
    assert s["bets"]==0

def test_2023_validation_reuses_2022_agreement_gate():
    rows22=[_row() for _ in range(30)]
    gate,_=m19.tune_gate_2022(rows22)
    assert gate is not None
    bad23=[_row(closing=2.20) for _ in range(20)]
    ok,stats=m19.validate_2023(bad23,gate)
    assert not ok
    assert stats["clv"]<0
