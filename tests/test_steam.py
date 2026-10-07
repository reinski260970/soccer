from datetime import datetime, timedelta, timezone

from oddswatch import steam


def _rec(probs):
    return {
        "key": "1|away",
        "event": "A – B",
        "kickoff": "2026-10-10T18:00:00+00:00",
        "league": "bundesliga",
        "market": "away",
        "selection": "B Sieg (90 Min.)",
        "probs": probs,
        "odds": {"Pinnacle": 4.0, "Bet365": 4.2, "Betfair": 4.1},
    }


def test_presteam_shortening(tmp_path):
    p = tmp_path / "steam.json"
    t0 = datetime(2026, 10, 7, 8, 0, tzinfo=timezone.utc)
    first = steam.update_many([_rec({
        "Pinnacle": 0.25, "Bet365": 0.245, "Betfair": 0.246,
    })], now=t0, path=p)
    assert first == []

    sig = steam.update_many([_rec({
        "Pinnacle": 0.272, "Bet365": 0.249, "Betfair": 0.250,
    })], now=t0 + timedelta(minutes=15), path=p)
    assert len(sig) == 1
    assert sig[0]["direction"] == "SHORTENING"
    assert sig[0]["score"] >= 3


def test_presteam_drifting(tmp_path):
    p = tmp_path / "steam.json"
    t0 = datetime(2026, 10, 7, 8, 0, tzinfo=timezone.utc)
    steam.update_many([_rec({
        "Pinnacle": 0.30, "Bet365": 0.296, "Betfair": 0.295,
    })], now=t0, path=p)

    sig = steam.update_many([_rec({
        "Pinnacle": 0.278, "Bet365": 0.292, "Betfair": 0.291,
    })], now=t0 + timedelta(minutes=15), path=p)
    assert len(sig) == 1
    assert sig[0]["direction"] == "DRIFTING"
