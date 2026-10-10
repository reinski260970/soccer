"""Period-specific fair models for NBA, NFL and NHL.

These models are trained from real historical quarter/period scores. They do
NOT scale full-game expectations by 1/2, 1/3 or 1/4.

Supported:
- NBA 1Q total, 1H total
- NFL 1Q total, 1H total
- NHL 1P total

Market prices are never features.
"""

from __future__ import annotations

import math
from datetime import date

from . import matching
from .models.ratings import Game, PointsModel
from .models.poisson import Match, PoissonModel
from .sources import espn


def _period_key(period: str) -> str | None:
    p = (period or "").casefold().strip()
    if p in {"q1", "quarter1", "1q", "1stquarter", "firstquarter"}:
        return "1q"
    if p in {"1h", "half1", "1sthalf", "firsthalf"}:
        return "1h"
    if p in {"p1", "period1", "1p", "1stperiod", "firstperiod"}:
        return "1p"
    return None


def _season_end_year(league: str, d: date) -> int:
    if league in {"nba", "nhl"}:
        return d.year + 1 if d.month >= 7 else d.year
    return d.year


def _period_points(g, key: str):
    hp = tuple(g.home_periods or ())
    ap = tuple(g.away_periods or ())
    if key == "1q":
        if len(hp) < 1 or len(ap) < 1:
            return None
        return hp[0], ap[0]
    if key == "1h":
        if len(hp) < 2 or len(ap) < 2:
            return None
        return hp[0] + hp[1], ap[0] + ap[1]
    if key == "1p":
        if len(hp) < 1 or len(ap) < 1:
            return None
        return hp[0], ap[0]
    return None


def _schedule_period_games(league: str, season: int, key: str, cache_days: float) -> list[Game]:
    ids, _ = espn.team_ids(league)
    seen = set()
    out = []
    for tid in ids:
        rows, _ = espn.team_schedule(league, tid, season, 2, cache_days=cache_days)
        for g in rows:
            if not g.final or g.id in seen:
                continue
            pts = _period_points(g, key)
            if pts is None:
                continue
            seen.add(g.id)
            out.append(Game(g.kickoff.date(), g.home.name, g.away.name, pts[0], pts[1], g.neutral))
    return out


def _nfl_period_games(season: int, key: str, cache_days: float) -> list[Game]:
    seen = set()
    out = []
    for st in (2, 3):
        weeks = range(1, 19) if st == 2 else range(1, 6)
        for wk in weeks:
            rows, _ = espn.nfl_week(season, wk, st, cache_days=cache_days)
            for g in rows:
                if not g.final or g.id in seen:
                    continue
                pts = _period_points(g, key)
                if pts is None:
                    continue
                seen.add(g.id)
                out.append(Game(g.kickoff.date(), g.home.name, g.away.name, pts[0], pts[1], g.neutral))
    return out


def _points_history(league: str, as_of: date, key: str):
    sy = _season_end_year(league, as_of)
    if league == "nfl":
        prev = _nfl_period_games(sy - 1, key, 30.0)
        cur = _nfl_period_games(sy, key, 0.15)
    else:
        prev = _schedule_period_games(league, sy - 1, key, 30.0)
        cur = _schedule_period_games(league, sy, key, 0.15)
    return prev + [g for g in cur if g.date < as_of]


def _normal_over(mean: float, sigma: float, line: float) -> float:
    sigma = max(float(sigma), 0.25)
    z = (float(line) - float(mean)) / sigma
    return 1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def points_period_total(
    league: str,
    home: str,
    away: str,
    kickoff: date,
    period: str,
    line: float,
    over: bool,
    cache: dict,
) -> tuple[float | None, str]:
    key = _period_key(period)
    if league not in {"nba", "nfl"} or key not in {"1q", "1h"}:
        return None, "kein unterstütztes Punkte-Periodenmodell"

    ck = (league, kickoff.year, key)
    if ck not in cache:
        rows = _points_history(league, kickoff, key)
        minimum = 300 if league == "nba" else 150
        if len(rows) < minimum:
            cache[ck] = (None, rows)
        else:
            cache[ck] = (
                PointsModel.fit(
                    rows,
                    kickoff,
                    half_life_days=100 if league == "nba" else 180,
                    ridge=8.0 if league == "nba" else 4.0,
                ),
                rows,
            )
    model, rows = cache[ck]
    if model is None:
        return None, f"zu wenig {key.upper()}-Daten ({len(rows)})"

    names = list(model.off)
    h = matching.find(home, names)
    a = matching.find(away, names)
    if not h or not a:
        return None, f"Teams nicht im {key.upper()}-Modell"

    ph, pa = model.expected_points(h, a)
    mean = ph + pa
    p_over = _normal_over(mean, model.sigma_total, line)
    p = p_over if over else 1.0 - p_over
    return p, (
        f"{league.upper()} {key.upper()} PointsModel "
        f"({len(rows)} Spiele, fair total {mean:.1f}, sigma {model.sigma_total:.1f})"
    )


def nhl_period1_total(
    home: str,
    away: str,
    kickoff: date,
    line: float,
    over: bool,
    cache: dict,
) -> tuple[float | None, str]:
    ck = ("nhl", kickoff.year, "1p")
    if ck not in cache:
        sy = _season_end_year("nhl", kickoff)
        rows_g = _schedule_period_games("nhl", sy - 1, "1p", 30.0)
        rows_g += [g for g in _schedule_period_games("nhl", sy, "1p", 0.15) if g.date < kickoff]
        rows = [Match(g.date, g.home, g.away, g.home_pts, g.away_pts) for g in rows_g]
        if len(rows) < 300:
            cache[ck] = (None, rows)
        else:
            cache[ck] = (
                PoissonModel.fit(
                    rows,
                    kickoff,
                    half_life_days=240,
                    xg_weight=0.0,
                    shrink=10.0,
                    rho=0.0,
                    max_goals=7,
                ),
                rows,
            )
    model, rows = cache[ck]
    if model is None:
        return None, f"zu wenig NHL-1P-Daten ({len(rows)})"

    names = list(model.attack)
    h = matching.find(home, names)
    a = matching.find(away, names)
    if not h or not a:
        return None, "Teams nicht im NHL-1P-Modell"
    mk = model.markets(h, a)
    key = ("O" if over else "U") + str(float(line))
    p = mk.get(key)
    if p is None:
        return None, "NHL-1P-Linie nicht unterstützt"
    return float(p), f"NHL 1P Poisson ({len(rows)} Spiele)"
