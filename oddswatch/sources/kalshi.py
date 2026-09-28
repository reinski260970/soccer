"""Kalshi: öffentliche Trade-API (ohne Login lesbar) und Make-Snapshot-Import.

Endpunkt: https://external-api.kalshi.com/trade-api/v2/events
  ?series_ticker=KXBUNDESLIGAGAME&status=open&with_nested_markets=true
Fußball-Märkte lösen nach 90 Minuten + Nachspielzeit auf (1X2).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime

API = "https://external-api.kalshi.com/trade-api/v2"

SOCCER_SERIES = {
    "KXBUNDESLIGAGAME": "Bundesliga",
    "KXUCLGAME": "Champions League",
    "KXUELGAME": "Europa League",
    "KXEPLGAME": "Premier League",
}
OTHER_SERIES = {"KXNHLGAME": "NHL", "KXNBAGAME": "NBA", "KXNFLGAME": "NFL"}


def events_url(series: str, status: str = "open") -> str:
    return f"{API}/events?series_ticker={series}&status={status}&with_nested_markets=true&limit=200"


@dataclass
class KalshiQuote:
    event: str          # z. B. "Stuttgart vs Dortmund"
    event_ticker: str
    ticker: str
    outcome: str        # "home" | "draw" | "away" | Teamname
    label: str
    yes_bid: float      # 0..1
    yes_ask: float      # 0..1
    volume: float
    liquidity: float
    observed_at: str
    kickoff: str = ""

    @property
    def mid(self) -> float:
        return (self.yes_bid + self.yes_ask) / 2 if self.yes_bid > 0 else self.yes_ask


_RULE_RE = re.compile(r"the (.+?) vs (.+?) professional", re.I)


def _event_from_rules(rules: str) -> tuple[str, str] | None:
    m = _RULE_RE.search(rules or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else None


def _outcome(label: str, home: str, away: str) -> str:
    low = label.lower()
    if low.startswith("tie"):
        return "draw"
    if low.startswith(home.lower()):
        return "home"
    if low.startswith(away.lower()):
        return "away"
    return label


def parse_api_events(payload: dict | str) -> list[KalshiQuote]:
    """Antwort von /events?with_nested_markets=true parsen."""
    data = json.loads(payload) if isinstance(payload, str) else payload
    out = []
    for ev in data.get("events", []):
        for m in ev.get("markets", []):
            teams = _event_from_rules(m.get("rules_primary", "")) or ("", "")
            label = m.get("yes_sub_title") or m.get("title", "")
            bid = _price(m, "yes_bid")
            ask = _price(m, "yes_ask")
            out.append(KalshiQuote(
                event=f"{teams[0]} vs {teams[1]}" if teams[0] else ev.get("title", ""),
                event_ticker=ev.get("event_ticker", ""), ticker=m.get("ticker", ""),
                outcome=_outcome(label, *teams) if teams[0] else label, label=label,
                yes_bid=bid, yes_ask=ask, volume=float(m.get("volume", 0) or 0),
                liquidity=float(m.get("liquidity", 0) or 0) / 100,
                observed_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
                kickoff=m.get("expected_expiration_time") or m.get("close_time", ""),
            ))
    return out


def _price(m: dict, key: str) -> float:
    if m.get(key + "_dollars") not in (None, ""):
        return float(m[key + "_dollars"])
    v = m.get(key)
    return float(v) / 100 if v not in (None, "") else 0.0


def parse_make_snapshots(records: list[dict]) -> list[KalshiQuote]:
    """Records aus dem Make-Data-Store 'SOCCER Kalshi Snapshots und
    Preisvergleich' (Format: {key, data:{ticker,title,ask,bid,size,volume,
    rules,observed_at}}). Batch-/News-Einträge werden übersprungen."""
    out = []
    for r in records:
        d = r.get("data", r)
        if not d.get("ticker", "").startswith("KX") or "ask" not in d:
            continue
        teams = _event_from_rules(d.get("rules", ""))
        if not teams:
            continue
        out.append(KalshiQuote(
            event=f"{teams[0]} vs {teams[1]}", event_ticker=d["ticker"].rsplit("-", 1)[0],
            ticker=d["ticker"], outcome=_outcome(d.get("title", ""), *teams),
            label=d.get("title", ""), yes_bid=float(d.get("bid") or 0),
            yes_ask=float(d.get("ask") or 0), volume=float(d.get("volume") or 0),
            liquidity=float(d.get("size") or 0), observed_at=d.get("observed_at", ""),
        ))
    return out


def group_1x2(quotes: list[KalshiQuote]) -> dict[str, dict[str, KalshiQuote]]:
    """event_ticker -> {'home','draw','away'} (nur vollständige Events)."""
    ev: dict[str, dict[str, KalshiQuote]] = {}
    for q in quotes:
        ev.setdefault(q.event_ticker, {})[q.outcome] = q
    return {k: v for k, v in ev.items() if {"home", "draw", "away"} <= v.keys()}
