"""Pre-match goals-intensity challenger fitted on historical goals.

Distinct from the hand-scaled xG fast/slow structural baseline. Fits two
regularized Poisson regressions (home and away goals) on frozen *prior-match*
rolling goals, proxy-xG, SoT/shots, rest, team strengths, venue and continuity.
No bookmaker prices as inputs. Every fit uses only earlier season outcomes.
"""
from __future__ import annotations

import math

from .goal_markets import goal_markets

# Feature positions are fixed by m17_17_research.build_regime_dataset() and
# two prior-season augmenters. No current-game goals, odds or closing prices.
# 1-16 rolling goals/xG, shots/SoT, venue, form/rest, league regime;
# 17-24 structurally opponent-adjusted fast/slow xG expectations;
# 34-38 current-season confidence, 39/40 Y-1 top-flight membership;
# 45-50 prior-season venue and 56-61 prior-season proxy-xG venue.
PREMATCH_FEATURE_INDEXES = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
    17, 18, 19, 20, 21, 22, 23, 24,
    34, 35, 36, 38, 39, 40,
    45, 46, 47, 48, 49, 50,
    56, 57, 58, 59, 60, 61,
)


def prematch_vector(row: dict) -> list[float]:
    """Reject missing/nonfinite historical features, never impute future data."""
    x = row["x"]
    if len(x) <= max(PREMATCH_FEATURE_INDEXES):
        raise ValueError("incomplete M17.17 rolling/venue/shot feature vector")
    chosen = [float(x[j]) for j in PREMATCH_FEATURE_INDEXES]
    if any(not math.isfinite(v) for v in chosen):
        raise ValueError("nonfinite historical model feature")
    return chosen


def _goals(row: dict) -> tuple[int, int]:
    if "home_goals" not in row or "away_goals" not in row:
        raise ValueError("missing historical labels; cannot train")
    h, a = int(row["home_goals"]), int(row["away_goals"])
    if h < 0 or a < 0 or h > 30 or a > 30:
        raise ValueError("invalid goals")
    return h, a


def predict_intensities(
    training: list[dict],
    test: list[dict],
    *,
    alpha: float,
    capped_goals: float = 5.8,
) -> list[tuple[float, float]]:
    """Independent home/away goal regressions, trained on strictly older rows."""
    # Research-only sklearn dependency is loaded on demand; production
    # scanners and CI without the extra do not import it accidentally.
    from sklearn.linear_model import PoissonRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if len(training) < 100 or not test:
        raise ValueError("too few training fixtures or no predictions requested")
    if not math.isfinite(alpha) or alpha <= 0:
        raise ValueError("positive Poisson regularization required")
    x = [prematch_vector(r) for r in training]
    y = [_goals(r) for r in training]
    x_future = [prematch_vector(r) for r in test]
    predictions = []
    for side in range(2):
        model = make_pipeline(
            StandardScaler(),
            PoissonRegressor(alpha=alpha, max_iter=250, tol=1e-6),
        )
        model.fit(x, [g[side] for g in y])
        predictions.append(model.predict(x_future))
    return [
        (
            max(0.08, min(capped_goals, float(h))),
            max(0.08, min(capped_goals, float(a))),
        )
        for h, a in zip(predictions[0], predictions[1])
    ]


def scored_rows(rows: list[dict],
                expected_goals: list[tuple[float, float]]) -> list[dict]:
    """Keep every row's independent intensity and pre-existing market quotes."""
    if len(rows) != len(expected_goals):
        raise ValueError("number of predicted games does not match feature rows")
    output = []
    for row, (h, a) in zip(rows, expected_goals):
        z = dict(row)
        # Compatibility with existing _losses / market-comparison code.
        # Both model intensity slots are the new trained intensity, not
        # reused M17.17 structural xG.
        z.update({
            "lambda_home_fast":h, "lambda_home_slow":h,
            "lambda_away_fast":a, "lambda_away_slow":a,
            "learned_home_goal_rate":h, "learned_away_goal_rate":a,
        })
        output.append(z)
    return output


def goal_nll(rows: list[dict]) -> dict:
    """Per-team Poisson negative log-likelihood for absolute goal predictions."""
    nll = mae = 0.0
    if not rows:
        return {"n":0, "goal_nll":None, "goal_mae":None}
    for r in rows:
        expected = (r["learned_home_goal_rate"], r["learned_away_goal_rate"])
        actual = _goals(r)
        for lam, goals in zip(expected, actual):
            nll += lam - goals * math.log(lam) + math.lgamma(goals+1)
            mae += abs(goals-lam)
    return {"n":len(rows), "goal_nll":nll/(2*len(rows)),
            "goal_mae":mae/(2*len(rows))}
