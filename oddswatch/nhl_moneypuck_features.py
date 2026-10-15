"""Leakage-safe MoneyPuck rolling team features joined to SBR odds games."""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

MP_PATH=Path("data/hockey/market/nhl_moneypuck_games_2011_2021.csv")

SBR_TO_MP={
    "Avalanche":"COL","Blackhawks":"CHI","Blue Jackets":"CBJ","Bruins":"BOS",
    "Canadiens":"MTL","Canucks":"VAN","Capitals":"WSH","Coyotes":"ARI",
    "Arizonas":"ARI","Devils":"N.J","Ducks":"ANA","Flames":"CGY","Flyers":"PHI",
    "Golden Knights":"VGK","Hurricanes":"CAR","Islanders":"NYI","NY Islanders":"NYI",
    "Jets":"WPG","WinnipegJets":"WPG","Kings":"L.A","Kraken":"SEA",
    "SeattleKraken":"SEA","Lightning":"T.B","Tampa":"T.B","Tampa Bay":"T.B",
    "Maple Leafs":"TOR","Oilers":"EDM","Panthers":"FLA","Penguins":"PIT",
    "Phoenix":"ARI","Predators":"NSH","Rangers":"NYR","Red Wings":"DET",
    "Sabres":"BUF","Senators":"OTT","Sharks":"S.J","St.Louis":"STL",
    "Stars":"DAL","Wild":"MIN","Mammoth":"UTA","Blues":"STL",
}

METRICS=(
    "xgf5","xga5","sogf5","soga5","caf5","caa5","hdxgf5","hdxga5",
    "xgfall","xgaall","sogfall","sogaall","svaxgf","svaxga",
)
PRIORS={
    "xgf5":1.8,"xga5":1.8,"sogf5":25.0,"soga5":25.0,
    "caf5":50.0,"caa5":50.0,"hdxgf5":0.7,"hdxga5":0.7,
    "xgfall":2.8,"xgaall":2.8,"sogfall":30.0,"sogaall":30.0,
    "svaxgf":2.8,"svaxga":2.8,
}


@dataclass
class MPState:
    values: dict
    last_date: date|None=None


def _new_state():
    return MPState(dict(PRIORS))


def _ema(old,v,a):
    return a*v+(1-a)*old


def _float(r,k,default=0.0):
    try: return float(r.get(k,""))
    except (TypeError,ValueError): return default


def load_mp_games(path=MP_PATH):
    out=[]
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            d=str(r["date"])
            try:
                day=date(int(d[:4]),int(d[4:6]),int(d[6:8]))
            except Exception:
                continue
            out.append({
                "season":int(r["season"]),"date":day,
                "home_code":r["home_team"],"away_code":r["away_team"],
                "home_stats":{
                    "xgf5":_float(r,"home_5on5_xGoalsFor"),
                    "xga5":_float(r,"home_5on5_xGoalsAgainst"),
                    "sogf5":_float(r,"home_5on5_shotsOnGoalFor"),
                    "soga5":_float(r,"home_5on5_shotsOnGoalAgainst"),
                    "caf5":_float(r,"home_5on5_shotAttemptsFor"),
                    "caa5":_float(r,"home_5on5_shotAttemptsAgainst"),
                    "hdxgf5":_float(r,"home_5on5_highDangerxGoalsFor"),
                    "hdxga5":_float(r,"home_5on5_highDangerxGoalsAgainst"),
                    "xgfall":_float(r,"home_all_xGoalsFor"),
                    "xgaall":_float(r,"home_all_xGoalsAgainst"),
                    "sogfall":_float(r,"home_all_shotsOnGoalFor"),
                    "sogaall":_float(r,"home_all_shotsOnGoalAgainst"),
                    "svaxgf":_float(r,"home_all_scoreVenueAdjustedxGoalsFor"),
                    "svaxga":_float(r,"home_all_scoreVenueAdjustedxGoalsAgainst"),
                },
                "away_stats":{
                    "xgf5":_float(r,"away_5on5_xGoalsFor"),
                    "xga5":_float(r,"away_5on5_xGoalsAgainst"),
                    "sogf5":_float(r,"away_5on5_shotsOnGoalFor"),
                    "soga5":_float(r,"away_5on5_shotsOnGoalAgainst"),
                    "caf5":_float(r,"away_5on5_shotAttemptsFor"),
                    "caa5":_float(r,"away_5on5_shotAttemptsAgainst"),
                    "hdxgf5":_float(r,"away_5on5_highDangerxGoalsFor"),
                    "hdxga5":_float(r,"away_5on5_highDangerxGoalsAgainst"),
                    "xgfall":_float(r,"away_all_xGoalsFor"),
                    "xgaall":_float(r,"away_all_xGoalsAgainst"),
                    "sogfall":_float(r,"away_all_shotsOnGoalFor"),
                    "sogaall":_float(r,"away_all_shotsOnGoalAgainst"),
                    "svaxgf":_float(r,"away_all_scoreVenueAdjustedxGoalsFor"),
                    "svaxga":_float(r,"away_all_scoreVenueAdjustedxGoalsAgainst"),
                },
            })
    return sorted(out,key=lambda x:(x["date"],x["home_code"],x["away_code"]))


