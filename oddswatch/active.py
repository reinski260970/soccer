"""Provider eligibility for new alerts; historical journal rows remain intact."""
SUPPORTED = {"bet365", "betfair", "orbit", "pinnacle", "kalshi"}


def eligible(row):
    return (row.get("source") or row.get("bookmaker") or "").lower() in SUPPORTED
