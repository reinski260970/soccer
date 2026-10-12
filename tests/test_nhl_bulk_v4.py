from oddswatch.nhl_bulk_v4 import FEATURES
from oddswatch.nhl_moneypuck_features import SBR_TO_MP


def test_v4_has_no_market_features():
    blob=" ".join(FEATURES).lower()
    assert all(x not in blob for x in ("open","close","odds","price"))


def test_key_sbr_moneypuck_aliases():
    assert SBR_TO_MP["Bruins"]=="BOS"
    assert SBR_TO_MP["Kings"]=="L.A"
    assert SBR_TO_MP["Lightning"]=="T.B"
    assert SBR_TO_MP["Sharks"]=="S.J"
    assert SBR_TO_MP["Devils"]=="N.J"
    assert SBR_TO_MP["WinnipegJets"]=="WPG"
