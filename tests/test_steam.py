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


def test_presteam_generic_lead_source(tmp_path):
    p = tmp_path / "steam.json"
    t0 = datetime(2026, 10, 7, 8, 0, tzinfo=timezone.utc)
    base = {
        "key": "us:nhl:1:away",
        "event": "A – B",
        "kickoff": "2026-10-08T01:30:00+00:00",
        "league": "nhl",
        "market": "away",
        "selection": "B ML",
        "lead_source": "Polymarket",
        "slow_sources": ["ESPN/DK"],
        "odds": {"Polymarket": 2.0, "ESPN/DK": 2.1},
    }
    r1 = dict(base)
    r1["probs"] = {"Polymarket": 0.50, "ESPN/DK": 0.48}
    assert steam.update_many([r1], now=t0, path=p) == []

    r2 = dict(base)
    r2["probs"] = {"Polymarket": 0.525, "ESPN/DK": 0.484}
    sig = steam.update_many([r2], now=t0 + timedelta(minutes=15), path=p)
    assert len(sig) == 1
    assert sig[0]["direction"] == "SHORTENING"
    assert sig[0]["lead_source"] == "Polymarket"


def test_steam_global_gc_removes_stale_keys_and_caps_snapshots(tmp_path):
    p = tmp_path / "steam.json"
    t0 = datetime(2026, 10, 7, 0, 0, tzinfo=timezone.utc)

    # Stale key from another event should disappear even if not scanned now.
    p.write_text(
        '{"stale":[{"ts":"2026-10-06T00:00:00+00:00","probs":{"Pinnacle":0.5}}]}',
        encoding="utf-8",
    )

    for i in range(45):
        steam.update_many([_rec({
            "Pinnacle": 0.25 + i * 0.0001,
            "Bet365": 0.245 + i * 0.00005,
            "Betfair": 0.246 + i * 0.00005,
        })], now=t0 + timedelta(minutes=i), path=p)

    import json
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "stale" not in data
    assert len(data["1|away"]) == steam.MAX_SNAPSHOTS_PER_KEY
