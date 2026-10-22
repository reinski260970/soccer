"""Spielplan aus dem eigenen Orbit-Crawler (Neon-Tabelle sports.orbit_fixtures).

Die Tabelle wird lokal von tools/orbit_fixtures_export.py befüllt. Hier wird
nur gelesen; es sind reine Termine, keine Quoten.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

MAX_AGE = timedelta(hours=12)   # ältere Einträge gelten als veraltet


def _ts(v) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, str):
        v = datetime.fromisoformat(v)
    return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


def league_of(competition: str | None) -> str | None:
    c = (competition or "").lower()
    if re.search(r"\bdel\b", c) and not re.search(r"del\s*2", c):
        return "del"
    if "extraliga" in c and "slovak" not in c and "slowak" not in c:
        return "extraliga"
    if re.search(r"\bshl\b", c) or ("swed" in c and "allsvenskan" not in c):
        return "shl"
    if re.search(r"\bnhl\b", c):
        return "nhl"
    return None


def upcoming(league: str, start: datetime, until: datetime) -> tuple[list[dict], str | None]:
    """Spiele einer Liga im Fenster (start, until] als dicts mit id/start/home/away."""
    try:
        from sqlalchemy import text
        from ..sql_store import engine
        with engine().connect() as conn:
            rows = conn.execute(text(
                "SELECT event_id, competition, home, away, start_utc, seen_at "
                "FROM sports.orbit_fixtures WHERE start_utc > :s AND start_utc <= :u"
            ), {"s": start, "u": until}).mappings().all()
    except Exception as exc:
        return [], f"Orbit-Spielplan nicht lesbar ({type(exc).__name__})"
    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        if league_of(r["competition"]) != league:
            continue
        seen, ko = _ts(r["seen_at"]), _ts(r["start_utc"])
        if ko is None or (seen is not None and now - seen > MAX_AGE):
            continue
        out.append({"id": f"orbit:{r['event_id']}", "start": ko,
                    "home": r["home"], "away": r["away"]})
    return sorted(out, key=lambda g: g["start"]), None
