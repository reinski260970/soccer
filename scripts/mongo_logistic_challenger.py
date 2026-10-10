"""Independent, strictly chronological multiclass football challenger.

Research only. Does not read bookmaker prices for model training or features.
Competes on fixed M17.17 historical features against its existing classifier.
Hyperparameters and calibration selected on 2020/21 OOS outcomes only.
2022 CLV tuning; 2023 strategy validation; 2024 retrospective stress; 2025 diagnostic.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from oddswatch import m17_17_research as legacy
from oddswatch import pricing
from oddswatch.m14_research import load_league, train_proxy
from oddswatch.m17_1_research import load_real_shots, _entry_stats
from oddswatch.m17_5_research import _logloss
from oddswatch.m17_16_research import _tune_gate_2022, _validate_gate_2023
from scripts.mongo_m17_17_backtest import LEAGUE_GROUPS


def _fit_predict(train, test, regularization, calibration):
    if not train or not test:
        raise ValueError("empty training or test fold")
    x = [r["x"] for r in train]
    y = [r["y"] for r in train]
    if set(y) != {0, 1, 2}:
        raise ValueError("train fold lacks all outcome classes")
    pipeline = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=regularization, max_iter=500, solver="lbfgs"),
    )
    pipeline.fit(x, y)
    pp = pipeline.predict_proba([r["x"] for r in test])
    classes = list(pipeline.named_steps["logisticregression"].classes_)
    out = []
    for row in pp:
        vec = [max(float(row[classes.index(k)]), 1e-12) for k in range(3)]
        adj = [p**calibration for p in vec]
        z = sum(adj)
        out.append([p/z for p in adj])
    return out


def _select_hyper(data):
    folds = [
        (2020, [r for r in data if r["season"] <= 2019]),
        (2021, [r for r in data if r["season"] <= 2020]),
    ]
    folds = [(year, train, [r for r in data if r["season"] == year])
             for year, train in folds]
    if any(len(train) < 400 or len(test) < 80 for _, train, test in folds):
        return None
    best = None
    for strength in (0.01, 0.1, 1.0, 5.0):
        raw = []
        for year, train, test in folds:
            raw.append((test, _fit_predict(train, test, strength, 1.0)))
        for calibration in (0.75, 0.90, 1.0, 1.10):
            losses = []
            for test, pp in raw:
                pp2 = []
                for p in pp:
                    q = [max(x, 1e-12)**calibration for x in p]
                    z = sum(q)
                    pp2.append([v/z for v in q])
                losses.append(_logloss(pp2, [r["y"] for r in test]))
            score = sum(losses)/len(losses)
            if best is None or score < best["early_oos_logloss"]:
                best = {
                    "C": strength,
                    "calibration": calibration,
                    "early_oos_logloss": score,
                    "fold_logloss": losses,
                }
    return best


def _oos(data, year, chosen):
    train = [r for r in data if r["season"] < year]
    test = [r for r in data if r["season"] == year]
    if len(train) < 500 or len(test) < 60:
        return []
    pp = _fit_predict(train, test, chosen["C"], chosen["calibration"])
    return [dict(r, p=p) for r, p in zip(test, pp)]


def evaluate_league(code, proxy):
    matches, odds_rows, cov = load_league(code, proxy, start_year=2017, end_year=2025)
    shots = load_real_shots(code, start_year=2017, end_year=2025)
    data, venue_cov, xg_cov = legacy._build_data(matches, odds_rows, shots)
    output = {
        "samples": len(data),
        "coverage": cov,
        "historical_venue_coverage": venue_cov,
        "historical_xg_coverage": xg_cov,
        "release_eligible": False,
        "note": "Retrospective already inspected; forward CLV required",
    }
    chosen = _select_hyper(data)
    if chosen is None:
        return dict(output, error="insufficient early OOS data")
    output["hyper"] = chosen
    eval22, eval23, eval24, eval25 = (
        _oos(data, year, chosen) for year in (2022, 2023, 2024, 2025)
    )
    if not eval24:
        return dict(output, error="2024 validation rows missing")
    tuned, near = _tune_gate_2022(eval22)
    survived, val23 = _validate_gate_2023(eval23, tuned)
    candidate_gate = tuned or near
    diagnostic24 = (
        _entry_stats(eval24, candidate_gate["edge"], candidate_gate["cap"],
                     candidate_gate["side"])
        if candidate_gate else None
    )
    y = [r["y"] for r in eval24]
    model = _logloss([r["p"] for r in eval24], y)
    market = _logloss([pricing.devig(r["op"]) for r in eval24], y)
    gaps = [sum(r["p"][k] - float(r["y"] == k) for r in eval24) / len(eval24)
            for k in range(3)]
    output.update({
        "2022_tuned_gate": tuned,
        "2023_gate_survived": survived,
        "2023_validation": val23,
        "2024_retrospective": diagnostic24,
        "2024_oos_games": len(eval24),
        "2024_logloss": {
            "model": model, "market": market, "gain": market-model,
        },
        "2024_calibration_gap_home_draw_away": gaps,
        "2025_diagnostic_games": len(eval25),
    })
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=LEAGUE_GROUPS, required=True)
    args = parser.parse_args()
    if not (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGODB_URI")):
        raise RuntimeError("MONGO_SOCCER required")
    if not os.environ.get("MONGO_SOCCER"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]
    proxy = train_proxy(years=range(2017, 2020))
    if max(proxy["train_seasons"]) >= 2020:
        raise RuntimeError("validation leakage in xG proxy")
    result = {
        "method": "logistic-regression-challenger, no market features",
        "proxy_train_seasons": proxy["train_seasons"],
        "splits": {"hyper": "2020/21", "entry_tune": "2022",
                   "entry_check": "2023", "stress": "2024", "diagnostic": "2025"},
        "release_eligible": False,
        "leagues": {},
    }
    valid = 0
    for league, code in LEAGUE_GROUPS[args.group].items():
        try:
            row = evaluate_league(code, proxy)
        except Exception as exc:
            row = {"release_eligible": False,
                   "error": f"{type(exc).__name__}: {exc}"}
        result["leagues"][league] = row
        if "2024_logloss" in row:
            valid += 1
        print("CHALLENGER", league, json.dumps({
            "samples": row.get("samples"),
            "2024_oos_games": row.get("2024_oos_games"),
            "logloss": row.get("2024_logloss"),
            "clv_roi": row.get("2024_retrospective"),
            "gate_survived": row.get("2023_gate_survived"),
            "error": row.get("error"),
        }, ensure_ascii=False), flush=True)
    dest = Path(f"reports/mongo_logistic_challenger_{args.group}.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if valid == 0:
        raise RuntimeError("No valid challenger comparison; cannot claim performance")


if __name__ == "__main__":
    main()
