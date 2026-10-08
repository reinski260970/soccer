from datetime import datetime, timezone

from oddswatch.quick import _supported_fixture
from oddswatch.sources.apifootball import ApiFixture


def _fx(league, country):
    return ApiFixture(
        id=1,
        kickoff=datetime(2026, 10, 9, 18, 0, tzinfo=timezone.utc),
        home="A",
        away="B",
        league=league,
        country=country,
    )


def test_supported_steam_leagues_include_model_scope():
    assert _supported_fixture(_fx("Bundesliga", "Germany"))
    assert _supported_fixture(_fx("2. Bundesliga", "Germany"))
    assert _supported_fixture(_fx("Championship", "England"))
    assert _supported_fixture(_fx("Bundesliga", "Austria"))
    assert _supported_fixture(_fx("Allsvenskan", "Sweden"))


def test_supported_steam_leagues_exclude_noise():
    assert not _supported_fixture(_fx("Tercera División RFEF - Group 15", "Spain"))
    assert not _supported_fixture(_fx("Nasjonal U19 Champions League", "Norway"))
    assert not _supported_fixture(_fx("Premier League U21", "England"))
