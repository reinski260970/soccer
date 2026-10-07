"""Unified external xG snapshots for football.

Provider order:
1. Understat for supported Top-5 leagues.
2. FootyStats for broad league coverage.
3. Caller may fall back to the local shots/SoT proxy, but this module never
   fabricates xG values.

Returned snapshots are strictly pre-match when as_of is supplied.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from . import footystats, understat


@dataclass
class XGSnapshot:
    team: str
    xg: float
    xga: float
    xg_home: float | None
    xga_home: float | None
    xg_away: float | None
    xga_away: float | None
    matches: int
    source: str


def _season_year(dt: datetime) -> int:
    return dt.year if dt.month >= 7 else dt.year - 1


def _understat_snapshot(code: str, as_of: datetime) -> tuple[list[XGSnapshot], str | None]:
    if code not in understat.LEAGUES:
        return [], f"Understat: Liga {code} nicht unterstützt"
    year = _season_year(as_of)
    rows, err = understat.season_matches(code, year, cache_days=0.25)
    if not rows:
        return [], err or f"Understat {code}/{year}: keine Daten"

    st = defaultdict(lambda: {
        "n": 0, "xf": 0.0, "xa": 0.0,
        "hn": 0, "hxf": 0.0, "hxa": 0.0,
        "an": 0, "axf": 0.0, "axa": 0.0,
    })
    cutoff = as_of.astimezone(timezone.utc).date()
    for m in rows:
        if m.date >= cutoff or m.home_xg is None or m.away_xg is None:
            continue
        h, a = st[m.home], st[m.away]
        hx, ax = float(m.home_xg), float(m.away_xg)

        h["n"] += 1; h["xf"] += hx; h["xa"] += ax
        h["hn"] += 1; h["hxf"] += hx; h["hxa"] += ax

        a["n"] += 1; a["xf"] += ax; a["xa"] += hx
        a["an"] += 1; a["axf"] += ax; a["axa"] += hx

    out = []
    for team, s in st.items():
        if s["n"] <= 0:
            continue
        out.append(XGSnapshot(
            team=team,
            xg=s["xf"] / s["n"],
            xga=s["xa"] / s["n"],
            xg_home=(s["hxf"] / s["hn"]) if s["hn"] else None,
            xga_home=(s["hxa"] / s["hn"]) if s["hn"] else None,
            xg_away=(s["axf"] / s["an"]) if s["an"] else None,
            xga_away=(s["axa"] / s["an"]) if s["an"] else None,
            matches=s["n"],
            source="understat",
        ))
    if not out:
        return [], f"Understat {code}/{year}: kein Pre-Match-xG vor {cutoff}"
    return out, None


def snapshot(code: str, as_of: datetime) -> tuple[list[XGSnapshot], str | None]:
    """Return the best real-xG source available for a league and time."""
    us, uerr = _understat_snapshot(code, as_of)
    if us:
        return us, None

    year = _season_year(as_of)
    fs, ferr = footystats.team_xg(code, year, as_of=as_of)
    if fs:
        return [
            XGSnapshot(
                team=r.team,
                xg=float(r.xg),
                xga=float(r.xga),
                xg_home=r.xg_home,
                xga_home=r.xga_home,
                xg_away=r.xg_away,
                xga_away=r.xga_away,
                matches=0,
                source="footystats",
            )
            for r in fs
            if r.xg is not None and r.xga is not None
        ], None

    return [], ferr or uerr or f"xG: keine Quelle für {code}"
