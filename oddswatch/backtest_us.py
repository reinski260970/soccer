"""Walk-forward-Backtest NFL und NHL gegen historische Buchmacherlinien.

Quelle der Linien: ESPN Core-API (je Spiel Eröffnung und Closing der
Moneyline; NFL meist ESPN BET, NHL DraftKings). Das Modell wird wöchentlich
nur mit vorher gespielten Partien neu gefittet – mit denselben Parametern
wie im Scan. Bewertung wie im Fußball-Backtest (backtest.evaluate):
LogLoss von w·Modell + (1−w)·Eröffnung, Tipps nach Regel (Quote ≥ 1,03/p)
mit CLV gegen die Closing-Line und ROI.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import fetch, matching, pricing
from .models.poisson import PoissonModel, hockey_regulation_to_moneyline
from .models.ratings import Game, PointsModel
from .sources import espn, nhl

CORE = "https://sports.core.api.espn.com/v2/sports"


def _american(v) -> float | None:
    try:
        v = float(str(v).replace("+", ""))
    except (TypeError, ValueError):
        return None
    if v == 0:
        return None
    return 1 + (v / 100 if v > 0 else 100 / -v)


def _ml(side: dict, key: str) -> float | None:
    part = side.get(key)
    if isinstance(part, dict):
        ml = part.get("moneyLine")
        if isinstance(ml, dict):
            return _american(ml.get("american") or ml.get("alternateDisplayValue"))
        return _american(ml)
    return None


def line(sport: str, league: str, event_id: str) -> tuple[list[float], list[float]] | None:
    """(Eröffnung [heim, gast], Closing [heim, gast]) als Dezimalquoten."""
    d, _ = fetch.get_json(f"{CORE}/{sport}/leagues/{league}/events/{event_id}/competitions/"
                          f"{event_id}/odds", cache_days=365)
    for it in (d or {}).get("items", []):
        if "live" in (it.get("provider") or {}).get("name", "").lower():
            continue
        h, a = it.get("homeTeamOdds") or {}, it.get("awayTeamOdds") or {}
        o = [_ml(h, "open"), _ml(a, "open")]
        c = [_ml(h, "close"), _ml(a, "close")]
        if not all(c):
            c = [_american(h.get("moneyLine")), _american(a.get("moneyLine"))]
        if all(o) and all(c) and all(x > 1 for x in o + c):
            return o, c
    return None


def _sample(pm: list[float], o: list[float], c: list[float], home_won: bool) -> tuple:
    return (pm, pricing.devig(o), [home_won, not home_won], o, pricing.devig(c))


# ------------------------------------------------------------------- NFL
def nfl_samples(cur: int) -> list[tuple]:
    raw: list[espn.EspnGame] = []
    for season in (cur - 2, cur - 1, cur):
        for wk in range(1, 19):
            g, _ = espn.nfl_week(season, wk, 2, cache_days=0 if season == cur else 365)
            raw += g
        if season < cur:
            for wk in range(1, 6):
                g, _ = espn.nfl_week(season, wk, 3, cache_days=365)
                raw += g
    seen, fin = set(), []
    for g in sorted(raw, key=lambda x: x.kickoff):
        if g.final and g.id not in seen and g.home_score is not None and g.home_score != g.away_score:
            seen.add(g.id)
            fin.append(g)
    games = [Game(g.kickoff.date(), g.home.name, g.away.name, g.home_score, g.away_score, g.neutral)
             for g in fin]
    out, model, last = [], None, None
    test_from = date(cur - 1, 9, 20)          # ab Woche 3 der Vorsaison
    for g in fin:
        d = g.kickoff.date()
        if d < test_from:
            continue
        if last is None or (d - last).days >= 6:
            hist = [x for x in games if x.date < d]
            model = PointsModel.fit(hist, d, half_life_days=120, ridge=3.0)
            last = d
        try:
            mk = model.markets(g.home.name, g.away.name, neutral=g.neutral)
        except KeyError:
            continue
        ln = line("football", "nfl", g.id)
        if ln:
            out.append(_sample([mk["ML1"], mk["ML2"]], *ln, g.home_score > g.away_score))
    return out


# ------------------------------------------------------------------- NHL
def nhl_samples(cur: int, stride_days: int = 1) -> list[tuple]:
    prev2, prev = f"{cur - 2}{cur - 1}", f"{cur - 1}{cur}"
    ms, names, _ = nhl.season_games(prev2, cache_days=365)
    ms2, names2, _ = nhl.season_games(prev, cache_days=30)
    names.update(names2)
    ms = sorted(ms + ms2, key=lambda m: m.date)
    by_name = {v: k for k, v in names.items()}
    test_days = sorted({m.date for m in ms2 if m.date >= date(cur - 1, 10, 25)})[::stride_days]
    out, model, last = [], None, None
    for d in test_days:
        if last is None or (d - last).days >= 7:
            model = PoissonModel.fit([m for m in ms if m.date < d], d, half_life_days=365,
                                     xg_weight=0.0, shrink=10.0, rho=0.0)
            last = d
        games, _ = espn.scoreboard_day("nhl", d, cache_days=365)
        for g in games:
            if not g.final or g.home_score is None or g.home_score == g.away_score:
                continue
            h = by_name.get(matching.find(g.home.name, list(by_name)) or "")
            a = by_name.get(matching.find(g.away.name, list(by_name)) or "")
            if not h or not a or h not in model.attack or a not in model.attack:
                continue
            mk = model.markets(h, a)
            ph, pa = hockey_regulation_to_moneyline(mk["1"], mk["X"], mk["2"])
            ln = line("hockey", "nhl", g.id)
            if ln:
                out.append(_sample([ph, pa], *ln, g.home_score > g.away_score))
    return out


def rule_by_divergence(samples: list[tuple], w: float = 0.25, max_div: float = 0.15) -> dict:
    """Regel wie im alten Scan (w=0,25, Divergenzsperre) – zur Einordnung."""
    n = pnl = 0
    clv = []
    for pm, po, y, odds, pc in samples:
        for i in range(2):
            if abs(pm[i] - po[i]) > max_div:
                continue
            p = w * pm[i] + (1 - w) * po[i]
            if odds[i] >= 1.03 / p:
                n += 1
                pnl += (odds[i] - 1) if y[i] else -1
                clv.append(odds[i] * pc[i] - 1)
    return {"n": n, "roi": pnl / n if n else 0.0, "clv": sum(clv) / len(clv) if clv else 0.0}
