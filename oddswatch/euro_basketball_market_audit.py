"""European basketball market-reference audit.

No bookmaker feed is assumed. Schedules come from API-Basketball when available;
prices come from public Polymarket and Kalshi markets. The output is a reference
layer for checking user-observed Bet365 prices later. It never creates a PLAY.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from .sources import kalshi, polymarket
from .sql.store import connect, ingest, migrate


TARGETS = ("euroleague", "eurocup")


class Team:
    def __init__(self, name: str):
        self.name = name
        self.short = name
        self.abbr = ""
    def aliases(self):
        return [self.name]


def _fixture_from_poly(code: str, q):
    outcomes = [str(x) for x in q.outcomes]
    if len(outcomes) != 2:
        return None
    home, away = outcomes[0], outcomes[1]
    game = SimpleNamespace(
        id=f"poly:{q.slug}",
        title=f"{home} - {away}",
        kickoff=q.kickoff or datetime.now(timezone.utc) + timedelta(days=1),
        home=Team(home),
        away=Team(away),
    )
    return SimpleNamespace(
        league=code,
        sport="basketball",
        game=game,
        probs={"home": 0.5, "away": 0.5},
        context=[],
        ref_probs={},
        flags={},
        offers={},
        market_quotes={},
    )


def _fixture_from_kalshi(code: str, event: dict):
    title = str(event.get("title") or "").strip()
    if " vs " not in title:
        return None
    away, home = [x.strip() for x in title.split(" vs ", 1)]
    ko = kalshi._sports_ticker_kickoff(str(event.get("event_ticker") or "")) or kalshi._dt(
        event.get("strike_date"), event.get("expected_expiration_time"),
        event.get("latest_expiration_time"), event.get("close_time"),
    )
    if ko is None:
        return None
    game = SimpleNamespace(
        id=f"kalshi:{event.get('event_ticker')}",
        title=f"{home} - {away}",
        kickoff=ko,
        home=Team(home),
        away=Team(away),
    )
    return SimpleNamespace(
        league=code,
        sport="basketball",
        game=game,
        probs={"home": 0.5, "away": 0.5},
        context=[],
        ref_probs={},
        flags={},
        offers={},
        market_quotes={},
    )


def _dedupe(fixtures):
    out = []
    seen = set()
    for fx in sorted(fixtures, key=lambda x: x.game.kickoff):
        key = (
            fx.league,
            fx.game.home.name.casefold(),
            fx.game.away.name.casefold(),
            fx.game.kickoff.date().isoformat(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(fx)
    return out


def audit(days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    result = {"generated_at": now.isoformat(), "leagues": {}, "sources": ["Polymarket", "Kalshi"]}

    for code in TARGETS:
        fixtures = []
        issues = []

        # Fixture discovery and price reference from Polymarket.
        try:
            pquotes, err = polymarket.discover(polymarket.TAGS[code])
            if err:
                issues.append(f"Polymarket {code}: {err}")
            for q in pquotes:
                if q.kickoff and now < q.kickoff <= until:
                    fx = _fixture_from_poly(code, q)
                    if fx:
                        fixtures.append(fx)
        except Exception as exc:
            issues.append(f"Polymarket {code}: {type(exc).__name__}: {exc}")

        # Kalshi is a second independent fixture/market source where available.
        series = kalshi.BASKETBALL_SERIES.get(code)
        if series:
            try:
                events, err = kalshi.series_events(series)
                if err:
                    issues.append(f"Kalshi {code}: {err}")
                for event in events:
                    fx = _fixture_from_kalshi(code, event)
                    if fx and now < fx.game.kickoff <= until:
                        fixtures.append(fx)
            except Exception as exc:
                issues.append(f"Kalshi {code}: {type(exc).__name__}: {exc}")

        fixtures = _dedupe(fixtures)

        # Attach both markets to the combined fixture list.
        try:
            polymarket.attach(fixtures, issues)
        except Exception as exc:
            issues.append(f"Polymarket attach {code}: {type(exc).__name__}: {exc}")
        try:
            kalshi.attach(fixtures, issues)
        except Exception as exc:
            issues.append(f"Kalshi attach {code}: {type(exc).__name__}: {exc}")

        games = []
        for fx in fixtures:
            refs = {}
            for side, offers in (fx.offers or {}).items():
                for q in offers:
                    refs.setdefault(q.source, {})[side] = {
                        "odds": float(q.odds),
                        "implied": 1.0 / float(q.odds),
                        "liquidity": q.liquidity,
                        "ref": q.ref,
                    }
            games.append({
                "event_id": str(fx.game.id),
                "kickoff": fx.game.kickoff.isoformat(),
                "home": fx.game.home.name,
                "away": fx.game.away.name,
                "reference_probabilities": fx.ref_probs,
                "references": refs,
                "context": fx.context,
            })

        result["leagues"][code] = {
            "count": len(games),
            "games": games,
            "issues": issues,
            "reference_note": (
                "No API-Basketball and no bookmaker feed. Fixtures/prices are discovered "
                "from Polymarket and Kalshi only. Bet365 prices must be supplied/observed "
                "separately and are then audited against these references plus our model."
            ),
        }

    return result


def main():
    print(json.dumps(
        audit(days=int(os.getenv("EU_BASKETBALL_AUDIT_DAYS", "7"))),
        ensure_ascii=False, default=str, indent=2,
    ))


if __name__ == "__main__":
    main()
