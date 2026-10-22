"""Orbit-Börsenkurse (letzter Vorspiel-Tick) aus Neon sports.orbit_prices.

Wird lokal von tools/orbit_fixtures_export.py befüllt. Hier werden nur
Siegwetten inkl. Verlängerung (2-Weg-Märkte ohne Remis) an Eishockey-Spiele
gehängt; 60-Minuten-1X2 passt nicht zu den Modell-Wahrscheinlichkeiten und
bleibt bis zu einer eigenen Auswertung außen vor.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .. import matching
from ..selection import Offer
from .orbit_fixtures import _ts

COMMISSION = 0.03                 # Orbit-Kommission auf Nettogewinne
MAX_TICK_AGE = timedelta(hours=3)   # gemessen am letzten Crawler-Kontakt
MAX_SPREAD = 0.10                   # (Lay - Back) / Back; breiter = zu dünner Markt
MATCH_WINDOW = timedelta(hours=3)
_DRAW = {"the draw", "draw", "unentschieden", "x"}
_SKIP_TYPES = ("OVER", "UNDER", "HANDICAP", "TOTAL", "PERIOD", "BOTH")


def effective_odds(back: float, commission: float = COMMISSION) -> float:
    return 1.0 + (back - 1.0) * (1.0 - commission)


def _load():
    from sqlalchemy import text
    from ..sql_store import engine
    with engine().connect() as conn:
        fx = conn.execute(text(
            "SELECT event_id, home, away, start_utc FROM sports.orbit_fixtures")).mappings().all()
        px = conn.execute(text(
            "SELECT market_id, selection_id, event_id, market_type, runner, back, back_amount, "
            "lay, tick_ts, market_seen FROM sports.orbit_prices")).mappings().all()
    return fx, px


def _event_for(fixture, orbit_fx) -> str | None:
    gid = str(fixture.game.id)
    if gid.startswith("orbit:"):
        return gid.split(":", 1)[1]
    ko = fixture.game.kickoff
    home_al, away_al = fixture.game.home.aliases(), fixture.game.away.aliases()
    hits = [f["event_id"] for f in orbit_fx
            if (k := _ts(f["start_utc"])) and abs(k - ko) <= MATCH_WINDOW
            and matching.match_label(f["home"] or "", home_al)
            and matching.match_label(f["away"] or "", away_al)]
    return hits[0] if len(hits) == 1 else None


def _moneyline(rows, fixture):
    """Liefert {"home": row, "away": row} für einen 2-Weg-Siegmarkt, sonst None."""
    by_market: dict[str, list] = {}
    for r in rows:
        if any(s in str(r["market_type"] or "").upper() for s in _SKIP_TYPES):
            continue
        by_market.setdefault(r["market_id"], []).append(r)
    home_al, away_al = fixture.game.home.aliases(), fixture.game.away.aliases()
    for runners in by_market.values():
        if len(runners) != 2 or any(str(r["runner"] or "").strip().lower() in _DRAW for r in runners):
            continue
        side = {}
        for r in runners:
            name = r["runner"] or ""
            if matching.match_label(name, home_al):
                side["home"] = r
            elif matching.match_label(name, away_al):
                side["away"] = r
        if set(side) == {"home", "away"}:
            return side
    return None


def attach(fixtures, issues: list[str]) -> int:
    hockey = [f for f in fixtures if f.sport in ("hockey", "nhl") or f.league == "nhl"]
    if not hockey:
        return 0
    try:
        orbit_fx, prices = _load()
    except Exception as exc:
        issues.append(f"Orbit-Kurse nicht lesbar ({type(exc).__name__})")
        return 0
    now = datetime.now(timezone.utc)
    by_event: dict[str, list] = {}
    for p in prices:
        by_event.setdefault(str(p["event_id"]), []).append(p)
    attached = three_way_only = stale = thin = 0
    for fx in hockey:
        ev = _event_for(fx, orbit_fx)
        if not ev or ev not in by_event:
            continue
        ml = _moneyline(by_event[ev], fx)
        if ml is None:
            three_way_only += 1
            continue
        for side, r in ml.items():
            back, lay, ts = r["back"], r.get("lay"), _ts(r["tick_ts"])
            seen = max([t for t in (ts, _ts(r.get("market_seen"))) if t is not None], default=None)
            if not back or back <= 1.01 or ts is None:
                continue
            if seen is None or now - seen > MAX_TICK_AGE:
                stale += 1
                continue
            if not lay or (lay - back) / back > MAX_SPREAD:
                thin += 1
                continue
            team = fx.game.home.name if side == "home" else fx.game.away.name
            fx.offers.setdefault(side, []).append(Offer(
                event=fx.game.title, kickoff=fx.game.kickoff.isoformat(), market=side,
                selection=f"{team} Sieg (inkl. OT)", odds=round(effective_odds(float(back)), 4),
                source="orbit", observed_at=ts.isoformat(), liquidity=r["back_amount"],
                ref=f"orbit:{r['market_id']}:{r['selection_id']}", league=fx.league,
            ))
            attached += 1
    if stale:
        issues.append(f"Orbit: {stale} Kurse veraltet (Crawler länger als 3 Std. ohne Kontakt)")
    if thin:
        issues.append(f"Orbit: {thin} Kurse übersprungen, Back/Lay-Spanne über 10 %")
    if three_way_only:
        issues.append(f"Orbit: {three_way_only} Spiele nur mit 60-Min-1X2, noch nicht ausgewertet")
    return attached
