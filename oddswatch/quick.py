"""Schneller Fußball-Quotenwächter über API-Football."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path

from . import guard, pricing, report, steam, telegram
from .sources import apifootball

MIN_EV = 0.03
PLAYABLE = ("Bet365", "Betfair")
SOCCER_MARKET_STEAM_STATE = Path("data/journal/soccer_market_steam_history.json")

SUPPORTED_STEAM_LEAGUES = {
    "germany": {"bundesliga", "2. bundesliga"},
    "england": {"premier league", "championship"},
    "spain": {"la liga"},
    "italy": {"serie a"},
    "france": {"ligue 1"},
    "netherlands": {"eredivisie"},
    "portugal": {"primeira liga", "liga portugal", "liga portugal betclic"},
    "belgium": {"jupiler pro league", "pro league"},
    "turkey": {"süper lig", "super lig"},
    "türkiye": {"süper lig", "super lig"},
    "scotland": {"premiership", "scottish premiership"},
    "greece": {"super league 1", "super league greece"},
    "austria": {"bundesliga", "admiral bundesliga"},
    "switzerland": {"super league", "swiss super league"},
    "sweden": {"allsvenskan"},
    "norway": {"eliteserien"},
    "denmark": {"superliga", "superligaen"},
    "poland": {"ekstraklasa"},
}


def _supported_fixture(fx: apifootball.ApiFixture) -> bool:
    country = fx.country.casefold().strip()
    league = fx.league.casefold().strip()
    return league in SUPPORTED_STEAM_LEAGUES.get(country, set())


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


def full_market_scan(day: str | None = None, min_ev: float = MIN_EV, top: int = 25,
                     send: bool = False, days: int = 1,
                     leagues: tuple[str, ...] = (), countries: tuple[str, ...] = (),
                     supported_only: bool = False) -> list[str]:
    """Alle API-Football-Spiele eines Tages gegen Pinnacle fair scannen.

    Pinnacle wird je Marktgruppe de-vigged. Bet365/Betfair sind die spielbaren
    Preise. Das ist ein Marktpreis-Scan, kein unabhängiges Prognosemodell.
    """
    start = datetime.fromisoformat(day).date() if day else datetime.now(timezone.utc).date()
    fixtures: list[apifootball.ApiFixture] = []
    for offset in range(max(1, days)):
        d = (start + timedelta(days=offset)).isoformat()
        daily, err = apifootball.fixtures_on(d)
        if err:
            raise RuntimeError(err)
        fixtures.extend(daily)

    if supported_only:
        fixtures = [fx for fx in fixtures if _supported_fixture(fx)]
    if leagues:
        wanted = {x.casefold() for x in leagues}
        fixtures = [fx for fx in fixtures if fx.league.casefold() in wanted]
    if countries:
        wanted_countries = {x.casefold() for x in countries}
        fixtures = [fx for fx in fixtures if fx.country.casefold() in wanted_countries]
    day_label = start.isoformat() if days <= 1 else f"{start.isoformat()}–{(start + timedelta(days=max(1, days)-1)).isoformat()}"

    rows: list[dict] = []
    steam_records: list[dict] = []
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

            book_probs: dict[str, dict[str, float]] = {"Pinnacle": fair}
            for book in PLAYABLE:
                bm = books.get(book, {})
                if all(k in bm and bm[k] > 1 for k in grp):
                    book_probs[book] = dict(zip(grp, pricing.devig([bm[k] for k in grp])))

            for market in grp:
                odds_by_book = {
                    book: books.get(book, {}).get(market)
                    for book in ("Pinnacle",) + PLAYABLE
                    if books.get(book, {}).get(market)
                }
                probs_by_book = {
                    book: pp[market]
                    for book, pp in book_probs.items()
                    if market in pp
                }
                steam_records.append({
                    "key": f"{fx.id}|{market}",
                    "event": f"{fx.home} – {fx.away}",
                    "kickoff": fx.kickoff.isoformat(),
                    "league": fx.league,
                    "market": market,
                    "selection": _selection(fx, market),
                    "probs": probs_by_book,
                    "odds": odds_by_book,
                })

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
        f"API-Football FULLSCAN {day_label}: {len(fixtures)} Fixture(s)",
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

    # Bei manuellen/push-ausgeloesten Scans immer einen kompakten Telegram-
    # Bericht senden. Geplante 15-Minuten-Laeufe bleiben still, solange es
    # kein PRE-STEAM-Signal gibt, damit der Kanal nicht zugespammt wird.
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if send and event_name != "schedule":
        lines = [
            f"📊 SOCCER MARKET SCAN {report.stand()}",
            f"{day_label} · {len(fixtures)} Spiele · {odds_with_data} mit Odds",
            f"Treffer ab {min_ev * 100:.1f}% Markt-EV: {len(rows)}",
            "⚠️ WATCH: Pinnacle de-vigged Referenz, kein unabhaengiges Modell/kein PLAY.",
        ]
        if rows:
            for r in rows[:8]:
                fx = r["fx"]
                lines += [
                    "",
                    f"• {report._league(fx.league)} · {fx.kickoff.astimezone(timezone.utc):%H:%M} UTC",
                    f"{fx.home} – {fx.away}",
                    f"{r['selection']} @ {r['odds']:.2f} ({r['book']})",
                    f"Pinnacle fair {r['fair']:.2f} · Edge {r['edge'] * 100:+.1f}pp · EV {r['ev'] * 100:+.1f}%",
                ]
        else:
            lines += ["", "Keine Markt-Treffer ueber dem Filter."]
        tr = telegram.send("\n".join(lines))
        log.append("FULLSCAN Telegram: " + (
            f"gesendet {tr['message_ids']}" if tr["sent"] else f"NICHT gesendet – {tr['error']}"
        ))

    signals = steam.update_many(steam_records, path=SOCCER_MARKET_STEAM_STATE)
    if signals:
        signals.sort(key=lambda s: (-s["score"], -abs(s["lead_move"])))
        log += ["", f"⚡ PRE-STEAM: {len(signals)} Frühindikator(en)"]
        for s in signals[:12]:
            odds = s.get("odds") or {}
            slow = " | ".join(
                f"{b} {odds[b]:.2f}" for b in ("Bet365", "Betfair") if b in odds
            ) or "Slow-Book ohne Quote"
            log.append(
                f"{s['direction']} {s['event']} | {s['selection']} | "
                f"Pinnacle Δ {s['lead_move']*100:+.1f}pp in {s['minutes']}m | "
                f"Lead-vs-Slow {s['lag']*100:+.1f}pp | {slow}"
            )
        if send:
            lines = [
                f"⚡ PRE-STEAM {report.stand()}",
                "Frühindikator: Pinnacle bewegt sich vor Bet365/Betfair. Kein automatisches PLAY.",
            ]
            for s in signals[:8]:
                odds = s.get("odds") or {}
                slow = " | ".join(
                    f"{b} {odds[b]:.2f}" for b in ("Bet365", "Betfair") if b in odds
                ) or "keine Slow-Book-Quote"
                arrow = "📉 Quote dürfte kürzer werden" if s["direction"] == "SHORTENING" else "📈 Quote dürfte länger werden"
                lines += [
                    "",
                    f"{arrow} · {report._league(s['league'])}",
                    f"🆚 {s['event']}",
                    f"➡️ {s['selection']}",
                    f"   Pinnacle {s['lead_move']*100:+.1f}pp / {s['minutes']}m · "
                    f"Lead-vs-Slow {s['lag']*100:+.1f}pp",
                    f"   {slow}",
                ]
            tr = telegram.send("\n".join(lines))
            log.append("PRE-STEAM Telegram: " + (
                f"gesendet {tr['message_ids']}" if tr["sent"] else f"NICHT gesendet – {tr['error']}"
            ))
    if errors:
        log.append(f"API-Hinweise: {len(errors)} Odds-Abruf(e) fehlgeschlagen")
    return log


def run(j=None, send=False, days=7, now=None, full=False, leagues=(), countries=(), start_day=None,
        supported_only=False):
    if full:
        return full_market_scan(
            day=start_day, send=send, days=days,
            leagues=tuple(leagues), countries=tuple(countries),
            supported_only=supported_only,
        )
    return guard.run(j, send=send, now=now, strict=True)
