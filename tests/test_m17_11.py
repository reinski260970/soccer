from oddswatch.m17_11_research import (
    StrengthState,
    _expected_xg,
    _update_strengths,
    _structural_features,
)


def test_m17_11_expected_xg_respects_attack_and_defense():
    home = StrengthState(attack_fast=0.30, defense_fast=0.10,
                         attack_slow=0.20, defense_slow=0.08)
    away = StrengthState(attack_fast=0.05, defense_fast=0.25,
                         attack_slow=0.04, defense_slow=0.20)
    strong = _expected_xg(1.45, 1.20, home, away)

    neutral = _expected_xg(
        1.45, 1.20, StrengthState(), StrengthState()
    )

    # Away's stronger defense suppresses the home attack relative to the same
    # home attack facing a neutral defense, but home attack still lifts above
    # the pure league baseline.
    assert strong["home_fast"] > 1.45
    assert strong["home_fast"] < 1.45 * __import__("math").exp(0.30)
    assert neutral["home_fast"] == 1.45


def test_m17_11_positive_home_xg_residual_strengthens_attack_and_weakens_away_defense():
    home = StrengthState()
    away = StrengthState()
    _update_strengths(
        home,
        away,
        observed_home_xg=2.40,
        observed_away_xg=1.20,
        league_home_xg=1.45,
        league_away_xg=1.20,
    )
    assert home.attack_fast > 0
    assert home.attack_slow > 0
    assert away.defense_fast < 0
    assert away.defense_slow < 0


def test_m17_11_structural_features_are_pre_match_state_only():
    home = StrengthState(n=10, attack_fast=0.20, defense_fast=0.05,
                         attack_slow=0.10, defense_slow=0.02)
    away = StrengthState(n=8, attack_fast=-0.05, defense_fast=0.10,
                         attack_slow=-0.02, defense_slow=0.06)
    before = _structural_features(1.45, 1.20, home, away)

    _update_strengths(
        home,
        away,
        observed_home_xg=3.0,
        observed_away_xg=0.4,
        league_home_xg=1.45,
        league_away_xg=1.20,
    )
    after = _structural_features(1.45, 1.20, home, away)

    assert before != after
    assert len(before) == 17
    assert len(after) == 17
