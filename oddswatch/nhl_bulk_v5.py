"""NHL bulk model v5: dual-timescale MoneyPuck xG/shot features.

Slow and fast rolling states are built strictly from completed prior games.
Opening/closing odds are never model features.
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
from .nhl_moneypuck_features import augment_sbr_rows

OUT=Path("data/hockey/nhl_bulk_v5_backtest.json")
BASE_FEATURES=[
    "elo_diff","gf_diff","ga_diff","win_diff",
    "venue_attack_diff","venue_defence_diff",
    "rest_diff","home_rest","away_rest",
]
MP_BASE=[
    "mp_xgf5_diff","mp_xga5_diff","mp_sogf5_diff","mp_soga5_diff",
    "mp_caf5_diff","mp_caa5_diff","mp_hdxgf5_diff","mp_hdxga5_diff",
    "mp_xgfall_diff","mp_xgaall_diff","mp_sogfall_diff","mp_sogaall_diff",
    "mp_svaxgf_diff","mp_svaxga_diff","mp_corsi_share_diff","mp_xg_share_diff",
    "mp_xg_per_sog_for_diff","mp_xg_per_sog_against_diff",
    "mp_hd_share_for_diff","mp_hd_share_against_diff",
    "mp_non5v5_xgf_diff","mp_non5v5_xga_diff",
]
FEATURES=BASE_FEATURES+[f"slow_{x}" for x in MP_BASE]+[f"fast_{x}" for x in MP_BASE]
CS=(0.01,0.03,0.1,0.3,1.0)
SHRINKS=(0.45,0.60,0.75,0.90,1.0)
MIN_CAL=400
MIN_TEST=400


def _key(r):
    return (r["date"],r["home"],r["away"])


def build_rows(raw):
    slow,u1=augment_sbr_rows(raw,alpha=.05)
    fast,u2=augment_sbr_rows(raw,alpha=.18)
    fmap={_key(r):r for r in fast}
    common=[r for r in slow if _key(r) in fmap]
    base=build_features(common,alpha=.10,elo_k=18.0,season_retain=1.0)
    if len(base)!=len(common):
        raise RuntimeError("feature alignment mismatch")
    out=[]
    for b,s in zip(base,common):
        f=fmap[_key(s)]
        q=dict(b)
        for name in MP_BASE:
            q[f"slow_{name}"]=float(s[name])
            q[f"fast_{name}"]=float(f[name])
        out.append(q)
    return out,u1,u2


def _xy(rows):
    x=np.asarray([[float(r[k]) for k in FEATURES] for r in rows],dtype=float)
    y=np.asarray([int(r["target"]) for r in rows],dtype=int)
    return x,y


def _fit(c,rows):
    x,y=_xy(rows)
    m=make_pipeline(
        StandardScaler(),
        LogisticRegression(C=float(c),max_iter=2000,solver="lbfgs"),
    )
    m.fit(x,y)
    return m


def _pred(m,rows):
    if not rows:return np.asarray([])
    x,_=_xy(rows)
    return m.predict_proba(x)[:,1]


def _base(rows):
    return (sum(int(r["target"]) for r in rows)+1)/(len(rows)+2)


def _blend(p,b,w):
    return w*float(p)+(1-w)*b


def _select(rows,season):
    train=[r for r in rows if r["season"]<season-1]
    cal=[r for r in rows if r["season"]==season-1]
    if len(train)<1000 or len(cal)<MIN_CAL:return None
    b=_base(train); cand=[]
    for c in CS:
        m=_fit(c,train); raw=_pred(m,cal)
        for w in SHRINKS:
            ps=[_blend(p,b,w) for p in raw]
            ll=sum(_ll(p,bool(r["target"])) for r,p in zip(cal,ps))/len(cal)
            cand.append((ll,c,w))
    ll,c,w=min(cand,key=lambda z:(z[0],z[1],z[2]))
    return {"C":c,"shrink":w,"calibration_logloss":ll}


def evaluate(rows,season):
    train=[r for r in rows if r["season"]<season]
    test=[r for r in rows if r["season"]==season]
    choice=_select(rows,season)
    if choice is None or len(test)<MIN_TEST:
        return {"status":"INSUFFICIENT_HISTORY_OR_TEST","train_n":len(train),"test_n":len(test)}
    m=_fit(choice["C"],train); b=_base(train)
    probs=[_blend(p,b,choice["shrink"]) for p in _pred(m,test)]
    ml=ql=profit=clv=ev=0.0; bets=wins=pos=0
    for r,p in zip(test,probs):
        y=bool(r["target"]); q=_devig_home(r["home_close"],r["away_close"])
        ml+=_ll(p,y); ql+=_ll(q,y)
        eh=p*r["home_open"]-1; ea=(1-p)*r["away_open"]-1
        if max(eh,ea)<MIN_EV:continue
        home=eh>=ea
        entry=r["home_open"] if home else r["away_open"]
        cp=q if home else 1-q; e=eh if home else ea; cv=cp*entry-1
        win=y if home else not y
        bets+=1;ev+=e;clv+=cv;pos+=cv>0
        if win:wins+=1;profit+=entry-1
        else:profit-=1
    n=len(test)
    return {
        "status":"EVALUATED","train_n":len(train),"test_n":n,
        "C":choice["C"],"shrink":choice["shrink"],
        "calibration_logloss":round(choice["calibration_logloss"],6),
        "model_logloss":round(ml/n,6),"market_logloss":round(ql/n,6),
        "logloss_gain_vs_market":round((ql-ml)/n,6),
        "bets":bets,"wins":wins,"profit_units":profit,
        "flat_roi":round(profit/bets,6) if bets else None,
        "mean_entry_ev":round(ev/bets,6) if bets else None,
        "mean_archive_clv":round(clv/bets,6) if bets else None,
        "positive_clv_rate":round(pos/bets,6) if bets else None,
        "_ml":ml,"_ql":ql,"_clv":clv,"_ev":ev,"_pos":pos,
    }


def run(path=SOURCE,dest=OUT):
    raw=load_rows(path)
    rows,u1,u2=build_rows(raw)
    seasons=sorted({r["season"] for r in rows})
    reports={str(s):evaluate(rows,s) for s in seasons if s>=2014}
    pooled=[r for r in reports.values() if r.get("status")=="EVALUATED"]
    scored=sum(r["test_n"] for r in pooled);bets=sum(r["bets"] for r in pooled)
    profit=sum(r["profit_units"] for r in pooled)
    ml=sum(r["_ml"] for r in pooled);ql=sum(r["_ql"] for r in pooled)
    clv=sum(r["_clv"] for r in pooled);ev=sum(r["_ev"] for r in pooled)
    pos=sum(r["_pos"] for r in pooled)
    for r in pooled:
        for k in list(r):
            if k.startswith("_"):del r[k]
    refs={}
    for v,p in (("v1","data/hockey/nhl_bulk_backtest.json"),
                ("v2","data/hockey/nhl_bulk_v2_backtest.json"),
                ("v4","data/hockey/nhl_bulk_v4_backtest.json")):
        try:refs[v]=json.loads(Path(p).read_text(encoding="utf-8")).get("pooled")
        except Exception:refs[v]=None
    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "source_odds_rows":len(raw),"matched_rows":len(rows),
        "slow_unmatched":len(u1),"fast_unmatched":len(u2),
        "features":FEATURES,"market_features_used":False,
        "model":"dual-timescale MoneyPuck + result features; logistic only",
        "fixed_min_ev":MIN_EV,"release_eligible":False,
        "pooled":{
            "scored_games":scored,
            "model_logloss":round(ml/scored,6) if scored else None,
            "market_logloss":round(ql/scored,6) if scored else None,
            "logloss_gain_vs_market":round((ql-ml)/scored,6) if scored else None,
            "bets":bets,"profit_units":round(profit,3),
            "flat_roi":round(profit/bets,6) if bets else None,
            "mean_entry_ev":round(ev/bets,6) if bets else None,
            "mean_archive_clv":round(clv/bets,6) if bets else None,
            "positive_clv_rate":round(pos/bets,6) if bets else None,
        },
        "references":refs,"season_results":reports,
    }
    Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return result

if __name__=="__main__":
    run()
