import oddswatch.m17_18_hgb_research as m18

def _rows(season,n):
    return [{"season":season,"x":[1.0,0.0],"y":0} for _ in range(n)]

def test_hgb_grid_is_small_and_regularized():
    assert 2 <= len(m18.GRID) <= 8
    assert all(p["l2_regularization"] > 0 for p in m18.GRID)
    assert all(p["min_samples_leaf"] >= 20 for p in m18.GRID)

def test_hyper_selection_never_sees_post_2021(monkeypatch):
    seen=[]
    def fake_fit(train,test,params):
        seen.extend(r["season"] for r in train+test)
        p=[0.80,0.10,0.10] if params["max_leaf_nodes"]==15 else [0.60,0.20,0.20]
        return [p[:] for _ in test]
    monkeypatch.setattr(m18,"_fit_raw",fake_fit)
    data=_rows(2019,500)+_rows(2020,100)+_rows(2021,100)+_rows(2022,100)+_rows(2024,100)
    best=m18.select_hyper(data)
    assert best is not None
    assert max(seen) <= 2021
    assert best["params"]["max_leaf_nodes"] == 15

def test_challenger_covers_main_13_leagues_only():
    assert len(m18.LEAGUES) == 13
    assert "bundesliga" in m18.LEAGUES
    assert "primeira" in m18.LEAGUES
    assert "austria" not in m18.LEAGUES
