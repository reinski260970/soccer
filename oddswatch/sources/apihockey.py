"""API-Sports Hockey odds for NHL and European hockey.

Uses the same API-Sports key as API-Football where possible. Public model fair
probabilities are never sent to the provider; prices are attached only afterwards.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .. import fetch, matching, pricing
from ..selection import Offer

BASE = "https://v1.hockey.api-sports.io"
EXEC_BOOKS = {"bet365", "betfair", "unibet", "bwin", "1xbet", "10bet"}
REF_BOOKS = {"pinnacle"}


def api_key() -> str:
    for name in ("API_HOCKEY_KEY", "APIKEY", "API_KEY"):
        key = (os.getenv(name) or "").strip()
        if key:
            return key
    return ""


def _get(path: str) -> tuple[dict | None, str | None]:
    key = api_key()
    if not key:
        return None, "API-Hockey: APIKEY nicht gesetzt"
    data, err = fetch.get_json(BASE + path, headers={"x-apisports-key": key}, retries=1)
    if err:
        return None, f"API-Hockey {path}: {err.split(': ', 1)[-1]}"
    errors = data.get("errors") if isinstance(data, dict) else None
    if errors:
        return None, f"API-Hockey {path}: {errors}"
    return data, None


@dataclass
class ApiGame:
    id: int
    kickoff: datetime
    home: str
    away: str
    league: str


def games_on(day: str) -> tuple[list[ApiGame], str | None]:
    data, err = _get(f"/games?date={day}&timezone=UTC")
    if data is None:
        return [], err
    out = []
    for row in data.get("response") or []:
        try:
            out.append(ApiGame(
                int(row["id"]), datetime.fromisoformat(str(row["date"]).replace("Z", "+00:00")),
                str(row["teams"]["home"]["name"]), str(row["teams"]["away"]["name"]),
                str(row.get("league", {}).get("name") or ""),
            ))
        except (KeyError, TypeError, ValueError):
            continue
    return out, None


def _hit(name: str, aliases: list[str]) -> bool:
    return any(matching.same(name, a) or matching.match_label(name, aliases)
               for a in aliases if a)


def find_game(games: list[ApiGame], home: list[str], away: list[str], kickoff: datetime,
              tolerance: timedelta = timedelta(hours=2)) -> ApiGame | None:
    ko = kickoff.astimezone(timezone.utc)
    hits = [g for g in games if abs(g.kickoff.astimezone(timezone.utc) - ko) <= tolerance
            and _hit(g.home, home) and _hit(g.away, away)]
    return hits[0] if len(hits) == 1 else None


def _book(name: str) -> str | None:
    n = matching.norm(name).replace(" ", "")
    for key in ("pinnacle", "bet365", "betfair", "unibet", "bwin", "1xbet", "10bet"):
        if key in n:
            return key
    return None


def _side(value: str, home: str = "", away: str = "") -> str | None:
    v = value.strip().lower()
    if v in {"home", "1", "team 1", "home team"}:
        return "home"
    if v in {"away", "2", "team 2", "away team"}:
        return "away"
    if home and matching.same(value, home):
        return "home"
    if away and matching.same(value, away):
        return "away"
    return None


def parse_odds(data: dict) -> dict[str, dict[str, float]]:
    """Return {book: {home, away}} for two-way full-game moneyline markets."""
    out: dict[str, dict[str, float]] = {}
    for row in data.get("response") or []:
        game = row.get("game") or {}
        teams = game.get("teams") or row.get("teams") or {}
        home = str((teams.get("home") or {}).get("name") or "")
        away = str((teams.get("away") or {}).get("name") or "")
        for b in row.get("bookmakers") or []:
            key = _book(str(b.get("name") or ""))
            if not key:
                continue
            mk = out.setdefault(key, {})
            for bet in b.get("bets") or []:
                bn = str(bet.get("name") or "").lower()
                if any(x in bn for x in ("period", "1st", "2nd", "3rd", "handicap", "over/under", "total")):
                    continue
                if not any(x in bn for x in ("home/away", "money line", "moneyline", "winner", "match winner")):
                    continue
                local = {}
                for val in bet.get("values") or []:
                    side = _side(str(val.get("value") or ""), home, away)
                    try:
                        odd = float(val.get("odd"))
                    except (TypeError, ValueError):
                        continue
                    if side and odd > 1.0:
                        local[side] = odd
                if set(local) == {"home", "away"}:
                    mk.update(local)
                    break
    return {b: m for b, m in out.items() if set(m) >= {"home", "away"}}


def odds(game_id: int) -> tuple[dict[str, dict[str, float]], str | None]:
    data, err = _get(f"/odds?game={game_id}")
    if data is None:
        return {}, err
    return parse_odds(data), None


def _consensus(books: dict[str, dict[str, float]]) -> dict[str, float]:
    refs = []
    for name, mk in books.items():
        if set(mk) >= {"home", "away"}:
            try:
                p = pricing.devig([mk["home"], mk["away"]])
            except (ValueError, ZeroDivisionError):
                continue
            refs.append((p[0], p[1], name))
    if not refs:
        return {}
    pin = next((r for r in refs if r[2] in REF_BOOKS), None)
    if pin:
        return {"home": pin[0], "away": pin[1]}
    hs = sorted(r[0] for r in refs)
    aas = sorted(r[1] for r in refs)
    i = len(hs) // 2
    h = hs[i] if len(hs) % 2 else (hs[i - 1] + hs[i]) / 2
    a = aas[i] if len(aas) % 2 else (aas[i - 1] + aas[i]) / 2
    z = h + a
    return {"home": h / z, "away": a / z}


def attach(fixtures, issues: list[str]) -> int:
    rows = [f for f in fixtures if f.sport in {"hockey", "nhl"}]
    if not rows:
        return 0
    if not api_key():
        issues.append("API-Hockey: APIKEY fehlt – keine europäischen Hockeypreise")
        return 0

    day_cache: dict[str, list[ApiGame]] = {}
    odds_cache: dict[int, dict[str, dict[str, float]]] = {}
    matched = 0
    now = datetime.now(timezone.utc)
    for fx in rows:
        day = fx.game.kickoff.astimezone(timezone.utc).date().isoformat()
        if day not in day_cache:
            day_cache[day], err = games_on(day)
            if err:
                issues.append(err)
        g = find_game(day_cache.get(day, []), fx.game.home.aliases(), fx.game.away.aliases(),
                      fx.game.kickoff)
        if not g:
            continue
        matched += 1
        if g.id not in odds_cache:
            odds_cache[g.id], err = odds(g.id)
            if err:
                issues.append(err)
        books = odds_cache[g.id]
        if not books:
            continue
        ref = _consensus(books)
        if ref:
            if not fx.ref_probs:
                fx.ref_probs = ref
            fx.context.append(
                f"API-Hockey Markt: {fx.game.home.name} {ref['home']*100:.1f}% / "
                f"{fx.game.away.name} {ref['away']*100:.1f}% ({'Pinnacle' if 'pinnacle' in books else 'Konsens'})"
            )

        executable = {k: v for k, v in books.items() if k in EXEC_BOOKS}
        for side in ("home", "away"):
            vals = {k: v[side] for k, v in executable.items() if side in v}
            if not vals:
                continue
            fair_ref = (1.0 / ref[side]) if ref.get(side) else None
            for book, odd in vals.items():
                extreme = bool(fair_ref and odd / fair_ref - 1.0 > 0.20)
                peer = any(k != book and o >= odd * 0.90 for k, o in vals.items())
                if extreme and not peer:
                    issues.append(
                        f"API-Hockey: Preis-Outlier verworfen ({fx.game.title}, {side}, "
                        f"{book} {odd:.2f} vs fair {fair_ref:.2f})")
                    continue
                team = fx.game.home.name if side == "home" else fx.game.away.name
                fx.offers.setdefault(side, []).append(Offer(
                    event=fx.game.title, kickoff=fx.game.kickoff.isoformat(), market=side,
                    selection=f"{team} Sieg (inkl. OT)", odds=odd, source=book,
                    observed_at=now.isoformat(), ref=f"api-hockey:{g.id}:{side}:{book}",
                    league=fx.league, executable=True,
                ))
    return matched
