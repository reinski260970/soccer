"""Profit gate regression: cannot mistake historic reference odds for true CLV."""
import math

import pytest

from oddswatch.profitability_audit import (
    PairedResult, HOCKEY_PAIR_SQL, audit_market, confidence_lower,
    exact_market_ev, playable_to,
)


def _pair(i, gain=.02, day="2026-09-10"):
    return PairedResult(event_id=f"game{i}",league="nhl",day=day,
                        gain_vs_market=gain,source_time_provided=False)


def test_exchange_commission_applies_to_winnings_only():
    assert exact_market_ev(.55,2.0,.03)==pytest.approx(.0835)
    assert exact_market_ev(.5,2.0,.03)==pytest.approx(-.015)
    assert exact_market_ev(.55,2.0,0)==pytest.approx(.1)
    price=playable_to(.55,.03,.02)
    assert exact_market_ev(.55,price,.03)==pytest.approx(.02)


@pytest.mark.parametrize("p,o,fee",[(1.2,2,.03),(-.1,2,.03),(.55,1,.03),
    (.55,2,1),(.55,float("nan"),.03)])
def test_invalid_pricing_fails_closed(p,o,fee):
    with pytest.raises(ValueError):
        exact_market_ev(p,o,fee)


def test_low_sample_never_approves():
    rows=[_pair(i,.1) for i in range(20)]
    audit=audit_market(rows)
    assert audit["betting_release"] is False
    assert "OOS_SAMPLE_LT_250" in audit["hold_reasons"]
    assert "NO_AUTHENTICATED_CLOSING_LINES" in audit["hold_reasons"]
    assert audit["verified_clv_bets"] == 0


def test_positive_historical_results_alone_cannot_turn_into_play():
    rows=[_pair(i,.04,"2026-09-10" if i<150 else "2026-10-10")
          for i in range(300)]
    audit=audit_market(rows)
    assert audit["unique_matches"]==300
    assert audit["paired_gain_95pct_lower"] > 0
    assert audit["betting_release"] is False
    assert "NO_AUTHENTICATED_CLOSING_LINES" in audit["hold_reasons"]
    assert "MEASURED_CLV_SAMPLE_LT_100" in audit["hold_reasons"]


def test_source_timestamp_is_not_same_as_authenticated_executable_close():
    rows=[PairedResult(str(i),"nhl","2026-10-01",.03,True)
          for i in range(500)]
    audit=audit_market(rows)
    assert audit["matched_reference_with_source_timestamps"]==500
    assert not audit["betting_release"]
    assert audit["verified_clv_bets"]==0


def test_duplicate_event_and_bad_gain_rejected():
    with pytest.raises(ValueError,match="duplicate event"):
        audit_market([_pair(1),_pair(1)])
    with pytest.raises(ValueError,match="nonfinite"):
        audit_market([_pair(1,float("nan"))])


def test_negative_model_gain_blocks_even_with_synthetic_clv():
    rows=[_pair(i,-.05,"2026-09-10" if i<200 else "2026-10-10")
          for i in range(400)]
    audit=audit_market(rows,closed_bet_clvs=[.1]*200,
                       independently_verified_closes=True)
    assert audit["paired_gain_95pct_lower"]<0
    assert not audit["betting_release"]
    assert "NO_CONFIDENT_POSITIVE_PAIRED_LOGLOSS_GAIN" in audit["hold_reasons"]


def test_winning_source_timestamp_not_guaranteed_and_oos_sql_is_one_game():
    assert "DISTINCT ON (p.event_id)" in HOCKEY_PAIR_SQL
    assert "p.as_of<e.kickoff" in HOCKEY_PAIR_SQL
    assert "h.observed_at<=f.as_of" in HOCKEY_PAIR_SQL
    assert "a.observed_at=h.observed_at" in HOCKEY_PAIR_SQL
    assert "e.season_type='regular'" in HOCKEY_PAIR_SQL
    assert confidence_lower([1.]) is None
