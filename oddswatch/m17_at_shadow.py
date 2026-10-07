"""M17.11-AT shadow scorer for the Austrian Bundesliga.

Austria has a long public result history (football-data AUT.csv) but no
historical xG/shot columns. Therefore this module does NOT pretend to be the
full M17.11 model used in Primeira research.

It keeps the M17.11 structural core:
- fast/slow opponent-adjusted attack/defense strengths
- strict chronological updates after each match
- rolling form/home-away/rest/league context
- no bookmaker odds as model features

Observed goals are used for structural residual updates because historical xG
is unavailable. Current external xG may be reported by the caller as context
but is not injected into probabilities until historically validated.

Model selection uses outcome logloss only on historical walk-forward seasons.
Market prices are attached later by the scan/entry layer.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import math

from .m12_research import _season_start
from .m17_1_research import (
    TeamState,
    _calibrate,
    _fit,
    _logloss,
    _points,
    _pred,
    _rest,
    _standardizer,
    _tx,
    _update,
)
from .m17_11_research import (
    StrengthState,
    _apply_season_carry,
    _expected_xg,
    _structural_features,
    _update_strengths,
)

L2_GRID = (0.05, 0.25, 1.0)
CALIB_GRID = (0.80, 0.90, 1.00, 1.10)
FAST_CARRY = 0.55
SLOW_CARRY = 0.85


@dataclass
class AustriaShadowModel:
    weights: list[list[float]]
    mean: list[float]
    sd: list[float]
    calib: float
    l2: float
    cv_logloss: float
    fold_logloss: list[float]
    states: dict[str, TeamState]
    strengths: dict[str, StrengthState]
    league: dict
    samples: int
    history_first: date
    history_last: date

    def teams(self) -> list[str]:
        return sorted(self.states)

    def predict(self, home: str, away: str, kickoff: date) -> tuple[dict[str, float], dict]:
        if home not in self.states or away not in self.states:
            raise KeyError(f"unknown Austria team: {home} / {away}")
        hs, as_ = self.states[home], self.states[away]
        hr, ar = self.strengths[home], self.strengths[away]
        x = _features(hs, as_, self.league, kickoff)
        xt = _tx([x], self.mean, self.sd)[0]
        p = _calibrate(_pred(self.weights, xt), self.calib)
        exp = _expected_xg(
            self.league["home_xg"], self.league["away_xg"], hr, ar
        )
        return {
            "home": p[0],
            "draw": p[1],
            "away": p[2],
        }, {
            "home_fast": exp["home_fast"],
            "away_fast": exp["away_fast"],
            "home_slow": exp["home_slow"],
            "away_slow": exp["away_slow"],
            "home_n": hs.n,
            "away_n": as_.n,
        }


def _features(hs: TeamState, as_: TeamState, league: dict, d: date) -> list[float]:
    conf_h = min(hs.n, 20) / 20.0
    conf_a = min(as_.n, 20) / 20.0
    base = [
        1.0,
        hs.gf - as_.ga,
        as_.gf - hs.ga,
        hs.pts - as_.pts,
        hs.home_gf - as_.away_ga,
        as_.away_gf - hs.home_ga,
        _rest(hs, d) - _rest(as_, d),
        conf_h - conf_a,
        league["home_rate"] - league["away_rate"],
        league["draw_rate"],
        league["goals"],
    ]
    base += _structural_features(
        league["home_xg"], league["away_xg"],
        league["_home_strength"], league["_away_strength"]
    ) if False else []
    return base


def _row_features(hs, as_, league, d, hr, ar) -> list[float]:
    return _features(hs, as_, league, d) + _structural_features(
        league["home_xg"], league["away_xg"], hr, ar
    )


def _neutral_team_state() -> TeamState:
    return TeamState()


def _neutral_strength_state() -> StrengthState:
    return StrengthState()


def _build(matches) -> tuple[list[dict], dict, dict, dict]:
    matches = sorted(matches, key=lambda m: m.date)
    participants = defaultdict(set)
    for m in matches:
        s = _season_start(m.date)
        participants[s].update((m.home, m.away))

    states = defaultdict(_neutral_team_state)
    strengths = defaultdict(_neutral_strength_state)
    league = {
        "n": 0,
        "home": 0,
        "draw": 0,
        "away": 0,
        "home_rate": 0.45,
        "draw_rate": 0.27,
        "away_rate": 0.28,
        "goals": 2.70,
        # M17 structural helper names these xG; in Austria these are explicitly
        # league scoring-rate baselines, not historical xG.
        "home_xg": 1.45,
        "away_xg": 1.20,
    }
    rows = []
    prev_season = None

    for m in matches:
        d, h, a = m.date, m.home, m.away
        season = _season_start(d)

        if prev_season is not None and season != prev_season:
            _apply_season_carry(strengths, FAST_CARRY, SLOW_CARRY)
            previous_teams = participants.get(prev_season, set())
            for team in participants.get(season, set()):
                if team not in previous_teams:
                    states[team] = TeamState()
                    strengths[team] = StrengthState()
        prev_season = season

        hs, as_ = states[h], states[a]
        hr, ar = strengths[h], strengths[a]

        if hs.n >= 6 and as_.n >= 6:
            rows.append({
                "season": season,
                "date": d,
                "home": h,
                "away": a,
                "x": _row_features(hs, as_, league, d, hr, ar),
                "y": 0 if m.home_goals > m.away_goals else (
                    1 if m.home_goals == m.away_goals else 2
                ),
            })

        hg, ag = float(m.home_goals), float(m.away_goals)

        # Austria historical source has no xG. Structural residual updates are
        # explicitly goals-based in this shadow adaptation.
        _update_strengths(
            hr, ar, hg, ag,
            league["home_xg"], league["away_xg"]
        )

        _update(
            hs, hg, ag, hg, ag,
            hs.shots_f, hs.shots_a, hs.sot_f, hs.sot_a,
            _points(hg, ag), d, True,
        )
        _update(
            as_, ag, hg, ag, hg,
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
        league["goals"] = 0.97 * league["goals"] + 0.03 * (hg + ag)
        league["home_xg"] = 0.97 * league["home_xg"] + 0.03 * hg
        league["away_xg"] = 0.97 * league["away_xg"] + 0.03 * ag

    return rows, dict(states), dict(strengths), league


def _choose_hyper(rows: list[dict]) -> dict:
    # Stable historical OOS folds. 2025/26 remain untouched by model selection.
    folds = []
    for season in (2022, 2023, 2024):
        tr = [r for r in rows if r["season"] < season]
        va = [r for r in rows if r["season"] == season]
        if len(tr) >= 500 and len(va) >= 100:
            folds.append((tr, va))
    if not folds:
        raise RuntimeError("too little Austria walk-forward history")

    best = None
    for l2 in L2_GRID:
        raw = []
        for tr, va in folds:
            mean, sd = _standardizer([r["x"] for r in tr])
            w = _fit(_tx([r["x"] for r in tr], mean, sd),
                     [r["y"] for r in tr], l2)
            pp = [_pred(w, x) for x in _tx([r["x"] for r in va], mean, sd)]
            raw.append((va, pp))
        for calib in CALIB_GRID:
            losses = []
            for va, pp in raw:
                losses.append(_logloss(
                    [_calibrate(p, calib) for p in pp],
                    [r["y"] for r in va],
                ))
            score = sum(losses) / len(losses)
            cand = {
                "l2": l2,
                "calib": calib,
                "cv_logloss": score,
                "fold_logloss": losses,
            }
            if best is None or score < best["cv_logloss"]:
                best = cand
    return best


def fit(matches) -> AustriaShadowModel:
    if not matches:
        raise RuntimeError("empty Austria history")
    rows, states, strengths, league = _build(matches)
    hyper = _choose_hyper(rows)
    mean, sd = _standardizer([r["x"] for r in rows])
    weights = _fit(
        _tx([r["x"] for r in rows], mean, sd),
        [r["y"] for r in rows],
        hyper["l2"],
    )
    return AustriaShadowModel(
        weights=weights,
        mean=mean,
        sd=sd,
        calib=hyper["calib"],
        l2=hyper["l2"],
        cv_logloss=hyper["cv_logloss"],
        fold_logloss=list(hyper["fold_logloss"]),
        states=states,
        strengths=strengths,
        league=league,
        samples=len(rows),
        history_first=min(m.date for m in matches),
        history_last=max(m.date for m in matches),
    )
