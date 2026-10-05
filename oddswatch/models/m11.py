"""M11 Fußballmodell: Tore + echtes Understat-xG + Elo/Form/Rest.

M11 nutzt zwei getrennte Poisson-Komponenten:
- Torstärke aus allen historischen Ligaspielen
- Chancenstärke ausschließlich aus Spielen mit echtem Understat Match-xG

Marktquoten sind KEINE Features.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from .m8 import _elo, _rest_diff, M8Params
from .poisson import Match, PoissonModel, markets_from_matrix


@dataclass
class M11Params:
    half_life_days: float = 180.0
    shrink: float = 5.0
    rho: float = -0.05
    xg_blend: float = 0.75
    elo_k: float = 20.0
    elo_home: float = 45.0
    elo_scale: float = 0.12
    xg_form_scale: float = 0.08
    rest_scale: float = 0.008
    form_games: int = 8
    poisson_iterations: int = 80


@dataclass
class M11Model:
    goals: PoissonModel
    chances: PoissonModel
    matches: list[Match]
    xg_matches: list[Match]
    ratings: dict[str, float]
    params: M11Params
    as_of: date

    @classmethod
    def fit(cls, matches: list[Match], as_of: date,
            params: M11Params | None = None) -> "M11Model":
        p = params or M11Params()
        hist = sorted((m for m in matches if m.date < as_of), key=lambda m: m.date)
        xg_hist = [m for m in hist if m.home_xg is not None and m.away_xg is not None]
        if len(hist) < 50:
            raise ValueError("zu wenige historische Spiele für M11")
        if len(xg_hist) < 50:
            raise ValueError("zu wenige echte xG-Spiele für M11")
        kw = dict(
            as_of=as_of, half_life_days=p.half_life_days, shrink=p.shrink,
            rho=p.rho, iterations=p.poisson_iterations,
        )
        goals = PoissonModel.fit(hist, xg_weight=0.0, **kw)
        chances = PoissonModel.fit(xg_hist, xg_weight=1.0, **kw)
        ep = M8Params(elo_k=p.elo_k, elo_home=p.elo_home)
        ratings = _elo(hist, ep)
        return cls(goals, chances, hist, xg_hist, ratings, p, as_of)

    def expected_goals(self, home: str, away: str, kickoff: date | None = None,
                       neutral: bool = False) -> tuple[float, float]:
        gh, ga = self.goals.expected_goals(home, away, neutral=neutral)
        xh, xa = self.chances.expected_goals(home, away, neutral=neutral)
        w = min(max(self.params.xg_blend, 0.0), 1.0)
        lh = math.exp((1 - w) * math.log(max(gh, 1e-6)) + w * math.log(max(xh, 1e-6)))
        la = math.exp((1 - w) * math.log(max(ga, 1e-6)) + w * math.log(max(xa, 1e-6)))

        d = (self.ratings.get(home, 1500.0) - self.ratings.get(away, 1500.0)) / 400.0
        adj = self.params.elo_scale * d
        adj += self.params.xg_form_scale * (
            _recent_real_xg_diff(self.xg_matches, home, kickoff or self.as_of, self.params.form_games)
            - _recent_real_xg_diff(self.xg_matches, away, kickoff or self.as_of, self.params.form_games)
        )
        adj += self.params.rest_scale * _rest_diff(
            self.matches, home, away, kickoff or self.as_of
        )
        adj = max(-0.30, min(0.30, adj))
        return lh * math.exp(adj), la * math.exp(-adj)

    def markets(self, home: str, away: str, kickoff: date | None = None,
                neutral: bool = False) -> dict[str, float]:
        lh, la = self.expected_goals(home, away, kickoff, neutral)
        mat = self.goals.score_matrix(lh, la)
        return markets_from_matrix(mat, lh, la)


def _recent_real_xg_diff(matches: list[Match], team: str, before: date, n: int) -> float:
    rows = [m for m in matches if m.date < before and team in (m.home, m.away)][-n:]
    vals = []
    for m in rows:
        if m.home_xg is None or m.away_xg is None:
            continue
        vals.append((m.home_xg - m.away_xg) if m.home == team
                    else (m.away_xg - m.home_xg))
    if not vals:
        return 0.0
    return max(-1.5, min(1.5, sum(vals) / len(vals)))
