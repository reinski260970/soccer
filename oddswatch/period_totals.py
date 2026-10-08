"""Independent period-total fair models for NBA, NFL and NHL.

Historical quarter/period scores come from ESPN linescores. These models are
candidate-driven and never use bookmaker odds as features.

Supported:
- NBA q1 / 1h totals
- NFL q1 / 1h totals
- NHL p1 totals
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from dataclasses import dataclass

from . import matching
from .models.ratings import Game, PointsModel
from .models.poisson import Match, PoissonModel
from .sources import espn


@dataclass
class PeriodFair:
    fair_odds: float
    probability: float
    expected_total: float
    sample_games: int
    model: str


def _period_points(g: espn.EspnGame, period: str):
    hp = tuple(g.home_periods or ())
    ap = tuple(g.away_periods or ())
    if period == "q1" and len(hp) >= 1 and len(ap) >= 1:
        return hp[0], ap[0]
    if period == "1h" and len(hp) >= 2 and len(ap) >= 2:
        return sum(hp[:2]), sum(ap[:2])
    if period == "p1" and len(hp) >= 1 and len(ap) >= 1:
        return hp[0], ap[0]
    return None


def _dedupe_games(raw, period: str) -> list[Game]:
    seen = set()
    out = []
    for g in raw:
        if not g.final or g.id in seen or g.season_type not in (2, 3):
            continue
        pts = _period_points(g, period)
        if pts is None:
            continue
        seen.add(g.id)
        out.append(Game(
            g.kickoff.date(), g.home.name, g.away.name,
            float(pts[0]), float(pts[1]), g.neutral,
        ))
    return out


def _nfl_raw(as_of: date, issues: list[str]):
    raw = []
    # Previous full regular season + playoffs.
    for wk in range(1, 19):
        gs, err = espn.nfl_week(as_of.year - 1, wk, 2, cache_days=30)
        if err:
            issues.append(err)
        raw += gs
    for wk in range(1, 6):
        gs, _ = espn.nfl_week(as_of.year - 1, wk, 3, cache_days=30)
        raw += gs
    # Current season up to the present week.
    for wk in range(1, 19):
        gs, err = espn.nfl_week(as_of.year, wk, 2, cache_days=0.10)
        if err:
            issues.append(err)
        finals = [g for g in gs if g.final and g.kickoff.date() < as_of]
        if not gs:
            continue
        raw += finals
        if gs and not finals and min(g.kickoff.date() for g in gs) >= as_of:
            break
    return raw


def _schedule_raw(league: str, as_of: date, issues: list[str]):
    """Historical NBA/NHL scoreboards in bounded date chunks.

    Scoreboard payloads expose quarter/period linescores directly and need far
    fewer requests than walking every team schedule.
    """
    start = as_of - timedelta(days=430)
    end_limit = as_of - timedelta(days=1)
    raw = []
    cur = start
    while cur <= end_limit:
        end = min(cur + timedelta(days=44), end_limit)
        cache_days = 30.0 if end < as_of - timedelta(days=30) else 0.25
        gs, err = espn.scoreboard_range(league, cur, end, cache_days=cache_days)
        if err:
            issues.append(f"{league.upper()} scoreboard {cur}–{end}: {err}")
        raw += gs
        cur = end + timedelta(days=1)
    return raw


def history(sport: str, period: str, as_of: date, cache: dict):
    key = (sport, period, as_of.isoformat())
    if key in cache:
        return cache[key]

    issues: list[str] = []
    if sport == "nba":
        raw = _schedule_raw("nba", as_of, issues)
    elif sport == "nfl":
        raw = _nfl_raw(as_of, issues)
    elif sport == "nhl":
        raw = _schedule_raw("nhl", as_of, issues)
    else:
        cache[key] = ([], issues)
        return cache[key]

    games = _dedupe_games(raw, period)
    cache[key] = (games, issues)
    return cache[key]


def _normal_cdf(x: float, mu: float, sigma: float) -> float:
    if sigma <= 1e-9:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2))))


def _normal_integer_pmf(mu: float, sigma: float, max_total: int):
    rows = []
    for k in range(max_total + 1):
        lo = -math.inf if k == 0 else k - 0.5
        hi = k + 0.5
        p_hi = 1.0 if math.isinf(hi) else _normal_cdf(hi, mu, sigma)
        p_lo = 0.0 if math.isinf(lo) else _normal_cdf(lo, mu, sigma)
        p = max(0.0, p_hi - p_lo)
        if p > 1e-12:
            rows.append((k, p))
    z = sum(p for _, p in rows)
    return [(k, p / z) for k, p in rows] if z else []


def _poisson_total_pmf(lam: float, max_total: int = 14):
    probs = []
    for k in range(max_total + 1):
        p = math.exp(-lam) * lam**k / math.factorial(k)
        probs.append((k, p))
    z = sum(p for _, p in probs)
    return [(k, p / z) for k, p in probs]


def _asian_legs(line: float):
    q = round(float(line) * 4.0) / 4.0
    # whole or half line
    if abs(q * 2 - round(q * 2)) < 1e-9:
        return [q]
    return [q - 0.25, q + 0.25]


def _fair_from_pmf(pmf, line: float, over: bool):
    win = loss = 0.0
    for total, p in pmf:
        legs = _asian_legs(line)
        frac = 1.0 / len(legs)
        for leg in legs:
            v = (total - leg) if over else (leg - total)
            if v > 1e-12:
                win += p * frac
            elif v < -1e-12:
                loss += p * frac
    if win <= 0:
        return None
    fair = 1.0 + loss / win
    return fair, 1.0 / fair


def _points_period_fair(
    sport: str,
    period: str,
    home: str,
    away: str,
    as_of: date,
    line: float,
    over: bool,
    cache: dict,
):
    games, issues = history(sport, period, as_of, cache)
    min_games = 250 if sport == "nba" else 100
    if len(games) < min_games:
        return None, f"{sport.upper()} {period}: zu wenig ESPN-Linescore-Daten ({len(games)})", issues

    half_life = 90.0 if sport == "nba" else 120.0
    ridge = 8.0 if sport == "nba" else 4.0
    model = PointsModel.fit(games, as_of, half_life_days=half_life, ridge=ridge)

    names = list(model.off)
    h = matching.find(home, names)
    a = matching.find(away, names)
    if not h or not a:
        return None, f"{sport.upper()} {period}: Teams nicht eindeutig im Modell", issues

    ph, pa = model.expected_points(h, a)
    mu = ph + pa
    max_total = 120 if sport == "nba" and period == "q1" else (
        220 if sport == "nba" else 90
    )
    pmf = _normal_integer_pmf(mu, model.sigma_total, max_total)
    fp = _fair_from_pmf(pmf, line, over)
    if not fp:
        return None, f"{sport.upper()} {period}: Fair nicht berechenbar", issues
    fair_odds, p = fp
    return PeriodFair(
        fair_odds=fair_odds,
        probability=p,
        expected_total=mu,
        sample_games=len(games),
        model=f"{sport.upper()} {period} PointsModel",
    ), None, issues


def _nhl_p1_fair(home, away, as_of, line, over, cache):
    games, issues = history("nhl", "p1", as_of, cache)
    if len(games) < 250:
        return None, f"NHL p1: zu wenig ESPN-Linescore-Daten ({len(games)})", issues

    ms = [Match(g.date, g.home, g.away, g.home_pts, g.away_pts) for g in games]
    model = PoissonModel.fit(
        ms, as_of, half_life_days=240, xg_weight=0.0,
        shrink=8.0, rho=0.0, max_goals=7,
    )
    names = list(model.attack)
    h = matching.find(home, names)
    a = matching.find(away, names)
    if not h or not a:
        return None, "NHL p1: Teams nicht eindeutig im Modell", issues
    lh, la = model.expected_goals(h, a)
    pmf = _poisson_total_pmf(lh + la, max_total=12)
    fp = _fair_from_pmf(pmf, line, over)
    if not fp:
        return None, "NHL p1: Fair nicht berechenbar", issues
    fair_odds, p = fp
    return PeriodFair(
        fair_odds=fair_odds,
        probability=p,
        expected_total=lh + la,
        sample_games=len(games),
        model="NHL p1 Poisson",
    ), None, issues


def fair_total(
    sport: str,
    period: str,
    home: str,
    away: str,
    kickoff: datetime,
    line: float,
    over: bool,
    cache: dict,
):
    if sport in {"nba", "nfl"} and period in {"q1", "1h"}:
        return _points_period_fair(
            sport, period, home, away, kickoff.date(), line, over, cache,
        )
    if sport == "nhl" and period == "p1":
        return _nhl_p1_fair(home, away, kickoff.date(), line, over, cache)
    return None, f"Periodenmarkt nicht unterstützt: {sport} {period}", []
