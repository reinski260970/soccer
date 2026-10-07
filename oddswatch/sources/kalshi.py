"""Kalshi public sports prices.

Open event/market data is used without authentication. Prices become PLAY-eligible
only when KALSHI_EXECUTABLE=1 is set; otherwise they are reference/watch prices.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from .. import fetch, matching
from ..selection import Offer

BASE = "https://external-api.kalshi.com/trade-api/v2"
SUPPORTED = {"nfl", "nhl", "nba"}
MAX_PAGES = 5


def _enabled() -> bool:
    return (os.getenv("KALSHI_EXECUTABLE", "").strip().lower()
            in {"1", "true", "yes", "on"})


def _num(v, default: float | None = None) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _dt(*vals) -> datetime | None:
    for v in vals:
        if not v:
            continue
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    return None


def events() -> tuple[list[dict], str | None]:
    out, cursor = [], ""
    for _ in range(MAX_PAGES):
        params = {"status": "open", "with_nested_markets": "true", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data, err = fetch.get_json(f"{BASE}/events?{urlencode(params)}", timeout=25, retries=1)
        if data is None:
            return out, err
        rows = data.get("events") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            return out, "Kalshi: ungültige Events-Antwort"
        out.extend(rows)
        cursor = str(data.get("cursor") or "")
        if not cursor:
            break
    return out, None


def _mentions(text: str, aliases: list[str]) -> bool:
    n = matching.norm(text)
    if not n:
        return False
    for a in aliases:
        na = matching.norm(a)
        if na and (na == n or na in n or matching.same(text, a)):
            return True
    return False


def _event_hit(event: dict, game) -> bool:
    text = " | ".join(str(event.get(k) or "") for k in ("title", "sub_title", "event_ticker"))
    if not (_mentions(text, game.home.aliases()) and _mentions(text, game.away.aliases())):
        return False
    ko = _dt(event.get("strike_date"), event.get("expected_expiration_time"),
             event.get("latest_expiration_time"))
    return not ko or abs(ko - game.kickoff.astimezone(timezone.utc)) <= timedelta(hours=36)


def _market_side(m: dict, game) -> tuple[str | None, str | None]:
    yes = str(m.get("yes_sub_title") or m.get("subtitle") or m.get("title") or "")
    no = str(m.get("no_sub_title") or "")
    yh, ya = _mentions(yes, game.home.aliases()), _mentions(yes, game.away.aliases())
    nh, na = _mentions(no, game.home.aliases()), _mentions(no, game.away.aliases())
    yside = "home" if yh and not ya else ("away" if ya and not yh else None)
    nside = "home" if nh and not na else ("away" if na and not nh else None)
    return yside, nside


def _ask(m: dict, side: str) -> float | None:
    p = _num(m.get(f"{side}_ask_dollars"))
    if p is None:
        cents = _num(m.get(f"{side}_ask"))
        p = cents / 100.0 if cents is not None and cents > 1 else cents
    return p if p is not None and 0 < p < 1 else None


def attach(fixtures, issues: list[str]) -> int:
    rows = [f for f in fixtures if f.league in SUPPORTED]
    if not rows:
        return 0
    es, err = events()
    if err:
        issues.append(f"Kalshi: {err}")
        return 0
    executable = _enabled()
    now = datetime.now(timezone.utc)
    matched = 0

    for fx in rows:
        hits = [e for e in es if _event_hit(e, fx.game)]
        if len(hits) != 1:
            continue
        event = hits[0]
        side_quotes: dict[str, list[tuple[float, float | None, str, str]]] = {"home": [], "away": []}
        for m in event.get("markets") or []:
            yside, nside = _market_side(m, fx.game)
            ticker = str(m.get("ticker") or "")
            liq = _num(m.get("liquidity_dollars"))
            if yside:
                p = _ask(m, "yes")
                if p:
                    side_quotes[yside].append((p, liq, ticker, "yes"))
            if nside:
                p = _ask(m, "no")
                if p:
                    side_quotes[nside].append((p, liq, ticker, "no"))
        if not side_quotes["home"] or not side_quotes["away"]:
            continue
        # Best available ask per team; normalize for a no-vig market reference.
        h = min(side_quotes["home"], key=lambda x: x[0])
        a = min(side_quotes["away"], key=lambda x: x[0])
        z = h[0] + a[0]
        if z <= 0:
            continue
        ref = {"home": h[0] / z, "away": a[0] / z}
        matched += 1
        fx.context.append(
            f"Kalshi ML: {fx.game.home.abbr or fx.game.home.name} {ref['home']*100:.1f}% / "
            f"{fx.game.away.abbr or fx.game.away.name} {ref['away']*100:.1f}%"
        )
        if not fx.ref_probs:
            fx.ref_probs = ref
        else:
            for side in ("home", "away"):
                if side in fx.ref_probs and abs(fx.ref_probs[side] - ref[side]) > 0.12:
                    fx.flags.setdefault(side, []).append(
                        f"Marktreferenzen uneinig: Kalshi {ref[side]*100:.1f}% vs bestehend "
                        f"{fx.ref_probs[side]*100:.1f}%")
        for side, q, team in (("home", h, fx.game.home.name), ("away", a, fx.game.away.name)):
            p, liq, ticker, contract_side = q
            fx.offers.setdefault(side, []).append(Offer(
                event=fx.game.title, kickoff=fx.game.kickoff.isoformat(), market=side,
                selection=f"{team} ML", odds=1.0 / p, source="kalshi",
                observed_at=now.isoformat(), liquidity=liq,
                ref=f"kalshi:{ticker}:{contract_side}", league=fx.league,
                executable=executable,
            ))
    return matched
