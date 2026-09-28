"""Kalshi-Fills -> Ledger 'placed' (deine tatsächlich gespielten Wetten).

Importiert werden Käufe (action=buy), dedupliziert per fill_id. Verkäufe
(vorzeitiges Glattstellen) werden gezählt und gemeldet, aber nicht verbucht –
deren Ergebnis ergibt sich nicht aus der Marktauflösung.
Quote je Fill = 1 / (Preis + Gebühr je Kontrakt); Einsatz in EH = $ / eh_usd.
"""

from __future__ import annotations

import os

from .journal import Journal
from .sources import kalshi
from .sources.kalshi_auth import Client, parse_fill
from . import fetch


def _event_title(event_ticker: str, cache: dict) -> str:
    if event_ticker not in cache:
        d, _ = fetch.get_json(f"{kalshi.API}/events/{event_ticker}")
        cache[event_ticker] = ((d or {}).get("event") or {}).get("title") or event_ticker
    return cache[event_ticker]


def import_fills(j: Journal, client: Client | None = None, eh_usd: float | None = None) -> list[str]:
    eh_usd = eh_usd or float(os.environ.get("ODDSWATCH_EH_USD", "10"))
    client = client or Client()
    raw = client.fills()
    known = {r.get("fill_id") for r in j.read("placed") if r.get("fill_id")}
    vb = {r.get("ref"): r for r in j.read("valuebets") if r.get("ref")}
    titles: dict[str, str] = {}
    rows, sells, log = [], 0, []
    for d in raw:
        f = parse_fill(d)
        if f.action != "buy":
            sells += 1
            continue
        if not f.fill_id or f.fill_id in known or f.count <= 0:
            continue
        m, _ = kalshi.fetch_market(f.ticker)
        label = (m or {}).get("yes_sub_title") or f.ticker.rsplit("-", 1)[-1]
        ev_ticker = (m or {}).get("event_ticker") or f.ticker.rsplit("-", 1)[0]
        cost = f.price * f.count + f.fee
        link = vb.get(f.ticker) if f.side == "yes" else None
        rows.append({
            "placed_at": f.created, "event": _event_title(ev_ticker, titles),
            "kickoff": (m or {}).get("occurrence_datetime", ""), "market": f.side,
            "selection": label if f.side == "yes" else f"NICHT {label}",
            "bookmaker": "kalshi", "odds_taken": f.count / cost if cost else "",
            "stake_eh": cost / eh_usd, "stake_usd": cost,
            "valuebet_ref": (link or {}).get("created_at", ""), "ref": f.ticker,
            "fill_id": f.fill_id})
        known.add(f.fill_id)
    j.append("placed", rows)
    log.append(f"Kalshi-Fills: {len(raw)} abgerufen, {len(rows)} neu verbucht"
               f" (1 EH = {eh_usd:g} $), {sells} Verkäufe nicht verbucht")
    for r in rows:
        tag = "freigegebene Valuebet" if r["valuebet_ref"] else "ohne Freigabe"
        log.append(f"  {r['placed_at'][:16]} {r['event']}: {r['selection']} @ "
                   f"{r['odds_taken']:.2f}, {r['stake_usd']:.2f} $ ({tag})")
    return log
