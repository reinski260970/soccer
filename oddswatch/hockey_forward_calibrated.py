"""Forward SHADOW for a chronologically calibrated hockey moneyline candidate.

Prices are NOT model inputs. No bet/PLAY/Telegram. The research 60-minute
class probabilities are converted to a 2-way INCLUDING_OT estimate, which is
explicitly unvalidated and must be evaluated against actual NHL/EU results.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import hockey_recalibration as calibrate
from .hockey_walkforward import LEAGUES, _canonical, _season_number, load_history
from .models.poisson import hockey_regulation_to_moneyline
from .sources.hockeyarchives import canonical_icehl
from .sql.hockey_settlement import _hockeyarchives_team
from .sql.store import connect, ingest


def _season_start(t):
    return t.year if t.month>=7 else t.year-1


def _normal_name(league, name):
    if league=="icehl":
        name=canonical_icehl(name)
    return _canonical(league,_hockeyarchives_team(name,league))


def _best_preseason_weight(league_rows, season):
    prev_model, before_prev, prev_base=calibrate._fit(league_rows,season-1)
    if prev_model is None:
        return None,0
    prior_label=f"{season-1}/{str(season)[-2:]}"
    cal=[r for r in league_rows if r["season"]==prior_label]
    scored=[(w,calibrate._evaluate(prev_model,prev_base,cal,w))
            for w in calibrate.WEIGHTS]
    valid=[(w,stats["blended_logloss"],stats["evaluated"])
           for w,stats in scored
           if stats["evaluated"]>=80 and stats["blended_logloss"] is not None]
    if not valid:
        return None,0
    weight,_,n=min(valid,key=lambda x:(x[1],abs(x[0]-0.5)))
    return weight,n


def build_bundle(events, history, now):
    """Pure candidate build; only season-frozen earlier-history features."""
    rows_by_league={lg:[r for r in history if r["league"]==lg] for lg in LEAGUES}
    models=[]
    predictions=[]
    issues=[]
    cache={}
    for e in events:
        league=e["league"]
        kick=e["kickoff"]
        if league not in LEAGUES or e["season_type"]!="regular" or not now<kick<=now+timedelta(days=3):
            continue
        year=_season_start(kick)
        key=(league,year)
        if key not in cache:
            lgrows=rows_by_league[league]
            weight,cal_n=_best_preseason_weight(lgrows,year)
            model,train,base=calibrate._fit(lgrows,year)
            if model is None or weight is None:
                cache[key]=None
                issues.append({"league":league,"reason":"NO_PAST_SEASON_CALIBRATION"})
                continue
            model_id=f"hockey-chronocal-v1:{league}:{year}"
            models.append({
                "model_id":model_id,"league":league,
                "trained_through":datetime(year,7,1,tzinfo=timezone.utc)-timedelta(seconds=1),
                "created_at":now,
                "method":"frozen-60minute-poisson-prior-blend-OT-estimate",
                "parameters":{"weight_poisson":weight,"training_games":len(train),
                              "calibration_games":cal_n,
                              "price_used_as_model_feature":False,
                              "ot_conversion_unvalidated":True},
                "validation":{"status":"SHADOW",
                              "release_reason":"no forward OOS 2-way CLV; 60-min to OT conversion not calibrated"},
                "approved":False,
            })
            cache[key]=(model,base,weight,model_id,len(train),cal_n)
        fitted=cache[key]
        if fitted is None:
            continue
        model,base,weight,model_id,train_n,cal_n=fitted
        home=_normal_name(league,e["home_name"])
        away=_normal_name(league,e["away_name"])
        try:
            r=model.markets(home,away)
            p3=calibrate._mix([r["1"],r["X"],r["2"]],base,weight)
            ph,pa=hockey_regulation_to_moneyline(*p3)
        except (KeyError,ValueError,OverflowError,ZeroDivisionError):
            issues.append({"league":league,"event_id":e["event_id"],
                           "reason":"UNMATCHED_TEAM_OR_INVALID_PROBABILITY"})
            continue
        if not 0<ph<1 or not 0<pa<1 or abs((ph+pa)-1)>1e-8:
            issues.append({"league":league,"event_id":e["event_id"],
                           "reason":"INVALID_TWO_WAY_PROBABILITY"})
            continue
        for side,p in (("HOME",ph),("AWAY",pa)):
            digest=hashlib.sha256(f'{e["event_id"]}|{model_id}|{now.isoformat()}|{side}'.encode()).hexdigest()
            predictions.append({
                "prediction_id":"chronocal:"+digest,
                "event_id":e["event_id"],"model_id":model_id,"as_of":now,
                "market":"moneyline","selection":side,"line":0,
                "period":"FULL_GAME","settlement_rules":"INCLUDING_OT",
                "probability":p,"quality":"LOW",
                "features":{"estimated":True,"forward_research_only":True,
                            "regulation_home":p3[0],"regulation_draw":p3[1],
                            "regulation_away":p3[2],
                            "calibration_weight":weight,"calibration_n":cal_n,
                            "training_n":train_n,"ot_conversion_unvalidated":True},
            })
    return {"model_versions":models,"predictions":predictions},issues


def run(now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    history=load_history(as_of=now.date())
    with connect() as conn:
        rows=conn.execute(
            "SELECT event_id,league,home_name,away_name,kickoff,season_type "
            "FROM sports.events WHERE league IN ('nhl','del','icehl','liiga','extraliga') "
            "AND status='STATUS_SCHEDULED' AND season_type='regular' "
            "AND kickoff>%s AND kickoff<=%s ORDER BY kickoff",
            (now,now+timedelta(days=3)),
        ).fetchall()
        bundle,issues=build_bundle(rows,history,now)
        counts=ingest(conn,bundle) if bundle["predictions"] else {"predictions":0,"model_versions":0}
    result={
        "at":now.isoformat(),"candidate_model":"hockey-chronocal-v1",
        "forward_events":len(rows),
        "prediction_rows_proposed":len(bundle["predictions"]),
        "persisted":counts,
        "issues":issues,
        "release_eligible":False,
        "signals_created":0,"stakes_placed":0,
    }
    print(json.dumps(result,ensure_ascii=False,default=str))
    return result


if __name__=="__main__":
    run()
