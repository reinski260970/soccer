from datetime import date, timedelta

from oddswatch.models.m9 import M9Model, M9Params
from oddswatch.models.poisson import Match


def _matches():
    start = date(2025, 1, 1)
    teams = ["A", "B", "C", "D"]
    out = []
    for i in range(90):
        h = teams[i % 4]
        a = teams[(i + 1 + (i // 5) % 3) % 4]
        if h == a:
            a = teams[(teams.index(a) + 1) % 4]
        hg = float((i * 3 + 1) % 4)
        ag = float((i * 2 + 2) % 3)
        hx = max(0.25, 0.55 + 0.55 * hg + 0.08 * (i % 3))
        ax = max(0.25, 0.50 + 0.55 * ag + 0.06 * ((i + 1) % 3))
        out.append(Match(start + timedelta(days=i * 3), h, a, hg, ag, hx, ax))
    return out


def test_m9_probabilities_sum_to_one():
    ms = _matches()
    as_of = ms[-1].date + timedelta(days=2)
    m = M9Model.fit(ms, as_of, M9Params())
    p = m.markets("A", "B", kickoff=as_of)
    assert abs(p["1"] + p["X"] + p["2"] - 1.0) < 1e-9


def test_m9_fit_excludes_future_matches():
    ms = _matches()
    cutoff = ms[65].date
    m = M9Model.fit(ms, cutoff, M9Params())
    assert all(x.date < cutoff for x in m.matches)


def test_m9_has_separate_goal_and_chance_models():
    ms = _matches()
    as_of = ms[-1].date + timedelta(days=2)
    m = M9Model.fit(ms, as_of, M9Params())
    assert m.goals is not m.chances
    assert m.goals.attack.keys() == m.chances.attack.keys()
