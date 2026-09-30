"""Walk-forward-Backtest: Ist das Modell besser als der Markt?

Für Ligen mit historischen Quoten (football-data.co.uk: Pinnacle-Eröffnung
und -Closing) wird das Modell wöchentlich nur mit vorher bekannten Spielen
neu gefittet und je Spiel mit dem Markt verglichen:

  - LogLoss von w·Modell + (1−w)·Eröffnungsmarkt für w in WEIGHTS
  - Tipps nach unserer Regel (Eröffnungsquote ≥ 1,03 / p) und deren
    CLV gegen die Pinnacle-Closing-Line sowie ROI

Validiert ist eine Liga/Marktart nur, wenn das LogLoss-beste w > 0 ist,
mindestens MIN_BETS Tipps entstehen und der mittlere CLV positiv ist.
Ergebnis: data/validation.json (liest scan.model_weight).
"""

from __future__ import annotations

import csv
import io
import json
import math
from datetime import date
from pathlib import Path

from . import fetch, pricing
from .models.poisson import PoissonModel
from .sources import football_data as fd

LEAGUES = {"bundesliga": "D1", "2bundesliga": "D2"}
WEIGHTS = (0.0, 0.1, 0.25, 0.5)
MIN_BETS = 200
OUT = Path("data/validation.json")


def _f(r: dict, k: str) -> float | None:
    try:
        v = float(r[k])
        return v if v > 1.0 else None
    except (KeyError, TypeError, ValueError):
        return None


def _load(code: str, seasons: list[int]) -> tuple[list, list[tuple[date, dict]]]:
    ms, rows = [], []
    for yr in seasons:
        t, _ = fetch.get(fd.csv_url(code, yr), cache_days=0 if yr == seasons[-1] else 30)
        if not t:
            continue
        ms += fd.parse(t)[0]
        for r in csv.DictReader(io.StringIO(t.lstrip("﻿"))):
            if r.get("HomeTeam") and r.get("FTHG") not in (None, ""):
                rows.append((fd._d(r["Date"]), r))
    ms.sort(key=lambda m: m.date)
    rows.sort(key=lambda x: x[0])
    return ms, rows


def _samples(ms: list, rows: list[tuple[date, dict]], test_from: date) -> dict[str, list]:
    """Je Marktart: (Modell-p, Eröffnung-p, Ergebnis, Eröffnungsquoten, Closing-p)."""
    out: dict[str, list] = {"1x2": [], "ou": [], "ah": []}
    model, last = None, None
    for d, r in rows:
        if d < test_from:
            continue
        if last is None or (d - last).days >= 7:
            hist = [m for m in ms if m.date < d]
            if len(hist) < 200:
                continue
            model = PoissonModel.fit(hist, d, half_life_days=180, xg_weight=0.5, shrink=3.0,
                                     rho=-0.05)
            last = d
        h, a = r["HomeTeam"], r["AwayTeam"]
        if model is None or h not in model.attack or a not in model.attack:
            continue
        hg, ag = int(float(r["FTHG"])), int(float(r["FTAG"]))
        lh, la = model.expected_goals(h, a)
        mat = model.score_matrix(lh, la)
        n = len(mat)
        o, c = [_f(r, k) for k in ("PSH", "PSD", "PSA")], [_f(r, k) for k in ("PSCH", "PSCD", "PSCA")]
        if all(o) and all(c):
            mk = model.markets(h, a)
            out["1x2"].append(([mk["1"], mk["X"], mk["2"]], pricing.devig(o),
                               [hg > ag, hg == ag, hg < ag], o, pricing.devig(c)))
        o, c = [_f(r, "P>2.5"), _f(r, "P<2.5")], [_f(r, "PC>2.5"), _f(r, "PC<2.5")]
        if all(o) and all(c):
            po = sum(mat[i][j] for i in range(n) for j in range(n) if i + j > 2.5)
            out["ou"].append(([po, 1 - po], pricing.devig(o), [hg + ag > 2.5, hg + ag < 2.5],
                              o, pricing.devig(c)))
        try:
            line, cline = float(r.get("AHh", "")), float(r.get("AHCh", ""))
        except ValueError:
            continue
        o, c = [_f(r, "PAHH"), _f(r, "PAHA")], [_f(r, "PCAHH"), _f(r, "PCAHA")]
        if line == cline and all(o) and all(c) and abs(line * 2) % 2 == 1:   # halbe Linien
            ph = sum(mat[i][j] for i in range(n) for j in range(n) if i + line > j)
            out["ah"].append(([ph, 1 - ph], pricing.devig(o), [hg + line > ag, hg + line < ag],
                              o, pricing.devig(c)))
    return out


