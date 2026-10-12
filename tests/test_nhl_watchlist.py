from datetime import datetime, timedelta, timezone

from oddswatch.nhl_watchlist import (
    classify_status,
    qualifies_new_watch,
    trigger_odds,
)


def test_trigger_odds_is_three_percent_ev_above_fair():
    assert abs(trigger_odds(2.00) - 2.06) < 1e-12


def test_new_watch_requires_agree_direction_and_price():
    now = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
    ko = now + timedelta(days=1)
    assert qualifies_new_watch(
        kickoff=ko, now=now, xg_gate="AGREE", xg_direction="AWAY",
        selection="AWAY", reference_odds=2.20, trigger=2.10,
    )
    assert not qualifies_new_watch(
        kickoff=ko, now=now, xg_gate="WEAK", xg_direction="AWAY",
        selection="AWAY", reference_odds=2.20, trigger=2.10,
    )
    assert not qualifies_new_watch(
        kickoff=ko, now=now, xg_gate="AGREE", xg_direction="HOME",
        selection="AWAY", reference_odds=2.20, trigger=2.10,
    )
    assert not qualifies_new_watch(
        kickoff=ko, now=now, xg_gate="AGREE", xg_direction="AWAY",
        selection="AWAY", reference_odds=2.05, trigger=2.10,
    )


def test_status_is_triggered_only_with_executable_price():
    now = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
    ko = now + timedelta(days=1)
    assert classify_status(
        kickoff=ko, now=now, xg_gate="AGREE", xg_direction="HOME",
        selection="HOME", executable_odds=None, trigger=1.93,
    ) == "WATCH"
    assert classify_status(
        kickoff=ko, now=now, xg_gate="AGREE", xg_direction="HOME",
        selection="HOME", executable_odds=1.95, trigger=1.93,
    ) == "TRIGGERED"
    assert classify_status(
        kickoff=ko, now=now, xg_gate="DISAGREE", xg_direction="HOME",
        selection="HOME", executable_odds=2.10, trigger=1.93,
    ) == "REJECTED"
    assert classify_status(
        kickoff=now, now=now, xg_gate="AGREE", xg_direction="HOME",
        selection="HOME", executable_odds=2.10, trigger=1.93,
    ) == "EXPIRED"
