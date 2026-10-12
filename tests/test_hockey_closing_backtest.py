from datetime import date

from oddswatch import hockey_closing_backtest as hb


def test_devig_sums_to_one():
    p=hb._devig([2.0,4.0,4.0])
    assert abs(sum(p)-1)<1e-12
    assert p[0] > p[1]


def test_resolve_is_fail_closed():
    teams={"Vienne","Klagenfurt"}
    assert hb._resolve("Vienna","icehl",teams)=="Vienne"
    assert hb._resolve("Klagenfurt","icehl",teams)=="Klagenfurt"
    assert hb._resolve("Unknown","icehl",teams) is None


def test_run_labels_reference_roi_not_true_clv(tmp_path, monkeypatch):
    market=tmp_path/"market.csv"
    market.write_text(
        "date,league,home_team,away_team,home_score,away_score,finish_status,reg_result,close_home,close_draw,close_away,source_url\n"
        "2026-10-01,NHL,A,B,3,1,FIN,HOME,2.10,4.00,3.00,x\n",
        encoding="utf-8",
    )
    history=[
        {"league":"nhl","season":"2025/26","date":date(2026,1,1),"home":"A","away":"B","home_goals":3,"away_goals":2}
    ]
    class Model:
        attack={"A":0,"B":0}
    monkeypatch.setattr(hb,"load_history",lambda *a,**k:history)
    monkeypatch.setattr(hb,"_fit",lambda *a,**k:(Model(),history,[.4,.2,.4]))
    monkeypatch.setattr(hb,"_choose_alpha",lambda *a,**k:1.0)
    monkeypatch.setattr(hb,"_prob",lambda *a,**k:[.55,.20,.25])
    out=hb.run(history_path="unused",market_path=market,dest=tmp_path/"out.json")
    assert out["true_clv"] is None
    assert out["production_roi"] is None
    assert out["leagues"]["nhl"]["matched"]==1
    assert out["leagues"]["nhl"]["bets"]==1
