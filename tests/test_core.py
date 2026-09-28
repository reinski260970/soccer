import random
from datetime import date, timedelta

from oddswatch import pricing
from oddswatch.journal import Journal
from oddswatch.models.poisson import Match, PoissonModel
from oddswatch.models.ratings import Game, PointsModel
from oddswatch.selection import Offer, evaluate, pick
from oddswatch.sources.kalshi import group_1x2, parse_make_snapshots


def _league(seed=1):
    rnd = random.Random(seed)
    strength = {"A": 0.4, "B": 0.1, "C": -0.1, "D": -0.4}
    teams, ms, d0 = list(strength), [], date(2026, 1, 1)
    for k in range(30):
        for h in teams:
            for a in teams:
                if h == a:
                    continue
                import math
                lh = math.exp(0.25 + 0.2 + strength[h] - (-strength[a]) * 0.0 - strength[a] * 0.5)
                la = math.exp(0.25 + strength[a] - strength[h] * 0.5)
                ms.append(Match(d0 + timedelta(days=k), h, a, _pois(rnd, lh), _pois(rnd, la)))
    return ms


def _pois(rnd, lam):
    import math
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= L:
            return k
        k += 1


def test_poisson_ranks_and_sums():
    m = PoissonModel.fit(_league(), date(2026, 3, 1), half_life_days=1e6)
    assert m.attack["A"] > m.attack["D"]
    mk = m.markets("A", "D")
    assert abs(mk["1"] + mk["X"] + mk["2"] - 1) < 1e-9
    assert mk["1"] > mk["2"]
    assert abs(mk["O2.5"] + mk["U2.5"] - 1) < 1e-9


def test_points_model():
    rnd = random.Random(3)
    r = {"X": 6, "Y": 0, "Z": -6}
    gs = []
    for k in range(40):
        for h in r:
            for a in r:
                if h != a:
                    base = 110 + rnd.gauss(0, 8)
                    mar = 3 + r[h] - r[a] + rnd.gauss(0, 11)
                    gs.append(Game(date(2026, 1, 1) + timedelta(days=k), h, a, base + mar / 2, base - mar / 2))
    m = PointsModel.fit(gs, date(2026, 3, 1), half_life_days=1e6)
    assert 2 < m.home_adv < 4  # wahr: 3
    mk = m.markets("X", "Z", spread=-10.5, total=220.5)
    assert mk["ML1"] > 0.8
    assert 8 < m.sigma_margin < 14


def test_pricing():
    assert abs(sum(pricing.devig([2.0, 3.5, 4.0])) - 1) < 1e-9
    assert abs(pricing.ev(0.5, 2.1) - 0.05) < 1e-12
    assert abs(pricing.min_odds(0.5, 0.03) - 2.06) < 1e-12
    assert pricing.kalshi_fee_per_contract(0.5) == 0.02
    assert abs(pricing.kalshi_decimal_odds(50) - 1 / 0.52) < 1e-12
    assert pricing.stake_units(0.4, 2.0) == 0.0
    assert 0 < pricing.stake_units(0.6, 2.0) <= 2.0


def test_make_snapshot_parse():
    rules = "If {t} wins the Stuttgart vs Dortmund professional Bundesliga soccer game"
    recs = [
        {"key": "K-VFB", "data": {"ticker": "KXB-26SEP19VFBBVB-VFB", "title": "Stuttgart wins", "ask": 0.4, "bid": 0.39, "rules": rules.format(t="Stuttgart")}},
        {"key": "K-TIE", "data": {"ticker": "KXB-26SEP19VFBBVB-TIE", "title": "Tie is the result", "ask": 0.26, "bid": 0.24, "rules": "If Tie is the result of the Stuttgart vs Dortmund professional"}},
        {"key": "K-BVB", "data": {"ticker": "KXB-26SEP19VFBBVB-BVB", "title": "Dortmund wins", "ask": 0.36, "bid": 0.35, "rules": rules.format(t="Dortmund")}},
        {"key": "BATCH", "data": {"markets": "[]"}},
    ]
    g = group_1x2(parse_make_snapshots(recs))
    assert list(g) == ["KXB-26SEP19VFBBVB"]
    assert g["KXB-26SEP19VFBBVB"]["home"].yes_ask == 0.4


def test_selection_and_journal(tmp_path):
    off = Offer("A vs B", "2026-10-01", "1", "A Sieg", 2.3, "kalshi", "now")
    c = evaluate(off, 0.52, reason="test")
    assert c.ev > 0.19 and c.stake_eh > 0
    assert pick([c, evaluate(off, 0.40)]) == [c]
    j = Journal(tmp_path)
    j.append("valuebets", [c.as_row()])
    assert j.settle("valuebets", "A vs B", "1", True, closing_fair_odds=2.1) == 1
    s = j.summary("valuebets")
    assert s["pnl_eh"] > 0 and s["avg_clv"] > 0


def test_poisson_constant_scores_regression():
    teams = "ABCD"
    ms = [Match(date(2026, 1, 1), h, a, 2, 1) for h in teams for a in teams if h != a]
    m = PoissonModel.fit(ms, date(2026, 2, 1), rho=0, shrink=0)
    lh, la = m.expected_goals("A", "B")
    assert abs(lh - 2) < 1e-6 and abs(la - 1) < 1e-6


def test_points_home_adv_not_halved():
    teams = "ABCD"
    gs = [Game(date(2026, 1, 1), h, a, 105, 95) for h in teams for a in teams if h != a]
    m = PointsModel.fit(gs, date(2026, 2, 1))
    ph, pa = m.expected_points("A", "B")
    assert abs(m.home_adv - 10) < 1e-6
    assert abs(ph - 105) < 1e-6 and abs(pa - 95) < 1e-6


def test_journal_keeps_timestamps(tmp_path):
    off = Offer("A vs B", "k", "1", "A Sieg", 2.0, "kalshi", "2026-09-28T10:00:00Z")
    j = Journal(tmp_path)
    j.append("valuebets", [evaluate(off, 0.6).as_row()])
    row = j.read("valuebets")[0]
    assert row["observed_at"] == "2026-09-28T10:00:00Z"
    assert row["created_at"]
