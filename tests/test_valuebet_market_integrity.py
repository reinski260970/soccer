"""Exact market orientation and fail-closed WATCH persistence regression tests."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pytest

from oddswatch import surebet_values
from oddswatch.sql import valuebet


def _fixture():
    start=datetime.now(timezone.utc)+timedelta(days=1)
    return NS(
        sport="hockey",league="nhl",detail="erw. Tore 2.5:0.5",
        model="shadow-research",probs={"home":.8,"away":.2},
        game=NS(id="test-match",kickoff=start,status="STATUS_SCHEDULED",
                home=NS(name="Alpha United"),away=NS(name="Beta United"))
    )


def _value(fx, bet_type, teams=None, line="0", odds=2.1):
    return NS(sport="Hockey",tournament="NHL",bookmaker="bet365",back=True,
        teams=teams or ("Alpha United","Beta United"),
        kickoff=fx.game.kickoff,bet_type=bet_type,condition=line,
        period="regularTime",base="overall",odds=odds,commission=0.0,
        created=None,ev=.10,id="example-id",market="Match winner",
        selection="Alpha United")


@pytest.mark.parametrize("market,line",[
    ("win1","0"),("win2","0"),("ah1","-1.5"),("ah2","1.5"),
    ("over","1.5"),("under","1.5"),("eh1","-1"),
])
def test_reverse_source_teams_reorients_entire_score_model(market,line):
    fx=_fixture()
    direct=_value(fx,market,line=line)
    reverse=_value(fx,market,teams=("Beta United","Alpha United"),line=line)
    f,p,ev,note=surebet_values._poisson_market_fair(direct,fx)
    f2,p2,ev2,note2=surebet_values._poisson_market_fair(reverse,fx)
    assert p is not None and p2 is not None, (market,note,note2)
    assert 0<p<1 and 0<p2<1
    # Totals are invariant under reversal; home/away moneyline flips sides.
    if market in ("over","under"):
        assert p2==pytest.approx(p)
    if market=="win1":
        counterpart=_value(fx,"win2")
        expected=surebet_values._poisson_market_fair(counterpart,fx)[1]
        assert p2==pytest.approx(expected)


def test_reversed_two_way_moneyline_selects_api_side():
    fx=_fixture()
    v=_value(fx,"winOnly1",teams=("Beta United","Alpha United"))
    _,p,_,_=surebet_values._model_probability(v,fx)
    assert p==pytest.approx(.2)


def test_reverse_or_unmatched_source_does_not_create_stored_wrong_market():
    fx=_fixture()
    assert valuebet._match_fixture(_value(fx,"ah1"),[fx]) is fx
    assert valuebet._match_fixture(
        _value(fx,"ah1",teams=("Beta United","Alpha United")),[fx]) is None
    assert valuebet._match_fixture(
        _value(fx,"ah1",teams=("Gamma United","Beta United")),[fx]) is None


def test_negative_and_rejected_valuebets_stored_for_research_not_as_watches(monkeypatch):
    monkeypatch.setenv("SPORTS_DATABASE_URL","fake-for-test")
    fx=_fixture()
    def _audit(status,market,ev,probability):
        return NS(status=status,our_probability=probability,
                  our_fair=1/probability,our_ev=ev,note="synthetic test",
                  value=_value(fx,market))
    captured=[]
    class Ctx:
        def __enter__(self):return self
        def __exit__(self,*args):return False
    monkeypatch.setattr(valuebet,"connect",lambda:Ctx())
    monkeypatch.setattr(valuebet,"migrate",lambda conn:None)
    def fake_ingest(conn,bundle):
        captured.append(bundle)
        return {"predictions":len(bundle["predictions"]),"signals":len(bundle["signals"])}
    monkeypatch.setattr(valuebet,"ingest",fake_ingest)
    out=valuebet.persist_audits([
        _audit("BESTÄTIGT","winOnly1",.055,.55),
        _audit("WIDERLEGT","winOnly2",-.20,.28),
        _audit("REDUZIERT","under",-.04,.40),
    ],[fx])
    assert out["predictions"]==3 and out["signals"]==1
    bundle=captured[0]
    assert all(p["quality"]=="LOW" for p in bundle["predictions"])
    assert all(p["features"]["release_eligible"] is False for p in bundle["predictions"])
    assert bundle["signals"][0]["stake_eh"]==0
    assert bundle["signals"][0]["signal_type"]=="WATCH"


def test_full_game_hockey_must_not_use_regulation_goal_model():
    fx=_fixture()
    full=_value(fx,"over",line="5.5")
    full.period="fullTime"
    fair,p,ev,note=surebet_values._poisson_market_fair(full,fx)
    assert fair is None and p is None and ev is None
    assert "Full-Game" in note
    regular=_value(fx,"over",line="5.5")
    assert surebet_values._poisson_market_fair(regular,fx)[1] is not None
