"""NHL V5.1 forward entry validation using dual-timescale MoneyPuck xG.

This module does NOT create PLAY signals. It downloads MoneyPuck's official
published team game bulk CSV once per run, builds leakage-safe slow/fast 5v5 xG
states using only games from dates strictly before each scheduled event, and
stores AGREE/WEAK/DISAGREE as SHADOW stats snapshots in Neon.

The classifier is intentionally frozen to the same definition used by the V5
regime diagnostics:
- WEAK: abs(slow xG-share diff) < 0.01 OR abs(fast diff) < 0.01
- AGREE: both non-weak and point in the same direction
- DISAGREE: both non-weak and point in opposite directions

No bookmaker price, close, ROI, or result is used to construct the signal.
"""
from __future__ import annotations

import csv
import io
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from urllib.request import Request, urlopen

from .sql.store import connect, ingest

SOURCE_URL = "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
SOURCE_NAME = "moneypuck-v5.1-entry"
SLOW_ALPHA = 0.05
FAST_ALPHA = 0.18
XG_AGREEMENT_THRESHOLD = 0.01
PRIOR_XGF5 = 1.8
PRIOR_XGA5 = 1.8

# ESPN / odds-watch full franchise names -> MoneyPuck team codes.
NHL_TO_MP = {
    "Anaheim Ducks": "ANA",
    "Arizona Coyotes": "ARI",
    "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY",
    "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL",
    "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET",
    "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA",
    "Los Angeles Kings": "L.A",
    "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL",
    "Nashville Predators": "NSH",
    "New Jersey Devils": "N.J",
    "New York Islanders": "NYI",
    "New York Rangers": "NYR",
    "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI",
    "Phoenix Coyotes": "ARI",
    "Pittsburgh Penguins": "PIT",
    "San Jose Sharks": "S.J",
    "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL",
    "Tampa Bay Lightning": "T.B",
    "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA",
    "Utah Mammoth": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH",
    "Winnipeg Jets": "WPG",
}


@dataclass
class XGState:
    xgf5: float = PRIOR_XGF5
    xga5: float = PRIOR_XGA5
    games: int = 0
    last_date: date | None = None


def _ema(old: float, value: float, alpha: float) -> float:
    return alpha * value + (1.0 - alpha) * old


def _share(state: XGState) -> float:
    den = state.xgf5 + state.xga5
    return state.xgf5 / den if den > 0 else 0.5


def classify_xg_agreement(
    slow_diff: float,
    fast_diff: float,
    threshold: float = XG_AGREEMENT_THRESHOLD,
) -> str:
    """Frozen V5 diagnostic definition; independent from odds/results."""
    if abs(float(slow_diff)) < threshold or abs(float(fast_diff)) < threshold:
        return "WEAK"
    return "AGREE" if slow_diff * fast_diff > 0 else "DISAGREE"


def download_text() -> str:
    req = Request(SOURCE_URL, headers={"User-Agent": "oddswatch-research/1.0"})
    with urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8-sig", "replace")


def parse_team_games(text: str) -> list[dict]:
    """Parse one 5v5 team-level row per team/game from the official bulk CSV."""
    reader = csv.DictReader(io.StringIO(text))
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for raw in reader:
        if raw.get("situation") != "5on5" or raw.get("position") != "Team Level":
            continue
        gid = (raw.get("gameId") or "").strip()
        team = (raw.get("playerTeam") or raw.get("team") or "").strip()
        day_raw = (raw.get("gameDate") or "").strip()
        if not gid or not team or len(day_raw) != 8:
            continue
        key = (gid, team)
        if key in seen:
            continue
        try:
            day = date(int(day_raw[:4]), int(day_raw[4:6]), int(day_raw[6:8]))
            xgf = float(raw.get("xGoalsFor") or "")
            xga = float(raw.get("xGoalsAgainst") or "")
            season = int(raw.get("season") or 0)
        except (TypeError, ValueError):
            continue
        if not (math.isfinite(xgf) and math.isfinite(xga)) or xgf < 0 or xga < 0:
            continue
        seen.add(key)
        out.append({
            "date": day,
            "game_id": gid,
            "team": team,
            "season": season,
            "xgf5": xgf,
            "xga5": xga,
        })
    return sorted(out, key=lambda r: (r["date"], r["game_id"], r["team"]))


