"""M17.1: rolling pre-match classifier with real shot data and strict walk-forward.

No bookmaker odds are model features.

Model selection:
- fold A: train <=2021/22, validate 2022/23
- fold B: train <=2022/23, validate 2023/24
- choose L2 + probability calibration by mean outcome logloss only
- refit <=2023/24 and choose entry gate on 2024/25 by CLV
- refit <=2024/25 and diagnose 2025/26
2025/26 is diagnostic only because it has already been inspected.

Features are strictly pre-match and use real Mongo HS/HST/AS/AST plus goals,
real xG (Top-5) or learned chance proxy (other leagues), form, home/away splits,
rest and league baselines. Market prices enter only after probabilities exist.
"""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from . import pricing
from .m12_research import _num, _season_start
from .m13_research import load_real_xg
from .m14_research import load_league, train_proxy
from .models.poisson import Match

OUT = Path("data/m17_1_validation.json")

TOP5 = {
    "bundesliga": "D1", "epl": "E0", "laliga": "SP1",
    "seriea": "I1", "ligue1": "F1",
}
EUROPE = {
    "2bundesliga": "D2", "championship": "E1", "eredivisie": "N1",
    "primeira": "P1", "belgium": "B1", "turkey": "T1",
    "scotland": "SC0", "greece": "G1",
}

L2_GRID = (0.05, 0.25, 1.0)
CALIB = (0.75, 0.90, 1.00, 1.10)
EDGE_GRID = (0.02, 0.03, 0.05, 0.075, 0.10)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0, 6.0)
SIDES = ("all", "home", "draw", "away")


@dataclass
class TeamState:
    n: int = 0
    gf: float = 1.35
    ga: float = 1.35
    xf: float = 1.35
    xa: float = 1.35
    shots_f: float = 12.0
    shots_a: float = 12.0
    sot_f: float = 4.2
    sot_a: float = 4.2
    pts: float = 1.35
    home_gf: float = 1.45
    home_ga: float = 1.20
    away_gf: float = 1.20
    away_ga: float = 1.45
    last_date: date | None = None


def _ew(old: float, new: float, alpha: float = 0.16) -> float:
    return (1.0 - alpha) * old + alpha * new


def _rest(st: TeamState, d: date) -> float:
    if st.last_date is None:
        return 7.0
    return float(max(2, min(14, (d - st.last_date).days)))


def _points(gf: float, ga: float) -> float:
    return 3.0 if gf > ga else (1.0 if gf == ga else 0.0)


def _mongo_db(client):
    from pymongo.errors import ConfigurationError
    try:
        db = client.get_default_database()
    except ConfigurationError:
        db = None
    return db if db is not None else client["euro_football"]


