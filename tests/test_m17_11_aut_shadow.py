from datetime import date

from oddswatch.m17_11_aut_shadow import fair
from oddswatch.models.poisson import Match
from oddswatch.sources.xg_external import XGSnapshot
from oddswatch.sources.soccerstats import TeamVenuePrior


def _snap(team, xg, xga):
    return XGSnapshot(
        team=team, xg=xg, xga=xga,
        xg_home=None, xga_home=None, xg_away=None, xga_away=None,
        matches=7, source="test",
    )


def test_austria_structural_shadow_multisource_consensus():
    matches = [
        Match(date(2026, 8, 1), "Tirol", "Ried", 1, 1),
        Match(date(2026, 8, 8), "Ried", "Tirol", 2, 1),
        Match(date(2026, 8, 15), "Tirol", "Other", 2, 0),
        Match(date(2026, 8, 22), "Other", "Ried", 1, 2),
    ]
    snaps = [
        _snap("WSG Wattens", 1.30, 1.80),
        _snap("Ried", 1.70, 1.60),
        _snap("Other", 1.40, 1.40),
    ]
    venue = [
        TeamVenuePrior("Tirol", 3, 1.0, 2.0, 0.67, 4, 1.5, 1.5, 1.50),
        TeamVenuePrior("Ried", 4, 1.75, 1.0, 1.75, 3, 1.33, 2.67, 0.33),
    ]
    alt = {
        "WSG Tirol": (1.75, 1.55),
        "Ried": (1.80, 1.57),
        "Other": (1.40, 1.40),
    }

    r = fair("Tirol", "Ried", date(2026, 10, 10), matches, snaps, venue, alt)

    assert abs(sum(r.probs.values()) - 1.0) < 1e-9
    assert r.home_fast_alt is not None
    assert r.away_fast_alt is not None
    assert r.xg_source_disagreement is not None
    assert r.home_venue is not None
    assert r.away_venue is not None
    assert r.home_xg > 0
    assert r.away_xg > 0


def test_austria_structural_shadow_primary_only_still_works():
    matches = [Match(date(2026, 8, 1), "A", "B", 1, 0)]
    snaps = [_snap("A", 1.6, 1.0), _snap("B", 1.1, 1.8)]
    r = fair("A", "B", date(2026, 10, 10), matches, snaps)
    assert abs(sum(r.probs.values()) - 1.0) < 1e-9
    assert r.home_fast_alt is None
    assert r.xg_source_disagreement is None
