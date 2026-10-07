"""Austria structural shadow based on the M17.11 core idea.

This is NOT the Primeira-trained M17.11 classifier transferred to Austria.
That would be methodologically invalid. Instead this module ports only the
structural concept to Austria:

- current real xG/xGA aggregate strength (fast signal)
- recent actual GF/GA structural strength (slow signal)
- opponent-adjusted attack/defence
- league home/away scoring baseline
- geometric consensus of fast/slow expected goals
- Dixon-Coles/Poisson is used ONLY to translate expected goals to 1X2
  probabilities; it does not estimate team strength.

No bookmaker price enters the fair model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from . import matching
from .models.poisson import Match, PoissonModel, markets_from_matrix
from .sources.xg_external import XGSnapshot


@dataclass
class AustriaStructuralFair:
    probs: dict[str, float]
    home_xg: float
    away_xg: float
    home_fast: float
    away_fast: float
    home_slow: float
    away_slow: float
    home_xg_matches: int
    away_xg_matches: int
    home_recent_n: int
    away_recent_n: int


def _clip(v: float, lo: float = 0.20, hi: float = 4.50) -> float:
    return max(lo, min(hi, float(v)))


def _safe_log_ratio(v: float, base: float) -> float:
    return math.log(max(float(v), 0.10) / max(float(base), 0.10))


def _league_goal_baseline(matches: list[Match], as_of: date) -> tuple[float, float]:
    rows = [m for m in matches if m.date < as_of]
    rows = rows[-120:]
    if not rows:
        return 1.45, 1.20
    return (
        sum(float(m.home_goals) for m in rows) / len(rows),
        sum(float(m.away_goals) for m in rows) / len(rows),
    )


def _recent_team(matches: list[Match], team: str, as_of: date, n: int = 10) -> tuple[float, float, int]:
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
        return 1.35, 1.35, 0
    return (
        sum(x[1] for x in rows) / len(rows),
        sum(x[2] for x in rows) / len(rows),
        len(rows),
    )


def _find_snapshot(team: str, snaps: list[XGSnapshot]) -> XGSnapshot | None:
    names = [r.team for r in snaps]
    hit = matching.find(team, names)
    if not hit:
        return None
    return next((r for r in snaps if r.team == hit), None)


def fair(
    home: str,
    away: str,
    kickoff: date,
    matches: list[Match],
    snapshots: list[XGSnapshot],
) -> AustriaStructuralFair:
    hs = _find_snapshot(home, snapshots)
    ass = _find_snapshot(away, snapshots)
    if hs is None or ass is None:
        raise KeyError(f"xG-Team nicht zugeordnet: {home} / {away}")

    league_xg = sum(float(r.xg) for r in snapshots) / len(snapshots)
    league_xga = sum(float(r.xga) for r in snapshots) / len(snapshots)
    base_h_goal, base_a_goal = _league_goal_baseline(matches, kickoff)

    # Current xG aggregates are the fast signal. MatchPulse has no venue split,
    # so home advantage comes only from the independent league home/away base.
    h_att_fast = _safe_log_ratio(hs.xg, league_xg)
    h_def_fast = -_safe_log_ratio(hs.xga, league_xga)
    a_att_fast = _safe_log_ratio(ass.xg, league_xg)
    a_def_fast = -_safe_log_ratio(ass.xga, league_xga)
    home_fast = _clip(base_h_goal * math.exp(h_att_fast - a_def_fast))
    away_fast = _clip(base_a_goal * math.exp(a_att_fast - h_def_fast))

    # Slow signal from recent results only. This is deliberately separate from
    # current xG and is used as structural consensus, not as a market blend.
    hgf, hga, hn = _recent_team(matches, home, kickoff)
    agf, aga, an = _recent_team(matches, away, kickoff)
    league_team_goal = max((base_h_goal + base_a_goal) / 2.0, 0.10)
    h_att_slow = _safe_log_ratio(hgf, league_team_goal)
    h_def_slow = -_safe_log_ratio(hga, league_team_goal)
    a_att_slow = _safe_log_ratio(agf, league_team_goal)
    a_def_slow = -_safe_log_ratio(aga, league_team_goal)
    home_slow = _clip(base_h_goal * math.exp(h_att_slow - a_def_slow))
    away_slow = _clip(base_a_goal * math.exp(a_att_slow - h_def_slow))

    # No tuned Austria weight exists. Geometric consensus treats fast/slow
    # symmetrically and prevents one noisy signal from dominating.
    home_xg = _clip(math.sqrt(home_fast * home_slow))
    away_xg = _clip(math.sqrt(away_fast * away_slow))

    converter = PoissonModel(rho=-0.05, max_goals=10)
    matrix = converter.score_matrix(home_xg, away_xg)
    mk = markets_from_matrix(matrix, home_xg, away_xg)
    probs = {"home": mk["1"], "draw": mk["X"], "away": mk["2"]}

    return AustriaStructuralFair(
        probs=probs,
        home_xg=home_xg,
        away_xg=away_xg,
        home_fast=home_fast,
        away_fast=away_fast,
        home_slow=home_slow,
        away_slow=away_slow,
        home_xg_matches=int(hs.matches),
        away_xg_matches=int(ass.matches),
        home_recent_n=hn,
        away_recent_n=an,
    )
