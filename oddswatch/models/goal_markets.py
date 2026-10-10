"""Score-distribution soccer prices and exact fractional Asian settlements.

Independent of bookmakers: bookmaker odds must NEVER enter probabilities.
All prices are decimal; research/release decisions live outside this module.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .poisson import PoissonModel, markets_from_matrix


@dataclass(frozen=True)
class AsianPrice:
    """Probabilistic stake-weighted fractions, including quarter-line half bets."""
    win_fraction: float
    lose_fraction: float
    push_fraction: float

    @property
    def fair_odds(self) -> float:
        if self.win_fraction <= 0:
            return math.inf
        return 1.0 + self.lose_fraction / self.win_fraction

    def ev(self, odds: float) -> float:
        if not math.isfinite(odds) or odds <= 1.0:
            raise ValueError("positive decimal odds > 1 required")
        return self.win_fraction * (odds - 1.0) - self.lose_fraction


def _lines(line: float) -> tuple[float, ...]:
    """Quarter Asian line is two equal half-stakes at surrounding half-lines."""
    if not math.isfinite(line) or abs(line) > 15:
        raise ValueError("invalid Asian line")
    quarters = round(float(line) * 4)
    if abs(quarters / 4 - line) > 1e-9:
        raise ValueError("Asian lines must have quarter-goal increments")
    if quarters % 2:
        return ((quarters - 1) / 4, (quarters + 1) / 4)
    return (quarters / 4,)


def _score_fraction(score: float) -> tuple[float, float, float]:
    if score > 1e-9:
        return 1.0, 0.0, 0.0
    if score < -1e-9:
        return 0.0, 1.0, 0.0
    return 0.0, 0.0, 1.0


def asian_probability(
    matrix: list[list[float]],
    *,
    kind: str,
    selection: str,
    line: float,
) -> AsianPrice:
    """Cash-flow probabilities for O/U and Asian Handicap incl. quarter lines.

    Kind: "total" with selection OVER/UNDER; or "asian_handicap" with
    HOME/AWAY. For AH, line is *the selected side's* goal handicap.
    """
    if kind not in {"total", "asian_handicap"}:
        raise ValueError("unsupported market kind")
    if (kind == "total" and selection not in {"OVER", "UNDER"}) or (
        kind == "asian_handicap" and selection not in {"HOME", "AWAY"}
    ):
        raise ValueError("unsupported selection")
    split = _lines(float(line))
    if kind == "total" and line < 0:
        raise ValueError("total must be nonnegative")
    n = len(matrix)
    if not n or any(len(row) != n for row in matrix):
        raise ValueError("square score matrix required")
    total_mass = sum(sum(r) for r in matrix)
    if not math.isfinite(total_mass) or total_mass <= 0:
        raise ValueError("invalid score matrix mass")
    win = lose = push = 0.0
    for h, row in enumerate(matrix):
        for a, probability in enumerate(row):
            if probability < 0 or not math.isfinite(probability):
                raise ValueError("invalid score probability")
            stake = probability / (total_mass * len(split))
            for half_line in split:
                if kind == "total":
                    v = h + a - half_line
                    if selection == "UNDER":
                        v = -v
                else:
                    v = h - a if selection == "HOME" else a - h
                    v += half_line
                w, l, p = _score_fraction(v)
                win += stake * w
                lose += stake * l
                push += stake * p
    return AsianPrice(win, lose, push)


def goal_markets(
    expected_home: float,
    expected_away: float,
    *,
    rho: float = -0.05,
    max_goals: int = 12,
) -> tuple[list[list[float]], dict[str, float]]:
    """Consistent 1X2, goal totals and BTTS from one score distribution."""
    if any(not math.isfinite(v) or v <= 0 or v > 8
           for v in (expected_home, expected_away)):
        raise ValueError("expected goals must be finite and within (0,8]")
    if abs(rho) > 0.20:
        raise ValueError("low-score rho outside calibrated research bounds")
    if max_goals < 8:
        raise ValueError("score grid must cover at least goals 0..8")
    model = PoissonModel(rho=rho, max_goals=max_goals)
    matrix = model.score_matrix(expected_home, expected_away)
    markets = markets_from_matrix(matrix, expected_home, expected_away)
    return matrix, markets
