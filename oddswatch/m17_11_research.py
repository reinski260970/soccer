"""M17.11: structural opponent-adjusted team strengths for Portugal.

This is deliberately NOT another probability-calibration variant.

M17.8-M17.10 showed that fixed or previous-season class calibration cannot
solve the untouched 2024 degradation. M17.11 changes the football model itself
by adding leakage-safe latent attack/defense ratings that update sequentially
from pre-match expectations versus observed xG.

Structural layer
----------------
For every team, maintain fast and slow latent ratings:
- attack strength
- defensive suppression strength

Before a match:
    home_xg_hat = league_home_xg * exp(home_attack - away_defense)
    away_xg_hat = league_away_xg * exp(away_attack - home_defense)

After the match only, ratings are updated by bounded log xG residuals.
Therefore the current match result/xG can never enter its own feature row.

The existing rolling goals/xG/shots/SOT/form/rest features remain in place.
Previous-season venue priors and previous-season xG/luck priors remain
leakage-safe Y-1 context.

No bookmaker odds or market probabilities are model features.

Strict chronology remains unchanged:
- model hyperparameters: 2020/2021 OOS outcome logloss
- entry gate: rolling OOS 2022 + 2023 CLV
- strict holdout: rolling OOS 2024
- 2025: diagnostic only
"""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass
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
    _choose_gate,
    _market_logloss,
    mongo_coverage,
)
from .m17_6_research import build_previous_season_priors, augment_with_priors
from .m17_7_research import (
    build_previous_season_xg_priors,
    augment_with_xg_priors,
)
from .m17_8_research import _prob_diagnostics

OUT = Path("data/m17_11_validation.json")
FOCUS = {"primeira": "P1"}

FAST_K = 0.20
SLOW_K = 0.065
FAST_DECAY = 0.995
SLOW_DECAY = 0.999
RATING_LIMIT = 0.85
RESIDUAL_LIMIT = 0.80
LEAGUE_ALPHA = 0.03


@dataclass
class StrengthState:
    n: int = 0
    attack_fast: float = 0.0
    defense_fast: float = 0.0
    attack_slow: float = 0.0
    defense_slow: float = 0.0


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def _safe_exp(v: float) -> float:
    return math.exp(_clip(v, -1.25, 1.25))


def _expected_xg(
    league_home_xg: float,
    league_away_xg: float,
    home: StrengthState,
    away: StrengthState,
) -> dict[str, float]:
    """Pre-match opponent-adjusted xG expectations at two time scales."""
    return {
        "home_fast": _clip(
            league_home_xg * _safe_exp(home.attack_fast - away.defense_fast),
            0.20,
            4.50,
        ),
        "away_fast": _clip(
            league_away_xg * _safe_exp(away.attack_fast - home.defense_fast),
            0.20,
            4.50,
        ),
        "home_slow": _clip(
            league_home_xg * _safe_exp(home.attack_slow - away.defense_slow),
            0.20,
            4.50,
        ),
        "away_slow": _clip(
            league_away_xg * _safe_exp(away.attack_slow - home.defense_slow),
            0.20,
            4.50,
        ),
    }


def _structural_features(
    league_home_xg: float,
    league_away_xg: float,
    home: StrengthState,
    away: StrengthState,
) -> list[float]:
    e = _expected_xg(league_home_xg, league_away_xg, home, away)
    conf_h = min(home.n, 20) / 20.0
    conf_a = min(away.n, 20) / 20.0
    return [
        e["home_fast"],
        e["away_fast"],
        e["home_fast"] - e["away_fast"],
        e["home_fast"] + e["away_fast"],
        e["home_slow"],
        e["away_slow"],
        e["home_slow"] - e["away_slow"],
        e["home_slow"] + e["away_slow"],
        home.attack_fast - away.defense_fast,
        away.attack_fast - home.defense_fast,
        home.attack_slow - away.defense_slow,
        away.attack_slow - home.defense_slow,
        home.attack_fast - home.attack_slow,
        away.attack_fast - away.attack_slow,
        home.defense_fast - home.defense_slow,
        away.defense_fast - away.defense_slow,
        conf_h - conf_a,
    ]


