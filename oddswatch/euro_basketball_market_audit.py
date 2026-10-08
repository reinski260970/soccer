"""Audit European basketball Bet365 moneyline prices against a sharp market reference.

Purpose: test whether apparent Bet365 "value" is realistic before trusting a model.
This module does not create PLAYs. It compares Bet365 to Pinnacle when both are
available and stores observed prices in the normalized Neon sports schema.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone

from .sources import apibasketball
from .sql.store import connect, ingest, migrate


TARGETS = {
    "euroleague": ("Euroleague", None),
    "eurocup": ("Eurocup", None),
    "bbl": ("BBL", "Germany"),
    "acb": ("ACB", "Spain"),
}

BOOK_ALIASES = {
    "bet365": {"bet365", "bet 365"},
    "pinnacle": {"pinnacle"},
}


def _find_book(books: dict[str, dict[str, float]], key: str):
    aliases = BOOK_ALIASES[key]
    for name, sides in books.items():
        if name.casefold().strip() in aliases:
            return name, sides
    return None, None


def _devig_two(home: float, away: float) -> tuple[float, float]:
    ih, ia = 1.0 / home, 1.0 / away
    z = ih + ia
    return ih / z, ia / z


def _edge(prob: float, odd: float) -> float:
    return prob * odd - 1.0


def _season(now: datetime) -> str:
    y = now.year if now.month >= 7 else now.year - 1
    # API-Sports season identifiers vary by competition. Most European basketball
    # competitions accept start-year strings; callers can override via env later.
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


def audit(days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    season = _season(now)
    result = {"generated_at": now.isoformat(), "season": season, "leagues": {}, "alerts": []}
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

        games = []
        for raw in rows:
            g = apibasketball.parse_game(raw)
            if not g or not (now < g["start"] <= until):
                continue

            odds_rows, oerr = apibasketball.odds(game_id=g["id"])
            if oerr:
                games.append({"game": f"{g['home']} - {g['away']}", "error": oerr})
                continue
            books = apibasketball.moneyline_books(odds_rows)
            b365_name, b365 = _find_book(books, "bet365")
            pin_name, pin = _find_book(books, "pinnacle")

            row = {
                "game_id": g["id"],
                "kickoff": g["start"].isoformat(),
                "home": g["home"],
                "away": g["away"],
                "bet365": b365,
                "pinnacle": pin,
            }
            bundle["events"].append(_event_row(code, g, now))

            for book_name, sides, executable in (
                (b365_name, b365, True),
                (pin_name, pin, False),
            ):
                if not book_name or not sides:
                    continue
                for side in ("home", "away"):
                    bundle["odds_snapshots"].append({
                        "quote_id": f"{code}:api-basketball:{g['id']}:{book_name}:{side}:{int(now.timestamp())}",
                        "event_id": f"{code}:apibasketball:{g['id']}",
                        "market": "moneyline",
                        "selection": side.upper(),
                        "line": 0,
                        "period": "FULL_GAME",
                        "settlement_rules": "INCLUDING_OT",
                        "bookmaker": book_name,
                        "source": "API-Basketball",
                        "source_url": None,
                        "observed_at": now,
                        "source_time": None,
                        "odds": sides[side],
                        "commission": 0,
                        "executable": executable,
                        "live": False,
                        "liquidity": None,
                    })

            if b365 and pin:
                ph, pa = _devig_two(pin["home"], pin["away"])
                edges = {
                    "home": _edge(ph, b365["home"]),
                    "away": _edge(pa, b365["away"]),
                }
                row["pinnacle_no_vig"] = {"home": ph, "away": pa}
                row["bet365_vs_pinnacle_ev"] = edges
                for side, ev in edges.items():
                    if ev >= 0.03:
                        alert = {
                            "league": code,
                            "game": f"{g['home']} - {g['away']}",
                            "side": side,
                            "bet365_odds": b365[side],
                            "pinnacle_odds": pin[side],
                            "pinnacle_fair": 1.0 / (ph if side == "home" else pa),
                            "market_ev": ev,
                            "severity": "HIGH" if ev >= 0.08 else ("MEDIUM" if ev >= 0.05 else "LOW"),
                        }
                        result["alerts"].append(alert)
            games.append(row)

        result["leagues"][code] = {
            "league_id": league_id,
            "name": lg.get("name") or search,
            "games": games,
            "count": len(games),
        }

    if os.getenv("SPORTS_DATABASE_URL", "").strip() and bundle["events"]:
        with connect() as conn:
            migrate(conn)
            result["neon"] = ingest(conn, bundle)
    else:
        result["neon"] = {"configured": False, "events": len(bundle["events"]), "odds": len(bundle["odds_snapshots"])}
    return result


def main():
    out = audit(days=int(os.getenv("EU_BASKETBALL_AUDIT_DAYS", "7")))
    print(json.dumps(out, ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
