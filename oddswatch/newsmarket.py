"""Preis-Check zu News-Meldungen: Ist die Meldung schon im Markt?

Für jedes betroffene Spiel: DraftKings (de-vigged, über ESPN) jetzt gegen den
ersten protokollierten Wert (forecasts.csv, vor der Meldung) und Kalshi
Geld/Brief jetzt. Urteil:
  ⚡ Fenster offen – Kalshi inkl. Gebühr ≥ 3 % über DraftKings-fair
  ✅ eingepreist  – DraftKings hat sich ≥ 2 Pp bewegt, Kalshi zieht mit
  ⏳ unbewegt     – DraftKings unverändert; Meldung evtl. noch nicht im Markt
Für gesetzte Wetten zusätzlich: Verkaufswert jetzt (Kalshi-Geldkurs abzgl.
Gebühr) gegen Haltewert (Kontrakte × DraftKings-fair).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from . import pricing
from .journal import Journal
from .scan import Fixture, _attach_kalshi, _devig_ref, evaluate_fixture
from .sources import espn, kalshi

MOVE_PP = 0.02
MIN_EV = 0.03


@dataclass
class Side:
    label: str
    dk_now: float | None
    dk_before: float | None
    bid: float
    ask: float
    odds: float
    ev: float | None


@dataclass
class MarketView:
    sides: dict[str, Side] = field(default_factory=dict)
    verdict: str = ""
    window: bool = False


def _game(league: str, event: str, kickoff: datetime) -> espn.EspnGame | None:
    for d in (kickoff.date(), kickoff.date() - timedelta(days=1)):
        games, _ = espn.scoreboard_day(league, d)
        for g in games:
            if g.title == event:
                return g
    return None


def _before(j: Journal, event: str) -> dict[str, float]:
    """Erster protokollierter DraftKings-Wert je Seite (älteste Prognose)."""
    out: dict[str, float] = {}
    for r in j.read("forecasts"):
        if r.get("event") == event and r.get("p_ref") and r["market"] not in out:
            out[r["market"]] = float(r["p_ref"])
    return out


def view(league: str, event: str, kickoff: str, j: Journal,
         quotes_cache: dict[str, list] | None = None) -> MarketView | None:
    from .quick import LEAGUES
    if league not in LEAGUES:
        return None
    path, series, sport, three = LEAGUES[league]
    espn.PATHS.setdefault(league, path)
    try:
        ko = datetime.fromisoformat(kickoff)
    except ValueError:
        return None
    g = _game(league, event, ko)
    if g is None:
        return None
    ref = _devig_ref(g, three_way=three)
    cache = quotes_cache if quotes_cache is not None else {}
    if series not in cache:
        cache[series] = kalshi.fetch_series(series)[0]
    fx = Fixture(league, sport, g, dict(ref) or {"home": 0.5, "away": 0.5}, "News-Check",
                 ref_probs=ref, model="market")
    _attach_kalshi(fx, cache[series])
    before = _before(j, event)
    v = MarketView()
    cands = {c.market: c for c in evaluate_fixture(fx, {})} if fx.kalshi else {}
    for side, q in fx.kalshi.items():
        c = cands.get(side)
        v.sides[side] = Side(
            label=c.selection if c else side, dk_now=ref.get(side), dk_before=before.get(side),
            bid=q.yes_bid, ask=q.yes_ask,
            odds=pricing.kalshi_decimal_odds(q.yes_ask * 100, contracts=100) if q.yes_ask > 0 else 0.0,
            ev=c.ev if c and ref.get(side) is not None else None)
    open_ = [s for s in v.sides.values() if s.ev is not None and s.ev >= MIN_EV]
    moves = [(s, s.dk_now - s.dk_before) for s in v.sides.values()
             if s.dk_now is not None and s.dk_before is not None]
    big = max(moves, key=lambda m: abs(m[1]), default=None)
    if open_:
        s = max(open_, key=lambda s: s.ev)
        v.window = True
        v.verdict = (f"⚡ Fenster offen: {s.label} @ {s.odds:.2f} bei Kalshi, fair {1 / s.dk_now:.2f} "
                     f"(EV {s.ev * 100:+.1f} %) – Kalshi hat noch nicht nachgezogen")
    elif not ref:
        v.verdict = "keine DraftKings-Linie – Einpreisung nicht prüfbar"
    elif big and abs(big[1]) >= MOVE_PP:
        s, d = big
        v.verdict = (f"✅ eingepreist: DraftKings {s.label} {s.dk_before * 100:.0f} % → "
                     f"{s.dk_now * 100:.0f} %, Kalshi {s.bid * 100:.0f}/{s.ask * 100:.0f} ¢ – keine Aktion")
    else:
        v.verdict = "⏳ Markt unbewegt – Meldung evtl. noch nicht eingepreist, Schnellscan beobachtet"
    return v


def position(v: MarketView, side: str, stake_eh: float, odds_taken: float) -> str:
    """Gesetzte Wette: Verkaufswert jetzt gegen Haltewert (in EH)."""
    s = v.sides.get(side)
    if not s or not stake_eh or not odds_taken:
        return ""
    contracts = stake_eh * odds_taken          # Auszahlung in EH bei Sieg
    fee = 0.07 * s.bid * (1 - s.bid)
    sell = contracts * max(s.bid - fee, 0.0)
    hold = contracts * s.dk_now if s.dk_now is not None else None
    txt = f"💼 Position {stake_eh:g} EH @ {odds_taken:.2f}: Verkauf jetzt ≈ {sell:.2f} EH"
    if hold is not None:
        txt += f", Haltewert ≈ {hold:.2f} EH (DraftKings {s.dk_now * 100:.0f} %)"
        txt += " → Verkauf lohnt" if sell > hold else " → Halten besser"
    return txt