def _update(states: dict[str, XGState], row: dict, alpha: float) -> None:
    state = states[row["team"]]
    state.xgf5 = _ema(state.xgf5, float(row["xgf5"]), alpha)
    state.xga5 = _ema(state.xga5, float(row["xga5"]), alpha)
    state.games += 1
    state.last_date = row["date"]


def build_event_signals(events: list[dict], games: list[dict]) -> tuple[list[dict], list[dict]]:
    """Build chronological event signals using only prior-date MoneyPuck games.

    MoneyPuck bulk rows carry a game date rather than a trusted puck-drop
    timestamp here, so same-calendar-day games are deliberately excluded. This
    is conservative and prevents hidden same-day look-ahead.
    """
    slow: dict[str, XGState] = defaultdict(XGState)
    fast: dict[str, XGState] = defaultdict(XGState)
    signals: list[dict] = []
    issues: list[dict] = []
    i = 0
    ordered_events = sorted(events, key=lambda e: e["kickoff"])

    for event in ordered_events:
        event_day = event["kickoff"].astimezone(timezone.utc).date()
        while i < len(games) and games[i]["date"] < event_day:
            row = games[i]
            _update(slow, row, SLOW_ALPHA)
            _update(fast, row, FAST_ALPHA)
            i += 1

        home_code = NHL_TO_MP.get(event["home_name"])
        away_code = NHL_TO_MP.get(event["away_name"])
        if not home_code or not away_code:
            issues.append({
                "event_id": event["event_id"],
                "reason": "UNMAPPED_MONEYPUCK_TEAM",
                "home": event["home_name"],
                "away": event["away_name"],
            })
            continue

        hs, away_slow = slow[home_code], slow[away_code]
        hf, away_fast = fast[home_code], fast[away_code]
        # Require actual observations for both teams; do not classify pure priors.
        if min(hs.games, away_slow.games, hf.games, away_fast.games) <= 0:
            issues.append({
                "event_id": event["event_id"],
                "reason": "NO_PRIOR_MONEYPUCK_GAMES",
                "home_code": home_code,
                "away_code": away_code,
            })
            continue

        slow_home = _share(hs)
        slow_away = _share(away_slow)
        fast_home = _share(hf)
        fast_away = _share(away_fast)
        slow_diff = slow_home - slow_away
        fast_diff = fast_home - fast_away
        agreement = classify_xg_agreement(slow_diff, fast_diff)
        through_dates = [
            d for d in (hs.last_date, away_slow.last_date, hf.last_date, away_fast.last_date)
            if d
        ]
        data_through_date = max(through_dates) if through_dates else event_day - timedelta(days=1)
        data_through = datetime.combine(
            data_through_date, datetime.min.time(), tzinfo=timezone.utc
        )

        signals.append({
            "event_id": event["event_id"],
            "home_team_id": event["home_team_id"],
            "away_team_id": event["away_team_id"],
            "home_name": event["home_name"],
            "away_name": event["away_name"],
            "home_code": home_code,
            "away_code": away_code,
            "data_through": data_through,
            "slow_home_xg_share": slow_home,
            "slow_away_xg_share": slow_away,
            "fast_home_xg_share": fast_home,
            "fast_away_xg_share": fast_away,
            "slow_mp_xg_share_diff": slow_diff,
            "fast_mp_xg_share_diff": fast_diff,
            "xg_agreement": agreement,
            "home_slow_games": hs.games,
            "away_slow_games": away_slow.games,
            "home_fast_games": hf.games,
            "away_fast_games": away_fast.games,
        })
    return signals, issues


