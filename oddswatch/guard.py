"""Quotenwächter: CEO-Freigaben und Watchlist gegen Pinnacle, Bet365, Betfair.

Beobachtet alles, was der CEO ausgibt (data/journal/watchlist.json plus offene
Freigaben aus dem Journal), in den Fußball-Märkten 1X2 und Über/Unter. Quelle
ist API-Football. Pinnacle (de-vigged) dient als faire Referenz, Bet365 und
Betfair (Sportsbook, nicht Exchange) sind die spielbaren Preise.

Meldet per Telegram, einmal je Tipp, Buchmacher und Preisstufe (+5 %):
- SPIELBAR: Bet365/Betfair ≥ spielbare Mindestquote (EV ≥ 3 % gegen Pinnacle fair)
- WARNUNG (nur PLAY): Pinnacle fair liegt über dem Freigabepreis – der Markt
  hat sich gegen die Freigabe bewegt. Der Wächter warnt nur, der CEO entscheidet.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import pricing, report, telegram
from .journal import Journal
from .news import Target, load_targets
from .sources import apifootball

NOT_SOCCER = {"nfl", "nhl", "nba", "del", "nl", "shl", "liiga", "khl", "icehl"}
PLAYABLE = ("Bet365", "Betfair")
MIN_EV = 0.03
HORIZON_DAYS = 14
STATE = Path("data/journal/odds_guard.json")
STATUS = Path("data/journal/odds_guard_status.txt")


def _group(market: str) -> list[str] | None:
    """Märkte, die gemeinsam de-vigged werden."""
    if market in ("home", "draw", "away"):
        return ["home", "draw", "away"]
    if market.startswith("O"):
        L = market[1:]
        return [f"O{L}", f"U{L}:no"]
    if market.startswith("U") and market.endswith(":no"):
        L = market[1:-3]
        return [f"O{L}", f"U{L}:no"]
    return None


def fair_prob(book: dict[str, float], market: str) -> float | None:
    grp = _group(market)
    if not grp or any(k not in book for k in grp):
        return None
    return dict(zip(grp, pricing.devig([book[k] for k in grp])))[market]


def assess(t: Target, books: dict[str, dict[str, float]]) -> dict | None:
    """Bewertung eines CEO-Tipps; None ohne Pinnacle-Referenz."""
    p = fair_prob(books.get("Pinnacle", {}), t.market)
    if p is None:
        return None
    prices = {b: books[b][t.market] for b in PLAYABLE if t.market in books.get(b, {})}
    best = max(prices.items(), key=lambda x: x[1]) if prices else None
    return {"p": p, "fair": 1 / p, "min": pricing.min_odds(p, MIN_EV), "prices": prices,
            "best": best, "pinnacle": books["Pinnacle"].get(t.market),
            "playable": bool(best) and best[1] >= pricing.min_odds(p, MIN_EV),
            "against": t.status == "PLAY" and 1 / p > t.odds}


def _head(t: Target) -> str:
    return f"{report._league(t.league)} · {report._kick(t.kickoff)}"


def _prices(a: dict) -> str:
    return " | ".join(f"{b} {report._q(o)}" for b, o in a["prices"].items()) or "keine Bet365/Betfair-Quote"


def alert_text(t: Target, a: dict, kind: str) -> list[str]:
    if kind == "play":
        b, o = a["best"]
        head = f"✅ SPIELBAR bei {b} · {_head(t)}"
        tail = f"   EV {report._pct(pricing.ev(a['p'], o))} gegen Pinnacle fair"
    else:
        head = f"⚠️ MARKT GEGEN FREIGABE · {_head(t)}"
        tail = (f"   Freigabe-Preis {report._q(t.odds)} liegt unter Pinnacle fair – "
                f"Freigabe prüfen, Entscheidung beim CEO")
    return ["", head, f"🆚 {t.event} ({t.status})", f"➡️ {t.selection}",
            f"   {_prices(a)}",
            f"   Pinnacle {report._q(a['pinnacle'])} → fair {report._q(a['fair'])} | "
            f"spielbar ab {report._q(a['min'])}", tail]


def _key(kind: str, t: Target, a: dict) -> str:
    if kind == "play":
        b, o = a["best"]
        return f"play|{t.event}|{t.market}|{b}|{int(o * 20)}"
    return f"against|{t.event}|{t.market}"


def _targets(j: Journal, now: datetime) -> list[Target]:
    out, seen = [], set()
    for t in load_targets(j):
        try:
            ko = datetime.fromisoformat(t.kickoff)
        except (TypeError, ValueError):
            continue
        if (t.league in NOT_SOCCER or (t.event, t.market) in seen or not _group(t.market)
                or not now < ko <= now + timedelta(days=HORIZON_DAYS)):
            continue
        seen.add((t.event, t.market))
        out.append(t)
    return out


def run(j: Journal | None = None, send: bool = False, now: datetime | None = None, strict: bool = False) -> list[str]:
    j = j or Journal()
    now = now or datetime.now(timezone.utc)
    if not apifootball.api_key():
        log = [f"Quotenwächter {report.stand(now)}: APIKEY (API-Football) nicht gesetzt – übersprungen"]
        STATUS.parent.mkdir(parents=True, exist_ok=True)
        STATUS.write_text(log[0] + "\n", encoding="utf-8")
        if strict:
            raise RuntimeError(log[0])
        return log
    failures = []
    targets = _targets(j, now)
    log = [f"Quotenwächter {report.stand(now)}: {len(targets)} Fußball-Tipp(s) des CEO "
           f"gegen Pinnacle/Bet365/Betfair"]
    days: dict[str, list] = {}
    odds_cache: dict[int, dict] = {}
    msgs: list[tuple[str, list[str]]] = []
    for t in targets:
        ko = datetime.fromisoformat(t.kickoff).astimezone(timezone.utc)
        day = f"{ko:%Y-%m-%d}"
        if day not in days:
            days[day], err = apifootball.fixtures_on(day)
            if err:
                log.append(f"  Hinweis: {err}")
                failures.append("API-Football-Abruf fehlgeschlagen")
        fx = apifootball.find_fixture(days[day], t.home, t.away, ko)
        if not fx:
            log.append(f"  {t.event}: bei API-Football nicht eindeutig gefunden")
            continue
        if fx.id not in odds_cache:
            odds_cache[fx.id], err = apifootball.odds(fx.id)
            if err:
                log.append(f"  Hinweis: {err}")
                failures.append("API-Football-Abruf fehlgeschlagen")
        a = assess(t, odds_cache[fx.id])
        if not a:
            log.append(f"  {t.event} – {t.selection}: noch keine Pinnacle-Quote")
            continue
        state = "SPIELBAR" if a["playable"] else "unter Mindestquote"
        log.append(f"  {t.status} {t.event} – {t.selection}: {_prices(a)} | Pinnacle fair "
                   f"{a['fair']:.2f}, spielbar ab {a['min']:.2f} → {state}"
                   + ("  [Markt gegen Freigabe]" if a["against"] else ""))
        for kind in ("play", "against"):
            if a["playable" if kind == "play" else "against"]:
                msgs.append((_key(kind, t, a), alert_text(t, a, kind)))
    try:
        seen = set(json.loads(STATE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        seen = set()
    new = [(k, m) for k, m in msgs if k not in seen]
    if send and new:
        txt = "\n".join([f"🛡️ QUOTENWÄCHTER {report.stand(now)}",
                         "CEO-Tipps gegen Pinnacle (fair) · Bet365/Betfair (spielbar)"]
                        + [line for _, m in new for line in m])
        r = telegram.send(txt)
        log.append("  Telegram: " + (f"gesendet {r['message_ids']}" if r["sent"] else f"NICHT gesendet – {r['error']}"))
        if not r["sent"]:
            failures.append("Telegram-Versand fehlgeschlagen")
        if r["sent"]:
            seen |= {k for k, _ in new}
    elif new:
        log.append(f"  {len(new)} neue Meldung(en), nicht gesendet (ohne --send)")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")
    # Letzter Lauf zum Nachsehen im Repo (ohne das Protokoll des Workflows)
    STATUS.write_text("\n".join(log) + "\n", encoding="utf-8")
    if strict and failures:
        raise RuntimeError("; ".join(sorted(set(failures))))
    return log
