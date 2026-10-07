from types import SimpleNamespace

from oddswatch.m17_6_research import augment_with_priors


def _row(season=2024, home="Home FC", away="Away FC"):
    return {
        "season": season,
        "home": home,
        "away": away,
        "x": [1.0, 2.0],
        "y": 0,
        "op": [2.0, 3.2, 3.8],
        "cl": [1.95, 3.1, 3.9],
    }


def _prior(team, hppg, hgf, hga, appg, agf, aga):
    return SimpleNamespace(
        team=team,
        home_ppg=hppg,
        home_gf_pg=hgf,
        home_ga_pg=hga,
        away_ppg=appg,
        away_gf_pg=agf,
        away_ga_pg=aga,
    )


def test_m17_6_adds_previous_season_team_priors():
    priors = {
        2024: [
            _prior("Home FC", 2.1, 1.9, 0.8, 1.2, 1.1, 1.4),
            _prior("Away FC", 1.8, 1.6, 1.0, 1.7, 1.5, 1.1),
        ]
    }
    out, cov = augment_with_priors([_row()], priors)
    x = out[0]["x"]
    assert x[:2] == [1.0, 2.0]
    assert abs(x[2] - 2.1) < 1e-12
    assert abs(x[3] - 1.7) < 1e-12
    assert x[-2:] == [0.0, 0.0]
    assert cov["both_prior"] == 1


def test_m17_6_marks_missing_promoted_team_without_inventing_strength():
    priors = {
        2024: [
            _prior("Home FC", 2.1, 1.9, 0.8, 1.2, 1.1, 1.4),
            _prior("Other FC", 1.4, 1.3, 1.2, 0.9, 0.9, 1.5),
        ]
    }
    out, cov = augment_with_priors([_row(away="Promoted FC")], priors)
    x = out[0]["x"]
    assert x[-2:] == [0.0, 1.0]
    assert cov["home_only"] == 1
