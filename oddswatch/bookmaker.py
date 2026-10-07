"""Attach market prices after model fair odds have been computed.

Sources:
- Football: API-Football sportsbook odds (Pinnacle ref, Bet365/Betfair offers)
- Hockey: API-Hockey sportsbook odds, including European leagues where covered
- NFL/NHL/NBA: public Polymarket and Kalshi prices as extra references; they are
  PLAY-eligible only when their explicit *_EXECUTABLE switch is enabled.
"""
from datetime import datetime, timezone

from . import pricing
from .selection import Offer
from .sources import apifootball, apihockey, kalshi, polymarket


def _attach_soccer(fixtures, issues):
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
        match = apifootball.find_fixture(days.get(day, []), g.home.aliases(), g.away.aliases(), g.kickoff)
        if match is None:
            issues.append(f"API-Football: {g.title} nicht eindeutig zugeordnet")
            continue
        if match.id not in books:
            books[match.id], err = apifootball.odds(match.id)
            if err:
                issues.append(err)
        data = books.get(match.id, {})
        keys = ("home", "draw", "away")
        pinnacle = data.get("Pinnacle", {})
        if all(k in pinnacle for k in keys):
            fx.ref_probs = dict(zip(keys, pricing.devig([pinnacle[k] for k in keys])))
        obs = datetime.now(timezone.utc).isoformat()
        for side in keys:
            offers = []
            pin_odd = data.get("Pinnacle", {}).get(side)
            if pin_odd and pin_odd > 1:
                label = ("Unentschieden (90 Min.)" if side == "draw" else
                         f"{g.home.name if side == 'home' else g.away.name} Sieg (90 Min.)")
                offers.append(Offer(
                    g.title, g.kickoff.isoformat(), side, label, pin_odd, "pinnacle", obs,
                    ref=f"apifootball:{match.id}:{side}:pinnacle", league=fx.league,
                    executable=False,
                ))
            raw_exec = {
                book: data.get(book, {}).get(side)
                for book in ("Bet365", "Betfair")
                if data.get(book, {}).get(side) and data.get(book, {}).get(side) > 1
            }
            fair_ref = (1.0 / fx.ref_probs[side]) if fx.ref_probs.get(side) else None
            for book, odds in raw_exec.items():
                extreme = bool(fair_ref and odds / fair_ref - 1.0 > 0.20)
                peer_confirmed = any(
                    other != book and other_odds >= odds * 0.90
                    for other, other_odds in raw_exec.items()
                )
                if extreme and not peer_confirmed:
                    issues.append(
                        f"API-Football: Preis-Outlier verworfen ({g.title}, {side}, "
                        f"{book} {odds:.2f} vs Pinnacle fair {fair_ref:.2f}); "
                        "zweiter Ausführungsmarkt bestätigt nicht"
                    )
                    continue
                label = ("Unentschieden (90 Min.)" if side == "draw" else
                         f"{g.home.name if side == 'home' else g.away.name} Sieg (90 Min.)")
                offers.append(Offer(
                    g.title, g.kickoff.isoformat(), side, label, odds, book.lower(), obs,
                    ref=f"apifootball:{match.id}:{side}", league=fx.league, executable=True,
                ))
            if offers:
                fx.offers[side] = offers


def _attach_espn_reference(fixtures):
    """Persist raw ESPN/DraftKings-style scoreboard moneylines as reference-only
    quotes. They may be compared with model fair odds but can never create PLAY."""
    obs = datetime.now(timezone.utc).isoformat()
    for fx in fixtures:
        r = getattr(fx.game, "ref_line", None) or {}
        for side, key in (("home", "ml_home"), ("draw", "ml_draw"), ("away", "ml_away")):
            odd = r.get(key)
            if not odd or odd <= 1 or side not in fx.probs:
                continue
            if side == "draw":
                label = "Unentschieden"
            else:
                team = fx.game.home.name if side == "home" else fx.game.away.name
                label = f"{team} ML"
            fx.offers.setdefault(side, []).append(Offer(
                event=fx.game.title, kickoff=fx.game.kickoff.isoformat(), market=side,
                selection=label, odds=float(odd), source="espn_ref", observed_at=obs,
                ref=f"espn:{fx.game.id}:{side}", league=fx.league, executable=False,
            ))


def _capture_and_filter_market_quotes(fixtures):
    """Keep every observed market quote for comparison, but expose only executable
    quotes to candidate/PLAY selection."""
    for fx in fixtures:
        fx.market_quotes = {}
        for side, offers in list(fx.offers.items()):
            if offers:
                fx.market_quotes[side] = list(offers)
            fx.offers[side] = [o for o in offers if getattr(o, "executable", True)]
            if not fx.offers[side]:
                del fx.offers[side]


def attach_prices(fixtures, issues):
    _attach_espn_reference(fixtures)
    _attach_soccer(fixtures, issues)

    # API-Hockey is the primary fix for the missing Liiga/SHL/ICEHL/NHL prices.
    try:
        apihockey.attach(fixtures, issues)
    except Exception as exc:
        issues.append(f"API-Hockey: {type(exc).__name__}: {exc}")

    # Prediction markets are additional public price/reference sources. Their
    # adapters decide whether the installation may treat a quote as executable.
    for name, source in (("Polymarket", polymarket), ("Kalshi", kalshi)):
        try:
            source.attach(fixtures, issues)
        except Exception as exc:
            issues.append(f"{name}: {type(exc).__name__}: {exc}")

    _capture_and_filter_market_quotes(fixtures)
