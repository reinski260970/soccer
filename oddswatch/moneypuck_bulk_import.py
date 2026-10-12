"""One-shot MoneyPuck NHL team game bulk importer.

MoneyPuck explicitly publishes this CSV as a bulk download. This module performs
one bulk download, keeps team-level rows for situations all/5on5, and writes a
compact game-level CSV. No page scraping.
"""
from __future__ import annotations

import csv, io, json
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_URL="https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
DEST=Path("data/hockey/market/nhl_moneypuck_games_2011_2021.csv")
PROVENANCE=Path("data/hockey/market/nhl_moneypuck_games_2011_2021.provenance.json")
KEEP_SEASONS=set(range(2011,2022))
SITUATIONS={"all","5on5"}

METRICS=(
    "xGoalsFor","xGoalsAgainst","shotsOnGoalFor","shotsOnGoalAgainst",
    "shotAttemptsFor","shotAttemptsAgainst",
    "highDangerxGoalsFor","highDangerxGoalsAgainst",
    "scoreVenueAdjustedxGoalsFor","scoreVenueAdjustedxGoalsAgainst",
)

FIELDS=["season","date","game_id","home_team","away_team"]
for sit in ("all","5on5"):
    for side in ("home","away"):
        for m in METRICS:
            FIELDS.append(f"{side}_{sit}_{m}")


def _f(v):
    try:
        return float(v)
    except (TypeError,ValueError):
        return None


def download_text()->str:
    req=Request(SOURCE_URL,headers={"User-Agent":"oddswatch-research/1.0"})
    with urlopen(req,timeout=120) as r:
        return r.read().decode("utf-8-sig","replace")


def normalize(text:str):
    reader=csv.DictReader(io.StringIO(text))
    games={}
    rows=0
    for r in reader:
        try:
            season=int(r.get("season") or -1)
        except ValueError:
            continue
        if season not in KEEP_SEASONS or r.get("situation") not in SITUATIONS:
            continue
        if r.get("position") != "Team Level":
            continue
        gid=(r.get("gameId") or "").strip()
        day=(r.get("gameDate") or "").strip()
        hoa=(r.get("home_or_away") or "").strip().upper()
        team=(r.get("playerTeam") or r.get("team") or "").strip()
        opp=(r.get("opposingTeam") or "").strip()
        if not gid or len(day)!=8 or hoa not in {"HOME","AWAY"} or not team or not opp:
            continue
        rows+=1
        g=games.setdefault(gid,{"season":season,"date":day,"game_id":gid})
        side="home" if hoa=="HOME" else "away"
        if side=="home":
            g["home_team"]=team; g["away_team"]=opp
        else:
            g["away_team"]=team; g["home_team"]=opp
        sit=r["situation"]
        for m in METRICS:
            v=_f(r.get(m))
            if v is not None:
                g[f"{side}_{sit}_{m}"]=v

    out=[]
    required={
        "home_5on5_xGoalsFor","away_5on5_xGoalsFor",
        "home_all_xGoalsFor","away_all_xGoalsFor",
        "home_5on5_shotsOnGoalFor","away_5on5_shotsOnGoalFor",
    }
    for g in games.values():
        if not g.get("home_team") or not g.get("away_team"):
            continue
        if not required.issubset(g):
            continue
        out.append(g)
    out.sort(key=lambda x:(x["date"],x["game_id"]))
    return out,{"source_team_situation_rows":rows,"games":len(out)}


def run(dest:Path=DEST):
    text=download_text()
    out,stats=normalize(text)
    if len(out)<10000:
        raise RuntimeError(f"MoneyPuck normalized game set unexpectedly small: {len(out)}")
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore")
        w.writeheader(); w.writerows(out)
    prov={
        "source":"MoneyPuck.com official bulk download",
        "source_url":SOURCE_URL,
        "usage":"non-commercial research",
        "download_mode":"single published bulk CSV; no scraping",
        "season_from":2011,"season_to":2021,
        **stats,
    }
    PROVENANCE.write_text(json.dumps(prov,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(prov))
    return prov


if __name__=="__main__":
    run()
