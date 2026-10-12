from datetime import date

from oddswatch.nhl_bulk_features import build_features


def _r(season, day, home="A", away="B", rh=4, ra=1, fh=4, fa=1):
    return {
        "season":season,"date":day,"home":home,"away":away,
        "reg_home":rh,"reg_away":ra,"final_home":fh,"final_away":fa,
        "home_open":2.0,"away_open":2.0,"home_close":2.0,"away_close":2.0,
    }


def test_offseason_reversion_reduces_state_gap():
    rows=[
        _r(2014,date(2014,10,1),rh=8,ra=0,fh=8,fa=0),
        _r(2014,date(2014,10,2),rh=7,ra=1,fh=7,fa=1),
        _r(2015,date(2015,10,1),rh=2,ra=1,fh=2,fa=1),
    ]
    keep=build_features(rows,alpha=.2,season_retain=1.0)
    revert=build_features(rows,alpha=.2,season_retain=.35)
    assert abs(revert[2]["gf_diff"]) < abs(keep[2]["gf_diff"])
    assert abs(revert[2]["elo_diff"]) < abs(keep[2]["elo_diff"])


def test_v3_uses_no_market_features():
    from oddswatch.nhl_bulk_v3 import FEATURES
    assert all(x not in " ".join(FEATURES).lower() for x in ["open","close","odds","price"])
