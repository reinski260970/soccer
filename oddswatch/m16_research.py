"""M16: de-correlated dual-Poisson CLV research.

Goal:
- remove Elo/form/rest double counting from M13/M14
- stronger shrinkage and probability flattening
- no market odds as model features
- choose structural model/calibration by outcome logloss on tune only
- choose entry gate by robust positive tune CLV
- 2025/26 is diagnostic only because it has already been inspected
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path

from . import pricing
from .m13_research import load_real_xg, strategy as m13_strategy, choose_entry as m13_choose
from .m14_research import load_league, train_proxy, strategy as m14_strategy, choose_entry as m14_choose
from .models.m11 import M11Model, M11Params
from .models.m9 import M9Model, M9Params

OUT = Path("data/m16_validation.json")

TOP5 = {
    "bundesliga": "D1",
    "epl": "E0",
    "laliga": "SP1",
    "seriea": "I1",
    "ligue1": "F1",
}
EUROPE = {
    "2bundesliga": "D2",
    "championship": "E1",
    "eredivisie": "N1",
    "primeira": "P1",
    "belgium": "B1",
    "turkey": "T1",
    "scotland": "SC0",
    "greece": "G1",
}

CALIB = (0.50, 0.65, 0.80, 0.95, 1.00)

TOP5_VARIANTS = [
    M11Params(half_life_days=180, shrink=10.0, xg_blend=0.50, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
    M11Params(half_life_days=270, shrink=15.0, xg_blend=0.60, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
    M11Params(half_life_days=365, shrink=25.0, xg_blend=0.70, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
    M11Params(half_life_days=365, shrink=35.0, xg_blend=0.55, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
]
EUROPE_VARIANTS = [
    M9Params(half_life_days=180, shrink=10.0, xg_blend=0.40, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
    M9Params(half_life_days=270, shrink=15.0, xg_blend=0.50, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
    M9Params(half_life_days=365, shrink=25.0, xg_blend=0.60, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
    M9Params(half_life_days=365, shrink=35.0, xg_blend=0.45, elo_scale=0.0, xg_form_scale=0.0, rest_scale=0.0),
]


def _calibrate(p, a):
    q=[max(x,1e-9)**a for x in p]
    z=sum(q)
    return [x/z for x in q]


def _samples(matches, rows, seasons, params, cls):
    out=[]
    model=None
    last_fit=None
    for season,d,h,a,hg,ag,op,cl in rows:
        if season not in seasons:
            continue
        if last_fit is None or (d-last_fit).days>=14:
            hist=[m for m in matches if m.date<d]
            try:
                model=cls.fit(hist,d,params)
            except ValueError:
                model=None
            last_fit=d
        if model is None:
            continue
        try:
            mk=model.markets(h,a,kickoff=d)
        except Exception:
            continue
        out.append((season,[mk["1"],mk["X"],mk["2"]],pricing.devig(op),pricing.devig(cl),
                    [hg>ag,hg==ag,hg<ag],op))
    return out


def _logloss(rows,a):
    if not rows:
        return 99.0
    s=0.0
    for _,pm,_,_,y,_ in rows:
        p=_calibrate(pm,a)
        i=y.index(True)
        s-=math.log(max(p[i],1e-12))
    return s/len(rows)


def _choose_structure(matches, rows, variants, cls, tune={2023,2024}):
    best=None
    all_seasons=tune|{2025}
    for vi,p in enumerate(variants):
        s=_samples(matches,rows,all_seasons,p,cls)
        tr=[x for x in s if x[0] in tune]
        ho=[x for x in s if x[0]==2025]
        if len(tr)<300 or len(ho)<100:
            continue
        for a in CALIB:
            ll=_logloss(tr,a)
            if best is None or ll<best["logloss"]:
                best={"variant":vi,"params":p,"calib":a,"logloss":ll,"train":tr,"hold":ho}
    return best


def _stats(strategy_fn, rows, calib, cfg):
    if not cfg:
        return {"bets":0,"clv":0.0,"roi":0.0}
    return strategy_fn(rows,calib,**cfg)


def run(out=OUT):
    tune={2023,2024}
    result={"_method":"M16 de-correlated dual Poisson; no Elo/form/rest overlay; no market features",
            "_tune":[2023,2024],"_diagnostic":[2025]}
    log=["M16: remove Elo/form/rest double counting; stronger shrink + calibration"]

    for league,code in TOP5.items():
        ms,rows,cov=load_real_xg(code)
        best=_choose_structure(ms,rows,TOP5_VARIANTS,M11Model,tune)
        if not best:
            result[league]={"validated":False,"reason":"too little data"}
            log.append(f"{league}: too little data")
            continue
        cfg,tune_stats=m13_choose(best["train"],best["calib"],tune)
        diag=_stats(m13_strategy,best["hold"],best["calib"],cfg)
        result[league]={
            "variant":best["variant"],"params":asdict(best["params"]),"calib":best["calib"],
            "tune_logloss":best["logloss"],"gate":cfg,"tune":tune_stats,"diagnostic_2025":diag,
            "validated":False,
        }
        log.append(f"{league}: v{best['variant']} a={best['calib']:.2f} gate={cfg} | "
                   f"2025 n={diag['bets']} CLV={diag['clv']*100:+.2f}% ROI={diag['roi']*100:+.2f}%")

    proxy=train_proxy()
    result["_proxy"]={"n":proxy["n"],"rmse":proxy["rmse"],"beta":proxy["beta"]}
    for league,code in EUROPE.items():
        ms,rows,cov=load_league(code,proxy)
        best=_choose_structure(ms,rows,EUROPE_VARIANTS,M9Model,tune)
        if not best:
            result[league]={"validated":False,"reason":"too little data"}
            log.append(f"{league}: too little data")
            continue
        cfg,tune_stats=m14_choose(best["train"],best["calib"],tune)
        diag=_stats(m14_strategy,best["hold"],best["calib"],cfg)
        result[league]={
            "variant":best["variant"],"params":asdict(best["params"]),"calib":best["calib"],
            "tune_logloss":best["logloss"],"gate":cfg,"tune":tune_stats,"diagnostic_2025":diag,
            "validated":False,
        }
        log.append(f"{league}: v{best['variant']} a={best['calib']:.2f} gate={cfg} | "
                   f"2025 n={diag['bets']} CLV={diag['clv']*100:+.2f}% ROI={diag['roi']*100:+.2f}%")

    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=1,ensure_ascii=False),encoding="utf-8")
    return log


if __name__=="__main__":
    for line in run():
        print(line)
