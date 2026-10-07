from oddswatch.sources import footystats


def test_footystats_num_rejects_negative_sentinel():
    assert footystats._num(-1) is None
    assert footystats._num("1.42") == 1.42


def test_footystats_data_list_handles_wrapped_teams():
    payload = {"data": {"teams": [{"name": "A"}]}}
    assert footystats._data_list(payload) == [{"name": "A"}]


def test_footystats_league_score_prefers_country_and_exact_name():
    exact = footystats._league_score(
        {"country": "Germany", "league_name": "2. Bundesliga"},
        "Germany", ("2. Bundesliga",),
    )
    wrong_country = footystats._league_score(
        {"country": "Austria", "league_name": "2. Bundesliga"},
        "Germany", ("2. Bundesliga",),
    )
    assert exact > wrong_country


def test_footystats_mapping_covers_non_understat_core_leagues():
    for code in ("D2", "AUT", "N1", "P1", "B1", "T1", "SC0", "G1",
                 "SUI", "SWE", "NOR", "DEN", "POL"):
        assert code in footystats.LEAGUES
