"""Soccer sharp-lead / pre-steam tracking for CEO Telegram.

This layer NEVER changes model fair probabilities. It compares repeated,
de-vigged sportsbook snapshots after fair probabilities already exist.

Lead source: Pinnacle.
Slower/execution books: Bet365, Betfair.

Confirmed steam requires time-series evidence via oddswatch.steam. A one-off
cross-book gap is reported only as a gap, never mislabeled as steam.

CLV target is NOT an invented closing-line forecast. It is the current Pinnacle
no-vig fair price: if the slower executable market converges to the sharp
reference, entry-vs-that-price is the immediate CLV capture opportunity.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import pricing, steam

SIDES = ("home", "draw", "away")
SOURCE_NAMES = {
    "pinnacle": "Pinnacle",
    "bet365": "Bet365",
    "betfair": "Betfair",
}


def _books(fx) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    quotes = getattr(fx, "market_quotes", None) or {}
    for side in SIDES:
        for q in quotes.get(side, []):
            source = SOURCE_NAMES.get(str(q.source).lower())
            if not source:
                continue
            if float(q.odds) <= 1:
                continue
            out.setdefault(source, {})[side] = float(q.odds)
    return out


def _prob_book(book: dict[str, float]) -> dict[str, float] | None:
    if not all(side in book for side in SIDES):
        return None
    ps = pricing.devig([book[s] for s in SIDES])
    return dict(zip(SIDES, ps))


def collect(fixtures) -> tuple[list[dict], dict[tuple[str, str], dict]]:
    records = []
    meta: dict[tuple[str, str], dict] = {}

    for fx in fixtures:
        if fx.sport != "soccer":
            continue
        books = _books(fx)
        pin = _prob_book(books.get("Pinnacle", {}))
        if not pin:
            continue

        slow_probs = {}
        for name in ("Bet365", "Betfair"):
            p = _prob_book(books.get(name, {}))
            if p:
                slow_probs[name] = p
        if not slow_probs:
            continue

        for side in SIDES:
            probs = {"Pinnacle": pin[side]}
            odds = {"Pinnacle": books["Pinnacle"][side]}
            for name, p in slow_probs.items():
                probs[name] = p[side]
                odds[name] = books[name][side]

            executable = [
                (name, odds[name])
                for name in ("Bet365", "Betfair")
                if name in odds
            ]
            best_name, best_odds = max(executable, key=lambda x: x[1])
            slow_avg = sum(probs[n] for n in slow_probs) / len(slow_probs)
            gap = pin[side] - slow_avg
            sharp_fair = 1.0 / pin[side]
            clv_to_sharp = best_odds / sharp_fair - 1.0

            key = f"soccer:{fx.league}:{fx.game.id}:{side}"
            records.append({
                "key": key,
                "event": fx.game.title,
                "kickoff": fx.game.kickoff.isoformat(),
                "league": fx.league,
                "market": side,
                "selection": (
                    "Unentschieden"
                    if side == "draw"
                    else (fx.game.home.name if side == "home" else fx.game.away.name)
                ),
                "lead_source": "Pinnacle",
                "slow_sources": list(slow_probs),
                "probs": probs,
                "odds": odds,
            })
            meta[(fx.game.title, side)] = {
                "event": fx.game.title,
                "league": fx.league,
                "side": side,
                "sharp_prob": pin[side],
                "sharp_fair": sharp_fair,
                "slow_prob": slow_avg,
                "gap": gap,
                "best_source": best_name,
                "best_odds": best_odds,
                "clv_to_sharp": clv_to_sharp,
                "probs": probs,
                "odds": odds,
            })
    return records, meta


def assess(fixtures, *, now: datetime | None = None) -> dict[tuple[str, str], dict]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    records, meta = collect(fixtures)
    signals = steam.update_many(records, now=now) if records else []
    by_key = {s["key"]: s for s in signals}

    for rec in records:
        row = meta[(rec["event"], rec["market"])]
        sig = by_key.get(rec["key"])
        row["signal"] = sig
        if sig:
            row["steam"] = "STEAM+" if sig["direction"] == "SHORTENING" else "STEAM-"
        else:
            row["steam"] = "UNCONFIRMED"
    return meta


def annotate_candidates(candidates, state: dict[tuple[str, str], dict]) -> None:
    """Confirmed drift against a candidate blocks PLAY; unconfirmed gaps do not."""
    for c in candidates:
        if c.league in {"nfl", "nhl", "nba", "del", "icehl", "liiga", "shl", "nl", "khl"}:
            continue
        row = state.get((c.event, c.market))
        if not row:
            continue
        sig = row.get("signal")
        if sig and sig.get("direction") == "DRIFTING":
            c.flags = list(c.flags or []) + [
                "STEAM-: Pinnacle bewegt sich bestätigt gegen die Auswahl"
            ]
