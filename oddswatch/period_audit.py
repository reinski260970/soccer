"""Coverage audit for quarter/half/period historical models."""

from __future__ import annotations

from datetime import date

from . import period_totals


TARGETS = (
    ("nba", "q1"),
    ("nba", "1h"),
    ("nfl", "q1"),
    ("nfl", "1h"),
    ("nhl", "p1"),
)


def run(as_of: date | None = None) -> list[str]:
    as_of = as_of or date.today()
    cache = {}
    out = [f"PERIOD MODEL AUDIT · {as_of.isoformat()}"]
    for sport, period in TARGETS:
        games, issues = period_totals.history(sport, period, as_of, cache)
        teams = {g.home for g in games} | {g.away for g in games}
        avg = (
            sum(g.home_pts + g.away_pts for g in games) / len(games)
            if games else 0.0
        )
        out.append(
            f"{sport.upper()} {period}: {len(games)} games · "
            f"{len(teams)} teams · avg total {avg:.2f} · issues {len(issues)}"
        )
        for issue in issues[:3]:
            out.append(f"  - {issue}")
    return out


if __name__ == "__main__":
    for line in run():
        print(line)
