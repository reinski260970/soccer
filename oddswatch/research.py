"""Modellforschung: Varianten gegen den Markt, mit Holdout.

Ziel: ein Modell, das besser ist als der Markt. Gemessen wird, ob die
Abweichung Modell − Eröffnungsmarkt die spätere Marktbewegung (Eröffnung →
Closing, Pinnacle) vorhersagt – genau das ist CLV. Kennzahlen je Variante:

  slope  Regression von logit(p_close) − logit(p_open) auf
         logit(p_model) − logit(p_open) (Heim- und Auswärtssieg);
         > 0 mit t > 2 heißt: das Modell weiß etwas, das der Markt erst später
         einpreist.
  dLL    LogLoss(Blend mit w) − LogLoss(Eröffnung); < 0 = besser als Markt.
  CLV    mittlerer CLV der Tipps nach unserer Regel (Eröffnungsquote ≥ 1,03/p).

Tuning-Saisons wählen w; die jüngste Saison ist Holdout und wird nur
berichtet. Ligen: alle football-data-Hauptligen mit Pinnacle-Quoten.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import date

from . import fetch, pricing
from .models.poisson import PoissonModel
from .sources import football_data as fd

LEAGUES = ["E0", "E1", "SP1", "I1", "F1", "D1", "D2", "N1", "P1", "B1", "T1", "SC0", "G1"]
WEIGHTS = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5)


@dataclass
class Variant:
    name: str
    shots_as_xg: bool = False
    xg_weight: float = 0.0
    half_life: float = 180.0
    shrink: float = 3.0
    rho: float = -0.05


VARIANTS = [
    Variant("Tore, HWZ 180"),
    Variant("Tore, HWZ 365", half_life=365),
    Variant("Schuss-xG 50 %", shots_as_xg=True, xg_weight=0.5),
    Variant("Schuss-xG 100 %", shots_as_xg=True, xg_weight=1.0),
    Variant("Schuss-xG 50 %, HWZ 90", shots_as_xg=True, xg_weight=0.5, half_life=90),
]


def _f(r: dict, k: str) -> float | None:
    try:
        v = float(r[k])
        return v if v > 1.0 else None
    except (KeyError, TypeError, ValueError):
        return None


def load(code: str, start_years: list[int]):
    texts = []
    for y in start_years:
        t, _ = fetch.get(fd.csv_url(code, y), cache_days=30 if y < start_years[-1] else 1)
        if t:
            texts.append((y, t))
    return texts


def samples(texts, v: Variant, test_years: set[int]) -> list[tuple]:
    """(Saison, Modell-p[3], Eröffnung-p[3], Closing-p[3], Ergebnis[3], Eröffnungsquoten[3])."""
    ms, rows = [], []
    for y, t in texts:
        ms += fd.parse(t, shots_as_xg=v.shots_as_xg)[0]
        for r in csv.DictReader(io.StringIO(t.lstrip("﻿"))):
            if r.get("HomeTeam") and r.get("FTHG") not in (None, ""):
                rows.append((fd._d(r["Date"]), y, r))
    ms.sort(key=lambda m: m.date)
    rows.sort(key=lambda x: x[0])
    out, model, last = [], None, None
    for d, y, r in rows:
        if y not in test_years:
            continue
        if last is None or d != last:
            hist = [m for m in ms if m.date < d]
            if len(hist) < 150:
                continue
            model = PoissonModel.fit(hist, d, half_life_days=v.half_life, xg_weight=v.xg_weight,
                                     shrink=v.shrink, rho=v.rho)
            last = d
        h, a = r["HomeTeam"], r["AwayTeam"]
        if h not in model.attack or a not in model.attack:
            continue
        o = [_f(r, k) for k in ("PSH", "PSD", "PSA")]
        c = [_f(r, k) for k in ("PSCH", "PSCD", "PSCA")]
        if not (all(o) and all(c)):
            continue
        mk = model.markets(h, a)
        hg, ag = int(float(r["FTHG"])), int(float(r["FTAG"]))
        out.append((y, [mk["1"], mk["X"], mk["2"]], pricing.devig(o), pricing.devig(c),
                    [hg > ag, hg == ag, hg < ag], o))
    return out


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def metrics(rows: list[tuple], w: float) -> dict:
    xs, ys = [], []
    for _, pm, po, pc, _, _ in rows:
        for i in (0, 2):
            xs.append(_logit(pm[i]) - _logit(po[i]))
            ys.append(_logit(pc[i]) - _logit(po[i]))
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    res = [y - my - slope * (x - mx) for x, y in zip(xs, ys)]
    se = math.sqrt(sum(e * e for e in res) / (n - 2) / sxx)
    ll_o = ll_b = 0.0
    clv, bets = [], 0
    for _, pm, po, pc, y, odds in rows:
        i = y.index(True)
        ll_o -= math.log(po[i])
        ll_b -= math.log(w * pm[i] + (1 - w) * po[i])
        for k in range(3):
            p = w * pm[k] + (1 - w) * po[k]
            if w > 0 and odds[k] >= 1.03 / p:
                bets += 1
                clv.append(odds[k] * pc[k] - 1)
    return {"n": len(rows), "slope": slope, "t": slope / se if se else 0.0,
            "dLL": (ll_b - ll_o) / len(rows), "bets": bets,
            "clv": sum(clv) / len(clv) if clv else 0.0}


def best_w(rows: list[tuple]) -> float:
    return min(WEIGHTS, key=lambda w: metrics(rows, w)["dLL"])


def run(today: date | None = None, variants: list[Variant] | None = None,
        leagues: list[str] | None = None) -> list[str]:
    today = today or date.today()
    cur = today.year if today.month >= 7 else today.year - 1
    years = [cur - 4, cur - 3, cur - 2, cur - 1]     # letzte abgeschlossene Saison = Holdout
    tune, hold = {cur - 3, cur - 2}, {cur - 1}
    data = {lg: load(lg, years) for lg in (leagues or LEAGUES)}
    log = [f"Tuning {min(tune)}/{min(tune) + 1}–{max(tune)}/{max(tune) + 1}, "
           f"Holdout {cur - 1}/{cur}; Ligen: {', '.join(data)}"]
    for v in variants or VARIANTS:
        rows = [s for lg, texts in data.items() for s in samples(texts, v, tune | hold)]
        tr = [s for s in rows if s[0] in tune]
        ho = [s for s in rows if s[0] in hold]
        w = best_w(tr)
        mt, mh = metrics(tr, w), metrics(ho, w)
        log.append(f"{v.name}: w={w} | Tuning n={mt['n']} slope {mt['slope']:+.3f} (t {mt['t']:+.1f}) "
                   f"dLL {mt['dLL'] * 1000:+.2f}‰ | Holdout n={mh['n']} slope {mh['slope']:+.3f} "
                   f"(t {mh['t']:+.1f}) dLL {mh['dLL'] * 1000:+.2f}‰ Tipps {mh['bets']} "
                   f"CLV {mh['clv'] * 100:+.2f} %")
    return log
