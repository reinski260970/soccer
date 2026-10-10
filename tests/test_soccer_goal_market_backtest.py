import pytest

from scripts.mongo_goal_markets_backtest import (
    _early_calibration,
    _losses,
    _market_prices,
    _odds_pair,
    _outcomes,
    _pre_match_rates,
    _total_market_test,
)


def _row(year, d, goals):
    return {
        "season":year,
        "date":d,
        "home":"A",
        "away":"B",
        "lambda_home_fast":1.8,
        "lambda_away_fast":1.1,
        "lambda_home_slow":1.5,
        "lambda_away_slow":1.2,
    }


def test_goal_rates_never_read_market_odds():
    row = _row(2024, "2024-08-01", (1,2))
    base = _pre_match_rates(row, scale=1.0, fast_weight=0.35)
    row["op"] = [1.2, 8.0, 9.0]
    row["cl"] = [9.0, 1.2, 9.0]
    assert _pre_match_rates(row, scale=1.0, fast_weight=0.35) == base


def test_goal_outcomes_include_regulation_draw_btts_and_ou():
    assert _outcomes((2,1)) == (0, 1, 1)
    assert _outcomes((0,0)) == (1, 0, 0)
    assert _outcomes((0,2)) == (2, 0, 0)


def test_pinnacle_total_prices_require_two_complete_sides():
    d = {"P>2.5":1.95, "P<2.5":1.97,
         "PC>2.5":1.85, "PC<2.5":2.04}
    opening, closing = _odds_pair(d, "pinnacle")
    assert opening == (1.95, 1.97)
    assert closing == (1.85, 2.04)
    d.pop("PC<2.5")
    assert _odds_pair(d, "pinnacle")[1] is None
    d.pop("P<2.5")
    assert _odds_pair(d, "pinnacle") == (None, None)


def test_research_total_price_only_uses_paired_historical_opening():
    row = _row(2024, "2024-08-01", (2,1))
    cfg = {"scale":1.0, "fast_weight":0.35, "draw_factor":1.0}
    score_map = {("2024-08-01","A","B"):(2,1)}
    odds = {(2024,"A","B"):{"source":"pinnacle",
                              "opening":(1.8,2.1),
                              "closing":(1.9,2.0)}}
    result = _total_market_test([row],cfg,score_map,odds)
    assert result["paired_opening_games"] == 1
    assert result["paired_closing_games"] == 1
    assert result["market_sources"] == {"pinnacle":1}
    assert result["model_logloss"] is not None
    assert result["opening_market_no_vig_logloss"] is not None


def test_early_hyper_requires_genuine_2020_2021_rows():
    assert _early_calibration([], {}) is None
    rows = [_row(2024, "2024-08-01", (1,2))]
    assert _early_calibration(rows, {}) is None


def test_goals_pair_is_converted_to_three_market_outcomes_before_scoring():
    row = _row(2024, "2024-08-01", (2, 1))
    cfg = {"scale":1.0, "fast_weight":0.35, "draw_factor":1.0}
    results = {("2024-08-01","A","B"):(2,1)}
    diag = _losses([row], results, cfg)
    assert diag["n"] == 1
    assert set(diag["logloss"]) == {"1X2","OU2.5","BTTS"}
    assert all(v > 0 for v in diag["logloss"].values())
