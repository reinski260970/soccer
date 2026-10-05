"""Schneller Fußball-Quotenwächter über API-Football."""

from __future__ import annotations

from datetime import datetime, timezone

from . import guard, pricing
from .sources import apifootball

MIN_EV = 0.03
PLAYABLE = ("Bet365", "Betfair")


def _groups(pinnacle: dict[str, float]) -> list[list[str]]:
    out: list[list[str]] = []
    if all(k in pinnacle for k in ("home", "draw", "away")):
        out.append(["home", "draw", "away"])
    totals: dict[str, list[str]] = {}
    for k in pinnacle:
        if k.startswith("O"):
            line = k[1:]
            u = f"U{line}:no"
            if u in pinnacle:
                totals[line] = [k, u]
    out.extend(totals[k] for k in sorted(totals, key=lambda x: float(x)))
    return out


def _selection(fx: apifootball.ApiFixture, market: str) -> str:
    if market == "home":
        return f"{fx.home} Sieg (90 Min.)"
    if market == "draw":
        return "Unentschieden (90 Min.)"
    if market == "away":
        return f"{fx.away} Sieg (90 Min.)"
    if market.startswith("O"):
        return f"Über {market[1:]} Tore"
    if market.startswith("U"):
        return f"Unter {market[1:-3]} Tore"
    return market


def full_market_scan(day: str | None = None, min_ev: float = MIN_EV, top: int = 25) -> list[str]:
    """Alle API-Football-Spiele eines Tages gegen Pinnacle fair scannen.

    Pinnacle wird je Marktgruppe de-vigged. Bet365/Betfair sind die spielbaren
    Preise. Das ist ein Marktpreis-Scan, kein unabhängiges Prognosemodell.
    """
    day = day or datetime.now(timezone.utc).date().isoformat()
    fixtures, err = apifootball.fixtures_on(day)
    if err:
        raise RuntimeError(err)

    rows: list[dict] = []
    api_ok = 1
    api_total = 1
    odds_with_data = 0
    quotes = 0
    errors: list[str] = []

    for fx in fixtures:
        api_total += 1
        books, err = apifootball.odds(fx.id)
        if err:
            errors.append(f"{fx.home} – {fx.away}: {err}")
            continue
        api_ok += 1
        if books:
            odds_with_data += 1
        pinnacle = books.get("Pinnacle", {})
        for grp in _groups(pinnacle):
            probs = pricing.devig([pinnacle[k] for k in grp])
            fair = dict(zip(grp, probs))
            for market in grp:
                best = None
                for book in PLAYABLE:
                    o = books.get(book, {}).get(market)
                    if o and o > 1:
                        quotes += 1
                        if best is None or o > best[1]:
                            best = (book, o)
                if not best:
                    continue
                p = fair[market]
                ev = p * best[1] - 1
                if ev >= min_ev:
                    rows.append({
                        "ev": ev, "edge": p - 1 / best[1], "p": p,
                        "fair": 1 / p, "book": best[0], "odds": best[1],
                        "market": market, "selection": _selection(fx, market),
                        "fx": fx,
                    })

    rows.sort(key=lambda r: r["ev"], reverse=True)
    log = [
        f"API-Football FULLSCAN {day}: {len(fixtures)} Fixture(s)",
        f"API: {api_ok}/{api_total} Request(s) OK | {odds_with_data} Fixture(s) mit Odds | "
        f"{quotes} Bet365/Betfair Marktquote(n)",
        f"Filter: EV >= {min_ev * 100:.1f}% gegen Pinnacle de-vigged fair "
        f"(Marktpreis-Scan, kein unabhängiges Modell)",
        f"Treffer: {len(rows)}",
    ]
    for r in rows[:top]:
        fx = r["fx"]
        log.append(
            f"{fx.league} | {fx.kickoff.astimezone(timezone.utc):%H:%M} UTC | "
            f"{fx.home} – {fx.away} | {r['selection']} | {r['book']} {r['odds']:.2f} | "
            f"Pinnacle fair {r['fair']:.2f} | Edge {r['edge'] * 100:+.2f}pp | EV {r['ev'] * 100:+.2f}%"
        )
    if len(rows) > top:
        log.append(f"... {len(rows) - top} weitere Treffer")
    if errors:
        log.append(f"API-Hinweise: {len(errors)} Odds-Abruf(e) fehlgeschlagen")
    return log


def run(j=None, send=False, days=7, now=None, full=False):
    if full:
        return full_market_scan()
    return guard.run(j, send=send, now=now, strict=True)
