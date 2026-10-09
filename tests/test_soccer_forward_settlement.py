"""Soccer regulation settlement and market grading coverage."""
from oddswatch.sql.soccer_settlement import parse_final
from oddswatch.sql.evaluation import outcome


def test_parse_final_uses_90_minute_score_not_extra_time():
    event = {"home_name": "Rapid Vienna", "away_name": "Austria Vienna"}
    data = {"response": [{
        "fixture": {"id": 123, "status": {"short": "AET"}},
        "teams": {"home": {"name": "Rapid Wien"}, "away": {"name": "Austria Wien"}},
        "score": {
            "fulltime": {"home": 1, "away": 1},
            "extratime": {"home": 2, "away": 1},
        },
    }]}
    result = parse_final(data, event)
    assert result[:2] == (1, 1)
    assert result[2]["score_scope"] == "REGULATION_90_MIN"


def p(market, selection, line=0, rules="REGULATION"):
    return {"period": "REGULATION", "settlement_rules": rules,
            "market": market, "selection": selection, "line": line}


def test_soccer_regulation_markets():
    assert outcome(p("moneyline", "HOME"), 2, 1, league="aut_bundesliga") == "WIN"
    assert outcome(p("moneyline", "DRAW"), 1, 1, league="aut_bundesliga") == "WIN"
    assert outcome(p("total", "OVER", 2.5), 2, 1, league="aut_bundesliga") == "WIN"
    assert outcome(p("btts", "YES"), 2, 1, league="aut_bundesliga") == "WIN"
    assert outcome(p("dnb", "HOME"), 1, 1, league="aut_bundesliga") == "PUSH"
    assert outcome(p("double_chance", "HOME_OR_DRAW"), 1, 1, league="aut_bundesliga") == "WIN"
    assert outcome(p("spread", "AWAY", 1.5), 2, 1, league="aut_bundesliga") == "WIN"
    assert outcome(p("team_total", "OVER", 1.5, "REGULATION:TEAM_TOTAL_HOME"),
                   2, 0, league="aut_bundesliga") == "WIN"


def test_quarter_lines_and_hockey_regulation_fail_closed():
    assert outcome(p("total", "OVER", 2.25), 2, 1, league="aut_bundesliga") is None
    assert outcome(p("moneyline", "HOME"), 3, 2, league="nhl") is None
