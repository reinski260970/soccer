"""M17.13: structural-uncertainty CLV gate on the frozen M17.11 model.

Architecture principle
----------------------
Model selection and trading-entry selection are separated.

MODEL:
- exactly the M17.11 structural probability model
- no offseason carry tuning
- model hyperparameters selected only by 2020/2021 outcome logloss
- no bookmaker odds as model features

ENTRY GATE:
- selected only on rolling OOS 2022 + 2023 CLV
- adds one pre-match uncertainty dimension:
  disagreement between fast and slow structural expected xG
- threshold candidates are tune-sample quantiles, not hand-picked from 2024
- robust gate requires positive mean AND median CLV and >=52% positive CLV
  overall and within both 2022 and 2023
- 2024 remains untouched strict holdout

This tests whether structurally unstable model states should be WATCH rather
than PLAY, without changing fair probabilities.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from . import pricing
from .m14_research import load_league, train_proxy
from .m17_1_research import load_real_shots, _logloss
from .m17_5_research import (
    START_YEAR,
    END_YEAR,
    EDGE_GRID,
    ODDS_CAP,
    SIDES,
    _early_hyper,
    _rolling_eval,
    _choose_gate,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import build_previous_season_xg_priors, augment_with_xg_priors
from .m17_8_research import _prob_diagnostics
from .m17_11_research import build_structural_dataset

OUT = Path("data/m17_13_validation.json")
FOCUS = {"primeira": "P1"}
UNCERTAINTY_QUANTILES = (0.50, 0.65, 0.80, 1.00)


def _uncertainty(row: dict, side: str) -> float:
    if side == "home":
        return float(row.get("home_structural_uncertainty", 0.0))
    if side == "away":
        return float(row.get("away_structural_uncertainty", 0.0))
    return float(row.get("structural_uncertainty", 0.0))


def _quantile(values: list[float], q: float) -> float:
    vals = sorted(float(v) for v in values)
    if not vals:
        return 0.0
    if len(vals) == 1:
        return vals[0]
    pos = max(0.0, min(1.0, float(q))) * (len(vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vals[lo]
    w = pos - lo
    return vals[lo] * (1.0 - w) + vals[hi] * w


def _entry_stats_uncertainty(
    rows: list[dict],
    edge: float,
    cap: float,
    side: str,
    max_uncertainty: float,
) -> dict:
    idx = {"home": 0, "draw": 1, "away": 2}.get(side)
    bets = 0
    pnl = 0.0
    clv = []

    for r in rows:
        if _uncertainty(r, side) > max_uncertainty:
            continue
        pc = pricing.devig(r["cl"])
        for k in range(3):
            if idx is not None and k != idx:
                continue
            if r["p"][k] * r["op"][k] - 1.0 < edge:
                continue
            if r["op"][k] > cap:
                continue
            bets += 1
            pnl += r["op"][k] - 1.0 if r["y"] == k else -1.0
            clv.append(r["op"][k] * pc[k] - 1.0)

    vals = sorted(clv)
    if vals:
        n = len(vals)
        median = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
    else:
        median = 0.0

    return {
        "bets": bets,
        "clv": sum(vals) / len(vals) if vals else 0.0,
        "median_clv": median,
        "positive_clv_rate": (
            sum(v > 0 for v in vals) / len(vals) if vals else 0.0
        ),
        "roi": pnl / bets if bets else 0.0,
    }


def _choose_uncertainty_gate(tune_by_year: dict[int, list[dict]]):
    merged = [r for y in sorted(tune_by_year) for r in tune_by_year[y]]
    best = None
    near = None

    for side in SIDES:
        values = [_uncertainty(r, side) for r in merged]
        thresholds = []
        for q in UNCERTAINTY_QUANTILES:
            t = _quantile(values, q)
            if not any(abs(t - old_t) < 1e-12 for _, old_t in thresholds):
                thresholds.append((q, t))

        for q, threshold in thresholds:
            for edge in EDGE_GRID:
                for cap in ODDS_CAP:
                    total = _entry_stats_uncertainty(
                        merged, edge, cap, side, threshold
                    )
                    yearly = {
                        str(y): _entry_stats_uncertainty(
                            rows, edge, cap, side, threshold
                        )
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
                        if s["median_clv"] <= 0:
                            fails.append(f"{y}_median_clv<=0")
                        if s["positive_clv_rate"] < 0.52:
                            fails.append(f"{y}_positive_clv_rate<52%")

                    passed = 8 - min(len(fails), 8)
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
                        "uncertainty_quantile": q,
                        "max_uncertainty": threshold,
                        "stats": total,
                        "per_year": yearly,
                        "fails": fails,
                        "near_score": near_score,
                    }
                    if near is None or near_score > near["near_score"]:
                        near = cand
                    if fails:
                        continue

                    cand["score"] = (
                        total["clv"]
                        * math.sqrt(total["bets"])
                        * (0.5 + total["positive_clv_rate"])
                    )
                    if best is None or cand["score"] > best["score"]:
                        best = cand

    return best, near


def _build_data(matches, odds_rows, shots):
    # Frozen M17.11 model: no offseason carry decay.
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
    }

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
        })
        return result

    baseline_gate, baseline_near = _choose_gate(tune)
    gate, near = _choose_uncertainty_gate(tune)

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
        _entry_stats_uncertainty(
            hold_eval,
            use_gate["edge"],
            use_gate["cap"],
            use_gate["side"],
            use_gate["max_uncertainty"],
        )
        if use_gate and hold_eval
        else dict(empty)
    )
    diag = (
        _entry_stats_uncertainty(
            diag_eval,
            use_gate["edge"],
            use_gate["cap"],
            use_gate["side"],
            use_gate["max_uncertainty"],
        )
        if use_gate and diag_eval
        else dict(empty)
    )

    hold_rows = [r for r in data if r["season"] == 2024]
    hold_model_ll = (
        _logloss([r["p"] for r in hold_eval], [r["y"] for r in hold_eval])
        if hold_eval else 9.0
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
        "baseline_gate_without_uncertainty": baseline_gate,
        "baseline_near_miss": baseline_near,
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
            "M17.13 frozen M17.11 structural probability model + separate "
            "fast/slow structural-uncertainty CLV gate; no market model features"
        ),
        "_focus": FOCUS,
        "_model_rule": (
            "M17.11 fair probabilities chosen by outcome logloss only; "
            "no offseason carry variant"
        ),
        "_entry_rule": (
            "edge/cap/side + structural-uncertainty quantile selected only on "
            "2022/2023 CLV with strict per-year robustness"
        ),
        "_splits": {
            "model_hyper_A": "train<=2019 validate=2020 outcome logloss",
            "model_hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "rolling OOS 2022 + 2023 CLV",
            "strict_holdout": "rolling OOS 2024",
            "diagnostic_only": "rolling OOS 2025",
        },
        "_release_rule": (
            "unchanged: robust entry gate AND 2024 >=15 bets, mean/median CLV>0, "
            "positive CLV rate>=52%, AND model 2024 logloss < Pinnacle opening"
        ),
        "mongo_profile": profile,
        "leagues": {},
    }

    log = [f"M17.13 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

    for league, code in FOCUS.items():
        try:
            matches, rows, cov = load_league(
                code, proxy, start_year=START_YEAR, end_year=END_YEAR
            )
            shots = load_real_shots(
                code, start_year=START_YEAR, end_year=END_YEAR
            )
            r = _league_run(matches, rows, shots, cov)
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
            f"earlyLL={h.get('cv_logloss',0):.4f} | "
            f"gate={'OK' if r.get('gate') else 'NONE'} "
            f"{gate.get('side','-')} edge={gate.get('edge')} cap={gate.get('cap')} "
            f"q={gate.get('uncertainty_quantile')} "
            f"u<={gate.get('max_uncertainty')} "
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
