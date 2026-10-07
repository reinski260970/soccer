"""M17.4: dedicated Serie-A away-win classifier with Elo + dual-timescale form.

No bookmaker odds are model features.

M17.3 showed that pooled multinomial modelling increased sample size but did not
produce positive CLV. M17.4 models the actual research target directly:
P(away win), while preserving the same strict temporal separation.

Splits:
- model hyperparameters/blend: Serie A 2020 + 2021 outcome logloss
- entry tune: rolling OOS Serie A 2022 + 2023 CLV
- strict holdout: rolling OOS Serie A 2024
- 2025: diagnostic only

The model uses only pre-match team state: fast/slow goals, xG, shots/SoT,
home-away splits, points, rest, league baselines and rolling Elo difference.
"""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from datetime import date
from pathlib import Path

from . import pricing
from .m12_research import _season_start
from .m13_research import load_real_xg
from .m17_1_research import TeamState, _features, _points, _xg, _standardizer, _tx, load_real_shots
from .m17_3_research import TOP5, FAST_ALPHA, SLOW_ALPHA, _dual_features, _update

OUT = Path("data/m17_4_validation.json")
TARGET = "seriea"

L2_GRID = (0.05, 0.25, 1.0)
CALIB_GRID = (0.80, 0.95, 1.05, 1.15)
BLEND_GRID = (0.0, 0.25, 0.50, 0.75, 1.0)
EDGE_GRID = (0.02, 0.03, 0.05, 0.075)
ODDS_CAP = 2.5

ELO_K = 20.0
ELO_HOME = 55.0


def _elo_expected(rh: float, ra: float) -> float:
    return 1.0 / (1.0 + 10.0 ** (-(rh + ELO_HOME - ra) / 400.0))


def _elo_update(ratings: dict[str, float], home: str, away: str,
                hg: float, ag: float) -> None:
    rh = ratings.get(home, 1500.0)
    ra = ratings.get(away, 1500.0)
    exp_h = _elo_expected(rh, ra)
    actual = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
    gd = abs(hg - ag)
    mult = 1.0 + 0.15 * min(gd, 4.0)
    delta = ELO_K * mult * (actual - exp_h)
    ratings[home] = rh + delta
    ratings[away] = ra - delta


def build_dataset(matches, odds_rows, shot_map, league_name: str) -> list[dict]:
    odds = {(d, h, a): (season, hg, ag, op, cl)
            for season, d, h, a, hg, ag, op, cl in odds_rows}
    fast = defaultdict(TeamState)
    slow = defaultdict(TeamState)
    ratings: dict[str, float] = {}
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
        rh, ra = ratings.get(h, 1500.0), ratings.get(a, 1500.0)

        if fh.n >= 6 and fa.n >= 6 and (d, h, a) in odds and shot is not None:
            s, hg, ag, op, cl = odds[(d, h, a)]
            x = _dual_features(fh, fa, sh, sa, league, d)
            elo_diff = (rh - ra) / 400.0
            # Away-oriented transforms remain pre-match and market-free.
            x += [
                elo_diff,
                elo_diff * abs(elo_diff),
                (fa.xf - fh.xa),
                (fa.sot_f - fh.sot_a),
                (fa.away_gf - fh.home_ga),
            ]
            out.append({
                "league": league_name,
                "season": s,
                "date": d,
                "home": h,
                "away": a,
                "x": x,
                "y": 1 if ag > hg else 0,
                "op": op,
                "cl": cl,
            })

        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = _xg(m, True), _xg(m, False)

        for alpha, hs1, as1 in (
            (FAST_ALPHA, fh, fa),
            (SLOW_ALPHA, sh, sa),
        ):
            if shot is not None:
                hshots, ashots, hsot, asot = shot
            else:
                hshots, ashots = hs1.shots_f, as1.shots_f
                hsot, asot = hs1.sot_f, as1.sot_f
            _update(hs1, hg, ag, hx, ax, hshots, ashots, hsot, asot,
                    _points(hg, ag), d, True, alpha)
            _update(as1, ag, hg, ax, hx, ashots, hshots, asot, hsot,
                    _points(ag, hg), d, False, alpha)

        _elo_update(ratings, h, a, hg, ag)

        league["n"] += 1
        league["home"] += int(hg > ag)
        league["draw"] += int(hg == ag)
        league["away"] += int(hg < ag)
        n = league["n"]
        league["home_rate"] = league["home"] / n
        league["draw_rate"] = league["draw"] / n
        league["away_rate"] = league["away"] / n
        league["goals"] = (0.97 * league["goals"] + 0.03 * (hg + ag))

    return out


def _sigmoid(z: float) -> float:
    if z >= 0:
        e = math.exp(-z)
        return 1.0 / (1.0 + e)
    e = math.exp(z)
    return e / (1.0 + e)


def _fit_binary(x, y, l2: float, epochs: int = 50, lr: float = 0.08):
    n, p = len(x), len(x[0])
    w = [0.0] * p
    for ep in range(epochs):
        g = [0.0] * p
        inv = 1.0 / n
        for xi, yi in zip(x, y):
            pr = _sigmoid(sum(a * b for a, b in zip(w, xi)))
            e = (pr - yi) * inv
            for j, xv in enumerate(xi):
                g[j] += e * xv
        for j in range(1, p):
            g[j] += l2 * w[j] / n
        step = lr / (1.0 + ep / 25.0)
        for j in range(p):
            w[j] -= step * g[j]
    return w