def _rating_residual(observed: float, expected: float) -> float:
    # Log residual makes a +0.5 xG miss more meaningful around 0.8 than 3.0.
    r = math.log((max(float(observed), 0.0) + 0.25) /
                 (max(float(expected), 0.0) + 0.25))
    return _clip(r, -RESIDUAL_LIMIT, RESIDUAL_LIMIT)


def _decay_and_clip(st: StrengthState) -> None:
    st.attack_fast = _clip(st.attack_fast * FAST_DECAY, -RATING_LIMIT, RATING_LIMIT)
    st.defense_fast = _clip(st.defense_fast * FAST_DECAY, -RATING_LIMIT, RATING_LIMIT)
    st.attack_slow = _clip(st.attack_slow * SLOW_DECAY, -RATING_LIMIT, RATING_LIMIT)
    st.defense_slow = _clip(st.defense_slow * SLOW_DECAY, -RATING_LIMIT, RATING_LIMIT)


def _update_strengths(
    home: StrengthState,
    away: StrengthState,
    observed_home_xg: float,
    observed_away_xg: float,
    league_home_xg: float,
    league_away_xg: float,
) -> None:
    """Update only AFTER feature generation for the current match."""
    expected = _expected_xg(league_home_xg, league_away_xg, home, away)
    rf_h = _rating_residual(observed_home_xg, expected["home_fast"])
    rf_a = _rating_residual(observed_away_xg, expected["away_fast"])
    rs_h = _rating_residual(observed_home_xg, expected["home_slow"])
    rs_a = _rating_residual(observed_away_xg, expected["away_slow"])

    _decay_and_clip(home)
    _decay_and_clip(away)

    # Expected log xG is attack - opponent defense.
    # Positive residual => attack was stronger and opponent defense weaker.
    home.attack_fast += FAST_K * rf_h
    away.defense_fast -= FAST_K * rf_h
    away.attack_fast += FAST_K * rf_a
    home.defense_fast -= FAST_K * rf_a

    home.attack_slow += SLOW_K * rs_h
    away.defense_slow -= SLOW_K * rs_h
    away.attack_slow += SLOW_K * rs_a
    home.defense_slow -= SLOW_K * rs_a

    for st in (home, away):
        st.attack_fast = _clip(st.attack_fast, -RATING_LIMIT, RATING_LIMIT)
        st.defense_fast = _clip(st.defense_fast, -RATING_LIMIT, RATING_LIMIT)
        st.attack_slow = _clip(st.attack_slow, -RATING_LIMIT, RATING_LIMIT)
        st.defense_slow = _clip(st.defense_slow, -RATING_LIMIT, RATING_LIMIT)
        st.n += 1


def _apply_season_carry(
    strengths,
    fast_carry: float,
    slow_carry: float,
) -> None:
    """Offseason shrinkage applied before any new-season feature row."""
    fc = _clip(fast_carry, 0.0, 1.0)
    sc = _clip(slow_carry, 0.0, 1.0)
    for st in strengths.values():
        st.attack_fast *= fc
        st.defense_fast *= fc
        st.attack_slow *= sc
        st.defense_slow *= sc


