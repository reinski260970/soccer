from oddswatch.nhl_bulk_v5 import FEATURES


def test_v5_market_isolation():
    blob=" ".join(FEATURES).lower()
    assert all(x not in blob for x in ("open","close","odds","price"))


def test_v5_contains_both_timescales():
    assert any(x.startswith("slow_mp_") for x in FEATURES)
    assert any(x.startswith("fast_mp_") for x in FEATURES)
    assert "slow_mp_xg_per_sog_for_diff" in FEATURES
    assert "fast_mp_non5v5_xgf_diff" in FEATURES
