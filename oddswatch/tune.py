"""Fußball-Modell ehrlich verbessern: Tuning auf einer Saison, Test auf der nächsten.

Walk-forward wie im Backtest (wöchentlicher Refit, nur vorher bekannte Spiele).
Getestet werden Modellparameter (Halbwertszeit, Schrumpfung, xG-Anteil) und eine
Kalibrierung p_i ∝ p_i^a (a < 1 zieht Extreme zur Mitte, a > 1 schärft sie).
Alles wird NUR auf der Trainingssaison ausgewählt und danach unverändert auf der
Testsaison gemessen – LogLoss gegen Pinnacle-Eröffnung und CLV der Tipps gegen
Pinnacle-Closing. Ergebnis: data/tuning.json.
"""

from __future__ import annotations

import itertools
import json
import math
from datetime import date
from pathlib import Path

from . import backtest as bt
from . import pricing
from .models.poisson import PoissonModel

GRID = {"half_life_days": (90, 180, 365), "shrink": (3.0, 8.0), "xg_weight": (0.0, 0.5, 1.0)}
CALIB = (0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2)
BLEND = (0.0, 0.1, 0.2, 0.3, 0.5)
OUT = Path("data/tuning.json")


def samples_1x2(ms: list, rows: list, test_from: date, params: dict) -> list[tuple]:
    """(Datum, Modell-p, Markt-p Eröffnung, Ergebnis, Eröffnungsquoten, Closing-p)."""
    out, model, last = [], None, None
    for d, r in rows:
        if d < test_from:
            continue
        if last is None or (d - last).days >= 7:
            hist = [m for m in ms if m.date < d]
            if len(hist) < 200:
                continue
            model = PoissonModel.fit(hist, d, rho=-0.05, **params)
            last = d
        h, a = r["HomeTeam"], r["AwayTeam"]
        if model is None or h not in model.attack or a not in model.attack:
            continue
        o = [bt._f(r, k) for k in ("PSH", "PSD", "PSA")]
        c = [bt._f(r, k) for k in ("PSCH", "PSCD", "PSCA")]
        if not (all(o) and all(c)):
            continue
        hg, ag = int(float(r["FTHG"])), int(float(r["FTAG"]))
        mk = model.markets(h, a)
        out.append((d, [mk["1"], mk["X"], mk["2"]], pricing.devig(o),
                    [hg > ag, hg == ag, hg < ag], o, pricing.devig(c)))
    return out


def calibrate(p: list[float], a: float) -> list[float]:
    q = [max(x, 1e-9) ** a for x in p]
    s = sum(q)
    return [x / s for x in q]


def score(samples: list, a: float, w: float) -> dict:
    """LogLoss von Blend(kalibriertes Modell, Markt) + Tipps nach Regel (EV ≥ 3 %)."""
    if not samples:
        return {"n": 0}
    ll = ll_mkt = 0.0
    bets = pnl = 0
    clv = []
    for _, pm, po, y, odds, pc in samples:
        pmc = calibrate(pm, a)
        pb = [w * x + (1 - w) * m for x, m in zip(pmc, po)]
        i = y.index(True)
        ll -= math.log(max(pb[i], 1e-12))
        ll_mkt -= math.log(max(po[i], 1e-12))
        for k in range(3):
            if odds[k] >= 1.03 / pb[k]:
                bets += 1
                pnl += (odds[k] - 1) if y[k] else -1
                clv.append(odds[k] * pc[k] - 1)
    n = len(samples)
    return {"n": n, "logloss": ll / n, "logloss_market": ll_mkt / n,
            "gain_vs_market": ll_mkt / n - ll / n, "bets": bets,
            "roi": pnl / bets if bets else 0.0, "clv": sum(clv) / len(clv) if clv else 0.0}


def run(today: date | None = None, out: Path = OUT) -> list[str]:
    today = today or date.today()
    cur = today.year if today.month >= 7 else today.year - 1
    split = date(cur - 1, 7, 1)                 # Training: Saison cur-2/cur-1, Test: ab cur-1
    log, result = [], {}
    for league, code in bt.LEAGUES.items():
        ms, rows = bt._load(code, [cur - 3, cur - 2, cur - 1, cur])
        best = None
        for hl, sh, xg in itertools.product(*GRID.values()):
            params = {"half_life_days": hl, "shrink": sh, "xg_weight": xg}
            s = samples_1x2(ms, rows, date(cur - 2, 7, 1), params)
            train = [x for x in s if x[0] < split]
            test = [x for x in s if x[0] >= split]
            for a in CALIB:
                for w in BLEND:
                    tr = score(train, a, w)
                    if tr["n"] and (best is None or tr["logloss"] < best["train"]["logloss"]):
                        best = {"params": params, "calib": a, "w": w, "train": tr,
                                "test": score(test, a, w), "test_w0": score(test, a, 0.0)}
        result[league] = best
        t, tr = best["test"], best["train"]
        log.append(
            f"{league}: bestes Setup auf Training {best['params']}, Kalibrierung a={best['calib']}, "
            f"Modellgewicht w={best['w']} | Training: LogLoss-Gewinn vs. Markt {tr['gain_vs_market']:+.4f} | "
            f"TEST ({t['n']} Spiele): Gewinn {t['gain_vs_market']:+.4f}, {t['bets']} Tipps, "
            f"CLV {t['clv'] * 100:+.1f} %, ROI {t['roi'] * 100:+.1f} %")
    result["_stand"] = today.isoformat()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    log.append(f"gespeichert: {out}")
    return log
