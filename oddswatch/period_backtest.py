"""Walk-forward backtest for NBA/NFL/NHL period-total models.

This validates predictive quality only. Historical closing prices for q1/1h/p1
are not available in our current store, so CLV/release remains a separate gate.

Metrics:
- discrete negative log-likelihood of the realized period total
- Brier score on over/under around the rolling training median line
- MAE of expected total
- same metrics for a naive league-only baseline

No bookmaker price enters the model or the backtest.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from statistics import median

from .models.poisson import Match, PoissonModel
from .models.ratings import Game, PointsModel
from . import matching, period_totals

OUT = Path("data/period_backtest.json")

TARGETS = (
    ("nba", "q1"),
    ("nba", "1h"),
    ("nfl", "q1"),
    ("nfl", "1h"),
    ("nhl", "p1"),
)

MIN_TRAIN = {
    "nba": 250,
    "nfl": 100,
    "nhl": 250,
}

REFIT_EVERY = {
    "nba": 20,
    "nfl": 8,
    "nhl": 20,
}


@dataclass
class Result:
    sport: str
    period: str
    n: int
    train_min: int
    test_start: str | None
    test_end: str | None
    model_nll: float | None
    baseline_nll: float | None
    nll_gain: float | None
    model_brier: float | None
    baseline_brier: float | None
    brier_gain: float | None
    model_mae: float | None
    baseline_mae: float | None
    mae_gain: float | None
    model_better_nll: bool
    model_better_brier: bool
    model_better_mae: bool
    release_eligible: bool
    note: str


def _normal_pmf(total: int, mu: float, sigma: float):
    rows = dict(period_totals._normal_integer_pmf(mu, sigma, max(total + 50, int(mu + 8*sigma + 10))))
    return max(float(rows.get(int(total), 0.0)), 1e-12)


def _poisson_pmf(total: int, lam: float):
    if lam <= 0:
        return 1e-12
    return max(math.exp(-lam + total*math.log(lam) - math.lgamma(total + 1)), 1e-12)


def _normal_over(line: float, mu: float, sigma: float) -> float:
    pmf = period_totals._normal_integer_pmf(mu, sigma, max(200, int(mu + 8*sigma + 20)))
    fp = period_totals._fair_from_pmf(pmf, line, True)
    return float(fp[1]) if fp else 0.5


def _poisson_over(line: float, lam: float) -> float:
    pmf = period_totals._poisson_total_pmf(lam, max_total=max(20, int(lam + 10)))
    fp = period_totals._fair_from_pmf(pmf, line, True)
    return float(fp[1]) if fp else 0.5


def _baseline_stats(train: list[Game]):
    totals = [g.home_pts + g.away_pts for g in train]
    mu = sum(totals) / len(totals)
    var = sum((x - mu) ** 2 for x in totals) / max(len(totals) - 1, 1)
    sigma = max(math.sqrt(var), 1e-6)
    line = float(median(totals)) + 0.5
    return mu, sigma, line


def _fit_points(sport: str, train: list[Game], as_of: date):
    if sport == "nba":
        return PointsModel.fit(train, as_of, half_life_days=90, ridge=8.0)
    return PointsModel.fit(train, as_of, half_life_days=120, ridge=4.0)


def _fit_nhl(train: list[Game], as_of: date):
    ms = [Match(g.date, g.home, g.away, g.home_pts, g.away_pts) for g in train]
    return PoissonModel.fit(ms, as_of, half_life_days=240, xg_weight=0.0,
                            shrink=8.0, rho=0.0, max_goals=7)


def _predict(model, sport: str, g: Game):
    if sport in {"nba", "nfl"}:
        names = list(model.off)
        h = matching.find(g.home, names)
        a = matching.find(g.away, names)
        if not h or not a:
            return None
        ph, pa = model.expected_points(h, a, neutral=g.neutral)
        return ph + pa, float(model.sigma_total)
    names = list(model.attack)
    h = matching.find(g.home, names)
    a = matching.find(g.away, names)
    if not h or not a:
        return None
    lh, la = model.expected_goals(h, a, neutral=g.neutral)
    return lh + la, None


def backtest_one(sport: str, period: str, as_of: date, cache: dict) -> Result:
    games, issues = period_totals.history(sport, period, as_of, cache)
    games = sorted(games, key=lambda g: g.date)
    min_train = MIN_TRAIN[sport]
    if len(games) <= min_train + 20:
        return Result(
            sport, period, 0, min_train, None, None,
            None, None, None, None, None, None, None, None, None,
            False, False, False, False,
            f"zu wenig Daten: {len(games)}; issues={len(issues)}",
        )

    model = None
    fit_at = -10**9
    rows = []
    for i in range(min_train, len(games)):
        g = games[i]
        train = games[:i]
        if model is None or i - fit_at >= REFIT_EVERY[sport]:
            try:
                model = _fit_points(sport, train, g.date) if sport in {"nba","nfl"} else _fit_nhl(train, g.date)
                fit_at = i
            except Exception:
                model = None
        if model is None:
            continue

        pred = _predict(model, sport, g)
        if pred is None:
            continue
        mu, sigma = pred
        bmu, bsigma, line = _baseline_stats(train)
        actual = int(round(g.home_pts + g.away_pts))

        if sport in {"nba", "nfl"}:
            mp = _normal_pmf(actual, mu, sigma)
            bp = _normal_pmf(actual, bmu, bsigma)
            p_over = _normal_over(line, mu, sigma)
            b_over = _normal_over(line, bmu, bsigma)
        else:
            mp = _poisson_pmf(actual, mu)
            bp = _poisson_pmf(actual, bmu)
            p_over = _poisson_over(line, mu)
            b_over = _poisson_over(line, bmu)

        y = 1.0 if actual > line else 0.0
        rows.append({
            "date": g.date,
            "actual": float(actual),
            "model_mu": float(mu),
            "base_mu": float(bmu),
            "model_nll": -math.log(mp),
            "base_nll": -math.log(bp),
            "model_brier": (p_over - y) ** 2,
            "base_brier": (b_over - y) ** 2,
            "model_mae": abs(mu - actual),
            "base_mae": abs(bmu - actual),
        })

    if not rows:
        return Result(
            sport, period, 0, min_train, None, None,
            None, None, None, None, None, None, None, None, None,
            False, False, False, False, "keine OOS-Predictions",
        )

    def avg(k): return sum(r[k] for r in rows) / len(rows)
    mn, bn = avg("model_nll"), avg("base_nll")
    mb, bb = avg("model_brier"), avg("base_brier")
    mm, bm = avg("model_mae"), avg("base_mae")
    ng, bg, mg = bn - mn, bb - mb, bm - mm

    # Predictive release gate only. Market/CLV release remains impossible until
    # we have historical period closing lines.
    predictive_ok = ng > 0 and bg > 0 and mg > 0 and len(rows) >= 75

    return Result(
        sport=sport, period=period, n=len(rows), train_min=min_train,
        test_start=rows[0]["date"].isoformat(), test_end=rows[-1]["date"].isoformat(),
        model_nll=mn, baseline_nll=bn, nll_gain=ng,
        model_brier=mb, baseline_brier=bb, brier_gain=bg,
        model_mae=mm, baseline_mae=bm, mae_gain=mg,
        model_better_nll=ng > 0, model_better_brier=bg > 0, model_better_mae=mg > 0,
        release_eligible=False,
        note=("PREDICTIVE_OK; CLV_GATE_MISSING" if predictive_ok else "NO_PREDICTIVE_RELEASE")
             + f"; issues={len(issues)}",
    )


def run(as_of: date | None = None):
    as_of = as_of or date.today()
    cache = {}
    results = [backtest_one(s, p, as_of, cache) for s, p in TARGETS]
    payload = {
        "as_of": as_of.isoformat(),
        "method": "strict_walk_forward_period_totals",
        "release_rule": "predictive metrics first; historical period closing-line CLV still required",
        "results": [asdict(r) for r in results],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    out = [f"PERIOD BACKTEST · {as_of.isoformat()}"]
    for r in results:
        if not r.n:
            out.append(f"{r.sport.upper()} {r.period}: NO DATA · {r.note}")
            continue
        out.append(
            f"{r.sport.upper()} {r.period}: n={r.n} · "
            f"NLL {r.model_nll:.4f} vs {r.baseline_nll:.4f} ({r.nll_gain:+.4f}) · "
            f"Brier {r.model_brier:.4f} vs {r.baseline_brier:.4f} ({r.brier_gain:+.4f}) · "
            f"MAE {r.model_mae:.2f} vs {r.baseline_mae:.2f} ({r.mae_gain:+.2f}) · "
            f"{r.note}"
        )
    return out


if __name__ == "__main__":
    for line in run():
        print(line)
