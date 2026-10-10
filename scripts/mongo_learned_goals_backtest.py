"""Leakage-safe expanding-season goal model challenger for 13 Soccer Mongo leagues.

History/target: scored fixtures in canonical Mongo data. Features: rolling
pre-match goals, xG proxy, shots, SoT, rest, venue, structure and last-season
priors. Hyperparameters chosen by 2020/21 joint 1X2/O2.5/BTTS logloss.
2022/23 temporal diagnostics, 2024 retrospective inspected stress only.
Quote comparison: same fixture Pinnacle 1X2 and archived O/U2.5 opening/close.
Zero odds are ever used as model features. Research only, never PLAY.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from oddswatch import m17_17_research as historic, pricing
from oddswatch.m14_research import load_league, train_proxy
from oddswatch.m17_1_research import load_real_shots
from oddswatch.models.learned_goals import (
    goal_nll, predict_intensities, scored_rows,
)
from scripts.mongo_goal_markets_backtest import (
    _losses,
    _market_prices,
    _one_x2_market_test,
    _total_market_test,
    _matrix,
    _outcomes,
)
from scripts.mongo_m17_17_backtest import LEAGUE_GROUPS

ALPHA_GRID = (0.03, 0.30, 2.0)
DRAW_FACTORS = (0.85, 1.00, 1.15)
FROZEN_MARKET_CONFIG = {"scale":1.0, "fast_weight":0.5}
TRAIN_CUTOFF = 2019


def attach_targets(rows, odds_rows):
    score_map = {
        (d,h,a):(hg,ag)
        for _,d,h,a,hg,ag,_,_ in odds_rows
    }
    labeled = []
    for r in rows:
        t = score_map.get((r["date"],r["home"],r["away"]))
        if t is None:
            continue
        labeled.append(dict(r, home_goals=t[0], away_goals=t[1]))
    return labeled, score_map


def _oos(train, test, alpha):
    """Requires chronological cut between all training and test seasons."""
    if len(train)<400 or len(test)<60:
        return []
    earliest = min(r["season"] for r in test)
    if max(r["season"] for r in train) >= earliest:
        raise RuntimeError("model fit consumed validation target season")
    predictions = predict_intensities(train,test,alpha=alpha)
    return scored_rows(test,predictions)


def _early_choose(data, score_map):
    candidates = []
    for year in (2020,2021):
        train = [r for r in data if r["season"]<year]
        test = [r for r in data if r["season"]==year]
        if len(train)<400 or len(test)<60:
            return None
        candidates.append((year,train,test))
    best = None
    for alpha in ALPHA_GRID:
        pred = [(year,_oos(train,test,alpha)) for year,train,test in candidates]
        for draw_factor in DRAW_FACTORS:
            cfg = dict(FROZEN_MARKET_CONFIG,draw_factor=draw_factor)
            diagnostic = {
                str(year):_losses(rows,score_map,cfg)
                for year,rows in pred
            }
            if any(d is None for d in diagnostic.values()):
                continue
            # Outcome probability metric. Equal fold weight prevents different
            # season match counts from choosing hyperparams by accident.
            score = sum(d["average_three_market_logloss"]
                        for d in diagnostic.values())/len(diagnostic)
            if best is None or score<best["early_joint_logloss"]:
                best = {"alpha":alpha,"draw_factor":draw_factor,
                        "early_joint_logloss":score,
                        "early_folds":diagnostic}
    return best


def historical_1x2_entry_test(rows, score_map, cfg):
    """Fixed 3%-model-EV historical opening entry, never train on prices.

    Three-way CLV is entry price multiplied by no-vig closing probability - 1.
    Missing opening/closing quotes exclude the fixture, no made-up quotes.
    """
    games = bets = positive = 0
    roi = clv = 0.0
    by_side = {"home":0, "draw":0, "away":0}
    for row in rows:
        score = score_map.get((row["date"],row["home"],row["away"]))
        opening,closing = row.get("op"),row.get("cl")
        if score is None or not opening or not closing:
            continue
        if len(opening)!=3 or len(closing)!=3:
            continue
        if any(
            not isinstance(x,(float,int)) or not 1.01 < x < 75
            for x in list(opening)+list(closing)
        ):
            continue
        try:
            p_close = pricing.devig(list(closing))
        except (TypeError,ValueError,ZeroDivisionError):
            continue
        if any(p<=0 for p in p_close):
            continue
        _, prices = _matrix(row,cfg)
        probs = (prices["1"],prices["X"],prices["2"])
        result = _outcomes(score)[0]
        games += 1
        for k, side in enumerate(("home","draw","away")):
            ev = probs[k]*opening[k]-1.0
            if ev < 0.03 or opening[k] > 3.0:
                continue
            bets += 1
            by_side[side] += 1
            shift = opening[k]*p_close[k]-1.0
            clv += shift
            positive += int(shift>0)
            roi += opening[k]-1 if k==result else -1
    return {
        "paired_open_close_games":games,
        "retrospective_bets":bets,
        "market_sides":by_side,
        "clv":clv/bets if bets else None,
        "positive_clv_rate":positive/bets if bets else None,
        "roi":roi/bets if bets else None,
        "entry_rule":"fixed +3% model EV, Pinnacle opening <= 3.0",
        "release_eligible":False,
        "note":"Retrospective 2024 research, not executable forward value",
    }


def evaluate_league(code,proxy):
    matches,odds_rows,coverage=load_league(code,proxy,2017,2025)
    shot_map=load_real_shots(code,2017,2025)
    base,venue_cov,xg_cov=historic._build_data(matches,odds_rows,shot_map)
    data,score_map=attach_targets(base,odds_rows)
    result={
        "samples":len(data),
        "feature_source":"Mongo historical strictly pre-day rolling goals, shots, SoT, xG proxy, form, venue, Y-1 priors",
        "odds_not_used_in_features":True,
        "history":coverage,
        "prior_coverage":venue_cov,
        "xg_prior_coverage":xg_cov,
        "release_eligible":False,
        "release_reason":"2024 previously inspected; never a fresh holdout",
    }
    best=_early_choose(data,score_map)
    if best is None:
        return dict(result,error="insufficient early 2020/2021 OOS data")
    result["early_selected"]=best
    cfg=dict(FROZEN_MARKET_CONFIG,draw_factor=best["draw_factor"])
    latest=[]
    for year in (2022,2023,2024,2025):
        training=[r for r in data if r["season"]<year]
        test=[r for r in data if r["season"]==year]
        forecast=_oos(training,test,best["alpha"])
        if not forecast:
            result[str(year)]={"n":0,"error":"insufficient historical training or test games"}
            continue
        s=_losses(forecast,score_map,cfg)
        result[str(year)]={
            "n":len(forecast),
            "scoring":s,
            "intensity":goal_nll(forecast),
        }
        if year==2024:
            latest=forecast
    if not latest:
        return dict(result,error="2024 retrospective OOS missing")
    market_1x2=_one_x2_market_test(latest,cfg,score_map)
    odds,odds_cov=_market_prices(code,start_year=2024,end_year=2024)
    market_total=_total_market_test(latest,cfg,score_map,odds)
    result["market_2024_1x2"]=market_1x2
    result["retrospective_1x2_clv"]=historical_1x2_entry_test(
        latest,score_map,cfg)
    result["market_2024_total25"]=market_total
    result["market_2024_total_coverage"]=odds_cov
    result["market_2024_btts"]="NO_HISTORICAL_PAIRED_QUOTES"
    result["market_2024_asian_handicap"]="NO_HISTORICAL_PAIRED_QUOTES"
    # Claims only made for actually paired observations.
    result["beats_1x2_opening"]=(
        market_1x2["gain_vs_market"] is not None
        and market_1x2["gain_vs_market"]>0
    )
    result["beats_ou25_opening"]=(
        market_total["gain_vs_market"] is not None
        and market_total["gain_vs_market"]>0
    )
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--group",required=True,choices=tuple(LEAGUE_GROUPS))
    args=parser.parse_args()
    uri=(os.getenv("MONGO_SOCCER") or os.getenv("MONGODB_URI") or "").strip()
    if not uri:
        raise RuntimeError("Missing Mongo secret - zero backtest cannot pass")
    os.environ["MONGO_SOCCER"]=uri
    proxy=train_proxy(years=range(2017,2020))
    if max(proxy["train_seasons"])>=2020:
        raise RuntimeError("xG proxy training leaked into 2020 validation")
    output={
        "approach":"Independent PoissonRegressor goal rate challenger / locked early 2020-21 hyperparam grid",
        "xg_proxy_train_seasons":proxy["train_seasons"],
        "hyper_selection":"2020 and 2021 joint 1X2 O/U BTTS result logloss",
        "2024_status":"retrospective stress, inspected repeatedly, not a release holdout",
        "data_policy":"model features are only pre-match Mongo; bookmaker opening/closing exclusively for comparisons",
        "release_eligible":False,
        "leagues":{},
    }
    valid=0
    for league,code in LEAGUE_GROUPS[args.group].items():
        try:
            outcome=evaluate_league(code,proxy)
        except Exception as ex:
            outcome={"error":f"{type(ex).__name__}: {ex}","release_eligible":False}
        output["leagues"][league]=outcome
        x2=outcome.get("market_2024_1x2") or {}
        ou=outcome.get("market_2024_total25") or {}
        diag=outcome.get("2024") or {}
        if x2.get("paired_2024_games",0)>0 and ou.get("paired_opening_games",0)>0:
            valid+=1
        print("LEARNED_GOALS",league,json.dumps({
            "n":diag.get("n"),"goal_nll":(diag.get("intensity") or {}).get("goal_nll"),
            "BTTS_ll":((diag.get("scoring") or {}).get("logloss") or {}).get("BTTS"),
            "selected":(outcome.get("early_selected") or {}).get("alpha"),
            "1x2":x2,
            "1x2_entries":outcome.get("retrospective_1x2_clv"),
            "O2.5":ou,"error":outcome.get("error"),
        },ensure_ascii=False),flush=True)
    path=Path(f"reports/mongo_learned_goals_{args.group}.json")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8")
    if valid==0:
        raise RuntimeError("NO_VALID_PAIRING cannot mark goal-model test successful")


if __name__=="__main__":
    main()
