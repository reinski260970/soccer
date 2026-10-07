"""M17.3: pooled Top-5 + Serie-A local blend with dual-timescale features.

No bookmaker odds are model features.

Why:
- M17.2 Serie A away showed positive CLV on the strict 2024 holdout but only
  six bets and poor global logloss.
- M17.3 improves the probability model rather than loosening release gates.
- General football patterns are learned from all Top-5 leagues, while a local
  Serie-A model preserves league-specific structure.
- Team form is represented at fast and slow EWMA horizons.

Splits remain strict:
- hyper/model blend: validate Serie A 2020 and 2021 only
- entry gate: rolling OOS Serie A 2022 + 2023 CLV
- strict holdout: Serie A 2024
- 2025: diagnostic only
"""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import pricing
from .m12_research import _season_start
from .m13_research import load_real_xg
from .m17_1_research import (
    TeamState,
    _features,
    _points,
    _xg,
    _fit,
    _pred,
    _calibrate,
    _standardizer,
    _tx,
    _logloss,
    _entry_stats,
    load_real_shots,
)

OUT = Path("data/m17_3_validation.json")

TOP5 = {
    "bundesliga": "D1",
    "epl": "E0",
    "laliga": "SP1",
    "seriea": "I1",
    "ligue1": "F1",
}
TARGET = "seriea"
L2_GRID = (0.05, 0.25, 1.0)
CALIB_GRID = (0.80, 0.95, 1.05, 1.15)
BLEND_GRID = (0.0, 0.25, 0.50, 0.75, 1.0)  # weight on local Serie-A model
EDGE_GRID = (0.01, 0.02, 0.03, 0.05, 0.075)
ODDS_CAP = 2.5
SIDE = "away"

FAST_ALPHA = 0.28
SLOW_ALPHA = 0.08


def _ew(old: float, new: float, alpha: float) -> float:
    return (1.0 - alpha) * old + alpha * new


def _update(st: TeamState, gf: float, ga: float, xf: float, xa: float,
            sf: float, sa: float, sotf: float, sota: float, pts: float,
            d: date, is_home: bool, alpha: float) -> None:
    st.n += 1
    st.gf = _ew(st.gf, gf, alpha)
    st.ga = _ew(st.ga, ga, alpha)
    st.xf = _ew(st.xf, xf, alpha)
    st.xa = _ew(st.xa, xa, alpha)
    st.shots_f = _ew(st.shots_f, sf, alpha)
    st.shots_a = _ew(st.shots_a, sa, alpha)
    st.sot_f = _ew(st.sot_f, sotf, alpha)
    st.sot_a = _ew(st.sot_a, sota, alpha)
    st.pts = _ew(st.pts, pts, alpha)
    if is_home:
        st.home_gf = _ew(st.home_gf, gf, alpha)
        st.home_ga = _ew(st.home_ga, ga, alpha)
    else:
        st.away_gf = _ew(st.away_gf, gf, alpha)
        st.away_ga = _ew(st.away_ga, ga, alpha)
    st.last_date = d


def _dual_features(fh: TeamState, fa: TeamState,
                   sh: TeamState, sa: TeamState,
                   league: dict, d: date) -> list[float]:
    fast = _features(fh, fa, league, d)
    slow = _features(sh, sa, league, d)

    # Keep one intercept and one set of league baselines. Add slow team-state
    # features and fast-minus-slow momentum terms.
    slow_team = slow[1:14]
    momentum = [fast[i] - slow[i] for i in range(1, 14)]

    # Shot quality proxies derived only from rolling pre-match states.
    fast_h_acc = fh.sot_f / max(fh.shots_f, 1.0)
    fast_a_acc = fa.sot_f / max(fa.shots_f, 1.0)
    slow_h_acc = sh.sot_f / max(sh.shots_f, 1.0)
    slow_a_acc = sa.sot_f / max(sa.shots_f, 1.0)
    quality = [
        fast_h_acc - fast_a_acc,
        slow_h_acc - slow_a_acc,
        (fh.xf / max(fh.sot_f, 0.5)) - (fa.xf / max(fa.sot_f, 0.5)),
        (sh.xf / max(sh.sot_f, 0.5)) - (sa.xf / max(sa.sot_f, 0.5)),
    ]

    return fast + slow_team + momentum + quality


