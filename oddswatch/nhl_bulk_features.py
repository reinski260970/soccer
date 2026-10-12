"""Leakage-safe rolling NHL features from the large historical archive.

No bookmaker prices enter the feature vector. Every feature for game t is
computed from team state after games strictly before t.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import math


@dataclass
class TeamState:
    elo: float = 1500.0
    gf_ema: float = 2.75
    ga_ema: float = 2.75
    win_ema: float = 0.5
    home_gf_ema: float = 2.85
    home_ga_ema: float = 2.65
    away_gf_ema: float = 2.65
    away_ga_ema: float = 2.85
    games: int = 0
    last_date: date | None = None


def _ema(old: float, value: float, alpha: float) -> float:
    return alpha * value + (1.0 - alpha) * old


def _rest_days(last: date | None, current: date) -> float:
    if last is None:
        return 7.0
    return float(max(0, min(14, (current - last).days)))


def _season_reset(states: dict[str, TeamState], retain: float) -> None:
    retain=max(0.0,min(1.0,float(retain)))
    for s in states.values():
        s.elo=1500.0 + retain*(s.elo-1500.0)
        s.gf_ema=2.75 + retain*(s.gf_ema-2.75)
        s.ga_ema=2.75 + retain*(s.ga_ema-2.75)
        s.win_ema=0.5 + retain*(s.win_ema-0.5)
        s.home_gf_ema=2.85 + retain*(s.home_gf_ema-2.85)
        s.home_ga_ema=2.65 + retain*(s.home_ga_ema-2.65)
        s.away_gf_ema=2.65 + retain*(s.away_gf_ema-2.65)
        s.away_ga_ema=2.85 + retain*(s.away_ga_ema-2.85)


def build_features(
    rows: list[dict],
    alpha: float = 0.10,
    elo_k: float = 18.0,
    season_retain: float = 1.0,
) -> list[dict]:
    """Return rows augmented with pre-game features and binary home-win target.

    season_retain controls off-season mean reversion. 1.0 preserves all state;
    0.0 fully resets team strength toward league priors.
    """
    states: dict[str, TeamState] = defaultdict(TeamState)
    out: list[dict] = []
    previous_season = None

    for r in sorted(rows, key=lambda x: (x["date"], x["home"], x["away"])):
        if previous_season is not None and r["season"] != previous_season:
            _season_reset(states, season_retain)
        previous_season = r["season"]
        h, a = states[r["home"]], states[r["away"]]
        home_rest = _rest_days(h.last_date, r["date"])
        away_rest = _rest_days(a.last_date, r["date"])

        features = {
            "season": r["season"],
            "date": r["date"],
            "home": r["home"],
            "away": r["away"],
            "target": 1 if r["final_home"] > r["final_away"] else 0,
            "home_open": r["home_open"],
            "away_open": r["away_open"],
            "home_close": r["home_close"],
            "away_close": r["away_close"],
            # Independent model features only:
            "elo_diff": h.elo - a.elo,
            "gf_diff": h.gf_ema - a.gf_ema,
            "ga_diff": a.ga_ema - h.ga_ema,
            "win_diff": h.win_ema - a.win_ema,
            "venue_attack_diff": h.home_gf_ema - a.away_gf_ema,
            "venue_defence_diff": a.away_ga_ema - h.home_ga_ema,
            "rest_diff": home_rest - away_rest,
            "home_rest": home_rest,
            "away_rest": away_rest,
            "home_games": float(h.games),
            "away_games": float(a.games),
        }
        out.append(features)

        # Update only after the pre-game vector has been frozen.
        home_win = r["final_home"] > r["final_away"]
        exp_home = 1.0 / (1.0 + 10.0 ** ((a.elo - h.elo - 35.0) / 400.0))
        actual_home = 1.0 if home_win else 0.0
        margin = abs(r["final_home"] - r["final_away"])
        mult = math.log(max(1.0, margin) + 1.0)
        delta = elo_k * mult * (actual_home - exp_home)
        h.elo += delta
        a.elo -= delta

        h.gf_ema = _ema(h.gf_ema, r["reg_home"], alpha)
        h.ga_ema = _ema(h.ga_ema, r["reg_away"], alpha)
        a.gf_ema = _ema(a.gf_ema, r["reg_away"], alpha)
        a.ga_ema = _ema(a.ga_ema, r["reg_home"], alpha)
        h.win_ema = _ema(h.win_ema, 1.0 if home_win else 0.0, alpha)
        a.win_ema = _ema(a.win_ema, 0.0 if home_win else 1.0, alpha)

        h.home_gf_ema = _ema(h.home_gf_ema, r["reg_home"], alpha)
        h.home_ga_ema = _ema(h.home_ga_ema, r["reg_away"], alpha)
        a.away_gf_ema = _ema(a.away_gf_ema, r["reg_away"], alpha)
        a.away_ga_ema = _ema(a.away_ga_ema, r["reg_home"], alpha)

        h.games += 1
        a.games += 1
        h.last_date = r["date"]
        a.last_date = r["date"]

    return out
