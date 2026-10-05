"""Verknüpft football-data Spiele/Quoten mit echtem Understat Match-xG."""

from __future__ import annotations

from datetime import timedelta

from .. import matching
from ..models.poisson import Match


def merge_xg(fd_matches: list[Match], us_matches: list[Match]) -> tuple[list[Match], dict]:
    """Behalte football-data Teamnamen/Resultate, ergänze Understat-xG.

    Matcht Datum (±1 Tag als Zeitzonen-Fallback) und beide Teams. Nur eindeutige
    Treffer werden übernommen; keine geratenen xG-Werte.
    """
    by_day: dict = {}
    for u in us_matches:
        by_day.setdefault(u.date, []).append(u)

    out: list[Match] = []
    matched = ambiguous = 0
    misses: list[str] = []
    for m in fd_matches:
        candidates = []
        for d in (m.date, m.date - timedelta(days=1), m.date + timedelta(days=1)):
            for u in by_day.get(d, []):
                if matching.same(m.home, u.home) and matching.same(m.away, u.away):
                    candidates.append(u)
        # Dedupe same Understat match if date loops somehow overlap.
        uniq = {(u.date, u.home, u.away): u for u in candidates}
        candidates = list(uniq.values())
        if len(candidates) == 1:
            u = candidates[0]
            out.append(Match(m.date, m.home, m.away, m.home_goals, m.away_goals,
                             u.home_xg, u.away_xg))
            matched += 1
        else:
            out.append(Match(m.date, m.home, m.away, m.home_goals, m.away_goals))
            if len(candidates) > 1:
                ambiguous += 1
            elif len(misses) < 25:
                misses.append(f"{m.date} {m.home} - {m.away}")

    return out, {
        "total": len(fd_matches),
        "matched": matched,
        "coverage": matched / len(fd_matches) if fd_matches else 0.0,
        "ambiguous": ambiguous,
        "misses": misses,
    }
