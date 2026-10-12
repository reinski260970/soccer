from datetime import datetime, timezone

from oddswatch.nhl_v5_1_forward import (
    XG_AGREEMENT_THRESHOLD,
    build_event_signals,
    build_snapshots,
    classify_xg_agreement,
    parse_team_games,
)


def test_classifier_matches_frozen_v5_diagnostic_rule():
    assert classify_xg_agreement(.02, .03) == "AGREE"
    assert classify_xg_agreement(-.02, -.03) == "AGREE"
    assert classify_xg_agreement(.02, -.03) == "DISAGREE"
    assert classify_xg_agreement(-.02, .03) == "DISAGREE"
    assert classify_xg_agreement(XG_AGREEMENT_THRESHOLD - 1e-6, .03) == "WEAK"
    assert classify_xg_agreement(.03, -XG_AGREEMENT_THRESHOLD + 1e-6) == "WEAK"


def _bulk_csv():
    return """season,gameDate,gameId,situation,position,playerTeam,opposingTeam,xGoalsFor,xGoalsAgainst
2025,20261010,1,5on5,Team Level,N.J,OTT,2.8,1.8
2025,20261010,1,5on5,Team Level,OTT,N.J,1.8,2.8
2025,20261011,2,5on5,Team Level,N.J,OTT,3.1,1.7
2025,20261011,2,5on5,Team Level,OTT,N.J,1.7,3.1
2025,20261012,3,5on5,Team Level,N.J,OTT,0.1,5.0
2025,20261012,3,5on5,Team Level,OTT,N.J,5.0,0.1
"""


def test_forward_signal_excludes_same_day_money_puck_rows():
    games = parse_team_games(_bulk_csv())
    events = [{
        "event_id": "nhl:test:1",
        "home_team_id": "nhl:home",
        "away_team_id": "nhl:away",
        "home_name": "New Jersey Devils",
        "away_name": "Ottawa Senators",
        "kickoff": datetime(2026, 10, 12, 23, 0, tzinfo=timezone.utc),
    }]
    signals, issues = build_event_signals(events, games)
    assert not issues
    assert len(signals) == 1
    s = signals[0]
    # The extreme 2026-10-12 rows must not enter a 2026-10-12 prematch signal.
    assert s["slow_mp_xg_share_diff"] > 0
    assert s["fast_mp_xg_share_diff"] > 0
    assert s["xg_agreement"] == "AGREE"
    assert s["data_through"].date().isoformat() == "2026-10-11"


def test_snapshots_are_shadow_only_and_never_create_play():
    games = parse_team_games(_bulk_csv())
    events = [{
        "event_id": "nhl:test:1",
        "home_team_id": "nhl:home",
        "away_team_id": "nhl:away",
        "home_name": "New Jersey Devils",
        "away_name": "Ottawa Senators",
        "kickoff": datetime(2026, 10, 12, 23, 0, tzinfo=timezone.utc),
    }]
    signals, _ = build_event_signals(events, games)
    observed = datetime(2026, 10, 12, 16, 0, tzinfo=timezone.utc)
    rows = build_snapshots(signals, observed)
    assert len(rows) == 2
    assert {r["metrics"]["side"] for r in rows} == {"HOME", "AWAY"}
    assert all(r["metrics"]["release_status"] == "SHADOW" for r in rows)
    assert all(r["metrics"]["price_used_as_feature"] is False for r in rows)
    assert all(r["metrics"]["result_used_as_feature"] is False for r in rows)