def build_dataset(matches, odds_rows, shot_map, league_name: str) -> list[dict]:
    odds = {(d, h, a): (season, hg, ag, op, cl)
            for season, d, h, a, hg, ag, op, cl in odds_rows}
    fast = defaultdict(TeamState)
    slow = defaultdict(TeamState)
    league = {
        "n": 0, "home": 0, "draw": 0, "away": 0,
        "home_rate": 0.45, "draw_rate": 0.27, "away_rate": 0.28,
        "goals": 2.70,
    }
    out = []

    for m in sorted(matches, key=lambda z: z.date):
        d, h, a = m.date, m.home, m.away
        season = _season_start(d)
        shot = shot_map.get((season, h, a))
        fh, fa = fast[h], fast[a]
        sh, sa = slow[h], slow[a]

        if fh.n >= 6 and fa.n >= 6 and (d, h, a) in odds and shot is not None:
            s, hg, ag, op, cl = odds[(d, h, a)]
            out.append({
                "league": league_name,
                "season": s,
                "date": d,
                "home": h,
                "away": a,
                "x": _dual_features(fh, fa, sh, sa, league, d),
                "y": 0 if hg > ag else (1 if hg == ag else 2),
                "op": op,
                "cl": cl,
            })

        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = _xg(m, True), _xg(m, False)
        if shot is not None:
            hshots, ashots, hsot, asot = shot
        else:
            # Preserve prior shot state; do not fabricate shot observations.
            hshots, ashots = fh.shots_f, fa.shots_f
            hsot, asot = fh.sot_f, fa.sot_f

        for alpha, hs1, as1 in (
            (FAST_ALPHA, fh, fa),
            (SLOW_ALPHA, sh, sa),
        ):
            _update(hs1, hg, ag, hx, ax, hshots, ashots, hsot, asot,
                    _points(hg, ag), d, True, alpha)
            _update(as1, ag, hg, ax, hx, ashots, hshots, asot, hsot,
                    _points(ag, hg), d, False, alpha)

        league["n"] += 1
        league["home"] += int(hg > ag)
        league["draw"] += int(hg == ag)
        league["away"] += int(hg < ag)
        n = league["n"]
        league["home_rate"] = league["home"] / n
        league["draw_rate"] = league["draw"] / n
        league["away_rate"] = league["away"] / n
        league["goals"] = _ew(league["goals"], hg + ag, 0.03)

    return out


def _fit_model(train):
    mean, sd = _standardizer([r["x"] for r in train])
    return mean, sd


def _raw_predictions(train, test, l2):
    mean, sd = _fit_model(train)
    w = _fit(_tx([r["x"] for r in train], mean, sd),
             [r["y"] for r in train], l2)
    return [_pred(w, x) for x in _tx([r["x"] for r in test], mean, sd)]


def _blend(a, b, local_weight: float):
    return [
        local_weight * x + (1.0 - local_weight) * y
        for x, y in zip(a, b)
    ]


def _fit_predict(pooled_train, local_train, test, l2, calib, local_weight):
    pp = _raw_predictions(pooled_train, test, l2)
    lp = _raw_predictions(local_train, test, l2)
    return [
        _calibrate(_blend(a, b, local_weight), calib)
        for a, b in zip(lp, pp)
    ]


def _select_hyper(all_data, local_data):
    folds = []
    for year in (2020, 2021):
        pooled_train = [r for r in all_data if r["season"] <= year - 1]
        local_train = [r for r in local_data if r["season"] <= year - 1]
        va = [r for r in local_data if r["season"] == year]
        if len(pooled_train) < 1500 or len(local_train) < 300 or len(va) < 80:
            return None
        folds.append((pooled_train, local_train, va))

    best = None
    for l2 in L2_GRID:
        raw = []
        for pooled_train, local_train, va in folds:
            pp = _raw_predictions(pooled_train, va, l2)
            lp = _raw_predictions(local_train, va, l2)
            raw.append((va, lp, pp))
        for blend in BLEND_GRID:
            for calib in CALIB_GRID:
                losses = []
                for va, lp, pp in raw:
                    probs = [
                        _calibrate(_blend(a, b, blend), calib)
                        for a, b in zip(lp, pp)
                    ]
                    losses.append(_logloss(probs, [r["y"] for r in va]))
                score = sum(losses) / len(losses)
                if best is None or score < best["cv_logloss"]:
                    best = {
                        "l2": l2,
                        "calib": calib,
                        "local_weight": blend,
                        "cv_logloss": score,
                        "fold_logloss": losses,
                    }
    return best


def _attach(rows, probs):
    out = []
    for r, p in zip(rows, probs):
        z = dict(r)
        z["p"] = p
        out.append(z)
    return out


def _rolling_eval(all_data, local_data, year: int, hyper: dict):
    pooled_train = [r for r in all_data if r["season"] <= year - 1]
    local_train = [r for r in local_data if r["season"] <= year - 1]
    test = [r for r in local_data if r["season"] == year]
    if len(pooled_train) < 1500 or len(local_train) < 300 or len(test) < 60:
        return []
    probs = _fit_predict(
        pooled_train, local_train, test,
        hyper["l2"], hyper["calib"], hyper["local_weight"],
    )
    return _attach(test, probs)


