"""Forward/shadow inference for M17.19 on truly new EPL/Primeira fixtures.

Model inputs stay independent from bookmaker prices.
Current-season state is extended with free public football sources:
- EPL xG: Understat match xG (primary), football-data results/shots/SOT.
- Primeira xG: football-data HxG/AxG when present, otherwise frozen M14
  shots/SOT/corners xG proxy.
- MatchPulse/OddAlerts/SoccerSTATS are audit/cross-check context only.
Market odds are attached only after fair probabilities are computed.
"""
from __future__ import annotations

import csv
import io
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import bookmaker, fetch, matching, soccer_steam, sql_store
from .m12_research import _season_start
from .m13_research import _resolve_understat
from .m14_research import proxy_xg
from .m17_1_research import _calibrate
from .m17_5_research import _fit_predict
from .m17_18_hgb_research import _fit_raw, build_data, load_one
from .m17_19_ensemble_research import _blend
from .models.poisson import Match
from .scan import Fixture
from .sources import espn, football_data, oddalerts, soccerstats, understat, xg_external

TZ = ZoneInfo("Europe/Vienna")
VALIDATION = Path("data/m17_19_ensemble_validation.json")
PROXY_VALIDATION = Path("data/m17_6_validation.json")
SCOPE = {
    "epl": ("Premier League", "E0"),
    "primeira": ("Primeira Liga", "P1"),
}

def _validation():
    return json.loads(VALIDATION.read_text(encoding="utf-8"))

def _frozen_proxy():
    data=json.loads(PROXY_VALIDATION.read_text(encoding="utf-8"))
    proxy=data.get("_proxy") or {}
    if not proxy.get("beta") or not proxy.get("n"):
        raise RuntimeError("frozen M17 proxy missing")
    return proxy

def _season_year(d: date) -> int:
    return d.year if d.month >= 7 else d.year - 1

def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _current_csv(code: str, season: int):
    text, err = fetch.get(football_data.csv_url(code, season), cache_days=0.05)
    if not text:
        return [], {}, err or f"football-data {code}/{season}: no data"
    parsed, _ = football_data.parse(text, shots_as_xg=False)
    stats = {}
    for row in csv.DictReader(io.StringIO(text.lstrip("\ufeff"))):
        if not row.get("HomeTeam") or not row.get("Date"):
            continue
        try:
            d = football_data._d(row["Date"])
        except Exception:
            continue
        vals = {k:_num(row.get(k)) for k in ("HS","AS","HST","AST","HC","AC","HxG","AxG")}
        stats[(d,row["HomeTeam"],row["AwayTeam"])] = vals
    return parsed, stats, None

def _map_name(name: str, known: list[str]) -> str:
    return matching.find(name, known) or name

def _merge_current(history, hist_shots, code: str, proxy: dict, season: int):
    cur, raw, err = _current_csv(code, season)
    if err:
        return list(history), dict(hist_shots), [], [err]

    us = []
    issues = []
    if code in understat.LEAGUES:
        us, uerr = understat.season_matches(code, season, cache_days=0.05)
        if uerr:
            issues.append(uerr)

    known = sorted({m.home for m in history} | {m.away for m in history})
    out = list(history)
    shots = dict(hist_shots)
    added = []

    existing={(m.date,matching.norm(m.home),matching.norm(m.away)) for m in history}
    for m in cur:
        if _season_start(m.date) != season:
            continue
        h=_map_name(m.home,known); a=_map_name(m.away,known)
        key=(m.date,matching.norm(h),matching.norm(a))
        if key in existing:
            continue
        st=raw.get((m.date,m.home,m.away),{})
        hs,ass,hst,ast=[st.get(k) for k in ("HS","AS","HST","AST")]
        if any(v is None for v in (hs,ass,hst,ast)):
            continue

        hx,ax=m.home_xg,m.away_xg
        source="football-data-hxg"
        if code in understat.LEAGUES and us:
            u,kind=_resolve_understat(m.date,m.home,m.away,m.home_goals,m.away_goals,us)
            if u is not None:
                hx,ax=float(u.home_xg),float(u.away_xg)
                source=f"understat/{kind}"
        if hx is None or ax is None:
            hx=proxy_xg(proxy,hs,hst,st.get("HC"),True)
            ax=proxy_xg(proxy,ass,ast,st.get("AC"),False)
            source="m14-shot-proxy"
        if hx is None or ax is None:
            continue

        nm=Match(m.date,h,a,float(m.home_goals),float(m.away_goals),float(hx),float(ax))
        out.append(nm)
        shots[(season,h,a)]=(float(hs),float(ass),float(hst),float(ast))
        added.append({"date":m.date.isoformat(),"home":h,"away":a,"xg_source":source})
        existing.add(key)
        if h not in known: known.append(h)
        if a not in known: known.append(a)

    out.sort(key=lambda m:m.date)
    return out, shots, added, issues

def _target_row(matches, shots, home: str, away: str, kickoff: date):
    season=_season_start(kickoff)
    target=Match(kickoff,home,away,0.0,0.0,None,None)
    mm=list(matches)+[target]
    ss=dict(shots)
    ss[(season,home,away)]=(0.0,0.0,0.0,0.0)
    # Neutral pseudo prices are a row-emission key only. They never enter x.
    rr=[(season,kickoff,home,away,0,0,[3.0,3.0,3.0],[3.0,3.0,3.0])]
    data,_,_=build_data(mm,rr,ss)
    rows=[r for r in data if r["date"]==kickoff and r["home"]==home and r["away"]==away]
    return rows[-1] if rows else None

