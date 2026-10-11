"""No lookahead in league-level hockey calibration weights."""
from datetime import date
from oddswatch import hockey_recalibration as hc


def _row(season, day, i, hg, ag, lg="nhl"):
    return dict(league=lg,season=season,date=date.fromisoformat(day),
                home=f"Home-{i}",away=f"Away-{i}",
                home_goals=hg,away_goals=ag)


def test_calibrate_only_previous_season_and_freeze_weight(monkeypatch):
    past=[_row("2023/24","2023-11-12",i,3,1) for i in range(250)]
    cal=[_row("2024/25","2024-11-12",i,3,1) for i in range(100)]
    future=[_row("2025/26","2025-11-12",i,1,3) for i in range(100)]
    recorded=[]
    class Model:
        pass
    def fake_fit(matches, as_of, **kw):
        recorded.append((as_of,[m.date for m in matches]))
        return Model()
    monkeypatch.setattr(hc.PoissonModel,"fit",staticmethod(fake_fit))
    monkeypatch.setattr(hc,"_prob",lambda model,row:[.65,.15,.20])
    a=hc.evaluate(past+cal+future, test_seasons=("2025/26",))
    report=a["leagues"]["nhl"]["2025/26"]
    assert report["status"]=="EVALUATED_RETROSPECTIVE"
    assert report["training_n"]==350 and report["calibration_scored"]==100
    assert report["evaluated"]==100
    assert {x[0] for x in recorded}=={date(2024,7,1),date(2025,7,1)}
    for cutoff,training_dates in recorded:
        assert all(d<cutoff for d in training_dates)
    # Altering the scored season outcome must not change calibrated weight.
    opposite=[dict(x,home_goals=5,away_goals=1) for x in future]
    b=hc.evaluate(past+cal+opposite,test_seasons=("2025/26",))
    assert (a["leagues"]["nhl"]["2025/26"]["selected_model_weight"]
            ==b["leagues"]["nhl"]["2025/26"]["selected_model_weight"])
    assert a["release_eligible"] is False
    assert a["market_logloss"] if "market_logloss" in a else True


def test_insufficient_previous_season_calibration_fails_closed(monkeypatch):
    rows=[_row("2023/24","2023-10-01",i,2,1) for i in range(220)]
    rows += [_row("2024/25","2024-10-01",i,2,1) for i in range(20)]
    rows += [_row("2025/26","2025-10-01",i,2,1) for i in range(100)]
    class Dummy:
        pass
    monkeypatch.setattr(hc.PoissonModel,"fit",staticmethod(lambda *a,**kw:Dummy()))
    monkeypatch.setattr(hc,"_prob",lambda model,row:[.5,.2,.3])
    r=hc.evaluate(rows,test_seasons=("2025/26",))
    assert r["leagues"]["nhl"]["2025/26"]["status"]=="INSUFFICIENT_PAST_CALIBRATION"


def test_weight_blend_is_proper_probability_vector():
    out=hc._mix([.5,.2,.3],[.4,.25,.35],.5)
    assert out==__import__("pytest").approx([.45,.225,.325])
    assert sum(out)==1.
