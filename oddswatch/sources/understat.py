"""Understat: echtes Match-xG für Europas Top-5-Ligen.

Öffentliche JSON-Endpunkte:
  https://understat.com/getLeagueData/{league}/{season}

Abdeckung: EPL, Bundesliga, La Liga, Serie A, Ligue 1.
Keine Marktquoten; ausschließlich Modell-Features.
"""

from __future__ import annotations

from datetime import datetime

from .. import fetch
from ..models.poisson import Match

BASE = "https://understat.com"
LEAGUES = {
    "E0": "EPL",
    "D1": "Bundesliga",
    "SP1": "La_Liga",
    "I1": "Serie_A",
    "F1": "Ligue_1",
}


def season_matches(code: str, season: int, cache_days: float = 30.0) -> tuple[list[Match], str | None]:
    league = LEAGUES.get(code)
    if not league:
        return [], f"Understat: Liga {code} nicht unterstützt"
    url = f"{BASE}/getLeagueData/{league}/{season}"
    data, err = fetch.get_json(
        url,
        cache_days=cache_days,
        headers={
            "Referer": f"{BASE}/league/{league}/{season}",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    if data is None:
        return [], err or f"Understat {league} {season}: keine Daten"

    out: list[Match] = []
    for r in data.get("dates", []):
        if not r.get("isResult"):
            continue
        try:
            d = datetime.strptime(r["datetime"].split()[0], "%Y-%m-%d").date()
            h = r["h"]["title"]
            a = r["a"]["title"]
            hg = float(r["goals"]["h"])
            ag = float(r["goals"]["a"])
            hx = float(r["xG"]["h"])
            ax = float(r["xG"]["a"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append(Match(d, h, a, hg, ag, hx, ax))

    out.sort(key=lambda m: m.date)
    if not out:
        return [], f"Understat {league} {season}: keine abgeschlossenen Spiele geparst"
    return out, None
