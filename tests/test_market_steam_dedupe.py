from datetime import datetime, timedelta, timezone

from oddswatch import market_steam


def _sig(direction="SHORTENING", p=0.52):
    return {
        "key": "us:nfl:g1:home",
        "direction": direction,
        "probs": {"Polymarket": p, "ESPN/DK": 0.49},
    }


def test_us_steam_no_duplicate_after_time_only(tmp_path, monkeypatch):
    state = tmp_path / "alerts.json"
    monkeypatch.setattr(market_steam, "ALERT_STATE", state)

    t0 = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    first = market_steam._new_alerts([_sig()], t0)
    assert len(first) == 1

    # Same direction/probability two hours later must NOT resend.
    second = market_steam._new_alerts([_sig()], t0 + timedelta(hours=2))
    assert second == []


def test_us_steam_resends_only_on_extension_or_direction_change(tmp_path, monkeypatch):
    state = tmp_path / "alerts.json"
    monkeypatch.setattr(market_steam, "ALERT_STATE", state)

    t0 = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    assert len(market_steam._new_alerts([_sig(p=0.52)], t0)) == 1

    # < 1.5pp extension: no alert.
    assert market_steam._new_alerts(
        [_sig(p=0.534)], t0 + timedelta(minutes=15)
    ) == []

    # >= 1.5pp extension from last SENT level: alert.
    assert len(market_steam._new_alerts(
        [_sig(p=0.536)], t0 + timedelta(minutes=30)
    )) == 1

    # Direction flip: alert immediately.
    assert len(market_steam._new_alerts(
        [_sig(direction="DRIFTING", p=0.535)], t0 + timedelta(minutes=45)
    )) == 1
