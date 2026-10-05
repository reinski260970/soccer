"""Preis-Mathematik: Vig entfernen, Edge/EV, Mindestquote, Einsatz in EH."""

from __future__ import annotations

import math


def implied(odds: float) -> float:
    return 1.0 / odds


def devig(odds: list[float], method: str = "power") -> list[float]:
    """Faire Marktwahrscheinlichkeiten aus Buchmacherquoten.

    power: p_i = (1/o_i)^k mit sum = 1 (berücksichtigt Favourite-Longshot-Bias).
    proportional: einfache Normierung.
    """
    raw = [1.0 / o for o in odds]
    if method == "proportional":
        s = sum(raw)
        return [r / s for r in raw]
    lo, hi = 0.5, 3.0
    for _ in range(100):
        k = (lo + hi) / 2
        s = sum(r ** k for r in raw)
        if s > 1:
            lo = k
        else:
            hi = k
    return [r ** k for r in raw]


def ev(p: float, odds: float) -> float:
    """Erwartungswert pro 1 Einheit Einsatz (dezimal)."""
    return p * odds - 1.0


def edge(p: float, odds: float) -> float:
    """Edge = eigene Wahrscheinlichkeit minus implizite Wahrscheinlichkeit."""
    return p - 1.0 / odds


def fair_odds(p: float) -> float:
    return math.inf if p <= 0 else 1.0 / p


def min_odds(p: float, min_ev: float = 0.03) -> float:
    """Kleinste Quote, bei der die Wette noch min_ev Erwartungswert hat."""
    return math.inf if p <= 0 else (1.0 + min_ev) / p


def kelly(p: float, odds: float) -> float:
    b = odds - 1.0
    return 0.0 if b <= 0 else max((b * p - (1 - p)) / b, 0.0)


def stake_units(p: float, odds: float, fraction: float = 0.25,
                bankroll_units: float = 100.0, cap_units: float = 2.0,
                uncertainty: float = 0.0) -> float:
    """Einsatz in EH (Einheiten, Bankroll = 100 EH).

    Fraktionelles Kelly; uncertainty (0..1) senkt die Wahrscheinlichkeit
    Richtung Marktpreis, bevor Kelly gerechnet wird (Schätzungsabschlag).
    Gerundet auf 0.25 EH, gedeckelt bei cap_units.
    """
    p_adj = p - uncertainty * (p - 1.0 / odds)
    units = kelly(p_adj, odds) * fraction * bankroll_units
    units = min(units, cap_units)
    return math.floor(units * 4) / 4
