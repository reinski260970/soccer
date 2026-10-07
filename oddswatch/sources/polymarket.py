"""Polymarket sports prices (read-only Gamma + CLOB).

Public data is always usable as a market reference. It becomes PLAY-eligible only
when POLYMARKET_EXECUTABLE=1 is set, because a public quote alone does not prove
that this installation can actually trade the market.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from .. import fetch, matching
from ..selection import Offer

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
TAGS = {"nfl": "nfl", "nhl": "nhl", "nba": "nba"}
SERIES = {"nfl": "10187", "nba": "10345"}
GAME_TAG_ID = "100639"
MIN_TOP_DEPTH_USD = 10.0
MAX_SPREAD = 0.05
NEAR_HOURS = 60


@dataclass
class PolyQuote:
    title: str
    slug: str
    kickoff: datetime | None
    outcomes: list[str]
    tokens: list[str]
    mids: list[float]
    liquidity: float


def _enabled() -> bool:
    return (os.getenv("POLYMARKET_EXECUTABLE", "").strip().lower()
            in {"1", "true", "yes", "on"})


def _arr(v) -> list:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            x = json.loads(v)
            return x if isinstance(x, list) else []
        except ValueError:
            return []
    return []


def _num(v, default: float = 0.0) -> float:
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


def events(tag: str) -> tuple[list[dict], str | None]:
    params = {"active": "true", "closed": "false", "limit": 500}
    if tag in SERIES:
        params.update({"series_id": SERIES[tag], "tag_id": GAME_TAG_ID})
    else:
        params["tag_slug"] = tag
    data, err = fetch.get_json(f"{GAMMA}/events?{urlencode(params)}", timeout=30, retries=2)
    if data is None:
        return [], err
    if isinstance(data, dict):
        data = data.get("data") or data.get("events") or []
    return (data if isinstance(data, list) else []), None


def _moneyline(event: dict) -> PolyQuote | None:
    for m in event.get("markets") or []:
        if str(m.get("sportsMarketType") or "").lower() != "moneyline":
            continue
        outcomes = [str(x) for x in _arr(m.get("outcomes"))]
        tokens = [str(x) for x in _arr(m.get("clobTokenIds"))]
        prices = [_num(x, -1) for x in _arr(m.get("outcomePrices"))]
        if len(outcomes) != 2 or len(tokens) != 2 or len(prices) != 2:
            continue
        if {x.strip().lower() for x in outcomes} <= {"yes", "no"}:
            continue
        if any(p <= 0 or p >= 1 for p in prices):
            continue
        kick = _dt(m.get("gameStartTime"), m.get("eventStartTime"),
                   event.get("gameStartTime"), event.get("eventStartTime"),
                   m.get("endDate"), event.get("endDate"))
        return PolyQuote(
            title=str(event.get("title") or m.get("question") or ""),
            slug=str(event.get("slug") or ""), kickoff=kick,
            outcomes=outcomes, tokens=tokens, mids=prices,
            liquidity=_num(m.get("liquidityNum") or m.get("liquidity")
                           or event.get("liquidityNum") or event.get("liquidity")),
        )
    return None


def event_by_slug(slug: str) -> tuple[dict | None, str | None]:
    data, err = fetch.get_json(f"{GAMMA}/events/slug/{slug}", timeout=20, retries=1)
    if data is None:
        return None, err
    if isinstance(data, list):
        return (data[0] if data else None), None
    if isinstance(data, dict):
        if "event" in data and isinstance(data["event"], dict):
            return data["event"], None
        return data, None
    return None, "Polymarket Gamma: ungültige Event-Antwort"


def _game_slug(league: str, game) -> str | None:
    if league != "nfl":
        return None
    a = (game.away.abbr or "").strip().lower()
    h = (game.home.abbr or "").strip().lower()
    if not a or not h:
        return None
    d = game.kickoff.astimezone(timezone.utc).date().isoformat()
    return f"nfl-{a}-{h}-{d}"


def direct_quote(league: str, game) -> tuple[PolyQuote | None, str | None]:
    slug = _game_slug(league, game)
    if not slug:
        return None, None
    e, err = event_by_slug(slug)
    if e is None:
        return None, err
    return _moneyline(e), None


def discover(tag: str) -> tuple[list[PolyQuote], str | None]:
    es, err = events(tag)
    if err:
        return [], err
    return [q for e in es if (q := _moneyline(e)) is not None], None


def _team_side(q: PolyQuote, aliases: list[str]) -> int | None:
    hits = []
    for i, outcome in enumerate(q.outcomes):
        if any(matching.same(outcome, a) or matching.match_label(outcome, aliases)
               for a in aliases if a):
            hits.append(i)
    return hits[0] if len(hits) == 1 else None


def find(qs: list[PolyQuote], game) -> tuple[PolyQuote, int, int] | None:
    hits = []
    for q in qs:
        h = _team_side(q, game.home.aliases())
        a = _team_side(q, game.away.aliases())
        if h is None or a is None or h == a:
            continue
        if q.kickoff and abs(q.kickoff - game.kickoff.astimezone(timezone.utc)) > timedelta(hours=12):
            continue
        hits.append((q, h, a))
    return hits[0] if len(hits) == 1 else None


def book(token: str) -> tuple[dict | None, str | None]:
    data, err = fetch.get_json(f"{CLOB}/book?{urlencode({'token_id': token})}",
                               timeout=15, retries=1)
    if not isinstance(data, dict):
        return None, err or "Polymarket CLOB: ungültiges Orderbuch"
    bids = sorted([(_num(x.get("price"), -1), _num(x.get("size")))
                   for x in data.get("bids") or []], reverse=True)
    asks = sorted([(_num(x.get("price"), 2), _num(x.get("size")))
                   for x in data.get("asks") or []])
    bids = [x for x in bids if 0 < x[0] < 1 and x[1] > 0]
    asks = [x for x in asks if 0 < x[0] < 1 and x[1] > 0]
    if not asks:
        return None, "Polymarket CLOB: kein Ask"
    bid = bids[0] if bids else (None, 0.0)
    ask = asks[0]
    spread = (ask[0] - bid[0]) if bid[0] is not None else None
    return {"best_bid": bid[0], "best_ask": ask[0], "ask_size": ask[1],
            "ask_depth_usd": ask[0] * ask[1], "spread": spread}, None


def attach(fixtures, issues: list[str]) -> int:
    by_league: dict[str, list] = {}
    for fx in fixtures:
        if fx.league in TAGS:
            by_league.setdefault(fx.league, []).append(fx)

    now = datetime.now(timezone.utc)
    executable = _enabled()
    matched = 0
    for league, rows in by_league.items():
        qs, err = discover(TAGS[league])
        if err:
            issues.append(f"Polymarket {league.upper()}: {err}")
            continue
        for fx in rows:
            hit = find(qs, fx.game)
            if not hit and league == "nfl":
                dq, derr = direct_quote(league, fx.game)
                if derr:
                    issues.append(f"Polymarket NFL {fx.game.title}: {derr}")
                if dq:
                    h = _team_side(dq, fx.game.home.aliases())
                    a = _team_side(dq, fx.game.away.aliases())
                    if h is not None and a is not None and h != a:
                        hit = (dq, h, a)
            if not hit:
                continue
            q, hi, ai = hit
            matched += 1
            raw = [q.mids[hi], q.mids[ai]]
            z = sum(raw)
            poly_ref = {"home": raw[0] / z, "away": raw[1] / z} if z > 0 else {}
            if poly_ref:
                fx.context.append(
                    f"Polymarket ML: {fx.game.home.abbr or fx.game.home.name} "
                    f"{poly_ref['home']*100:.1f}% / {fx.game.away.abbr or fx.game.away.name} "
                    f"{poly_ref['away']*100:.1f}% · Liq ~${q.liquidity:,.0f}"
                )
                if not fx.ref_probs:
                    fx.ref_probs = poly_ref
                else:
                    for side in ("home", "away"):
                        if side in fx.ref_probs and abs(fx.ref_probs[side] - poly_ref[side]) > 0.12:
                            fx.flags.setdefault(side, []).append(
                                f"Marktreferenzen uneinig: Polymarket {poly_ref[side]*100:.1f}% "
                                f"vs bestehend {fx.ref_probs[side]*100:.1f}%")

            if fx.game.kickoff.astimezone(timezone.utc) - now > timedelta(hours=NEAR_HOURS):
                continue
            obs = now.isoformat()
            for side, idx, team in (("home", hi, fx.game.home.name),
                                    ("away", ai, fx.game.away.name)):
                b, berr = book(q.tokens[idx])
                if berr or not b:
                    if berr:
                        issues.append(f"Polymarket {fx.game.title} {side}: {berr}")
                    continue
                ask, spread, depth = b["best_ask"], b["spread"], b["ask_depth_usd"]
                if ask <= 0 or ask >= 0.98:
                    continue
                if spread is None or spread > MAX_SPREAD or depth < MIN_TOP_DEPTH_USD:
                    continue
                fx.offers.setdefault(side, []).append(Offer(
                    event=fx.game.title, kickoff=fx.game.kickoff.isoformat(),
                    market=side, selection=f"{team} ML", odds=1.0 / ask,
                    source="polymarket", observed_at=obs, liquidity=depth,
                    ref=f"polymarket:{q.slug}:{q.tokens[idx]}", league=fx.league,
                    executable=executable,
                ))
    return matched
