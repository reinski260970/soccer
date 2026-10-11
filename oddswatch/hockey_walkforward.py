"""Leakage-safe hockey regulation (60-minute) model diagnostics.

Offline historical research only: neither Valuebets nor Telegram nor a model
release. The dataset has 60-minute results but no uniformly paired closing
odds, so scores are compared to a LEAGUE BASE RATE, never called 'market edge'.

Each evaluation season's model is fitted exclusively on earlier seasons.
A current season is a provisional forward diagnostic, not a release holdout.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from .models.poisson import Match, PoissonModel

INPUT = Path("data/hockey/history.csv")
OUTPUT = Path("data/hockey/walkforward_validation.json")
LEAGUES = ("nhl", "del", "icehl", "liiga", "extraliga")
TEST_SEASONS = ("2024/25", "2025/26", "2026/27")


def load_history(path=INPUT, as_of: date | None = None) -> list[dict]:
    as_of = as_of or date.today()
    rows, seen = [], set()
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            try:
                league, season = raw["league"], raw["season"]
                day = date.fromisoformat(raw["date"])
                home, away = raw["home_team"].strip(), raw["away_team"].strip()
                hg, ag = int(raw["reg_home"]), int(raw["reg_away"])
            except (KeyError, TypeError, ValueError):
                continue
            if league not in LEAGUES or day >= as_of or hg < 0 or ag < 0 or not home or not away or home == away:
                continue
            if raw.get("extra", "") not in ("", "OT", "SO"):
                continue
            if not season.endswith(("/23", "/24", "/25", "/26", "/27")):
                continue
            key = (league, day, home, away)
            if key in seen:  # never count a duplicate as another scored match
                continue
            seen.add(key)
            rows.append(dict(league=league, season=season, date=day,
                             home=home, away=away, home_goals=hg, away_goals=ag))
    return sorted(rows, key=lambda x: (x["date"], x["league"], x["home"], x["away"]))


def _outcome(row: dict) -> int:
    return 0 if row["home_goals"] > row["away_goals"] else 1 if row["home_goals"] == row["away_goals"] else 2


def _prob(model: PoissonModel, row: dict) -> list[float] | None:
    try:
        m = model.markets(row["home"], row["away"])
        p = [m["1"], m["X"], m["2"]]
        return p if all(math.isfinite(x) and 0 < x < 1 for x in p) and abs(sum(p) - 1) < 1e-6 else None
    except (KeyError, OverflowError, ValueError, ZeroDivisionError):
        return None


def _metric(probs: list[float], y: int) -> tuple[float, float]:
    return -math.log(max(probs[y], 1e-12)), sum((p - (i == y)) ** 2 for i, p in enumerate(probs))


def _season_number(label: str) -> int:
    return int(label.split("/")[0])


def evaluate(rows: list[dict], test_seasons=TEST_SEASONS, min_training: int = 200) -> dict:
    """Train on strictly earlier completed seasons; never on the scored season."""
    result = {"method": "Poisson 60-minute 1X2, fixed parameters (shrink=8, half-life=365)",
              "baseline": "training-season 60-minute 1X2 class frequencies (Laplace-smoothed), NOT bookmaker odds",
              "release_eligible": False,
              "validation_status": "HISTORICAL_RESEARCH_AND_FORWARD_DIAGNOSTIC_ONLY",
              "as_of": max((r["date"] for r in rows), default=None),
              "leagues": {}}
    for league in LEAGUES:
        league_rows = [r for r in rows if r["league"] == league]
        reports = {}
        for season in test_seasons:
            cutoff = _season_number(season)
            training = [r for r in league_rows if _season_number(r["season"]) < cutoff]
            held_out = [r for r in league_rows if r["season"] == season]
            if len(training) < min_training or not held_out:
                reports[season] = {"status": "INSUFFICIENT_HISTORY_OR_TEST_MATCHES",
                                   "train_n": len(training), "test_n": len(held_out)}
                continue
            # Freeze parameters at the beginning of the test season.
            as_of = date(cutoff, 7, 1)
            # Never permit a future-dated source row in training even if its season label is wrong.
            training = [r for r in training if r["date"] < as_of]
            matches = [Match(r["date"], r["home"], r["away"],r["home_goals"],r["away_goals"])
                       for r in training]
            model = PoissonModel.fit(matches, as_of, half_life_days=365.0, xg_weight=0.0,
                                     shrink=8.0, rho=0.0, max_goals=12, iterations=90)
            counts = Counter(_outcome(r) for r in training)
            base = [(counts[i] + 1) / (len(training) + 3) for i in range(3)]
            model_ll, base_ll, model_brier, base_brier, scored, unseen = 0., 0., 0., 0., 0, 0
            calib = defaultdict(lambda: {"n": 0, "p_sum": 0., "actual": 0})
            for row in held_out:
                p = _prob(model, row)
                if p is None:
                    unseen += 1
                    continue
                y = _outcome(row)
                ll,b = _metric(p,y)
                bl,bb = _metric(base,y)
                model_ll += ll; model_brier += b
                base_ll += bl; base_brier += bb; scored += 1
                # outcome confidence calibration, selected-class event only
                choice = max(range(3),key=lambda i:p[i])
                bucket = min(9,int(p[choice]*10))
                c = calib[bucket]
                c["n"] += 1; c["p_sum"] += p[choice]; c["actual"] += int(choice==y)
            reports[season] = {
                "status": "EVALUATED_RESEARCH" if scored else "NO_SUPPORTED_TEST_TEAMS",
                "train_n": len(training), "test_n": len(held_out), "scored_n": scored,
                "unseen_teams_n": unseen, "model_logloss": round(model_ll/scored, 6) if scored else None,
                "base_rate_logloss": round(base_ll/scored,6) if scored else None,
                "logloss_gain_vs_base": round((base_ll-model_ll)/scored,6) if scored else None,
                "model_brier_3way": round(model_brier/scored,6) if scored else None,
                "base_rate_brier_3way": round(base_brier/scored,6) if scored else None,
                "baseline_probabilities_home_draw_away": [round(v,4) for v in base],
                "calibration_top_choice": [{"bucket":k, "n":v["n"],
                    "mean_confidence":round(v["p_sum"]/v["n"],4),
                    "hit_rate":round(v["actual"]/v["n"],4)}
                    for k,v in sorted(calib.items())],
            }
        result["leagues"][league] = reports
    return result


def run(path=INPUT, dest=OUTPUT, as_of: date | None = None):
    as_of = as_of or date.today()
    rows = load_history(path, as_of=as_of)
    result = evaluate(rows)
    result["evaluated_at_date"] = as_of.isoformat()
    result["market_logloss"] = None
    result["market_clv"] = None
    result["release_reason"] = "No paired contemporaneous bookmaker close and no untouched forward CLV cohort"
    Path(dest).parent.mkdir(parents=True,exist_ok=True)
    Path(dest).write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",encoding="utf-8")
    print(json.dumps({"evaluated_at_date":result["evaluated_at_date"],
          "league_season_summary":{lg:{year:{k:v.get(k) for k in ("scored_n","model_logloss",
               "base_rate_logloss","logloss_gain_vs_base")}
               for year,v in reports.items()} for lg,reports in result["leagues"].items()},
          "release_eligible": False},ensure_ascii=False))


if __name__ == "__main__":
    run()
