"""M13: Mongo-Langzeithistorie + echtes Understat-xG, strikt OOS.

- Ergebnisse/Teams/Pinnacle Opening+Closing aus MONGO_SOCCER/euro_football.mains
- echtes Match-xG aus Understat (Top-5-Ligen)
- Marktquoten sind niemals Modellfeatures
- Future rows werden hart ausgeschlossen
- Loader dedupliziert Fixture-Key defensiv
- Tune: 2023/24 + 2024/25, unangetasteter Holdout: 2025/26
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from datetime import date
from pathlib import Path

from . import pricing
from .m12_research import load_mongo
from .models.m11 import M11Model, M11Params
from .sources import understat, xg_merge

LEAGUES = {
    "bundesliga": "D1",
    "epl": "E0",
    "laliga": "SP1",
    "seriea": "I1",
    "ligue1": "F1",
}
CALIB = (0.80, 0.90, 1.00, 1.10)
EDGE = (0.03, 0.05, 0.075, 0.10, 0.125, 0.15)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0, 6.0)
SIDES = ("all", "home", "draw", "away")
OUT = Path("data/m13_validation.json")

VARIANTS = [
    M11Params(half_life_days=120, xg_blend=0.55, elo_scale=0.08, xg_form_scale=0.05),
    M11Params(half_life_days=180, xg_blend=0.65, elo_scale=0.10, xg_form_scale=0.06),
    M11Params(half_life_days=180, xg_blend=0.75, elo_scale=0.12, xg_form_scale=0.08),
    M11Params(half_life_days=270, xg_blend=0.75, elo_scale=0.10, xg_form_scale=0.06),
    M11Params(half_life_days=365, xg_blend=0.65, elo_scale=0.10, xg_form_scale=0.05),
]


def _calibrate(p: list[float], a: float) -> list[float]:
    q = [max(x, 1e-9) ** a for x in p]
    z = sum(q)
    return [x / z for x in q]


def _dedupe_matches(matches):
    seen = set()
    out = []
    for m in sorted(matches, key=lambda x: x.date):
        key = (m.date, m.home, m.away)
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


def load_real_xg(code: str, start_year: int = 2017, end_year: int = 2025):
    """Mongo-Ergebnisse + echtes Understat-xG. Keine Future-Spiele jenseits 2025/26."""
    base, rows = load_mongo(code, start_year, end_year)
    base = _dedupe_matches(base)
    by_season = {}
    for m in base:
        y = m.date.year if m.date.month >= 7 else m.date.year - 1
        by_season.setdefault(y, []).append(m)

    merged_all = []
    coverage = {}
    for y in range(start_year, end_year + 1):
        fm = by_season.get(y, [])
        if not fm:
            coverage[str(y)] = {"total": 0, "matched": 0, "coverage": 0.0}
            continue
        um, err = understat.season_matches(code, y, cache_days=30 if y < end_year else 1)
        merged, st = xg_merge.merge_xg(fm, um)
        st["understat_error"] = err
        coverage[str(y)] = st
        merged_all.extend(merged)

    # load_mongo endet hart am 01.07.2026 für end_year=2025; keine Future-Leakage.
    return _dedupe_matches(merged_all), rows, coverage


def samples(matches, rows, seasons: set[int], params: M11Params):
    out = []
    model = None
    last_fit = None
    for season, d, h, a, hg, ag, op, cl in rows:
        if season not in seasons:
            continue
        if last_fit is None or (d - last_fit).days >= 14:
            hist = [m for m in matches if m.date < d]
            try:
                model = M11Model.fit(hist, d, params)
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
        out.append((
            season,
            [mk["1"], mk["X"], mk["2"]],
            pricing.devig(op),
            pricing.devig(cl),
            [hg > ag, hg == ag, hg < ag],
            op,
        ))
    return out


def model_score(rows, calib: float) -> dict:
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


def strategy(rows, calib: float, min_edge: float, max_odds: float, side: str) -> dict:
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
        "roi": pnl/bets if bets else 0.0,
        "clv": sum(clv)/len(clv) if clv else 0.0,
    }


def choose_entry(rows, calib: float, tune_years: set[int]):
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


def run(today: date | None = None, out: Path = OUT, leagues: list[str] | None = None):
    today = today or date.today()
    tune = {2023, 2024}
    hold = {2025}
    selected = LEAGUES if not leagues else {k: LEAGUES[k] for k in leagues if k in LEAGUES}
    result = {
        "_stand": today.isoformat(),
        "_method": "M13 Mongo long-history + real Understat xG; no market features",
        "_tune": sorted(tune),
        "_holdout": sorted(hold),
    }
    log = ["M13: Mongo 2017-2025 + echtes Understat-xG | Tune 2023/24+2024/25 | Holdout 2025/26"]

    for league, code in selected.items():
        ms, rows, coverage = load_real_xg(code)
        relevant_cov = [
            v.get("coverage", 0.0) for y, v in coverage.items()
            if int(y) >= 2023 and isinstance(v, dict)
        ]
        min_cov = min(relevant_cov, default=0.0)
        if min_cov < 0.95:
            result[league] = {
                "validated": False, "reason": "xG coverage <95%",
                "coverage": coverage,
            }
            log.append(f"{league}: xG-Abdeckung {min_cov*100:.1f}% -> nicht getestet")
            for yy in ("2023", "2024", "2025"):
                st = coverage.get(yy, {})
                misses = st.get("misses", []) if isinstance(st, dict) else []
                if misses:
                    log.append(f"{league} {yy} misses: " + " | ".join(misses[:25]))
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
                    best = {
                        "variant": vi, "params": asdict(params), "calib": a,
                        "train_score": sc, "train": tr, "hold": ho,
                    }

        if best is None:
            result[league] = {"validated": False, "reason": "zu wenig OOS-Daten", "coverage": coverage}
            log.append(f"{league}: zu wenig OOS-Daten")
            continue

        cfg, tune_stats = choose_entry(best["train"], best["calib"], tune)
        hs = model_score(best["hold"], best["calib"])
        he = strategy(best["hold"], best["calib"], **cfg) if cfg else {
            "bets": 0, "clv": 0.0, "roi": 0.0
        }
        validated = bool(
            cfg and hs["gain"] > 0
            and he["bets"] >= 40
            and he["clv"] > 0
            and he["roi"] > 0
        )
        result[league] = {
            "validated": validated,
            "variant": best["variant"],
            "params": best["params"],
            "calib": best["calib"],
            "coverage": coverage,
            "train_score": best["train_score"],
            "gate": cfg,
            "tune": tune_stats,
            "holdout_score": hs,
            "holdout": he,
        }
        log.append(
            f"{league}: M13 v{best['variant']} a={best['calib']:.2f} | "
            f"Holdout dLL {hs['gain']:+.4f} | "
            f"{he['bets']} Bets CLV {he['clv']*100:+.2f}% ROI {he['roi']*100:+.2f}% -> "
            + ("VALIDIERT" if validated else "nicht validiert")
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log