def build_snapshots(signals: list[dict], observed_at: datetime) -> list[dict]:
    snapshots: list[dict] = []
    for s in signals:
        shared = {
            "version": "NHL-V5.1-entry-shadow",
            "release_status": "SHADOW",
            "price_used_as_feature": False,
            "result_used_as_feature": False,
            "gate_candidate": s["xg_agreement"] == "AGREE",
            "xg_agreement": s["xg_agreement"],
            "threshold": XG_AGREEMENT_THRESHOLD,
            "slow_alpha": SLOW_ALPHA,
            "fast_alpha": FAST_ALPHA,
            "home_code": s["home_code"],
            "away_code": s["away_code"],
            "slow_home_xg_share": s["slow_home_xg_share"],
            "slow_away_xg_share": s["slow_away_xg_share"],
            "fast_home_xg_share": s["fast_home_xg_share"],
            "fast_away_xg_share": s["fast_away_xg_share"],
            "slow_mp_xg_share_diff": s["slow_mp_xg_share_diff"],
            "fast_mp_xg_share_diff": s["fast_mp_xg_share_diff"],
            "home_games": s["home_slow_games"],
            "away_games": s["away_slow_games"],
            "source_url": SOURCE_URL,
        }
        for side, team_id in (("HOME", s["home_team_id"]), ("AWAY", s["away_team_id"])):
            metrics = dict(shared)
            metrics["side"] = side
            snapshots.append({
                "event_id": s["event_id"],
                "league": "nhl",
                "entity_type": "team",
                "entity_id": team_id,
                "source": SOURCE_NAME,
                "observed_at": observed_at,
                "data_through": min(s["data_through"], observed_at),
                "metrics": metrics,
            })
    return snapshots


def run(now: datetime | None = None, horizon_days: int = 3) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone-aware now required")
    if not 1 <= horizon_days <= 7:
        raise ValueError("horizon_days must be 1..7")

    with connect() as conn:
        events = conn.execute(
            "SELECT event_id,home_team_id,away_team_id,home_name,away_name,kickoff "
            "FROM sports.events WHERE league='nhl' AND status='STATUS_SCHEDULED' "
            "AND season_type='regular' AND kickoff>%s AND kickoff<=%s ORDER BY kickoff",
            (now, now + timedelta(days=horizon_days)),
        ).fetchall()

    if not events:
        result = {
            "at": now.isoformat(),
            "source": SOURCE_NAME,
            "forward_events": 0,
            "signals": 0,
            "persisted": {"stats_snapshots": 0},
            "issues": [],
            "release_eligible": False,
            "plays_created": 0,
        }
        print(json.dumps(result, ensure_ascii=False))
        return result

    text = download_text()
    games = parse_team_games(text)
    signals, issues = build_event_signals(events, games)
    snapshots = build_snapshots(signals, now)
    with connect() as conn:
        counts = ingest(conn, {"stats_snapshots": snapshots}) if snapshots else {
            "stats_snapshots": 0
        }

    result = {
        "at": now.isoformat(),
        "source": SOURCE_NAME,
        "money_puck_team_game_rows": len(games),
        "money_puck_season_min": min((r["season"] for r in games), default=None),
        "money_puck_season_max": max((r["season"] for r in games), default=None),
        "money_puck_date_max": max((r["date"] for r in games), default=None),
        "forward_events": len(events),
        "signals": len(signals),
        "agreement_counts": {
            k: sum(s["xg_agreement"] == k for s in signals)
            for k in ("AGREE", "WEAK", "DISAGREE")
        },
        "persisted": counts,
        "issues": issues,
        "release_eligible": False,
        "plays_created": 0,
    }
    print(json.dumps(result, ensure_ascii=False, default=str))
    return result


if __name__ == "__main__":
    run()
