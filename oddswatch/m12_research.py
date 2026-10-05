"""M12: Mongo Long-History OOS Research.

Historie: euro_football.mains (read-only, MONGO_SOCCER).
Fair-Modell: M9 Dual-Poisson (Tore + Schuss-xG-Proxy + Elo/Form/Rest).
Marktquoten sind KEINE Modellfeatures. Pinnacle Opening/Closing werden nur
zur Kalibrierungs-/Entry-Auswahl auf Tuning-Saisons und zur Holdout-Messung benutzt.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from . import pricing
from .models.m9 import M9Model, M9Params
from .models.poisson import Match

LEAGUES = {
    "bundesliga": "D1", "2bundesliga": "D2",
    "epl": "E0", "championship": "E1",
    "laliga": "SP1", "seriea": "I1", "ligue1": "F1",
    "eredivisie": "N1", "primeira": "P1", "belgium": "B1",
    "turkey": "T1", "scotland": "SC0", "greece": "G1",
}
CALIB = (0.80, 0.90, 1.00, 1.10)
EDGE = (0.03, 0.05, 0.075, 0.10, 0.125, 0.15)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0, 6.0, 10.0)
SIDES = ("all", "home", "draw", "away")
OUT = Path("data/m12_validation.json")

VARIANTS = [
    M9Params(half_life_days=120, xg_blend=0.50, elo_scale=0.08, xg_form_scale=0.04),
    M9Params(half_life_days=180, xg_blend=0.60, elo_scale=0.10, xg_form_scale=0.06),
    M9Params(half_life_days=180, xg_blend=0.75, elo_scale=0.12, xg_form_scale=0.08),
    M9Params(half_life_days=365, xg_blend=0.60, elo_scale=0.10, xg_form_scale=0.06),
]


def _season_start(d: date) -> int:
    return d.year if d.month >= 7 else d.year - 1


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _odds(doc: dict, keys: tuple[str, str, str]) -> list[float] | None:
    vals = [_num(doc.get(k)) for k in keys]
    if any(v is None or v <= 1.0 for v in vals):
        return None
    return vals


def _shot_xg(doc: dict) -> tuple[float | None, float | None]:
    hs, hst = _num(doc.get("HS")), _num(doc.get("HST"))
    a_s, ast = _num(doc.get("AS")), _num(doc.get("AST"))
    if None in (hs, hst, a_s, ast):
        return None, None
    # Gleiche robuste Proxy-Definition wie bisher: SoT stark, restliche Schüsse schwach.
    hx = 0.30 * hst + 0.03 * max(hs - hst, 0.0)
    ax = 0.30 * ast + 0.03 * max(a_s - ast, 0.0)
    return hx, ax


def load_mongo(code: str, start_year: int, end_year: int) -> tuple[list[Match], list[tuple]]:
    from pymongo import MongoClient, timeout

    uri = (os.environ.get("MONGO_SOCCER") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER fehlt")

    start = datetime(start_year, 7, 1, tzinfo=timezone.utc)
    end = datetime(end_year + 1, 7, 1, tzinfo=timezone.utc)
    projection = {
        "_id": 0, "Date": 1, "Div": 1, "HomeTeam": 1, "AwayTeam": 1,
        "FTHG": 1, "FTAG": 1, "FTR": 1, "HS": 1, "AS": 1, "HST": 1, "AST": 1,
        "PSH": 1, "PSD": 1, "PSA": 1, "PSCH": 1, "PSCD": 1, "PSCA": 1,
    }
    matches: list[Match] = []
    rows: list[tuple] = []

    with timeout(120):
        with MongoClient(uri, serverSelectionTimeoutMS=15000, connectTimeoutMS=10000,
                         socketTimeoutMS=20000, appname="oddswatch-m12-readonly") as client:
            from pymongo.errors import ConfigurationError
            try:
                db = client.get_default_database()
            except ConfigurationError:
                db = None
            if db is None:
                db = client["euro_football"]
            cur = db["mains"].find(
                {"Div": code, "Date": {"$gte": start, "$lt": end},
                 "FTHG": {"$exists": True, "$ne": None},
                 "FTAG": {"$exists": True, "$ne": None}},
                projection,
            ).sort("Date", 1)

            for doc in cur:
                dt = doc.get("Date")
                if not isinstance(dt, datetime):
                    continue
                d = dt.date()
                h, a = doc.get("HomeTeam"), doc.get("AwayTeam")
                hg, ag = _num(doc.get("FTHG")), _num(doc.get("FTAG"))
                if not h or not a or hg is None or ag is None:
                    continue
                hx, ax = _shot_xg(doc)
                matches.append(Match(d, h, a, hg, ag, hx, ax))

                op = _odds(doc, ("PSH", "PSD", "PSA"))
                cl = _odds(doc, ("PSCH", "PSCD", "PSCA"))
                if op and cl:
                    rows.append((_season_start(d), d, h, a, int(hg), int(ag), op, cl))

    return matches, rows


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
    return {"n": n, "logloss": lm / n, "market": lo / n, "gain": lo / n - lm / n}


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
    return {"bets": bets, "roi": pnl / bets if bets else 0.0,
            "clv": sum(clv) / len(clv) if clv else 0.0}


def choose_entry(rows: list[tuple], calib: float, tune_years: set[int]):
    best_cfg = best = None
    best_score = -999.0
    for edge in EDGE:
        for cap in ODDS_CAP:
            for side in SIDES:
                cfg = {"min_edge": edge, "max_odds": cap, "side": side}
                per_year = {
                    y: strategy([r for r in rows if r[0] == y], calib, **cfg)
                    for y in sorted(tune_years)
                }
                total = strategy(rows, calib, **cfg)
                if total["bets"] < 80:
                    continue
                if any(v["bets"] < 25 or v["clv"] <= 0 for v in per_year.values()):
                    continue
                if total["roi"] <= 0:
                    continue
                worst = min(v["clv"] for v in per_year.values())
                score = worst * math.sqrt(total["bets"]) + 0.05 * total["roi"]
                if score > best_score:
                    best_score, best_cfg, best = score, cfg, {
                        "total": total, "per_year": per_year,
                    }
    return best_cfg, best


def run(today: date | None = None, out: Path = OUT,
        leagues: list[str] | None = None) -> list[str]:
    today = today or date.today()
    # Unangetasteter Holdout 2025/26, Tuning 2023/24 + 2024/25.
    tune = {2023, 2024}
    hold = {2025}
    selected = LEAGUES if not leagues else {k: LEAGUES[k] for k in leagues if k in LEAGUES}
    result = {"_stand": today.isoformat(),
              "_method": "M12 Mongo long-history M9 fair; no market features"}
    log = ["M12: Mongo long-history; Tune 2023/24+2024/25, Holdout 2025/26"]

    for league, code in selected.items():
        ms, rows = load_mongo(code, 2017, 2025)
        if len(ms) < 1000 or len(rows) < 600:
            result[league] = {"validated": False, "reason": "zu wenig Mongo-Daten",
                              "matches": len(ms), "odds_rows": len(rows)}
            log.append(f"{league}: zu wenig Mongo-Daten ({len(ms)} Spiele/{len(rows)} Odds)")
            continue

        best = None
        for vi, params in enumerate(VARIANTS):
            s = samples(ms, rows, tune | hold, params)
            tr = [x for x in s if x[0] in tune]
            ho = [x for x in s if x[0] in hold]
            if len(tr) < 400 or len(ho) < 150:
                continue
            for a in CALIB:
                sc = model_score(tr, a)
                if best is None or sc["logloss"] < best["train_score"]["logloss"]:
                    best = {"variant": vi, "params": asdict(params), "calib": a,
                            "train_score": sc, "train": tr, "hold": ho}
        if best is None:
            result[league] = {"validated": False, "reason": "zu wenig OOS-Daten"}
            log.append(f"{league}: zu wenig OOS-Daten")
            continue

        cfg, tune_stats = choose_entry(best["train"], best["calib"], tune)
        hs = model_score(best["hold"], best["calib"])
        he = strategy(best["hold"], best["calib"], **cfg) if cfg else {
            "bets": 0, "clv": 0.0, "roi": 0.0
        }
        validated = bool(cfg and hs["gain"] > 0 and he["bets"] >= 40
                         and he["clv"] > 0 and he["roi"] > 0)
        result[league] = {
            "validated": validated,
            "variant": best["variant"], "params": best["params"],
            "calib": best["calib"], "matches": len(ms), "odds_rows": len(rows),
            "train_score": best["train_score"], "gate": cfg,
            "tune": tune_stats, "holdout_score": hs, "holdout": he,
        }
        log.append(
            f"{league}: M12 v{best['variant']} a={best['calib']:.2f} | "
            f"{len(ms)} Hist-Spiele/{len(rows)} Odds | "
            f"Holdout dLL-Gewinn {hs['gain']:+.4f} | "
            f"{he['bets']} Bets CLV {he['clv']*100:+.2f}% ROI {he['roi']*100:+.2f}% -> "
            + ("VALIDIERT" if validated else "nicht validiert")
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log
