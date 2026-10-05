"""Attach football sportsbook offers; no exchange or binary-market fallback."""
from datetime import datetime, timezone
from . import pricing
from .selection import Offer
from .sources import apifootball


def attach_prices(fixtures, issues):
    soccer = [f for f in fixtures if f.sport == "soccer"]
    if not soccer:
        return
    if not apifootball.api_key():
        issues.append("APIKEY fehlt: keine Fußball-Buchmacherpreise abrufbar")
        return
    days, books = {}, {}
    for fx in soccer:
        g = fx.game
        day = g.kickoff.astimezone(timezone.utc).date().isoformat()
        if day not in days:
            days[day], err = apifootball.fixtures_on(day)
            if err:
                issues.append(err)
        match = apifootball.find_fixture(days[day], g.home.aliases(), g.away.aliases(), g.kickoff)
        if match is None:
            issues.append(f"API-Football: {g.title} nicht eindeutig zugeordnet")
            continue
        if match.id not in books:
            books[match.id], err = apifootball.odds(match.id)
            if err:
                issues.append(err)
        data = books[match.id]
        keys = ("home", "draw", "away")
        pinnacle = data.get("Pinnacle", {})
        if all(k in pinnacle for k in keys):
            fx.ref_probs = dict(zip(keys, pricing.devig([pinnacle[k] for k in keys])))
        obs = datetime.now(timezone.utc).isoformat()
        for side in keys:
            offers = []
            for book in ("Bet365", "Betfair"):
                odds = data.get(book, {}).get(side)
                if odds and odds > 1:
                    label = "Unentschieden (90 Min.)" if side == "draw" else f"{g.home.name if side == 'home' else g.away.name} Sieg (90 Min.)"
                    offers.append(Offer(g.title, g.kickoff.isoformat(), side, label, odds,
                                        book.lower(), obs, ref=f"apifootball:{match.id}:{side}", league=fx.league))
            if offers:
                fx.offers[side] = offers
