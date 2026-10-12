"""NHL 1st-period xG/xGA shadow model from MoneyPuck shot data.

Purpose
-------
Build a dedicated first-period model instead of scaling the full-game model.
The model uses MoneyPuck shot-level xGoal values from period 1 only, keeps
HOME and AWAY venue states separate, and derives fair decimal odds for:
- 1P 1X2
- 1P Over/Under 0.5, 1.5 and 2.5

No bookmaker odds enter the model. No PLAY signals are created. Output is
persisted as SHADOW stats snapshots in Neon for prospective validation.

MoneyPuck explicitly publishes the season shot ZIP files for non-commercial
research. We use the published ZIPs rather than scraping pages.
"""
from __future__ import annotations

import csv
import io
import json
import math
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

from .nhl_v5_1_forward import NHL_TO_MP
from .sql.store import connect, ingest

SOURCE_NAME = "moneypuck-1p-xg-v1"
ZIP_TEMPLATE = "https://peter-tanner.com/moneypuck/downloads/shots_{season}.zip"
SEASONS = (2025, 2026)
ALPHA_SLOW = 0.08
ALPHA_FAST = 0.22
SEASON_RETAIN = 0.70
PRIOR_XGF1 = 0.95
PRIOR_XGA1 = 0.95
MAX_GOALS = 8

_CODE_ALIASES = {
    "NJD": "N.J", "N.J": "N.J",
    "TBL": "T.B", "T.B": "T.B",
    "LAK": "L.A", "L.A": "L.A",
    "SJS": "S.J", "S.J": "S.J",
    "UTA": "UTA",
}


@dataclass
class PeriodState:
    xgf1: float = PRIOR_XGF1
    xga1: float = PRIOR_XGA1
    games: int = 0


def _canon(code: str) -> str:
    code = (code or "").strip()
    return _CODE_ALIASES.get(code, code)


