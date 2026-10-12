import io
import math
import zipfile

from oddswatch.nhl_first_period_xg import (
    build_states,
    fair_decimal,
    parse_period1_games,
    poisson_1p_1x2,
    project_event,
    total_prob_over,
)


def _zip(rows: str) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("shots_2026.csv", rows)
    return out.getvalue()


def test_parse_period1_only_and_home_away_xg():
    blob = _zip(
        "game_id,season,isPlayoffGame,period,homeTeamCode,awayTeamCode,teamCode,xGoal\n"
        "2026020001,2026,0,1,NJD,OTT,NJD,0.20\n"
        "2026020001,2026,0,1,NJD,OTT,NJD,0.30\n"
        "2026020001,2026,0,1,NJD,OTT,OTT,0.40\n"
        "2026020001,2026,0,2,NJD,OTT,NJD,0.90\n"
        "2026020002,2026,1,1,NJD,OTT,NJD,0.80\n"
    )
    rows = parse_period1_games(blob, 2026)
    assert len(rows) == 1
    assert rows[0]["home"] == "N.J"
    assert rows[0]["away"] == "OTT"
    assert abs(rows[0]["home_xg1"] - 0.50) < 1e-9
    assert abs(rows[0]["away_xg1"] - 0.40) < 1e-9


def test_poisson_first_period_probabilities_and_decimal_fair():
    p = poisson_1p_1x2(0.9, 0.7)
    assert abs(sum(p.values()) - 1.0) < 1e-9
    assert p["HOME"] > p["AWAY"]
    assert fair_decimal(p["HOME"]) > 1.0
    po = total_prob_over(1.6, 1.5)
    assert 0 < po < 1
    expected = 1 - math.exp(-1.6) * (1 + 1.6)
    assert abs(po - expected) < 1e-12


def test_venue_specific_matchup_changes_first_period_projection():
    games = {
        2025: [
            {"game_id":"1","season":2025,"home":"N.J","away":"OTT","home_xg1":1.4,"away_xg1":0.4,"shots":4},
            {"game_id":"2","season":2025,"home":"N.J","away":"OTT","home_xg1":1.2,"away_xg1":0.5,"shots":4},
            {"game_id":"3","season":2025,"home":"OTT","away":"N.J","home_xg1":0.5,"away_xg1":1.3,"shots":4},
            {"game_id":"4","season":2025,"home":"OTT","away":"N.J","home_xg1":0.4,"away_xg1":1.1,"shots":4},
        ],
        2026: [
            {"game_id":"5","season":2026,"home":"N.J","away":"OTT","home_xg1":1.5,"away_xg1":0.3,"shots":4},
        ],
    }
    slow = build_states(games, 0.20)
    fast = build_states(games, 0.40)
    pr = project_event("N.J", "OTT", slow, fast)
    assert pr["home_home_slow_xgf1"] > pr["away_away_slow_xgf1"]
    assert pr["lambda_home_1p"] > pr["lambda_away_1p"]
    assert pr["fair_1p_home"] < pr["fair_1p_away"]
    assert set(pr["totals"]) == {"0.5","1.5","2.5"}
