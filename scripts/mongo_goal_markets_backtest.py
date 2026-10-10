"""Cross-market soccer research using Soccer Mongo history and pre-match xG states.

No bookmaker odds as features; goal rates/1X2/totals/BTTS/AH from one
probability matrix. Select calibration only on 2020/21 historical outcomes.
2022/23 diagnostics and 2024 retrospective stress are NOT release evidence.
Pinnacle/B365 O2.5 opening vs closing compared only on paired matches.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from oddswatch import m17_17_research as research, pricing
from oddswatch.m12_research import _season_start
from oddswatch.m14_research import load_league, train_proxy, _mongo_db
from oddswatch.m17_1_research import load_real_shots
from oddswatch.models.goal_markets import goal_markets, asian_probability
from scripts.mongo_m17_17_backtest import LEAGUE_GROUPS

# Everything below is chosen before any 2022+ outcomes are inspected.
SCALES = (0.88, 1.0, 1.12)
FAST_WEIGHTS = (0.35, 0.65)
DRAW_FACTORS = (0.85, 1.0, 1.15)
RHO = -0.05
EPS = 1e-12


def _pre_match_rates(row: dict, *, scale: float, fast_weight: float):
    h = (float(row["lambda_home_fast"]) ** fast_weight
         * float(row["lambda_home_slow"]) ** (1-fast_weight)) * scale
    a = (float(row["lambda_away_fast"]) ** fast_weight
         * float(row["lambda_away_slow"]) ** (1-fast_weight)) * scale
    return h, a


def _outcomes(goals):
    h, a = goals
    return (0 if h > a else (1 if h == a else 2),
            int(h + a > 2.5), int(h > 0 and a > 0))


def _matrix(row, cfg):
    h, a = _pre_match_rates(row, scale=cfg["scale"],
                            fast_weight=cfg["fast_weight"])
    return goal_markets(h, a, rho=RHO, draw_factor=cfg["draw_factor"])


def _safe_log(p: float):
    return -math.log(max(EPS, min(1.0, float(p))))


def _losses(rows: list[dict], outcomes: dict[tuple, tuple], cfg: dict):
    losses = {"1X2": 0.0, "OU2.5": 0.0, "BTTS": 0.0}
    n = 0
    bias = [0.0, 0.0, 0.0]
    actual = [0, 0, 0]
    for r in rows:
        key = (r["date"], r["home"], r["away"])
        if key not in outcomes:
            continue
        y, over, btts = _outcomes(outcomes[key])
        _, m = _matrix(r, cfg)
        p1x2 = [m["1"], m["X"], m["2"]]
        losses["1X2"] += _safe_log(p1x2[y])
        losses["OU2.5"] += _safe_log(m["O2.5"] if over else m["U2.5"])
        losses["BTTS"] += _safe_log(m["BTTS_Y"] if btts else m["BTTS_N"])
        for k in range(3):
            bias[k] += p1x2[k]
            actual[k] += int(y == k)
        n += 1
    if not n:
        return None
    return {
        "n": n, "logloss": {k:v/n for k,v in losses.items()},
        "average_three_market_logloss": sum(losses.values())/(3*n),
        "predicted_1x2_rates": [v/n for v in bias],
        "actual_1x2_rates": [v/n for v in actual],
        "draw_gap": (bias[1]-actual[1])/n,
    }


def _early_calibration(data, outcomes):
    early = [r for r in data if r["season"] in (2020, 2021)]
    if sum(r["season"] == 2020 for r in early) < 60 or (
        sum(r["season"] == 2021 for r in early) < 60
    ):
        return None
    best = None
    for scale in SCALES:
        for fast_weight in FAST_WEIGHTS:
            for draw_factor in DRAW_FACTORS:
                cfg = {"scale":scale, "fast_weight":fast_weight,
                       "draw_factor":draw_factor}
                a = _losses([r for r in early if r["season"] == 2020],
                            outcomes, cfg)
                b = _losses([r for r in early if r["season"] == 2021],
                            outcomes, cfg)
                if not a or not b:
                    continue
                score = (a["average_three_market_logloss"]
                         + b["average_three_market_logloss"]) / 2
                if best is None or score < best["early_avg_loss"]:
                    best = dict(cfg, early_avg_loss=score,
                                folds={"2020": a, "2021": b})
    return best


def _odds_pair(doc, kind):
    if kind == "pinnacle":
        keys = (("P>2.5", "P<2.5"), ("PC>2.5", "PC<2.5"))
    else:
        keys = (("B365>2.5", "B365<2.5"),
                ("B365C>2.5", "B365C<2.5"))
    def get(k):
        try:
            x = float(doc.get(k))
            return x if math.isfinite(x) and 1.01 <= x <= 100 else None
        except (TypeError, ValueError):
            return None
    opening = tuple(get(k) for k in keys[0])
    closing = tuple(get(k) for k in keys[1])
    open2 = opening if all(x is not None for x in opening) else None
    close2 = closing if all(x is not None for x in closing) else None
    return open2, close2


def _market_prices(code, start_year=2017, end_year=2025):
    """Read-only O/U 2.5 odds; unambiguous (season, home, away) joins only."""
    from pymongo import MongoClient, timeout
    uri = (os.getenv("MONGO_SOCCER") or os.getenv("MONGODB_URI") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER/MONGODB_URI required")
    fields = ("P>2.5", "P<2.5", "PC>2.5", "PC<2.5",
              "B365>2.5", "B365<2.5", "B365C>2.5", "B365C<2.5")
    projection = {"_id":0, "Date":1, "HomeTeam":1, "AwayTeam":1}
    projection.update({k:1 for k in fields})
    start = datetime(start_year, 7, 1, tzinfo=timezone.utc)
    end = datetime(end_year+1, 7, 1, tzinfo=timezone.utc)
    records = {}
    seen = Counter()
    with timeout(180):
        with MongoClient(uri, serverSelectionTimeoutMS=15000,
                         connectTimeoutMS=10000,socketTimeoutMS=30000,
                         appname="soccer-goal-market-research") as client:
            col = _mongo_db(client)["mains"]
            docs = col.find({"Div":code,
                             "Date":{"$gte":start,"$lt":end}}, projection)
            for d in docs:
                when, home, away = d.get("Date"),d.get("HomeTeam"),d.get("AwayTeam")
                if not isinstance(when,datetime) or not home or not away:
                    continue
                key = (_season_start(when.date()),home,away)
                seen[key] += 1
                candidates = []
                for book in ("pinnacle","bet365"):
                    op, cl = _odds_pair(d,book)
                    if op:
                        candidates.append({"source":book, "opening":op,
                                           "closing":cl})
                records[key] = sorted(candidates,
                                      key=lambda v: (v["closing"] is None,
                                                     v["source"] != "pinnacle"))
    mongo_prices = {k:v[0] for k,v in records.items() if seen[k] == 1 and v}

    # The soccer Mongo import contains extensive 1X2 opening/closing quotes
    # but historically sparse O2.5 price columns. Use football-data's archived
    # *same-season* CSV as a completely separate market comparator. It never
    # enters goal-rate features or the 2020/21 calibration.
    import csv
    import io
    from oddswatch import fetch
    from oddswatch.sources import football_data as fd

    archive = {}
    fd_seen = Counter()
    fd_errors = {}
    for season in range(start_year, end_year + 1):
        raw, err = fetch.get(fd.csv_url(code, season), cache_days=30)
        if not raw:
            fd_errors[str(season)] = err or "football-data source unavailable"
            continue
        for d in csv.DictReader(io.StringIO(raw.lstrip("\ufeff"))):
            home, away = d.get("HomeTeam"), d.get("AwayTeam")
            if not home or not away:
                continue
            key = (season, home, away)
            fd_seen[key] += 1
            quotes = []
            for book in ("pinnacle", "bet365"):
                op, cl = _odds_pair(d, book)
                if op:
                    quotes.append({
                        "source":book+"_football_data",
                        "opening":op, "closing":cl,
                    })
            archive[key] = sorted(quotes,
                                  key=lambda v: (v["closing"] is None,
                                                 not v["source"].startswith("pinnacle")))
    fallback = {k:v[0] for k,v in archive.items() if fd_seen[k] == 1 and v}
    selected = dict(fallback)
    # Prefer the Mongo source when it has real opening/closing O/U pairs.
    selected.update(mongo_prices)
    return selected, {
        "mongo_ou_prices":len(mongo_prices),
        "football_data_ou_prices":len(fallback),
        "ambiguous_mongo_pairs":sum(n>1 for n in seen.values()),
        "ambiguous_football_data_pairs":sum(n>1 for n in fd_seen.values()),
        "merged_price_rows":len(selected),
        "football_data_errors":fd_errors,
    }


def _one_x2_market_test(rows, cfg, score_map):
    """Same-match 1X2 outcome logloss vs no-vig historical opening quotes."""
    model_loss = market_loss = 0.0
    n = 0
    for r in rows:
        outcome = score_map.get((r["date"], r["home"], r["away"]))
        op = r.get("op")
        if outcome is None or not op or len(op) != 3:
            continue
        y = _outcomes(outcome)[0]
        try:
            p_market = pricing.devig(list(op))
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        if any(not math.isfinite(p) or p <= 0 for p in p_market):
            continue
        _, pm = _matrix(r, cfg)
        p_model = [pm["1"], pm["X"], pm["2"]]
        model_loss += _safe_log(p_model[y])
        market_loss += _safe_log(p_market[y])
        n += 1
    return {
        "paired_2024_games":n,
        "model_logloss":model_loss/n if n else None,
        "opening_no_vig_logloss":market_loss/n if n else None,
        "gain_vs_market":(market_loss-model_loss)/n if n else None,
        "market_reference":"Pinnacle opening 1X2 as archived in Mongo",
        "release_eligible":False,
    }


def _total_market_test(rows, cfg, score_map, historical_prices):
    """Strict paired O2.5 opening market; no prices leak into model."""
    n = n_close = bets = positive = 0
    model_loss = market_loss = total_clv = total_roi = 0.0
    missing_close = 0
    by_source = Counter()
    for r in rows:
        key = (r["date"],r["home"],r["away"])
        target = score_map.get(key)
        historical = historical_prices.get((r["season"],r["home"],r["away"]))
        if target is None or historical is None:
            continue
        over = int(sum(target)>2.5)
        _, m = _matrix(r, cfg)
        opening = historical["opening"]
        market_p = pricing.devig(list(opening))
        model_loss += _safe_log(m["O2.5"] if over else m["U2.5"])
        market_loss += _safe_log(market_p[0] if over else market_p[1])
        n += 1
        by_source[historical["source"]] += 1
        if historical["closing"] is None:
            missing_close += 1
            continue
        n_close += 1
        close_p = pricing.devig(list(historical["closing"]))
        # Fixed 3% EV threshold, not retrospectively tuned.
        for k, name in enumerate(("O2.5", "U2.5")):
            edge = m[name]*opening[k]-1
            if edge < 0.03 or opening[k] > 3.0:
                continue
            bets += 1
            clv = opening[k]*close_p[k]-1
            total_clv += clv
            positive += int(clv > 0)
            won = over == (k == 0)
            total_roi += opening[k]-1 if won else -1
    return {
        "paired_opening_games":n,
        "paired_closing_games":n_close,
        "missing_closing":missing_close,
        "market_sources":dict(by_source),
        "model_logloss":model_loss/n if n else None,
        "opening_market_no_vig_logloss":market_loss/n if n else None,
        "gain_vs_market":(market_loss-model_loss)/n if n else None,
        "fixed_edge_3pct_retrospective_bets":bets,
        "fixed_edge_3pct_clv":total_clv/bets if bets else None,
        "fixed_edge_3pct_positive_clv_rate":positive/bets if bets else None,
        "fixed_edge_3pct_roi":total_roi/bets if bets else None,
        "note":"Research, matched openings + closings only. No validated PLAY.",
    }


def evaluate_league(code, proxy):
    matches, odds_rows, coverage = load_league(code,proxy,2017,2025)
    shots = load_real_shots(code,2017,2025)
    data, venue_coverage, xg_coverage = research._build_data(
        matches,odds_rows,shots)
    outcomes = {(d,h,a):(hg,ag) for _,d,h,a,hg,ag,_,_ in odds_rows}
    result = {
        "samples":len(data),
        "coverage":coverage,
        "release_eligible":False,
        "note":"2024 research stress; 2025 diagnostic; not a fresh holdout",
    }
    cfg = _early_calibration(data,outcomes)
    if cfg is None:
        return dict(result,error="insufficient 2020 and 2021 calibration games")
    result["calibration_2020_2021"] = cfg
    for season in (2022,2023,2024,2025):
        rows = [r for r in data if r["season"]==season]
        score = _losses(rows,outcomes,cfg)
        result[str(season)] = score
    result["retrospective_2024_1x2_vs_market"] = _one_x2_market_test(
        [r for r in data if r["season"] == 2024],cfg,outcomes)
    prices, market_coverage = _market_prices(code, start_year=2024, end_year=2024)
    result["historical_ou2.5_coverage"] = market_coverage
    result["retrospective_2024_ou2.5_vs_market"] = _total_market_test(
        [r for r in data if r["season"]==2024],cfg,outcomes,prices)
    # Other markets have no verified historical paired executable quotes;
    # never claim a CLV or mark a bet as PLAY for BTTS / AH.
    result["BTTS_historical_odds_comparison"] = "NO_MARKET_PRICE"
    result["AH_historical_odds_comparison"] = "NO_MARKET_PRICE"
    # Structural model supports pricing quarter-line total and AH in live shadow
    # only when a real current quote has been separately fetched.
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group",choices=tuple(LEAGUE_GROUPS),required=True)
    args = parser.parse_args()
    if not os.getenv("MONGO_SOCCER") and os.getenv("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]
    if not os.getenv("MONGO_SOCCER"):
        raise RuntimeError("Missing Soccer Mongo read-only connection")
    proxy = train_proxy(years=range(2017,2020))
    if max(proxy["train_seasons"])>=2020:
        raise RuntimeError("xG proxy fit leaked into early validation")
    output = {
        "method":"historical xG fast/slow score distribution + 2020-21 calibrated goal/draw factors",
        "proxy_training_seasons":proxy["train_seasons"],
        "split":{"hyper":"2020,2021","diagnostics":[2022,2023,2024,2025]},
        "no_bookmaker_odds_as_features":True,
        "release_eligible":False,
        "leagues":{},
    }
    valid = 0
    for league,code in LEAGUE_GROUPS[args.group].items():
        try:
            row = evaluate_league(code,proxy)
        except Exception as exc:
            row = {"release_eligible":False,
                   "error":f"{type(exc).__name__}: {exc}"}
        output["leagues"][league] = row
        if row.get("2024"):
            valid += 1
        print("GOAL_MODEL",league,json.dumps({
            "sample":row.get("samples"),
            "2024":row.get("2024"),
            "2024_1x2_market":row.get("retrospective_2024_1x2_vs_market"),
            "2024_ou2.5_market":row.get("retrospective_2024_ou2.5_vs_market"),
            "missing":row.get("error"),
        },ensure_ascii=False),flush=True)
    dest = Path(f"reports/mongo_goal_markets_{args.group}.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,indent=2,ensure_ascii=False),
                    encoding="utf-8")
    if not valid:
        raise RuntimeError("No usable historical goal model; no results")


if __name__=="__main__":
    main()
