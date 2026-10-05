"""M10 Specialist-Gate auf M9.

M9 bleibt die unabhängige Fair-Probability-Engine. M10 verändert keine Fair Odds
und nutzt den Markt ausschließlich im Decision Gate: Es lernt auf zwei Tuning-
Saisons robuste Residual-Regime (Modell vs. Opening-Markt) und prüft diese
unangetastet auf der jüngsten Holdout-Saison.

Eine Regel muss in BEIDEN Tuning-Saisons positiven CLV zeigen.
"""

from __future__ import annotations

import itertools
import json
import math
from datetime import date
from pathlib import Path

from . import m9_research as m9

OUT = Path("data/m10_validation.json")

MIN_EDGE = (0.03, 0.05, 0.075, 0.10, 0.125)
MIN_PP = (0.01, 0.03, 0.05, 0.08)
MAX_PP = (0.08, 0.12, 0.18, 0.25)
MARKET_BANDS = (
    (0.00, 1.00),
    (0.10, 0.30),
    (0.20, 0.40),
    (0.30, 0.50),
    (0.40, 0.65),
    (0.55, 0.85),
)
SIDES = ("all", "home", "draw", "away")


def gate_metrics(rows: list[tuple], calib: float, *, min_edge: float, min_pp: float,
                 max_pp: float, market_lo: float, market_hi: float, side: str) -> dict:
    idx = {"home": 0, "draw": 1, "away": 2}.get(side)
    bets = 0
    pnl = 0.0
    clv = []
    for _, pm, po, pc, y, odds in rows:
        p = m9._calibrate(pm, calib)
        for k in range(3):
            if idx is not None and k != idx:
                continue
            pp = p[k] - po[k]
            ev = p[k] * odds[k] - 1.0
            if not (min_pp <= pp <= max_pp):
                continue
            if ev < min_edge or not (market_lo <= po[k] < market_hi):
                continue
            bets += 1
            pnl += odds[k] - 1.0 if y[k] else -1.0
            clv.append(odds[k] * pc[k] - 1.0)
    return {
        "bets": bets,
        "roi": pnl / bets if bets else 0.0,
        "clv": sum(clv) / len(clv) if clv else 0.0,
    }


def choose_gate(rows: list[tuple], calib: float, tune_years: set[int]) -> tuple[dict | None, dict | None]:
    best_cfg = best = None
    best_score = -999.0
    for edge, lo_pp, hi_pp, band, side in itertools.product(
        MIN_EDGE, MIN_PP, MAX_PP, MARKET_BANDS, SIDES
    ):
        if hi_pp <= lo_pp:
            continue
        cfg = {
            "min_edge": edge, "min_pp": lo_pp, "max_pp": hi_pp,
            "market_lo": band[0], "market_hi": band[1], "side": side,
        }
        per_year = {
            y: gate_metrics([r for r in rows if r[0] == y], calib, **cfg)
            for y in sorted(tune_years)
        }
        total = gate_metrics(rows, calib, **cfg)
        # Robustheit vor Rendite: beide Tuning-Saisons müssen eigenständig CLV+ sein.
        if total["bets"] < 60:
            continue
        if any(v["bets"] < 20 or v["clv"] <= 0 for v in per_year.values()):
            continue
        if total["roi"] <= 0:
            continue
        worst_clv = min(v["clv"] for v in per_year.values())
        # Stichprobe belohnen, aber nicht durch ROI-Extrema dominieren lassen.
        score = worst_clv * math.sqrt(total["bets"]) + 0.05 * total["roi"]
        if score > best_score:
            best_score = score
            best_cfg = cfg
            best = {"total": total, "per_year": per_year}
    return best_cfg, best


def run(today: date | None = None, out: Path = OUT, leagues: list[str] | None = None) -> list[str]:
    today = today or date.today()
    cur = today.year if today.month >= 7 else today.year - 1
    years = [cur - 4, cur - 3, cur - 2, cur - 1]
    tune, hold = {cur - 3, cur - 2}, {cur - 1}
    selected = m9.LEAGUES if not leagues else {k: m9.LEAGUES[k] for k in leagues if k in m9.LEAGUES}
    result: dict = {"_stand": today.isoformat(), "_method": "M10 specialist gate on independent M9 fair"}
    log = [f"M10: Tuning {sorted(tune)}, Holdout {sorted(hold)}; Fair=M9, Markt nur Gate"]

    for league, code in selected.items():
        ms, rows = m9._load(code, years)
        best = None
        for vi, params in enumerate(m9.VARIANTS):
            s = m9.samples(ms, rows, tune | hold, params)
            tr = [x for x in s if x[0] in tune]
            ho = [x for x in s if x[0] in hold]
            if len(tr) < 250 or len(ho) < 100:
                continue
            for a in m9.CALIB:
                sc = m9.model_score(tr, a)
                if best is None or sc["logloss"] < best["train_score"]["logloss"]:
                    best = {
                        "variant": vi, "params": params, "calib": a,
                        "train_score": sc, "train": tr, "hold": ho,
                    }
        if best is None:
            result[league] = {"validated": False, "reason": "zu wenig Daten"}
            log.append(f"{league}: zu wenig Daten")
            continue

        cfg, tune_stats = choose_gate(best["train"], best["calib"], tune)
        hold_stats = gate_metrics(best["hold"], best["calib"], **cfg) if cfg else {
            "bets": 0, "clv": 0.0, "roi": 0.0
        }
        validated = bool(
            cfg and hold_stats["bets"] >= 30
            and hold_stats["clv"] > 0 and hold_stats["roi"] > 0
        )
        result[league] = {
            "validated": validated,
            "m9_variant": best["variant"],
            "calib": best["calib"],
            "gate": cfg,
            "tune": tune_stats,
            "holdout": hold_stats,
        }
        if cfg:
            log.append(
                f"{league}: Gate {cfg} | Tune {tune_stats['total']['bets']} Bets "
                f"CLV {tune_stats['total']['clv']*100:+.2f}% ROI {tune_stats['total']['roi']*100:+.2f}% | "
                f"Holdout {hold_stats['bets']} Bets CLV {hold_stats['clv']*100:+.2f}% "
                f"ROI {hold_stats['roi']*100:+.2f}% -> "
                + ("VALIDIERT" if validated else "nicht validiert")
            )
        else:
            log.append(f"{league}: keine in beiden Tuning-Saisons robuste CLV-positive Gate-Regel")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log
