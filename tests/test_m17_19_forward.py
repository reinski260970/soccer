from datetime import date
import oddswatch.m17_19_forward as fwd

def test_scope_is_only_epl_and_primeira():
    assert set(fwd.SCOPE) == {"epl","primeira"}

def test_season_year_uses_european_start():
    assert fwd._season_year(date(2026,10,12)) == 2026
    assert fwd._season_year(date(2027,3,1)) == 2026

def test_forward_predict_uses_only_rows_before_target(monkeypatch):
    seen=[]
    def fake_base(train,test,l2,calib):
        seen.extend(r["date"] for r in train)
        return [[0.60,0.20,0.20]]
    def fake_hgb(train,test,params):
        seen.extend(r["date"] for r in train)
        return [[0.40,0.30,0.30]]
    monkeypatch.setattr(fwd,"_fit_predict",fake_base)
    monkeypatch.setattr(fwd,"_fit_raw",fake_hgb)
    monkeypatch.setattr(fwd,"_calibrate",lambda p,a:p)

    data=[
        {"date":date(2025,1,1),"x":[1],"y":i % 3}
        for i in range(500)
    ] + [
        {"date":date(2026,10,20),"x":[1],"y":1},
    ]
    target={"date":date(2026,10,15),"x":[1],"y":1}
    cfg={
        "base_hyper":{"l2":1.0,"calib":1.0},
        "hgb_hyper":{"params":{},"calib":1.0},
        "blend":{"hgb_weight":0.15},
    }
    pb,ph,pe,gap=fwd._predict(data,target,cfg)
    assert max(seen) < target["date"]
    assert pb == [0.60,0.20,0.20]
    assert ph == [0.40,0.30,0.30]
    assert all(abs(a-b) < 1e-12 for a,b in zip(pe,[0.57,0.215,0.215]))
    assert abs(gap-0.20) < 1e-12
