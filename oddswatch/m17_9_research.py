"""M17.9: class-bias calibration for the Portugal candidate.

Builds on M17.8 and keeps every release rule unchanged.

M17.8 slightly improved Portugal 2024 outcome logloss but remained worse than
Pinnacle opening and still had negative holdout CLV. M17.9 therefore adds a
small class-specific calibration layer after temperature calibration/shrinkage:
- home is the reference class
- draw multiplier is selected on 2020/2021 OOS outcome logloss
- away multiplier is selected on 2020/2021 OOS outcome logloss

No bookmaker price or market probability is a model feature. Opening/closing
odds remain validation-only after probabilities are produced.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .m14_research import load_league, train_proxy
from .m17_1_research import (
    L2_GRID,
    CALIB,
    load_real_shots,
    _calibrate,
    _logloss,
)
from .m17_5_research import START_YEAR, END_YEAR, mongo_coverage
from .m17_8_research import (
    SHRINK_GRID,
    _class_prior,
    _shrink,
    _raw_predict,
    _attach,
    _league_run,
)

OUT = Path("data/m17_9_validation.json")
FOCUS = {"primeira": "P1"}

DRAW_SCALE_GRID = (0.90, 0.95, 1.00, 1.05, 1.10)
AWAY_SCALE_GRID = (0.95, 1.00, 1.05)


def _class_bias(
    p: list[float],
    draw_scale: float,
    away_scale: float,
) -> list[float]:
    q = [
        max(float(p[0]), 1e-12),
        max(float(p[1]) * float(draw_scale), 1e-12),
        max(float(p[2]) * float(away_scale), 1e-12),
    ]
    z = sum(q)
    return [x / z for x in q]


def _fit_predict(
    train: list[dict],
    test: list[dict],
    l2: float,
    calib: float,
    shrink: float,
    draw_scale: float,
    away_scale: float,
) -> list[list[float]]:
    prior = _class_prior(train)
    raw = _raw_predict(train, test, l2)
    out = []
    for p in raw:
        p = _calibrate(p, calib)
        p = _shrink(p, prior, shrink)
        p = _class_bias(p, draw_scale, away_scale)
        out.append(p)
    return out


def _early_hyper(data: list[dict]):
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
                shrunk = [
                    (va, [_shrink(p, prior, shrink) for p in pp])
                    for va, pp, prior in calibrated
                ]
                for draw_scale in DRAW_SCALE_GRID:
                    for away_scale in AWAY_SCALE_GRID:
                        losses = [
                            _logloss(
                                [
                                    _class_bias(p, draw_scale, away_scale)
                                    for p in pp
                                ],
                                [r["y"] for r in va],
                            )
                            for va, pp in shrunk
                        ]
                        score = sum(losses) / len(losses)
                        if best is None or score < best["cv_logloss"]:
                            best = {
                                "l2": l2,
                                "calib": calib,
                                "shrink": shrink,
                                "draw_scale": draw_scale,
                                "away_scale": away_scale,
                                "cv_logloss": score,
                                "fold_logloss": losses,
                            }
    return best


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
            hyper["draw_scale"],
            hyper["away_scale"],
        ),
    )


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    profile = mongo_coverage()
    proxy = train_proxy()

    result = {
        "_method": (
            "M17.9 Portugal-only M17.8 + early-OOS draw/away class-bias "
            "calibration; no market features"
        ),
        "_focus": FOCUS,
        "_probability_control": (
            "temperature + training-only base-rate shrink + draw/away multipliers; "
            "all selected solely on 2020/2021 OOS outcome logloss"
        ),
        "_splits": {
            "hyper_A": "train<=2019 validate=2020 outcome logloss",
            "hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "rolling OOS 2022 + 2023 CLV",
            "strict_holdout": "rolling OOS 2024",
            "diagnostic_only": "rolling OOS 2025",
        },
        "_release_rule": (
            "unchanged: robust 2022+2023 CLV gate AND 2024 >=15 bets, "
            "mean/median CLV>0, positive CLV rate>=52%, "
            "AND model 2024 logloss < Pinnacle opening"
        ),
        "mongo_profile": profile,
        "leagues": {},
    }

    log = [f"M17.9 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

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
            r = _league_run(
                matches,
                rows,
                shots,
                cov,
                hyper_fn=_early_hyper,
                eval_fn=_rolling_eval,
            )
        except Exception as exc:
            r = {
                "validated": False,
                "reason": f"load/research failed: {type(exc).__name__}: {exc}",
            }

        result["leagues"][league] = r
        gate = r.get("gate") or r.get("near_miss_gate") or {}
        ts = gate.get("stats") or {}
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        h = r.get("hyper") or {}
        log.append(
            f"{league}: l2={h.get('l2')} calib={h.get('calib')} "
            f"shrink={h.get('shrink')} draw={h.get('draw_scale')} "
            f"away={h.get('away_scale')} earlyLL={h.get('cv_logloss',0):.4f} | "
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
