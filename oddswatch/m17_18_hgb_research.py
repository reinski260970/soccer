from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from .m13_research import load_real_xg
from .m14_research import load_league, train_proxy
from .m17_1_research import TOP5, EUROPE, CALIB, _calibrate, _entry_stats, _logloss, load_real_shots
from .m17_5_research import START_YEAR, END_YEAR, _market_logloss, mongo_coverage
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import build_previous_season_xg_priors, augment_with_xg_priors
from .m17_8_research import _prob_diagnostics
from .m17_16_research import _tune_gate_2022, _validate_gate_2023
from .m17_17_research import build_regime_dataset

OUT = Path("data/m17_18_hgb_validation.json")
LEAGUES = {**TOP5, **EUROPE}
GRID = (
    dict(learning_rate=.03,max_iter=180,max_leaf_nodes=7,min_samples_leaf=30,l2_regularization=1.0),
    dict(learning_rate=.04,max_iter=220,max_leaf_nodes=15,min_samples_leaf=30,l2_regularization=1.0),
    dict(learning_rate=.05,max_iter=180,max_leaf_nodes=15,min_samples_leaf=45,l2_regularization=2.0),
    dict(learning_rate=.03,max_iter=260,max_leaf_nodes=31,min_samples_leaf=45,l2_regularization=2.0),
)

def build_data(matches, odds, shots):
    d = build_regime_dataset(matches, odds, shots)
    d, vc = augment_with_priors(d, build_previous_season_priors(matches))
    d, xc = augment_with_xg_priors(d, build_previous_season_xg_priors(matches))
    return d, vc, xc

def _fit_raw(train, test, p):
    m = HistGradientBoostingClassifier(loss="log_loss", early_stopping=False, random_state=42, **p)
    m.fit(np.asarray([r["x"] for r in train],float), np.asarray([r["y"] for r in train],int))
    z = m.predict_proba(np.asarray([r["x"] for r in test],float))
    cls = list(m.classes_); ix = [cls.index(i) for i in (0,1,2)]
    return [[float(row[j]) for j in ix] for row in z]

def select_hyper(data):
    folds = [
        ([r for r in data if r["season"]<=2019],[r for r in data if r["season"]==2020]),
        ([r for r in data if r["season"]<=2020],[r for r in data if r["season"]==2021]),
    ]
    if any(len(a)<400 or len(b)<80 for a,b in folds): return None
    best = None
    for p in GRID:
        raw = [(va,_fit_raw(tr,va,p)) for tr,va in folds]
        for a in CALIB:
            ll = [_logloss([_calibrate(x,a) for x in pp],[r["y"] for r in va]) for va,pp in raw]
            s = sum(ll)/len(ll)
            if best is None or s<best["cv_logloss"]:
                best = {"params":p,"calib":a,"cv_logloss":s,"fold_logloss":ll}
    return best

def rolling_eval(data, year, h):
    tr=[r for r in data if r["season"]<=year-1]; te=[r for r in data if r["season"]==year]
    if len(tr)<500 or len(te)<60: return []
    pp=[_calibrate(x,h["calib"]) for x in _fit_raw(tr,te,h["params"])]
    return [{**r,"p":p} for r,p in zip(te,pp)]

def score(rows):
    if not rows: return {"n":0,"model":9.0,"opening":9.0,"gain":-9.0}
    ml=_logloss([r["p"] for r in rows],[r["y"] for r in rows]); mk=_market_logloss(rows)
    return {"n":len(rows),"model":ml,"opening":mk,"gain":mk-ml}

def load_one(name, code, proxy):
    if name in TOP5:
        ms, odds, meta = load_real_xg(code,start_year=START_YEAR,end_year=END_YEAR)
        cov={"matches":len(ms),"odds_rows":len(odds),"xg_source":"real","meta":meta}
    else:
        ms, odds, cov = load_league(code,proxy,start_year=START_YEAR,end_year=END_YEAR)
        cov=dict(cov); cov["xg_source"]="shot_proxy"
    shots=load_real_shots(code,start_year=START_YEAR,end_year=END_YEAR); cov["real_shot_rows"]=len(shots)
    return ms, odds, shots, cov

def league_run(ms, odds, shots, cov):
    data,vc,xc=build_data(ms,odds,shots)
    out={"samples":len(data),"coverage":cov,"previous_season_prior_coverage":vc,
         "previous_season_xg_prior_coverage":xc,"release_eligible":False}
    h=select_hyper(data); out["hyper"]=h
    if h is None: return {**out,"validated":False,"reason":"too little early OOS data"}
    ev={y:rolling_eval(data,y,h) for y in (2022,2023,2024,2025)}
    g,near=_tune_gate_2022(ev[2022]); survived,v23=_validate_gate_2023(ev[2023],g)
    dg=g or near
    empty={"bets":0,"clv":0.0,"median_clv":0.0,"positive_clv_rate":0.0,"roi":0.0}
    s24=_entry_stats(ev[2024],dg["edge"],dg["cap"],dg["side"]) if dg and ev[2024] else dict(empty)
    s25=_entry_stats(ev[2025],dg["edge"],dg["cap"],dg["side"]) if dg and ev[2025] else dict(empty)
    out.update({"validated":False,"tuned_gate_2022":g,"near_miss_2022":near,
        "entry_validation_2023":v23,"gate_survived_2023":survived,
        "retrospective_stress_2024":s24,"diagnostic_only_2025":s25,
        "same_game_logloss":{str(y):score(ev[y]) for y in ev},
        "probability_diagnostics":{str(y):_prob_diagnostics(ev[y]) for y in ev}})
    return out

def run(out=OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"]=os.environ["MONGODB_URI"]
    proxy=train_proxy()
    result={"_method":"M17.18-HGB challenger on leakage-safe M17.17 features; no market features",
            "_release":"challenger only; future forward/shadow CLV required",
            "_splits":{"hyper":"2020+2021 OOS logloss","entry_tune":"2022","entry_validation":"2023",
                       "stress":"2024","diagnostic":"2025"},
            "mongo_profile":mongo_coverage(),"leagues":{}}
    log=[f"M17.18-HGB proxy n={proxy['n']} RMSE={proxy['rmse']:.3f}"]
    for name,code in LEAGUES.items():
        try:
            ms,odds,shots,cov=load_one(name,code,proxy); r=league_run(ms,odds,shots,cov)
        except Exception as e:
            r={"validated":False,"release_eligible":False,"reason":f"{type(e).__name__}: {e}"}
        result["leagues"][name]=r
        ll=(r.get("same_game_logloss") or {}).get("2024") or {}
        log.append(f"{name}: n={r.get('samples',0)} dLL24={ll.get('gain',-9):+.4f} -> CHALLENGER")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=1,default=str),encoding="utf-8")
    return log

if __name__=="__main__":
    for x in run(): print(x)
