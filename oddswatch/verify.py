"""Nachprüfbarkeit: offene Tipps gegen den aktuellen Kalshi-Preis prüfen.

Für jeden offenen Tipp (valuebets + placed) werden Geld/Brief live abgerufen,
die Quote inkl. Gebühr nachgerechnet (0,07 · P · (1 − P) je Kontrakt, je
Order auf den Cent gerundet, Order ≈ 100 Kontrakte) und mit "spielbar ab"
aus dem Journal verglichen. Dazu die Links, unter denen sich Preis und
Referenzlinie selbst nachsehen lassen.
"""

from __future__ import annotations

import math

from . import pricing
from .journal import Journal
from .sources import kalshi

_ESPN = {"nfl": "nfl/game", "nhl": "nhl/game", "nba": "nba/game"}


def espn_url(league: str, event_id: str) -> str:
    if not event_id.isdigit():
        return ""
    path = _ESPN.get(league, "soccer/match")
    return f"https://www.espn.com/{path}/_/gameId/{event_id}"


def kalshi_url(ticker: str) -> str:
    return f"{kalshi.API}/markets/{ticker}"


def fee_per_contract(p: float, contracts: int = 100) -> float:
    return math.ceil(0.07 * contracts * p * (1 - p) * 100 - 1e-9) / 100 / contracts


def verify(j: Journal, fetch_market=kalshi.fetch_market) -> list[str]:
    ids = {(r["event"], r["market"]): r for r in j.read("forecasts")}
    rows, seen = [], set()
    for name in ("valuebets", "placed"):
        for r in j.read(name):
            ref = r.get("ref", "")
            if r.get("result") or not ref.startswith("KX") or ref in seen:
                continue
            seen.add(ref)
            vb = r if name == "valuebets" else next(
                (v for v in j.read("valuebets") if v.get("ref") == ref), {})
            rows.append((r, vb))
    if not rows:
        return ["Keine offenen Tipps."]
    lines = ["| Tipp | Geld/Brief | Quote inkl. Gebühr | spielbar ab | Status |",
             "|---|---|---|---|---|"]
    details = []
    for r, vb in sorted(rows, key=lambda x: x[0].get("kickoff", "")):
        m, err = fetch_market(r["ref"])
        sel = r.get("selection", r["ref"])
        if err or not m:
            lines.append(f"| {sel} | – | – | – | Abruf fehlgeschlagen ({err}) |")
            continue
        bid = kalshi._price(m, "yes_bid")
        ask = kalshi._price(m, "yes_ask")
        if (vb.get("market") or r.get("market", "")).endswith(":no"):   # NEIN-Seite
            bid, ask = (1 - ask, 1 - bid) if ask > 0 else (0.0, 0.0)
        mn = float(vb["min_odds"]) if vb.get("min_odds") else None
        if m.get("status") not in ("active", "open") or ask <= 0:
            status, odds = f"geschlossen ({m.get('status')})", None
        else:
            odds = pricing.kalshi_decimal_odds(ask * 100, contracts=100)
            status = ("✅ PLAY" if mn and odds >= mn else "❌ unter Mindestquote") if mn else "–"
        lines.append(f"| {r['event']}: {sel} | {bid * 100:.0f}/{ask * 100:.0f} ¢ | "
                     f"{f'{odds:.2f}' if odds else '–'} | {f'{mn:.2f}' if mn else '–'} | {status} |")
        fee = fee_per_contract(ask) if ask > 0 else 0.0
        fc = ids.get((r["event"], vb.get("market") or r.get("market")), {})
        d = [f"**{r['event']} – {sel}**",
             f"  Preis: {kalshi_url(r['ref'])} (yes_ask_dollars)"]
        if ask > 0:
            d.append(f"  Quote: 1 / ({ask:.2f} + {fee:.4f} Gebühr) = {1 / (ask + fee):.2f}")
        if vb.get("p_final"):
            pm, pf = float(vb["p_model"]), float(vb["p_final"])
            pr = f"{float(vb['p_ref']) * 100:.1f} %" if vb.get("p_ref") else "keine"
            d.append(f"  Fair: Modell {pm * 100:.1f} %, Referenz {pr}, Entscheidung "
                     f"{pf * 100:.1f} % → fair {1 / pf:.2f}, spielbar ab 1,03 / {pf:.4f} = {1.03 / pf:.2f}")
        url = espn_url(r.get("league") or vb.get("league", "") or fc.get("league", ""),
                       fc.get("event_id", ""))
        if url:
            d.append(f"  Referenzlinie (DraftKings über ESPN): {url}")
        details.append("\n".join(d))
    return lines + [""] + details
