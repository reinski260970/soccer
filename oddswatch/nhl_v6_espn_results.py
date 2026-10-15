"""Fetch verified NHL regulation scores and upcoming fixtures from ESPN.

No API key. Fails closed when period scores are missing. Outputs CSV consumed
by nhl_v6_feature_bridge and schedule JSON. Dates are queried month by month.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
ALIASES = {"Utah Hockey Club":"Mammoth","Utah Mammoth":"Mammoth",
           "Arizona Coyotes":"Coyotes","Phoenix Coyotes":"Coyotes",
           "Vegas Golden Knights":"Golden Knights","Columbus Blue Jackets":"Blue Jackets",
           "New York Islanders":"Islanders","New York Rangers":"Rangers",
           "New Jersey Devils":"Devils","Los Angeles Kings":"Kings",
           "St. Louis Blues":"Blues","Tampa Bay Lightning":"Lightning",
           "Toronto Maple Leafs":"Maple Leafs","Detroit Red Wings":"Red Wings",
           "Chicago Blackhawks":"Blackhawks","Seattle Kraken":"Kraken"}
def team_name(competitor):
    team=competitor["team"]
    full=team.get("displayName","")
    return ALIASES.get(full,team.get("name",full))

def fetch(month):
    url=BASE+"?"+urlencode({"dates":month,"limit":250})
    with urlopen(url,timeout=35) as response:
        return json.load(response).get("events",[])

def parse(events, today):
    results, schedule = [], []
    seen=set()
    for event in events:
        eid=str(event.get("id",""))
        if eid in seen: continue
        seen.add(eid)
        comp=(event.get("competitions") or [{}])[0]
        teams=comp.get("competitors",[])
        if len(teams)!=2: continue
        by_side={t.get("homeAway"):t for t in teams}
        if set(by_side)!={"home","away"}: continue
        h,a=by_side["home"],by_side["away"]
        start=datetime.fromisoformat(event["date"].replace("Z","+00:00"))
        day=start.date()
        home,away=team_name(h),team_name(a)
        state=event.get("status",{}).get("type",{})
        completed=state.get("completed") is True
        if completed and day<=today:
            def regulation(t):
                periods=t.get("linescores") or []
                if len(periods)<3: return None
                try:
                    return sum(int(float(periods[i]["value"])) for i in range(3))
                except (KeyError,TypeError,ValueError): return None
            rh,ra=regulation(h),regulation(a)
            if rh is None or ra is None: continue
            try: fh,fa=int(h["score"]),int(a["score"])
            except (ValueError,TypeError,KeyError): continue
            if fh==fa: continue
            results.append({"date":day.isoformat(),"season":day.year if day.month>=7 else day.year-1,
                            "home_team":home,"away_team":away,"reg_home":rh,"reg_away":ra,
                            "final_home":fh,"final_away":fa})
        elif not completed and day>=today:
            schedule.append({"date":day.isoformat(),"home":home,"away":away})
    return results,schedule

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",default="2025-10")
    ap.add_argument("--through",default=date.today().strftime("%Y-%m"))
    ap.add_argument("--results",default="data/hockey/nhl_espn_results.csv")
    ap.add_argument("--schedule",default="data/hockey/nhl_espn_schedule.json")
    args=ap.parse_args()
    start=date.fromisoformat(args.start+"-01")
    end=date.fromisoformat(args.through+"-01")
    today=datetime.now(timezone.utc).date()
    if end<start: raise ValueError("through must be >= start")
    events=[]
    month=start
    while month<=end:
        events.extend(fetch(month.strftime("%Y%m")))
        month=date(month.year+1,1,1) if month.month==12 else date(month.year,month.month+1,1)
    results,schedule=parse(events,today)
    if not results: raise RuntimeError("No verified regulation scores retrieved")
    rp=Path(args.results); rp.parent.mkdir(parents=True,exist_ok=True)
    with rp.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["date","season","home_team","away_team",
                                          "reg_home","reg_away","final_home","final_away"])
        writer.writeheader();writer.writerows(sorted(results,key=lambda r:r["date"]))
    sp=Path(args.schedule);sp.parent.mkdir(parents=True,exist_ok=True)
    sp.write_text(json.dumps(sorted(schedule,key=lambda r:r["date"]),indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"verified_completed_games":len(results),"upcoming_games":len(schedule),
                      "results":str(rp),"schedule":str(sp)}))

if __name__=="__main__": main()
