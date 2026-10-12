"""Large-sample historical NHL market backtest.

Uses regulation-period goals to fit a preseason Poisson model, converts 60-minute
1X2 probabilities to 2-way winner probabilities including OT/SO, selects a
calibration blend on the previous season only, and evaluates against archived
opening/closing moneylines.

Archived "open"/"close" labels are treated as historical market references,
not authenticated executable timestamps.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from .models.poisson import Match, PoissonModel, hockey_regulation_to_moneyline

SOURCE = Path("data/hockey/market/nhl_sbr_2011_2021.csv")
OUT = Path("data/hockey/nhl_bulk_backtest.json")
WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)
MIN_EV = 0.03
MIN_CAL = 400
MIN_TEST = 400


def american_to_decimal(x: float) -> float:
    x=float(x)
    if x == 0:
        raise ValueError("zero American odds")
    return 1 + (x/100 if x>0 else 100/abs(x))


def load_rows(path: Path = SOURCE) -> list[dict]:
    rows=[]
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                d=str(r["date"])
                day=date(int(d[:4]),int(d[4:6]),int(d[6:8]))
                row={
                    "season":int(r["season"]),
                    "date":day,
                    "home":r["home_team"].strip(),
                    "away":r["away_team"].strip(),
                    "reg_home":int(r["reg_home"]),
                    "reg_away":int(r["reg_away"]),
                    "final_home":int(r["final_home"]),
                    "final_away":int(r["final_away"]),
                    "home_open":american_to_decimal(float(r["home_open_ml"])),
                    "away_open":american_to_decimal(float(r["away_open_ml"])),
                    "home_close":american_to_decimal(float(r["home_close_ml"])),
                    "away_close":american_to_decimal(float(r["away_close_ml"])),
                }
                if row["home"]==row["away"] or row["final_home"]==row["final_away"]:
                    continue
                rows.append(row)
            except (KeyError,TypeError,ValueError,ZeroDivisionError):
                continue
    return sorted(rows,key=lambda r:(r["date"],r["home"],r["away"]))


def _fit(rows:list[dict], cutoff:int):
    training=[r for r in rows if r["season"]<cutoff and r["date"]<date(cutoff,7,1)]
    if len(training)<1000:
        return None,training,None
    model=PoissonModel.fit(
        [Match(r["date"],r["home"],r["away"],r["reg_home"],r["reg_away"]) for r in training],
        date(cutoff,7,1),half_life_days=730.0,xg_weight=0.0,
        shrink=10.0,rho=0.0,max_goals=12,iterations=90,
    )
    home_wins=sum(r["final_home"]>r["final_away"] for r in training)
    base=(home_wins+1)/(len(training)+2)
    return model,training,base


def _p_home(model,row) -> float|None:
    try:
        m=model.markets(row["home"],row["away"])
        ph,pa=hockey_regulation_to_moneyline(m["1"],m["X"],m["2"])
        return ph if 0<ph<1 and abs(ph+pa-1)<1e-6 else None
    except (KeyError,ValueError,OverflowError,ZeroDivisionError):
        return None


def _ll(p:float,y:bool)->float:
    return -math.log(max(p if y else 1-p,1e-12))


def _devig_home(home_odds:float,away_odds:float)->float:
    h,a=1/home_odds,1/away_odds
    return h/(h+a)


def _mix(p:float,base:float,alpha:float)->float:
    return alpha*p+(1-alpha)*base


def _choose_alpha(rows:list[dict], season:int):
    # For test season Y, calibrate on Y-1 using a model fit strictly before Y-1.
    cal=[r for r in rows if r["season"]==season-1]
    model,_,base=_fit(rows,season-1)
    if model is None or len(cal)<MIN_CAL:
        return None
    scored=[]
    for alpha in WEIGHTS:
        loss=n=0.0
        count=0
        for r in cal:
            p=_p_home(model,r)
            if p is None: continue
            y=r["final_home"]>r["final_away"]
            loss+=_ll(_mix(p,base,alpha),y); count+=1
        if count>=MIN_CAL:
            scored.append((alpha,loss/count))
    return min(scored,key=lambda x:(x[1],abs(x[0]-.5)))[0] if scored else None


def evaluate_season(rows:list[dict],season:int)->dict:
    test=[r for r in rows if r["season"]==season]
    model,training,base=_fit(rows,season)
    alpha=_choose_alpha(rows,season)
    if model is None or alpha is None or len(test)<MIN_TEST:
        return {"status":"INSUFFICIENT_HISTORY_OR_TEST","train_n":len(training),"test_n":len(test),"alpha":alpha}

    n=0; model_ll=market_ll=profit=clv_sum=ev_sum=0.0
    bets=wins=positive_clv=0
    for r in test:
        p0=_p_home(model,r)
        if p0 is None: continue
        p=_mix(p0,base,alpha)
        y=r["final_home"]>r["final_away"]
        q_close=_devig_home(r["home_close"],r["away_close"])
        model_ll+=_ll(p,y); market_ll+=_ll(q_close,y); n+=1

        ev_home=p*r["home_open"]-1
        ev_away=(1-p)*r["away_open"]-1
        if max(ev_home,ev_away)<MIN_EV:
            continue
        side_home=ev_home>=ev_away
        entry=r["home_open"] if side_home else r["away_open"]
        p_close=q_close if side_home else 1-q_close
        ev=ev_home if side_home else ev_away
        clv=p_close*entry-1
        win=y if side_home else not y
        bets+=1; ev_sum+=ev; clv_sum+=clv; positive_clv+=clv>0
        if win:
            wins+=1; profit+=entry-1
        else:
            profit-=1

    return {
        "status":"EVALUATED",
        "train_n":len(training),"test_n":len(test),"scored_n":n,"alpha":alpha,
        "model_logloss":round(model_ll/n,6) if n else None,
        "market_logloss":round(market_ll/n,6) if n else None,
        "logloss_gain_vs_market":round((market_ll-model_ll)/n,6) if n else None,
        "bets":bets,"wins":wins,
        "flat_roi":round(profit/bets,6) if bets else None,
        "mean_entry_ev":round(ev_sum/bets,6) if bets else None,
        "mean_archive_clv":round(clv_sum/bets,6) if bets else None,
        "positive_clv_rate":round(positive_clv/bets,6) if bets else None,
    }


def run(path:Path=SOURCE,dest:Path=OUT)->dict:
    rows=load_rows(path)
    seasons=sorted({r["season"] for r in rows})
    reports={str(s):evaluate_season(rows,s) for s in seasons if s>=2014}
    pooled=[v for v in reports.values() if v.get("status")=="EVALUATED"]
    total_scored=sum(v["scored_n"] for v in pooled)
    total_bets=sum(v["bets"] for v in pooled)
    # weighted headline summaries; ROI pooled exactly cannot be reconstructed
    # from rounded season ROI, so aggregate via an independent full pass is not
    # claimed here.
    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "source_rows":len(rows),
        "seasons":seasons,
        "method":"strict preseason Poisson on regulation goals -> 2-way OT/SO probability; prior-season calibration only",
        "entry":"archived opening moneyline",
        "closing_reference":"archived closing 2-way no-vig moneyline",
        "fixed_min_ev":MIN_EV,
        "release_eligible":False,
        "archive_clv_only":True,
        "evaluated_seasons":len(pooled),
        "scored_games":total_scored,
        "bets":total_bets,
        "season_results":reports,
    }
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=="__main__":
    run()
