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

from .sources import apibasketball, kalshi, polymarket
from .sql.store import connect, ingest, migrate


TARGETS = {
    "euroleague": ("Euroleague", None),
    "eurocup": ("Eurocup", None),
    "bbl": ("BBL", "Germany"),
    "acb": ("ACB", "Spain"),
}


class Team:
    def __init__(self, name: str):
        self.name = name
        self.short = name
        self.abbr = ""
    def aliases(self):
        return [self.name]


def _season(now: datetime) -> str:
    y = now.year if now.month >= 7 else now.year - 1
    return str(y)


def _event_row(league: str, g: dict, observed: datetime) -> dict:
    return {
        "event_id": f"{league}:apibasketball:{g['id']}",
        "league": league,
        "source": "API-Basketball",
        "source_event_id": str(g["id"]),
        "home_team_id": f"{league}:api:{g['home_id']}",
        "away_team_id": f"{league}:api:{g['away_id']}",
        "home_name": g["home"],
        "away_name": g["away"],
        "kickoff": g["start"],
        "season": int(_season(g["start"])),
        "season_type": "regular",
        "status": g["status"] or "NS",
        "home_score": None,
        "away_score": None,
        "observed_at": observed,
    }


def _fixture(code: str, g: dict):
    game = SimpleNamespace(
        id=str(g["id"]),
        title=f"{g['home']} - {g['away']}",
        kickoff=g["start"],
        home=Team(g["home"]),
        away=Team(g["away"]),
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


def audit(days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    season = _season(now)
    result = {"generated_at": now.isoformat(), "season": season, "leagues": {}}
    bundle = {"events": [], "odds_snapshots": []}

    for code, (search, country) in TARGETS.items():
        league_row, err = apibasketball.resolve_league(search, country)
        if err or not league_row:
            result["leagues"][code] = {"error": err or "not found"}
            continue
        lg = league_row.get("league") or league_row
        league_id = lg.get("id") or league_row.get("id")
        if league_id is None:
            result["leagues"][code] = {"error": "league id missing"}
            continue

        rows, err = apibasketball.games(league_id=int(league_id), season=season)
        if err:
            result["leagues"][code] = {"error": err}
            continue

        fixtures = []
        for raw in rows:
            g = apibasketball.parse_game(raw)
            if not g or not (now < g["start"] <= until):
                continue
            fixtures.append((_fixture(code, g), g))
            bundle["events"].append(_event_row(code, g, now))

        fx_only = [x[0] for x in fixtures]
        issues = []
        try:
            polymarket.attach(fx_only, issues)
        except Exception as exc:
            issues.append(f"Polymarket: {type(exc).__name__}: {exc}")
        try:
            kalshi.attach(fx_only, issues)
        except Exception as exc:
            issues.append(f"Kalshi: {type(exc).__name__}: {exc}")

        games = []
        for fx, g in fixtures:
            refs = {}
            for side, offers in (fx.offers or {}).items():
                for q in offers:
                    refs.setdefault(q.source, {})[side] = {
                        "odds": float(q.odds),
                        "implied": 1.0 / float(q.odds),
                        "liquidity": q.liquidity,
                        "ref": q.ref,
                    }
                    bundle["odds_snapshots"].append({
                        "quote_id": f"{code}:{g['id']}:{q.source}:{side}:{int(now.timestamp())}",
                        "event_id": f"{code}:apibasketball:{g['id']}",
                        "market": "moneyline",
                        "selection": side.upper(),
                        "line": 0,
                        "period": "FULL_GAME",
                        "settlement_rules": "INCLUDING_OT",
                        "bookmaker": q.source,
                        "source": q.source,
                        "source_url": None,
                        "observed_at": now,
                        "source_time": None,
                        "odds": float(q.odds),
                        "commission": 0,
                        "executable": False,
                        "live": False,
                        "liquidity": q.liquidity,
                    })
            games.append({
                "game_id": g["id"],
                "kickoff": g["start"].isoformat(),
                "home": g["home"],
                "away": g["away"],
                "reference_probabilities": fx.ref_probs,
                "references": refs,
                "context": fx.context,
            })

        result["leagues"][code] = {
            "league_id": league_id,
            "name": lg.get("name") or search,
            "count": len(games),
            "games": games,
            "issues": issues,
            "reference_note": (
                "Polymarket/Kalshi reference only; compare an observed Bet365 price "
                "against these markets and the independent model before calling it value."
            ),
        }

    if os.getenv("SPORTS_DATABASE_URL", "").strip() and bundle["events"]:
        with connect() as conn:
            migrate(conn)
            result["neon"] = ingest(conn, bundle)
    else:
        result["neon"] = {
            "configured": False,
            "events": len(bundle["events"]),
            "odds": len(bundle["odds_snapshots"]),
        }
    return result


def main():
    print(json.dumps(
        audit(days=int(os.getenv("EU_BASKETBALL_AUDIT_DAYS", "7"))),
        ensure_ascii=False, default=str, indent=2,
    ))


if __name__ == "__main__":
    main()
