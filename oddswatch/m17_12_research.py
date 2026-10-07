"""M17.12: offseason decay for structural attack/defense ratings.

M17.11 materially improved untouched 2024 outcome logloss (0.9376 vs 0.9492
for M17.8) but its away entry strategy still failed 2024 CLV. A likely
structural cause is carrying too much latent team strength unchanged through
the summer break despite transfers, coaching changes and promoted/relegated
teams.

M17.12 keeps the M17.11 structural model and selects ONLY the offseason carry
factors on early 2020/2021 OOS outcome logloss:
- fast structural ratings: stronger offseason reset
- slow structural ratings: more persistent underlying team strength

No bookmaker odds or market probabilities are model features.
Carry selection never sees 2022/2023 CLV, 2024 holdout, or 2025 diagnostics.

Chronology:
- carry + L2 + calibration: 2020/2021 OOS outcome logloss
- entry gate: rolling OOS 2022 + 2023 CLV
- strict holdout: rolling OOS 2024
- 2025: diagnostic only
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .m14_research import load_league, train_proxy
from .m17_1_research import load_real_shots, _logloss, _entry_stats
from .m17_5_research import (
    START_YEAR,
    END_YEAR,
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

OUT = Path("data/m17_12_validation.json")
FOCUS = {"primeira": "P1"}

# Candidate structural persistence chosen ONLY by early outcome logloss.
# Fast ratings represent current form and are allowed to reset more heavily.
# Slow ratings represent underlying strength and therefore retain more.
CARRY_GRID = (
    (1.00, 1.00),
    (0.65, 0.85),
    (0.40, 0.75),
    (0.20, 0.60),
    (0.00, 0.50),
)


def _build_with_carry(matches, odds_rows, shots, fast_carry, slow_carry):
    base = build_structural_dataset(
        matches,
        odds_rows,
        shots,
        season_fast_carry=fast_carry,
        season_slow_carry=slow_carry,
    )
    venue_priors = build_previous_season_priors(matches)
    data, venue_cov = augment_with_priors(base, venue_priors)
    xg_priors = build_previous_season_xg_priors(matches)
    data, xg_cov = augment_with_xg_priors(data, xg_priors)
    return data, venue_cov, xg_cov


def _select_carry(matches, odds_rows, shots):
    candidates = []
    for fast_carry, slow_carry in CARRY_GRID:
        data, venue_cov, xg_cov = _build_with_carry(
            matches, odds_rows, shots, fast_carry, slow_carry
        )
        hyper = _early_hyper(data)
        row = {
            "fast_carry": fast_carry,
            "slow_carry": slow_carry,
            "samples": len(data),
            "hyper": hyper,
            "cv_logloss": hyper["cv_logloss"] if hyper else 9.0,
        }
        candidates.append((row, data, venue_cov, xg_cov))

    valid = [x for x in candidates if x[0]["hyper"] is not None]
    if not valid:
        return None, candidates
    best = min(valid, key=lambda x: x[0]["cv_logloss"])
    return best, candidates


def _league_run(matches, odds_rows, shots, cov):
    best, candidates = _select_carry(matches, odds_rows, shots)
    result = {
        "coverage": cov,
        "carry_candidates": [x[0] for x in candidates],
    }

    if cov.get("proxy_coverage", 0.0) < 0.70:
        result.update({
            "validated": False,
            "reason": "historical shot/corner proxy coverage <70%",
        })
        return result

    if best is None:
        result.update({
            "validated": False,
            "reason": "no carry candidate has enough strict early data",
        })
        return result

    chosen, data, venue_cov, xg_cov = best
    hyper = chosen["hyper"]
    result.update({
        "samples": len(data),
        "selected_carry": {
            "fast": chosen["fast_carry"],
            "slow": chosen["slow_carry"],
            "early_cv_logloss": chosen["cv_logloss"],
        },
        "hyper": hyper,
        "previous_season_prior_coverage": venue_cov,
        "previous_season_xg_prior_coverage": xg_cov,
    })

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
        _entry_stats(hold_eval, use_gate["edge"], use_gate["cap"], use_gate["side"])
        if use_gate and hold_eval
        else dict(empty)
    )
    diag = (
        _entry_stats(diag_eval, use_gate["edge"], use_gate["cap"], use_gate["side"])
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
            "M17.12 M17.11 structural opponent-adjusted attack/defense ratings "
            "+ early-logloss-selected offseason fast/slow carry; no market features"
        ),
        "_focus": FOCUS,
        "_carry_grid": [
            {"fast": f, "slow": s} for f, s in CARRY_GRID
        ],
        "_splits": {
            "hyper_and_carry_A": "train<=2019 validate=2020 outcome logloss",
            "hyper_and_carry_B": "train<=2020 validate=2021 outcome logloss",
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

    log = [f"M17.12 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

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
        sel = r.get("selected_carry") or {}
        h = r.get("hyper") or {}
        log.append(
            f"{league}: carry={sel.get('fast')}/{sel.get('slow')} "
            f"l2={h.get('l2')} calib={h.get('calib')} "
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
