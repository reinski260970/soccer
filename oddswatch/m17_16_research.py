"""M17.16: nested CLV gate validation on frozen M17.11 probabilities.

Purpose
-------
M17.11-M17.15 repeatedly found strong 2022+2023 tune CLV but failed the
untouched 2024 holdout. The likely issue is entry-gate overfitting when both
2022 and 2023 are used jointly to choose the gate.

M17.16 strengthens chronology:
- probability model hyperparameters: 2020/2021 OOS outcome logloss
- ENTRY TUNE ONLY: 2022
- ENTRY VALIDATION ONLY: 2023
- strict holdout: 2024
- diagnostic only: 2025

The fair-probability model is frozen M17.11.
No bookmaker odds or market probabilities are model features.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from .m14_research import load_league, train_proxy
from .m17_1_research import load_real_shots, _logloss, _entry_stats
from .m17_5_research import (
    START_YEAR,
    END_YEAR,
    _early_hyper,
    _rolling_eval,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import build_previous_season_xg_priors, augment_with_xg_priors
from .m17_8_research import _prob_diagnostics
from .m17_11_research import build_structural_dataset

OUT = Path("data/m17_16_validation.json")
FOCUS = {"primeira": "P1"}

EDGE_GRID = (0.02, 0.03, 0.05, 0.075, 0.10)
ODDS_CAP_GRID = (2.0, 2.5, 3.0, 4.0)
SIDE = "away"


def _tune_gate_2022(rows: list[dict]):
    best = None
    near = None

    for edge in EDGE_GRID:
        for cap in ODDS_CAP_GRID:
            s = _entry_stats(rows, edge, cap, SIDE)
            fails = []
            if s["bets"] < 20:
                fails.append("2022_bets<20")
            if s["clv"] <= 0:
                fails.append("2022_mean_clv<=0")
            if s["median_clv"] <= 0:
                fails.append("2022_median_clv<=0")
            if s["positive_clv_rate"] < 0.55:
                fails.append("2022_positive_clv_rate<55%")

            score = (
                s["clv"] * math.sqrt(max(s["bets"], 1))
                * (0.5 + s["positive_clv_rate"])
            )
            cand = {
                "edge": edge,
                "cap": cap,
                "side": SIDE,
                "stats_2022": s,
                "fails_2022": fails,
                "score_2022": score,
            }

            if near is None or score > near["score_2022"]:
                near = cand
            if fails:
                continue
            if best is None or score > best["score_2022"]:
                best = cand

    return best, near


def _validate_gate_2023(rows: list[dict], gate: dict | None) -> tuple[bool, dict]:
    if not gate:
        return False, {
            "bets": 0,
            "clv": 0.0,
            "median_clv": 0.0,
            "positive_clv_rate": 0.0,
            "roi": 0.0,
            "fails": ["no_2022_gate"],
        }

    s = _entry_stats(rows, gate["edge"], gate["cap"], gate["side"])
    fails = []
    if s["bets"] < 15:
        fails.append("2023_bets<15")
    if s["clv"] <= 0:
        fails.append("2023_mean_clv<=0")
    if s["median_clv"] <= 0:
        fails.append("2023_median_clv<=0")
    if s["positive_clv_rate"] < 0.52:
        fails.append("2023_positive_clv_rate<52%")

    out = dict(s)
    out["fails"] = fails
    return not fails, out


def _build_data(matches, odds_rows, shots):
    base = build_structural_dataset(
        matches,
        odds_rows,
        shots,
        season_fast_carry=1.0,
        season_slow_carry=1.0,
    )
    venue_priors = build_previous_season_priors(matches)
    data, venue_cov = augment_with_priors(base, venue_priors)
    xg_priors = build_previous_season_xg_priors(matches)
    data, xg_cov = augment_with_xg_priors(data, xg_priors)
    return data, venue_cov, xg_cov


def _league_run(matches, odds_rows, shots, cov):
    data, venue_cov, xg_cov = _build_data(matches, odds_rows, shots)
    result = {
        "samples": len(data),
        "coverage": cov,
        "previous_season_prior_coverage": venue_cov,
        "previous_season_xg_prior_coverage": xg_cov,
        "model": "frozen M17.11 structural probability model",
    }

    hyper = _early_hyper(data)
    result["hyper"] = hyper
    if hyper is None:
        result.update({"validated": False, "reason": "too little early OOS data"})
        return result

    eval_2022 = _rolling_eval(data, 2022, hyper)
    eval_2023 = _rolling_eval(data, 2023, hyper)
    hold_eval = _rolling_eval(data, 2024, hyper)
    diag_eval = _rolling_eval(data, 2025, hyper)

    if min(len(eval_2022), len(eval_2023), len(hold_eval)) < 60:
        result.update({"validated": False, "reason": "too little strict OOS data"})
        return result

    tuned_gate, near = _tune_gate_2022(eval_2022)
    gate_valid_2023, validation_2023 = _validate_gate_2023(eval_2023, tuned_gate)

    # Only a gate that survived 2023 may be evaluated as a strategy on 2024.
    release_gate = tuned_gate if gate_valid_2023 else None
    diagnostic_gate = tuned_gate or near

    empty = {
        "bets": 0,
        "clv": 0.0,
        "median_clv": 0.0,
        "positive_clv_rate": 0.0,
        "roi": 0.0,
    }

    if diagnostic_gate:
        hold = _entry_stats(
            hold_eval,
            diagnostic_gate["edge"],
            diagnostic_gate["cap"],
            diagnostic_gate["side"],
        )
        diag = _entry_stats(
            diag_eval,
            diagnostic_gate["edge"],
            diagnostic_gate["cap"],
            diagnostic_gate["side"],
        )
    else:
        hold = dict(empty)
        diag = dict(empty)

    hold_rows = [r for r in data if r["season"] == 2024]
    hold_model_ll = _logloss(
        [r["p"] for r in hold_eval],
        [r["y"] for r in hold_eval],
    )
    hold_market_ll = _market_logloss(hold_rows)

    strategy_ok = bool(
        release_gate is not None
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
        "tuned_gate_2022": tuned_gate,
        "near_miss_2022": near,
        "entry_validation_2023": validation_2023,
        "gate_survived_2023": gate_valid_2023,
        "gate": release_gate,
        "strict_holdout_2024": hold,
        "strict_holdout_logloss": {
            "model": hold_model_ll,
            "opening": hold_market_ll,
            "gain": hold_market_ll - hold_model_ll,
        },
        "diagnostic_only_2025": diag,
        "probability_diagnostics": {
            "2022": _prob_diagnostics(eval_2022),
            "2023": _prob_diagnostics(eval_2023),
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
            "M17.16 frozen M17.11 fair model + nested entry chronology: "
            "2022 tune, 2023 gate validation, 2024 strict holdout"
        ),
        "_focus": FOCUS,
        "_entry_rule": (
            "away edge/cap chosen ONLY on 2022 CLV; identical gate must pass "
            "2023 CLV before it is eligible for 2024 release evaluation"
        ),
        "_splits": {
            "model_hyper_A": "train<=2019 validate=2020 outcome logloss",
            "model_hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "2022 only",
            "entry_validation": "2023 only",
            "strict_holdout": "2024",
            "diagnostic_only": "2025",
        },
        "_release_rule": (
            "2022 gate passes tune requirements + identical gate passes 2023 + "
            "2024 >=15 bets, mean/median CLV>0, positive CLV rate>=52%, "
            "AND model 2024 logloss < Pinnacle opening"
        ),
        "mongo_profile": profile,
        "leagues": {},
    }

    log = [f"M17.16 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

    for league, code in FOCUS.items():
        try:
            matches, rows, cov = load_league(
                code, proxy, start_year=START_YEAR, end_year=END_YEAR
            )
            shots = load_real_shots(code, start_year=START_YEAR, end_year=END_YEAR)
            r = _league_run(matches, rows, shots, cov)
        except Exception as exc:
            r = {
                "validated": False,
                "reason": f"load/research failed: {type(exc).__name__}: {exc}",
            }

        result["leagues"][league] = r
        g = r.get("tuned_gate_2022") or r.get("near_miss_2022") or {}
        s22 = g.get("stats_2022") or {}
        s23 = r.get("entry_validation_2023") or {}
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        log.append(
            f"{league}: 2022 gate edge={g.get('edge')} cap={g.get('cap')} "
            f"n={s22.get('bets',0)} CLV={s22.get('clv',0)*100:+.2f}% | "
            f"2023 pass={r.get('gate_survived_2023')} "
            f"n={s23.get('bets',0)} CLV={s23.get('clv',0)*100:+.2f}% | "
            f"hold n={hs.get('bets',0)} CLV={hs.get('clv',0)*100:+.2f}% "
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
