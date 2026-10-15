"""Build V6 game features from an up-to-date results and MoneyPuck archive.

The results CSV must have the same SBR column schema as the historic archive;
the MoneyPuck CSV must have the joined game schema used by
nhl_moneypuck_features.load_mp_games. Only games completed before the target
date may be used. Bookmaker columns in the results archive are placeholders
for rolling-feature compatibility and are NEVER fed to V6 features.

Run:
 python -m oddswatch.nhl_v6_feature_bridge --results recent_results.csv \
   --moneypuck recent_mp_games.csv --schedule schedule.json \
   --out data/hockey/nhl_v6_features.json

Schedule JSON: [{"date":"2026-10-15","home":"Maple Leafs","away":"Sabres"}]
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path

from .nhl_bulk_features import build_features
from .nhl_moneypuck_features import (
    SBR_TO_MP, METRICS, PRIORS, _ema, load_mp_games,
)
from .nhl_bulk_v5 import MP_BASE
from .nhl_bulk_v6 import FEATURES, _augment_interactions

DEFENSIVE = {"xga5","soga5","caa5","hdxga5","xgaall","sogaall","svaxga"}


def load_completed_results(path):
    """Results-only input; no bookmaker odds required or consumed."""
    rows = []
    with Path(path).open(encoding="utf-8-sig",newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                d=str(r["date"])
                day=date(int(d[:4]),int(d[4:6]),int(d[6:8])) if len(d)==8 and d.isdigit() else date.fromisoformat(d[:10])
                row={"date":day,"season":int(r["season"]),
                     "home":r["home_team"].strip(),"away":r["away_team"].strip(),
                     "reg_home":int(r["reg_home"]),"reg_away":int(r["reg_away"]),
                     "final_home":int(r["final_home"]),"final_away":int(r["final_away"]),
                     "home_open":2.0,"away_open":2.0,"home_close":2.0,"away_close":2.0}
                if row["home"]!=row["away"] and row["final_home"]!=row["final_away"]:
                    rows.append(row)
            except (KeyError,TypeError,ValueError):
                continue
    return sorted(rows,key=lambda r:(r["date"],r["home"],r["away"]))


def _mp_snapshot(states, home, away):
    h, a = states[home], states[away]
    f = {}
    for k in METRICS:
        f["mp_"+k+"_diff"] = a[k]-h[k] if k in DEFENSIVE else h[k]-a[k]
    def ratio(x, y):
        return x/y if y else 0.0
    f["mp_corsi_share_diff"] = ratio(h["caf5"],h["caf5"]+h["caa5"]) - ratio(a["caf5"],a["caf5"]+a["caa5"])
    f["mp_xg_share_diff"] = ratio(h["xgf5"],h["xgf5"]+h["xga5"]) - ratio(a["xgf5"],a["xgf5"]+a["xga5"])
    f["mp_xg_per_sog_for_diff"] = ratio(h["xgfall"],h["sogfall"])-ratio(a["xgfall"],a["sogfall"])
    f["mp_xg_per_sog_against_diff"] = ratio(a["xgaall"],a["sogaall"])-ratio(h["xgaall"],h["sogaall"])
    f["mp_hd_share_for_diff"] = ratio(h["hdxgf5"],h["xgf5"])-ratio(a["hdxgf5"],a["xgf5"])
    f["mp_hd_share_against_diff"] = ratio(a["hdxga5"],a["xga5"])-ratio(h["hdxga5"],h["xga5"])
    f["mp_non5v5_xgf_diff"] = (h["xgfall"]-h["xgf5"])-(a["xgfall"]-a["xgf5"])
    f["mp_non5v5_xga_diff"] = (a["xgaall"]-a["xga5"])-(h["xgaall"]-h["xga5"])
    return f


def _states_before(mp_games, cutoff, alpha):
    states = {}
    last = {}
    for game in mp_games:
        if game["date"] >= cutoff:
            break
        for code, vals in ((game["home_code"],game["home_stats"]), (game["away_code"],game["away_stats"])):
            state = states.setdefault(code, dict(PRIORS))
            for k in METRICS:
                state[k] = _ema(state[k], float(vals[k]), alpha)
            last[code] = game["date"]
    return states, last


def build(targets, results_path, mp_path, max_age_days=7):
    results = load_completed_results(results_path)
    mp_games = load_mp_games(Path(mp_path))
    if not results or not mp_games:
        raise ValueError("Empty results or MoneyPuck history")
    out = []
    for target in targets:
        day = date.fromisoformat(str(target["date"])[:10])
        home, away = target["home"], target["away"]
        hc, ac = SBR_TO_MP.get(home), SBR_TO_MP.get(away)
        if not hc or not ac:
            raise ValueError(f"Unknown team alias: {home} / {away}")
        prior = [r for r in results if r["date"] < day]
        if not prior:
            raise ValueError("No completed prior results")
        # A single synthetic future fixture obtains the exact existing Elo,
        # rest and venue rolling state. It is never used as training evidence.
        sentinel = dict(prior[-1], season=day.year if day.month>=7 else day.year-1,
                        date=day, home=home, away=away, reg_home=0,
                        reg_away=0, final_home=1, final_away=0)
        base = build_features(prior+[sentinel], alpha=.10, elo_k=18.0, season_retain=1.0)[-1]
        q = dict(base)
        dates = []
        for prefix, alpha in (("slow",.05),("fast",.18)):
            states, last = _states_before(mp_games, day, alpha)
            if hc not in states or ac not in states:
                raise ValueError(f"No MoneyPuck observations: {home} / {away}")
            dates.extend([last[hc],last[ac]])
            snapshot = _mp_snapshot(states,hc,ac)
            for key in MP_BASE:
                q[prefix+"_"+key] = snapshot[key]
        # Require each team to have both recent results and MoneyPuck.
        for code in (hc,ac):
            last_mp = max(g["date"] for g in mp_games if g["date"]<day and code in (g["home_code"],g["away_code"]))
            if (day-last_mp).days > max_age_days:
                raise ValueError(f"Stale MoneyPuck: {code}, {last_mp}")
        for team in (home,away):
            team_last = max((r["date"] for r in prior if team in (r["home"],r["away"])),default=None)
            if team_last is None or (day-team_last).days>max_age_days:
                raise ValueError(f"Stale results: {team}")
        q = _augment_interactions(q)
        missing = [k for k in FEATURES if k not in q]
        if missing:
            raise ValueError(f"Missing V6 features: {missing}")
        out.append({"date":day.isoformat(),"home":home,"away":away,
                    "data_through":max(dates).isoformat(),
                    **{k:float(q[k]) for k in FEATURES}})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results",required=True)
    ap.add_argument("--moneypuck",required=True)
    ap.add_argument("--schedule",required=True)
    ap.add_argument("--out",default="data/hockey/nhl_v6_features.json")
    ap.add_argument("--max-age-days",type=int,default=7)
    args = ap.parse_args()
    targets=json.loads(Path(args.schedule).read_text(encoding="utf-8"))
    features=build(targets,args.results,args.moneypuck,args.max_age_days)
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(features,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"games":len(features),"features":len(FEATURES),"out":str(dest)}))


if __name__=="__main__":
    main()
