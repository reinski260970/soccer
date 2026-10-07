"""M17.7: focused Portugal/Greece research with previous-season xG/luck priors.

Builds on M17.6:
- Mongo chronology and results
- HS/HST/HC learned xG proxy
- previous-season home/away PPG + GF/GA priors

Adds only leakage-safe Y-1 information:
- venue xGF/xGA per match from the learned xG proxy
- goals minus xG attack over/under-performance
- goals conceded minus xGA defensive over/under-performance
- matchup transforms (home xGF vs away xGA, away xGF vs home xGA)

No bookmaker odds are model features. Pinnacle opening/closing remain validation
only. Focus is intentionally narrow because M17.6 identified Portugal and
Greece as the strongest next research candidates.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .m12_research import _season_start
from .m14_research import load_league, train_proxy
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
from .m17_6_research import build_previous_season_priors, augment_with_priors

OUT = Path("data/m17_7_validation.json")

FOCUS = {
    "primeira": "P1",
    "greece": "G1",
}


@dataclass
class XGVenuePrior:
    team: str
    home_gp: int
    home_xgf_pg: float
    home_xga_pg: float
    home_gf_pg: float
    home_ga_pg: float
    away_gp: int
    away_xgf_pg: float
    away_xga_pg: float
    away_gf_pg: float
    away_ga_pg: float


def build_previous_season_xg_priors(matches):
    raw = defaultdict(lambda: defaultdict(lambda: {
        "hgp": 0, "hxgf": 0.0, "hxga": 0.0, "hgf": 0.0, "hga": 0.0,
        "agp": 0, "axgf": 0.0, "axga": 0.0, "agf": 0.0, "aga": 0.0,
    }))

    for m in matches:
        if m.home_xg is None or m.away_xg is None:
            continue
        s = _season_start(m.date)
        h = raw[s][m.home]
        a = raw[s][m.away]
        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = float(m.home_xg), float(m.away_xg)

        h["hgp"] += 1
        h["hxgf"] += hx
        h["hxga"] += ax
        h["hgf"] += hg
        h["hga"] += ag

        a["agp"] += 1
        a["axgf"] += ax
        a["axga"] += hx
        a["agf"] += ag
        a["aga"] += hg

    out = {}
    seasons = sorted(raw)
    for target in range(min(seasons) + 1 if seasons else START_YEAR, END_YEAR + 1):
        prev = raw.get(target - 1, {})
        rows = []
        for team, s in prev.items():
            if s["hgp"] <= 0 or s["agp"] <= 0:
                continue
            rows.append(XGVenuePrior(
                team=team,
                home_gp=s["hgp"],
                home_xgf_pg=s["hxgf"] / s["hgp"],
                home_xga_pg=s["hxga"] / s["hgp"],
                home_gf_pg=s["hgf"] / s["hgp"],
                home_ga_pg=s["hga"] / s["hgp"],
                away_gp=s["agp"],
                away_xgf_pg=s["axgf"] / s["agp"],
                away_xga_pg=s["axga"] / s["agp"],
                away_gf_pg=s["agf"] / s["agp"],
                away_ga_pg=s["aga"] / s["agp"],
            ))
        out[target] = rows
    return out


def _xg_defaults(rows):
    if not rows:
        return {
            "home_xgf_pg": 1.4, "home_xga_pg": 1.2,
            "home_gf_pg": 1.4, "home_ga_pg": 1.2,
            "away_xgf_pg": 1.1, "away_xga_pg": 1.4,
            "away_gf_pg": 1.1, "away_ga_pg": 1.4,
        }

    def avg(attr):
        vals = [float(getattr(r, attr)) for r in rows]
        return sum(vals) / len(vals)

    return {k: avg(k) for k in (
        "home_xgf_pg", "home_xga_pg", "home_gf_pg", "home_ga_pg",
        "away_xgf_pg", "away_xga_pg", "away_gf_pg", "away_ga_pg",
    )}


def augment_with_xg_priors(data, priors):
    defaults = {season: _xg_defaults(rows) for season, rows in priors.items()}
    out = []
    both = home_only = away_only = neither = 0

    for r in data:
        season = int(r["season"])
        rows = priors.get(season, [])
        by_team = {x.team: x for x in rows}
        d = defaults.get(season) or _xg_defaults([])
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

        hxgf = hp.home_xgf_pg if hp else d["home_xgf_pg"]
        hxga = hp.home_xga_pg if hp else d["home_xga_pg"]
        hgf = hp.home_gf_pg if hp else d["home_gf_pg"]
        hga = hp.home_ga_pg if hp else d["home_ga_pg"]

        axgf = ap.away_xgf_pg if ap else d["away_xgf_pg"]
        axga = ap.away_xga_pg if ap else d["away_xga_pg"]
        agf = ap.away_gf_pg if ap else d["away_gf_pg"]
        aga = ap.away_ga_pg if ap else d["away_ga_pg"]

        z = dict(r)
        z["x"] = list(r["x"]) + [
            hxgf,
            hxga,
            axgf,
            axga,
            hxgf - axga,
            axgf - hxga,
            hgf - hxgf,
            hga - hxga,
            agf - axgf,
            aga - axga,
            (hgf - hxgf) - (agf - axgf),
            (hga - hxga) - (aga - axga),
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
    base_priors = build_previous_season_priors(matches)
    data, base_cov = augment_with_priors(base, base_priors)

    xg_priors = build_previous_season_xg_priors(matches)
    data, xg_cov = augment_with_xg_priors(data, xg_priors)

    result = {
        "samples": len(data),
        "coverage": cov,
        "previous_season_prior_coverage": base_cov,
        "previous_season_xg_prior_coverage": xg_cov,
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
            "M17.7 focused P1/G1: M17.6 previous-season priors + "
            "previous-season xG/xGA and goals-minus-xG luck features; "
            "no market features"
        ),
        "_focus": FOCUS,
        "_proxy": {
            "n": proxy["n"],
            "rmse": proxy["rmse"],
            "beta": proxy["beta"],
            "features": proxy["features"],
        },
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
        "leagues": {},
    }

    log = [f"M17.7 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

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
                "reason": f"load/research failed: {type(exc).__name__}",
            }

        result["leagues"][league] = r
        gate = r.get("gate") or r.get("near_miss_gate") or {}
        ts = gate.get("stats") or {}
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        xc = r.get("previous_season_xg_prior_coverage") or {}
        log.append(
            f"{league}: samples={r.get('samples',0)} "
            f"xg-prior-both={xc.get('both_prior_pct',0)*100:.1f}% | "
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
