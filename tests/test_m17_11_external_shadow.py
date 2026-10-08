from datetime import date

from oddswatch.m17_11_external_shadow import fair
from oddswatch.models.poisson import Match
from oddswatch.sources.xg_external import XGSnapshot
from oddswatch.sources.soccerstats import TeamVenuePrior


def _x(team, xg, xga):
    return XGSnapshot(team, xg, xga, None, None, None, None, 7, "matchpulse")


def test_external_structural_fair_uses_multiple_signals():
    snaps = [_x("Alpha", 1.8, 1.0), _x("Beta", 1.1, 1.7), _x("Gamma", 1.4, 1.4)]
    venue = [
        TeamVenuePrior("Alpha", 4, 2.0, 0.75, 2.5, 3, 1.4, 1.2, 1.7),
        TeamVenuePrior("Beta", 4, 1.3, 1.5, 1.2, 3, 1.0, 2.0, 0.7),
        TeamVenuePrior("Gamma", 4, 1.4, 1.3, 1.5, 3, 1.2, 1.4, 1.0),
    ]
    hist = [
        Match(date(2026,9,1), "Alpha", "Gamma", 2, 0),
        Match(date(2026,9,5), "Beta", "Gamma", 1, 1),
        Match(date(2026,9,10), "Gamma", "Alpha", 1, 2),
        Match(date(2026,9,15), "Gamma", "Beta", 2, 0),
    ]
    alt = {"Alpha": (1.7, 1.1), "Beta": (1.2, 1.6), "Gamma": (1.4, 1.4)}
    r = fair("Alpha", "Beta", date(2026,10,10), snaps, venue, hist, alt)
    assert abs(sum(r.probs.values()) - 1.0) < 1e-9
    assert r.signals_used >= 2
    assert r.home_fast_alt is not None
    assert r.home_venue is not None
    assert r.home_xg > 0 and r.away_xg > 0


def test_external_structural_fair_can_run_without_history():
    snaps = [_x("Alpha", 1.8, 1.0), _x("Beta", 1.1, 1.7)]
    venue = [
        TeamVenuePrior("Alpha", 4, 2.0, 0.75, 2.5, 3, 1.4, 1.2, 1.7),
        TeamVenuePrior("Beta", 4, 1.3, 1.5, 1.2, 3, 1.0, 2.0, 0.7),
    ]
    r = fair("Alpha", "Beta", date(2026,10,10), snaps, venue)
    assert abs(sum(r.probs.values()) - 1.0) < 1e-9
    assert r.signals_used == 2
    assert r.home_slow is None