def _training_rows(matches, shots):
    # Generate labels for every completed match that has a valid shot row.
    rr=[]
    for m in matches:
        s=_season_start(m.date)
        if (s,m.home,m.away) not in shots:
            continue
        rr.append((s,m.date,m.home,m.away,int(m.home_goals),int(m.away_goals),
                   [3.0,3.0,3.0],[3.0,3.0,3.0]))
    data,_,_=build_data(matches,rr,shots)
    return data

def _predict(data, target, cfg):
    train=[r for r in data if r["date"] < target["date"]]
    if len(train) < 500:
        raise ValueError(f"too little forward training data: {len(train)}")
    bh=cfg["base_hyper"]; hh=cfg["hgb_hyper"]; a=float(cfg["blend"]["hgb_weight"])
    pb=_fit_predict(train,[target],bh["l2"],bh["calib"])[0]
    raw=_fit_raw(train,[target],hh["params"])[0]
    ph=_calibrate(raw,hh["calib"])
    pe=_blend(pb,ph,a)
    gap=max(abs(x-y) for x,y in zip(pb,ph))
    return pb,ph,pe,gap

def _crosscheck(code: str, now: datetime):
    notes=[]
    rows,err=xg_external.snapshot(code,now)
    if rows:
        xg_external.persist_snapshot(code,rows,now)
        notes.append(f"xG primary/current: {rows[0].source}, teams={len(rows)}")
    elif err:
        notes.append(f"xG current unavailable: {err}")
    oa,oerr=oddalerts.team_xg(code)
    if oa:
        notes.append(f"OddAlerts crosscheck teams={len(oa)}")
    elif oerr:
        notes.append(f"OddAlerts: {oerr}")
    venue,verr=soccerstats.team_homeaway(code,cache_days=0.10)
    if venue:
        notes.append(f"SoccerSTATS H/A teams={len(venue)}")
    elif verr:
        notes.append(f"SoccerSTATS: {verr}")
    return notes

def build(start: date | None=None, days: int=7):
    now=datetime.now(timezone.utc)
    start=start or now.astimezone(TZ).date()
    season=_season_year(start)
    proxy=_frozen_proxy()
    val=_validation()
    fixtures=[]
    issues=[]
    notes=[]

    for league,(label,code) in SCOPE.items():
        cfg=(val.get("leagues") or {}).get(league) or {}
        if not cfg.get("blend") or not cfg.get("base_hyper") or not cfg.get("hgb_hyper"):
            issues.append(f"{label}: M17.19 config missing")
            continue

        hist,_,hist_shots,_=load_one(league,code,proxy)
        matches,shots,added,errs=_merge_current(hist,hist_shots,code,proxy,season)
        issues += [f"{label}: {e}" for e in errs]
        notes += [f"{label}: current completed rows={len(added)}"] + [
            f"{label}: {x}" for x in _crosscheck(code,now)
        ]
        train=_training_rows(matches,shots)
        teams=sorted({m.home for m in matches}|{m.away for m in matches})

        games,gerrs=espn.upcoming(league,start,days)
        issues += [f"{label}: {e}" for e in gerrs]
        for g in games:
            if g.status != "STATUS_SCHEDULED" or g.kickoff <= now:
                continue
            h=_map_name(g.home.name,teams); a=_map_name(g.away.name,teams)
            target=_target_row(matches,shots,h,a,g.kickoff.date())
            if target is None:
                issues.append(f"{label}: no leakage-safe target vector {g.title}")
                continue
            try:
                pb,ph,pe,gap=_predict(train,target,cfg)
            except Exception as exc:
                issues.append(f"{label}: {g.title}: {type(exc).__name__}: {exc}")
                continue
            probs=dict(zip(("home","draw","away"),pe))
            flags={s:["M17.19 forward SHADOW – keine PLAY-Freigabe"] for s in probs}
            detail=(
                f"M17.19 forward ensemble HGBw={cfg['blend']['hgb_weight']:.2f}; "
                f"base={pb[0]:.4f}/{pb[1]:.4f}/{pb[2]:.4f}; "
                f"hgb={ph[0]:.4f}/{ph[1]:.4f}/{ph[2]:.4f}; "
                f"gap={gap:.4f}"
            )
            fixtures.append(Fixture(
                league,"soccer",g,probs,detail,
                context=[f"current season={season}",f"free xG/stats only"],
                flags=flags,estimate=True,model="m17.19-forward-shadow",
            ))

    bookmaker.attach_prices(fixtures,issues)
    steam=soccer_steam.assess(fixtures,now=now)
    sql_store.sync_scan(fixtures,[])

    lines=[
        f"⚽ M17.19 FORWARD SHADOW · {now.astimezone(TZ):%d.%m.%Y %H:%M}",
        f"{len(fixtures)} fixtures · EPL + Primeira · 0 PLAY",
        "Fair model first → market second → Steam/CLV tracked separately",
    ]
    for fx in fixtures[:40]:
        lines.append(
            f"{fx.league} · {fx.game.title} · "
            f"H {fx.probs['home']:.3f} X {fx.probs['draw']:.3f} A {fx.probs['away']:.3f}"
        )
    if notes:
        lines += ["","DATA"]+[f"• {x}" for x in notes[:20]]
    if issues:
        lines += ["",f"WARNINGS {len(issues)}"]+[f"• {x}" for x in issues[:20]]
    return "\n".join(lines)+"\n",fixtures,steam,notes,issues

def run():
    text,*_=build()
    print(text)
    return 0

if __name__=="__main__":
    raise SystemExit(run())
