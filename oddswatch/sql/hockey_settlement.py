"""Forward settlement of stored hockey forecasts from independently verified results.

Never infer full-game scores from 60-minute tied results or from model output.
The match must have the same league, date and unambiguous home/away teams
(or the exact ESPN game ID for NHL). This module never sends Telegram/PLAYs.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from .. import matching
from ..sources import hockeyarchives
from .evaluation import evaluate


def _score(value):
    """Reject missing, negative, fractional or boolean score data."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        n = int(str(value))
        return n if n >= 0 and str(value).strip() in (str(n), f"{n}.0") else None
    except (TypeError, ValueError):
        return None


def nhl_finals(data: dict) -> dict[str, dict]:
    """Extract only official FINAL NHL regular-season results by ESPN ID."""
    out = {}
    for event in data.get("events", []):
        if (event.get("status") or {}).get("type", {}).get("name") != "STATUS_FINAL":
            continue
        season = event.get("season") or {}
        if season.get("type") not in (None, 2, "2"):
            continue  # no preseason or postseason leakage
        competitions = event.get("competitions") or []
        if len(competitions) != 1:
            continue
        teams = {t.get("homeAway"): t for t in competitions[0].get("competitors", [])}
        if set(teams) != {"home", "away"}:
            continue
        h, a = teams["home"], teams["away"]
        hs, ass = _score(h.get("score")), _score(a.get("score"))
        if hs is None or ass is None or hs == ass:
            continue  # A 2-way NHL game cannot end tied.
        hid = str(event.get("id", ""))
        if not hid or hid in out:
            continue
        out[hid] = {
            "home": (h.get("team") or {}).get("displayName", ""),
            "away": (a.get("team") or {}).get("displayName", ""),
            "home_score": hs, "away_score": ass,
        }
    return out



# Only audited name variants of hockeyarchives' top-league teams.
# Never use generic city-only fuzzy matching across different leagues.
_DEL_NAMES = {
    "adler mannheim": "Mannheim",
    "augsburger panther": "Augsbourg",
    "erc ingolstadt": "Ingolstadt",
    "eisbaren berlin": "Berlin",
    "fischtown pinguins": "Bremerhaven",
    "grizzlys wolfsburg": "Wolfsburg",
    "iserlohn roosters": "Iserlohn",
    "kolner haie": "Cologne",
    "krefeld pinguine": "Krefeld",
    "lowen frankfurt": "Francfort",
    "nuremberg ice tigers": "Nuremberg",
    "nurnberg ice tigers": "Nuremberg",
    "red bull munich": "Munich",
    "ehc red bull munchen": "Munich",
    "schwenninger wild wings": "Schwenningen",
    "straubing tigers": "Straubing",
    "dresdner eislowen": "Dresde",
    "dusseldorfer eg": "Düsseldorf",
}


def _hockeyarchives_team(name: str, league: str) -> str:
    if league == "del":
        return _DEL_NAMES.get(matching.norm(name), name)
    return name


def _same_team(a: str, b: str, league: str) -> bool:
    if league == "icehl":
        a = hockeyarchives.canonical_icehl(a)
        b = hockeyarchives.canonical_icehl(b)
    a = _hockeyarchives_team(a, league)
    b = _hockeyarchives_team(b, league)
    na, nb = matching.norm(a), matching.norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    shorter, longer = (set(na.split()), set(nb.split()))
    if len(shorter) > len(longer):
        shorter, longer = longer, shorter
    # Prefix names like "KooKoo" vs "KooKoo Kouvola" are valid;
    # exclude generic "HC" matches and never swap home/away.
    return bool(shorter) and shorter <= longer and any(len(t) >= 3 for t in shorter)


def european_final(event: dict, results: list) -> tuple[int, int] | None:
    """Use verified regulation winners only: OT/SO data lack final winner here."""
    league = event["league"]
    zones = {"icehl": "Europe/Vienna", "liiga": "Europe/Helsinki",
             "shl": "Europe/Stockholm", "del": "Europe/Berlin",
             "extraliga": "Europe/Prague"}
    day = event["kickoff"].astimezone(ZoneInfo(zones[league])).date()
    hits = [r for r in results
            if r.date == day
            and _same_team(event["home_name"], r.home, league)
            and _same_team(event["away_name"], r.away, league)]
    if len(hits) != 1:
        return None
    r = hits[0]
    if r.extra or r.reg_home == r.reg_away:
        return None
    if _score(r.reg_home) is None or _score(r.reg_away) is None:
        return None
    return int(r.reg_home), int(r.reg_away)


def _fetch_espn(url: str) -> dict:
    with urlopen(Request(url, headers={"User-Agent": "SportsResearch/1.0"}), timeout=25) as reply:
        return json.load(reply)