def _raw_predictions(train, test, l2):
    mean, sd = _standardizer([r["x"] for r in train])
    xtr = _tx([r["x"] for r in train], mean, sd)
    xte = _tx([r["x"] for r in test], mean, sd)
    w = _fit_binary(xtr, [r["y"] for r in train], l2)
    return [_sigmoid(sum(a * b for a, b in zip(w, x))) for x in xte]


def _calibrate_binary(p: float, a: float) -> float:
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    x = p ** a
    y = (1.0 - p) ** a
    return x / (x + y)


def _blend(local: float, pooled: float, local_weight: float) -> float:
    return local_weight * local + (1.0 - local_weight) * pooled


def _binary_logloss(probs, ys):
    if not probs:
        return 9.0
    s = 0.0
    for p, y in zip(probs, ys):
        p = min(max(p, 1e-12), 1.0 - 1e-12)
        s -= math.log(p if y else 1.0 - p)
    return s / len(probs)


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
                        _calibrate_binary(_blend(a, b, blend), calib)
                        for a, b in zip(lp, pp)
                    ]
                    losses.append(_binary_logloss(probs, [r["y"] for r in va]))
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


def _rolling_eval(all_data, local_data, year: int, hyper: dict):
    pooled_train = [r for r in all_data if r["season"] <= year - 1]
    local_train = [r for r in local_data if r["season"] <= year - 1]
    test = [r for r in local_data if r["season"] == year]
    if len(pooled_train) < 1500 or len(local_train) < 300 or len(test) < 60:
        return []
    pp = _raw_predictions(pooled_train, test, hyper["l2"])
    lp = _raw_predictions(local_train, test, hyper["l2"])
    out = []
    for r, a, b in zip(test, lp, pp):
        z = dict(r)
        z["p"] = _calibrate_binary(
            _blend(a, b, hyper["local_weight"]), hyper["calib"]
        )
        out.append(z)
    return out


def _entry_stats(rows, edge: float):
    bets = 0
    pnl = 0.0
    clv = []
    for r in rows:
        odd = float(r["op"][2])
        if odd > ODDS_CAP or r["p"] * odd - 1.0 < edge:
            continue
        bets += 1
        pnl += odd - 1.0 if r["y"] else -1.0
        pc = pricing.devig(r["cl"])[2]
        clv.append(odd * pc - 1.0)

    vals = sorted(clv)
    med = 0.0
    if vals:
        n = len(vals)
        med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
    return {
        "bets": bets,
        "clv": sum(vals) / len(vals) if vals else 0.0,
        "median_clv": med,
        "positive_clv_rate": sum(v > 0 for v in vals) / len(vals) if vals else 0.0,
        "roi": pnl / bets if bets else 0.0,
    }


def _choose_gate(tune_by_year):
    merged = [r for y in sorted(tune_by_year) for r in tune_by_year[y]]
    best = None
    near = None
    for edge in EDGE_GRID:
        total = _entry_stats(merged, edge)
        yearly = {str(y): _entry_stats(rows, edge) for y, rows in tune_by_year.items()}
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
            "side": "away",
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


def _market_binary_logloss(rows):
    probs = [pricing.devig(r["op"])[2] for r in rows]
    return _binary_logloss(probs, [r["y"] for r in rows])


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

    all_data = [r for lg in TOP5 for r in data_by_league[lg]]
    local = data_by_league[TARGET]
    hyper = _select_hyper(all_data, local)

    result = {
        "_method": "M17.4 pooled/local binary Serie-A away-win classifier + Elo + dual-timescale features; no market features",
        "_target": "Serie A away moneyline/1X2 away side",
        "_splits": {
            "hyper_A": "train<=2019 validate SerieA 2020 binary logloss",
            "hyper_B": "train<=2020 validate SerieA 2021 binary logloss",
            "entry_tune": "rolling OOS SerieA 2022 + 2023 CLV",
            "strict_holdout": "rolling OOS SerieA 2024",
            "diagnostic_only": "rolling OOS SerieA 2025",
        },
        "_release_rule": "robust tune gate + strict 2024 >=15 bets, mean/median CLV>0, positive CLV rate>=52%",
        "coverage": coverage,
        "samples": {k: len(v) for k, v in data_by_league.items()},
        "hyper": hyper,
    }
    log = [f"M17.4: pooled Top-5={len(all_data)} rows + SerieA local={len(local)} rows"]

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
    edge = use_gate["edge"] if use_gate else 0.02
    hold = _entry_stats(hold_eval, edge) if hold_eval else dict(empty)
    diag = _entry_stats(diag_eval, edge) if diag_eval else dict(empty)

    hold_rows = [r for r in local if r["season"] == 2024]
    hold_model_ll = _binary_logloss(
        [r["p"] for r in hold_eval], [r["y"] for r in hold_eval]
    ) if hold_eval else 9.0
    hold_market_ll = _market_binary_logloss(hold_rows) if hold_rows else 9.0

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
