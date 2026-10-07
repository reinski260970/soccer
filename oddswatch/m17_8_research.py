"""M17.8: probability shrinkage for better OOS outcome logloss.

Builds on M17.7 without adding bookmaker information to the model.

What changes:
- keeps M17.7 leakage-safe rolling features and previous-season priors
- keeps previous-season xG/xGA and goals-minus-xG luck context
- adds a post-model probability shrinkage toward TRAINING-ONLY class priors
- tunes shrinkage only on the early 2020/2021 outcome-logloss folds

Why:
M17.7 could create positive CLV in the 2022/2023 tune window for Portugal,
but failed the untouched 2024 holdout and lost to Pinnacle opening on logloss.
M17.8 therefore attacks probability overconfidence directly instead of loosening
entry or release gates.

No bookmaker odds are model features. Opening/closing prices are validation only.

Strict chronology:
- model hyperparameters incl. shrinkage: validate 2020 and 2021 outcome logloss
- entry gate: rolling OOS 2022 + 2023 CLV
- strict holdout: rolling OOS 2024
- 2025: diagnostic only
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .m14_research import load_league, train_proxy
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
from .m17_5_research import (
    START_YEAR,
    END_YEAR,
    _choose_gate,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import (
    FOCUS,
    build_previous_season_xg_priors,
    augment_with_xg_priors,
)

OUT = Path("data/m17_8_validation.json")

# Small grid on purpose: regularization is selected only by early outcome
# logloss. 0.0 keeps the exact M17.7 probability surface as a candidate.
SHRINK_GRID = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40)


def _class_prior(rows: list[dict]) -> list[float]:
    """Training-only empirical H/D/A base rates with tiny Laplace smoothing."""
    counts = [1.0, 1.0, 1.0]
    for r in rows:
        y = int(r["y"])
        if 0 <= y <= 2:
            counts[y] += 1.0
    z = sum(counts)
    return [x / z for x in counts]


def _shrink(p: list[float], prior: list[float], weight: float) -> list[float]:
    """Convex probability shrinkage; never uses market probabilities."""
    w = max(0.0, min(1.0, float(weight)))
    q = [(1.0 - w) * float(pi) + w * float(pr) for pi, pr in zip(p, prior)]
    z = sum(max(x, 1e-12) for x in q)
    return [max(x, 1e-12) / z for x in q]


def _raw_predict(train: list[dict], test: list[dict], l2: float) -> list[list[float]]:
    mean, sd = _standardizer([r["x"] for r in train])
    xtr = _tx([r["x"] for r in train], mean, sd)
    xte = _tx([r["x"] for r in test], mean, sd)
    w = _fit(xtr, [r["y"] for r in train], l2)
    return [_pred(w, x) for x in xte]


def _fit_predict(
    train: list[dict],
    test: list[dict],
    l2: float,
    calib: float,
    shrink: float,
) -> list[list[float]]:
    prior = _class_prior(train)
    raw = _raw_predict(train, test, l2)
    return [_shrink(_calibrate(p, calib), prior, shrink) for p in raw]


def _early_hyper(data: list[dict]):
    """Choose L2/calibration/shrinkage only by early OOS outcome logloss."""
    folds = [
        (
            [r for r in data if r["season"] <= 2019],
            [r for r in data if r["season"] == 2020],
        ),
        (
            [r for r in data if r["season"] <= 2020],
            [r for r in data if r["season"] == 2021],
        ),
    ]
    if any(len(tr) < 400 or len(va) < 80 for tr, va in folds):
        return None

    best = None
    for l2 in L2_GRID:
        raw = []
        for tr, va in folds:
            pp = _raw_predict(tr, va, l2)
            raw.append((tr, va, pp, _class_prior(tr)))

        for calib in CALIB:
            calibrated = [
                (va, [_calibrate(p, calib) for p in pp], prior)
                for _, va, pp, prior in raw
            ]
            for shrink in SHRINK_GRID:
                losses = [
                    _logloss(
                        [_shrink(p, prior, shrink) for p in pp],
                        [r["y"] for r in va],
                    )
                    for va, pp, prior in calibrated
                ]
                score = sum(losses) / len(losses)
                if best is None or score < best["cv_logloss"]:
                    best = {
                        "l2": l2,
                        "calib": calib,
                        "shrink": shrink,
                        "cv_logloss": score,
                        "fold_logloss": losses,
                    }
    return best


def _attach(rows: list[dict], probs: list[list[float]]) -> list[dict]:
    out = []
    for r, p in zip(rows, probs):
        z = dict(r)
        z["p"] = p
        out.append(z)
    return out


def _prob_diagnostics(rows: list[dict]) -> dict:
    """Aggregate outcome calibration only; never used for hyper/gate selection."""
    if not rows:
        return {
            "n": 0,
            "avg_pred": [0.0, 0.0, 0.0],
            "actual_rate": [0.0, 0.0, 0.0],
            "gap_pred_minus_actual": [0.0, 0.0, 0.0],
            "logloss": 0.0,
        }
    n = len(rows)
    avg = [
        sum(float(r["p"][k]) for r in rows) / n
        for k in range(3)
    ]
    actual = [
        sum(1 for r in rows if int(r["y"]) == k) / n
        for k in range(3)
    ]
    return {
        "n": n,
        "avg_pred": avg,
        "actual_rate": actual,
        "gap_pred_minus_actual": [avg[k] - actual[k] for k in range(3)],
        "logloss": _logloss([r["p"] for r in rows], [r["y"] for r in rows]),
    }


def _rolling_eval(data: list[dict], year: int, hyper: dict) -> list[dict]:
    train = [r for r in data if r["season"] <= year - 1]
    test = [r for r in data if r["season"] == year]
    if len(train) < 500 or len(test) < 60:
        return []
    return _attach(
        test,
        _fit_predict(
            train,
            test,
            hyper["l2"],
            hyper["calib"],
            hyper["shrink"],
        ),
    )


def _league_run(matches, odds_rows, shots, cov, hyper_fn=None, eval_fn=None):
    hyper_fn = hyper_fn or _early_hyper
    eval_fn = eval_fn or _rolling_eval
    base = build_dataset(matches, odds_rows, shots)

    venue_priors = build_previous_season_priors(matches)
    data, venue_cov = augment_with_priors(base, venue_priors)

    xg_priors = build_previous_season_xg_priors(matches)
    data, xg_cov = augment_with_xg_priors(data, xg_priors)

    result = {
        "samples": len(data),
        "coverage": cov,
        "previous_season_prior_coverage": venue_cov,
        "previous_season_xg_prior_coverage": xg_cov,
    }

    if cov.get("proxy_coverage", 0.0) < 0.70:
        result.update({
            "validated": False,
            "reason": "historical shot/corner proxy coverage <70%",
        })
        return result

    hyper = hyper_fn(data)
    result["hyper"] = hyper
    if hyper is None:
        result.update({
            "validated": False,
            "reason": "too little strict early walk-forward data",
        })
        return result

    tune = {
        2022: eval_fn(data, 2022, hyper),
        2023: eval_fn(data, 2023, hyper),
    }
    if any(len(v) < 60 for v in tune.values()):
        result.update({
            "validated": False,
            "reason": "too little 2022/2023 OOS tune data",
            "tune_counts": {str(k): len(v) for k, v in tune.items()},
        })
        return result

    gate, near = _choose_gate(tune)
    hold_eval = eval_fn(data, 2024, hyper)
    diag_eval = eval_fn(data, 2025, hyper)
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
        "probability_diagnostics": {
            "2022": _prob_diagnostics(tune[2022]),
            "2023": _prob_diagnostics(tune[2023]),
            "2024": _prob_diagnostics(hold_eval),
            "2025": _prob_diagnostics(diag_eval),
        },
    })
    return result


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    profile = mongo_coverage()
    proxy = train_proxy()

    result = {
        "_method": (
            "M17.8 M17.7 priors + training-only empirical probability shrinkage; "
            "shrink selected solely by early outcome logloss; no market features"
        ),
        "_focus": FOCUS,
        "_proxy": {
            "n": proxy["n"],
            "rmse": proxy["rmse"],
            "beta": proxy["beta"],
            "features": proxy["features"],
        },
        "_probability_control": (
            "convex shrinkage toward training-only H/D/A base rates; "
            "weight tuned on 2020/2021 OOS logloss only"
        ),
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

    log = [f"M17.8 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

    for league, code in FOCUS.items():
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
        hyper = r.get("hyper") or {}
        log.append(
            f"{league}: samples={r.get('samples',0)} "
            f"shrink={hyper.get('shrink')} earlyLL={hyper.get('cv_logloss',0):.4f} | "
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
