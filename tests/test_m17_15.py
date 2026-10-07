from oddswatch.m17_15_research import (
    _structural_gate_values,
    _entry_stats_consensus,
)


def _row(
    home_fast=1.20,
    away_fast=1.50,
    home_slow=1.25,
    away_slow=1.45,
    p_away=0.50,
    opening=2.10,
    closing_away_novig_p=0.50,
    y=2,
):
    # 17 base features, then structural positions used by M17.15.
    x = [0.0] * 34
    x[17] = home_fast
    x[18] = away_fast
    x[21] = home_slow
    x[22] = away_slow

    # Use a normalized closing vector where away probability is explicit.
    rem = 1.0 - closing_away_novig_p
    clp = [rem * 0.60, rem * 0.40, closing_away_novig_p]
    cl = [1.0 / p for p in clp]

    return {
        "x": x,
        "p": [0.25, 0.25, p_away],
        "op": [4.0, 4.0, opening],
        "cl": cl,
        "y": y,
        "date": "2024-01-01",
        "home": "H",
        "away": "A",
    }


def test_m17_15_structural_consensus_uses_weaker_timescale_margin():
    r = _row(
        home_fast=1.20,
        away_fast=1.55,
        home_slow=1.30,
        away_slow=1.40,
    )
    consensus, disagreement = _structural_gate_values(r)
    assert abs(consensus - 0.10) < 1e-12
    assert abs(disagreement - 0.25) < 1e-12


def test_m17_15_gate_requires_structural_consensus():
    good = _row()
    bad = _row(
        home_fast=1.40,
        away_fast=1.30,
        home_slow=1.20,
        away_slow=1.50,
    )
    s = _entry_stats_consensus(
        [good, bad],
        edge=0.02,
        cap=2.5,
        min_consensus_margin=0.0,
        max_disagreement=1.0,
    )
    assert s["bets"] == 1
    assert len(s["selected"]) == 1


def test_m17_15_gate_applies_disagreement_limit():
    stable = _row(
        home_fast=1.20,
        away_fast=1.45,
        home_slow=1.20,
        away_slow=1.42,
    )
    unstable = _row(
        home_fast=1.00,
        away_fast=1.70,
        home_slow=1.30,
        away_slow=1.35,
    )
    s = _entry_stats_consensus(
        [stable, unstable],
        edge=0.02,
        cap=2.5,
        min_consensus_margin=0.0,
        max_disagreement=0.25,
    )
    assert s["bets"] == 1
