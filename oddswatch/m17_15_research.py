"""M17.15: structural-consensus entry gate on frozen M17.11 probabilities.

M17.11 remains the probability champion. This variant does NOT change fair
probabilities. It tests whether the unstable away-value strategy can be made
more robust by requiring the underlying fast and slow structural xG layers to
agree with the selected away side.

Model:
- exactly M17.11 structural probability model
- model hyperparameters selected only by 2020/2021 OOS outcome logloss

Entry gate:
- away side only (the existing M17.11 research candidate)
- opening EV threshold
- opening odds cap
- minimum consensus structural away xG margin:
      min(away_fast - home_fast, away_slow - home_slow)
- optional maximum fast/slow disagreement
- all entry parameters selected only on 2022 + 2023 CLV
- strict per-year robustness is required

2024 remains untouched strict holdout.
2025 remains diagnostic only.

No bookmaker odds or market probabilities are model features.
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
    _early_hyper,
    _rolling_eval,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import build_previous_season_xg_priors, augment_with_xg_priors
from .m17_8_research import _prob_diagnostics
from .m17_11_research import build_structural_dataset

OUT = Path("data/m17_15_validation.json")
FOCUS = {"primeira": "P1"}

# build_structural_dataset = 17 original M17.1 features + 17 structural features.
BASE_FEATURE_COUNT = 17
STRUCT_HOME_FAST = BASE_FEATURE_COUNT + 0
STRUCT_AWAY_FAST = BASE_FEATURE_COUNT + 1
STRUCT_HOME_SLOW = BASE_FEATURE_COUNT + 4
STRUCT_AWAY_SLOW = BASE_FEATURE_COUNT + 5

EDGE_GRID = (0.02, 0.03, 0.05, 0.075)
ODDS_CAP_GRID = (2.0, 2.5, 3.0)
MIN_CONSENSUS_MARGIN_GRID = (-0.15, -0.05, 0.0, 0.10, 0.20)
DISAGREEMENT_QUANTILES = (0.50, 0.75, 0.90, 1.00)


def _structural_gate_values(row: dict) -> tuple[float, float]:
    """Return consensus away margin and fast/slow directional disagreement."""
    x = row["x"]
    fast_margin = float(x[STRUCT_AWAY_FAST]) - float(x[STRUCT_HOME_FAST])
    slow_margin = float(x[STRUCT_AWAY_SLOW]) - float(x[STRUCT_HOME_SLOW])
    consensus = min(fast_margin, slow_margin)
    disagreement = abs(fast_margin - slow_margin)
    return consensus, disagreement


def _quantile(vals: list[float], q: float) -> float:
    if not vals:
        return float("inf")
    xs = sorted(float(x) for x in vals)
    if len(xs) == 1:
        return xs[0]
    pos = max(0.0, min(1.0, float(q))) * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def _entry_stats_consensus(
    rows: list[dict],
    edge: float,
    cap: float,
    min_consensus_margin: float,
    max_disagreement: float,
) -> dict:
    bets = 0
    pnl = 0.0
    clv = []
    selected = []

    for r in rows:
        consensus, disagreement = _structural_gate_values(r)
        if consensus < min_consensus_margin:
            continue
        if disagreement > max_disagreement:
            continue

        k = 2  # away only
        if r["op"][k] > cap:
            continue
        ev = float(r["p"][k]) * float(r["op"][k]) - 1.0
        if ev < edge:
            continue

        pc = pricing.devig(r["cl"])
        c = float(r["op"][k]) * float(pc[k]) - 1.0
        bets += 1
        pnl += float(r["op"][k]) - 1.0 if int(r["y"]) == k else -1.0
        clv.append(c)
        selected.append({
            "date": str(r.get("date", "")),
            "home": r.get("home"),
            "away": r.get("away"),
            "model_p": float(r["p"][k]),
            "opening": float(r["op"][k]),
            "closing_novig_p": float(pc[k]),
            "ev": ev,
            "clv": c,
            "consensus_margin": consensus,
            "structural_disagreement": disagreement,
            "result": "WIN" if int(r["y"]) == k else "LOSE",
        })

    vals = sorted(clv)
    med = 0.0
    if vals:
        n = len(vals)
        med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0

    return {
        "bets": bets,
        "clv": sum(vals) / len(vals) if vals else 0.0,
        "median_clv": med,
        "positive_clv_rate": sum(v > 0 for v in vals) / len(vals) if vals else 0.0,
        "roi": pnl / bets if bets else 0.0,
        "selected": selected,
    }


def _strip_selected(stats: dict) -> dict:
    return {k: v for k, v in stats.items() if k != "selected"}


def _candidate_disagreements(rows: list[dict], edge: float, cap: float) -> list[float]:
    vals = []
    for r in rows:
        k = 2
        if float(r["op"][k]) > cap:
            continue
        if float(r["p"][k]) * float(r["op"][k]) - 1.0 < edge:
            continue
        _, d = _structural_gate_values(r)
        vals.append(d)
    return vals


def _choose_consensus_gate(tune_by_year: dict[int, list[dict]]):
    merged = [r for y in sorted(tune_by_year) for r in tune_by_year[y]]
    best = None
    near = None

    for edge in EDGE_GRID:
        for cap in ODDS_CAP_GRID:
            disagreements = _candidate_disagreements(merged, edge, cap)
            for q in DISAGREEMENT_QUANTILES:
                max_disagreement = _quantile(disagreements, q)
                for margin in MIN_CONSENSUS_MARGIN_GRID:
                    total_raw = _entry_stats_consensus(
                        merged, edge, cap, margin, max_disagreement
                    )
                    yearly_raw = {
                        str(y): _entry_stats_consensus(
                            rows, edge, cap, margin, max_disagreement
                        )
                        for y, rows in tune_by_year.items()
                    }
                    total = _strip_selected(total_raw)
                    yearly = {y: _strip_selected(s) for y, s in yearly_raw.items()}

                    fails = []
                    if total["bets"] < 40:
                        fails.append("tune_bets<40")
                    if total["clv"] <= 0:
                        fails.append("tune_mean_clv<=0")
                    if total["median_clv"] <= 0:
                        fails.append("tune_median_clv<=0")
                    if total["positive_clv_rate"] < 0.55:
                        fails.append("tune_positive_clv_rate<55%")

                    for y, s in yearly.items():
                        if s["bets"] < 15:
                            fails.append(f"{y}_bets<15")
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
                        + total["median_clv"] * 12.0
                        + (total["positive_clv_rate"] - 0.5) * 12.0
                    )
                    cand = {
                        "edge": edge,
                        "cap": cap,
                        "side": "away",
                        "min_consensus_margin": margin,
                        "disagreement_quantile": q,
                        "max_disagreement": max_disagreement,
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

    tune = {
        2022: _rolling_eval(data, 2022, hyper),
        2023: _rolling_eval(data, 2023, hyper),
    }
    if any(len(v) < 60 for v in tune.values()):
        result.update({"validated": False, "reason": "too little tune data"})
        return result

    gate, near = _choose_consensus_gate(tune)
    use_gate = gate or near
    hold_eval = _rolling_eval(data, 2024, hyper)
    diag_eval = _rolling_eval(data, 2025, hyper)

    empty = {
        "bets": 0,
        "clv": 0.0,
        "median_clv": 0.0,
        "positive_clv_rate": 0.0,
        "roi": 0.0,
    }
    if use_gate:
        hold_raw = _entry_stats_consensus(
            hold_eval,
            use_gate["edge"],
            use_gate["cap"],
            use_gate["min_consensus_margin"],
            use_gate["max_disagreement"],
        )
        diag_raw = _entry_stats_consensus(
            diag_eval,
            use_gate["edge"],
            use_gate["cap"],
            use_gate["min_consensus_margin"],
            use_gate["max_disagreement"],
        )
        hold = _strip_selected(hold_raw)
        diag = _strip_selected(diag_raw)
        hold_selected = hold_raw["selected"]
        diag_selected = diag_raw["selected"]
    else:
        hold = dict(empty)
        diag = dict(empty)
        hold_selected = []
        diag_selected = []

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
        "strict_holdout_selected": hold_selected,
        "strict_holdout_logloss": {
            "model": hold_model_ll,
            "opening": hold_market_ll,
            "gain": hold_market_ll - hold_model_ll,
        },
        "diagnostic_only_2025": diag,
        "diagnostic_selected_2025": diag_selected,
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
            "M17.15 frozen M17.11 fair model + fast/slow structural consensus "
            "away entry gate; no market model features"
        ),
        "_focus": FOCUS,
        "_model_rule": (
            "M17.11 probability model frozen; only entry gate researched here"
        ),
        "_entry_rule": (
            "away EV/cap + min fast/slow structural xG consensus margin + "
            "max timescale disagreement; selected only on 2022/2023 CLV"
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

    log = [f"M17.15 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

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
        gate = r.get("gate") or r.get("near_miss_gate") or {}
        ts = gate.get("stats") or {}
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        log.append(
            f"{league}: gate={'OK' if r.get('gate') else 'NONE'} "
            f"edge={gate.get('edge')} cap={gate.get('cap')} "
            f"margin>={gate.get('min_consensus_margin')} "
            f"q={gate.get('disagreement_quantile')} "
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
