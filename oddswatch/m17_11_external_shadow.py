"""Generic structural shadow for leagues without Understat.

Fair model only. Market prices never enter this module.

Signals:
- current real xG/xGA snapshot (MatchPulse or other verified provider)
- optional second xG source as a cross-check / geometric consensus
- SoccerSTATS home/away GF/GA + PPG venue structure
- optional recent actual GF/GA from our own historical results

Poisson/Dixon-Coles is used only to translate finished expected-goal estimates
into 1X2 probabilities. It does not estimate team strength.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from . import matching
from .models.poisson import Match, PoissonModel, markets_from_matrix
from .sources.xg_external import XGSnapshot
from .sources.soccerstats import TeamVenuePrior


@dataclass
class ExternalStructuralFair:
    probs: dict[str, float]
    home_xg: float
    away_xg: float
    home_fast: float
    away_fast: float
    home_fast_primary: float
    away_fast_primary: float
    home_fast_alt: float | None
    away_fast_alt: float | None
    xg_source_disagreement: float | None
    home_slow: float | None
    away_slow: float | None
    home_venue: float | None
    away_venue: float | None
    home_ppg: float | None
    away_ppg: float | None
    home_recent_n: int
    away_recent_n: int
    signals_used: int


def _clip(v: float, lo: float = 0.20, hi: float = 4.50) -> float:
    return max(lo, min(hi, float(v)))


def _log_ratio(v: float, base: float) -> float:
    return math.log(max(float(v), 0.10) / max(float(base), 0.10))


def _alias_candidates(team: str, aliases: dict[str, list[str] | str] | None):
    vals = [team]
    if aliases and team in aliases:
        x = aliases[team]
        vals += [x] if isinstance(x, str) else list(x)
    return [v for v in vals if v]


def _find_snapshot(team: str, rows: list[XGSnapshot], aliases=None) -> XGSnapshot | None:
    names = [r.team for r in rows]
    for cand in _alias_candidates(team, aliases):
        hit = matching.find(cand, names)
        if hit:
            return next((r for r in rows if r.team == hit), None)
    return None


def _find_venue(team: str, rows: list[TeamVenuePrior], aliases=None) -> TeamVenuePrior | None:
    names = [r.team for r in rows]
    for cand in _alias_candidates(team, aliases):
        hit = matching.find(cand, names)
        if hit:
            return next((r for r in rows if r.team == hit), None)
    return None


def _find_alt(team: str, rows: dict[str, tuple[float, float]], aliases=None):
    for cand in _alias_candidates(team, aliases):
        if cand in rows:
            return rows[cand]
        hit = matching.find(cand, list(rows))
        if hit:
            return rows[hit]
    return None


def _league_baseline(matches: list[Match], venue: list[TeamVenuePrior], as_of: date):
    hist = [m for m in matches if m.date < as_of][-160:]
    if hist:
        return (
            sum(float(m.home_goals) for m in hist) / len(hist),
            sum(float(m.away_goals) for m in hist) / len(hist),
        )
    hgp = sum(r.home_gp for r in venue)
    agp = sum(r.away_gp for r in venue)
    if hgp and agp:
        return (
            sum(r.home_gf_pg * r.home_gp for r in venue) / hgp,
            sum(r.away_gf_pg * r.away_gp for r in venue) / agp,
        )
    return 1.45, 1.20


def _recent(matches: list[Match], team: str, as_of: date, n: int = 10):
    rows = []
    for m in matches:
        if m.date >= as_of:
            continue
        if m.home == team:
            rows.append((m.date, float(m.home_goals), float(m.away_goals)))
        elif m.away == team:
            rows.append((m.date, float(m.away_goals), float(m.home_goals)))
    rows.sort(key=lambda x: x[0])
    rows = rows[-n:]
    if not rows:
        return None, None, 0
    return (
        sum(x[1] for x in rows) / len(rows),
        sum(x[2] for x in rows) / len(rows),
        len(rows),
    )


def _venue_expectation(home, away, rows, base_h, base_a, aliases=None):
    h = _find_venue(home, rows, aliases)
    a = _find_venue(away, rows, aliases)
    if h is None or a is None:
        return None, None, None, None
    hraw = math.sqrt(max(h.home_gf_pg, .10) * max(a.away_ga_pg, .10))
    araw = math.sqrt(max(a.away_gf_pg, .10) * max(h.home_ga_pg, .10))
    hc = min(h.home_gp, a.away_gp, 8) / 8.0
    ac = min(a.away_gp, h.home_gp, 8) / 8.0
    hv = _clip((1 - .5*hc) * base_h + (.5*hc) * hraw)
    av = _clip((1 - .5*ac) * base_a + (.5*ac) * araw)
    return hv, av, h.home_ppg, a.away_ppg


def fair(
    home: str,
    away: str,
    kickoff: date,
    snapshots: list[XGSnapshot],
    venue_rows: list[TeamVenuePrior],
    matches: list[Match] | None = None,
    alt_xg: dict[str, tuple[float, float]] | None = None,
    aliases: dict[str, list[str] | str] | None = None,
) -> ExternalStructuralFair:
    matches = matches or []
    hs = _find_snapshot(home, snapshots, aliases)
    ass = _find_snapshot(away, snapshots, aliases)
    if hs is None or ass is None:
        raise KeyError(f"xG-Team nicht zugeordnet: {home} / {away}")

    lxg = sum(float(r.xg) for r in snapshots) / len(snapshots)
    lxga = sum(float(r.xga) for r in snapshots) / len(snapshots)
    base_h, base_a = _league_baseline(matches, venue_rows, kickoff)
    if not matches and not venue_rows:
        # No league-specific result/venue history: anchor the scoring level to
        # the current real-xG league mean, with only a mild generic home split.
        # Shadow only; this assumption is tracked by estimate=True upstream.
        level = max((lxg + lxga) / 2.0, 0.60)
        base_h, base_a = level * 1.08, level * 0.92

    hp = _clip(base_h * math.exp(_log_ratio(hs.xg, lxg) + _log_ratio(ass.xga, lxga)))
    ap = _clip(base_a * math.exp(_log_ratio(ass.xg, lxg) + _log_ratio(hs.xga, lxga)))

    ha = aa = disagreement = None
    if alt_xg:
        ah = _find_alt(home, alt_xg, aliases)
        ax = _find_alt(away, alt_xg, aliases)
        if ah and ax:
            alxg = sum(v[0] for v in alt_xg.values()) / len(alt_xg)
            alxga = sum(v[1] for v in alt_xg.values()) / len(alt_xg)
            ha = _clip(base_h * math.exp(_log_ratio(ah[0], alxg) + _log_ratio(ax[1], alxga)))
            aa = _clip(base_a * math.exp(_log_ratio(ax[0], alxg) + _log_ratio(ah[1], alxga)))
            disagreement = abs(math.log(hp/ha)) + abs(math.log(ap/aa))

    hf = _clip(math.sqrt(hp * ha)) if ha is not None else hp
    af = _clip(math.sqrt(ap * aa)) if aa is not None else ap

    hgf, hga, hn = _recent(matches, home, kickoff)
    agf, aga, an = _recent(matches, away, kickoff)
    hslo = aslo = None
    if hn and an:
        lg = max((base_h + base_a) / 2.0, .10)
        hslo = _clip(base_h * math.exp(_log_ratio(hgf, lg) + _log_ratio(aga, lg)))
        aslo = _clip(base_a * math.exp(_log_ratio(agf, lg) + _log_ratio(hga, lg)))

    hv, av, hppg, appg = _venue_expectation(home, away, venue_rows, base_h, base_a, aliases)

    hsigs = [hf] + ([hslo] if hslo is not None else []) + ([hv] if hv is not None else [])
    asigs = [af] + ([aslo] if aslo is not None else []) + ([av] if av is not None else [])
    hx = _clip(math.exp(sum(math.log(x) for x in hsigs) / len(hsigs)))
    ax = _clip(math.exp(sum(math.log(x) for x in asigs) / len(asigs)))

    conv = PoissonModel(rho=-0.05, max_goals=10)
    mk = markets_from_matrix(conv.score_matrix(hx, ax), hx, ax)
    probs = {"home": mk["1"], "draw": mk["X"], "away": mk["2"]}

    return ExternalStructuralFair(
        probs=probs,
        home_xg=hx, away_xg=ax,
        home_fast=hf, away_fast=af,
        home_fast_primary=hp, away_fast_primary=ap,
        home_fast_alt=ha, away_fast_alt=aa,
        xg_source_disagreement=disagreement,
        home_slow=hslo, away_slow=aslo,
        home_venue=hv, away_venue=av,
        home_ppg=hppg, away_ppg=appg,
        home_recent_n=hn, away_recent_n=an,
        signals_used=(2 if ha is not None and aa is not None else 1)
                     + (1 if hslo is not None and aslo is not None else 0)
                     + (1 if hv is not None and av is not None else 0),
    )
