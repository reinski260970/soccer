"""FootyStats xG provider for leagues outside Understat coverage.

Uses the documented Football Data API endpoints:
- /league-list
- /league-teams?include=stats&max_time=...

The max_time parameter is critical: historical research can request only the
team state known before a match, preventing future-data leakage.

Requires FOOTYSTATS_API_KEY. No scraping fallback is used because public pages
can expose premium-locked zero placeholders for some leagues.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from .. import fetch, matching

BASE = "https://api.football-data-api.com"

LEAGUES = {
    "D1": ("Germany", ("Bundesliga",)),
    "D2": ("Germany", ("2. Bundesliga", "2 Bundesliga")),
    "E0": ("England", ("Premier League",)),
    "E1": ("England", ("Championship", "EFL Championship")),
    "SP1": ("Spain", ("La Liga", "Primera Division")),
    "I1": ("Italy", ("Serie A",)),
    "F1": ("France", ("Ligue 1",)),
    "N1": ("Netherlands", ("Eredivisie",)),
    "P1": ("Portugal", ("Liga Portugal", "Primeira Liga", "Liga NOS")),
    "B1": ("Belgium", ("Pro League", "First Division A", "Belgian Pro League")),
    "T1": ("Turkey", ("Super Lig", "Süper Lig")),
    "SC0": ("Scotland", ("Premiership", "Scottish Premiership")),
    "G1": ("Greece", ("Super League", "Super League Greece")),
    "AUT": ("Austria", ("Bundesliga", "Austrian Bundesliga")),
}


@dataclass
class TeamXG:
    team: str
    xg: float | None
    xga: float | None
    xg_home: float | None
    xga_home: float | None
    xg_away: float | None
    xga_away: float | None
    source: str = "footystats"


def _key() -> str:
    return (os.environ.get("FOOTYSTATS_API_KEY") or "").strip()


def _num(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    # FootyStats uses negative sentinels for unavailable values.
    if x < 0:
        return None
    return x


def _data_list(payload):
    if not isinstance(payload, dict):
        return []
    d = payload.get("data")
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        # Some endpoints wrap rows under keys such as "teams".
        for k in ("teams", "all", "results"):
            if isinstance(d.get(k), list):
                return d[k]
    return []


def _stats(team):
    s = team.get("stats") if isinstance(team, dict) else None
    if isinstance(s, dict):
        return s
    if isinstance(s, list) and s and isinstance(s[0], dict):
        return s[0]
    return {}


def _league_score(row: dict, country: str, names: tuple[str, ...]) -> int:
    rc = str(row.get("country") or "")
    ln = str(row.get("league_name") or row.get("name") or "")
    score = 0
    if matching.norm(country) in matching.norm(rc) or matching.norm(country) in matching.norm(ln):
        score += 4
    nln = matching.norm(ln)
    for n in names:
        nn = matching.norm(n)
        if nln == nn:
            score += 8
        elif nn in nln or nln in nn:
            score += 4
    return score


def season_id(code: str, year: int) -> tuple[int | None, str | None]:
    key = _key()
    if not key:
        return None, "FOOTYSTATS_API_KEY fehlt"
    cfg = LEAGUES.get(code)
    if not cfg:
        return None, f"FootyStats: Liga {code} nicht gemappt"

    data, err = fetch.get_json(
        f"{BASE}/league-list?key={key}",
        cache_days=1,
    )
    if data is None:
        return None, err or "FootyStats league-list fehlgeschlagen"

    rows = _data_list(data)
    country, names = cfg
    candidates = []
    for row in rows:
        score = _league_score(row, country, names)
        if score <= 0:
            continue
        seasons = row.get("season") or row.get("seasons") or []
        if isinstance(seasons, dict):
            seasons = [seasons]
        for s in seasons:
            try:
                sy = int(s.get("year"))
                sid = int(s.get("id"))
            except (AttributeError, TypeError, ValueError):
                continue
            if sy == year:
                candidates.append((score, sid, row.get("name") or row.get("league_name")))

    if not candidates:
        return None, f"FootyStats: keine Saison {year} für {code}"
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0] and candidates[0][1] != candidates[1][1]:
        return None, f"FootyStats: Saison-Mapping für {code}/{year} mehrdeutig"
    return candidates[0][1], None


def team_xg(code: str, year: int, as_of: datetime | None = None,
            cache_days: float = 0.25) -> tuple[list[TeamXG], str | None]:
    key = _key()
    if not key:
        return [], "FOOTYSTATS_API_KEY fehlt"
    sid, err = season_id(code, year)
    if sid is None:
        return [], err

    url = f"{BASE}/league-teams?key={key}&season_id={sid}&include=stats"
    if as_of is not None:
        ts = int(as_of.astimezone(timezone.utc).timestamp())
        url += f"&max_time={ts}"

    data, err = fetch.get_json(url, cache_days=cache_days)
    if data is None:
        return [], err or f"FootyStats {code}/{year}: keine Daten"

    out = []
    for row in _data_list(data):
        name = str(row.get("name") or row.get("full_name") or row.get("english_name") or "").strip()
        if not name:
            continue
        s = _stats(row)
        out.append(TeamXG(
            team=name,
            xg=_num(s.get("xg_for_avg_overall")),
            xga=_num(s.get("xg_against_avg_overall")),
            xg_home=_num(s.get("xg_for_avg_home")),
            xga_home=_num(s.get("xg_against_avg_home")),
            xg_away=_num(s.get("xg_for_avg_away")),
            xga_away=_num(s.get("xg_against_avg_away")),
        ))

    real = [r for r in out if r.xg is not None and r.xga is not None and (r.xg > 0 or r.xga > 0)]
    if not real:
        return [], f"FootyStats {code}/{year}: keine echten xG/xGA-Werte"
    return real, None
