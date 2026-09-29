"""Über/Unter und Handicap: Kalshi gegen DraftKings auf derselben Linie.

Kalshi führt je Spiel eine Leiter binärer Märkte ("Over 38.5 points",
"PIT Steelers wins by over 2.5 points"); DraftKings (über ESPN) eine Linie
mit Quoten. Verglichen wird nur exakt dieselbe Linie:
  - Total: JA = Über, NEIN = Unter
  - Handicap: JA = Favorit gewinnt mit mehr als x, NEIN = Außenseiter +x
Fairer Kurs = de-vigged DraftKings. Das Modell ist für diese Märkte laut
Backtest nicht besser als der Markt und fließt daher nicht ein.
Die Events hängen über das Ticker-Suffix am Sieger-Markt
(KXNFLGAME-26OCT01PITCLE ↔ KXNFLTOTAL-26OCT01PITCLE).
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import fetch, matching, pricing
from .selection import Candidate, Offer, evaluate
from .sources import kalshi

SERIES = {"nfl": ("KXNFLTOTAL", "KXNFLSPREAD", "Punkte"),
          "nhl": ("KXNHLTOTAL", "KXNHLSPREAD", "Tore"),
          "nba": ("KXNBATOTAL", "KXNBASPREAD", "Punkte"),
          "bundesliga": ("KXBUNDESLIGATOTAL", "KXBUNDESLIGASPREAD", "Tore"),
          "2bundesliga": ("KXBUNDESLIGA2TOTAL", "KXBUNDESLIGA2SPREAD", "Tore"),
          "ucl": ("KXUCLTOTAL", "KXUCLSPREAD", "Tore"),
          "uel": ("KXUELTOTAL", "KXUELSPREAD", "Tore"),
          "uecl": ("KXUECLTOTAL", "KXUECLSPREAD", "Tore"),
          "nations": ("KXUEFANLTOTAL", "KXUEFANLSPREAD", "Tore")}
MAX_SPREAD = 0.10


def _suffix(event_ticker: str) -> str:
    return event_ticker.split("-", 1)[1] if "-" in event_ticker else ""


def _events(series: str) -> tuple[dict[str, list[dict]], str | None]:
    data, err = fetch.get_json(kalshi.events_url(series))
    if data is None:
        return {}, err
    return {_suffix(e.get("event_ticker", "")): e.get("markets") or []
            for e in data.get("events", [])}, None


def _side(m: dict, no: bool) -> tuple[float, float]:
    """(Geld, Brief) für JA bzw. NEIN."""
    bid, ask = kalshi._price(m, "yes_bid"), kalshi._price(m, "yes_ask")
    return (1 - ask, 1 - bid) if no else (bid, ask)


def _candidate(fx, m: dict, no: bool, market: str, selection: str, p: float,
               note: str) -> Candidate | None:
    bid, ask = _side(m, no)
    if ask <= 0 or ask >= 0.99:
        return None
    flags = []
    if bid <= 0 or ask - bid > MAX_SPREAD:
        flags.append(f"Orderbuch dünn (Spread {(ask - max(bid, 0)) * 100:.0f} ¢) – Preis nicht verlässlich")
    odds = pricing.kalshi_decimal_odds(ask * 100, contracts=100)
    g = fx.game
    off = Offer(g.title, g.kickoff.isoformat(timespec="minutes"), market, selection, odds, "kalshi",
                datetime.now(timezone.utc).isoformat(timespec="seconds"), liquidity=None, ref=m.get("ticker", ""), league=fx.league)
    reason = (f"Markt (DraftKings, de-vigged) {p * 100:.1f} % auf derselben Linie. {note} "
              f"Kalshi {'NEIN' if no else 'JA'} {bid * 100:.0f}/{ask * 100:.0f} ¢")
    return evaluate(off, p, estimate=False, reason=reason, p_ref=p, p_final=p, flags=flags)


def candidates(fixtures: list, issues: list[str], notes: list[str]) -> list[Candidate]:
    out: list[Candidate] = []
    by_league: dict[str, list] = {}
    for fx in fixtures:
        if fx.league in SERIES and fx.kalshi and fx.game.ref_line:
            by_league.setdefault(fx.league, []).append(fx)
    note = "Modell laut Backtest nicht besser als der Markt – reiner Preisvergleich."
    n_total = n_spread = 0
    for lg, fxs in by_league.items():
        tot_s, spr_s, unit = SERIES[lg]
        tot, e1 = _events(tot_s)
        spr, e2 = _events(spr_s)
        for e in (e1, e2):
            if e:
                issues.append(f"Kalshi {lg} Linien: {e}")
        for fx in fxs:
            suf = _suffix(next(iter(fx.kalshi.values())).event_ticker)
            r = fx.game.ref_line
            # Total
            L, ov, un = r.get("total_line"), r.get("ml_over"), r.get("ml_under")
            if L is not None and ov and un and suf in tot:
                m = next((x for x in tot[suf] if abs(float(x.get("floor_strike") or -1) - L) < 1e-6), None)
                if m:
                    p_over, p_under = pricing.devig([ov, un])
                    n_total += 1
                    for no, p, lab, code in ((False, p_over, "Über", f"O{L:g}"),
                                             (True, p_under, "Unter", f"U{L:g}:no")):
                        c = _candidate(fx, m, no, code, f"{lab} {L:g} {unit}", p, note)
                        if c:
                            out.append(c)
            # Handicap: Favorit mit negativer Linie
            hl, ho, al, ao = (r.get("spread_home"), r.get("odds_spread_home"),
                              r.get("spread_away"), r.get("odds_spread_away"))
            if None in (hl, ho, al, ao) or suf not in spr or hl == 0:
                continue
            fav, dog, x = ((fx.game.home, fx.game.away, -hl) if hl < 0 else (fx.game.away, fx.game.home, -al))
            p_fav, p_dog = pricing.devig([ho, ao] if hl < 0 else [ao, ho])
            m = None
            for cand in spr[suf]:
                lab = (cand.get("yes_sub_title") or "").split(" wins by")[0]
                if abs(float(cand.get("floor_strike") or -1) - x) < 1e-6 and (
                        matching.match_label(lab, fav.aliases()) or matching.same(lab, fav.name)
                        or lab.split(" ")[0] == fav.abbr):
                    m = cand
                    break
            if not m:
                continue
            n_spread += 1
            for no, p, sel, code in ((False, p_fav, f"{fav.name} −{x:g} (gewinnt mit mehr als {x:g})",
                                      f"HC-{x:g} {fav.abbr or fav.name}"),
                                     (True, p_dog, f"{dog.name} +{x:g}", f"HC+{x:g} {dog.abbr or dog.name}:no")):
                c = _candidate(fx, m, no, code, sel, p, note)
                if c:
                    out.append(c)
    notes.append(f"Über/Unter & Handicap: {n_total} Total- und {n_spread} Handicap-Linien mit "
                 "DraftKings und Kalshi auf derselben Linie verglichen (BTTS: keine DraftKings-"
                 "Referenz über ESPN – nicht bewertet)")
    return out
