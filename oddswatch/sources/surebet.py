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
    period = str(typ.get("period") or "regularTime").strip()
    base = str(typ.get("base") or "overall").strip()
    teams = [str(x) for x in (row.get("teams") or [])]

    labels = {
        "win1": teams[0] if len(teams) > 0 else "Team 1",
        "win2": teams[1] if len(teams) > 1 else "Team 2",
        "draw": "Unentschieden",
        "win1RetX": (teams[0] if teams else "Team 1") + " DNB",
        "win2RetX": (teams[1] if len(teams) > 1 else "Team 2") + " DNB",
        "over": f"Over {condition}".strip(),
        "under": f"Under {condition}".strip(),
        "yes": "Ja",
        "no": "Nein",
        "ah1": f"{teams[0] if teams else 'Team 1'} AH {condition}".strip(),
        "ah2": f"{teams[1] if len(teams) > 1 else 'Team 2'} AH {condition}".strip(),
        "eh1": f"{teams[0] if teams else 'Team 1'} EH {condition}".strip(),
        "ehx": f"Unentschieden EH {condition}".strip(),
        "eh2": f"{teams[1] if len(teams) > 1 else 'Team 2'} EH {condition}".strip(),
    }
    selection = labels.get(code, code or "Markt unbekannt")
    market = " · ".join(x for x in (period, base, code, condition) if x)
    return selection, market


def parse(data) -> list[SurebetValue]:
    out: list[SurebetValue] = []
    seen: set[tuple] = set()
    for row in _iter_dicts(data):
        # Bet objects are documented with bk/value/sport_id/teams/type.
        if str(row.get("bk") or "").lower() != "bet365":
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
        key = (str(row.get("id") or ""), sport, teams, selection, round(odds, 6))
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
        ))
    out.sort(key=lambda x: (
        x.kickoff or datetime.max.replace(tzinfo=timezone.utc),
        -(x.ev if x.ev is not None else -999),
    ))
    return out


def fetch_valuebets(sports: tuple[str, ...] = DEFAULT_SPORTS, limit: int = 100
                    ) -> tuple[list[SurebetValue], str | None]:
    token = api_token()
    if not token:
        return [], "SUREBET_API_TOKEN nicht gesetzt"
    wanted = tuple(s for s in sports if s in DEFAULT_SPORTS)
    if not wanted:
        return [], "Keine unterstützte Sportart angefordert"
    params = {
        "product": "valuebets",
        "source": "bet365",
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