def _float(v, default=None):
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _int(v, default=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _boolish(v) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y"}


def download_season_zip(season: int) -> bytes:
    url = ZIP_TEMPLATE.format(season=int(season))
    req = Request(url, headers={"User-Agent": "oddswatch-research/1.0"})
    with urlopen(req, timeout=180) as response:
        return response.read()


def _csv_member(zf: zipfile.ZipFile) -> str:
    names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if not names:
        raise ValueError("MoneyPuck shot ZIP has no CSV")
    # Season ZIPs normally contain one CSV; choose the largest if more exist.
    return max(names, key=lambda n: zf.getinfo(n).file_size)


def parse_period1_games(zip_bytes: bytes, season_hint: int | None = None) -> list[dict]:
    """Aggregate period-1 shot xG to one HOME/AWAY row per regular-season game."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        member = _csv_member(zf)
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.DictReader(text)
            games: dict[str, dict] = {}
            for r in reader:
                period = _int(r.get("period"))
                if period != 1:
                    continue
                if _boolish(r.get("isPlayoffGame")):
                    continue
                gid = str(r.get("game_id") or r.get("gameId") or "").strip()
                if not gid:
                    continue
                home = _canon(r.get("homeTeamCode") or r.get("home_team") or "")
                away = _canon(r.get("awayTeamCode") or r.get("away_team") or "")
                if not home or not away or home == away:
                    continue
                team_raw = str(r.get("teamCode") or r.get("team") or "").strip()
                if team_raw.upper() == "HOME":
                    team = home
                elif team_raw.upper() == "AWAY":
                    team = away
                else:
                    team = _canon(team_raw)
                if team not in {home, away}:
                    continue
                xg = _float(r.get("xGoal"))
                if xg is None or xg < 0 or xg > 1:
                    continue
                season = _int(r.get("season"), season_hint or 0) or (season_hint or 0)
                g = games.setdefault(gid, {
                    "game_id": gid, "season": season,
                    "home": home, "away": away,
                    "home_xg1": 0.0, "away_xg1": 0.0,
                    "shots": 0,
                })
                if team == home:
                    g["home_xg1"] += xg
                else:
                    g["away_xg1"] += xg
                g["shots"] += 1

    out = [g for g in games.values() if g["shots"] > 0]
    return sorted(out, key=lambda g: (_int(g["game_id"], 0) or 0, g["home"], g["away"]))


def _ema(old: float, value: float, alpha: float) -> float:
    return alpha * value + (1.0 - alpha) * old


def _retain(states: dict, retain: float = SEASON_RETAIN) -> None:
    for s in states.values():
        s.xgf1 = PRIOR_XGF1 + retain * (s.xgf1 - PRIOR_XGF1)
        s.xga1 = PRIOR_XGA1 + retain * (s.xga1 - PRIOR_XGA1)


def build_states(games_by_season: dict[int, list[dict]], alpha: float) -> dict[tuple[str, str], PeriodState]:
    """Build venue-specific states: (team, HOME/AWAY)."""
    states: dict[tuple[str, str], PeriodState] = defaultdict(PeriodState)
    previous = None
    for season in sorted(games_by_season):
        if previous is not None and season != previous:
            _retain(states)
        previous = season
        for g in games_by_season[season]:
            hs = states[(g["home"], "HOME")]
            av = states[(g["away"], "AWAY")]
            hx, ax = float(g["home_xg1"]), float(g["away_xg1"])
            # Update after each completed game.
            hs.xgf1 = _ema(hs.xgf1, hx, alpha)
            hs.xga1 = _ema(hs.xga1, ax, alpha)
            hs.games += 1
            av.xgf1 = _ema(av.xgf1, ax, alpha)
            av.xga1 = _ema(av.xga1, hx, alpha)
            av.games += 1
    return states


def poisson_1p_1x2(home_lambda: float, away_lambda: float, max_goals: int = MAX_GOALS) -> dict[str, float]:
    ph = [math.exp(-home_lambda) * home_lambda**k / math.factorial(k) for k in range(max_goals + 1)]
    pa = [math.exp(-away_lambda) * away_lambda**k / math.factorial(k) for k in range(max_goals + 1)]
    # Fold the tiny truncated tail into the last bucket.
    ph[-1] += max(0.0, 1.0 - sum(ph))
    pa[-1] += max(0.0, 1.0 - sum(pa))
    home = draw = away = 0.0
    for i, p1 in enumerate(ph):
        for j, p2 in enumerate(pa):
            p = p1 * p2
            if i > j:
                home += p
            elif i == j:
                draw += p
            else:
                away += p
    total = home + draw + away
    return {"HOME": home / total, "DRAW": draw / total, "AWAY": away / total}


def total_prob_over(total_lambda: float, line: float) -> float:
    if line not in {0.5, 1.5, 2.5}:
        raise ValueError("supported first-period total lines: 0.5, 1.5, 2.5")
    threshold = int(line + 0.5)
    under_or_equal = sum(
        math.exp(-total_lambda) * total_lambda**k / math.factorial(k)
        for k in range(threshold)
    )
    return 1.0 - under_or_equal


def fair_decimal(p: float) -> float:
    return 1.0 / p if 0 < p < 1 else float("inf")


def project_event(
    home_code: str,
    away_code: str,
    slow: dict[tuple[str, str], PeriodState],
    fast: dict[tuple[str, str], PeriodState],
) -> dict:
    hs, avs = slow[(home_code, "HOME")], slow[(away_code, "AWAY")]
    hf, avf = fast[(home_code, "HOME")], fast[(away_code, "AWAY")]

    slow_home = (hs.xgf1 + avs.xga1) / 2.0
    slow_away = (avs.xgf1 + hs.xga1) / 2.0
    fast_home = (hf.xgf1 + avf.xga1) / 2.0
    fast_away = (avf.xgf1 + hf.xga1) / 2.0

    # Blend slow/fast rather than letting the tiny early-season fast state dominate.
    home_lam = 0.60 * slow_home + 0.40 * fast_home
    away_lam = 0.60 * slow_away + 0.40 * fast_away
    probs = poisson_1p_1x2(home_lam, away_lam)
    total = home_lam + away_lam

    totals = {}
    for line in (0.5, 1.5, 2.5):
        po = total_prob_over(total, line)
        totals[str(line)] = {
            "p_over": po,
            "p_under": 1.0 - po,
            "fair_over": fair_decimal(po),
            "fair_under": fair_decimal(1.0 - po),
        }

    return {
        "home_home_slow_xgf1": hs.xgf1,
        "home_home_slow_xga1": hs.xga1,
        "away_away_slow_xgf1": avs.xgf1,
        "away_away_slow_xga1": avs.xga1,
        "home_home_fast_xgf1": hf.xgf1,
        "home_home_fast_xga1": hf.xga1,
        "away_away_fast_xgf1": avf.xgf1,
        "away_away_fast_xga1": avf.xga1,
        "home_home_games": hs.games,
        "away_away_games": avs.games,
        "slow_matchup_home_xg1": slow_home,
        "slow_matchup_away_xg1": slow_away,
        "fast_matchup_home_xg1": fast_home,
        "fast_matchup_away_xg1": fast_away,
        "lambda_home_1p": home_lam,
        "lambda_away_1p": away_lam,
        "lambda_total_1p": total,
        "p_1p_home": probs["HOME"],
        "p_1p_draw": probs["DRAW"],
        "p_1p_away": probs["AWAY"],
        "fair_1p_home": fair_decimal(probs["HOME"]),
        "fair_1p_draw": fair_decimal(probs["DRAW"]),
        "fair_1p_away": fair_decimal(probs["AWAY"]),
        "totals": totals,
    }


def run(now: datetime | None = None, horizon_days: int = 3) -> dict:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("timezone-aware now required")
    with connect() as conn:
        events = conn.execute(
            "SELECT event_id,home_team_id,away_team_id,home_name,away_name,kickoff "
            "FROM sports.events WHERE league='nhl' AND status='STATUS_SCHEDULED' "
            "AND season_type='regular' AND kickoff>%s AND kickoff<=%s ORDER BY kickoff",
            (now, now + timedelta(days=horizon_days)),
        ).fetchall()

    games_by_season: dict[int, list[dict]] = {}
    source_sizes = {}
    issues = []
    for season in SEASONS:
        try:
            blob = download_season_zip(season)
            source_sizes[str(season)] = len(blob)
            games_by_season[season] = parse_period1_games(blob, season)
        except Exception as exc:
            issues.append({"season": season, "error": f"{type(exc).__name__}: {exc}"})

    if not games_by_season:
        raise RuntimeError(f"no MoneyPuck shot seasons available: {issues}")

    slow = build_states(games_by_season, ALPHA_SLOW)
    fast = build_states(games_by_season, ALPHA_FAST)
    snapshots = []
    projected = 0
    for e in events:
        home = NHL_TO_MP.get(e["home_name"])
        away = NHL_TO_MP.get(e["away_name"])
        if not home or not away:
            issues.append({"event_id": e["event_id"], "error": "unmapped team"})
            continue
        p = project_event(home, away, slow, fast)
        # Do not call prior-only states valid projections.
        if p["home_home_games"] <= 0 or p["away_away_games"] <= 0:
            issues.append({"event_id": e["event_id"], "error": "no venue-specific 1P history"})
            continue
        projected += 1
        common = {
            "version": "NHL-1P-xG-v1",
            "release_status": "SHADOW",
            "market_features_used": False,
            "price_used_as_feature": False,
            "period": "1P",
            "home_code": home,
            "away_code": away,
            "source_seasons": list(SEASONS),
            **p,
        }
        for side, entity_id in (("HOME", e["home_team_id"]), ("AWAY", e["away_team_id"])):
            metrics = dict(common)
            metrics["side"] = side
            snapshots.append({
                "event_id": e["event_id"],
                "league": "nhl",
                "entity_type": "team",
                "entity_id": entity_id,
                "source": SOURCE_NAME,
                "observed_at": now,
                "data_through": now,
                "metrics": metrics,
            })

    with connect() as conn:
        counts = ingest(conn, {"stats_snapshots": snapshots}) if snapshots else {"stats_snapshots": 0}

    result = {
        "at": now.isoformat(),
        "source": SOURCE_NAME,
        "source_zip_bytes": source_sizes,
        "games_by_season": {str(k): len(v) for k, v in games_by_season.items()},
        "forward_events": len(events),
        "projected_events": projected,
        "persisted": counts,
        "issues": issues,
        "release_eligible": False,
        "plays_created": 0,
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
