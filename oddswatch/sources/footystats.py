"""FootyStats API: Matchdaten/xG für breite europäische Ligaabdeckung.

API-Key via FOOTYSTATS_API_KEY (alternativ FOOTYSTATS_KEY).
Marktquoten aus FootyStats werden NICHT als Modellfeatures verwendet.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from .. import fetch

BASE = "https://api.football-data-api.com"


def api_key() -> str:
    return (os.environ.get("FOOTYSTATS_API_KEY")
            or os.environ.get("FOOTYSTATS_KEY")
            or "").strip()


def _get(path: str, *, key: str | None = None,
         cache_days: float = 1.0) -> tuple[dict | None, str | None]:
    k = (key or api_key()).strip()
    if not k:
        return None, "FootyStats: FOOTYSTATS_API_KEY fehlt"
    sep = "&" if "?" in path else "?"
    data, err = fetch.get_json(
        BASE + path + f"{sep}key={k}",
        cache_days=cache_days,
        retries=1,
    )
    if data is None:
        return None, err or "FootyStats: keine Daten"
    if not isinstance(data, dict) or data.get("success") is False:
        return None, "FootyStats: API-Antwort nicht erfolgreich"
    return data, None


@dataclass
class FSMatch:
    id: int
    season_id: int
    kickoff: datetime
    home_id: int
    away_id: int
    home: str | None
    away: str | None
    status: str
    home_goals: int | None
    away_goals: int | None
    home_xg: float | None
    away_xg: float | None


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def league_list(*, key: str | None = None) -> tuple[list[dict], str | None]:
    data, err = _get("/league-list", key=key, cache_days=7)
    if data is None:
        return [], err
    rows = data.get("data") or data.get("response") or []
    return rows if isinstance(rows, list) else [], None


def league_matches(season_id: int, *, key: str | None = None,
                   max_per_page: int = 1000) -> tuple[list[dict], str | None]:
    data, err = _get(
        f"/league-matches?season_id={int(season_id)}&max_per_page={int(max_per_page)}",
        key=key, cache_days=1,
    )
    if data is None:
        return [], err
    rows = data.get("data") or data.get("response") or []
    return rows if isinstance(rows, list) else [], None


def match_detail(match_id: int, *, key: str | None = None,
                 cache_days: float = 30.0) -> tuple[dict | None, str | None]:
    data, err = _get(f"/match?match_id={int(match_id)}", key=key,
                     cache_days=cache_days)
    if data is None:
        return None, err
    row = data.get("data")
    if isinstance(row, list):
        row = row[0] if row else None
    if row is None:
        row = data.get("response")
        if isinstance(row, list):
            row = row[0] if row else None
    return row if isinstance(row, dict) else None, None


def parse_match(row: dict, season_id: int | None = None) -> FSMatch | None:
    mid = _int(row.get("id"))
    ts = _int(row.get("date_unix") or row.get("timestamp"))
    hid = _int(row.get("homeID"))
    aid = _int(row.get("awayID"))
    if mid is None or ts is None or hid is None or aid is None:
        return None
    sid = _int(row.get("competition_id") or row.get("season_id") or season_id)
    if sid is None:
        return None
    hg = _int(row.get("homeGoalCount") if row.get("homeGoalCount") is not None
              else row.get("home_team_goal_count"))
    ag = _int(row.get("awayGoalCount") if row.get("awayGoalCount") is not None
              else row.get("away_team_goal_count"))
    hx = _num(row.get("team_a_xg"))
    ax = _num(row.get("team_b_xg"))
    return FSMatch(
        id=mid, season_id=sid,
        kickoff=datetime.fromtimestamp(ts, tz=timezone.utc),
        home_id=hid, away_id=aid,
        home=row.get("home_name") or row.get("team_a_name"),
        away=row.get("away_name") or row.get("team_b_name"),
        status=str(row.get("status") or ""),
        home_goals=hg, away_goals=ag,
        home_xg=hx, away_xg=ax,
    )


def example_probe() -> dict:
    """Öffentlicher FootyStats-Beispieltest, keine Nutzer-Credentials."""
    detail, err = match_detail(579101, key="example", cache_days=30)
    if detail is None:
        return {"ok": False, "error": err}
    return {
        "ok": True,
        "has_match_xg": _num(detail.get("team_a_xg")) is not None
                        and _num(detail.get("team_b_xg")) is not None,
        "has_shots": detail.get("team_a_shots") is not None
                     and detail.get("team_b_shots") is not None,
        "has_lineups": isinstance(detail.get("lineups"), dict),
    }