def evaluate(samples: list) -> dict:
    """LogLoss je w, Tipps nach unserer Regel mit CLV und ROI, Validierungsurteil."""
    if not samples:
        return {"n_games": 0, "validated": False, "w": 0.0, "clv": 0.0, "n": 0, "roi": 0.0}
    ll = {}
    for w in WEIGHTS:
        tot = 0.0
        for pm, po, y, _, _ in samples:
            i = y.index(True)
            tot -= math.log(max(1e-12, w * pm[i] + (1 - w) * po[i]))
        ll[w] = tot / len(samples)
    best = min(ll, key=ll.get)
    w_eval = best if best > 0 else 0.25        # Regel-Kennzahlen auch für w=0 aussagekräftig
    n = pnl = 0
    clv = []
    for pm, po, y, odds, pc in samples:
        for i in range(len(odds)):
            p = w_eval * pm[i] + (1 - w_eval) * po[i]
            if odds[i] >= 1.03 / p:
                n += 1
                pnl += (odds[i] - 1) if y[i] else -1
                clv.append(odds[i] * pc[i] - 1)
    avg_clv = sum(clv) / len(clv) if clv else 0.0
    return {"n_games": len(samples), "logloss": {str(k): round(v, 5) for k, v in ll.items()},
            "best_w": best, "w": best if best > 0 else 0.0, "w_rule": w_eval, "n": n,
            "clv": round(avg_clv, 4), "roi": round(pnl / n, 4) if n else 0.0,
            "validated": best > 0 and n >= MIN_BETS and avg_clv > 0}


def run(today: date | None = None, out: Path = OUT, us: bool = False) -> list[str]:
    today = today or date.today()
    cur = today.year if today.month >= 7 else today.year - 1
    try:   # bestehende Einträge (z. B. NFL/NHL aus einem früheren --us-Lauf) behalten
        result = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        result = {}
    log = []
    for league, code in LEAGUES.items():
        ms, rows = _load(code, [cur - 3, cur - 2, cur - 1, cur])
        samples = _samples(ms, rows, date(cur - 2, 7, 1))
        for mtype, s in samples.items():
            ev = evaluate(s)
            result[f"{league}:{mtype}"] = ev
            log.append(f"{league} {mtype}: {ev['n_games']} Spiele, LogLoss Markt "
                       f"{ev.get('logloss', {}).get('0.0', 0):.4f} / bestes w {ev.get('best_w', 0)}, "
                       f"Regel (w={ev.get('w_rule', 0)}): {ev['n']} Tipps, CLV {ev['clv'] * 100:+.1f} %, "
                       f"ROI {ev['roi'] * 100:+.1f} % → "
                       + ("VALIDIERT" if ev["validated"] else "nicht besser als der Markt"))
    if us:
        from . import backtest_us
        for key, samples in (("nfl:1x2", backtest_us.nfl_samples(cur)),
                             ("nhl:1x2", backtest_us.nhl_samples(cur))):
            ev = evaluate(samples)
            result[key] = ev
            log.append(f"{key}: {ev['n_games']} Spiele, LogLoss Markt "
                       f"{ev.get('logloss', {}).get('0.0', 0):.4f} / bestes w {ev.get('best_w', 0)}, "
                       f"Regel: {ev['n']} Tipps, CLV {ev['clv'] * 100:+.1f} %, "
                       f"ROI {ev['roi'] * 100:+.1f} % → "
                       + ("VALIDIERT" if ev["validated"] else "nicht besser als der Markt"))
    result["_stand"] = today.isoformat()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    log.append(f"gespeichert: {out}. Ohne Eintrag (NBA, UEFA, europ. Eishockey, AT"
               + ("" if us else "; NFL/NHL nur mit --us") + ") gilt: nicht validiert.")
    return log
