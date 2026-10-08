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
    "bundesliga": "soccer/ger.1", "2bundesliga": "soccer/ger.2", "3liga": "soccer/ger.3",
    "austria": "soccer/aut.1",
    "epl": "soccer/eng.1", "championship": "soccer/eng.2",
    "laliga": "soccer/esp.1", "seriea": "soccer/ita.1", "ligue1": "soccer/fra.1",
    "eredivisie": "soccer/ned.1", "primeira": "soccer/por.1", "belgium": "soccer/bel.1",
    "switzerland": "soccer/sui.1", "turkey": "soccer/tur.1", "scotland": "soccer/sco.1",
    "sweden": "soccer/swe.1", "norway": "soccer/nor.1", "denmark": "soccer/den.1",
    "poland": "soccer/pol.1", "greece": "soccer/gre.1",
    "ucl": "soccer/uefa.champions", "uel": "soccer/uefa.europa",
    "uecl": "soccer/uefa.europa.conf", "nations": "soccer/uefa.nations",
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
    home_periods: tuple[float, ...] = field(default_factory=tuple)
    away_periods: tuple[float, ...] = field(default_factory=tuple)

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


def _period_scores(c: dict) -> tuple[float, ...]:
    out = []
    for row in c.get("linescores") or []:
        value = row.get("value")
        if value is None:
            value = row.get("displayValue")
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return tuple(out)


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
        o = next((x for x in comp.get("odds") or [] if x), None)
        if o:
            ml = o.get("moneyline") or {}

            def mline(side: str, legacy: dict | None):
                cur = (ml.get(side) or {}).get("close") or (ml.get(side) or {}).get("open") or {}
                v = _ml(str(cur.get("odds", "")).replace("+", "")) if cur.get("odds") else None
                return v or _ml((legacy or {}).get("moneyLine"))
            def line(block: dict | None) -> tuple[float | None, float | None]:
                cur = (block or {}).get("close") or (block or {}).get("open") or {}
                try:
                    ln = float(str(cur.get("line", "")).lstrip("ou").replace("+", ""))
                except ValueError:
                    ln = None
                od = _ml(str(cur.get("odds", "")).replace("+", "")) if cur.get("odds") else None
                return ln, od
            ps, tot = o.get("pointSpread") or {}, o.get("total") or {}
            (hs_line, hs_odds), (as_line, as_odds) = line(ps.get("home")), line(ps.get("away"))
            (ov_line, ov_odds), (_, un_odds) = line(tot.get("over")), line(tot.get("under"))
            ref = {"provider": (o.get("provider") or {}).get("name", ""),
                   "total_line": ov_line, "ml_over": ov_odds, "ml_under": un_odds,
                   "spread_home": hs_line, "odds_spread_home": hs_odds,
                   "spread_away": as_line, "odds_spread_away": as_odds,
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
            home_periods=_period_scores(cs["home"]),
            away_periods=_period_scores(cs["away"]),
        ))
    return out


def scoreboard_day(league: str, day: date, cache_days: float = 0.0) -> tuple[list[EspnGame], str | None]:
    url = f"{SITE}/{PATHS[league]}/scoreboard?dates={day:%Y%m%d}"
    data, err = fetch.get_json(url, cache_days=cache_days)
    if data is None:
        return [], err
    return parse_scoreboard(data, league), None


def scoreboard_range(
    league: str,
    start: date,
    end: date,
    cache_days: float = 0.0,
) -> tuple[list[EspnGame], str | None]:
    """Scoreboard range for historical period/quarter data.

    ESPN's scoreboard includes competitor.linescores for completed NBA/NFL/NHL
    games. Keep ranges reasonably small at call sites to avoid oversized payloads.
    """
    url = (
        f"{SITE}/{PATHS[league]}/scoreboard?limit=1000"
        f"&dates={start:%Y%m%d}-{end:%Y%m%d}"
    )
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


CORE = "https://sports.core.api.espn.com/v2/sports"


def _score(c: dict) -> float | None:
    s = c.get("score")
    if isinstance(s, dict):
        s = s.get("value")
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def team_ids(league: str) -> tuple[list[str], str | None]:
    data, err = fetch.get_json(f"{SITE}/{PATHS[league]}/teams", cache_days=30)
    if data is None:
        return [], err
    teams = data["sports"][0]["leagues"][0]["teams"]
    return [str(t["team"]["id"]) for t in teams], None


def team_schedule(league: str, team_id: str, season: int, season_type: int = 2,
                  cache_days: float = 0.0) -> tuple[list[EspnGame], str | None]:
    """Alle Spiele eines Teams einer Saison (ESPN-Saisonjahr = Endjahr, NBA 2026 = 2025/26)."""
    url = (f"{SITE}/{PATHS[league]}/teams/{team_id}/schedule"
           f"?season={season}&seasontype={season_type}")
    data, err = fetch.get_json(url, cache_days=cache_days)
    if data is None:
        return [], err
    out = []
    for e in data.get("events", []):
        comp = e["competitions"][0]
        cs = {c["homeAway"]: c for c in comp.get("competitors", [])}
        if "home" not in cs or "away" not in cs:
            continue
        st = (comp.get("status") or e.get("status") or {}).get("type", {}).get("name", "")
        final = st == "STATUS_FINAL"
        out.append(EspnGame(
            id=str(e["id"]), league=league,
            kickoff=datetime.fromisoformat(e["date"].replace("Z", "+00:00")),
            home=_team(cs["home"]), away=_team(cs["away"]), status=st,
            home_score=_score(cs["home"]) if final else None,
            away_score=_score(cs["away"]) if final else None,
            neutral=bool(comp.get("neutralSite")), season_type=season_type,
            home_periods=_period_scores(cs["home"]),
            away_periods=_period_scores(cs["away"])))
    return out, None


def key_players(league: str, season: int, top: int = 3) -> tuple[dict[str, tuple[str, float]], list[str]]:
    """Leistungsträger: je Team die Top-n nach Punkten pro Spiel der Saison.

    Gibt Spielername -> (Team der Saison, PPG) zurück; Namen über die Athleten-Refs."""
    ids, err = team_ids(league)
    if err:
        return {}, [err]
    sport = PATHS[league].split("/")[0]
    out, errs = {}, []
    for tid in ids:
        d, err = fetch.get_json(f"{CORE}/{sport}/leagues/{league}/seasons/{season}/types/2/"
                                f"teams/{tid}/leaders", cache_days=14)
        if d is None:
            errs.append(err)
            continue
        cat = next((c for c in d.get("categories", []) if c.get("name") == "pointsPerGame"), None)
        for ld in (cat or {}).get("leaders", [])[:top]:
            ref = (ld.get("athlete") or {}).get("$ref", "")
            a, aerr = fetch.get_json(ref, cache_days=60) if ref else (None, "kein Ref")
            if a and a.get("displayName"):
                out[a["displayName"]] = (tid, float(ld.get("value", 0)))
    return out, errs
