"""Tor-Modell für Fußball und Eishockey.

Maher/Dixon-Coles-Poisson: log(lambda_heim) = mu + home + att_h - def_a,
log(lambda_aus) = mu + att_a - def_h. Fit per Maximum Likelihood
(Newton-Schritte je Parameter), mit exponentiellem Zeitverfall und
optionaler Mischung aus Toren und xG (Fußball) bzw. 5v5-xG (Hockey).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Match:
    date: date
    home: str
    away: str
    home_goals: float
    away_goals: float
    home_xg: float | None = None
    away_xg: float | None = None


@dataclass
class PoissonModel:
    mu: float = 0.3
    home_adv: float = 0.25
    attack: dict[str, float] = field(default_factory=dict)
    defence: dict[str, float] = field(default_factory=dict)
    games: dict[str, float] = field(default_factory=dict)
    rho: float = -0.05  # Dixon-Coles Low-Score-Korrektur (nur Fußball sinnvoll)
    max_goals: int = 10

    # ------------------------------------------------------------------ fit
    @classmethod
    def fit(
        cls,
        matches: list[Match],
        as_of: date,
        half_life_days: float = 180.0,
        xg_weight: float = 0.5,
        shrink: float = 2.0,
        iterations: int = 200,
        rho: float = -0.05,
        max_goals: int = 10,
    ) -> "PoissonModel":
        """Gewichteter MLE-Fit.

        xg_weight: Anteil xG an der Zielgröße (0 = nur Tore). Fehlt xG für ein
        Spiel, werden dort nur Tore genutzt.
        shrink: Ridge-Strafe (in "Pseudo-Spielen") Richtung Ligaschnitt, damit
        Teams mit wenigen Spielen nicht extrem geschätzt werden.
        """
        if not matches:
            raise ValueError("keine Spiele zum Fitten")
        rows = []
        for m in matches:
            age = (as_of - m.date).days
            if age < 0:
                continue
            w = 0.5 ** (age / half_life_days)
            hg, ag = m.home_goals, m.away_goals
            if m.home_xg is not None and m.away_xg is not None and xg_weight > 0:
                hg = (1 - xg_weight) * hg + xg_weight * m.home_xg
                ag = (1 - xg_weight) * ag + xg_weight * m.away_xg
            rows.append((m.home, m.away, hg, ag, w))
        if not rows:
            raise ValueError("keine Spiele vor dem Stichtag")

        teams = sorted({r[0] for r in rows} | {r[1] for r in rows})
        att = {t: 0.0 for t in teams}
        dfn = {t: 0.0 for t in teams}
        games = {t: 0.0 for t in teams}
        for h, a, _, _, w in rows:
            games[h] += w
            games[a] += w
        tot_w = sum(r[4] for r in rows)
        mean_goals = sum((r[2] + r[3]) * r[4] for r in rows) / (2 * tot_w)
        mu = math.log(max(mean_goals, 0.05))
        home = 0.2

        # Jede Tor-Beobachtung als (Angreifer, Verteidiger, ist_heim, tore, w).
        obs = []
        for h, a, hg, ag, w in rows:
            obs.append((h, a, 1.0, hg, w))
            obs.append((a, h, 0.0, ag, w))
        by_att: dict[str, list] = {t: [] for t in teams}
        by_def: dict[str, list] = {t: [] for t in teams}
        for o in obs:
            by_att[o[0]].append(o)
            by_def[o[1]].append(o)

        def lam(o) -> float:
            return math.exp(mu + home * o[2] + att[o[0]] - dfn[o[1]])

        def sums(os_) -> tuple[float, float]:
            y = sum(o[4] * o[3] for o in os_)
            m = sum(o[4] * lam(o) for o in os_)
            return y, m

        home_obs = [o for o in obs if o[2]]
        for _ in range(iterations):
            # Gauss-Seidel: jeder Parameter wird mit frisch berechneten
            # Residuen aktualisiert (gekoppelte Parameter überkorrigieren
            # sonst gemeinsam und divergieren).
            y, m = sums(obs)
            d_mu = math.log(y / m)
            mu += d_mu
            y, m = sums(home_obs)
            d_home = math.log(y / m) if y > 0 else 0.0
            home += d_home
            step = max(abs(d_mu), abs(d_home))
            for t in teams:
                # Newton-Schritt mit Ridge-Strafe, gedämpft auf |Schritt| <= 1
                y, m = sums(by_att[t])
                da = (y - m - shrink * att[t]) / (m + shrink)
                da = max(-1.0, min(1.0, da))
                att[t] += da
                y, m = sums(by_def[t])
                dd = (m - y - shrink * dfn[t]) / (m + shrink)
                dd = max(-1.0, min(1.0, dd))
                dfn[t] += dd
                step = max(step, abs(da), abs(dd))
            # Identifizierbarkeit: Stärken um 0 zentrieren
            ma = sum(att.values()) / len(teams)
            md = sum(dfn.values()) / len(teams)
            for t in teams:
                att[t] -= ma
                dfn[t] -= md
            mu += ma - md
            if step < 1e-7:
                break
        return cls(mu=mu, home_adv=home, attack=att, defence=dfn, games=games,
                   rho=rho, max_goals=max_goals)

    # ------------------------------------------------------------ predict
    def expected_goals(self, home: str, away: str, neutral: bool = False,
                       home_adj: float = 0.0, away_adj: float = 0.0) -> tuple[float, float]:
        """Erwartete Tore. *_adj: manuelle log-Anpassung (Ausfälle, Belastung)."""
        for t in (home, away):
            if t not in self.attack:
                raise KeyError(f"Team ohne Daten: {t}")
        ha = 0.0 if neutral else self.home_adv
        lh = math.exp(self.mu + ha + self.attack[home] - self.defence[away] + home_adj)
        la = math.exp(self.mu + self.attack[away] - self.defence[home] + away_adj)
        return lh, la

    def score_matrix(self, lh: float, la: float) -> list[list[float]]:
        n = self.max_goals + 1
        ph = [_pois(k, lh) for k in range(n)]
        pa = [_pois(k, la) for k in range(n)]
        m = [[ph[i] * pa[j] for j in range(n)] for i in range(n)]
        r = self.rho
        if r:
            m[0][0] *= 1 - lh * la * r
            m[0][1] *= 1 + lh * r
            m[1][0] *= 1 + la * r
            m[1][1] *= 1 - r
        s = sum(map(sum, m))
        return [[x / s for x in row] for row in m]

    def markets(self, home: str, away: str, **kw) -> dict[str, float]:
        lh, la = self.expected_goals(home, away, **kw)
        return markets_from_matrix(self.score_matrix(lh, la), lh, la)


def markets_from_matrix(m: list[list[float]], lh: float, la: float) -> dict[str, float]:
    n = len(m)
    out: dict[str, float] = {"xg_home": lh, "xg_away": la}
    out["1"] = sum(m[i][j] for i in range(n) for j in range(n) if i > j)
    out["X"] = sum(m[i][i] for i in range(n))
    out["2"] = sum(m[i][j] for i in range(n) for j in range(n) if i < j)
    for line in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5):
        over = sum(m[i][j] for i in range(n) for j in range(n) if i + j > line)
        out[f"O{line}"] = over
        out[f"U{line}"] = 1 - over
    out["BTTS_Y"] = sum(m[i][j] for i in range(1, n) for j in range(1, n))
    out["BTTS_N"] = 1 - out["BTTS_Y"]
    out["1X"] = out["1"] + out["X"]
    out["X2"] = out["X"] + out["2"]
    # Draw-no-bet (bedingt auf kein Remis)
    nd = out["1"] + out["2"]
    out["DNB1"] = out["1"] / nd
    out["DNB2"] = out["2"] / nd
    return out


def hockey_regulation_to_moneyline(p1: float, px: float, p2: float) -> tuple[float, float]:
    """60-Minuten-1X2 -> Sieger inkl. OT/SO. Remis wird ~50/50 aufgeteilt,
    leicht zum stärkeren Team verschoben (Schätzung, gekennzeichnet)."""
    share = 0.5 + 0.25 * (p1 - p2)
    share = min(max(share, 0.35), 0.65)
    return p1 + px * share, p2 + px * (1 - share)


def _pois(k: int, lam: float) -> float:
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1)) if lam > 0 else float(k == 0)
