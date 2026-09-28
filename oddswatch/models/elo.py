"""Elo -> Torerwartung -> 1X2.

log(lambda_heim) = a + b * d,  log(lambda_gast) = a - b * d,
d = (Elo_heim + H * heim - Elo_gast) / 400.
a und b werden per Poisson-Maximum-Likelihood auf historischen Spielen mit
Elo-Werten vor dem Spiel geschätzt; die 1X2-Wahrscheinlichkeiten kommen aus
der Dixon-Coles-Tormatrix des Poisson-Modells.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .poisson import PoissonModel, markets_from_matrix


@dataclass
class EloGoals:
    a: float = 0.25
    b: float = 0.9
    home: float = 100.0     # Elo-Punkte Heimvorteil (eloratings.net: 100)
    rho: float = -0.05

    @classmethod
    def fit(cls, rows: list[tuple[float, int, float, float]], home: float = 100.0,
            rho: float = -0.05, iterations: int = 50) -> "EloGoals":
        """rows: (Elo-Differenz Heim-Gast ohne Heimvorteil, Heim-Kennz. +1/0/-1,
        Tore Heim, Tore Gast)."""
        obs = []
        for diff, edge, hg, ag in rows:
            d = (diff + home * edge) / 400
            obs += [(d, hg), (-d, ag)]
        if len(obs) < 50:
            raise ValueError("zu wenige Spiele für die Kalibrierung")
        a, b = math.log(sum(y for _, y in obs) / len(obs)), 0.0
        for _ in range(iterations):
            ga = gb = haa = hab = hbb = 0.0
            for x, y in obs:
                lam = math.exp(a + b * x)
                ga += y - lam
                gb += (y - lam) * x
                haa += lam
                hab += lam * x
                hbb += lam * x * x
            det = haa * hbb - hab * hab
            da = (hbb * ga - hab * gb) / det
            db = (haa * gb - hab * ga) / det
            a, b = a + da, b + db
            if abs(da) + abs(db) < 1e-9:
                break
        return cls(a=a, b=b, home=home, rho=rho)

    def expected_goals(self, elo_home: float, elo_away: float,
                       neutral: bool = False) -> tuple[float, float]:
        d = (elo_home - elo_away + (0 if neutral else self.home)) / 400
        return math.exp(self.a + self.b * d), math.exp(self.a - self.b * d)

    def markets(self, elo_home: float, elo_away: float, neutral: bool = False) -> dict[str, float]:
        lh, la = self.expected_goals(elo_home, elo_away, neutral)
        m = PoissonModel(rho=self.rho).score_matrix(lh, la)
        return markets_from_matrix(m, lh, la)
