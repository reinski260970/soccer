"""World Football Elo Ratings (eloratings.net): Nationalmannschaften.

Dateien (Tab-getrennt, ohne Kopfzeile):
  World.tsv           Rang, Rang, Code, Elo, ...            (aktuelle Wertung)
  en.teams.tsv        Code, Name, Namensvarianten ...
  <Jahr>_results.tsv  J, M, T, Heim, Gast, Tore H, Tore G, Wettbewerb, Spielort,
                      Elo-Änderung (Heim-Sicht), Elo H nachher, Elo G nachher, ...
Spielort leer = Land des Heimteams; sonst Ländercode des Austragungsorts.
Minuszeichen kommen teils als U+2212.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .. import matching

BASE = "https://www.eloratings.net"
RATINGS_URL = f"{BASE}/World.tsv"
TEAMS_URL = f"{BASE}/en.teams.tsv"
# ESPN-/Kalshi-Schreibweisen, die in en.teams.tsv fehlen
EXTRA_NAMES = {"Türkiye": "TR", "Turkiye": "TR", "Republic of Ireland": "IE",
               "Bosnia-Herzegovina": "BA", "Czech Republic": "CZ", "IR Iran": "IR",
               "Korea Republic": "KR", "USA": "US", "Cabo Verde": "CV"}


def results_url(year: int) -> str:
    return f"{BASE}/{year}_results.tsv"


@dataclass
class EloResult:
    date: date
    home: str          # Ländercode
    away: str
    home_goals: int
    away_goals: int
    tournament: str
    venue: str         # Code des Austragungslands ("" = Heimteam)
    elo_home: float    # vor dem Spiel
    elo_away: float

    @property
    def home_edge(self) -> int:
        """+1 Heimspiel, -1 Gast spielt zu Hause, 0 neutral."""
        if self.venue in ("", self.home):
            return 1
        return -1 if self.venue == self.away else 0


def _int(s: str) -> int:
    return int(s.strip().replace("−", "-").replace("+", ""))


def parse_ratings(text: str) -> dict[str, float]:
    out = {}
    for line in text.splitlines():
        p = line.split("\t")
        if len(p) > 3 and p[2]:
            try:
                out[p[2]] = float(_int(p[3]))
            except ValueError:
                continue
    return out


def parse_teams(text: str) -> dict[str, list[str]]:
    out = {}
    for line in text.splitlines():
        p = [x for x in line.split("\t") if x]
        if len(p) >= 2:
            out[p[0]] = p[1:]
    return out


def parse_results(text: str) -> list[EloResult]:
    out = []
    for line in text.splitlines():
        p = line.split("\t")
        if len(p) < 12:
            continue
        try:
            d = date(int(p[0]), int(p[1]), int(p[2]))
            ch, rh, ra = _int(p[9]), _int(p[10]), _int(p[11])
            out.append(EloResult(d, p[3], p[4], _int(p[5]), _int(p[6]), p[7], p[8].strip(),
                                 float(rh - ch), float(ra + ch)))
        except ValueError:
            continue
    return out


def code_for(name: str, teams: dict[str, list[str]]) -> str | None:
    if name in EXTRA_NAMES:
        return EXTRA_NAMES[name]
    n = matching.norm(name)
    hits = {c for c, names in teams.items() for x in names if matching.norm(x) == n}
    return hits.pop() if len(hits) == 1 else None
