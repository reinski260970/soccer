from datetime import datetime, timezone

from oddswatch import period_value_watch
from oddswatch.sources.surebet import SurebetValue


def _v(sport, tournament, period, base="overall"):
    return SurebetValue(
        id="1",
        sport=sport,
        tournament=tournament,
        teams=("Home", "Away"),
        kickoff=datetime(2026, 10, 12, 18, 0, tzinfo=timezone.utc),
        selection="x",
        market="x",
        odds=1.95,
        probability=None,
        overvalue=None,
        bet_type="over",
        condition="22.5",
        period=period,
        base=base,
    )


def test_fast_period_candidate_scope():
    assert period_value_watch._fast_period_candidate(_v("Basketball", "NBA", "q1"))
    assert period_value_watch._fast_period_candidate(_v("Basketball", "NBA", "2h"))
    assert period_value_watch._fast_period_candidate(_v("American football", "NFL", "q4"))
    assert period_value_watch._fast_period_candidate(_v("Hockey", "NHL", "p3"))
    assert period_value_watch._fast_period_candidate(_v("Hockey", "Finland Liiga", "p1"))

    assert not period_value_watch._fast_period_candidate(_v("Basketball", "EuroLeague", "q1"))
    assert not period_value_watch._fast_period_candidate(_v("Hockey", "Finland Liiga", "p2"))
    assert not period_value_watch._fast_period_candidate(_v("Basketball", "NBA", "q1", base="team1"))
