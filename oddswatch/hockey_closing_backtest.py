"""Retrospective hockey closing-reference backtest.

Uses independent preseason model probabilities and archived 1X2 closing
references. Closing rows are NOT authenticated executable entry prices and are
therefore never called true CLV or production ROI.
"""
from __future__ import annotations

import csv, json, math
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from .hockey_walkforward import load_history, _outcome, _prob, _metric, _season_number
from .hockey_recalibration import WEIGHTS, _fit, _evaluate, _mix
from .matching import norm

MARKET = Path("data/hockey/market/oddsportal_seed_2026_27.csv")
OUT = Path("data/hockey/closing_reference_backtest.json")
SEASON = "2026/27"
MIN_EV = 0.03
LEAGUE_MAP = {
    "NHL":"nhl","DEL":"del","ICEHL":"icehl","LIIGA":"liiga",
    "CZE_EXTRALIGA":"extraliga","EXTRALIGA":"extraliga",
}

# Audited archive label aliases only. Resolver otherwise requires one exact
# normalized candidate among teams known to the preseason model.
ALIASES = {
    "nhl": {
        "anaheim ducks":"ANA","boston bruins":"BOS","buffalo sabres":"BUF",
        "carolina hurricanes":"CAR","columbus blue jackets":"CBJ","calgary flames":"CGY",
        "chicago blackhawks":"CHI","colorado avalanche":"COL","dallas stars":"DAL",
        "detroit red wings":"DET","edmonton oilers":"EDM","florida panthers":"FLA",
        "los angeles kings":"LAK","minnesota wild":"MIN","montreal canadiens":"MTL",
        "new jersey devils":"NJD","nashville predators":"NSH","new york islanders":"NYI",
        "new york rangers":"NYR","ottawa senators":"OTT","philadelphia flyers":"PHI",
        "pittsburgh penguins":"PIT","seattle kraken":"SEA","san jose sharks":"SJS",
        "st louis blues":"STL","tampa bay lightning":"TBL","toronto maple leafs":"TOR",
        "utah mammoth":"UTA","utah hockey club":"UTA","vancouver canucks":"VAN",
        "vegas golden knights":"VGK","winnipeg jets":"WPG","washington capitals":"WSH",
    },
    "del": {
        "erc ingolstadt":"Ingolstadt","adler mannheim":"Mannheim",
        "iserlohn roosters":"Iserlohn","augsburger panther":"Augsbourg",
        "nurnberg ice tigers":"Nuremberg","nuremberg ice tigers":"Nuremberg",
        "kolner":"Cologne","kolner haie":"Cologne","frankfurt lowen":"Francfort",
        "lowen frankfurt":"Francfort","grizzly wolfsburg":"Wolfsburg",
        "grizzlys wolfsburg":"Wolfsburg","munchen":"Munich","red bull munich":"Munich",
        "eisbaren berlin":"Berlin","bremerhaven":"Bremerhaven",
        "straubing tigers":"Straubing","krefeld pinguine":"Krefeld",
        "schwenninger":"Schwenningen","schwenninger wild wings":"Schwenningen",
    },
    "icehl": {
        "vienna":"Vienne",
        "fehervar av19":"Fehérvár",
        "hk olimpija":"Ljubljana",
        "vorarlberg":"Feldkirch",
        "salzburg":"Salzbourg",
        "black wings linz":"Linz",
        "valpusteria":"Pustertal",
        "milano":"Milano HC",
    },
    "extraliga": {
        "mountfield hk":"Hradec Králové",
    },
    "liiga": {
        "ifk helsinki":"HIFK Helsinki",
        "hameenlinna":"HPK Hämeenlinna",
        "karpat":"Kärpät Oulu",
        "assat":"Ässät Pori",
        "lukko":"Lukko Rauma",
        "ilves":"Ilves Tampere",
        "jyp":"JYP Jyväskylä",
        "kalpa":"KalPa Kuopio",
        "kookoo":"KooKoo Kouvola",
        "saipa":"SaiPa Lappeenranta",
        "pelicans":"Pelicans Lahti",
        "tappara":"Tappara Tampere",
        "sport":"Sport Vaasa",
        "kiekko-espoo":"Kiekko-Espoo",
        "jukurit":"Jukurit Mikkeli",
    },
}

