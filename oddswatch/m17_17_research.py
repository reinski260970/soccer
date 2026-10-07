"""M17.17: season-regime and top-flight continuity features.

M17.11 remains the structural reference model. M17.17 changes the football
inputs, not the market gate:

- reset stale rolling/structural team state when a club was absent from the
  immediately previous top-flight season
- add leakage-safe current-season match-count / early-season uncertainty
- add previous-season top-flight presence and season-gap features
- keep structural fast/slow attack-defense ratings, rolling xG, shots/SOT,
  form/rest and Y-1 priors
- never use bookmaker odds as model features

IMPORTANT METHODOLOGY
---------------------
2024 has been inspected repeatedly during M17.5-M17.16 research. It is no
longer treated as a pristine release holdout. M17.17 therefore labels 2024 a
retrospective stress test and is NEVER production-release eligible from this
backtest alone. Real release requires forward/shadow CLV on future data.

Chronology:
- model hyperparameters: 2020/2021 OOS outcome logloss
- entry tune: 2022 only
- entry validation: 2023 only
- retrospective stress: 2024
- diagnostic only: 2025
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from .m12_research import _season_start
from .m14_research import load_league, train_proxy
from .m17_1_research import (
    TeamState,
    _features,
    _update,
    _xg,
    _points,
    load_real_shots,
    _logloss,
    _entry_stats,
)
from .m17_5_research import (
    START_YEAR,
    END_YEAR,
    _early_hyper,
    _rolling_eval,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import build_previous_season_xg_priors, augment_with_xg_priors
from .m17_8_research import _prob_diagnostics
from .m17_11_research import (
    StrengthState,
    _expected_xg,
    _structural_features,
    _update_strengths,
)
from .m17_16_research import _tune_gate_2022, _validate_gate_2023

OUT = Path("data/m17_17_validation.json")
FOCUS = {"primeira": "P1"}

CURRENT_SEASON_CONF_GAMES = 10
MAX_SEASON_GAP = 3


def _season_membership(matches):
    members = defaultdict(set)
    last_season = {}
    for m in matches:
        s = _season_start(m.date)
        members[s].add(m.home)
        members[s].add(m.away)
        last_season[m.home] = max(s, last_season.get(m.home, s))
        last_season[m.away] = max(s, last_season.get(m.away, s))
    return dict(members)


def _gap_from_previous_membership(
    team: str,
    season: int,
    membership: dict[int, set[str]],
) -> int:
    """0 if present in Y-1, otherwise capped number of missed top-flight seasons."""
    if team in membership.get(season - 1, set()):
        return 0
    for gap in range(1, MAX_SEASON_GAP + 1):
        if team in membership.get(season - 1 - gap, set()):
            return gap
    return MAX_SEASON_GAP


def _regime_features(
    home: str,
    away: str,
    season: int,
    season_games: dict[str, int],
    membership: dict[int, set[str]],
) -> list[float]:
    hg = int(season_games.get(home, 0))
    ag = int(season_games.get(away, 0))
    h_conf = min(hg, CURRENT_SEASON_CONF_GAMES) / CURRENT_SEASON_CONF_GAMES
    a_conf = min(ag, CURRENT_SEASON_CONF_GAMES) / CURRENT_SEASON_CONF_GAMES

    prev = membership.get(season - 1, set())
    h_prev = 1.0 if home in prev else 0.0
    a_prev = 1.0 if away in prev else 0.0

    h_gap = _gap_from_previous_membership(home, season, membership)
    a_gap = _gap_from_previous_membership(away, season, membership)
    early = 1.0 - min(h_conf, a_conf)

    return [
        h_conf,
        a_conf,
        min(h_conf, a_conf),
        h_conf - a_conf,
        early,
        h_prev,
        a_prev,
        h_prev * a_prev,
        h_gap / MAX_SEASON_GAP,
        a_gap / MAX_SEASON_GAP,
        (h_gap - a_gap) / MAX_SEASON_GAP,
    ]


def _reset_team_state(states, strengths, team: str) -> None:
    """Remove stale top-flight state before a returning/promoted club's first row."""
    states[team] = TeamState()
    strengths[team] = StrengthState()


