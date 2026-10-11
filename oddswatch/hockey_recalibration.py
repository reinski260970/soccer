"""Chronologically calibrated hockey regulation model research.

For test season Y: select blend weight ONLY on Y-1, with an earlier-only
model fit before Y-1; then refit on seasons <Y and evaluate Y untouched.
No bookmaker prices are used as features, and no betting strategy is released.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from .hockey_walkforward import LEAGUES, load_history, _outcome, _prob, _metric, _season_number
from .models.poisson import Match, PoissonModel

WEIGHTS=(0.0,0.25,0.5,0.75,1.0)
TEST_SEASONS=("2025/26","2026/27")
DEST=Path("data/hockey/recalibration_research.json")


def _fit(rows: list[dict], cutoff: int):
    as_of=date(cutoff,7,1)
    training=[r for r in rows
              if _season_number(r["season"]) < cutoff and r["date"] < as_of]
    if len(training)<200:
        return None, training, None
    model=PoissonModel.fit(
        [Match(r["date"],r["home"],r["away"],r["home_goals"],r["away_goals"])
         for r in training],
        as_of, half_life_days=365.0, xg_weight=0.0,
        shrink=8.0, rho=0.0, max_goals=12, iterations=90,
    )
    n=Counter(_outcome(r) for r in training)
    base=[(n[k]+1)/(len(training)+3) for k in range(3)]
    return model, training, base


def _mix(p:list[float],base:list[float],alpha:float)->list[float]:
    mixed=[alpha*m+(1-alpha)*b for m,b in zip(p,base)]
    if not math.isclose(sum(mixed),1,abs_tol=1e-6):
        raise ValueError("invalid mixed probabilities")
    return mixed


def _evaluate(model, base, rows, alpha):
    m=b=c=0.0
    scored=skipped=0
    for row in rows:
        p=_prob(model,row)
        if p is None:
            skipped+=1
            continue
        y=_outcome(row)
        m+=_metric(p,y)[0]
        b+=_metric(base,y)[0]
        c+=_metric(_mix(p,base,alpha),y)[0]
        scored+=1
    return {
        "evaluated":scored,"unseen":skipped,
        "poisson_logloss":round(m/scored,6) if scored else None,
        "base_rate_logloss":round(b/scored,6) if scored else None,
        "blended_logloss":round(c/scored,6) if scored else None,
        "gain_vs_raw_poisson":round((m-c)/scored,6) if scored else None,
        "gain_vs_base_rate":round((b-c)/scored,6) if scored else None,
    }


def evaluate(rows, test_seasons=TEST_SEASONS):
    output={
        "method":"Nested prior-season blend-weight calibration; independent 60-minute Poisson + league base rates",
        "weights":list(WEIGHTS),
        "release_eligible":False,
        "validation":"RETROSPECTIVE_RESEARCH_NOT_FRESH_HOLDOUT",
        "leagues":{},
    }
    for lg in LEAGUES:
        league_rows=[r for r in rows if r["league"]==lg]
        reports={}
        for season in test_seasons:
            year=_season_number(season)
            prev_year=year-1
            calibration=[r for r in league_rows
                         if _season_number(r["season"])==prev_year]
            holdout=[r for r in league_rows if r["season"]==season]
            model_prev, before_cal, base_prev=_fit(league_rows,prev_year)
            model_test, before_test, base_test=_fit(league_rows,year)
            if model_prev is None or model_test is None or not holdout:
                reports[season]={"status":"INSUFFICIENT_HISTORY_OR_TEST",
                                 "pre_calibration_n":len(before_cal),
                                 "calibration_n":len(calibration),
                                 "test_n":len(holdout)}
                continue
            # Hyperparameter chosen ONLY from the previous season; never test data.
            losses={a:_evaluate(model_prev,base_prev,calibration,a) for a in WEIGHTS}
            eligible=[(a,stats["blended_logloss"]) for a,stats in losses.items()
                      if stats["evaluated"]>=80 and stats["blended_logloss"] is not None]
            if not eligible:
                reports[season]={"status":"INSUFFICIENT_PAST_CALIBRATION",
                                 "calibration_n":len(calibration),
                                 "test_n":len(holdout)}
                continue
            chosen=min(eligible,key=lambda z:(z[1],abs(z[0]-0.5)))[0]
            tested=_evaluate(model_test,base_test,holdout,chosen)
            reports[season]={
                "status":"EVALUATED_RETROSPECTIVE",
                "training_n":len(before_test),
                "calibration_season":f"{prev_year}/{str(prev_year+1)[-2:]}",
                "calibration_scored":losses[chosen]["evaluated"],
                "selected_model_weight":chosen,
                **tested,
            }
        output["leagues"][lg]=reports
    return output


def run(input_path="data/hockey/history.csv",dest=DEST):
    rows=load_history(input_path,as_of=datetime.now(timezone.utc).date())
    result=evaluate(rows)
    result["run_time"]=datetime.now(timezone.utc).isoformat()
    result["market_logloss"]=None
    result["closing_line_value"]=None
    target=Path(dest)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({lg:{season:{k:r.get(k) for k in (
        "status","selected_model_weight","evaluated","poisson_logloss",
        "blended_logloss","base_rate_logloss","gain_vs_raw_poisson","gain_vs_base_rate")}
        for season,r in reports.items()}
        for lg,reports in result["leagues"].items()},ensure_ascii=False))


if __name__=="__main__":
    run()
