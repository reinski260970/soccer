"""Offline historical hockey market CSV importer/auditor.

This module performs no network requests. It only reads local CSV files from
data/hockey/market/, normalizes rows, removes exact duplicates, rejects
conflicts, and audits strict team matching against our historical team universe.
"""
from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .hockey_closing_backtest import LEAGUE_MAP, _resolve
from .hockey_walkforward import load_history
from .matching import norm

MARKET_DIR = Path("data/hockey/market")


@dataclass(frozen=True)
class MarketRow:
    league: str
    day: date
    home: str
    away: str
    close_home: float
    close_draw: float
    close_away: float
    result: str
    source_file: str


def _odd(value) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 1 else None


def read_market_dir(path: Path = MARKET_DIR) -> tuple[list[MarketRow], list[str]]:
    rows: list[MarketRow] = []
    issues: list[str] = []

    if not path.exists():
        return rows, [f"MISSING_DIR {path}"]

    for src in sorted(path.glob("*.csv")):
        try:
            fh = src.open(encoding="utf-8-sig", newline="")
        except OSError as exc:
            issues.append(f"OPEN_ERROR {src.name}: {type(exc).__name__}")
            continue
        with fh:
            for n, raw in enumerate(csv.DictReader(fh), start=2):
                league = LEAGUE_MAP.get((raw.get("league") or "").strip().upper())
                if not league:
                    issues.append(f"UNKNOWN_LEAGUE {src.name}:{n}")
                    continue
                try:
                    day = date.fromisoformat((raw.get("date") or "").strip())
                except ValueError:
                    issues.append(f"BAD_DATE {src.name}:{n}")
                    continue
                odds = [_odd(raw.get(k)) for k in ("close_home", "close_draw", "close_away")]
                if any(x is None for x in odds):
                    issues.append(f"BAD_ODDS {src.name}:{n}")
                    continue
                result = (raw.get("reg_result") or "").strip().upper()
                if result not in {"HOME", "DRAW", "AWAY"}:
                    issues.append(f"BAD_RESULT {src.name}:{n}")
                    continue
                home = (raw.get("home_team") or "").strip()
                away = (raw.get("away_team") or "").strip()
                if not home or not away or norm(home) == norm(away):
                    issues.append(f"BAD_TEAMS {src.name}:{n}")
                    continue
                rows.append(MarketRow(
                    league, day, home, away,
                    float(odds[0]), float(odds[1]), float(odds[2]),
                    result, src.name,
                ))

    # Deduplicate exact same event. Conflicting copies are excluded fail-closed.
    grouped: dict[tuple, MarketRow] = {}
    conflicts: set[tuple] = set()
    for row in rows:
        key = (row.league, row.day, norm(row.home), norm(row.away))
        old = grouped.get(key)
        if old is None:
            grouped[key] = row
            continue
        same = (
            old.result == row.result
            and abs(old.close_home - row.close_home) < 1e-12
            and abs(old.close_draw - row.close_draw) < 1e-12
            and abs(old.close_away - row.close_away) < 1e-12
        )
        if not same:
            conflicts.add(key)

    for key in conflicts:
        grouped.pop(key, None)
        issues.append("CONFLICT " + "|".join(map(str, key)))

    return sorted(grouped.values(), key=lambda r: (r.day, r.league, r.home, r.away)), issues


def audit_matching(
    rows: list[MarketRow],
    history_path: str | Path = "data/hockey/history.csv",
    as_of: date = date(2026, 10, 12),
) -> dict:
    history = load_history(history_path, as_of=as_of)
    teams: dict[str, set[str]] = {}
    for r in history:
        teams.setdefault(r["league"], set()).update((r["home"], r["away"]))

    out = {}
    for league in ("nhl", "del", "icehl", "liiga", "extraliga"):
        xs = [r for r in rows if r.league == league]
        matched = 0
        unmatched: list[dict] = []
        for r in xs:
            home = _resolve(r.home, league, teams.get(league, set()))
            away = _resolve(r.away, league, teams.get(league, set()))
            if home and away and home != away:
                matched += 1
            else:
                unmatched.append({
                    "date": r.day.isoformat(),
                    "home": r.home,
                    "away": r.away,
                    "home_match": home,
                    "away_match": away,
                    "source_file": r.source_file,
                })
        out[league] = {
            "rows": len(xs),
            "matched": matched,
            "unmatched": len(unmatched),
            "match_rate": round(matched / len(xs), 4) if xs else None,
            "unmatched_examples": unmatched[:10],
        }

    return {
        "files": dict(Counter(r.source_file for r in rows)),
        "rows": len(rows),
        "leagues": out,
    }


def run() -> dict:
    rows, issues = read_market_dir()
    report = audit_matching(rows)
    report["issues"] = issues
    print(report)
    return report


if __name__ == "__main__":
    run()
