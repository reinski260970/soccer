"""Vom fairen Preis zum Value-Kandidaten (max. 5)."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from . import pricing


@dataclass
class Offer:
    """Ein verifizierter Preis. source: 'kalshi' | 'bet365' | 'orbit'."""
    event: str
    kickoff: str
    market: str       # z. B. "1", "X", "2", "O2.5"
    selection: str    # lesbar: "Dortmund Sieg (90 Min.)"
    odds: float       # effektive Dezimalquote (Kalshi inkl. Gebühr)
    source: str
    observed_at: str
    liquidity: float | None = None
    ref: str = ""     # z. B. Kalshi-Ticker, für Abrechnung/CLV
    league: str = ""


@dataclass
class Candidate:
    event: str
    kickoff: str
    market: str
    selection: str
    source: str
    odds: float
    p_model: float
    fair_odds: float
    min_odds: float
    edge: float
    ev: float
    stake_eh: float
    estimate: bool
    reason: str
    observed_at: str
    liquidity: float | None
    p_ref: float | None = None     # Referenzmarkt (de-vigged), falls vorhanden
    p_final: float | None = None   # Entscheidungswahrscheinlichkeit
    ref: str = ""
    league: str = ""
    flags: list[str] | None = None  # Newsvorbehalte -> keine Freigabe

    def as_row(self) -> dict:
        return asdict(self)


def evaluate(offer: Offer, p_model: float, *, min_ev: float = 0.03,
             estimate: bool = False, reason: str = "",
             uncertainty: float | None = None, p_ref: float | None = None,
             p_final: float | None = None, flags: list[str] | None = None) -> Candidate:
    """p_model = unabhängige Modellwahrscheinlichkeit; p_final (falls gesetzt)
    ist die Entscheidungsgrundlage für fair/Edge/EV/Einsatz."""
    unc = uncertainty if uncertainty is not None else (0.5 if estimate else 0.25)
    p = p_final if p_final is not None else p_model
    return Candidate(
        event=offer.event, kickoff=offer.kickoff, market=offer.market,
        selection=offer.selection, source=offer.source, odds=offer.odds,
        p_model=p_model, fair_odds=pricing.fair_odds(p),
        min_odds=pricing.min_odds(p, min_ev),
        edge=pricing.edge(p, offer.odds), ev=pricing.ev(p, offer.odds),
        stake_eh=pricing.stake_units(p, offer.odds, uncertainty=unc),
        estimate=estimate, reason=reason, observed_at=offer.observed_at,
        liquidity=offer.liquidity, p_ref=p_ref, p_final=p, ref=offer.ref,
        league=offer.league, flags=flags or [],
    )


def pick(cands: list[Candidate], max_n: int = 5, min_ev: float = 0.03,
         min_edge: float = 0.02, max_odds: float = 6.0) -> list[Candidate]:
    """Filter + Ranking. Pro Event höchstens ein Tipp (korrelierte Märkte).
    Liquidität ist kein Ausschlusskriterium, wird aber ausgewiesen."""
    ok = [c for c in cands
          if c.ev >= min_ev and c.edge >= min_edge and c.odds <= max_odds
          and c.stake_eh > 0 and not c.flags]
    ok.sort(key=lambda c: (c.estimate, -c.ev))
    seen, out = set(), []
    for c in ok:
        if c.event in seen:
            continue
        seen.add(c.event)
        out.append(c)
        if len(out) == max_n:
            break
    return out