def load_real_shots(code: str, start_year: int = 2017, end_year: int = 2025) -> dict:
    """Read-only raw shot map keyed by season/home/away.

    League fixtures have one home-away occurrence per season, so this survives
    the known 2025 Mongo day/month date corruption without using results to join.
    """
    from pymongo import MongoClient, timeout

    uri = (os.environ.get("MONGO_SOCCER") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER fehlt")
    start = datetime(start_year, 7, 1, tzinfo=timezone.utc)
    end = datetime(end_year + 1, 7, 1, tzinfo=timezone.utc)
    proj = {
        "_id": 0, "Date": 1, "HomeTeam": 1, "AwayTeam": 1,
        "HS": 1, "AS": 1, "HST": 1, "AST": 1,
    }
    grouped = defaultdict(list)
    with timeout(120):
        with MongoClient(uri, serverSelectionTimeoutMS=15000,
                         connectTimeoutMS=10000, socketTimeoutMS=30000,
                         appname="oddswatch-m17-real-shots") as client:
            cur = _mongo_db(client)["mains"].find(
                {"Div": code, "Date": {"$gte": start, "$lt": end}},
                proj,
            )
            for d in cur:
                dt = d.get("Date")
                h, a = d.get("HomeTeam"), d.get("AwayTeam")
                vals = [_num(d.get(k)) for k in ("HS", "AS", "HST", "AST")]
                if not isinstance(dt, datetime) or not h or not a or any(v is None for v in vals):
                    continue
                hs, ass, hst, ast = vals
                if min(hs, ass, hst, ast) < 0 or hst > hs or ast > ass:
                    continue
                grouped[(_season_start(dt.date()), h, a)].append(
                    (float(hs), float(ass), float(hst), float(ast))
                )
    # Keep only unambiguous league fixture joins.
    return {k: v[0] for k, v in grouped.items() if len(v) == 1}


def _features(hs: TeamState, as_: TeamState, league: dict, d: date) -> list[float]:
    conf_h = min(hs.n, 20) / 20.0
    conf_a = min(as_.n, 20) / 20.0
    return [
        1.0,
        hs.gf - as_.ga,
        as_.gf - hs.ga,
        hs.xf - as_.xa,
        as_.xf - hs.xa,
        hs.sot_f - as_.sot_a,
        as_.sot_f - hs.sot_a,
        hs.shots_f - as_.shots_a,
        as_.shots_f - hs.shots_a,
        hs.pts - as_.pts,
        hs.home_gf - as_.away_ga,
        as_.away_gf - hs.home_ga,
        _rest(hs, d) - _rest(as_, d),
        conf_h - conf_a,
        league["home_rate"] - league["away_rate"],
        league["draw_rate"],
        league["goals"],
    ]


def _update(st: TeamState, gf: float, ga: float, xf: float, xa: float,
            sf: float, sa: float, sotf: float, sota: float, pts: float,
            d: date, is_home: bool) -> None:
    st.n += 1
    st.gf = _ew(st.gf, gf)
    st.ga = _ew(st.ga, ga)
    st.xf = _ew(st.xf, xf)
    st.xa = _ew(st.xa, xa)
    st.shots_f = _ew(st.shots_f, sf)
    st.shots_a = _ew(st.shots_a, sa)
    st.sot_f = _ew(st.sot_f, sotf)
    st.sot_a = _ew(st.sot_a, sota)
    st.pts = _ew(st.pts, pts)
    if is_home:
        st.home_gf = _ew(st.home_gf, gf)
        st.home_ga = _ew(st.home_ga, ga)
    else:
        st.away_gf = _ew(st.away_gf, gf)
        st.away_ga = _ew(st.away_ga, ga)
    st.last_date = d


def _xg(m: Match, home: bool) -> float:
    v = m.home_xg if home else m.away_xg
    return float(v if v is not None else (m.home_goals if home else m.away_goals))


def build_dataset(matches: list[Match], odds_rows: list[tuple], shot_map: dict) -> list[dict]:
    odds = {(d, h, a): (season, hg, ag, op, cl)
            for season, d, h, a, hg, ag, op, cl in odds_rows}
    states = defaultdict(TeamState)
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
        hs, as_ = states[h], states[a]

        if hs.n >= 6 and as_.n >= 6 and (d, h, a) in odds and shot is not None:
            s, hg, ag, op, cl = odds[(d, h, a)]
            out.append({
                "season": s, "date": d, "home": h, "away": a,
                "x": _features(hs, as_, league, d),
                "y": 0 if hg > ag else (1 if hg == ag else 2),
                "op": op, "cl": cl,
            })

        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = _xg(m, True), _xg(m, False)
        if shot is not None:
            hshots, ashots, hsot, asot = shot
            _update(hs, hg, ag, hx, ax, hshots, ashots, hsot, asot,
                    _points(hg, ag), d, True)
            _update(as_, ag, hg, ax, hx, ashots, hshots, asot, hsot,
                    _points(ag, hg), d, False)
        else:
            # No fake shot feature. Update non-shot state only via neutral prior carry.
            _update(hs, hg, ag, hx, ax, hs.shots_f, hs.shots_a, hs.sot_f, hs.sot_a,
                    _points(hg, ag), d, True)
            _update(as_, ag, hg, ax, hx, as_.shots_f, as_.shots_a, as_.sot_f, as_.sot_a,
                    _points(ag, hg), d, False)

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


def _softmax(z):
    m = max(z)
    ex = [math.exp(v - m) for v in z]
    s = sum(ex)
    return [v / s for v in ex]


def _calibrate(p, a):
    q = [max(v, 1e-12) ** a for v in p]
    s = sum(q)
    return [v / s for v in q]


def _standardizer(rows):
    p = len(rows[0])
    mean = [0.0] * p
    sd = [1.0] * p
    for j in range(1, p):
        vals = [x[j] for x in rows]
        mean[j] = sum(vals) / len(vals)
        var = sum((v - mean[j]) ** 2 for v in vals) / max(len(vals) - 1, 1)
        sd[j] = max(math.sqrt(var), 1e-6)
    return mean, sd


def _tx(rows, mean, sd):
    return [[x[0]] + [(x[j] - mean[j]) / sd[j] for j in range(1, len(x))]
            for x in rows]


def _fit(x, y, l2, epochs=35, lr=0.09):
    n, p = len(x), len(x[0])
    w = [[0.0] * p for _ in range(3)]
    for ep in range(epochs):
        g = [[0.0] * p for _ in range(3)]
        inv = 1.0 / n
        for xi, yi in zip(x, y):
            pr = _softmax([sum(a*b for a, b in zip(wk, xi)) for wk in w])
            for k in range(3):
                e = (pr[k] - (1.0 if yi == k else 0.0)) * inv
                for j, xv in enumerate(xi):
                    g[k][j] += e * xv
        for k in range(3):
            for j in range(1, p):
                g[k][j] += l2 * w[k][j] / n
        step = lr / (1.0 + ep / 20.0)
        for k in range(3):
            for j in range(p):
                w[k][j] -= step * g[k][j]
    return w


def _pred(w, x):
    return _softmax([sum(a*b for a, b in zip(wk, x)) for wk in w])


def _logloss(probs, ys):
    return -sum(math.log(max(p[y], 1e-12)) for p, y in zip(probs, ys)) / len(ys)


def _fit_predict(train, test, l2, calib):
    mean, sd = _standardizer([r["x"] for r in train])
    xtr = _tx([r["x"] for r in train], mean, sd)
    xte = _tx([r["x"] for r in test], mean, sd)
    w = _fit(xtr, [r["y"] for r in train], l2)
    return [_calibrate(_pred(w, x), calib) for x in xte]


def _select_hyper(data):
    folds = [
        ([r for r in data if r["season"] <= 2021],
         [r for r in data if r["season"] == 2022]),
        ([r for r in data if r["season"] <= 2022],
         [r for r in data if r["season"] == 2023]),
    ]
    if any(len(tr) < 500 or len(va) < 100 for tr, va in folds):
        return None
    best = None
    for l2 in L2_GRID:
        raw = []
        for tr, va in folds:
            # Fit once per L2; calibration is cheap after that.
            mean, sd = _standardizer([r["x"] for r in tr])
            w = _fit(_tx([r["x"] for r in tr], mean, sd),
                     [r["y"] for r in tr], l2)
            raw.append((va, [_pred(w, x) for x in _tx([r["x"] for r in va], mean, sd)]))
        for a in CALIB:
            losses = []
            for va, pp in raw:
                losses.append(_logloss([_calibrate(p, a) for p in pp],
                                       [r["y"] for r in va]))
            score = sum(losses) / len(losses)
            if best is None or score < best["cv_logloss"]:
                best = {"l2": l2, "calib": a, "cv_logloss": score,
                        "fold_logloss": losses}
    return best


def _attach(rows, probs):
    out = []
    for r, p in zip(rows, probs):
        z = dict(r)
        z["p"] = p
        out.append(z)
    return out


def _entry_stats(rows, edge, cap, side):
    idx = {"home": 0, "draw": 1, "away": 2}.get(side)
    bets = 0
    pnl = 0.0
    clv = []
    for r in rows:
        pc = pricing.devig(r["cl"])
        for k in range(3):
            if idx is not None and k != idx:
                continue
            if r["p"][k] * r["op"][k] - 1.0 < edge or r["op"][k] > cap:
                continue
            bets += 1
            pnl += r["op"][k] - 1.0 if r["y"] == k else -1.0
            clv.append(r["op"][k] * pc[k] - 1.0)
    vals = sorted(clv)
    med = 0.0
    if vals:
        n = len(vals)
        med = vals[n//2] if n % 2 else (vals[n//2-1] + vals[n//2]) / 2
    return {
        "bets": bets,
        "clv": sum(vals) / len(vals) if vals else 0.0,
        "median_clv": med,
        "positive_clv_rate": sum(v > 0 for v in vals) / len(vals) if vals else 0.0,
        "roi": pnl / bets if bets else 0.0,
    }


def _choose_gate(rows):
    best = None
    for edge in EDGE_GRID:
        for cap in ODDS_CAP:
            for side in SIDES:
                s = _entry_stats(rows, edge, cap, side)
                if s["bets"] < 40:
                    continue
                if s["clv"] <= 0 or s["median_clv"] <= 0 or s["positive_clv_rate"] < 0.52:
                    continue
                score = s["clv"] * math.sqrt(s["bets"])
                if best is None or score > best["score"]:
                    best = {"edge": edge, "cap": cap, "side": side,
                            "stats": s, "score": score}
    return best


def _run_league(matches, odds_rows, shot_map):
    data = build_dataset(matches, odds_rows, shot_map)
    hyper = _select_hyper(data)
    if hyper is None:
        return {"validated": False, "reason": "too little strict walk-forward data",
                "samples": len(data)}

    gate_train = [r for r in data if r["season"] <= 2023]
    gate_rows = [r for r in data if r["season"] == 2024]
    diag_train = [r for r in data if r["season"] <= 2024]
    diag_rows = [r for r in data if r["season"] == 2025]
    if len(gate_rows) < 100 or len(diag_rows) < 100:
        return {"validated": False, "reason": "too little gate/diagnostic data",
                "counts": {"gate": len(gate_rows), "diag": len(diag_rows)}}

    gp = _fit_predict(gate_train, gate_rows, hyper["l2"], hyper["calib"])
    gate_eval = _attach(gate_rows, gp)
    gate = _choose_gate(gate_eval)

    dp = _fit_predict(diag_train, diag_rows, hyper["l2"], hyper["calib"])
    diag_eval = _attach(diag_rows, dp)
    diag = _entry_stats(diag_eval, gate["edge"], gate["cap"], gate["side"]) if gate else {
        "bets": 0, "clv": 0.0, "median_clv": 0.0,
        "positive_clv_rate": 0.0, "roi": 0.0,
    }
    model_ll = _logloss(dp, [r["y"] for r in diag_rows])
    open_ll = _logloss([pricing.devig(r["op"]) for r in diag_rows],
                       [r["y"] for r in diag_rows])
    return {
        "validated": False,
        "samples": len(data),
        "hyper": hyper,
        "gate": gate,
        "diagnostic_2025": diag,
        "diagnostic_logloss": {
            "model": model_ll, "opening": open_ll, "gain": open_ll - model_ll
        },
    }


def run(out: Path = OUT):
    result = {
        "_method": "M17.1 rolling classifier + real HS/HST; strict walk-forward; no market features",
        "_splits": {
            "hyper_fold_A": "train<=2021 validate=2022",
            "hyper_fold_B": "train<=2022 validate=2023",
            "entry_gate": "fit<=2023 evaluate CLV on 2024",
            "diagnostic_only": "refit<=2024 evaluate 2025",
        },
        "_note": "2025 is diagnostic only, not fresh live validation",
    }
    log = ["M17.1: real HS/HST + strict walk-forward"]

    for league, code in TOP5.items():
        ms, rows, _ = load_real_xg(code)
        shots = load_real_shots(code)
        r = _run_league(ms, rows, shots)
        result[league] = r
        d = r.get("diagnostic_2025", {})
        log.append(
            f"{league}: shots={len(shots)} gate={r.get('gate')} | "
            f"2025 n={d.get('bets',0)} CLV={d.get('clv',0)*100:+.2f}% "
            f"med={d.get('median_clv',0)*100:+.2f}% pos={d.get('positive_clv_rate',0)*100:.1f}% "
            f"ROI={d.get('roi',0)*100:+.2f}%"
        )

    proxy = train_proxy()
    result["_proxy"] = {"n": proxy["n"], "rmse": proxy["rmse"], "beta": proxy["beta"]}
    for league, code in EUROPE.items():
        ms, rows, _ = load_league(code, proxy)
        shots = load_real_shots(code)
        r = _run_league(ms, rows, shots)
        result[league] = r
        d = r.get("diagnostic_2025", {})
        log.append(
            f"{league}: shots={len(shots)} gate={r.get('gate')} | "
            f"2025 n={d.get('bets',0)} CLV={d.get('clv',0)*100:+.2f}% "
            f"med={d.get('median_clv',0)*100:+.2f}% pos={d.get('positive_clv_rate',0)*100:.1f}% "
            f"ROI={d.get('roi',0)*100:+.2f}%"
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return log


if __name__ == "__main__":
    for line in run():
        print(line)