def _market_rows(path=MARKET):
    out=[]
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            lg=LEAGUE_MAP.get((r.get("league") or "").upper())
            if not lg:
                continue
            try:
                odds=[float(r["close_home"]),float(r["close_draw"]),float(r["close_away"])]
                if not all(math.isfinite(x) and x>1 for x in odds):
                    continue
                d=date.fromisoformat(r["date"])
            except (KeyError,TypeError,ValueError):
                continue
            out.append({
                "league":lg,"date":d,"home":r["home_team"].strip(),"away":r["away_team"].strip(),
                "odds":odds,"result":(r.get("reg_result") or "").upper(),
                "source_url":r.get("source_url") or None,
            })
    return out

def _resolve(name:str, league:str, teams:set[str]) -> str|None:
    explicit=ALIASES.get(league,{}).get(norm(name))
    if explicit in teams:
        return explicit
    hits=[t for t in teams if norm(t)==norm(name)]
    return hits[0] if len(hits)==1 else None

def _choose_alpha(rows:list[dict], league:str) -> float|None:
    xs=[r for r in rows if r["league"]==league]
    calibration=[r for r in xs if r["season"]=="2025/26"]
    model,_,base=_fit(xs,2025)
    if model is None or not calibration:
        return None
    scores=[]
    for a in WEIGHTS:
        s=_evaluate(model,base,calibration,a)
        if s["evaluated"]>=80 and s["blended_logloss"] is not None:
            scores.append((a,s["blended_logloss"]))
    return min(scores,key=lambda z:(z[1],abs(z[0]-.5)))[0] if scores else None

def _devig(odds:list[float]) -> list[float]:
    raw=[1/x for x in odds]
    s=sum(raw)
    return [x/s for x in raw]

def run(history_path="data/hockey/history.csv", market_path=MARKET, dest=OUT):
    history=load_history(history_path, as_of=date(2026,10,12))
    market=_market_rows(market_path)
    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "season":SEASON,
        "method":"preseason Poisson + prior-season-selected calibration; archived 1X2 closing reference",
        "fixed_min_ev":MIN_EV,
        "release_eligible":False,
        "true_clv":None,
        "production_roi":None,
        "warning":"Archived closing references are not authenticated executable entry prices.",
        "leagues":{},
    }
    for lg in ("nhl","del","icehl","liiga","extraliga"):
        xs=[r for r in history if r["league"]==lg]
        model,training,base=_fit(xs,2026)
        alpha=_choose_alpha(history,lg)
        rows=[r for r in market if r["league"]==lg]
        report={"archive_rows":len(rows),"training_n":len(training),"alpha":alpha,
                "matched":0,"unmatched":0,"model_logloss":None,"market_logloss":None,
                "logloss_gain_vs_market":None,"bets":0,"wins":0,
                "closing_reference_roi":None,"mean_model_ev_at_close":None}
        if model is None or base is None or alpha is None:
            result["leagues"][lg]=report
            continue
        teams=set(model.attack)
        mll=qll=profit=evsum=0.0
        bets=wins=matched=unmatched=0
        for r in rows:
            h=_resolve(r["home"],lg,teams); a=_resolve(r["away"],lg,teams)
            if not h or not a or h==a:
                unmatched+=1; continue
            p0=_prob(model,{"home":h,"away":a})
            if p0 is None:
                unmatched+=1; continue
            p=_mix(p0,base,alpha)
            q=_devig(r["odds"])
            y={"HOME":0,"DRAW":1,"AWAY":2}.get(r["result"])
            if y is None:
                unmatched+=1; continue
            matched+=1
            mll+=_metric(p,y)[0]; qll+=_metric(q,y)[0]
            evs=[p[i]*r["odds"][i]-1 for i in range(3)]
            side=max(range(3),key=lambda i:evs[i])
            if evs[side] >= MIN_EV:
                bets+=1; evsum+=evs[side]
                if side==y:
                    wins+=1; profit += r["odds"][side]-1
                else:
                    profit -= 1
        report.update({
            "matched":matched,"unmatched":unmatched,
            "model_logloss":round(mll/matched,6) if matched else None,
            "market_logloss":round(qll/matched,6) if matched else None,
            "logloss_gain_vs_market":round((qll-mll)/matched,6) if matched else None,
            "bets":bets,"wins":wins,
            "closing_reference_roi":round(profit/bets,6) if bets else None,
            "mean_model_ev_at_close":round(evsum/bets,6) if bets else None,
        })
        result["leagues"][lg]=report
    Path(dest).parent.mkdir(parents=True,exist_ok=True)
    Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result["leagues"],ensure_ascii=False))
    return result

if __name__=="__main__":
    run()
