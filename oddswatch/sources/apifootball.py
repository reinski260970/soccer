"""API-Football (api-sports.io): Buchmacherquoten Pinnacle, Bet365, Betfair.

Nur Fußball. Schlüssel aus der Umgebungsvariable APIKEY (alternativ
API_FOOTBALL_KEY oder API_KEY). Ein Abruf je Spieltag (Spielplan) und je
Spiel (alle Buchmacher auf einmal); Kontingent Pro: 7.500 Anfragen/Tag.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from .. import fetch, matching

BASE = "https://v3.football.api-sports.io"
BOOKMAKERS = {4: "Pinnacle", 8: "Bet365", 3: "Betfair"}


def api_key() -> str:
    for name in ("APIKEY", "API_FOOTBALL_KEY", "API_KEY"):
        k = (os.environ.get(name) or "").strip()
        if k:
            return k
    return ""


def _get(path: str) -> tuple[dict | None, str | None]:
    key = api_key()
    if not key:
        return None, "API-Football: APIKEY nicht gesetzt"
    data, err = fetch.get_json(BASE + path, headers={"x-apisports-key": key}, retries=1)
    if err:
        # Fehlermeldung ohne Schlüssel (steht ohnehin nur im Header)
        return None, f"API-Football {path}: {err.split(': ', 1)[-1]}"
    errs = data.get("errors") if isinstance(data, dict) else None
    if errs:
        return None, f"API-Football {path}: {errs}"
    return data, None


@dataclass
class ApiFixture:
    id: int
    kickoff: datetime
    home: str
    away: str
    league: str


def fixtures_on(day: str) -> tuple[list[ApiFixture], str | None]:
    """Alle Spiele eines Tages (YYYY-MM-DD, UTC)."""
    data, err = _get(f"/fixtures?date={day}&timezone=UTC")
    if data is None:
        return [], err
    out = []
    for f in data.get("response") or []:
        try:
            out.append(ApiFixture(int(f["fixture"]["id"]), datetime.fromisoformat(f["fixture"]["date"]),
                                  f["teams"]["home"]["name"], f["teams"]["away"]["name"],
                                  f["league"]["name"]))
        except (KeyError, TypeError, ValueError):
            continue
    return out, None


def _hit(name: str, aliases: list[str]) -> bool:
    return any(matching.norm(name) == matching.norm(a) or matching.same(name, a) for a in aliases if a)


def find_fixture(fixtures: list[ApiFixture], home: list[str], away: list[str],
                 kickoff: datetime, tolerance: timedelta = timedelta(minutes=90)) -> ApiFixture | None:
    """Spiel mit passendem Anstoß (±90 Min., schließt U19/U21 zu anderer Zeit aus)
    und beiden Teams; nur bei genau einem Treffer."""
    hits = [f for f in fixtures if abs(f.kickoff - kickoff) <= tolerance
            and _hit(f.home, home) and _hit(f.away, away)]
    return hits[0] if len(hits) == 1 else None


def _key(bet: str, value: str) -> str | None:
    if bet == "Match Winner":
        return {"Home": "home", "Draw": "draw", "Away": "away"}.get(value)
    if bet == "Goals Over/Under":
        side, _, line = value.partition(" ")
        try:
            L = float(line)
        except ValueError:
            return None
        return {"Over": f"O{L:g}", "Under": f"U{L:g}:no"}.get(side)
    return None


def parse_odds(data: dict) -> dict[str, dict[str, float]]:
    """{Buchmacher: {Markt: Quote}} für 1X2 und Über/Unter (Schlüssel wie im Journal)."""
    out: dict[str, dict[str, float]] = {}
    for r in data.get("response") or []:
        for b in r.get("bookmakers") or []:
            name = BOOKMAKERS.get(b.get("id"))
            if not name:
                continue
            mk = out.setdefault(name, {})
            for bet in b.get("bets") or []:
                for v in bet.get("values") or []:
                    k = _key(bet.get("name", ""), str(v.get("value", "")))
                    try:
                        o = float(v.get("odd"))
                    except (TypeError, ValueError):
                        continue
                    if k and o > 1.0:
                        mk[k] = o
    return out


def odds(fixture_id: int) -> tuple[dict[str, dict[str, float]], str | None]:
    data, err = _get(f"/odds?fixture={fixture_id}")
    if data is None:
        return {}, err
    return parse_odds(data), None
