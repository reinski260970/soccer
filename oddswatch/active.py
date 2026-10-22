"""Provider eligibility for new alerts; historical journal rows remain intact."""
from __future__ import annotations

SUPPORTED = {
    "bet365", "betfair", "orbit", "pinnacle",
    "unibet", "bwin", "1xbet", "10bet",
}


def eligible(row):
    # Kalshi/Polymarket are removed as sources; their historical journal rows
    # stay untouched but are never eligible for new alerts.
    source = (row.get("source") or row.get("bookmaker") or "").lower()
    return source in SUPPORTED
