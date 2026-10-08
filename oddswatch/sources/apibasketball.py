"""API-Sports Basketball adapter for European basketball market auditing.

Uses the same API-Sports key convention as the football/hockey adapters.
The adapter is intentionally defensive: API coverage differs by league.
"""
from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import urlencode

from .. import fetch

BASE = "https://v1.basketball.api-sports.io"


def api_key() -> str:
    return (
        os.getenv("API_BASKETBALL_KEY")
        or os.getenv("APIKEY")
        or os.getenv("API_KEY")
        or ""
    ).strip()


def _get(path: str) -> tuple[dict | None, str | None]:
    key = api_key()
    if not key:
        return None, "API-Basketball: APIKEY fehlt"
    data, err = fetch.get_json(
        BASE + path,
        headers={"x-apisports-key": key},
        cache_days=0,
    )
    if data is None:
        return None, err
    if isinstance(data, dict) and data.get("errors"):
        return None, f"API-Basketball: {data.get('errors')}"
    return data if isinstance(data, dict) else {"response": data}, None


def leagues(search: str) -> tuple[list[dict], str | None]:
    data, err = _get("/leagues?" + urlencode({"search": search}))
    return ([] if data is None else list(data.get("response") or [])), err


def resolve_league(search: str, country: str | None = None) -> tuple[dict | None, str | None]:
    rows, err = leagues(search)
    if err:
        return None, err
    target = search.casefold().replace(" ", "")
    scored = []
    for row in rows:
        lg = row.get("league") or row
        name = str(lg.get("name") or row.get("name") or "")
        c = row.get("country") or {}
        cname = str(c.get("name") if isinstance(c, dict) else c or "")
        score = 0
        norm = name.casefold().replace(" ", "")
        if norm == target:
            score += 10
        elif target in norm or norm in target:
            score += 5
        if country and cname.casefold() == country.casefold():
            score += 3
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored or scored[0][0] <= 0:
        return None, f"API-Basketball: Liga nicht gefunden ({search})"
    return scored[0][1], None


def games(*, league_id: int, season: str, date: str | None = None) -> tuple[list[dict], str | None]:
    params = {"league": league_id, "season": season}
    if date:
        params["date"] = date
    data, err = _get("/games?" + urlencode(params))
    return ([] if data is None else list(data.get("response") or [])), err


def odds(*, game_id: int) -> tuple[list[dict], str | None]:
    data, err = _get("/odds?" + urlencode({"game": game_id}))
    return ([] if data is None else list(data.get("response") or [])), err


def parse_game(row: dict) -> dict | None:
    try:
        g = row.get("game") or row
        teams = row["teams"]
        dt = datetime.fromisoformat(str(g["date"]).replace("Z", "+00:00"))
        return {
            "id": int(g["id"]),
            "start": dt,
            "status": str((g.get("status") or {}).get("short") if isinstance(g.get("status"), dict) else g.get("status") or ""),
            "home": str(teams["home"]["name"]),
            "away": str(teams["away"]["name"]),
            "home_id": str(teams["home"].get("id") or teams["home"]["name"]),
            "away_id": str(teams["away"].get("id") or teams["away"]["name"]),
        }
    except (KeyError, TypeError, ValueError):
        return None


def moneyline_books(rows: list[dict]) -> dict[str, dict[str, float]]:
    """Return bookmaker -> {'home': odd, 'away': odd} for full-game Home/Away."""
    out: dict[str, dict[str, float]] = {}
    for block in rows:
        for book in block.get("bookmakers") or []:
            name = str(book.get("name") or "").strip()
            sides: dict[str, float] = {}
            for bet in book.get("bets") or []:
                bname = str(bet.get("name") or "").casefold()
                if not (
                    bname in {"home/away", "moneyline", "money line"}
                    or ("home" in bname and "away" in bname and "1st" not in bname)
                ):
                    continue
                for val in bet.get("values") or []:
                    label = str(val.get("value") or "").casefold()
                    try:
                        odd = float(val.get("odd"))
                    except (TypeError, ValueError):
                        continue
                    if odd <= 1:
                        continue
                    if label in {"home", "1"}:
                        sides["home"] = odd
                    elif label in {"away", "2"}:
                        sides["away"] = odd
            if {"home", "away"} <= sides.keys():
                out[name] = sides
    return out
