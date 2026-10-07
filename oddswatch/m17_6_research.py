"""M17.6: M17.5 + leakage-safe SoccerSTATS previous-season team priors.

Core history remains Mongo:
- results, HS/AS, HST/AST, HC/AC
- learned chance/xG proxy trained against real Understat xG
- Pinnacle opening/closing only for validation, never as model features

New in M17.6:
For a match in season Y, only SoccerSTATS HOME/AWAY aggregates from the fully
completed previous season Y-1 are allowed as priors:
- home team's prior home PPG, GF/game, GA/game
- away team's prior away PPG, GF/game, GA/game
- relative venue-strength transforms
- explicit missing/promoted flags

No current-season final SoccerSTATS table is backfilled into earlier matches.
This keeps the strict 2024 holdout genuinely chronological.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import matching
from .m14_research import LEAGUES, load_league, train_proxy
from .m17_1_research import build_dataset, load_real_shots, _logloss, _entry_stats
from .m17_5_research import (
    START_YEAR,
    END_YEAR,
    _early_hyper,
    _rolling_eval,
    _choose_gate,
    _market_logloss,
    mongo_coverage,
)
from .sources import soccerstats

OUT = Path("data/m17_6_validation.json")


def _defaults(rows):
    if not rows:
        return {
            "home_ppg": 1.5, "home_gf_pg": 1.4, "home_ga_pg": 1.2,
            "away_ppg": 1.1, "away_gf_pg": 1.1, "away_ga_pg": 1.4,
        }
    def avg(attr):
        vals = [float(getattr(r, attr)) for r in rows]
        return sum(vals) / len(vals)
    return {
        "home_ppg": avg("home_ppg"),
        "home_gf_pg": avg("home_gf_pg"),
        "home_ga_pg": avg("home_ga_pg"),
        "away_ppg": avg("away_ppg"),
        "away_gf_pg": avg("away_gf_pg"),
        "away_ga_pg": avg("away_ga_pg"),
    }


def load_prior_seasons(code: str, seasons: list[int]):
    """Load prior season Y-1 for every target season Y."""
    priors = {}
    errors = {}
    for season in sorted(set(seasons)):
        prev = season - 1
        rows, err = soccerstats.team_homeaway(code, prev, cache_days=30.0)
        priors[season] = rows
        if err:
            errors[str(season)] = err
    return priors, errors


def _find_prior(team: str, rows):
    if not rows:
        return None
    names = [r.team for r in rows]
    hit = matching.find(team, names)
    if hit is None:
        hit = matching.find_strict(team, names)
    if hit is None:
        return None
    return next((r for r in rows if r.team == hit), None)


def augment_with_priors(data: list[dict], priors: dict[int, list]) -> tuple[list[dict], dict]:
    out = []
    both = home_only = away_only = neither = 0

    defaults = {season: _defaults(rows) for season, rows in priors.items()}

    for r in data:
        season = int(r["season"])
        rows = priors.get(season, [])
        d = defaults.get(season) or _defaults([])
        hp = _find_prior(r["home"], rows)
        ap = _find_prior(r["away"], rows)

        if hp and ap:
            both += 1
        elif hp:
            home_only += 1
        elif ap:
            away_only += 1
        else:
            neither += 1

        h_ppg = hp.home_ppg if hp else d["home_ppg"]
        h_gf = hp.home_gf_pg if hp else d["home_gf_pg"]
        h_ga = hp.home_ga_pg if hp else d["home_ga_pg"]
        a_ppg = ap.away_ppg if ap else d["away_ppg"]
        a_gf = ap.away_gf_pg if ap else d["away_gf_pg"]
        a_ga = ap.away_ga_pg if ap else d["away_ga_pg"]

        z = dict(r)
        z["x"] = list(r["x"]) + [
            h_ppg,
            a_ppg,
            h_gf,
            h_ga,
            a_gf,
            a_ga,
            h_ppg - a_ppg,
            h_gf - a_ga,
            a_gf - h_ga,
            0.0 if hp else 1.0,
            0.0 if ap else 1.0,
        ]
        out.append(z)

    n = len(data)
    return out, {
        "rows": n,
        "both_prior": both,
        "home_only": home_only,
        "away_only": away_only,
        "neither": neither,
        "both_prior_pct": both / n if n else 0.0,
        "at_least_one_pct": (both + home_only + away_only) / n if n else 0.0,
    }


def _league_run(matches, odds_rows, shots, cov, code):
    base = build_dataset(matches, odds_rows, shots)
    seasons = sorted({int(r["season"]) for r in base})
    priors, prior_errors = load_prior_seasons(code, seasons)
    data, prior_cov = augment_with_priors(base, priors)

    result = {
        "samples": len(data),
        "coverage": cov,
        "soccerstats_prior_coverage": prior_cov,
        "soccerstats_prior_errors": prior_errors,
        "loaded_prior_seasons": sorted(
            int(s) for s, rows in priors.items() if rows
        ),
    }

    if cov.get("proxy_coverage", 0.0) < 0.70:
        result.update({
            "validated": False,
            "reason": "historical shot/corner proxy coverage <70%",
        })
        return result

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
    })
    return result


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    profile = mongo_coverage()
    proxy = train_proxy()

    result = {
        "_method": (
            "M17.6 M17.5 Mongo/xG-proxy + SoccerSTATS previous-season "
            "home-away team priors; no market features"
        ),
        "_proxy": {
            "n": proxy["n"],
            "rmse": proxy["rmse"],
            "beta": proxy["beta"],
            "features": proxy["features"],
            "train_seasons": proxy["train_seasons"],
        },
        "_soccerstats_rule": (
            "season Y uses only completed season Y-1 team home/away aggregates; "
            "missing/promoted teams use league means + explicit missing flags"
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

    log = [f"M17.6 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

    for league, code in LEAGUES.items():
        try:
            matches, rows, cov = load_league(
                code, proxy, start_year=START_YEAR, end_year=END_YEAR
            )
            shots = load_real_shots(
                code, start_year=START_YEAR, end_year=END_YEAR
            )
            r = _league_run(matches, rows, shots, cov, code)
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
        pc = r.get("soccerstats_prior_coverage") or {}
        log.append(
            f"{league}: samples={r.get('samples',0)} "
            f"SSboth={pc.get('both_prior_pct',0)*100:.1f}% | "
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
