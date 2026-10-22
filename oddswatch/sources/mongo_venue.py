"""Heim-/Auswärtsstärke für SWE/NOR/DEN – football-data.co.uk direkt, Mongo als Ersatz.

Primär: die aktuellen CSVs von football-data.co.uk (new/SWE.csv usw.); aus dieser
Quelle stammt auch der Mongo-Bestand, ist dort aber nicht aktuell. Ersatz: die
eigene Fußball-Mongo (euro_football.extra_leagues).

Ersatz für SoccerSTATS (dort inzwischen Cloudflare-Sperre). Gerechnet wird je Team
über die laufende Saison: Spiele, Tore/Gegentore pro Spiel und Punkte pro Spiel,
getrennt nach Heim und Auswärts. Gelesen wird nur; Secret MONGO_SOCCER.

Hinweis zur Datenqualität: Das Datumsfeld in extra_leagues hat bei Tagen <= 12
Tag und Monat vertauscht. Deshalb wird über das Feld Season gefiltert, nicht über Date.
"""
from __future__ import annotations

import os
from datetime import date

from .soccerstats import TeamVenuePrior

# Liga-Code im Scan -> (Country, League, Saisonformat)
LEAGUES = {
    "SWE": ("Sweden", "Allsvenskan", "calendar"),
    "NOR": ("Norway", "Eliteserien", "calendar"),
    "DEN": ("Denmark", "Superliga", "split"),
}
FD_FILES = {"SWE": "SWE", "NOR": "NOR", "DEN": "DNK"}
FD_URL = "https://www.football-data.co.uk/new/{}.csv"
MIN_GAMES = 3


def season_label(fmt: str, today: date | None = None) -> str:
    today = today or date.today()
    if fmt == "calendar":
        return str(today.year)
    start = today.year if today.month >= 7 else today.year - 1
    return f"{start}/{start + 1}"


def _uri() -> str:
    return (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGODB_URI") or "").strip().strip("'\"")


def aggregate(rows: list[dict]) -> list[TeamVenuePrior]:
    home: dict[str, list] = {}
    away: dict[str, list] = {}
    for r in rows:
        try:
            hg, ag = int(r["HG"]), int(r["AG"])
        except (KeyError, TypeError, ValueError):
            continue
        h, a = str(r.get("Home") or "").strip(), str(r.get("Away") or "").strip()
        if not h or not a:
            continue
        hp = 3 if hg > ag else 1 if hg == ag else 0
        ap = 3 if ag > hg else 1 if hg == ag else 0
        home.setdefault(h, []).append((hg, ag, hp))
        away.setdefault(a, []).append((ag, hg, ap))
    out = []
    for team in sorted(set(home) | set(away)):
        hs, as_ = home.get(team, []), away.get(team, [])
        if len(hs) < MIN_GAMES or len(as_) < MIN_GAMES:
            continue
        def avg(xs, i):
            return sum(x[i] for x in xs) / len(xs)
        out.append(TeamVenuePrior(team, len(hs), avg(hs, 0), avg(hs, 1), avg(hs, 2),
                                  len(as_), avg(as_, 0), avg(as_, 1), avg(as_, 2), source="mongo"))
    return out


def from_football_data(code: str) -> tuple[list[TeamVenuePrior], str | None]:
    from .. import fetch
    from .football_data import parse_new_league
    spec = LEAGUES.get(code)
    if not spec or code not in FD_FILES:
        return [], f"football-data: Liga {code} nicht gemappt"
    season = season_label(spec[2])
    text, err = fetch.get(FD_URL.format(FD_FILES[code]), cache_days=0.25)
    if err or not text:
        return [], f"football-data {code}: {err or 'leer'}"
    matches, _ = parse_new_league(text, {season})
    rows = [{"Home": m.home, "Away": m.away, "HG": m.home_goals, "AG": m.away_goals} for m in matches]
    priors = [p.__class__(**{**p.__dict__, "source": "football-data"}) for p in aggregate(rows)]
    return (priors, None) if priors else ([], f"football-data {code}: keine Saison {season}")


def team_homeaway(code: str) -> tuple[list[TeamVenuePrior], str | None]:
    priors, err = from_football_data(code)
    if priors:
        return priors, None
    rows, merr = from_mongo(code)
    return (rows, None) if rows else ([], f"{err}; {merr}")


def from_mongo(code: str) -> tuple[list[TeamVenuePrior], str | None]:
    spec = LEAGUES.get(code)
    if not spec:
        return [], f"Mongo-Venue: Liga {code} nicht gemappt"
    uri = _uri()
    if not uri.startswith("mongodb"):
        return [], "Mongo-Venue: MONGO_SOCCER nicht gesetzt"
    country, league, fmt = spec
    season = season_label(fmt)
    try:
        from pymongo import MongoClient
        with MongoClient(uri, serverSelectionTimeoutMS=15000, appname="oddswatch-venue-readonly") as c:
            try:
                db = c.get_default_database()
            except Exception:
                db = None
            if db is None:
                db = c["euro_football"]
            rows = list(db["extra_leagues"].find(
                {"Country": {"$in": [country, country + " "]}, "League": league,
                 "Season": {"$in": [season, int(season) if season.isdigit() else season]}},
                {"_id": 0, "Home": 1, "Away": 1, "HG": 1, "AG": 1},
            ).max_time_ms(20000))
    except Exception as exc:
        return [], f"Mongo-Venue {code}: {type(exc).__name__}"
    priors = aggregate(rows)
    if not priors:
        return [], f"Mongo-Venue {code}: keine Saison {season} mit genug Spielen"
    return priors, None
