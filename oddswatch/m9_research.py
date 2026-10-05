"""M9 OOS-Research: Dual-Poisson (Tore + Chancen) ohne Markt-Blend."""

from __future__ import annotations

import csv
import io
import itertools
import json
import math
from dataclasses import asdict
from datetime import date
from pathlib import Path

from . import pricing, fetch
from .models.m9 import M9Model, M9Params
from .sources import football_data as fd

LEAGUES = {
    "bundesliga": "D1", "2bundesliga": "D2", "epl": "E0", "championship": "E1",
    "laliga": "SP1", "seriea": "I1", "ligue1": "F1", "eredivisie": "N1",
    "primeira": "P1", "belgium": "B1", "turkey": "T1", "scotland": "SC0", "greece": "G1",
}
CALIB = (0.80, 0.90, 1.00, 1.10)
EDGE = (0.03, 0.05, 0.075, 0.10, 0.125, 0.15)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0, 6.0, 10.0)
SIDES = ("all", "home", "draw", "away")
OUT = Path("data/m9_validation.json")

VARIANTS = [
    M9Params(xg_blend=0.50, elo_scale=0.10, xg_form_scale=0.05),
    M9Params(xg_blend=0.65, elo_scale=0.10, xg_form_scale=0.08),
    M9Params(xg_blend=0.75, elo_scale=0.15, xg_form_scale=0.08),
    M9Params(xg_blend=0.85, elo_scale=0.15, xg_form_scale=0.10),
    M9Params(xg_blend=0.70, elo_scale=0.20, xg_form_scale=0.10),
    M9Params(half_life_days=365, xg_blend=0.75, elo_scale=0.15, xg_form_scale=0.08),
]


def _f(r: dict, k: str) -> float | None:
    try:
        x = float(r[k])
        return x if x > 1.0 else None
    except (KeyError, TypeError, ValueError):
        return None


def _load(code: str, years: list[int]) -> tuple[list, list[tuple[date, int, dict]]]:
    matches, rows = [], []
    for y in years:
        t, _ = fetch.get(fd.csv_url(code, y), cache_days=30 if y < years[-1] else 1)
        if not t:
            continue
        matches += fd.parse(t, shots_as_xg=True)[0]
        for r in csv.DictReader(io.StringIO(t.lstrip("\ufeff"))):
            if r.get("HomeTeam") and r.get("FTHG") not in (None, ""):
                rows.append((fd._d(r["Date"]), y, r))
    matches.sort(key=lambda m: m.date)
    rows.sort(key=lambda x: x[0])
    return matches, rows


def _calibrate(p: list[float], a: float) -> list[float]:
    q = [max(x, 1e-9) ** a for x in p]
    z = sum(q)
    return [x / z for x in q]


def samples(matches: list, rows: list[tuple[date, int, dict]], years: set[int],
            params: M9Params) -> list[tuple]:
    out = []
    model = None
    last_fit = None
    for d, season, r in rows:
        if season not in years:
            continue
        if last_fit is None or (d - last_fit).days >= 7:
            hist = [m for m in matches if m.date < d]
            if len(hist) < 180:
                continue
            model = M9Model.fit(hist, d, params)
            last_fit = d
        h, a = r["HomeTeam"], r["AwayTeam"]
        if model is None or h not in model.goals.attack or a not in model.goals.attack:
            continue
        op = [_f(r, k) for k in ("PSH", "PSD", "PSA")]
        cl = [_f(r, k) for k in ("PSCH", "PSCD", "PSCA")]
        if not all(op) or not all(cl):
            continue
        mk = model.markets(h, a, kickoff=d)
        hg, ag = int(float(r["FTHG"])), int(float(r["FTAG"]))
        out.append((season, [mk["1"], mk["X"], mk["2"]], pricing.devig(op),
                    pricing.devig(cl), [hg > ag, hg == ag, hg < ag], op))
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


