"""M17.2: focused football research for away-side 1X2 value.

Goals:
- keep bookmaker odds OUT of model features,
- use a richer nonlinear transform of M17.1's strictly pre-match state,
- tune model hyperparameters only on early outcome-logloss folds,
- tune the entry rule on 2022/23 + 2023/24 CLV,
- reserve 2024/25 as a strict untouched validation season,
- keep 2025/26 diagnostic-only because it has already been inspected.

Initial focus is deliberately narrow: Bundesliga away and Serie A away. This is
not a blanket football release. A segment is only marked validated when the
untouched 2024/25 entry sample has positive mean/median CLV and >=52% positive
CLV rate with a minimum sample.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from . import pricing
from .m13_research import load_real_xg
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

OUT = Path("data/m17_2_validation.json")

FOCUS = {
    "bundesliga": "D1",
    "seriea": "I1",
}

# Fixed away-side research family. Restricting the search space reduces
# multiple-testing risk versus re-optimising side/cap for every league.
EDGE_GRID = (0.02, 0.03, 0.05, 0.075)
ODDS_CAP = 2.5
SIDE = "away"


def _augment(x: list[float]) -> list[float]:
    """Deterministic nonlinear transforms of pre-match M17.1 features.

    No market or closing-price information enters here.
    """
    # Original indices:
    # 1/2 goals matchup, 3/4 xG matchup, 5/6 SoT, 7/8 shots,
    # 9 points, 10/11 venue goals, 12 rest, 13 confidence.
    goal = x[1] - x[2]
    xg = x[3] - x[4]
    sot = x[5] - x[6]
    shots = x[7] - x[8]
    pts = x[9]
    venue = x[10] - x[11]
    rest = x[12]
    conf = x[13]
    # Signed quadratic terms retain direction while allowing nonlinear effects.
    return x + [
        goal,
        xg,
        sot,
        shots,
        venue,
        goal * abs(goal),
        xg * abs(xg),
        sot * abs(sot),
        xg * sot,
        xg * pts,
        venue * xg,
        rest * xg,
        conf * xg,
    ]


def _dataset(matches, odds_rows, shot_map):
    rows = build_dataset(matches, odds_rows, shot_map)
    for r in rows:
        r["x"] = _augment(r["x"])
    return rows


def _fit_predict(train, test, l2, calib):
    mean, sd = _standardizer([r["x"] for r in train])
    xtr = _tx([r["x"] for r in train], mean, sd)
    xte = _tx([r["x"] for r in test], mean, sd)
    w = _fit(xtr, [r["y"] for r in train], l2)
    return [_calibrate(_pred(w, x), calib) for x in xte]


def _early_hyper(data):
    """Hyperparameters are chosen before any CLV entry-gate season."""
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
            w = _fit(_tx([r["x"] for r in tr], mean, sd),
                     [r["y"] for r in tr], l2)
            pp = [_pred(w, x) for x in _tx([r["x"] for r in va], mean, sd)]
            raw.append((va, pp))
        for a in CALIB:
            losses = [
                _logloss([_calibrate(p, a) for p in pp], [r["y"] for r in va])
                for va, pp in raw
            ]
            score = sum(losses) / len(losses)
            if best is None or score < best["cv_logloss"]:
                best = {
                    "l2": l2,
                    "calib": a,
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
    return _attach(test, _fit_predict(train, test, hyper["l2"], hyper["calib"]))


def _choose_gate(tune_by_year: dict[int, list[dict]]):
    best = None
    near = None
    merged = [r for y in sorted(tune_by_year) for r in tune_by_year[y]]

    for edge in EDGE_GRID:
        total = _entry_stats(merged, edge, ODDS_CAP, SIDE)
        yearly = {
            str(y): _entry_stats(rows, edge, ODDS_CAP, SIDE)
            for y, rows in tune_by_year.items()
        }
        fails = []
        if total["bets"] < 30:
            fails.append("tune_bets<30")
        if total["clv"] <= 0:
            fails.append("tune_mean_clv<=0")
        if total["median_clv"] <= 0:
            fails.append("tune_median_clv<=0")
        if total["positive_clv_rate"] < 0.52:
            fails.append("tune_positive_clv_rate<52%")
        for y, s in yearly.items():
            if s["bets"] < 8:
                fails.append(f"{y}_bets<8")
            if s["clv"] <= 0:
                fails.append(f"{y}_clv<=0")

        passed = 6 - min(len(fails), 6)
        near_score = (
            passed * 100.0
            + total["clv"] * math.sqrt(max(total["bets"], 1)) * 20.0
            + total["median_clv"] * 10.0
            + (total["positive_clv_rate"] - 0.5) * 10.0
        )
        cand = {
            "edge": edge,
            "cap": ODDS_CAP,
            "side": SIDE,
            "stats": total,
            "per_year": yearly,
            "fails": fails,
            "near_score": near_score,
        }
        if near is None or near_score > near["near_score"]:
            near = cand
        if fails:
            continue

        # Prefer robust positive CLV with more observations.
        score = total["clv"] * math.sqrt(total["bets"])
        cand["score"] = score
        if best is None or score > best["score"]:
            best = cand
    return best, near


def _market_logloss(rows):
    return _logloss([pricing.devig(r["op"]) for r in rows], [r["y"] for r in rows])


def _run_league(matches, odds_rows, shots):
    data = _dataset(matches, odds_rows, shots)
    hyper = _early_hyper(data)
    if hyper is None:
        return {
            "validated": False,
            "reason": "too little early walk-forward data",
            "samples": len(data),
        }

    tune = {
        2022: _rolling_eval(data, 2022, hyper),
        2023: _rolling_eval(data, 2023, hyper),
    }
    if any(len(v) < 60 for v in tune.values()):
        return {
            "validated": False,
            "reason": "too little tune data",
            "samples": len(data),
            "counts": {str(k): len(v) for k, v in tune.items()},
            "hyper": hyper,
        }

    gate, near = _choose_gate(tune)

    hold_rows = [r for r in data if r["season"] == 2024]
    hold_eval = _rolling_eval(data, 2024, hyper)
    diag_rows = [r for r in data if r["season"] == 2025]
    diag_eval = _rolling_eval(data, 2025, hyper)

    if len(hold_eval) < 80:
        return {
            "validated": False,
            "reason": "too little strict 2024 holdout data",
            "samples": len(data),
            "hyper": hyper,
            "gate": gate,
            "near_miss_gate": near,
            "holdout_n": len(hold_eval),
        }

    use_gate = gate or near
    hold = _entry_stats(
        hold_eval, use_gate["edge"], use_gate["cap"], use_gate["side"]
    ) if use_gate else {
        "bets": 0, "clv": 0.0, "median_clv": 0.0,
        "positive_clv_rate": 0.0, "roi": 0.0,
    }
    diag = _entry_stats(
        diag_eval, use_gate["edge"], use_gate["cap"], use_gate["side"]
    ) if use_gate and diag_eval else {
        "bets": 0, "clv": 0.0, "median_clv": 0.0,
        "positive_clv_rate": 0.0, "roi": 0.0,
    }

    hp = _fit_predict(
        [r for r in data if r["season"] <= 2023],
        hold_rows,
        hyper["l2"],
        hyper["calib"],
    )
    hold_model_ll = _logloss(hp, [r["y"] for r in hold_rows]) if hold_rows else 9.0
    hold_market_ll = _market_logloss(hold_rows) if hold_rows else 9.0

    gate_robust = gate is not None
    strategy_validated = bool(
        gate_robust
        and hold["bets"] >= 12
        and hold["clv"] > 0
        and hold["median_clv"] >= 0
        and hold["positive_clv_rate"] >= 0.52
    )

    return {
        "validated": strategy_validated,
        "strategy_validated": strategy_validated,
        "model_beats_opening_logloss": hold_model_ll < hold_market_ll,
        "samples": len(data),
        "hyper": hyper,
        "gate": gate,
        "near_miss_gate": near,
        "strict_holdout_2024": hold,
        "strict_holdout_logloss": {
            "model": hold_model_ll,
            "opening": hold_market_ll,
            "gain": hold_market_ll - hold_model_ll,
        },
        "diagnostic_only_2025": diag,
    }


def run(out: Path = OUT):
    # Existing deployments use either name. Keep this research path read-only.
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    result = {
        "_method": "M17.2 focused away-side nonlinear rolling classifier; no market features",
        "_focus": {
            "side": SIDE,
            "max_odds": ODDS_CAP,
            "leagues": list(FOCUS),
        },
        "_splits": {
            "hyper_A": "train<=2019 validate=2020 outcome logloss",
            "hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "rolling OOS 2022 + 2023 CLV",
            "strict_holdout": "fit<=2023 evaluate 2024",
            "diagnostic_only": "fit<=2024 evaluate 2025",
        },
        "_release_rule": "gate robust on 2022+2023 AND 2024 holdout >=12 bets, mean CLV>0, median CLV>=0, positive CLV rate>=52%",
    }
    log = ["M17.2: focused Bundesliga/SerieA away-side strict OOS research"]

    for league, code in FOCUS.items():
        matches, odds_rows, _ = load_real_xg(code)
        shots = load_real_shots(code)
        r = _run_league(matches, odds_rows, shots)
        result[league] = r

        g = r.get("gate") or r.get("near_miss_gate") or {}
        ts = (g.get("stats") or {})
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        log.append(
            f"{league}: gate={'OK' if r.get('gate') else 'NONE'} "
            f"edge={g.get('edge')} cap={g.get('cap')} side={g.get('side')} | "
            f"tune n={ts.get('bets',0)} CLV={ts.get('clv',0)*100:+.2f}% | "
            f"hold n={hs.get('bets',0)} CLV={hs.get('clv',0)*100:+.2f}% "
            f"med={hs.get('median_clv',0)*100:+.2f}% "
            f"pos={hs.get('positive_clv_rate',0)*100:.1f}% | "
            f"dLL={ll.get('gain',0):+.4f} -> "
            + ("VALIDATED" if r.get("validated") else "NO RELEASE")
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log


if __name__ == "__main__":
    for line in run():
        print(line)