def build_structural_dataset(
    matches,
    odds_rows,
    shot_map,
    season_fast_carry: float = 1.0,
    season_slow_carry: float = 1.0,
) -> list[dict]:
    """Existing rolling features + structural ratings, all strictly pre-match."""
    odds = {
        (d, h, a): (season, hg, ag, op, cl)
        for season, d, h, a, hg, ag, op, cl in odds_rows
    }
    states = defaultdict(TeamState)
    strengths = defaultdict(StrengthState)
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
        if previous_season is not None and season != previous_season:
            _apply_season_carry(
                strengths,
                season_fast_carry,
                season_slow_carry,
            )
        previous_season = season
        shot = shot_map.get((season, h, a))
        hs, as_ = states[h], states[a]
        hr, ar = strengths[h], strengths[a]

        # IMPORTANT: feature row is built BEFORE any current-match update.
        if hs.n >= 6 and as_.n >= 6 and (d, h, a) in odds and shot is not None:
            s, hg, ag, op, cl = odds[(d, h, a)]
            expected = _expected_xg(
                league["home_xg"], league["away_xg"], hr, ar
            )
            x = _features(hs, as_, league, d)
            x += _structural_features(
                league["home_xg"], league["away_xg"], hr, ar
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
                # Gate-only pre-match uncertainty metadata. These fields are
                # never model inputs and are available before kickoff.
                "structural_uncertainty": (
                    abs(expected["home_fast"] - expected["home_slow"])
                    + abs(expected["away_fast"] - expected["away_slow"])
                ),
                "home_structural_uncertainty": abs(
                    expected["home_fast"] - expected["home_slow"]
                ),
                "away_structural_uncertainty": abs(
                    expected["away_fast"] - expected["away_slow"]
                ),
            })

        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = _xg(m, True), _xg(m, False)

        # Structural update uses current xG only after current features exist.
        _update_strengths(
            hr,
            ar,
            hx,
            ax,
            league["home_xg"],
            league["away_xg"],
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

        league["n"] += 1
        league["home"] += int(hg > ag)
        league["draw"] += int(hg == ag)
        league["away"] += int(hg < ag)
        n = league["n"]
        league["home_rate"] = league["home"] / n
        league["draw_rate"] = league["draw"] / n
        league["away_rate"] = league["away"] / n
        league["goals"] = (1.0 - LEAGUE_ALPHA) * league["goals"] + LEAGUE_ALPHA * (hg + ag)
        league["home_xg"] = (1.0 - LEAGUE_ALPHA) * league["home_xg"] + LEAGUE_ALPHA * hx
        league["away_xg"] = (1.0 - LEAGUE_ALPHA) * league["away_xg"] + LEAGUE_ALPHA * ax

    return out


def _league_run(matches, odds_rows, shots, cov):
    base = build_structural_dataset(matches, odds_rows, shots)
    venue_priors = build_previous_season_priors(matches)
    data, venue_cov = augment_with_priors(base, venue_priors)
    xg_priors = build_previous_season_xg_priors(matches)
    data, xg_cov = augment_with_xg_priors(data, xg_priors)

    result = {
        "samples": len(data),
        "coverage": cov,
        "previous_season_prior_coverage": venue_cov,
        "previous_season_xg_prior_coverage": xg_cov,
        "structural_feature_count": 17,
        "structural_rule": (
            "fast/slow opponent-adjusted attack/defense ratings updated after match "
            "from bounded log xG residuals"
        ),
    }

    if cov.get("proxy_coverage", 0.0) < 0.70:
        result.update({
            "validated": False,
            "reason": "historical shot/corner proxy coverage <70%",
        })
        return result

    hyper = _early_hyper(data)
    result["hyper"] = hyper
    if hyper is None:
        result.update({
            "validated": False,
            "reason": "too little strict early walk-forward data",
        })
        return result

    tune = {
        2022: _rolling_eval(data, 2022, hyper),
        2023: _rolling_eval(data, 2023, hyper),
    }
    if any(len(v) < 60 for v in tune.values()):
        result.update({
            "validated": False,
            "reason": "too little 2022/2023 OOS tune data",
            "tune_counts": {str(k): len(v) for k, v in tune.items()},
        })
        return result

    gate, near = _choose_gate(tune)
    hold_eval = _rolling_eval(data, 2024, hyper)
    diag_eval = _rolling_eval(data, 2025, hyper)
    use_gate = gate or near

    empty = {
        "bets": 0,
        "clv": 0.0,
        "median_clv": 0.0,
        "positive_clv_rate": 0.0,
        "roi": 0.0,
    }
    hold = (
        _entry_stats(hold_eval, use_gate["edge"], use_gate["cap"], use_gate["side"])
        if use_gate and hold_eval
        else dict(empty)
    )
    diag = (
        _entry_stats(diag_eval, use_gate["edge"], use_gate["cap"], use_gate["side"])
        if use_gate and diag_eval
        else dict(empty)
    )

    hold_rows = [r for r in data if r["season"] == 2024]
    hold_model_ll = (
        _logloss([r["p"] for r in hold_eval], [r["y"] for r in hold_eval])
        if hold_eval else 9.0
    )
    hold_market_ll = _market_logloss(hold_rows)

    strategy_ok = bool(
        gate is not None
        and hold["bets"] >= 15
        and hold["clv"] > 0
        and hold["median_clv"] > 0
        and hold["positive_clv_rate"] >= 0.52
    )
    model_ok = hold_model_ll < hold_market_ll
    validated = bool(strategy_ok and model_ok)

    result.update({
        "validated": validated,
        "strategy_validated": strategy_ok,
        "model_beats_opening_logloss": model_ok,
        "gate": gate,
        "near_miss_gate": near,
        "strict_holdout_2024": hold,
        "strict_holdout_logloss": {
            "model": hold_model_ll,
            "opening": hold_market_ll,
            "gain": hold_market_ll - hold_model_ll,
        },
        "diagnostic_only_2025": diag,
        "probability_diagnostics": {
            "2022": _prob_diagnostics(tune[2022]),
            "2023": _prob_diagnostics(tune[2023]),
            "2024": _prob_diagnostics(hold_eval),
            "2025": _prob_diagnostics(diag_eval),
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
            "M17.11 structural opponent-adjusted fast/slow attack-defense ratings "
            "+ existing rolling xG/shots/SOT/form/rest + Y-1 priors; no market features"
        ),
        "_focus": FOCUS,
        "_proxy": {
            "n": proxy["n"],
            "rmse": proxy["rmse"],
            "beta": proxy["beta"],
            "features": proxy["features"],
        },
        "_splits": {
            "hyper_A": "train<=2019 validate=2020 outcome logloss",
            "hyper_B": "train<=2020 validate=2021 outcome logloss",
            "entry_tune": "rolling OOS 2022 + 2023 CLV",
            "strict_holdout": "rolling OOS 2024",
            "diagnostic_only": "rolling OOS 2025",
        },
        "_release_rule": (
            "unchanged: robust 2022+2023 CLV gate AND 2024 >=15 bets, "
            "mean/median CLV>0, positive CLV rate>=52%, "
            "AND model 2024 logloss < Pinnacle opening"
        ),
        "mongo_profile": profile,
        "leagues": {},
    }

    log = [f"M17.11 proxy: n={proxy['n']} RMSE={proxy['rmse']:.3f}"]

    for league, code in FOCUS.items():
        try:
            matches, rows, cov = load_league(
                code, proxy, start_year=START_YEAR, end_year=END_YEAR
            )
            shots = load_real_shots(
                code, start_year=START_YEAR, end_year=END_YEAR
            )
            r = _league_run(matches, rows, shots, cov)
        except Exception as exc:
            r = {
                "validated": False,
                "reason": f"load/research failed: {type(exc).__name__}: {exc}",
            }

        result["leagues"][league] = r
        gate = r.get("gate") or r.get("near_miss_gate") or {}
        ts = gate.get("stats") or {}
        hs = r.get("strict_holdout_2024") or {}
        ll = r.get("strict_holdout_logloss") or {}
        h = r.get("hyper") or {}
        log.append(
            f"{league}: samples={r.get('samples',0)} "
            f"l2={h.get('l2')} calib={h.get('calib')} "
            f"earlyLL={h.get('cv_logloss',0):.4f} | "
            f"gate={'OK' if r.get('gate') else 'NONE'} "
            f"{gate.get('side','-')} edge={gate.get('edge')} cap={gate.get('cap')} "
            f"tune n={ts.get('bets',0)} CLV={ts.get('clv',0)*100:+.2f}% | "
            f"hold n={hs.get('bets',0)} CLV={hs.get('clv',0)*100:+.2f}% "
            f"med={hs.get('median_clv',0)*100:+.2f}% "
            f"pos={hs.get('positive_clv_rate',0)*100:.1f}% "
            f"dLL={ll.get('gain',0):+.4f} -> "
            + ("RELEASE" if r.get("validated") else "NO RELEASE")
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
