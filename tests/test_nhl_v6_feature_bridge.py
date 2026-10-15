from datetime import date, timedelta
from oddswatch.nhl_v6_feature_bridge import _mp_snapshot, load_completed_results
from oddswatch.nhl_moneypuck_features import PRIORS


def test_money_puck_snapshot_neutral_priors():
    p = _mp_snapshot({"TOR":dict(PRIORS),"BUF":dict(PRIORS)}, "TOR", "BUF")
    assert len(p) == 22
    assert all(abs(v) < 1e-12 for v in p.values())


def test_results_only_csv(tmp_path):
    f=tmp_path/"results.csv"
    f.write_text(
        "season,date,home_team,away_team,reg_home,reg_away,final_home,final_away\n"
        "2026,20261010,Maple Leafs,Sabres,3,2,3,2\n",encoding="utf-8"
    )
    rows=load_completed_results(f)
    assert len(rows)==1
    assert rows[0]["home_open"]==2.0
    assert rows[0]["date"]==date(2026,10,10)
