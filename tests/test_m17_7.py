from datetime import date
from types import SimpleNamespace

from oddswatch.m17_7_research import (
    build_previous_season_xg_priors,
    augment_with_xg_priors,
)


def _m(d, h, a, hg, ag, hx, ax):
    return SimpleNamespace(
        date=d, home=h, away=a,
        home_goals=hg, away_goals=ag,
        home_xg=hx, away_xg=ax,
    )


def test_m17_7_previous_season_xg_prior_is_y_minus_1_only():
    ms = [
        _m(date(2023,8,1),"A","B",2,1,1.4,0.8),
        _m(date(2023,8,8),"B","A",0,1,0.9,1.2),
        _m(date(2024,8,1),"A","B",3,0,2.1,0.5),
    ]
    priors = build_previous_season_xg_priors(ms)
    # target season 2024 must use only 2023/24 rows.
    a = next(x for x in priors[2024] if x.team == "A")
    assert abs(a.home_xgf_pg - 1.4) < 1e-12
    assert abs(a.away_xgf_pg - 1.2) < 1e-12


def test_m17_7_adds_xg_and_luck_features():
    prior = SimpleNamespace(
        team="A",
        home_gp=10, home_xgf_pg=1.5, home_xga_pg=0.9,
        home_gf_pg=1.8, home_ga_pg=0.7,
        away_gp=10, away_xgf_pg=1.2, away_xga_pg=1.1,
        away_gf_pg=1.3, away_ga_pg=1.0,
    )
    prior_b = SimpleNamespace(
        team="B",
        home_gp=10, home_xgf_pg=1.4, home_xga_pg=1.0,
        home_gf_pg=1.5, home_ga_pg=1.0,
        away_gp=10, away_xgf_pg=1.1, away_xga_pg=1.4,
        away_gf_pg=0.9, away_ga_pg=1.6,
    )
    row = {
        "season": 2024, "home": "A", "away": "B", "x": [1.0],
        "y": 0, "op": [2,3,4], "cl": [2,3,4],
    }
    out, cov = augment_with_xg_priors([row], {2024:[prior, prior_b]})
    x = out[0]["x"]
    assert x[0] == 1.0
    assert abs(x[1] - 1.5) < 1e-12
    assert abs(x[4] - 1.4) < 1e-12
    assert abs(x[7] - (1.8 - 1.5)) < 1e-12
    assert cov["both_prior"] == 1
