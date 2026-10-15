"""NHL V6 pre-match fair odds. Independent of bookmaker prices.

Usage:
 python -m oddswatch.nhl_v6_prematch --features current_v6_features.json --out v6_fair.json

Input is a JSON list of game objects with 'date','home','away',
'data_through', and ALL V6 feature columns. The feature producer must
use only completed games before the event. Missing/stale inputs fail closed.
"""
import argparse
import json
import math
from datetime import date
from pathlib import Path

from .nhl_bulk_backtest import SOURCE, load_rows
from .nhl_bulk_v6 import FEATURES, build_rows, _select, _fit, _pred, _base, _blend


def score_games(games, *, archive=SOURCE, max_age_days=7):
    raw = load_rows(archive)
    history, _, _ = build_rows(raw)
    if not history:
        raise ValueError("No V6 training rows")
    last_season = max(r["season"] for r in history)
    choice = _select(history, last_season + 1)
    if choice is None:
        raise ValueError("Insufficient history for chronological V6 calibration")
    model = _fit(choice["C"], history)
    baseline = _base(history)
    clean = []
    for game in games:
        event_day = date.fromisoformat(str(game["date"])[:10])
        through = date.fromisoformat(str(game["data_through"])[:10])
        if not (through < event_day and (event_day - through).days <= max_age_days):
            raise ValueError(f"Missing/stale pre-match data for {game.get('home')} - {game.get('away')}")
        missing = [k for k in FEATURES if k not in game]
        if missing:
            raise ValueError(f"Missing V6 features for {game.get('home')}: {missing}")
        if not all(math.isfinite(float(game[k])) for k in FEATURES):
            raise ValueError("Non-finite V6 feature")
        clean.append({**game, "target": 0})
    if not clean:
        return []
    ps = _pred(model, clean)
    result = []
    for game, p in zip(clean, ps):
        p = min(0.999999, max(0.000001, _blend(p, baseline, choice["shrink"])))
        result.append({
            "date": game["date"], "home": game["home"], "away": game["away"],
            "data_through": game["data_through"], "model": "NHL_V6",
            "home_probability": round(p, 6),
            "away_probability": round(1-p, 6),
            "home_fair_decimal": round(1/p, 3),
            "away_fair_decimal": round(1/(1-p), 3),
            "status": "WATCH_NO_PLAY",
        })
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--out", default="data/hockey/nhl_v6_fair_today.json")
    ap.add_argument("--max-age-days", type=int, default=7)
    args = ap.parse_args()
    games = json.loads(Path(args.features).read_text(encoding="utf-8"))
    result = score_games(games, max_age_days=args.max_age_days)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"scored": len(result), "out": str(dest)}))


if __name__ == "__main__":
    main()
