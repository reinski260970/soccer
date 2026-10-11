"""Leakage, duplicate and misleading release-claim regression tests."""
from datetime import date
import csv
import json

from oddswatch import hockey_walkforward as hw


def _row(season, day, h, a, hg=3, ag=2, league="nhl"):
    return {"league": league, "season":season,"date":date.fromisoformat(day),
            "home":h,"away":a,"home_goals":hg,"away_goals":ag}


def test_loader_deduplicates_and_rejects_future_malformed(tmp_path):
    src = tmp_path/"history.csv"
    rows = [
        ["nhl","2025/26","2026-03-01","H","A","3","1","","nhl-api"],
        ["nhl","2025/26","2026-03-01","H","A","3","1","","nhl-api"],
        ["nhl","2026/27","2026-11-01","H","A","5","4","","nhl-api"],
        ["del","2025/26","2026-02-01","H","A","-2","2","","hockeyarchives"],
        ["nhl","2025/26","2026-03-02","H","A","2","2","SO","nhl-api"],
    ]
    with src.open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(("league","season","date","home_team","away_team",
                    "reg_home","reg_away","extra","source"))
        w.writerows(rows)
    out=hw.load_history(src,as_of=date(2026,10,11))
    assert len(out)==2
    assert [x["date"] for x in out]==[date(2026,3,1),date(2026,3,2)]


def test_train_is_strictly_previous_seasons(monkeypatch):
    training=[
        _row("2023/24","2023-12-01","H","A"),
        _row("2023/24","2024-01-01","A","H"),
        _row("2024/25","2024-11-01","H","A"),
        _row("2025/26","2025-11-01","H","A",4,1),
        _row("2025/26","2025-12-01","A","H",2,2),
        _row("2026/27","2026-10-01","A","H"),
    ]
    seen=[]
    class Fake:
        def markets(self,home,away):
            return {"1":.55,"X":.20,"2":.25}
    def fake_fit(matches, as_of, **kw):
        seen.append((as_of, [m.date for m in matches]))
        return Fake()
    monkeypatch.setattr(hw.PoissonModel, "fit", staticmethod(fake_fit))
    report=hw.evaluate(training,test_seasons=["2025/26","2026/27"],min_training=2)
    assert len(seen)==2
    assert all(d<date(2025,7,1) for d in seen[0][1])
    assert all(d<date(2026,7,1) for d in seen[1][1])
    assert report["leagues"]["nhl"]["2025/26"]["scored_n"]==2
    assert report["leagues"]["nhl"]["2026/27"]["scored_n"]==1
    assert report["release_eligible"] is False
    assert "NOT bookmaker" in report["baseline"]


def test_no_false_market_claims(tmp_path,monkeypatch):
    src=tmp_path/"history.csv"
    src.write_text("league,season,date,home_team,away_team,reg_home,reg_away,extra,source\n",encoding="utf-8")
    dst=tmp_path/"result.json"
    monkeypatch.setattr(hw, "TEST_SEASONS", ("2026/27",))
    hw.run(src,dst,as_of=date(2026,10,11))
    data=json.loads(dst.read_text())
    assert data["market_clv"] is None
    assert data["market_logloss"] is None
    assert data["release_eligible"] is False
    assert data["leagues"]["nhl"]["2026/27"]["status"]=="INSUFFICIENT_HISTORY_OR_TEST_MATCHES"
