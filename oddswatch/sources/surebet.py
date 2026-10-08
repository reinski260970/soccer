"""SureBet API: Bet365 Valuebets for football, hockey and basketball.

This adapter is intentionally read-only.  SureBet supplies the observed Bet365
price and its own value estimate.  We preserve that distinction in reporting:
a SureBet signal is not silently relabelled as an oddswatch model PLAY.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode

from .. import fetch

BASE = "https://api.apostasseguras.com/request"
DEFAULT_SPORTS = ("Football", "Hockey", "Basketball")
DEFAULT_BOOKS = ("bet365", "betfair", "orbitxch")


@dataclass(frozen=True)
class SurebetValue:
    id: str
    sport: str
    tournament: str
    teams: tuple[str, ...]
    kickoff: datetime | None
    selection: str
    market: str
    odds: float
    probability: float | None
    overvalue: float | None
    bookmaker: str = "bet365"
    back: bool = True
    commission: float = 0.0

    @property
    def event(self) -> str:
        return " vs ".join(self.teams) if self.teams else "Event unbekannt"

    @property
    def fair_odds(self) -> float | None:
        return 1.0 / self.probability if self.probability and self.probability > 0 else None

    @property
    def ev(self) -> float | None:
        return self.probability * self.odds - 1.0 if self.probability else None


def api_token() -> str:
    return (os.getenv("SUREBET_API_TOKEN") or "").strip()


def _num(value) -> float | None:
    try:
        x = float(value)
        return x
    except (TypeError, ValueError):
        return None


def _dt(value) -> datetime | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    # SureBet documents milliseconds since epoch.
    if x > 10_000_000_000:
        x /= 1000.0
    try:
        return datetime.fromtimestamp(x, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _iter_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _iter_dicts(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _iter_dicts(value)


def _selection(row: dict) -> tuple[str, str]:
    typ = row.get("type") if isinstance(row.get("type"), dict) else {}
    code = str(typ.get("type") or row.get("bet_type") or "").strip()
    condition = str(typ.get("condition") or "").strip()
    period = str(typ.get("period") or typ.get("periode") or "regularTime").strip()
    base = str(typ.get("base") or "overall").strip()
    teams = [str(x) for x in (row.get("teams") or [])]
    sport = str(row.get("sport_id") or "")

    t1 = teams[0] if len(teams) > 0 else "Team 1"
    t2 = teams[1] if len(teams) > 1 else "Team 2"

    period_labels = {
        "regularTime": "reguläre Spielzeit",
        "fullTime": "gesamtes Spiel",
        "match": "gesamtes Spiel",
        "1h": "1. Halbzeit",
        "2h": "2. Halbzeit",
        "q1": "1. Viertel",
        "q2": "2. Viertel",
        "q3": "3. Viertel",
        "q4": "4. Viertel",
        "p1": "1. Drittel",
        "p2": "2. Drittel",
        "p3": "3. Drittel",
    }
    period_text = period_labels.get(period, period)

    def _total_unit() -> str:
        return "Punkte" if sport == "Basketball" else "Tore"

    def _base_label() -> str:
        b = base.casefold()
        if b in {"overall", "total", "match", ""}:
            return f"Gesamt-{_total_unit()}"
        if b in {"team1", "home", "1", "first"}:
            return f"{t1} Teamtotal"
        if b in {"team2", "away", "2", "second"}:
            return f"{t2} Teamtotal"
        if "team1" in b or "home" in b:
            return f"{t1} Teamtotal"
        if "team2" in b or "away" in b:
            return f"{t2} Teamtotal"
        return base

    labels = {
        "win1": f"{t1} Sieg",
        "win2": f"{t2} Sieg",
        "winOnly1": f"{t1} Sieg (2-Wege)",
        "winOnly2": f"{t2} Sieg (2-Wege)",
        "draw": "Unentschieden",
        "win1RetX": f"{t1} DNB (bei Remis Einsatz zurück)",
        "win2RetX": f"{t2} DNB (bei Remis Einsatz zurück)",
        "yes": "Ja",
        "no": "Nein",
        "ah1": f"{t1} Asian Handicap {condition}".strip(),
        "ah2": f"{t2} Asian Handicap {condition}".strip(),
        "eh1": f"{t1} Europäisches Handicap {condition}".strip(),
        "ehx": f"Unentschieden · Europäisches Handicap {condition}".strip(),
        "eh2": f"{t2} Europäisches Handicap {condition}".strip(),
    }

    if code == "over":
        selection = f"{_base_label()} Über {condition}".strip()
    elif code == "under":
        selection = f"{_base_label()} Unter {condition}".strip()
    else:
        selection = labels.get(code, code or "Markt unbekannt")

    if code in {"win1", "win2", "draw"}:
        market_name = "3-Wege-Sieg"
    elif code in {"winOnly1", "winOnly2"}:
        market_name = "2-Wege-Sieg"
    elif code in {"win1RetX", "win2RetX"}:
        market_name = "Draw No Bet"
    elif code in {"ah1", "ah2"}:
        market_name = "Asian Handicap"
    elif code in {"eh1", "ehx", "eh2"}:
        market_name = "Europäisches Handicap"
    elif code in {"over", "under"}:
        market_name = _base_label()
    else:
        market_name = code or "Markt"

    market = f"{market_name} · {period_text}"
    return selection, market


def parse(data) -> list[SurebetValue]:
    out: list[SurebetValue] = []
    seen: set[tuple] = set()
    for row in _iter_dicts(data):
        # Bet objects are documented with bk/value/sport_id/teams/type.
        bookmaker = str(row.get("bk") or "").lower()
        if bookmaker not in DEFAULT_BOOKS:
            continue
        odds = _num(row.get("value"))
        if not odds or odds <= 1.0:
            continue
        sport = str(row.get("sport_id") or "")
        if sport not in DEFAULT_SPORTS:
            continue
        teams_raw = row.get("teams")
        teams = tuple(str(x) for x in teams_raw) if isinstance(teams_raw, list) else ()
        selection, market = _selection(row)
        probability = _num(row.get("probability"))
        if probability is not None and not (0 < probability < 1):
            probability = None
        overvalue = _num(row.get("overvalue"))
        key = (str(row.get("id") or ""), sport, teams, selection, bookmaker, round(odds, 6))
        if key in seen:
            continue
        seen.add(key)
        out.append(SurebetValue(
            id=str(row.get("id") or row.get("event_id") or ""),
            sport=sport,
            tournament=str(row.get("tournament") or ""),
            teams=teams,
            kickoff=_dt(row.get("time")),
            selection=selection,
            market=market,
            odds=odds,
            probability=probability,
            overvalue=overvalue,
            bookmaker=bookmaker,
            back=bool(typ.get("back", True)) if isinstance((typ := row.get("type")), dict) else True,
            commission=float(row.get("commission") or 0.0),
        ))
    out.sort(key=lambda x: (
        x.kickoff or datetime.max.replace(tzinfo=timezone.utc),
        -(x.ev if x.ev is not None else -999),
    ))
    return out


def fetch_valuebets(sports: tuple[str, ...] = DEFAULT_SPORTS,
                    books: tuple[str, ...] = DEFAULT_BOOKS,
                    limit: int = 100
                    ) -> tuple[list[SurebetValue], str | None]:
    token = api_token()
    if not token:
        return [], "SUREBET_API_TOKEN nicht gesetzt"
    wanted = tuple(s for s in sports if s in DEFAULT_SPORTS)
    if not wanted:
        return [], "Keine unterstützte Sportart angefordert"
    wanted_books = tuple(b for b in books if b in DEFAULT_BOOKS)
    if not wanted_books:
        return [], "Keine unterstützte Buchmacherquelle angefordert"
    params = {
        "product": "valuebets",
        "source": "|".join(wanted_books),
        "sport": "|".join(wanted),
        "limit": str(max(1, min(int(limit), 500))),
        "oddsFormat": "eu",
    }
    data, err = fetch.get_json(
        f"{BASE}?{urlencode(params, safe='|')}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
        retries=1,
    )
    if data is None:
        return [], f"SureBet API: {err or 'keine Antwort'}"
    return parse(data), None
