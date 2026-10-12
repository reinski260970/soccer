from __future__ import annotations
import json, math, os
from pathlib import Path

from .m14_research import train_proxy
from .m17_1_research import _logloss
from .m17_5_research import _early_hyper, _rolling_eval, _market_logloss, mongo_coverage
from .m17_8_research import _prob_diagnostics
from .m17_18_hgb_research import LEAGUES, load_one, build_data, select_hyper as hgb_hyper, rolling_eval as hgb_eval

OUT = Path("data/m17_19_ensemble_validation.json")
ALPHA_GRID = (0.0, 0.15, 0.30, 0.45, 0.60)  # HGB weight; 0 = pure structural model
AGREE_GRID = (0.03, 0.05, 0.08, 0.12)
EDGE_GRID = (0.02, 0.03, 0.05, 0.075, 0.10)
ODDS_CAP_GRID = (2.0, 2.5, 3.0, 4.0)
SIDE = 2  # away, kept fixed for comparability with M17.16-M17.18

def _blend(pb, ph, alpha):
    p=[(1-alpha)*float(a)+alpha*float(b) for a,b in zip(pb,ph)]
    z=sum(p)
    return [x/z for x in p]

def _paired_eval(data, year, base_h, hgb_h, alpha):
    b=_rolling_eval(data,year,base_h)
    h=hgb_eval(data,year,hgb_h)
    if len(b)!=len(h): return []
    out=[]
    for rb,rh in zip(b,h):
        if (rb["date"],rb["home"],rb["away"]) != (rh["date"],rh["home"],rh["away"]):
            raise ValueError("base/HGB row alignment mismatch")
        out.append({**rb,"p_base":rb["p"],"p_hgb":rh["p"],
                    "p":_blend(rb["p"],rh["p"],alpha),
                    "model_gap":max(abs(x-y) for x,y in zip(rb["p"],rh["p"]))})
    return out

def select_alpha(data, base_h, hgb_h):
    folds=[]
    for year in (2020,2021):
        b=_rolling_eval(data,year,base_h); h=hgb_eval(data,year,hgb_h)
        if len(b)!=len(h) or len(b)<80: return None
        folds.append((b,h))
    best=None
    for a in ALPHA_GRID:
        losses=[]
        for b,h in folds:
            pp=[_blend(rb["p"],rh["p"],a) for rb,rh in zip(b,h)]
            losses.append(_logloss(pp,[r["y"] for r in b]))
        score=sum(losses)/len(losses)
        if best is None or score<best["cv_logloss"]:
            best={"hgb_weight":a,"structural_weight":1-a,
                  "cv_logloss":score,"fold_logloss":losses}
    return best

