"""Europäisches Eishockey: Ergebnisse von hockeyarchives.info (+ Liiga-API).

hockeyarchives.info führt je Land und Saison eine Seite (<Land><Endjahr>.htm,
z. B. Allemagne2027.htm = 2026/27) mit Zeilen wie
  "Munich - Mannheim 4-3 t.a.b. (1-0,2-1,0-2,0-0,1-0)"
Heim zuerst; "a.p." = Verlängerung, "t.a.b." = Penaltyschießen; die ersten
drei Drittel ergeben das 60-Minuten-Ergebnis. Datum aus den Spieltags-
überschriften ("(vendredi 18 septembre 2026)") oder "18/08/2026". Teamnamen
französisch (Cologne, Munich, Berne). Eine Seite enthält auch Unterligen und
Testspiele – für ein Poisson-Modell je Team unschädlich.

Die laufende Saison fehlt dort anfangs teils (404) – Liiga und SHL kommen
daher zusätzlich aus den offiziellen APIs (liiga.fi, shl.se). Die SHL-API hat
keine Drittelergebnisse: nach Verlängerung/Penalty stand es nach 60 Minuten
unentschieden (niedrigerer Endstand beider Teams).
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date, datetime

from .. import fetch

BASE = "https://www.hockeyarchives.info"
UA = "Mozilla/5.0 (X11; Linux x86_64) oddswatch/0.2"
# Liga -> Länderseite
PAGES = {"del": "Allemagne", "icehl": "Autriche", "shl": "Suede", "liiga": "Finlande",
         "nl": "Suisse", "khl": "Russie", "extraliga": "Tcheque", "slovakia": "Slovaquie",
         "norway": "Norvege", "denmark": "Danemark", "chl": "CHL"}
LIIGA_API = "https://liiga.fi/api/v2/games?tournament=runkosarja&season={season}"
SHL_API = "https://www.shl.se/api/sports-v2"

_MONTHS = {m: i + 1 for i, m in enumerate(
    "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split())}
_NAME = r"[A-ZÀ-ÝŠŽČŘ][\w .'’\-]+?"
_GAME = re.compile(rf"({_NAME}) - ({_NAME}) (\d+)-(\d+)( a\.p\.| t\.a\.b\.)? \(([\d,\- ]+)\)")
_DATE = re.compile(r"(\d{1,2})(?:er)? (" + "|".join(_MONTHS) + r") (\d{4})|(\d{2})/(\d{2})/(\d{4})")


@dataclass
class HockeyResult:
    date: date
    home: str
    away: str
    reg_home: int          # Tore nach 60 Minuten
    reg_away: int
    extra: str = ""        # "" | "OT" | "SO"


def page_url(league: str, end_year: int) -> str:
    return f"{BASE}/{PAGES[league]}{end_year}.htm"


_ANCHOR = re.compile(r'<a\s+name="([^"]*)"', re.I)


def _text(raw: bytes) -> str:
    """Seitentext ohne Testspiel-Abschnitte (<A NAME="Amicaux">)."""
    enc = "utf-8" if b"charset=utf-8" in raw[:800].lower() else "cp1252"
    h = raw.decode(enc, "replace")
    parts, last, keep = [], 0, True
    for m in _ANCHOR.finditer(h):
        if keep:
            parts.append(h[last:m.start()])
        keep, last = not m.group(1).lower().startswith("amicaux"), m.start()
    if keep:
        parts.append(h[last:])
    t = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(parts)))
    return re.sub(r"\s+", " ", t)


def parse_page(raw: bytes | str, season_start: int) -> list[HockeyResult]:
    """Alle Spiele einer Länderseite in Textreihenfolge; Datum = letzte
    Datumsangabe davor (fehlt sie, 1.9. des Startjahres)."""
    t = _text(raw.encode("utf-8") if isinstance(raw, str) else raw)
    events = sorted([(m.start(), "d", m) for m in _DATE.finditer(t)]
                    + [(m.start(), "g", m) for m in _GAME.finditer(t)], key=lambda x: x[0])
    cur, out = date(season_start, 9, 1), []
    for _, kind, m in events:
        if kind == "d":
            try:
                cur = (date(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1))) if m.group(1)
                       else date(int(m.group(6)), int(m.group(5)), int(m.group(4))))
            except ValueError:
                pass
            continue
        periods = [p.split("-") for p in m.group(6).split(",") if "-" in p]
        if len(periods) < 3:
            continue
        try:
            rh = sum(int(p[0]) for p in periods[:3])
            ra = sum(int(p[1]) for p in periods[:3])
        except ValueError:
            continue
        ext = {" a.p.": "OT", " t.a.b.": "SO"}.get(m.group(5) or "", "")
        out.append(HockeyResult(cur, m.group(1).strip(), m.group(2).strip(), rh, ra, ext))
    return out


def season_results(league: str, season_start: int, cache_days: float
                   ) -> tuple[list[HockeyResult], str | None]:
    raw, err = fetch.get(page_url(league, season_start + 1), timeout=45,
                         cache_days=cache_days, user_agent=UA)
    if raw is None:
        return [], err
    return parse_page(raw, season_start), None


def parse_liiga(data: list) -> tuple[list[HockeyResult], list[dict]]:
    """Liiga-API: (beendete Spiele, anstehende Spiele {start, home, away})."""
    done, upcoming = [], []
    for g in data:
        h, a = g["homeTeam"]["teamName"], g["awayTeam"]["teamName"]
        start = datetime.fromisoformat(g["start"].replace("Z", "+00:00"))
        if not g.get("ended"):
            upcoming.append({"start": start, "home": h, "away": a})
            continue
        reg = [p for p in g.get("periods") or [] if p.get("category") == "NORMAL"][:3]
        rh = sum(p["homeTeamGoals"] for p in reg)
        ra = sum(p["awayTeamGoals"] for p in reg)
        ft = g.get("finishedType", "")
        ext = "SO" if "WINNING_SHOT" in ft else ("OT" if "EXTENDED" in ft else "")
        done.append(HockeyResult(start.date(), h, a, rh, ra, ext))
    return done, upcoming


def liiga(season_end: int) -> tuple[list[HockeyResult], list[dict], str | None]:
    data, err = fetch.get_json(LIIGA_API.format(season=season_end), timeout=45)
    if data is None:
        return [], [], err
    done, up = parse_liiga(data)
    return done, up, None


def parse_shl(data: dict) -> tuple[list[HockeyResult], list[dict]]:
    done, upcoming = [], []
    for g in data.get("gameInfo", []):
        hi, ai = g.get("homeTeamInfo") or {}, g.get("awayTeamInfo") or {}
        h = (hi.get("names") or {}).get("long") or hi.get("code", "")
        a = (ai.get("names") or {}).get("long") or ai.get("code", "")
        start = datetime.fromisoformat(g["rawStartDateTime"].replace("Z", "+00:00"))
        if g.get("state") != "post-game":
            upcoming.append({"start": start, "home": h, "away": a})
            continue
        sh, sa = int(hi.get("score") or 0), int(ai.get("score") or 0)
        ext = "SO" if g.get("shootout") else ("OT" if g.get("overtime") else "")
        rh, ra = (min(sh, sa), min(sh, sa)) if ext else (sh, sa)
        done.append(HockeyResult(start.date(), h, a, rh, ra, ext))
    return done, upcoming


def shl(season_start: int) -> tuple[list[HockeyResult], list[dict], str | None]:
    f, err = fetch.get_json(f"{SHL_API}/season-series-game-types-filter", timeout=45, cache_days=7)
    if f is None:
        return [], [], err
    season = next((x["uuid"] for x in f.get("season", []) if x.get("code") == str(season_start)), None)
    series = next((x["uuid"] for x in f.get("series", []) if x.get("code") == "SHL"), None)
    gtype = next((x["uuid"] for x in f.get("gameType", []) if x.get("code") == "regular"), None)
    if not (season and series and gtype):
        return [], [], f"SHL-API: Saison {season_start} nicht gefunden"
    data, err = fetch.get_json(f"{SHL_API}/game-schedule?seasonUuid={season}&seriesUuid={series}"
                               f"&gameTypeUuid={gtype}&gamePlace=all&played=all", timeout=45)
    if data is None:
        return [], [], err
    done, up = parse_shl(data)
    return done, up, None


ICEHL_API = "https://s3-eu-west-1.amazonaws.com/icehl.hokejovyzapis.cz/league-matches/{season}/1.json"


def parse_icehl(data: dict) -> tuple[list[HockeyResult], list[dict]]:
    """ICEHL-Datenfeed (Widget von ice.hockey): Anstoß in Ortszeit Wien."""
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Europe/Vienna")
    done, upcoming = [], []
    for m in data.get("matches", []):
        h, a = m["home"]["name"], m["guest"]["name"]
        start = datetime.strptime(m["start_date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
        if m.get("status") != "AFTER_MATCH":
            if m.get("status") == "BEFORE_MATCH":
                upcoming.append({"start": start, "home": h, "away": a})
            continue
        sc = (m.get("results") or {}).get("score") or {}
        per = [sc.get(k) or {} for k in ("first_period", "second_period", "third_period")]
        rh = sum(int(p.get("score_home") or 0) for p in per)
        ra = sum(int(p.get("score_guest") or 0) for p in per)
        r = m.get("results") or {}
        ext = "SO" if r.get("shooting") else ("OT" if r.get("extra_time") else "")
        done.append(HockeyResult(start.date(), h, a, rh, ra, ext))
    return done, upcoming


def icehl(season_start: int, cache_days: float = 0.0
          ) -> tuple[list[HockeyResult], list[dict], str | None]:
    data, err = fetch.get_json(ICEHL_API.format(season=season_start), timeout=45,
                               cache_days=cache_days)
    if data is None:
        return [], [], err
    done, up = parse_icehl(data)
    return done, up, None
