"""M14 Europa: gelernter Chance-Quality-Proxy für Nicht-Top-5-Ligen.

Kein kostenpflichtiger xG-Feed:
1. Proxy-Koeffizienten werden ausschließlich auf Top-5 2019/20-2022/23
   gegen echtes Understat Match-xG gelernt.
2. Der eingefrorene Proxy wird aus Mongo HS/HST/HC bzw. AS/AST/AC
   für andere europäische Ligen berechnet.
3. Fair-Modell nutzt keine Marktquoten. Pinnacle Opening/Closing dienen
   ausschließlich Tuning-/Holdout-Messung.
4. Tune: 2023/24 + 2024/25. Holdout: 2025/26.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from . import fetch, matching, pricing
from .m12_research import _num, _odds, _season_start
from .m13_research import _resolve_understat
from .models.m9 import M9Model, M9Params
from .models.poisson import Match
from .sources import football_data as fd, understat

TOP5 = ("D1", "E0", "SP1", "I1", "F1")
LEAGUES = {
    "2bundesliga": "D2",
    "championship": "E1",
    "eredivisie": "N1",
    "primeira": "P1",
    "belgium": "B1",
    "turkey": "T1",
    "scotland": "SC0",
    "greece": "G1",
}
PROXY_YEARS = range(2019, 2023)
CALIB = (0.80, 0.90, 1.00, 1.10)
EDGE = (0.03, 0.05, 0.075, 0.10, 0.125, 0.15)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0, 6.0)
SIDES = ("all", "home", "draw", "away")
OUT = Path("data/m14_validation.json")

VARIANTS = [
    M9Params(half_life_days=120, xg_blend=0.45, elo_scale=0.08, xg_form_scale=0.04),
    M9Params(half_life_days=180, xg_blend=0.55, elo_scale=0.10, xg_form_scale=0.05),
    M9Params(half_life_days=180, xg_blend=0.65, elo_scale=0.10, xg_form_scale=0.06),
    M9Params(half_life_days=270, xg_blend=0.55, elo_scale=0.10, xg_form_scale=0.05),
    M9Params(half_life_days=365, xg_blend=0.45, elo_scale=0.08, xg_form_scale=0.04),
]


def _mongo_db(client):
    from pymongo.errors import ConfigurationError
    try:
        db = client.get_default_database()
    except ConfigurationError:
        db = None
    return db if db is not None else client["euro_football"]


def _projection():
    return {
        "_id": 0, "Date": 1, "Div": 1, "HomeTeam": 1, "AwayTeam": 1,
        "FTHG": 1, "FTAG": 1, "FTR": 1,
        "HS": 1, "AS": 1, "HST": 1, "AST": 1, "HC": 1, "AC": 1,
        "PSH": 1, "PSD": 1, "PSA": 1, "PSCH": 1, "PSCD": 1, "PSCA": 1,
    }


def _features(shots, sot, corners, home: bool) -> list[float] | None:
    vals = [_num(shots), _num(sot), _num(corners)]
    if any(v is None for v in vals):
        return None
    s, st, c = vals
    if min(s, st, c) < 0 or st > s:
        return None
    return [1.0, st, max(s - st, 0.0), c, 1.0 if home else 0.0]


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Kleine lineare Gleichung per Gauß-Elimination, ohne neue Dependency."""
    n = len(b)
    m = [list(a[i]) + [float(b[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("singuläres Proxy-System")
        m[col], m[pivot] = m[pivot], m[col]
        z = m[col][col]
        m[col] = [x / z for x in m[col]]
        for r in range(n):
            if r == col:
                continue
            f = m[r][col]
            if abs(f) < 1e-15:
                continue
            m[r] = [m[r][j] - f * m[col][j] for j in range(n + 1)]
    return [m[i][-1] for i in range(n)]


def fit_proxy(rows: list[tuple[list[float], float]], ridge: float = 10.0) -> dict:
    if len(rows) < 1000:
        raise ValueError("zu wenig echte xG-Zeilen für M14 Proxy")
    p = len(rows[0][0])
    xtx = [[0.0] * p for _ in range(p)]
    xty = [0.0] * p
    for x, y in rows:
        for i in range(p):
            xty[i] += x[i] * y
            for j in range(p):
                xtx[i][j] += x[i] * x[j]
    for i in range(1, p):  # Intercept nicht regularisieren
        xtx[i][i] += ridge
    beta = _solve(xtx, xty)

    # Chance-Erzeugung darf durch mehr Schüsse/SoT/Ecken nicht sinken.
    beta[1] = max(beta[1], 0.0)
    beta[2] = max(beta[2], 0.0)
    beta[3] = max(beta[3], 0.0)

    err = 0.0
    for x, y in rows:
        pred = sum(v * w for v, w in zip(x, beta))
        err += (pred - y) ** 2
    rmse = math.sqrt(err / len(rows))
    return {
        "beta": beta,
        "n": len(rows),
        "rmse": rmse,
        "features": ["intercept", "shots_on_target", "shots_off_target",
                     "corners", "home"],
    }


def proxy_xg(proxy: dict, shots, sot, corners, home: bool) -> float | None:
    x = _features(shots, sot, corners, home)
    if x is None:
        return None
    y = sum(v * w for v, w in zip(x, proxy["beta"]))
    return max(0.05, min(5.5, y))


def train_proxy(years=None) -> dict:
    """Learn xG proxy using ONLY explicitly allowed past seasons when provided."""
    selected_years = tuple(PROXY_YEARS if years is None else years)
    if not selected_years:
        raise ValueError("at least one completed proxy training season required")
    from pymongo import MongoClient, timeout

    uri = (os.environ.get("MONGO_SOCCER") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER fehlt")

    samples = []
    per_league = {}
    with timeout(180):
        with MongoClient(uri, serverSelectionTimeoutMS=15000,
                         connectTimeoutMS=10000, socketTimeoutMS=30000,
                         appname="oddswatch-m14-proxy") as client:
            db = _mongo_db(client)
            col = db["mains"]
            for code in TOP5:
                n = 0
                for y in selected_years:
                    start = datetime(y, 7, 1, tzinfo=timezone.utc)
                    end = datetime(y + 1, 7, 1, tzinfo=timezone.utc)
                    docs = list(col.find({
                        "Div": code, "Date": {"$gte": start, "$lt": end},
                        "FTHG": {"$exists": True, "$ne": None},
                        "FTAG": {"$exists": True, "$ne": None},
                    }, _projection()).sort("Date", 1))
                    us, err = understat.season_matches(code, y, cache_days=30)
                    if err or not us:
                        continue
                    for d in docs:
                        dt = d.get("Date")
                        h, a = d.get("HomeTeam"), d.get("AwayTeam")
                        hg, ag = _num(d.get("FTHG")), _num(d.get("FTAG"))
                        if not isinstance(dt, datetime) or not h or not a or hg is None or ag is None:
                            continue
                        u, kind = _resolve_understat(dt.date(), h, a, hg, ag, us)
                        if u is None:
                            continue
                        hf = _features(d.get("HS"), d.get("HST"), d.get("HC"), True)
                        af = _features(d.get("AS"), d.get("AST"), d.get("AC"), False)
                        if hf is not None:
                            samples.append((hf, float(u.home_xg)))
                            n += 1
                        if af is not None:
                            samples.append((af, float(u.away_xg)))
                            n += 1
                per_league[code] = n
    p = fit_proxy(samples)
    p["per_league"] = per_league
    p["train_seasons"] = list(selected_years)
    return p


def _canonical_fd_by_season(code: str, start_year: int, end_year: int):
    out = {}
    errors = {}
    for y in range(start_year, end_year + 1):
        text, err = fetch.get(
            fd.csv_url(code, y),
            cache_days=30 if y < end_year else 1,
        )
        if not text:
            out[y] = []
            errors[y] = err or "football-data fehlt"
            continue
        out[y] = fd.parse(text)[0]
    return out, errors


def load_league(code: str, proxy: dict, start_year: int = 2017,
                end_year: int = 2025) -> tuple[list[Match], list[tuple], dict]:
    """Mongo-Historie, aber Datum gegen football-data kanonisiert."""
    from pymongo import MongoClient, timeout

    uri = (os.environ.get("MONGO_SOCCER") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER fehlt")

    fd_by_season, fd_errors = _canonical_fd_by_season(code, start_year, end_year)
    start = datetime(start_year, 7, 1, tzinfo=timezone.utc)
    end = datetime(end_year + 1, 7, 1, tzinfo=timezone.utc)
    matches = []
    rows = []
    seen = set()
    shots_ok = 0
    canonical_exact = canonical_swap = canonical_score = excluded = 0

    with timeout(120):
        with MongoClient(uri, serverSelectionTimeoutMS=15000,
                         connectTimeoutMS=10000, socketTimeoutMS=30000,
                         appname="oddswatch-m14-readonly") as client:
            db = _mongo_db(client)
            cur = db["mains"].find({
                "Div": code,
                "Date": {"$gte": start, "$lt": end},
                "FTHG": {"$exists": True, "$ne": None},
                "FTAG": {"$exists": True, "$ne": None},
            }, _projection()).sort("Date", 1)

            for doc in cur:
                dt = doc.get("Date")
                h, a = doc.get("HomeTeam"), doc.get("AwayTeam")
                hg, ag = _num(doc.get("FTHG")), _num(doc.get("FTAG"))
                if not isinstance(dt, datetime) or not h or not a or hg is None or ag is None:
                    continue

                raw_d = dt.date()
                season = _season_start(raw_d)
                candidates = fd_by_season.get(season, [])
                u, kind = _resolve_understat(raw_d, h, a, hg, ag, candidates)
                if u is None:
                    excluded += 1
                    continue
                d = u.date
                if kind == "exact":
                    canonical_exact += 1
                elif kind == "swap":
                    canonical_swap += 1
                else:
                    canonical_score += 1

                key = (d, h, a)
                if key in seen:
                    continue
                seen.add(key)

                hx = proxy_xg(proxy, doc.get("HS"), doc.get("HST"), doc.get("HC"), True)
                ax = proxy_xg(proxy, doc.get("AS"), doc.get("AST"), doc.get("AC"), False)
                if hx is not None and ax is not None:
                    shots_ok += 1
                matches.append(Match(d, h, a, hg, ag, hx, ax))

                op = _odds(doc, ("PSH", "PSD", "PSA"))
                cl = _odds(doc, ("PSCH", "PSCD", "PSCA"))
                if op and cl:
                    rows.append((_season_start(d), d, h, a, int(hg), int(ag), op, cl))

    matches.sort(key=lambda m: m.date)
    rows.sort(key=lambda r: r[1])
    return matches, rows, {
        "matches": len(matches),
        "proxy_matches": shots_ok,
        "proxy_coverage": shots_ok / len(matches) if matches else 0.0,
        "odds_rows": len(rows),
        "canonical_exact": canonical_exact,
        "canonical_day_month_fixed": canonical_swap,
        "canonical_team_score_fixed": canonical_score,
        "excluded_unreconciled": excluded,
        "football_data_errors": {
            str(y): e for y, e in fd_errors.items() if e
        },
    }


def _calibrate(p: list[float], a: float) -> list[float]:
    q = [max(x, 1e-9) ** a for x in p]
    z = sum(q)
    return [x / z for x in q]


def samples(matches: list[Match], rows: list[tuple], seasons: set[int],
            params: M9Params) -> list[tuple]:
    out = []
    model = None
    last_fit = None
    for season, d, h, a, hg, ag, op, cl in rows:
        if season not in seasons:
            continue
        if last_fit is None or (d - last_fit).days >= 14:
            hist = [m for m in matches if m.date < d]
            try:
                model = M9Model.fit(hist, d, params)
            except ValueError:
                model = None
            last_fit = d
        if model is None:
            continue
        if h not in model.goals.attack or a not in model.goals.attack:
            continue
        if h not in model.chances.attack or a not in model.chances.attack:
            continue
        mk = model.markets(h, a, kickoff=d)
        out.append((season, [mk["1"], mk["X"], mk["2"]],
                    pricing.devig(op), pricing.devig(cl),
                    [hg > ag, hg == ag, hg < ag], op))
    return out


def model_score(rows: list[tuple], calib: float) -> dict:
    if not rows:
        return {"n": 0, "logloss": 9.0, "market": 9.0, "gain": -9.0}
    lm = lo = 0.0
    for _, pm, po, _, y, _ in rows:
        p = _calibrate(pm, calib)
        i = y.index(True)
        lm -= math.log(max(p[i], 1e-12))
        lo -= math.log(max(po[i], 1e-12))
    n = len(rows)
    return {"n": n, "logloss": lm/n, "market": lo/n, "gain": lo/n-lm/n}


def strategy(rows: list[tuple], calib: float, min_edge: float,
             max_odds: float, side: str) -> dict:
    idx = {"home": 0, "draw": 1, "away": 2}.get(side)
    bets = 0
    pnl = 0.0
    clv = []
    for _, pm, _, pc, y, odds in rows:
        p = _calibrate(pm, calib)
        for k in range(3):
            if idx is not None and k != idx:
                continue
            ev = p[k] * odds[k] - 1.0
            if ev < min_edge or odds[k] > max_odds:
                continue
            bets += 1
            pnl += odds[k] - 1.0 if y[k] else -1.0
            clv.append(odds[k] * pc[k] - 1.0)
    return {
        "bets": bets,
        "roi": pnl / bets if bets else 0.0,
        "clv": sum(clv) / len(clv) if clv else 0.0,
    }


def choose_entry(rows: list[tuple], calib: float, tune_years: set[int]):
    best_cfg = best = None
    best_score = -999.0
    for edge in EDGE:
        for cap in ODDS_CAP:
            for side in SIDES:
                cfg = {"min_edge": edge, "max_odds": cap, "side": side}
                yearly = {
                    y: strategy([r for r in rows if r[0] == y], calib, **cfg)
                    for y in sorted(tune_years)
                }
                total = strategy(rows, calib, **cfg)
                if total["bets"] < 80:
                    continue
                if any(v["bets"] < 25 or v["clv"] <= 0 for v in yearly.values()):
                    continue
                worst = min(v["clv"] for v in yearly.values())
                score = worst * math.sqrt(total["bets"])
                if score > best_score:
                    best_score, best_cfg, best = score, cfg, {
                        "total": total, "per_year": yearly
                    }
    return best_cfg, best


def run(today: date | None = None, out: Path = OUT,
        leagues: list[str] | None = None) -> list[str]:
    today = today or date.today()
    tune = {2023, 2024}
    hold = {2025}
    selected = LEAGUES if not leagues else {
        k: LEAGUES[k] for k in leagues if k in LEAGUES
    }

    proxy = train_proxy()
    result = {
        "_stand": today.isoformat(),
        "_method": "M14 CLV-first learned Understat-calibrated shot/corner proxy; no market features",
        "_validation_target": "positive closing line value; ROI/logloss diagnostic only",
        "_proxy": proxy,
        "_tune": sorted(tune),
        "_holdout": sorted(hold),
    }
    b = proxy["beta"]
    log = [
        "M14: gelernter Chancenproxy aus Top-5 2019-2022; "
        "Tune 2023/24+2024/25, Holdout 2025/26",
        f"Proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f} | "
        f"b0={b[0]:+.3f} SoT={b[1]:+.3f} Off={b[2]:+.3f} "
        f"Corner={b[3]:+.3f} Home={b[4]:+.3f}",
    ]

    for league, code in selected.items():
        ms, rows, cov = load_league(code, proxy)
        if cov["proxy_coverage"] < 0.70:
            result[league] = {
                "validated": False, "reason": "Chance-Proxy-Abdeckung <70%",
                "coverage": cov,
            }
            log.append(
                f"{league}: Proxy-Abdeckung {cov['proxy_coverage']*100:.1f}% -> nicht getestet"
            )
            continue

        # CLV-first: Variante, Kalibrierung UND Entry-Regel werden gemeinsam
        # nur auf den beiden Tune-Saisons gewählt. LogLoss ist rein diagnostisch.
        best = None
        had_samples = False
        for vi, params in enumerate(VARIANTS):
            s = samples(ms, rows, tune | hold, params)
            tr = [x for x in s if x[0] in tune]
            ho = [x for x in s if x[0] in hold]
            if len(tr) < 300 or len(ho) < 120:
                continue
            had_samples = True
            for a in CALIB:
                cfg, tune_stats = choose_entry(tr, a, tune)
                if not cfg or not tune_stats:
                    continue
                worst_clv = min(v["clv"] for v in tune_stats["per_year"].values())
                total_bets = tune_stats["total"]["bets"]
                clv_score = worst_clv * math.sqrt(total_bets)
                if best is None or clv_score > best["clv_score"]:
                    best = {
                        "variant": vi, "params": asdict(params), "calib": a,
                        "train_score": model_score(tr, a),
                        "train": tr, "hold": ho,
                        "gate": cfg, "tune": tune_stats,
                        "clv_score": clv_score,
                    }

        if best is None:
            reason = "kein robuster positiver Tune-CLV" if had_samples else "zu wenig OOS-Daten"
            result[league] = {
                "validated": False, "reason": reason,
                "coverage": cov,
            }
            log.append(
                f"{league}: {reason} | {cov['matches']} Spiele/"
                f"{cov['odds_rows']} Odds | Proxy {cov['proxy_coverage']*100:.1f}%"
            )
            continue

        cfg, tune_stats = best["gate"], best["tune"]
        hs = model_score(best["hold"], best["calib"])
        he = strategy(best["hold"], best["calib"], **cfg) if cfg else {
            "bets": 0, "clv": 0.0, "median_clv": 0.0,
            "positive_clv_rate": 0.0, "roi": 0.0
        }
        validated = bool(
            cfg and he["bets"] >= 40 and he["clv"] > 0
        )
        result[league] = {
            "validated": validated,
            "variant": best["variant"],
            "params": best["params"],
            "calib": best["calib"],
            "coverage": cov,
            "train_score": best["train_score"],
            "gate": cfg,
            "tune": tune_stats,
            "holdout_score": hs,
            "holdout": he,
        }
        log.append(
            f"{league}: M14 v{best['variant']} a={best['calib']:.2f} | "
            f"Proxy {cov['proxy_coverage']*100:.1f}% | "
            f"Holdout dLL {hs['gain']:+.4f} | "
            f"{he['bets']} Bets CLV {he['clv']*100:+.2f}% "
            f"ROI {he['roi']*100:+.2f}% -> "
            + ("CLV-VALIDIERT" if validated else "nicht CLV-validiert")
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log