def build_mp_pregame(path=MP_PATH,alpha=.10):
    states=defaultdict(_new_state)
    snapshots={}
    for g in load_mp_games(path):
        h,a=states[g["home_code"]],states[g["away_code"]]
        feat={}
        for k in METRICS:
            # Defensive against feature is inverted so positive generally favors home.
            if k in {"xga5","soga5","caa5","hdxga5","xgaall","sogaall","svaxga"}:
                feat[f"mp_{k}_diff"]=a.values[k]-h.values[k]
            else:
                feat[f"mp_{k}_diff"]=h.values[k]-a.values[k]
        hshare=h.values["caf5"]/(h.values["caf5"]+h.values["caa5"]) if h.values["caf5"]+h.values["caa5"] else .5
        ashare=a.values["caf5"]/(a.values["caf5"]+a.values["caa5"]) if a.values["caf5"]+a.values["caa5"] else .5
        feat["mp_corsi_share_diff"]=hshare-ashare
        hx=h.values["xgf5"]/(h.values["xgf5"]+h.values["xga5"]) if h.values["xgf5"]+h.values["xga5"] else .5
        ax=a.values["xgf5"]/(a.values["xgf5"]+a.values["xga5"]) if a.values["xgf5"]+a.values["xga5"] else .5
        feat["mp_xg_share_diff"]=hx-ax
        # Derived shot-quality and non-5v5 proxies, all from prior state.
        hq=h.values["xgfall"]/h.values["sogfall"] if h.values["sogfall"] else 0.0
        aq=a.values["xgfall"]/a.values["sogfall"] if a.values["sogfall"] else 0.0
        feat["mp_xg_per_sog_for_diff"]=hq-aq
        hqa=h.values["xgaall"]/h.values["sogaall"] if h.values["sogaall"] else 0.0
        aqa=a.values["xgaall"]/a.values["sogaall"] if a.values["sogaall"] else 0.0
        feat["mp_xg_per_sog_against_diff"]=aqa-hqa
        hhd=h.values["hdxgf5"]/h.values["xgf5"] if h.values["xgf5"] else 0.0
        ahd=a.values["hdxgf5"]/a.values["xgf5"] if a.values["xgf5"] else 0.0
        feat["mp_hd_share_for_diff"]=hhd-ahd
        hhda=h.values["hdxga5"]/h.values["xga5"] if h.values["xga5"] else 0.0
        ahda=a.values["hdxga5"]/a.values["xga5"] if a.values["xga5"] else 0.0
        feat["mp_hd_share_against_diff"]=ahda-hhda
        feat["mp_non5v5_xgf_diff"]=(h.values["xgfall"]-h.values["xgf5"])-(a.values["xgfall"]-a.values["xgf5"])
        feat["mp_non5v5_xga_diff"]=(a.values["xgaall"]-a.values["xga5"])-(h.values["xgaall"]-h.values["xga5"])
        snapshots[(g["date"],g["home_code"],g["away_code"])]=feat

        # Only now ingest current-game performance.
        for state,vals in ((h,g["home_stats"]),(a,g["away_stats"])):
            for k in METRICS:
                state.values[k]=_ema(state.values[k],float(vals[k]),alpha)
            state.last_date=g["date"]
    return snapshots


def augment_sbr_rows(sbr_rows, path=MP_PATH, alpha=.10):
    pre=build_mp_pregame(path,alpha)
    out=[]; unmatched=[]
    for r in sbr_rows:
        hc=SBR_TO_MP.get(r["home"]); ac=SBR_TO_MP.get(r["away"])
        if not hc or not ac:
            unmatched.append((r["date"],r["home"],r["away"],"alias"))
            continue
        snap=pre.get((r["date"],hc,ac))
        if snap is None:
            # Date conventions can differ around late-night games. Accept only
            # a unique exact team-pair match one calendar day either side.
            candidates=[
                pre[k] for k in (
                    (r["date"]-timedelta(days=1),hc,ac),
                    (r["date"]+timedelta(days=1),hc,ac),
                ) if k in pre
            ]
            if len(candidates)==1:
                snap=candidates[0]
            else:
                unmatched.append((r["date"],r["home"],r["away"],"game"))
                continue
        q=dict(r); q.update(snap); out.append(q)
    return out,unmatched
