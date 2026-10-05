from datetime import date, timedelta

from oddswatch.models.m8 import M8Model, M8Params
from oddswatch.models.poisson import Match


def _matches():
    start = date(2025, 1, 1)
    teams = ["A", "B", "C", "D"]
    out = []
    for i in range(80):
        h = teams[i % 4]
        a = teams[(i + 1 + (i // 4) % 3) % 4]
        if h == a:
            a = teams[(teams.index(a) + 1) % 4]
        hg = float((i * 3) % 4)
        ag = float((i * 2 + 1) % 3)
        out.append(Match(start + timedelta(days=i * 3), h, a, hg, ag,
                         max(0.2, hg * 0.75 + 0.4), max(0.2, ag * 0.75 + 0.35)))
    return out


def test_m8_probabilities_sum_to_one():
    ms = _matches()
    as_of = ms[-1].date + timedelta(days=2)
    m = M8Model.fit(ms, as_of, M8Params())
    p = m.markets("A", "B", kickoff=as_of)
    assert abs(p["1"] + p["X"] + p["2"] - 1.0) < 1e-9
    assert 0 < p["1"] < 1
    assert 0 < p["X"] < 1
    assert 0 < p["2"] < 1


def test_m8_fit_excludes_future_matches():
    ms = _matches()
    cutoff = ms[60].date
    m = M8Model.fit(ms, cutoff, M8Params())
    assert all(x.date < cutoff for x in m.matches)


def test_m8_api_has_no_market_price_input():
    ms = _matches()
    as_of = ms[-1].date + timedelta(days=2)
    m = M8Model.fit(ms, as_of, M8Params())
    # Fair probabilities depend only on team/history/date/neutrality.
    a = m.markets("A", "B", kickoff=as_of)
    b = m.markets("A", "B", kickoff=as_of)
    assert a == b