def build_regime_dataset(matches, odds_rows, shot_map) -> list[dict]:
    odds = {
        (d, h, a): (season, hg, ag, op, cl)
        for season, d, h, a, hg, ag, op, cl in odds_rows
    }
    membership = _season_membership(matches)

    states = defaultdict(TeamState)
    strengths = defaultdict(StrengthState)
    season_games = defaultdict(int)
    reset_done = set()

    league = {
        "n": 0,
        "home": 0,
        "draw": 0,
        "away": 0,
        "home_rate": 0.45,
        "draw_rate": 0.27,
        "away_rate": 0.28,
        "goals": 2.70,
        "home_xg": 1.45,
        "away_xg": 1.20,
    }
    out = []
    previous_season = None

    for m in sorted(matches, key=lambda z: z.date):
        d, h, a = m.date, m.home, m.away
        season = _season_start(d)

        if previous_season is None or season != previous_season:
            season_games = defaultdict(int)
            reset_done = set()
            previous_season = season

        # Before a club's first match of season Y, reset stale state if it did
        # not participate in Y-1. Membership is schedule/league-status context.
        for team in (h, a):
            key = (season, team)
            if key not in reset_done:
                if team not in membership.get(season - 1, set()):
                    _reset_team_state(states, strengths, team)
                reset_done.add(key)

        shot = shot_map.get((season, h, a))
        hs, as_ = states[h], states[a]
        hr, ar = strengths[h], strengths[a]

        if hs.n >= 6 and as_.n >= 6 and (d, h, a) in odds and shot is not None:
            s, hg, ag, op, cl = odds[(d, h, a)]
            expected = _expected_xg(
                league["home_xg"], league["away_xg"], hr, ar
            )
            x = _features(hs, as_, league, d)
            x += _structural_features(
                league["home_xg"], league["away_xg"], hr, ar
            )
            x += _regime_features(
                h, a, season, season_games, membership
            )
            out.append({
                "season": s,
                "date": d,
                "home": h,
                "away": a,
                "x": x,
                "y": 0 if hg > ag else (1 if hg == ag else 2),
                "op": op,
                "cl": cl,
                "early_season_uncertainty": 1.0 - min(
                    min(season_games[h], CURRENT_SEASON_CONF_GAMES)
                    / CURRENT_SEASON_CONF_GAMES,
                    min(season_games[a], CURRENT_SEASON_CONF_GAMES)
                    / CURRENT_SEASON_CONF_GAMES,
                ),
                "home_prev_topflight": h in membership.get(season - 1, set()),
                "away_prev_topflight": a in membership.get(season - 1, set()),
                "home_season_gap": _gap_from_previous_membership(
                    h, season, membership
                ),
                "away_season_gap": _gap_from_previous_membership(
                    a, season, membership
                ),
                "structural_uncertainty": (
                    abs(expected["home_fast"] - expected["home_slow"])
                    + abs(expected["away_fast"] - expected["away_slow"])
                ),
            })

        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = _xg(m, True), _xg(m, False)

        _update_strengths(
            hr, ar, hx, ax, league["home_xg"], league["away_xg"]
        )

        if shot is not None:
            hshots, ashots, hsot, asot = shot
            _update(
                hs, hg, ag, hx, ax, hshots, ashots, hsot, asot,
                _points(hg, ag), d, True,
            )
            _update(
                as_, ag, hg, ax, hx, ashots, hshots, asot, hsot,
                _points(ag, hg), d, False,
            )
        else:
            _update(
                hs, hg, ag, hx, ax,
                hs.shots_f, hs.shots_a, hs.sot_f, hs.sot_a,
                _points(hg, ag), d, True,
            )
            _update(
                as_, ag, hg, ax, hx,
                as_.shots_f, as_.shots_a, as_.sot_f, as_.sot_a,
                _points(ag, hg), d, False,
            )

        season_games[h] += 1
        season_games[a] += 1

        league["n"] += 1
        league["home"] += int(hg > ag)
        league["draw"] += int(hg == ag)
        league["away"] += int(hg < ag)
        n = league["n"]
        league["home_rate"] = league["home"] / n
        league["draw_rate"] = league["draw"] / n
        league["away_rate"] = league["away"] / n
        league["goals"] = 0.97 * league["goals"] + 0.03 * (hg + ag)
        league["home_xg"] = 0.97 * league["home_xg"] + 0.03 * hx
        league["away_xg"] = 0.97 * league["away_xg"] + 0.03 * ax

    return out


def _build_data(matches, odds_rows, shots):
    base = build_regime_dataset(matches, odds_rows, shots)
    venue_priors = build_previous_season_priors(matches)
    data, venue_cov = augment_with_priors(base, venue_priors)
    xg_priors = build_previous_season_xg_priors(matches)
    data, xg_cov = augment_with_xg_priors(data, xg_priors)
    return data, venue_cov, xg_cov


