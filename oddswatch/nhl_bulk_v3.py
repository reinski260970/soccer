"""NHL bulk model v3: nested tuning of recency, Elo and offseason mean reversion.

All model features come only from prior game results. Market odds are excluded
from model fitting and are used only for post-prediction entry/CLV evaluation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .nhl_bulk_backtest import SOURCE, MIN_EV, _devig_home, _ll, load_rows
from .nhl_bulk_features import build_features

OUT = Path("data/hockey/nhl_bulk_v3_backtest.json")
FEATURES = [
    "elo_diff","gf_diff","ga_diff","win_diff",
    "venue_attack_diff","venue_defence_diff",
    "rest_diff","home_rest","away_rest",
]
CONFIGS = (
    {"name":"a06_k12_r35","alpha":0.06,"elo_k":12.0,"season_retain":0.35},
    {"name":"a06_k20_r55","alpha":0.06,"elo_k":20.0,"season_retain":0.55},
    {"name":"a10_k12_r35","alpha":0.10,"elo_k":12.0,"season_retain":0.35},
    {"name":"a10_k20_r55","alpha":0.10,"elo_k":20.0,"season_retain":0.55},
    {"name":"a16_k12_r35","alpha":0.16,"elo_k":12.0,"season_retain":0.35},
    {"name":"a16_k20_r55","alpha":0.16,"elo_k":20.0,"season_retain":0.55},
)
CS=(0.05,0.2,1.0,4.0)
SHRINKS=(0.45,0.60,0.75,0.90,1.00)
MIN_CAL=400
MIN_TEST=400


def _xy(rows):
    x=np.asarray([[float(r[k]) for k in FEATURES] for r in rows],dtype=float)
    y=np.asarray([int(r["target"]) for r in rows],dtype=int)
    return x,y


def _fit(train,c):
    x,y=_xy(train)
    m=make_pipeline(
        StandardScaler(),
        LogisticRegression(C=float(c),max_iter=1500,solver="lbfgs"),
    )
    m.fit(x,y)
    return m


def _probs(model,rows):
    if not rows:
        return np.asarray([],dtype=float)
    x,_=_xy(rows)
    return model.predict_proba(x)[:,1]


def _base(train):
    return (sum(int(r["target"]) for r in train)+1)/(len(train)+2)


def _blend(p,base,w):
    return w*float(p)+(1-w)*base


def _avg_ll(rows,probs):
    return sum(_ll(float(p),bool(r["target"])) for r,p in zip(rows,probs))/len(rows)


def _precompute(raw_rows):
    return {
        cfg["name"]: build_features(
            raw_rows,
            alpha=cfg["alpha"],
            elo_k=cfg["elo_k"],
            season_retain=cfg["season_retain"],
        )
        for cfg in CONFIGS
    }


def _select(feature_sets,season):
    candidates=[]
    for cfg in CONFIGS:
        rows=feature_sets[cfg["name"]]
        train=[r for r in rows if r["season"]<season-1]
        cal=[r for r in rows if r["season"]==season-1]
        if len(train)<1000 or len(cal)<MIN_CAL:
            continue
        base=_base(train)
        for c in CS:
            model=_fit(train,c)
            raw=_probs(model,cal)
            for w in SHRINKS:
                ps=[_blend(p,base,w) for p in raw]
                candidates.append((_avg_ll(cal,ps),cfg["name"],c,w,len(train),len(cal)))
    if not candidates:
        return None
    ll,cfg,c,w,tn,cn=min(candidates,key=lambda z:(z[0],z[1],z[2],z[3]))
    return {
        "calibration_logloss":ll,
        "config":cfg,
        "C":c,
        "shrink":w,
        "selection_train_n":tn,
        "calibration_n":cn,
    }


def evaluate_season(feature_sets,season):
    choice=_select(feature_sets,season)
    if choice is None:
        return {"status":"INSUFFICIENT_HISTORY_OR_TEST"}
    rows=feature_sets[choice["config"]]
    train=[r for r in rows if r["season"]<season]
    test=[r for r in rows if r["season"]==season]
    if len(train)<1000 or len(test)<MIN_TEST:
        return {"status":"INSUFFICIENT_HISTORY_OR_TEST","train_n":len(train),"test_n":len(test)}

    model=_fit(train,choice["C"])
    base=_base(train)
    raw=_probs(model,test)
    probs=[_blend(p,base,choice["shrink"]) for p in raw]

    mloss=qloss=profit=clv=evsum=0.0
    bets=wins=posclv=0
    for r,p in zip(test,probs):
        y=bool(r["target"])
        q=_devig_home(r["home_close"],r["away_close"])
        mloss+=_ll(p,y); qloss+=_ll(q,y)
        evh=p*r["home_open"]-1
        eva=(1-p)*r["away_open"]-1
        if max(evh,eva)<MIN_EV:
            continue
        home=evh>=eva
        entry=r["home_open"] if home else r["away_open"]
        closep=q if home else 1-q
        e=evh if home else eva
        cval=closep*entry-1
        win=y if home else not y
        bets+=1; evsum+=e; clv+=cval; posclv+=cval>0
        if win:
            wins+=1; profit+=entry-1
        else:
            profit-=1

    n=len(test)
    return {
        "status":"EVALUATED",
        "train_n":len(train),"test_n":n,
        "selected_config":choice["config"],
        "C":choice["C"],"shrink":choice["shrink"],
        "calibration_logloss":round(choice["calibration_logloss"],6),
        "model_logloss":round(mloss/n,6),
        "market_logloss":round(qloss/n,6),
        "logloss_gain_vs_market":round((qloss-mloss)/n,6),
        "bets":bets,"wins":wins,
        "profit_units":profit,
        "flat_roi":round(profit/bets,6) if bets else None,
        "mean_entry_ev":round(evsum/bets,6) if bets else None,
        "mean_archive_clv":round(clv/bets,6) if bets else None,
        "positive_clv_rate":round(posclv/bets,6) if bets else None,
        "_mloss":mloss,"_qloss":qloss,"_clv":clv,"_ev":evsum,"_posclv":posclv,
    }


def run(path=SOURCE,dest=OUT):
    raw=load_rows(path)
    feature_sets=_precompute(raw)
    seasons=sorted({r["season"] for r in raw})
    reports={str(s):evaluate_season(feature_sets,s) for s in seasons if s>=2014}
    pooled=[r for r in reports.values() if r.get("status")=="EVALUATED"]
    scored=sum(r["test_n"] for r in pooled)
    bets=sum(r["bets"] for r in pooled)
    profit=sum(r["profit_units"] for r in pooled)
    mloss=sum(r["_mloss"] for r in pooled); qloss=sum(r["_qloss"] for r in pooled)
    clv=sum(r["_clv"] for r in pooled); ev=sum(r["_ev"] for r in pooled)
    pos=sum(r["_posclv"] for r in pooled)
    for r in pooled:
        for k in list(r):
            if k.startswith("_"):
                del r[k]

    v1=v2=None
    for p,label in [(Path("data/hockey/nhl_bulk_backtest.json"),"v1"),(Path("data/hockey/nhl_bulk_v2_backtest.json"),"v2")]:
        if p.exists():
            try:
                val=json.loads(p.read_text(encoding="utf-8")).get("pooled")
                if label=="v1": v1=val
                else: v2=val
            except Exception:
                pass

    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "source_rows":len(raw),
        "market_features_used":False,
        "selection":"recency/Elo/offseason/C/shrink selected on previous season only",
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
            "positive_clv_rate":round(pos/bets,6) if bets else None,
        },
        "v1_reference":v1,
        "v2_reference":v2,
        "season_results":reports,
    }
    Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=="__main__":
    run()
