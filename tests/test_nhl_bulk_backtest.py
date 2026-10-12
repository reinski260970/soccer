from datetime import date

from oddswatch import nhl_bulk_backtest as nb
from oddswatch import nhl_bulk_import as ni


def test_american_odds_conversion():
    assert abs(nb.american_to_decimal(150)-2.5)<1e-12
    assert abs(nb.american_to_decimal(-200)-1.5)<1e-12


def test_devig_two_way():
    p=nb._devig_home(2.0,2.0)
    assert abs(p-.5)<1e-12
    p=nb._devig_home(1.5,3.0)
    assert p>.5


def test_bulk_normalizer_rejects_duplicates_and_missing_close():
    base={
        "season":2020,"date":20201001.0,"home_team":"A","away_team":"B",
        "home_1stPeriod":"1","away_1stPeriod":"0",
        "home_2ndPeriod":"1","away_2ndPeriod":"1",
        "home_3rdPeriod":"1","away_3rdPeriod":"0",
        "home_final":"3","away_final":"1",
        "home_open_ml":-120,"away_open_ml":110,
        "home_close_ml":-125,"away_close_ml":115,
        "open_over_under":5.5,"open_over_under_odds":-110,
        "close_over_under":5.5,"close_over_under_odds":-115,
    }
    rows,stats=ni.normalize([base,dict(base)])
    assert len(rows)==1
    assert stats["rejected"]==1
    assert rows[0]["reg_home"]==3
    assert rows[0]["reg_away"]==1


def test_fit_uses_only_prior_seasons(monkeypatch):
    rows=[]
    for season in (2011,2012,2013):
        for i in range(500):
            rows.append({
                "season":season,
                "date":date(season,10,1),
                "home":"A","away":"B",
                "reg_home":3,"reg_away":2,
                "final_home":3,"final_away":2,
                "home_open":2.0,"away_open":2.0,
                "home_close":2.0,"away_close":2.0,
            })
    seen=[]
    class Fake:
        pass
    def fake_fit(matches,as_of,**kw):
        seen.extend(m.date for m in matches)
        return Fake()
    monkeypatch.setattr(nb.PoissonModel,"fit",staticmethod(fake_fit))
    model,training,base=nb._fit(rows,2013)
    assert model is not None
    assert len(training)==1000
    assert all(d<date(2013,7,1) for d in seen)
