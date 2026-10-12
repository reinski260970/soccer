"""NHL bulk model v2: rolling independent features + nested model selection.

No bookmaker odds are model features. Opening odds are used only after a
probability is frozen, for the unchanged EV>=3% entry simulation. Closing odds
are used only for evaluation.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .nhl_bulk_backtest import (
    SOURCE, MIN_EV, _devig_home, _ll, load_rows,
)
from .nhl_bulk_features import build_features

OUT = Path("data/hockey/nhl_bulk_v2_backtest.json")
FEATURES = [
    "elo_diff",
    "gf_diff",
    "ga_diff",
    "win_diff",
    "venue_attack_diff",
    "venue_defence_diff",
    "rest_diff",
    "home_rest",
    "away_rest",
]
SHRINKS = (0.50, 0.65, 0.80, 0.90, 1.00)
MIN_CAL = 400
MIN_TEST = 400


def _matrix(rows):
    x=np.asarray([[float(r[k]) for k in FEATURES] for r in rows],dtype=float)
    y=np.asarray([int(r["target"]) for r in rows],dtype=int)
    return x,y


def _models():
    return {
        "logit_c0.1": make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.1,max_iter=1000,solver="lbfgs"),
        ),
        "logit_c0.5": make_pipeline(
            StandardScaler(),
            LogisticRegression(C=0.5,max_iter=1000,solver="lbfgs"),
        ),
        "logit_c2": make_pipeline(
            StandardScaler(),
            LogisticRegression(C=2.0,max_iter=1000,solver="lbfgs"),
        ),
        "hgb_7": HistGradientBoostingClassifier(
            learning_rate=0.04,max_iter=180,max_leaf_nodes=7,
            min_samples_leaf=35,l2_regularization=2.0,random_state=17,
        ),
        "hgb_15": HistGradientBoostingClassifier(
            learning_rate=0.035,max_iter=180,max_leaf_nodes=15,
            min_samples_leaf=45,l2_regularization=4.0,random_state=17,
        ),
    }


def _fit_named(name,train):
    model=_models()[name]
    x,y=_matrix(train)
    model.fit(x,y)
    return model


def _predict(model,rows):
    if not rows:
        return np.asarray([],dtype=float)
    x,_=_matrix(rows)
    return model.predict_proba(x)[:,1]


def _base_rate(train):
    # Smoothed home-win base rate from training only.
    wins=sum(int(r["target"]) for r in train)
    return (wins+1)/(len(train)+2)


def _shrink(p,base,w):
    return w*p+(1-w)*base


def _score_probs(rows,probs):
    loss=0.0
    for r,p in zip(rows,probs):
        loss+=_ll(float(p),bool(r["target"]))
    return loss/len(rows) if rows else None


def _choose(features,season):
    cal=[r for r in features if r["season"]==season-1]
    train=[r for r in features if r["season"]<season-1]
    if len(cal)<MIN_CAL or len(train)<1000:
        return None
    base=_base_rate(train)
    candidates=[]
    for name in _models():
        model=_fit_named(name,train)
        raw=_predict(model,cal)
        for w in SHRINKS:
            probs=[_shrink(float(p),base,w) for p in raw]
            ll=_score_probs(cal,probs)
            candidates.append((ll,name,w))
    if not candidates:
        return None
    ll,name,w=min(candidates,key=lambda z:(z[0],z[1],z[2]))
    return {"model":name,"shrink":w,"calibration_logloss":ll,
            "calibration_n":len(cal),"selection_train_n":len(train)}


def evaluate_season(features,season):
    test=[r for r in features if r["season"]==season]
    train=[r for r in features if r["season"]<season]
    choice=_choose(features,season)
    if len(test)<MIN_TEST or len(train)<1000 or choice is None:
        return {"status":"INSUFFICIENT_HISTORY_OR_TEST",
                "train_n":len(train),"test_n":len(test),"choice":choice}

    model=_fit_named(choice["model"],train)
    raw=_predict(model,test)
    base=_base_rate(train)
    probs=[_shrink(float(p),base,choice["shrink"]) for p in raw]

    model_loss=market_loss=profit=clv_sum=ev_sum=0.0
    bets=wins=positive_clv=0
    for r,p in zip(test,probs):
        y=bool(r["target"])
        qclose=_devig_home(r["home_close"],r["away_close"])
        model_loss+=_ll(p,y)
        market_loss+=_ll(qclose,y)

        evh=p*r["home_open"]-1
        eva=(1-p)*r["away_open"]-1
        if max(evh,eva)<MIN_EV:
            continue
        side_home=evh>=eva
        entry=r["home_open"] if side_home else r["away_open"]
        close_prob=qclose if side_home else 1-qclose
        ev=evh if side_home else eva
        clv=close_prob*entry-1
        win=y if side_home else not y
        bets+=1; ev_sum+=ev; clv_sum+=clv
        positive_clv+=clv>0
        if win:
            wins+=1; profit+=entry-1
        else:
            profit-=1

    n=len(test)
    return {
        "status":"EVALUATED",
        "train_n":len(train),"test_n":n,
        "model":choice["model"],"shrink":choice["shrink"],
        "calibration_logloss":round(choice["calibration_logloss"],6),
        "model_logloss":round(model_loss/n,6),
        "market_logloss":round(market_loss/n,6),
        "logloss_gain_vs_market":round((market_loss-model_loss)/n,6),
        "bets":bets,"wins":wins,
        "profit_units":profit,
        "flat_roi":round(profit/bets,6) if bets else None,
        "mean_entry_ev":round(ev_sum/bets,6) if bets else None,
        "mean_archive_clv":round(clv_sum/bets,6) if bets else None,
        "positive_clv_rate":round(positive_clv/bets,6) if bets else None,
        "_model_loss_sum":model_loss,"_market_loss_sum":market_loss,
        "_clv_sum":clv_sum,"_ev_sum":ev_sum,"_positive_clv":positive_clv,
    }


def run(path=SOURCE,dest=OUT):
    rows=load_rows(path)
    features=build_features(rows)
    seasons=sorted({r["season"] for r in features})
    reports={str(s):evaluate_season(features,s) for s in seasons if s>=2014}
    pooled=[r for r in reports.values() if r.get("status")=="EVALUATED"]
    scored=sum(r["test_n"] for r in pooled)
    bets=sum(r["bets"] for r in pooled)
    profit=sum(r["profit_units"] for r in pooled)
    mloss=sum(r["_model_loss_sum"] for r in pooled)
    qloss=sum(r["_market_loss_sum"] for r in pooled)
    clv=sum(r["_clv_sum"] for r in pooled)
    ev=sum(r["_ev_sum"] for r in pooled)
    pclv=sum(r["_positive_clv"] for r in pooled)
    for r in pooled:
        for k in list(r):
            if k.startswith("_"):
                del r[k]

    baseline=None
    base_path=Path("data/hockey/nhl_bulk_backtest.json")
    if base_path.exists():
        try:
            baseline=json.loads(base_path.read_text(encoding="utf-8")).get("pooled")
        except Exception:
            baseline=None

    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "source_rows":len(rows),
        "feature_rows":len(features),
        "features":FEATURES,
        "model_selection":"previous-season only; candidate family + probability shrink selected on Y-1",
        "market_features_used":False,
        "fixed_min_ev":MIN_EV,
        "release_eligible":False,
        "pooled":{
            "scored_games":scored,
            "model_logloss":round(mloss/scored,6) if scored else None,
            "market_logloss":round(qloss/scored,6) if scored else None,
            "logloss_gain_vs_market":round((qloss-mloss)/scored,6) if scored else None,
            "bets":bets,
            "profit_units":round(profit,3),
            "flat_roi":round(profit/bets,6) if bets else None,
            "mean_entry_ev":round(ev/bets,6) if bets else None,
            "mean_archive_clv":round(clv/bets,6) if bets else None,
            "positive_clv_rate":round(pclv/bets,6) if bets else None,
        },
        "v1_pooled_reference":baseline,
        "season_results":reports,
    }
    Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=="__main__":
    run()
