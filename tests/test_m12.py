from datetime import date

from oddswatch.m12_research import _season_start, _shot_xg


def test_season_start():
    assert _season_start(date(2025, 8, 1)) == 2025
    assert _season_start(date(2026, 5, 1)) == 2025


def test_shot_xg_proxy():
    hx, ax = _shot_xg({"HS": 12, "HST": 5, "AS": 8, "AST": 3})
    assert round(hx, 2) == 1.71
    assert round(ax, 2) == 1.05


def test_shot_xg_missing_is_none():
    assert _shot_xg({"HS": 12}) == (None, None)
