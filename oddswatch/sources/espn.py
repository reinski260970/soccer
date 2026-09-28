"""ESPN Site-API: Spielpläne, Ergebnisse, Verletzungen, Referenzlinien.

Scoreboard: https://site.api.espn.com/apis/site/v2/sports/<sport>/<liga>/scoreboard
  ?dates=YYYYMMDD                        (ein Tag; Datumsbereiche liefern 400)
  ?dates=<Jahr>&seasontype=2&week=<n>    (NFL-Woche)
Die Quoten in der Antwort stammen von DraftKings – sie dienen nur als
Marktreferenz, nicht als spielbarer bet365-/Orbit-Preis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .. import fetch

SITE = "https://site.api.espn.com/apis/site/v2/sports"

PATHS = {
    "bundesliga": "soccer/ger.1", "2bundesliga": "soccer/ger.2",
    "austria": "soccer/aut.1", "ucl": "soccer/uefa.champions",
    "uel": "soccer/uefa.europa", "uecl": "soccer/uefa.europa.conf",
    "nfl": "football/nfl", "nhl": "hockey/nhl", "nba": "basketball/nba",
}


@dataclass
class Team:
    name: str
    location: str = ""
    short: str = ""
    abbr: str = ""
    id: str = ""

    def aliases(self) -> list[str]:
        return [a for a in (self.name, self.location, self.short, self.abbr) if a]


@dataclass
class EspnGame:
    id: str
    league: str
    kickoff: datetime
    home: Team
    away: Team
    status: str                 # STATUS_SCHEDULED / STATUS_FINAL / ...
    home_score: float | None = None
    away_score: float | None = None
    neutral: bool = False
    season_type: int = 2
    ref_line: dict = field(default_factory=dict)  # DraftKings: spread/total/ml

    @property
    def final(self) -> bool:
        return self.status == "STATUS_FINAL"

    @property
    def title(self) -> str:
        return f"{self.home.name} – {self.away.name}"


def _team(c: dict) -> Team:
    t = c.get("team", {})
    return Team(t.get("displayName", ""), t.get("location", ""),
                t.get("shortDisplayName", ""), t.get("abbreviation", ""), str(t.get("id", "")))


def _ml(v) -> float | None:
    """Amerikanische Moneyline -> Dezimalquote."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return 1 + (v / 100 if v > 0 else 100 / -v)


def parse_scoreboard(data: dict, league: str) -> list[EspnGame]:
    out = []
    for e in data.get("events", []):
        comp = e["competitions"][0]
        cs = {c["homeAway"]: c for c in comp.get("competitors", [])}
        if "home" not in cs or "away" not in cs:
            continue
        st = e.get("status", {}).get("type", {}).get("name", "")
        def sc(c):
            try:
                return float(c.get("score"))
            except (TypeError, ValueError):
                return None
        ref = {}
        if comp.get("odds"):
            o = comp["odds"][0]
            ml = o.get("moneyline") or {}

            def mline(side: str, legacy: dict | None):
                cur = (ml.get(side) or {}).get("close") or (ml.get(side) or {}).get("open") or {}
                v = _ml(str(cur.get("odds", "")).replace("+", "")) if cur.get("odds") else None
                return v or _ml((legacy or {}).get("moneyLine"))
            ref = {"provider": (o.get("provider") or {}).get("name", ""),
                   "details": o.get("details", ""), "total": o.get("overUnder"),
                   "spread": o.get("spread"),
                   "ml_home": mline("home", o.get("homeTeamOdds")),
                   "ml_away": mline("away", o.get("awayTeamOdds")),
                   "ml_draw": mline("draw", o.get("drawOdds"))}
        final = st == "STATUS_FINAL"
        out.append(EspnGame(
            id=str(e["id"]), league=league,
            kickoff=datetime.fromisoformat(e["date"].replace("Z", "+00:00")),
            home=_team(cs["home"]), away=_team(cs["away"]), status=st,
            home_score=sc(cs["home"]) if final else None,
            away_score=sc(cs["away"]) if final else None,
            neutral=bool(comp.get("neutralSite")),
            season_type=int((e.get("season") or {}).get("type", 2) or 2),
            ref_line=ref,
        ))
    return out


def scoreboard_day(league: str, day: date, cache_days: float = 0.0) -> tuple[list[EspnGame], str | None]:
    url = f"{SITE}/{PATHS[league]}/scoreboard?dates={day:%Y%m%d}"
    data, err = fetch.get_json(url, cache_days=cache_days)
    if data is None:
        return [], err
    return parse_scoreboard(data, league), None


def upcoming(league: str, start: date, days: int) -> tuple[list[EspnGame], list[str]]:
    games, errs = [], []
    for k in range(days + 1):
        g, err = scoreboard_day(league, start + timedelta(days=k))
        if err and "HTTP 400" not in err:  # 400 = an diesem Tag keine Spiele
            errs.append(err)
        games += g
    seen, out = set(), []
    for g in games:
        key = (g.home.name, g.away.name, g.kickoff.date())
        if g.id not in seen and key not in seen:
            seen.update({g.id, key})
            out.append(g)
    return out, errs


def nfl_week(season: int, week: int, season_type: int = 2,
             cache_days: float = 0.0) -> tuple[list[EspnGame], str | None]:
    url = f"{SITE}/football/nfl/scoreboard?dates={season}&seasontype={season_type}&week={week}"
    data, err = fetch.get_json(url, cache_days=cache_days)
    if data is None:
        return [], err
    return parse_scoreboard(data, "nfl"), None


def injuries(league: str, event_id: str) -> tuple[dict[str, list[tuple[str, str, str]]], str | None]:
    """Teamname -> [(Spieler, Position, Status)]."""
    data, err = fetch.get_json(f"{SITE}/{PATHS[league]}/summary?event={event_id}")
    if data is None:
        return {}, err
    out = {}
    for t in data.get("injuries", []):
        out[t.get("team", {}).get("displayName", "")] = [
            (i.get("athlete", {}).get("displayName", ""),
             (i.get("athlete", {}).get("position") or {}).get("abbreviation", ""),
             i.get("status", "")) for i in t.get("injuries", [])]
    return out, None
