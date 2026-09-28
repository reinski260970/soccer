"""Punkte-Modell für NBA/NFL.

Punktdifferenz = home_adv + r_home - r_away + eps, eps ~ N(0, sigma).
Offense/Defense getrennt für Totals: pts_h = base + home/2 + off_h - def_a.
Fit per gewichteter Ridge-Regression (Gauss-Seidel), Zeitverfall wie im
Tor-Modell.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Game:
    date: date
    home: str
    away: str
    home_pts: float
    away_pts: float
    neutral: bool = False


@dataclass
class PointsModel:
    base: float = 0.0
    home_adv: float = 0.0
    off: dict[str, float] = field(default_factory=dict)
    dfn: dict[str, float] = field(default_factory=dict)
    sigma_margin: float = 12.0
    sigma_total: float = 18.0

    @classmethod
    def fit(cls, games: list[Game], as_of: date, half_life_days: float = 120.0,
            ridge: float = 3.0, iterations: int = 300) -> "PointsModel":
        rows = []
        for g in games:
            age = (as_of - g.date).days
            if age < 0:
                continue
            rows.append((g, 0.5 ** (age / half_life_days)))
        if not rows:
            raise ValueError("keine Spiele vor dem Stichtag")
        teams = sorted({g.home for g, _ in rows} | {g.away for g, _ in rows})
        off = {t: 0.0 for t in teams}
        dfn = {t: 0.0 for t in teams}
        tw = sum(w for _, w in rows)
        base = sum((g.home_pts + g.away_pts) * w for g, w in rows) / (2 * tw)
        home = 0.0
        for _ in range(iterations):
            # Heimvorteil
            num = den = 0.0
            for g, w in rows:
                if g.neutral:
                    continue
                num += w * ((g.home_pts - base - off[g.home] + dfn[g.away]) -
                            (g.away_pts - base - off[g.away] + dfn[g.home]))
                den += w  # Differenz Heim - Aus enthält home_adv genau einmal
            home = num / den if den else 0.0
            delta = 0.0
            for t in teams:
                no = nd = do = dd = 0.0
                for g, w in rows:
                    h = 0.0 if g.neutral else home / 2
                    if g.home == t:
                        no += w * (g.home_pts - base - h + dfn[g.away]); nd += w
                        do += w * (base - h + off[g.away] - g.away_pts); dd += w
                    elif g.away == t:
                        no += w * (g.away_pts - base + h + dfn[g.home]); nd += w
                        do += w * (base + h + off[g.home] - g.home_pts); dd += w
                new_o, new_d = no / (nd + ridge), do / (dd + ridge)
                delta = max(delta, abs(new_o - off[t]), abs(new_d - dfn[t]))
                off[t], dfn[t] = new_o, new_d
            if delta < 1e-6:
                break
        m = cls(base=base, home_adv=home, off=off, dfn=dfn)
        rm = rt = ws = 0.0
        for g, w in rows:
            ph, pa = m.expected_points(g.home, g.away, g.neutral)
            rm += w * ((g.home_pts - g.away_pts) - (ph - pa)) ** 2
            rt += w * ((g.home_pts + g.away_pts) - (ph + pa)) ** 2
            ws += w
        n = len(rows)
        dof = max(n - 2 * len(teams) - 2, max(n // 3, 1))
        m.sigma_margin = math.sqrt(rm / ws * n / dof)
        m.sigma_total = math.sqrt(rt / ws * n / dof)
        return m

    def expected_points(self, home: str, away: str, neutral: bool = False,
                        home_adj: float = 0.0, away_adj: float = 0.0) -> tuple[float, float]:
        for t in (home, away):
            if t not in self.off:
                raise KeyError(f"Team ohne Daten: {t}")
        h = 0.0 if neutral else self.home_adv / 2
        return (self.base + h + self.off[home] - self.dfn[away] + home_adj,
                self.base - h + self.off[away] - self.dfn[home] + away_adj)

    def markets(self, home: str, away: str, spread: float | None = None,
                total: float | None = None, **kw) -> dict[str, float]:
        ph, pa = self.expected_points(home, away, **kw)
        mar = ph - pa
        out = {"pts_home": ph, "pts_away": pa, "margin": mar, "total": ph + pa}
        # Moneyline (Remis vernachlässigt; NFL-Ties < 0.5 %)
        out["ML1"] = _ncdf(mar / self.sigma_margin)
        out["ML2"] = 1 - out["ML1"]
        if spread is not None:  # Heim-Handicap, z. B. -3.5
            out[f"H1 {spread:+g}"] = _ncdf((mar + spread) / self.sigma_margin)
            out[f"H2 {-spread:+g}"] = 1 - out[f"H1 {spread:+g}"]
        if total is not None:
            out[f"O{total}"] = 1 - _ncdf((total - (ph + pa)) / self.sigma_total)
            out[f"U{total}"] = 1 - out[f"O{total}"]
        return out


def _ncdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
