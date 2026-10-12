"""Diagnostic decomposition for NHL V5.

This module does not change the forecast or entry gate. It only decomposes the
already-defined strict OOS predictions to identify where Logloss/CLV/ROI are lost.
Opening/closing prices are diagnostic-only.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .nhl_bulk_backtest import SOURCE, MIN_EV, _devig_home, _ll, load_rows
from .nhl_bulk_v5 import build_rows, _select, _fit, _base, _pred, _blend

OUT = Path("data/hockey/nhl_v5_diagnostics.json")
TARGET_SEASONS = (2020, 2021)


def _forecast(rows, season):
    choice = _select(rows, season)
    train = [r for r in rows if r["season"] < season]
    test = [r for r in rows if r["season"] == season]
    if choice is None or not test:
        return [], choice
    m = _fit(choice["C"], train)
    b = _base(train)
    ps = [_blend(p, b, choice["shrink"]) for p in _pred(m, test)]
    out = []
    for r, p in zip(test, ps):
        q = dict(r)
        q["p_home"] = float(p)
        q["market_p_home"] = _devig_home(r["home_close"], r["away_close"])
        q["open_p_home"] = _devig_home(r["home_open"], r["away_open"])
        out.append(q)
    return out, choice


def _segment_stats(rows):
    if not rows:
        return {"n": 0}
    model_ll = sum(_ll(r["p_home"], bool(r["target"])) for r in rows)
    market_ll = sum(_ll(r["market_p_home"], bool(r["target"])) for r in rows)
    home_rate = sum(int(r["target"]) for r in rows) / len(rows)
    avg_model_home = sum(r["p_home"] for r in rows) / len(rows)
    avg_market_home = sum(r["market_p_home"] for r in rows) / len(rows)

    bets = []
    for r in rows:
        eh = r["p_home"] * r["home_open"] - 1
        ea = (1-r["p_home"]) * r["away_open"] - 1
        if max(eh, ea) < MIN_EV:
            continue
        home = eh >= ea
        entry = r["home_open"] if home else r["away_open"]
        close_prob = r["market_p_home"] if home else 1-r["market_p_home"]
        won = bool(r["target"]) if home else not bool(r["target"])
        bets.append({
            "home": home,
            "entry": entry,
            "ev": eh if home else ea,
            "clv": close_prob * entry - 1,
            "won": won,
        })

    profit = sum(b["entry"]-1 if b["won"] else -1 for b in bets)
    return {
        "n": len(rows),
        "model_logloss": round(model_ll/len(rows), 6),
        "market_logloss": round(market_ll/len(rows), 6),
        "logloss_gain_vs_market": round((market_ll-model_ll)/len(rows), 6),
        "actual_home_win_rate": round(home_rate, 6),
        "avg_model_home_prob": round(avg_model_home, 6),
        "avg_market_home_prob": round(avg_market_home, 6),
        "home_bias_model_minus_actual": round(avg_model_home-home_rate, 6),
        "home_bias_market_minus_actual": round(avg_market_home-home_rate, 6),
        "bets": len(bets),
        "home_bets": sum(b["home"] for b in bets),
        "away_bets": sum(not b["home"] for b in bets),
        "profit_units": round(profit, 3),
        "roi": round(profit/len(bets), 6) if bets else None,
        "mean_clv": round(sum(b["clv"] for b in bets)/len(bets), 6) if bets else None,
        "positive_clv_rate": round(sum(b["clv"]>0 for b in bets)/len(bets), 6) if bets else None,
        "mean_entry_ev": round(sum(b["ev"] for b in bets)/len(bets), 6) if bets else None,
    }


def _by(rows, labeler):
    buckets = defaultdict(list)
    for r in rows:
        buckets[str(labeler(r))].append(r)
    return {k: _segment_stats(v) for k, v in sorted(buckets.items())}


def _odds_band(r):
    eh = r["p_home"] * r["home_open"] - 1
    ea = (1-r["p_home"]) * r["away_open"] - 1
    home = eh >= ea
    o = r["home_open"] if home else r["away_open"]
    if o < 1.60: return "<1.60"
    if o < 1.90: return "1.60-1.89"
    if o < 2.20: return "1.90-2.19"
    if o < 2.80: return "2.20-2.79"
    if o < 3.50: return "2.80-3.49"
    return "3.50+"


def _edge_band(r):
    eh = r["p_home"] * r["home_open"] - 1
    ea = (1-r["p_home"]) * r["away_open"] - 1
    e = max(eh, ea)
    if e < .03: return "<3%"
    if e < .06: return "3-6%"
    if e < .10: return "6-10%"
    if e < .15: return "10-15%"
    return "15%+"


def _side(r):
    eh = r["p_home"] * r["home_open"] - 1
    ea = (1-r["p_home"]) * r["away_open"] - 1
    return "HOME" if eh >= ea else "AWAY"


def _market_role(r):
    eh = r["p_home"] * r["home_open"] - 1
    ea = (1-r["p_home"]) * r["away_open"] - 1
    home = eh >= ea
    selected_open = r["home_open"] if home else r["away_open"]
    other_open = r["away_open"] if home else r["home_open"]
    return "FAVORITE" if selected_open < other_open else "UNDERDOG"


def _rest_bucket(r):
    d = float(r["rest_diff"])
    if d <= -2: return "HOME_REST_-2_OR_WORSE"
    if d == -1: return "HOME_REST_-1"
    if d == 0: return "EVEN_REST"
    if d == 1: return "HOME_REST_+1"
    return "HOME_REST_+2_OR_MORE"


def _prob_bucket(r):
    p = r["p_home"]
    if p < .35: return "<.35"
    if p < .45: return ".35-.44"
    if p < .55: return ".45-.54"
    if p < .65: return ".55-.64"
    return ".65+"


def _xg_agreement(r):
    slow = float(r.get("slow_mp_xg_share_diff", 0.0))
    fast = float(r.get("fast_mp_xg_share_diff", 0.0))
    if abs(slow) < .01 or abs(fast) < .01:
        return "WEAK"
    return "AGREE" if slow * fast > 0 else "DISAGREE"


def diagnose(rows, season):
    fc, choice = _forecast(rows, season)
    if not fc:
        return {"status": "NO_FORECAST", "season": season}
    return {
        "status": "OK",
        "season": season,
        "model_choice": choice,
        "overall": _segment_stats(fc),
        "by_side": _by(fc, _side),
        "by_selected_market_role": _by(fc, _market_role),
        "by_selected_open_odds": _by(fc, _odds_band),
        "by_model_edge": _by(fc, _edge_band),
        "by_rest": _by(fc, _rest_bucket),
        "by_model_home_probability": _by(fc, _prob_bucket),
        "by_slow_fast_xg_agreement": _by(fc, _xg_agreement),
    }


def run(path=SOURCE, dest=OUT):
    raw = load_rows(path)
    rows, _, _ = build_rows(raw)
    seasons = {}
    for s in TARGET_SEASONS:
        seasons[str(s)] = diagnose(rows, s)
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "diagnostic only; no model or gate selection",
        "market_features_used_in_forecast": False,
        "seasons": seasons,
    }
    Path(dest).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
