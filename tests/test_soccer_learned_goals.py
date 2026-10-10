"""Temporal tests for learned soccer goal intensities and their market conversion."""
import pytest

from oddswatch.models.learned_goals import (
    PREMATCH_FEATURE_INDEXES,
    goal_nll,
    prematch_vector,
    predict_intensities,
    scored_rows,
)
from scripts.mongo_learned_goals_backtest import (
    _early_choose,
    _oos,
    attach_targets,
)


def _example(i, season=2018, with_quote=True):
    # Variations across years and teams, all model values pre-match.
    x=[0.2 + (i%11)*0.03 + j*0.005 for j in range(70)]
    x[0]=1.0
    return {
        "season":season, "date":f"{season}-{(i%12)+1:02}-01",
        "home":f"H{i}", "away":f"A{i}",
        "x":x, "home_goals":(i*3)%4,"away_goals":(i*7)%3,
        "op":[1.90,3.2,4.4] if with_quote else None,
        "cl":[2.0,3.1,4.0] if with_quote else None,
    }


def test_feature_vector_ignores_all_bookmaker_prices_and_labels():
    original=_example(12)
    same=dict(original,op=[15,1.15,8],cl=[1.3,9,9],
              home_goals=12,away_goals=0)
    assert prematch_vector(original)==prematch_vector(same)
    assert len(prematch_vector(original))==len(PREMATCH_FEATURE_INDEXES)


def test_feature_vector_fails_closed_on_invalid_rows():
    short=_example(12)
    short["x"]=[1.,2.]
    with pytest.raises(ValueError):
        prematch_vector(short)


def test_training_cannot_use_same_or_later_validation_season():
    training=[_example(i,2018) for i in range(400)]
    validate=[_example(500+i,2018) for i in range(60)]
    with pytest.raises(RuntimeError,match="consumed validation"):
        _oos(training,validate,alpha=0.1)


def test_2024_2025_not_used_in_early_calibration():
    data=[_example(i,2017) for i in range(400)]
    data += [_example(i,2024) for i in range(100)]
    assert _early_choose(data,{}) is None


def test_model_intensities_positive_and_do_not_depend_on_market_quotes():
    training=[_example(i,2018) for i in range(110)]
    test=[_example(i+200,2020) for i in range(4)]
    p=predict_intensities(training,test,alpha=0.3)
    test2=[dict(r,op=[1.01,3,90],cl=[90,1.01,3]) for r in test]
    repeated=predict_intensities(training,test2,alpha=0.3)
    assert [v for pair in p for v in pair] == pytest.approx(
        [v for pair in repeated for v in pair]
    )
    assert len(p)==4
    assert all(0<a<=5.8 and 0<b<=5.8 for a,b in p)
    row=scored_rows(test,p)
    assert row[0]["learned_home_goal_rate"]==pytest.approx(p[0][0])
    assert goal_nll(row)["goal_nll"]>0


def test_historical_result_join_does_not_use_quoted_price_as_label():
    a=_example(1,2019)
    a["date"]="2019-08-13";a["home"]="A";a["away"]="B"
    odds=[(2019,"2019-08-13","A","B",2,1,[1.9,3.3,4.5],[1.8,3.4,4.7])]
    labeled,score_map=attach_targets([a],odds)
    assert score_map[("2019-08-13","A","B")]==(2,1)
    assert labeled[0]["home_goals"]==2
    assert labeled[0]["away_goals"]==1
