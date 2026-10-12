from datetime import date

from oddswatch.nhl_bulk_features import build_features


def _row(day, home="A", away="B", rh=3, ra=2, fh=3, fa=2):
    return {
        "season": 2014,
        "date": day,
        "home": home,
        "away": away,
        "reg_home": rh,
        "reg_away": ra,
        "final_home": fh,
        "final_away": fa,
        "home_open": 2.0,
        "away_open": 2.0,
        "home_close": 2.0,
        "away_close": 2.0,
    }


def test_features_are_frozen_before_current_result():
    first=_row(date(2014,10,1),rh=9,ra=0,fh=9,fa=0)
    second=_row(date(2014,10,2),rh=1,ra=2,fh=1,fa=2)
    f=build_features([first,second],alpha=.1)
    # First pre-game state is neutral regardless of its extreme eventual score.
    assert abs(f[0]["gf_diff"]) < 1e-12
    assert abs(f[0]["win_diff"]) < 1e-12
    # The second game may reflect the first, proving sequential updates.
    assert f[1]["gf_diff"] > 0
    assert f[1]["win_diff"] > 0


def test_future_game_cannot_change_past_feature_vector():
    a=_row(date(2014,10,1),rh=3,ra=2)
    b=_row(date(2014,10,2),rh=4,ra=1)
    f1=build_features([a])
    f2=build_features([a,b])
    keys=["elo_diff","gf_diff","ga_diff","win_diff","rest_diff"]
    assert all(f1[0][k] == f2[0][k] for k in keys)


def test_market_prices_are_not_in_feature_list():
    from oddswatch.nhl_bulk_v2 import FEATURES
    assert all("open" not in x and "close" not in x and "odds" not in x for x in FEATURES)
