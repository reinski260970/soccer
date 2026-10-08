from oddswatch.sources import espn


def test_parse_scoreboard_captures_period_linescores():
    data = {
        "events": [{
            "id": "g1",
            "date": "2026-10-01T18:00:00Z",
            "season": {"type": 2},
            "status": {"type": {"name": "STATUS_FINAL"}},
            "competitions": [{
                "neutralSite": False,
                "competitors": [
                    {
                        "homeAway": "home",
                        "score": "104",
                        "team": {"displayName": "Home", "id": "1"},
                        "linescores": [
                            {"value": 25}, {"value": 28},
                            {"value": 24}, {"value": 27},
                        ],
                    },
                    {
                        "homeAway": "away",
                        "score": "99",
                        "team": {"displayName": "Away", "id": "2"},
                        "linescores": [
                            {"value": 21}, {"value": 26},
                            {"value": 22}, {"value": 30},
                        ],
                    },
                ],
                "odds": [],
            }],
        }],
    }
    rows = espn.parse_scoreboard(data, "nba")
    assert len(rows) == 1
    g = rows[0]
    assert g.home_periods == (25.0, 28.0, 24.0, 27.0)
    assert g.away_periods == (21.0, 26.0, 22.0, 30.0)
    assert g.final
