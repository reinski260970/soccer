from oddswatch.sources import soccerstats


def test_soccerstats_historical_url_uses_season_end_year():
    assert soccerstats.url("D1", 2024).endswith("league=germany_2025")
    assert soccerstats.url("D2", 2024).endswith("league=germany2_2025")


def test_soccerstats_parse_summary():
    html = """
    <html><body>
    306 matches played / 306
    Home wins: 45% Draws: 28% Away wins: 27%
    Goals per match: 2.72
    Over 1.5 goals: 76% Over 2.5 goals: 53% Over 3.5 goals: 29%
    Both teams scored: 55%
    </body></html>
    """
    c = soccerstats.parse_summary(html)
    assert c.matches_played == 306
    assert abs(c.goals_per_match - 2.72) < 1e-12
    assert abs(c.home_win_pct - 0.45) < 1e-12
    assert abs(c.over25_pct - 0.53) < 1e-12
    assert abs(c.btts_pct - 0.55) < 1e-12


def test_soccerstats_core_mapping():
    for code in ("D1","D2","E0","E1","SP1","I1","F1","N1","P1","B1",
                 "T1","SC0","G1","AUT","SUI","SWE","NOR","DEN","POL"):
        assert soccerstats.url(code) is not None