def strategy(rows: list[tuple], calib: float, min_edge: float, max_odds: float,
             side: str) -> dict:
    idx = {"home": 0, "draw": 1, "away": 2}.get(side)
    bets = 0
    pnl = 0.0
    clv = []
    for _, pm, _, pc, y, odds in rows:
        p = _calibrate(pm, calib)
        for k in range(3):
            if idx is not None and k != idx:
                continue
            ev = p[k] * odds[k] - 1
            if ev < min_edge or odds[k] > max_odds:
                continue
            bets += 1
            pnl += odds[k] - 1 if y[k] else -1
            clv.append(odds[k] * pc[k] - 1)
    return {"bets": bets, "roi": pnl / bets if bets else 0.0,
            "clv": sum(clv) / len(clv) if clv else 0.0}


def choose_entry(rows: list[tuple], calib: float) -> tuple[dict | None, dict | None]:
    best_cfg = best_m = None
    best_score = -999.0
    for edge, cap, side in itertools.product(EDGE, ODDS_CAP, SIDES):
        m = strategy(rows, calib, edge, cap, side)
        if m["bets"] < 60 or m["clv"] <= 0:
            continue
        sc = m["clv"] + 0.10 * m["roi"]
        if sc > best_score:
            best_score = sc
            best_cfg = {"min_edge": edge, "max_odds": cap, "side": side}
            best_m = m
    return best_cfg, best_m


def run(today: date | None = None, out: Path = OUT, leagues: list[str] | None = None) -> list[str]:
    today = today or date.today()
    cur = today.year if today.month >= 7 else today.year - 1
    years = [cur - 4, cur - 3, cur - 2, cur - 1]
    tune, hold = {cur - 3, cur - 2}, {cur - 1}
    result: dict = {"_stand": today.isoformat(), "_method": "M9 dual Poisson, no market blend"}
    log = [f"M9: Tuning {sorted(tune)}, Holdout {sorted(hold)}; kein Markt-Blend"]
    selected = LEAGUES if not leagues else {k: LEAGUES[k] for k in leagues if k in LEAGUES}

    for league, code in selected.items():
        ms, rows = _load(code, years)
        best = None
        for vi, params in enumerate(VARIANTS):
            s = samples(ms, rows, tune | hold, params)
            tr = [x for x in s if x[0] in tune]
            ho = [x for x in s if x[0] in hold]
            if len(tr) < 250 or len(ho) < 100:
                continue
            for a in CALIB:
                mt = model_score(tr, a)
                if best is None or mt["logloss"] < best["train_score"]["logloss"]:
                    best = {"variant": vi, "params": asdict(params), "calib": a,
                            "train_score": mt, "train": tr, "hold": ho}
        if best is None:
            result[league] = {"validated": False, "reason": "zu wenig Daten"}
            log.append(f"{league}: zu wenig Daten")
            continue

        cfg, tune_entry = choose_entry(best["train"], best["calib"])
        hs = model_score(best["hold"], best["calib"])
        he = strategy(best["hold"], best["calib"], **cfg) if cfg else {"bets": 0, "clv": 0.0, "roi": 0.0}
        validated = bool(cfg and hs["gain"] > 0 and he["bets"] >= 30 and he["clv"] > 0 and he["roi"] > 0)
        result[league] = {
            "validated": validated, "variant": best["variant"], "params": best["params"],
            "calib": best["calib"], "train_score": best["train_score"], "entry": cfg,
            "tune_entry": tune_entry, "holdout_score": hs, "holdout_entry": he,
        }
        log.append(
            f"{league}: M9 v{best['variant']} a={best['calib']:.2f} | "
            f"Holdout LogLoss-Gewinn {hs['gain']:+.4f} | "
            f"{he['bets']} Bets, CLV {he['clv']*100:+.2f} %, ROI {he['roi']*100:+.2f} % -> "
            + ("VALIDIERT" if validated else "nicht validiert")
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log