def _league_run(matches, odds_rows, shots, cov):
    data, venue_cov, xg_cov = _build_data(matches, odds_rows, shots)
    result = {
        "samples": len(data),
        "coverage": cov,
        "previous_season_prior_coverage": venue_cov,
        "previous_season_xg_prior_coverage": xg_cov,
        "regime_feature_count": 11,
        "release_eligible": False,
        "release_block_reason": (
            "2024/2025 have already been inspected during iterative research; "
            "future forward/shadow validation required"
        ),
    }

    hyper = _early_hyper(data)
    result["hyper"] = hyper
    if hyper is None:
        result.update({"validated": False, "reason": "too little early OOS data"})
        return result

    eval_2022 = _rolling_eval(data, 2022, hyper)
    eval_2023 = _rolling_eval(data, 2023, hyper)
    eval_2024 = _rolling_eval(data, 2024, hyper)
    eval_2025 = _rolling_eval(data, 2025, hyper)

    gate_2022, near_2022 = _tune_gate_2022(eval_2022)
    survived_2023, validation_2023 = _validate_gate_2023(eval_2023, gate_2022)
    diagnostic_gate = gate_2022 or near_2022

    empty = {
        "bets": 0,
        "clv": 0.0,
        "median_clv": 0.0,
        "positive_clv_rate": 0.0,
        "roi": 0.0,
    }
    stress_2024 = (
        _entry_stats(
            eval_2024,
            diagnostic_gate["edge"],
            diagnostic_gate["cap"],
            diagnostic_gate["side"],
        )
        if diagnostic_gate and eval_2024 else dict(empty)
    )
    diag_2025 = (
        _entry_stats(
            eval_2025,
            diagnostic_gate["edge"],
            diagnostic_gate["cap"],
            diagnostic_gate["side"],
        )
        if diagnostic_gate and eval_2025 else dict(empty)
    )

    rows_2024 = [r for r in data if r["season"] == 2024]
    ll_model = (
        _logloss([r["p"] for r in eval_2024], [r["y"] for r in eval_2024])
        if eval_2024 else 9.0
    )
    ll_market = _market_logloss(rows_2024)

    # Deliberately never production-valid from already-observed backtest years.
    result.update({
        "validated": False,
        "strategy_validated": False,
        "model_beats_opening_logloss_2024_research": ll_model < ll_market,
        "tuned_gate_2022": gate_2022,
        "near_miss_2022": near_2022,
        "entry_validation_2023": validation_2023,
        "gate_survived_2023": survived_2023,
        "retrospective_stress_2024": stress_2024,
        "retrospective_stress_logloss_2024": {
            "model": ll_model,
            "opening": ll_market,
            "gain": ll_market - ll_model,
        },
        "diagnostic_only_2025": diag_2025,
        "probability_diagnostics": {
            "2022": _prob_diagnostics(eval_2022),
            "2023": _prob_diagnostics(eval_2023),
            "2024": _prob_diagnostics(eval_2024),
            "2025": _prob_diagnostics(eval_2025),
        },
    })
    return result


def run(out: Path = OUT):
    if not os.environ.get("MONGO_SOCCER") and os.environ.get("MONGODB_URI"):
        os.environ["MONGO_SOCCER"] = os.environ["MONGODB_URI"]

    profile = mongo_coverage()
    proxy = train_proxy()

    result = {
        "_method": (
            "M17.17 M17.11 structural model + top-flight continuity reset + "
            "current-season confidence/regime features; no market features"
        ),
        "_focus": FOCUS,
        "_methodology_note": (
            "2024 is retrospective research stress, NOT an untouched release "
            "holdout; production release requires future forward/shadow CLV"
        ),
        "_splits": {
            "model_hyper_A": "train<=2019 validate=2020 outcome logloss",
            "model_hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "2022 only",
            "entry_validation": "2023 only",
            "retrospective_stress": "2024",
            "diagnostic_only": "2025",
        },
        "mongo_profile": profile,
        "leagues": {},
    }

    log = [f"M17.17 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]
    for league, code in FOCUS.items():
        try:
            matches, rows, cov = load_league(
                code, proxy, start_year=START_YEAR, end_year=END_YEAR
            )
            shots = load_real_shots(code, start_year=START_YEAR, end_year=END_YEAR)
            r = _league_run(matches, rows, shots, cov)
        except Exception as exc:
            r = {
                "validated": False,
                "release_eligible": False,
                "reason": f"load/research failed: {type(exc).__name__}: {exc}",
            }

        result["leagues"][league] = r
        g = r.get("tuned_gate_2022") or r.get("near_miss_2022") or {}
        s22 = g.get("stats_2022") or {}
        s23 = r.get("entry_validation_2023") or {}
        s24 = r.get("retrospective_stress_2024") or {}
        ll = r.get("retrospective_stress_logloss_2024") or {}
        log.append(
            f"{league}: earlyLL={(r.get('hyper') or {}).get('cv_logloss',0):.4f} | "
            f"2022 n={s22.get('bets',0)} CLV={s22.get('clv',0)*100:+.2f}% | "
            f"2023 pass={r.get('gate_survived_2023')} "
            f"CLV={s23.get('clv',0)*100:+.2f}% | "
            f"2024 stress n={s24.get('bets',0)} CLV={s24.get('clv',0)*100:+.2f}% "
            f"dLL={ll.get('gain',0):+.4f} -> NO RELEASE (forward validation required)"
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=1, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    log.append(f"gespeichert: {out}")
    return log


if __name__ == "__main__":
    for line in run():
        print(line)
