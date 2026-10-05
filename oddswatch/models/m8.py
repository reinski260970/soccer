"""M8 Fußballmodell: unabhängiger Hybrid aus Poisson/xG, Elo, Form und Rest.

Keine Marktquote ist ein Feature. Marktpreise dürfen ausschließlich außerhalb dieses
Moduls zur Validierung bzw. Value-Berechnung verwendet werden.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from .poisson import Match, PoissonModel, markets_from_matrix


@dataclass
class M8Params:
    half_life_days: float = 180.0
    xg_weight: float = 0.5
    shrink: float = 5.0
    rho: float = -0.05
    elo_k: float = 20.0
    elo_home: float = 45.0
    elo_scale: float = 0.22
    form_scale: float = 0.08
    rest_scale: float = 0.012
    form_games: int = 6


@dataclass
class M8Model:
    poisson: PoissonModel
    matches: list[Match]
    ratings: dict[str, float]
    params: M8Params
    as_of: date

    @classmethod
    def fit(cls, matches: list[Match], as_of: date, params: M8Params | None = None) -> "M8Model":
        p = params or M8Params()
        hist = sorted((m for m in matches if m.date < as_of), key=lambda m: m.date)
        if len(hist) < 50:
            raise ValueError("zu wenige historische Spiele für M8")
        poisson = PoissonModel.fit(
            hist, as_of,
            half_life_days=p.half_life_days,
            xg_weight=p.xg_weight,
            shrink=p.shrink,
            rho=p.rho,
        )
        ratings = _elo(hist, p)
        return cls(poisson=poisson, matches=hist, ratings=ratings, params=p, as_of=as_of)

    def expected_goals(self, home: str, away: str, kickoff: date | None = None,
                       neutral: bool = False) -> tuple[float, float]:
        lh, la = self.poisson.expected_goals(home, away, neutral=neutral)
        if home not in self.ratings or away not in self.ratings:
            raise KeyError(f"Team ohne M8-Rating: {home if home not in self.ratings else away}")

        # Elo ergänzt die Poisson-Angriff/Defensivschätzung, ohne Marktinformation.
        elo_diff = (self.ratings[home] - self.ratings[away]) / 400.0
        adj = self.params.elo_scale * elo_diff

        # Kurzfristige Form: gegnerbereinigte Outcome-Leistung relativ zur Elo-Erwartung.
        fh = _form_residual(self.matches, home, kickoff or self.as_of,
                            self.ratings, self.params, self.params.form_games)
        fa = _form_residual(self.matches, away, kickoff or self.as_of,
                            self.ratings, self.params, self.params.form_games)
        adj += self.params.form_scale * (fh - fa)

        # Rest nur als kleine, gedeckelte Korrektur.
        rd = _rest_diff(self.matches, home, away, kickoff or self.as_of)
        adj += self.params.rest_scale * rd

        adj = max(-0.35, min(0.35, adj))
        return lh * math.exp(adj), la * math.exp(-adj)

    def markets(self, home: str, away: str, kickoff: date | None = None,
                neutral: bool = False) -> dict[str, float]:
        lh, la = self.expected_goals(home, away, kickoff, neutral)
        mat = self.poisson.score_matrix(lh, la)
        return markets_from_matrix(mat, lh, la)


def _elo(matches: list[Match], p: M8Params) -> dict[str, float]:
    ratings: dict[str, float] = {}
    for m in matches:
        rh = ratings.setdefault(m.home, 1500.0)
        ra = ratings.setdefault(m.away, 1500.0)
        exp_h = 1.0 / (1.0 + 10.0 ** (-(rh + p.elo_home - ra) / 400.0))
        actual = 1.0 if m.home_goals > m.away_goals else (0.5 if m.home_goals == m.away_goals else 0.0)
        gd = abs(m.home_goals - m.away_goals)
        mult = 1.0 + 0.15 * min(gd, 4.0)
        delta = p.elo_k * mult * (actual - exp_h)
        ratings[m.home] = rh + delta
        ratings[m.away] = ra - delta
    return ratings


def _form_residual(matches: list[Match], team: str, before: date,
                   ratings: dict[str, float], p: M8Params, n: int) -> float:
    rows = [m for m in matches if m.date < before and team in (m.home, m.away)][-n:]
    if not rows:
        return 0.0
    vals = []
    for m in rows:
        home = team == m.home
        opp = m.away if home else m.home
        rt = ratings.get(team, 1500.0)
        ro = ratings.get(opp, 1500.0)
        diff = rt + (p.elo_home if home else -p.elo_home) - ro
        exp = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
        if home:
            actual = 1.0 if m.home_goals > m.away_goals else (0.5 if m.home_goals == m.away_goals else 0.0)
        else:
            actual = 1.0 if m.away_goals > m.home_goals else (0.5 if m.home_goals == m.away_goals else 0.0)
        vals.append(actual - exp)
    return sum(vals) / len(vals)


def _rest_diff(matches: list[Match], home: str, away: str, kickoff: date) -> float:
    def rest(team: str) -> int:
        ds = [m.date for m in matches if m.date < kickoff and team in (m.home, m.away)]
        return min((kickoff - max(ds)).days, 14) if ds else 7
    # Mehr als fünf Tage Differenz soll nie großen Modell-Effekt erzeugen.
    return float(max(-5, min(5, rest(home) - rest(away))))
