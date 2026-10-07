"""M17.10: adaptive previous-season outcome-prior calibration for Portugal.

The M17.9 diagnostics show season-dependent class drift rather than one stable
home/draw/away bias. M17.10 therefore removes the fixed class-bias layer and
shrinks probabilities toward the immediately PREVIOUS season's empirical
H/D/A outcome rates.

Leakage safety:
- season Y uses only season Y-1 outcome frequencies
- if Y-1 is unavailable, fall back to the full training-only class prior
- shrink weight is selected only on 2020/2021 OOS outcome logloss
- 2022/2023 remain CLV gate seasons
- 2024 remains untouched strict holdout
- 2025 remains diagnostic only

No bookmaker odds or market probabilities are model features.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .m14_research import load_league, train_proxy
from .m17_1_research import L2_GRID, CALIB, load_real_shots, _calibrate, _logloss
from .m17_5_research import START_YEAR, END_YEAR, mongo_coverage
from .m17_8_research import (
    _class_prior,
    _shrink,
    _raw_predict,
    _attach,
    _league_run,
)

OUT = Path("data/m17_10_validation.json")
FOCUS = {"primeira": "P1"}
RECENT_SHRINK_GRID = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40)


def _previous_season_prior(train: list[dict], target_year: int) -> list[float]:
    recent = [r for r in train if int(r["season"]) == int(target_year) - 1]
    if len(recent) >= 80:
        return _class_prior(recent)
    return _class_prior(train)


def _fit_predict(
    train: list[dict],
    test: list[dict],
    target_year: int,
    l2: float,
    calib: float,
    recent_shrink: float,
) -> list[list[float]]:
    prior = _previous_season_prior(train, target_year)
    raw = _raw_predict(train, test, l2)
    return [
        _shrink(_calibrate(p, calib), prior, recent_shrink)
        for p in raw
    ]


def _early_hyper(data: list[dict]):
    folds = [
        (
            [r for r in data if r["season"] <= 2019],
            [r for r in data if r["season"] == 2020],
            2020,
        ),
        (
            [r for r in data if r["season"] <= 2020],
            [r for r in data if r["season"] == 2021],
            2021,
        ),
    ]
    if any(len(tr) < 400 or len(va) < 80 for tr, va, _ in folds):
        return None

    best = None
    for l2 in L2_GRID:
        raw = []
        for tr, va, year in folds:
            pp = _raw_predict(tr, va, l2)
            prior = _previous_season_prior(tr, year)
            raw.append((va, pp, prior))

        for calib in CALIB:
            calibrated = [
                (va, [_calibrate(p, calib) for p in pp], prior)
                for va, pp, prior in raw
            ]
            for recent_shrink in RECENT_SHRINK_GRID:
                losses = [
                    _logloss(
                        [_shrink(p, prior, recent_shrink) for p in pp],
                        [r["y"] for r in va],
                    )
                    for va, pp, prior in calibrated
                ]
                score = sum(losses) / len(losses)
                if best is None or score < best["cv_logloss"]:
                    best = {
                        "l2": l2,
                        "calib": calib,
                        "recent_shrink": recent_shrink,
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
            year,
            hyper["l2"],
            hyper["calib"],
            hyper["recent_shrink"],
        ),
    )


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    profile = mongo_coverage()
    proxy = train_proxy()

    result = {
        "_method": (
            "M17.10 Portugal-only M17.7 base + adaptive previous-season "
            "H/D/A prior shrinkage; no market features"
        ),
        "_focus": FOCUS,
        "_probability_control": (
            "temperature + shrink toward immediately previous season outcome "
            "rates; weight selected only on 2020/2021 OOS logloss"
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

    log = [f"M17.10 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

    for league, code in FOCUS.items():
        try:
            matches, rows, cov = load_league(
                code, proxy, start_year=START_YEAR, end_year=END_YEAR
            )
            shots = load_real_shots(
                code, start_year=START_YEAR, end_year=END_YEAR
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
            f"recent_shrink={h.get('recent_shrink')} "
            f"earlyLL={h.get('cv_logloss',0):.4f} | "
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
