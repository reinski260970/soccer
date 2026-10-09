"""Strict forward settlement for stored soccer forecasts via API-Football.

Only official finished fixtures are accepted. For regulation markets we persist
the API-Football fulltime (90-minute) score, never extra-time or penalty scores.
No Telegram/PLAY side effects.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .. import matching
from ..sources import apifootball
from .evaluation import evaluate


def _score(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        n = int(str(value))
        return n if n >= 0 and str(value).strip() in (str(n), f"{n}.0") else None
    except (TypeError, ValueError):
        return None


def parse_final(data: dict, event: dict) -> tuple[int, int, dict] | None:
    """Accept exactly one finished matching fixture and its 90-minute score."""
    hits = []
    for row in data.get("response") or []:
        fixture = row.get("fixture") or {}
        status = (fixture.get("status") or {}).get("short")
        if status not in {"FT", "AET", "PEN"}:
            continue
        teams = row.get("teams") or {}
        home = (teams.get("home") or {}).get("name", "")
        away = (teams.get("away") or {}).get("name", "")
        if not (matching.same(event["home_name"], home)
                and matching.same(event["away_name"], away)):
            continue
        score = row.get("score") or {}
        fulltime = score.get("fulltime") or {}
        hs, ass = _score(fulltime.get("home")), _score(fulltime.get("away"))
        if hs is None or ass is None:
            continue
        hits.append((hs, ass, {
            "fixture_id": fixture.get("id"),
            "status": status,
            "home": home, "away": away,
            "score_scope": "REGULATION_90_MIN",
            "fulltime": {"home": hs, "away": ass},
        }))
    return hits[0] if len(hits) == 1 else None


def _fetch_fixture(fixture_id: str):
    return apifootball._get(f"/fixtures?id={fixture_id}")


def run(conn, now: datetime | None = None, fetch_fixture=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("timezone-aware now required")
    fetch_fixture = fetch_fixture or _fetch_fixture

    pending = conn.execute(
        "SELECT e.event_id,e.league,e.source_event_id,e.home_name,e.away_name,e.kickoff "
        "FROM sports.events e WHERE e.status<>'STATUS_FINAL' AND e.kickoff<%s "
        "AND e.league NOT IN ('nhl','liiga','icehl','shl','nba','nfl','euroleague','acb','bbl') "
        "AND EXISTS(SELECT 1 FROM sports.predictions p WHERE p.event_id=e.event_id "
        "AND p.settlement_rules='REGULATION') ORDER BY e.kickoff LIMIT 300",
        (now,),
    ).fetchall()
    totals = {"pending": len(pending), "events_settled": 0,
              "predictions_evaluated": 0, "not_verifiable": 0, "errors": []}

    from psycopg.types.json import Jsonb
    for event in pending:
        sid = str(event["source_event_id"] or "")
        if not sid.isdigit():
            totals["not_verifiable"] += 1
            continue
        try:
            data, err = fetch_fixture(sid)
        except Exception as exc:
            totals["errors"].append(f"{event['event_id']}: {type(exc).__name__}")
            continue
        if err or not isinstance(data, dict):
            totals["errors"].append(f"{event['event_id']}: {err or 'invalid response'}")
            continue
        result = parse_final(data, event)
        if result is None:
            totals["not_verifiable"] += 1
            continue
        home, away, proof = result
        with conn.transaction():
            row = conn.execute(
                "UPDATE sports.events SET status='STATUS_FINAL',home_score=%s,away_score=%s,observed_at=%s "
                "WHERE event_id=%s AND status<>'STATUS_FINAL' AND kickoff<%s AND observed_at<=%s "
                "RETURNING event_id",
                (home, away, now, event["event_id"], now, now),
            ).fetchone()
            if not row:
                continue
            conn.execute(
                "INSERT INTO sports.event_observations(event_id,observed_at,kickoff,status,home_score,away_score) "
                "VALUES(%s,%s,%s,'STATUS_FINAL',%s,%s) ON CONFLICT DO NOTHING",
                (event["event_id"], now, event["kickoff"], home, away),
            )
            conn.execute(
                "INSERT INTO sports.raw_payloads(source,resource,observed_at,payload) "
                "VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                ("api-football-regulation-final", "verified-result:" + event["event_id"],
                 now, Jsonb(proof)),
            )
        totals["events_settled"] += 1

    totals["predictions_evaluated"] = evaluate(conn)
    return totals
