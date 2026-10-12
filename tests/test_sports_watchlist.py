from datetime import datetime, timedelta, timezone

from oddswatch.sports_watchlist import (
    sport_for_league,
    state,
    target_ev,
    trigger_odds,
)


def test_sport_mapping():
    assert sport_for_league("bundesliga") == "soccer"
    assert sport_for_league("nhl") == "hockey"
    assert sport_for_league("euroleague") == "basketball"
    assert sport_for_league("nfl") == "nfl"
    assert sport_for_league("atp") == "tennis"


def test_market_specific_ev_thresholds():
    assert target_ev("soccer", "moneyline") == 0.020
    assert target_ev("soccer", "total") == 0.015
    assert target_ev("soccer", "btts") == 0.018
    assert target_ev("hockey", "moneyline") == 0.030
    assert target_ev("basketball", "spread") == 0.030
    assert target_ev("nfl", "moneyline") == 0.030
    assert target_ev("tennis", "moneyline") == 0.020


def test_trigger_and_state():
    now = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
    kickoff = now + timedelta(days=1)
    trig = trigger_odds(2.00, "soccer", "moneyline")
    assert abs(trig - 2.04) < 1e-12
    assert state(kickoff=kickoff, now=now, executable_odds=None, trigger=trig) == "WATCH"
    assert state(kickoff=kickoff, now=now, executable_odds=2.05, trigger=trig) == "TRIGGERED"
    assert state(kickoff=now, now=now, executable_odds=2.05, trigger=trig) == "EXPIRED"