def _write_final(conn, event: dict, home: int, away: int,
                 source: str, evidence: dict, now: datetime) -> bool:
    if event["kickoff"] >= now or home == away:
        return False
    from psycopg.types.json import Jsonb
    with conn.transaction():
        row = conn.execute(
            "UPDATE sports.events SET status='STATUS_FINAL',home_score=%s,away_score=%s,observed_at=%s "
            "WHERE event_id=%s AND status<>'STATUS_FINAL' AND kickoff<%s AND observed_at<=%s "
            "RETURNING event_id",
            (home, away, now, event["event_id"], now, now),
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "INSERT INTO sports.event_observations(event_id,observed_at,kickoff,status,home_score,away_score) "
            "VALUES(%s,%s,%s,'STATUS_FINAL',%s,%s) ON CONFLICT DO NOTHING",
            (event["event_id"], now, event["kickoff"], home, away),
        )
        conn.execute(
            "INSERT INTO sports.raw_payloads(source,resource,observed_at,payload) "
            "VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (source, "verified-result:" + event["event_id"], now, Jsonb({
                "source": source, "event_id": event["event_id"],
                "home": event["home_name"], "away": event["away_name"],
                "home_score": home, "away_score": away,
                "score_scope": "FULL_GAME_VERIFIED",
                "evidence": evidence,
            })),
        )
    return True


def run(conn, now: datetime | None = None, fetch_espn=None, fetch_europe=None):
    """Incrementally settle expired hockey events; report rather than invent gaps."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    fetch_espn = fetch_espn or _fetch_espn
    fetch_europe = fetch_europe or {
        "liiga": lambda season: hockeyarchives.liiga(season + 1),
        "icehl": lambda season: hockeyarchives.icehl(season, cache_days=0),
        "shl": hockeyarchives.shl,
        # Historical top-league pages carry 60-minute period totals.
        # OT/SO ties are withheld: we cannot identify the market winner.
        "del": lambda season: hockeyarchives.season_results(
            "del", season, cache_days=0.02),
        "extraliga": lambda season: hockeyarchives.season_results(
            "extraliga", season, cache_days=0.02),
    }
    pending = conn.execute(
        "SELECT e.event_id,e.league,e.source_event_id,e.home_name,e.away_name,e.kickoff "
        "FROM sports.events e WHERE e.league IN ('nhl','liiga','icehl','shl','del','extraliga') "
        "AND e.status<>'STATUS_FINAL' AND e.kickoff<%s AND "
        "EXISTS(SELECT 1 FROM sports.predictions p WHERE p.event_id=e.event_id) "
        "ORDER BY e.kickoff LIMIT 200", (now,),
    ).fetchall()
    totals = {"pending": len(pending), "events_settled": 0,
              "predictions_evaluated": 0, "not_verifiable": 0, "errors": []}
    nhl_pending = [e for e in pending if e["league"] == "nhl"]
    # ESPN scoreboard dates are US-local: include the preceding local date.
    scoreboard = {}
    if nhl_pending:
        days = sorted({(e["kickoff"] + timedelta(hours=offset)).date()
                       for e in nhl_pending for offset in (-12, 0, 12)})
        for day in days:
            url = ("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/"
                   f"scoreboard?dates={day:%Y%m%d}&limit=500")
            try:
                data = fetch_espn(url)
                scoreboard.update(nhl_finals(data))
            except Exception as exc:
                totals["errors"].append(f"ESPN NHL {day}: {type(exc).__name__}")
    euro_results = {}
    for league in ("liiga", "icehl", "shl", "del", "extraliga"):
        rows = [e for e in pending if e["league"] == league]
        for season in sorted({e["kickoff"].year if e["kickoff"].month >= 7
                              else e["kickoff"].year - 1 for e in rows}):
            try:
                result = fetch_europe[league](season)
                if league in ("del", "extraliga") and len(result) == 2:
                    done, err = result
                else:
                    done, _, err = result
                if err:
                    totals["errors"].append(f"{league} {season}: {err}")
                else:
                    euro_results[(league, season)] = done
            except Exception as exc:
                totals["errors"].append(f"{league} {season}: {type(exc).__name__}")
    for event in pending:
        league = event["league"]
        if league == "nhl":
            result = scoreboard.get(str(event["source_event_id"]))
            if not result or not (_same_team(event["home_name"], result["home"], league)
                                  and _same_team(event["away_name"], result["away"], league)):
                totals["not_verifiable"] += 1
                continue
            home, away = result["home_score"], result["away_score"]
            source, proof = "espn-nhl-final", result
        else:
            season = (event["kickoff"].year if event["kickoff"].month >= 7
                      else event["kickoff"].year - 1)
            result = european_final(event, euro_results.get((league, season), []))
            if result is None:
                totals["not_verifiable"] += 1
                continue
            home, away = result
            source = (f"{league}-hockeyarchives-regulation-final"
                      if league in ("del", "extraliga")
                      else f"{league}-official-regulation-final")
            proof = {"method": "regulation win, no OT/SO; full-game winner proven"}
        if _write_final(conn, event, home, away, source, proof, now):
            totals["events_settled"] += 1
    totals["predictions_evaluated"] = evaluate(conn)
    return totals
