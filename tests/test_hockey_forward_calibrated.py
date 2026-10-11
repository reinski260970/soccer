"""Forward hockey model uses only prior seasons and never places bets."""
from datetime import datetime,timedelta,timezone
from oddswatch import hockey_forward_calibrated as fc


def _event(now,home="KooKoo",away="Jukurit",league="liiga",delta=24):
    return {"event_id":"fake:"+home+away,"league":league,
            "home_name":home,"away_name":away,
            "kickoff":now+timedelta(hours=delta),"season_type":"regular"}


def test_new_calibration_shadow_is_two_way_no_signals(monkeypatch):
    now=datetime(2026,10,11,18,tzinfo=timezone.utc)
    seen=[]
    class Model:
        def markets(self,home,away):
            seen.append((home,away))
            return {"1":.55,"X":.25,"2":.20}
    def fake_fit(rows,season):
        assert season==2026
        return Model(),[None]*400,[.45,.25,.30]
    monkeypatch.setattr(fc.calibrate,"_fit",fake_fit)
    monkeypatch.setattr(fc,"_best_preseason_weight",lambda rows,season:(.25,300))
    bundle,issues=fc.build_bundle([_event(now)],[],now)
    assert not issues
    assert seen==[("KooKoo Kouvola","Jukurit Mikkeli")]
    assert len(bundle["model_versions"])==1
    assert bundle["model_versions"][0]["approved"] is False
    ps=bundle["predictions"]
    assert len(ps)==2
    assert {p["selection"] for p in ps}=={"HOME","AWAY"}
    assert abs(sum(p["probability"] for p in ps)-1)<1e-9
    assert all(p["quality"]=="LOW" for p in ps)
    assert all(p["features"]["ot_conversion_unvalidated"] for p in ps)
    assert all(p["as_of"]<now+timedelta(days=1) for p in ps)
    assert "signals" not in bundle


def test_unknown_team_remains_unscored_not_guessed(monkeypatch):
    now=datetime(2026,10,11,18,tzinfo=timezone.utc)
    class Model:
        def markets(self,home,away):
            raise KeyError("Unknown")
    monkeypatch.setattr(fc.calibrate,"_fit",lambda rows,season:(Model(),[None]*500,[.4,.25,.35]))
    monkeypatch.setattr(fc,"_best_preseason_weight",lambda rows,season:(.5,250))
    bundle,issues=fc.build_bundle([_event(now,home="Mystery Team")],[],now)
    assert not bundle["predictions"]
    assert issues[0]["reason"]=="UNMATCHED_TEAM_OR_INVALID_PROBABILITY"


def test_calibration_requires_prior_complete_season(monkeypatch):
    now=datetime(2026,10,11,18,tzinfo=timezone.utc)
    monkeypatch.setattr(fc.calibrate,"_fit",lambda rows,season:(None,[],None))
    monkeypatch.setattr(fc,"_best_preseason_weight",lambda rows,season:(None,0))
    bundle,issues=fc.build_bundle([_event(now)],[],now)
    assert bundle["predictions"]==[]
    assert issues[0]["reason"]=="NO_PAST_SEASON_CALIBRATION"


def test_started_or_too_distant_games_are_not_backfilled(monkeypatch):
    now=datetime(2026,10,11,18,tzinfo=timezone.utc)
    monkeypatch.setattr(fc.calibrate,"_fit",lambda *args: (_ for _ in ()).throw(AssertionError("No fit expected")))
    bundle,issues=fc.build_bundle([_event(now,delta=-2),_event(now,delta=99)],[],now)
    assert not bundle["predictions"] and not issues
