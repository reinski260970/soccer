from oddswatch.nhl_bulk_v6 import FEATURES, _augment_interactions


def test_v6_market_isolation():
    blob=" ".join(FEATURES).lower()
    assert all(x not in blob for x in ("open","close","odds","price"))


def test_xg_agreement_interaction():
    r={
        "slow_mp_xg_share_diff":.1,
        "fast_mp_xg_share_diff":.2,
        "slow_mp_svaxgf_diff":.1,"fast_mp_svaxgf_diff":.2,
        "slow_mp_svaxga_diff":.1,"fast_mp_svaxga_diff":.2,
        "slow_mp_corsi_share_diff":.1,"fast_mp_corsi_share_diff":.2,
        "slow_mp_xg_per_sog_for_diff":.1,"fast_mp_xg_per_sog_for_diff":.2,
        "slow_mp_xg_per_sog_against_diff":.1,"fast_mp_xg_per_sog_against_diff":.2,
        "slow_mp_hd_share_for_diff":.1,"fast_mp_hd_share_for_diff":.2,
        "slow_mp_hd_share_against_diff":.1,"fast_mp_hd_share_against_diff":.2,
        "slow_mp_non5v5_xgf_diff":.1,"fast_mp_non5v5_xgf_diff":.2,
        "slow_mp_non5v5_xga_diff":.1,"fast_mp_non5v5_xga_diff":.2,
    }
    q=_augment_interactions(r)
    assert q["ix_xg_share_agreement"]==1.0
    assert abs(q["ix_xg_share_product"]-.02)<1e-12
