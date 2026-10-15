"""Convert official MoneyPuck all_teams.csv into V6 wide games and completed results.

No bookmaker inputs. Only completed games with both team-level 5on5 and all
rows are emitted; missing required stats are rejected rather than zero-filled.
"""
import argparse
import csv
import io
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

from .nhl_v5_1_forward import download_text, NHL_TO_MP

CODE_TO_SHORT = {
    "ANA":"Ducks","BOS":"Bruins","BUF":"Sabres","CGY":"Flames",
    "CAR":"Hurricanes","CHI":"Blackhawks","COL":"Avalanche",
    "CBJ":"Blue Jackets","DAL":"Stars","DET":"Red Wings",
    "EDM":"Oilers","FLA":"Panthers","L.A":"Kings","MIN":"Wild",
    "MTL":"Canadiens","N.J":"Devils","NSH":"Predators",
    "NYI":"Islanders","NYR":"Rangers","OTT":"Senators",
    "PHI":"Flyers","PIT":"Penguins","S.J":"Sharks","SEA":"Kraken",
    "STL":"St.Louis","T.B":"Lightning","TOR":"Maple Leafs",
    "UTA":"Mammoth","VAN":"Canucks","VGK":"Golden Knights",
    "WPG":"Jets","WSH":"Capitals","ARI":"Coyotes",
}
FIELDS5=("xGoalsFor","xGoalsAgainst","shotsOnGoalFor","shotsOnGoalAgainst",
         "shotAttemptsFor","shotAttemptsAgainst","highDangerxGoalsFor",
         "highDangerxGoalsAgainst")
FIELDS_ALL=("xGoalsFor","xGoalsAgainst","shotsOnGoalFor","shotsOnGoalAgainst",
            "scoreVenueAdjustedxGoalsFor","scoreVenueAdjustedxGoalsAgainst",
            "goalsFor","goalsAgainst")


def convert(text):
    games=defaultdict(dict)
    conflicting=set()
    for row in csv.DictReader(io.StringIO(text)):
        if row.get("position")!="Team Level" or row.get("situation") not in ("5on5","all"):
            continue
        gid=(row.get("gameId") or "").strip()
        team=(row.get("playerTeam") or row.get("team") or "").strip()
        venue=(row.get("home_or_away") or "").upper()
        d=(row.get("gameDate") or "").strip()
        if not gid or team not in CODE_TO_SHORT or venue not in ("HOME","AWAY") or len(d)!=8:
            continue
        key=(gid,venue,row["situation"])
        if key in games[(gid,d)]:
            # Some MoneyPuck team-level exports repeat a team/situation.
            # Accept exact metric duplicates; reject inconsistent records.
            prev=games[(gid,d)][key]
            cols=FIELDS5 if row["situation"]=="5on5" else FIELDS_ALL
            if any(prev.get(c)!=row.get(c) for c in cols):
                conflicting.add((gid,d))
            continue
        games[(gid,d)][key]=row
    wide=[];results=[];rejected=0
    for (gid,d), parts in sorted(games.items(),key=lambda x:x[0][1]):
        if (gid,d) in conflicting:
            rejected+=1
            continue
        try:
            season=int(next(iter(parts.values()))["season"])
            pair={}
            for venue in ("HOME","AWAY"):
                pair[venue]={}
                for sit, fields in (("5on5",FIELDS5),("all",FIELDS_ALL)):
                    candidates=[v for (g,vn,s),v in parts.items() if vn==venue and s==sit]
                    if len(candidates)!=1:
                        raise ValueError("Missing team-level situation")
                    r=candidates[0]
                    vals={k:float(r[k]) for k in fields}
                    if not all(math.isfinite(v) and v>=0 for v in vals.values()):
                        raise ValueError("Non-finite or negative metrics")
                    pair[venue][sit]=(r["playerTeam"],vals)
            hc=pair["HOME"]["all"][0];ac=pair["AWAY"]["all"][0]
            if hc==ac or hc!=pair["HOME"]["5on5"][0] or ac!=pair["AWAY"]["5on5"][0]:
                raise ValueError("Team mismatch")
            home_goals=pair["HOME"]["all"][1]["goalsFor"]
            away_goals=pair["AWAY"]["all"][1]["goalsFor"]
            if home_goals==away_goals or home_goals!=int(home_goals) or away_goals!=int(away_goals):
                raise ValueError("Invalid final score")
            # MoneyPuck all-goals includes OT but not always shootout deciding
            # goal. Avoid fabricating regulation scores from all-goals.
            w={"date":d,"season":season,"home_team":hc,"away_team":ac}
            for venue,prefix in (("HOME","home"),("AWAY","away")):
                for sit,fields in (("5on5",FIELDS5),("all",FIELDS_ALL)):
                    for field in fields:
                        w[f"{prefix}_{sit}_{field}"]=pair[venue][sit][1][field]
            wide.append(w)
            # Regulation goals are unavailable in this bulk format: intentionally
            # do NOT emit a fake regulation-goals archive.
        except (ValueError,KeyError,TypeError):
            rejected+=1
    return wide,{"wide_games":len(wide),"rejected_games":rejected,"conflicting_games":len(conflicting),
                 "results_generated":0,"reason":"regulation_goals_unavailable"}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="data/hockey/market/nhl_moneypuck_games_live.csv")
    args=ap.parse_args()
    rows,report=convert(download_text())
    if not rows: raise RuntimeError("No complete MoneyPuck games")
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps(report))


if __name__=="__main__":
    main()
