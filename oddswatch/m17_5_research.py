"""M17.5: league-wide Mongo history research with learned xG proxy.

Purpose
-------
Use the large football Mongo history immediately instead of waiting for new
public xG snapshots.

Historical model inputs:
- results / home-away context
- HS/AS, HST/AST, HC/AC from Mongo
- xG proxy learned ONLY from Top-5 Mongo shot data matched to real Understat xG
- rolling form/rest/home-away state

Market data:
- Pinnacle opening/closing are used ONLY after model probabilities exist
  for entry/CLV evaluation. They are never model features.

Strict chronology per league:
- model hyperparameters: early outcome-logloss folds (2020, 2021)
- entry gate: rolling OOS 2022 + 2023 CLV
- untouched holdout: rolling OOS 2024
- 2025: diagnostic only

A league is RELEASED only if:
1) the tune gate is robust,
2) 2024 holdout CLV is positive on mean + median with >=52% positive CLV,
3) enough 2024 bets exist,
4) the independent model also beats Pinnacle opening on 2024 outcome logloss.

No gate is loosened to create picks.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

from . import pricing
from .m14_research import LEAGUES, load_league, train_proxy
from .m17_1_research import (
    L2_GRID,
    CALIB,
    build_dataset,
    load_real_shots,
    _fit,
    _pred,
    _calibrate,
    _standardizer,
    _tx,
    _logloss,
    _entry_stats,
)

OUT = Path("data/m17_5_validation.json")

EDGE_GRID = (0.02, 0.03, 0.05, 0.075, 0.10)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0)
SIDES = ("all", "home", "draw", "away")

START_YEAR = 2017
END_YEAR = 2025


def _mongo_db(client):
    from pymongo.errors import ConfigurationError
    try:
        db = client.get_default_database()
    except ConfigurationError:
        db = None
    return db if db is not None else client["euro_football"]


def _exists(fields: list[str]) -> dict:
    return {f: {"$exists": True, "$ne": None} for f in fields}


def mongo_coverage() -> dict:
    """Read-only Mongo coverage, aggregated only; no document values exported."""
    from pymongo import MongoClient, timeout

    uri = (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGODB_URI") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER fehlt")

    start = datetime(START_YEAR, 7, 1, tzinfo=timezone.utc)
    end = datetime(END_YEAR + 1, 7, 1, tzinfo=timezone.utc)

    out = {"mains": {}, "extra_leagues": {}}
    with timeout(180):
        with MongoClient(
            uri,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            appname="oddswatch-m17-5-coverage",
        ) as client:
            db = _mongo_db(client)

            if "mains" in db.list_collection_names():
                col = db["mains"]
                for league, code in LEAGUES.items():
                    base = {"Div": code, "Date": {"$gte": start, "$lt": end}}
                    total = col.count_documents(base)
                    results = col.count_documents({
                        **base, **_exists(["FTHG", "FTAG", "HomeTeam", "AwayTeam"])
                    })
                    shots = col.count_documents({
                        **base, **_exists(["HS", "AS", "HST", "AST", "HC", "AC"])
                    })
                    odds = col.count_documents({
                        **base, **_exists(["PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA"])
                    })
                    complete = col.count_documents({
                        **base,
                        **_exists([
                            "FTHG", "FTAG", "HomeTeam", "AwayTeam",
                            "HS", "AS", "HST", "AST", "HC", "AC",
                            "PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA",
                        ]),
                    })
                    dates = list(col.aggregate([
                        {"$match": base},
                        {"$group": {
                            "_id": None,
                            "min": {"$min": "$Date"},
                            "max": {"$max": "$Date"},
                        }},
                    ]))
                    out["mains"][league] = {
                        "code": code,
                        "rows": total,
                        "results": results,
                        "shots_corners": shots,
                        "pinnacle_open_close": odds,
                        "complete_rows": complete,
                        "complete_pct": complete / total if total else 0.0,
                        "date_min": dates[0]["min"].isoformat() if dates and dates[0].get("min") else None,
                        "date_max": dates[0]["max"].isoformat() if dates and dates[0].get("max") else None,
                    }

            # Extra leagues are profiled explicitly because they may contain
            # long history but often lack the shot/corner + closing-price fields
            # needed for strict M17.5 xG-proxy/CLV validation.
            if "extra_leagues" in db.list_collection_names():
                col = db["extra_leagues"]
                countries = ["Austria", "Switzerland", "Norway", "Sweden", "Denmark"]
                for country in countries:
                    base = {"Country": country}
                    total = col.count_documents(base)
                    result_fields = ["Date", "Home", "Away", "HG", "AG"]
                    shot_fields = ["HS", "AS", "HST", "AST", "HC", "AC"]
                    close_fields = ["PSH", "PSD", "PSA", "PSCH", "PSCD", "PSCA"]
                    out["extra_leagues"][country] = {
                        "rows": total,
                        "results": col.count_documents({**base, **_exists(result_fields)}),
                        "shots_corners": col.count_documents({**base, **_exists(shot_fields)}),
                        "pinnacle_open_close": col.count_documents({**base, **_exists(close_fields)}),
                        "avg_1x2": col.count_documents({
                            **base, **_exists(["AvgH", "AvgD", "AvgA"])
                        }),
                    }
    return out


def _fit_predict(train, test, l2, calib):
    mean, sd = _standardizer([r["x"] for r in train])
    xtr = _tx([r["x"] for r in train], mean, sd)
    xte = _tx([r["x"] for r in test], mean, sd)
    w = _fit(xtr, [r["y"] for r in train], l2)
    return [_calibrate(_pred(w, x), calib) for x in xte]


def _early_hyper(data):
    """Choose model only by outcome logloss before any CLV-tune season."""
    folds = [
        ([r for r in data if r["season"] <= 2019],
         [r for r in data if r["season"] == 2020]),
        ([r for r in data if r["season"] <= 2020],
         [r for r in data if r["season"] == 2021]),
    ]
    if any(len(tr) < 400 or len(va) < 80 for tr, va in folds):
        return None

    best = None
    for l2 in L2_GRID:
        raw = []
        for tr, va in folds:
            mean, sd = _standardizer([r["x"] for r in tr])
            w = _fit(
                _tx([r["x"] for r in tr], mean, sd),
                [r["y"] for r in tr],
                l2,
            )
            pp = [_pred(w, x) for x in _tx([r["x"] for r in va], mean, sd)]
            raw.append((va, pp))

        for calib in CALIB:
            losses = [
                _logloss(
                    [_calibrate(p, calib) for p in pp],
                    [r["y"] for r in va],
                )
                for va, pp in raw
            ]
            score = sum(losses) / len(losses)
            if best is None or score < best["cv_logloss"]:
                best = {
                    "l2": l2,
                    "calib": calib,
                    "cv_logloss": score,
                    "fold_logloss": losses,
                }
    return best


def _attach(rows, probs):
    out = []
    for r, p in zip(rows, probs):
        z = dict(r)
        z["p"] = p
        out.append(z)
    return out


def _rolling_eval(data, year: int, hyper: dict):
    train = [r for r in data if r["season"] <= year - 1]
    test = [r for r in data if r["season"] == year]
    if len(train) < 500 or len(test) < 60:
        return []
    return _attach(
        test,
        _fit_predict(train, test, hyper["l2"], hyper["calib"]),
    )


def _choose_gate(tune_by_year):
    merged = [r for y in sorted(tune_by_year) for r in tune_by_year[y]]
    best = None
    near = None

    for edge in EDGE_GRID:
        for cap in ODDS_CAP:
            for side in SIDES:
                total = _entry_stats(merged, edge, cap, side)
                yearly = {
                    str(y): _entry_stats(rows, edge, cap, side)
                    for y, rows in tune_by_year.items()
                }
                fails = []
                if total["bets"] < 40:
                    fails.append("tune_bets<40")
                if total["clv"] <= 0:
                    fails.append("tune_mean_clv<=0")
                if total["median_clv"] <= 0:
                    fails.append("tune_median_clv<=0")
                if total["positive_clv_rate"] < 0.52:
                    fails.append("tune_positive_clv_rate<52%")
                for y, s in yearly.items():
                    if s["bets"] < 10:
                        fails.append(f"{y}_bets<10")
                    if s["clv"] <= 0:
                        fails.append(f"{y}_clv<=0")

                passed = 6 - min(6, len(fails))
                near_score = (
                    passed * 100.0
                    + total["clv"] * math.sqrt(max(total["bets"], 1)) * 20.0
                    + total["median_clv"] * 10.0
                    + (total["positive_clv_rate"] - 0.5) * 10.0
                )
                cand = {
                    "edge": edge,
                    "cap": cap,
                    "side": side,
                    "stats": total,
                    "per_year": yearly,
                    "fails": fails,
                    "near_score": near_score,
                }
                if near is None or near_score > near["near_score"]:
                    near = cand
                if fails:
                    continue

                cand["score"] = total["clv"] * math.sqrt(total["bets"])
                if best is None or cand["score"] > best["score"]:
                    best = cand
    return best, near


def _market_logloss(rows):
    if not rows:
        return 9.0
    return _logloss(
        [pricing.devig(r["op"]) for r in rows],
        [r["y"] for r in rows],
    )


def _league_run(matches, odds_rows, shots, cov):
    data = build_dataset(matches, odds_rows, shots)
    result = {
        "samples": len(data),
        "coverage": cov,
    }

    if cov.get("proxy_coverage", 0.0) < 0.70:
        result.update({
            "validated": False,
            "reason": "historical shot/corner proxy coverage <70%",
        })
        return result

    hyper = _early_hyper(data)
    result["hyper"] = hyper
    if hyper is None:
        result.update({
            "validated": False,
            "reason": "too little strict early walk-forward data",
        })
        return result

    tune = {
        2022: _rolling_eval(data, 2022, hyper),
        2023: _rolling_eval(data, 2023, hyper),
    }
    if any(len(v) < 60 for v in tune.values()):
        result.update({
            "validated": False,
            "reason": "too little 2022/2023 OOS tune data",
            "tune_counts": {str(k): len(v) for k, v in tune.items()},
        })
        return result

    gate, near = _choose_gate(tune)
    hold_eval = _rolling_eval(data, 2024, hyper)
    diag_eval = _rolling_eval(data, 2025, hyper)
    use_gate = gate or near

    empty = {
        "bets": 0,
        "clv": 0.0,
        "median_clv": 0.0,
        "positive_clv_rate": 0.0,
        "roi": 0.0,
    }
    hold = (
        _entry_stats(
            hold_eval,
            use_gate["edge"],
            use_gate["cap"],
            use_gate["side"],
        )
        if use_gate and hold_eval
        else dict(empty)
    )
    diag = (
        _entry_stats(
            diag_eval,
            use_gate["edge"],
            use_gate["cap"],
            use_gate["side"],
        )
        if use_gate and diag_eval
        else dict(empty)
    )

    hold_rows = [r for r in data if r["season"] == 2024]
    hold_model_ll = (
        _logloss([r["p"] for r in hold_eval], [r["y"] for r in hold_eval])
        if hold_eval
        else 9.0
    )
    hold_market_ll = _market_logloss(hold_rows)

    strategy_ok = bool(
        gate is not None
        and hold["bets"] >= 15
        and hold["clv"] > 0
        and hold["median_clv"] > 0
        and hold["positive_clv_rate"] >= 0.52
    )
    model_ok = hold_model_ll < hold_market_ll
    validated = bool(strategy_ok and model_ok)

    result.update({
        "validated": validated,
        "strategy_validated": strategy_ok,
        "model_beats_opening_logloss": model_ok,
        "gate": gate,
        "near_miss_gate": near,
        "strict_holdout_2024": hold,
        "strict_holdout_logloss": {
            "model": hold_model_ll,
            "opening": hold_market_ll,
            "gain": hold_market_ll - hold_model_ll,
        },
        "diagnostic_only_2025": diag,
    })
    return result


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    profile = mongo_coverage()
    proxy = train_proxy()

    result = {
        "_method": (
            "M17.5 Mongo HS/HST/HC learned-xG proxy + rolling classifier; "
            "strict league-by-league OOS; no market features"
        ),
        "_proxy": {
            "n": proxy["n"],
            "rmse": proxy["rmse"],
            "beta": proxy["beta"],
            "features": proxy["features"],
            "train_seasons": proxy["train_seasons"],
        },
        "_splits": {
            "hyper_A": "train<=2019 validate=2020 outcome logloss",
            "hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "rolling OOS 2022 + 2023 CLV",
            "strict_holdout": "rolling OOS 2024",
            "diagnostic_only": "rolling OOS 2025",
        },
        "_release_rule": (
            "robust 2022+2023 CLV gate AND 2024 >=15 bets, mean/median CLV>0, "
            "positive CLV rate>=52%, AND model 2024 logloss < Pinnacle opening"
        ),
        "mongo_profile": profile,
        "leagues": {},
    }

    log = [
        f"M17.5 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}",
    ]

    for league, code in LEAGUES.items():
        try:
            matches, rows, cov = load_league(
                code,
                proxy,
                start_year=START_YEAR,
                end_year=END_YEAR,
            )
            shots = load_real_shots(
                code,
                start_year=START_YEAR,
                end_year=END_YEAR,
            )
            r = _league_run(matches, rows, shots, cov)
        except Exception as exc:
            r = {
                "validated": False,
                "reason": f"load/research failed: {type(exc).__name__}",
            }

        result["leagues"][league] = r
        gate = r.get("gate") or r.get("near_miss_gate") or {}
        ts = gate.get("stats") or {}
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        log.append(
            f"{league}: samples={r.get('samples',0)} "
            f"proxy={((r.get('coverage') or {}).get('proxy_coverage',0))*100:.1f}% | "
            f"gate={'OK' if r.get('gate') else 'NONE'} "
            f"{gate.get('side','-')} edge={gate.get('edge')} cap={gate.get('cap')} "
            f"tune n={ts.get('bets',0)} CLV={ts.get('clv',0)*100:+.2f}% | "
            f"hold n={hs.get('bets',0)} CLV={hs.get('clv',0)*100:+.2f}% "
            f"med={hs.get('median_clv',0)*100:+.2f}% "
            f"pos={hs.get('positive_clv_rate',0)*100:.1f}% "
            f"dLL={ll.get('gain',0):+.4f} -> "
            + ("RELEASE" if r.get("validated") else "NO RELEASE")
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=1, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    log.append(f"gespeichert: {out}")
    return log


if __name__ == "__main__":
    for line in run():
        print(line)