def _choose_gate(tune_by_year):
    merged = [r for y in sorted(tune_by_year) for r in tune_by_year[y]]
    best = None
    near = None

    for edge in EDGE_GRID:
        total = _entry_stats(merged, edge, ODDS_CAP, SIDE)
        yearly = {
            str(y): _entry_stats(rows, edge, ODDS_CAP, SIDE)
            for y, rows in tune_by_year.items()
        }
        fails = []
        if total["bets"] < 30:
            fails.append("tune_bets<30")
        if total["clv"] <= 0:
            fails.append("tune_mean_clv<=0")
        if total["median_clv"] <= 0:
            fails.append("tune_median_clv<=0")
        if total["positive_clv_rate"] < 0.52:
            fails.append("tune_positive_clv_rate<52%")
        for y, s in yearly.items():
            if s["bets"] < 8:
                fails.append(f"{y}_bets<8")
            if s["clv"] <= 0:
                fails.append(f"{y}_clv<=0")

        passed = 6 - min(len(fails), 6)
        near_score = (
            passed * 100.0
            + total["clv"] * math.sqrt(max(total["bets"], 1)) * 20.0
            + total["median_clv"] * 10.0
            + (total["positive_clv_rate"] - 0.5) * 10.0
        )
        cand = {
            "edge": edge,
            "cap": ODDS_CAP,
            "side": SIDE,
            "stats": total,
            "per_year": yearly,
            "fails": fails,
            "near_score": near_score,
        }
        if near is None or near_score > near["near_score"]:
            near = cand
        if fails:
            continue

        cand["score"] = total["clv"] * math.sqrt(total["bets"])
        if best is None or cand["score"] > best["score"]:
            best = cand

    return best, near


def _market_logloss(rows):
    return _logloss([pricing.devig(r["op"]) for r in rows],
                    [r["y"] for r in rows])


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    data_by_league = {}
    coverage = {}
    for league, code in TOP5.items():
        matches, rows, cov = load_real_xg(code)
        shots = load_real_shots(code)
        data_by_league[league] = build_dataset(matches, rows, shots, league)
        coverage[league] = cov

    all_data = [r for league in TOP5 for r in data_by_league[league]]
    local = data_by_league[TARGET]
    hyper = _select_hyper(all_data, local)

    result = {
        "_method": "M17.3 pooled Top-5 + Serie-A local blend; dual-timescale pre-match features; no market features",
        "_target": "seriea away",
        "_splits": {
            "hyper_A": "pooled/local train<=2019 validate SerieA 2020",
            "hyper_B": "pooled/local train<=2020 validate SerieA 2021",
            "entry_tune": "rolling OOS SerieA 2022 + 2023 CLV",
            "strict_holdout": "rolling OOS SerieA 2024",
            "diagnostic_only": "rolling OOS SerieA 2025",
        },
        "_release_rule": "robust tune gate + strict 2024 >=15 bets, mean/median CLV>0, positive CLV rate>=52%",
        "coverage": coverage,
        "samples": {k: len(v) for k, v in data_by_league.items()},
        "hyper": hyper,
    }
    log = [
        f"M17.3: pooled Top-5={len(all_data)} rows + SerieA local={len(local)} rows",
    ]

    if hyper is None:
        result["validated"] = False
        result["reason"] = "too little strict early-fold data"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        return log + ["NO RELEASE: too little strict early-fold data"]

    tune = {
        2022: _rolling_eval(all_data, local, 2022, hyper),
        2023: _rolling_eval(all_data, local, 2023, hyper),
    }
    gate, near = _choose_gate(tune)

    hold_eval = _rolling_eval(all_data, local, 2024, hyper)
    diag_eval = _rolling_eval(all_data, local, 2025, hyper)
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

    hold_rows = [r for r in local if r["season"] == 2024]
    hold_model_ll = (
        _logloss([r["p"] for r in hold_eval], [r["y"] for r in hold_eval])
        if hold_eval else 9.0
    )
    hold_market_ll = _market_logloss(hold_rows) if hold_rows else 9.0

    validated = bool(
        gate is not None
        and hold["bets"] >= 15
        and hold["clv"] > 0
        and hold["median_clv"] > 0
        and hold["positive_clv_rate"] >= 0.52
    )

    result.update({
        "validated": validated,
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

    g = gate or near or {}
    ts = g.get("stats") or {}
    ll = result["strict_holdout_logloss"]
    log += [
        f"hyper: l2={hyper['l2']} calib={hyper['calib']} local_weight={hyper['local_weight']:.2f} "
        f"earlyLL={hyper['cv_logloss']:.4f}",
        f"gate={'OK' if gate else 'NONE'} edge={g.get('edge')} cap={g.get('cap')} "
        f"tune n={ts.get('bets',0)} CLV={ts.get('clv',0)*100:+.2f}% "
        f"med={ts.get('median_clv',0)*100:+.2f}% pos={ts.get('positive_clv_rate',0)*100:.1f}%",
        f"hold2024 n={hold['bets']} CLV={hold['clv']*100:+.2f}% "
        f"med={hold['median_clv']*100:+.2f}% pos={hold['positive_clv_rate']*100:.1f}% "
        f"ROI={hold['roi']*100:+.2f}% dLL={ll['gain']:+.4f} -> "
        + ("VALIDATED" if validated else "NO RELEASE"),
        f"diag2025 n={diag['bets']} CLV={diag['clv']*100:+.2f}% ROI={diag['roi']*100:+.2f}%",
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log


if __name__ == "__main__":
    for line in run():
        print(line)
