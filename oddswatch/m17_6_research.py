"""M17.6: M17.5 + leakage-safe previous-season team priors.

Historical source is Mongo only. We compute the same kind of context commonly
shown on SoccerSTATS (home/away PPG, GF/game, GA/game) from the completed
PREVIOUS season, so research is not dependent on scraping and cannot leak
future season information.

SoccerSTATS remains a live/cross-check source in the scanner, not a historical
backtest dependency.

Core history:
- results, HS/AS, HST/AST, HC/AC from Mongo
- learned chance/xG proxy trained against real Understat xG
- Pinnacle opening/closing only for validation, never model features

For a match in season Y, only completed season Y-1 priors are allowed:
- home team's prior HOME PPG, GF/game, GA/game
- away team's prior AWAY PPG, GF/game, GA/game
- relative venue-strength transforms
- explicit promoted/missing flags
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .m12_research import _season_start
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

OUT = Path("data/m17_6_validation.json")


@dataclass
class VenuePrior:
    team: str
    home_gp: int
    home_gf_pg: float
    home_ga_pg: float
    home_ppg: float
    away_gp: int
    away_gf_pg: float
    away_ga_pg: float
    away_ppg: float
    source: str = "mongo_previous_season"


def _pts(gf: float, ga: float) -> int:
    return 3 if gf > ga else (1 if gf == ga else 0)


def build_previous_season_priors(matches) -> dict[int, list[VenuePrior]]:
    """Target season Y -> team venue priors from completed season Y-1."""
    raw = defaultdict(lambda: defaultdict(lambda: {
        "hgp": 0, "hgf": 0.0, "hga": 0.0, "hpts": 0.0,
        "agp": 0, "agf": 0.0, "aga": 0.0, "apts": 0.0,
    }))

    for m in matches:
        s = _season_start(m.date)
        h = raw[s][m.home]
        a = raw[s][m.away]
        hg, ag = float(m.home_goals), float(m.away_goals)

        h["hgp"] += 1
        h["hgf"] += hg
        h["hga"] += ag
        h["hpts"] += _pts(hg, ag)

        a["agp"] += 1
        a["agf"] += ag
        a["aga"] += hg
        a["apts"] += _pts(ag, hg)

    out = {}
    seasons = sorted(raw)
    for target in range(min(seasons) + 1 if seasons else START_YEAR, END_YEAR + 1):
        prev = raw.get(target - 1, {})
        rows = []
        for team, s in prev.items():
            if s["hgp"] <= 0 or s["agp"] <= 0:
                continue
            rows.append(VenuePrior(
                team=team,
                home_gp=s["hgp"],
                home_gf_pg=s["hgf"] / s["hgp"],
                home_ga_pg=s["hga"] / s["hgp"],
                home_ppg=s["hpts"] / s["hgp"],
                away_gp=s["agp"],
                away_gf_pg=s["agf"] / s["agp"],
                away_ga_pg=s["aga"] / s["agp"],
                away_ppg=s["apts"] / s["agp"],
            ))
        out[target] = rows
    return out


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


def augment_with_priors(data: list[dict], priors: dict[int, list[VenuePrior]]):
    out = []
    both = home_only = away_only = neither = 0
    defaults = {season: _defaults(rows) for season, rows in priors.items()}

    for r in data:
        season = int(r["season"])
        rows = priors.get(season, [])
        by_team = {x.team: x for x in rows}
        d = defaults.get(season) or _defaults([])

        hp = by_team.get(r["home"])
        ap = by_team.get(r["away"])

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


def _league_run(matches, odds_rows, shots, cov):
    base = build_dataset(matches, odds_rows, shots)
    priors = build_previous_season_priors(matches)
    data, prior_cov = augment_with_priors(base, priors)

    result = {
        "samples": len(data),
        "coverage": cov,
        "previous_season_prior_coverage": prior_cov,
        "prior_source": "Mongo completed Y-1 season; SoccerSTATS-style home/away context",
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
        "bets": 0, "clv": 0.0, "median_clv": 0.0,
        "positive_clv_rate": 0.0, "roi": 0.0,
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
            "M17.6 M17.5 Mongo/xG-proxy + leakage-safe Mongo-derived "
            "previous-season SoccerSTATS-style home-away priors; no market features"
        ),
        "_proxy": {
            "n": proxy["n"],
            "rmse": proxy["rmse"],
            "beta": proxy["beta"],
            "features": proxy["features"],
            "train_seasons": proxy["train_seasons"],
        },
        "_prior_rule": (
            "season Y uses only completed Mongo season Y-1 home/away aggregates; "
            "promoted/missing teams use league means + explicit missing flags"
        ),
        "_soccerstats_role": (
            "live/cross-check only; historical research does not depend on scraping"
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
        pc = r.get("previous_season_prior_coverage") or {}
        log.append(
            f"{league}: samples={r.get('samples',0)} "
            f"prior-both={pc.get('both_prior_pct',0)*100:.1f}% | "
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
