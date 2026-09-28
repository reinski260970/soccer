"""football-data.co.uk: Ergebnisse, Schüsse und bet365-Quoten (inkl. Closing).

CSV-URL-Schema: https://www.football-data.co.uk/mmz4281/<YYYY>/<LIGA>.csv
(YYYY = 2627 für 2026/27; D1 = Bundesliga, D2 = 2. BL, A1 fehlt dort ->
Österreich über new/AUT.csv). Nutzt keine Netzwerk-Library, damit Tests
offline laufen; das Laden übernimmt oddswatch.fetch.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime

from ..models.poisson import Match

BASE = "https://www.football-data.co.uk/mmz4281"
LEAGUES = {"D1": "Bundesliga", "D2": "2. Bundesliga", "E0": "Premier League",
           "SP1": "La Liga", "I1": "Serie A", "F1": "Ligue 1"}


def season_code(start_year: int) -> str:
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def csv_url(league: str, start_year: int) -> str:
    return f"{BASE}/{season_code(start_year)}/{league}.csv"


@dataclass
class OddsRow:
    date: date
    home: str
    away: str
    b365: tuple[float, float, float] | None
    b365_closing: tuple[float, float, float] | None
    b365_ou25: tuple[float, float] | None
    b365_ou25_closing: tuple[float, float] | None


def _d(s: str) -> date:
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unbekanntes Datum: {s!r}")


def _f(row: dict, *keys: str) -> tuple[float, ...] | None:
    try:
        vals = tuple(float(row[k]) for k in keys)
    except (KeyError, ValueError, TypeError):
        return None
    return vals if all(v > 1.0 for v in vals) else None


def parse(text: str, shots_as_xg: bool = False) -> tuple[list[Match], list[OddsRow]]:
    """Liest eine football-data-CSV.

    shots_as_xg: Ersatz-xG aus Schüssen aufs Tor (0.30 je SoT + 0.03 je
    Schuss daneben). Nur Notlösung, wenn keine echten xG vorliegen – wird im
    Bericht als Schätzung gekennzeichnet.
    """
    matches, odds = [], []
    for row in csv.DictReader(io.StringIO(text.lstrip("﻿"))):
        if not row.get("HomeTeam") or not row.get("Date"):
            continue
        d = _d(row["Date"])
        hg, ag = row.get("FTHG", ""), row.get("FTAG", "")
        if hg not in ("", None) and ag not in ("", None):
            hx = ax = None
            if shots_as_xg:
                try:
                    hst, ast = float(row["HST"]), float(row["AST"])
                    hs, as_ = float(row["HS"]), float(row["AS"])
                    hx = 0.30 * hst + 0.03 * max(hs - hst, 0)
                    ax = 0.30 * ast + 0.03 * max(as_ - ast, 0)
                except (KeyError, ValueError):
                    pass
            matches.append(Match(d, row["HomeTeam"], row["AwayTeam"],
                                 float(hg), float(ag), hx, ax))
        odds.append(OddsRow(
            d, row["HomeTeam"], row["AwayTeam"],
            _f(row, "B365H", "B365D", "B365A"),
            _f(row, "B365CH", "B365CD", "B365CA"),
            _f(row, "B365>2.5", "B365<2.5"),
            _f(row, "B365C>2.5", "B365C<2.5"),
        ))
    return matches, odds
