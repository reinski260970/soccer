"""M17.14: structural xG -> Poisson 1X2 transforms as secondary features.

Poisson is NOT the main model.

The main probability model remains the M17 multinomial classifier selected by
outcome logloss. M17.14 only gives that classifier nonlinear football-specific
transforms of the leakage-safe M17.11 structural expected-goal intensities.

Inputs remain independent of bookmaker prices:
- rolling goals/xG/shots/SOT/form/rest
- opponent-adjusted fast/slow attack and defense ratings
- Y-1 venue and xG/luck priors
- fast/slow Poisson 1X2 probabilities derived ONLY from structural xG

Market prices enter only after fair probabilities exist for CLV evaluation.
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
    _choose_gate,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import build_previous_season_xg_priors, augment_with_xg_priors
from .m17_8_research import _prob_diagnostics
from .m17_11_research import build_structural_dataset

OUT = Path("data/m17_14_validation.json")
FOCUS = {"primeira": "P1"}

BASE_FEATURE_COUNT = 17
STRUCT_HOME_FAST = BASE_FEATURE_COUNT + 0
STRUCT_AWAY_FAST = BASE_FEATURE_COUNT + 1
STRUCT_HOME_SLOW = BASE_FEATURE_COUNT + 4
STRUCT_AWAY_SLOW = BASE_FEATURE_COUNT + 5
MAX_GOALS = 10


def _poisson_pmf(lam: float, k: int) -> float:
    lam = max(0.05, min(6.0, float(lam)))
    return math.exp(-lam) * (lam ** int(k)) / math.factorial(int(k))


def _poisson_1x2(home_xg: float, away_xg: float) -> list[float]:
    """Truncated independent Poisson transform, renormalized to 1."""
    hp = [_poisson_pmf(home_xg, k) for k in range(MAX_GOALS + 1)]
    ap = [_poisson_pmf(away_xg, k) for k in range(MAX_GOALS + 1)]
    out = [0.0, 0.0, 0.0]
    for h, ph in enumerate(hp):
        for a, pa in enumerate(ap):
            p = ph * pa
            if h > a:
                out[0] += p
            elif h == a:
                out[1] += p
            else:
                out[2] += p
    z = sum(out)
    if z <= 0:
        return [1 / 3, 1 / 3, 1 / 3]
    return [x / z for x in out]


def augment_poisson_features(data: list[dict]) -> list[dict]:
    out = []
    for r in data:
        x = list(r["x"])
        hf = x[STRUCT_HOME_FAST]
        af = x[STRUCT_AWAY_FAST]
        hs = x[STRUCT_HOME_SLOW]
        ass = x[STRUCT_AWAY_SLOW]

        pf = _poisson_1x2(hf, af)
        ps = _poisson_1x2(hs, ass)
        pm = [(a + b) / 2.0 for a, b in zip(pf, ps)]

        z = dict(r)
        # Secondary transforms only. Classifier remains the final model.
        z["x"] = x + pf + ps + pm
        z["poisson_fast"] = pf
        z["poisson_slow"] = ps
        out.append(z)
    return out


def _build_data(matches, odds_rows, shots):
    base = build_structural_dataset(
        matches,
        odds_rows,
        shots,
        season_fast_carry=1.0,
        season_slow_carry=1.0,
    )
    base = augment_poisson_features(base)
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
        "poisson_role": "secondary nonlinear features only; classifier is final model",
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
        if use_gate and hold_eval else dict(empty)
    )
    diag = (
        _entry_stats(diag_eval, use_gate["edge"], use_gate["cap"], use_gate["side"])
        if use_gate and diag_eval else dict(empty)
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
            "M17.14 M17.11 structural model + fast/slow Poisson 1X2 secondary "
            "features; multinomial classifier remains final model; no market features"
        ),
        "_focus": FOCUS,
        "_poisson_role": "feature transform only, never main model",
        "_splits": {
            "model_hyper_A": "train<=2019 validate=2020 outcome logloss",
            "model_hyper_B": "train<=2020 validate=2021 outcome logloss",
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

    log = [f"M17.14 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

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