def _entry_stats(rows, edge, cap, agree):
    bets=0; pnl=0.0; clv=[]
    for r in rows:
        k=SIDE
        if r["model_gap"]>agree: continue
        o=float(r["op"][k])
        # Both component models must independently see non-negative EV.
        if r["p_base"][k]*o<=1.0 or r["p_hgb"][k]*o<=1.0: continue
        if r["p"][k]*o-1.0<edge or o>cap: continue
        bets+=1
        pnl += o-1.0 if r["y"]==k else -1.0
        pc = __import__("oddswatch.pricing",fromlist=["devig"]).devig(r["cl"])
        clv.append(o*pc[k]-1.0)
    vals=sorted(clv)
    med=(vals[len(vals)//2] if len(vals)%2 else
         ((vals[len(vals)//2-1]+vals[len(vals)//2])/2 if vals else 0.0))
    return {"bets":bets,"clv":sum(vals)/len(vals) if vals else 0.0,
            "median_clv":med,
            "positive_clv_rate":sum(v>0 for v in vals)/len(vals) if vals else 0.0,
            "roi":pnl/bets if bets else 0.0}

def tune_gate_2022(rows):
    best=near=None
    for edge in EDGE_GRID:
        for cap in ODDS_CAP_GRID:
            for agree in AGREE_GRID:
                s=_entry_stats(rows,edge,cap,agree)
                fails=[]
                if s["bets"]<20: fails.append("2022_bets<20")
                if s["clv"]<=0: fails.append("2022_mean_clv<=0")
                if s["median_clv"]<=0: fails.append("2022_median_clv<=0")
                if s["positive_clv_rate"]<0.55: fails.append("2022_positive_clv_rate<55%")
                score=s["clv"]*math.sqrt(max(s["bets"],1))*(0.5+s["positive_clv_rate"])
                c={"edge":edge,"cap":cap,"agree":agree,"side":"away",
                   "stats_2022":s,"fails_2022":fails,"score_2022":score}
                if near is None or score>near["score_2022"]: near=c
                if not fails and (best is None or score>best["score_2022"]): best=c
    return best,near

def validate_2023(rows, gate):
    if not gate:
        return False,{"bets":0,"clv":0.0,"median_clv":0.0,"positive_clv_rate":0.0,
                      "roi":0.0,"fails":["no_2022_gate"]}
    s=_entry_stats(rows,gate["edge"],gate["cap"],gate["agree"])
    fails=[]
    if s["bets"]<15: fails.append("2023_bets<15")
    if s["clv"]<=0: fails.append("2023_mean_clv<=0")
    if s["median_clv"]<=0: fails.append("2023_median_clv<=0")
    if s["positive_clv_rate"]<0.52: fails.append("2023_positive_clv_rate<52%")
    return not fails,{**s,"fails":fails}

def _score(rows):
    if not rows: return {"n":0,"model":9.0,"opening":9.0,"gain":-9.0}
    ml=_logloss([r["p"] for r in rows],[r["y"] for r in rows])
    mk=_market_logloss(rows)
    return {"n":len(rows),"model":ml,"opening":mk,"gain":mk-ml}

def league_run(ms,odds,shots,cov):
    data,vc,xc=build_data(ms,odds,shots)
    out={"samples":len(data),"coverage":cov,"previous_season_prior_coverage":vc,
         "previous_season_xg_prior_coverage":xc,"release_eligible":False}
    bh=_early_hyper(data); hh=hgb_hyper(data)
    out["base_hyper"]=bh; out["hgb_hyper"]=hh
    if bh is None or hh is None:
        return {**out,"validated":False,"reason":"too little early OOS data"}
    blend=select_alpha(data,bh,hh); out["blend"]=blend
    if blend is None:
        return {**out,"validated":False,"reason":"ensemble early OOS unavailable"}
    a=blend["hgb_weight"]
    ev={y:_paired_eval(data,y,bh,hh,a) for y in (2022,2023,2024,2025)}
    g,near=tune_gate_2022(ev[2022]); survived,v23=validate_2023(ev[2023],g)
    dg=g or near
    empty={"bets":0,"clv":0.0,"median_clv":0.0,"positive_clv_rate":0.0,"roi":0.0}
    s24=_entry_stats(ev[2024],dg["edge"],dg["cap"],dg["agree"]) if dg and ev[2024] else dict(empty)
    s25=_entry_stats(ev[2025],dg["edge"],dg["cap"],dg["agree"]) if dg and ev[2025] else dict(empty)
    out.update({"validated":False,"tuned_gate_2022":g,"near_miss_2022":near,
        "entry_validation_2023":v23,"gate_survived_2023":survived,
        "retrospective_stress_2024":s24,"diagnostic_only_2025":s25,
        "same_game_logloss":{str(y):_score(ev[y]) for y in ev},
        "probability_diagnostics":{str(y):_prob_diagnostics(ev[y]) for y in ev}})
    return out

def run(out=OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"]=os.environ["MONGODB_URI"]
    proxy=train_proxy()
    result={"_method":"M17.19 structural+HGB ensemble with agreement-gated entries; no market features",
            "_release":"challenger only; future forward/shadow validation required",
            "_alpha_grid":ALPHA_GRID,"_agreement_grid":AGREE_GRID,
            "_splits":{"model_and_blend":"2020+2021 OOS logloss",
                       "entry_tune":"2022","entry_validation":"2023",
                       "stress":"2024","diagnostic":"2025"},
            "mongo_profile":mongo_coverage(),"leagues":{}}
    log=[f"M17.19 proxy n={proxy['n']} RMSE={proxy['rmse']:.3f}"]
    for name,code in LEAGUES.items():
        try:
            ms,odds,shots,cov=load_one(name,code,proxy)
            r=league_run(ms,odds,shots,cov)
        except Exception as e:
            r={"validated":False,"release_eligible":False,"reason":f"{type(e).__name__}: {e}"}
        result["leagues"][name]=r
        bl=r.get("blend") or {}; ll=(r.get("same_game_logloss") or {}).get("2024") or {}
        s24=r.get("retrospective_stress_2024") or {}
        log.append(f"{name}: HGBw={bl.get('hgb_weight')} dLL24={ll.get('gain',-9):+.4f} "
                   f"CLV24={s24.get('clv',0)*100:+.2f}% -> CHALLENGER")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=1,default=str),encoding="utf-8")
    return log

if __name__=="__main__":
    for x in run(): print(x)
