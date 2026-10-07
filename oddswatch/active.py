"""Provider eligibility for new alerts; historical journal rows remain intact."""
from __future__ import annotations

import os

SUPPORTED = {
    "bet365", "betfair", "orbit", "pinnacle",
    "unibet", "bwin", "1xbet", "10bet",
}


def _on(name: str) -> bool:
    return (os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"})


def eligible(row):
    source = (row.get("source") or row.get("bookmaker") or "").lower()
    ref = str(row.get("ref") or "")
    if source == "kalshi":
        return _on("KALSHI_EXECUTABLE") and ref.startswith("kalshi:")
    if source == "polymarket":
        return _on("POLYMARKET_EXECUTABLE") and ref.startswith("polymarket:")
    return source in SUPPORTED
