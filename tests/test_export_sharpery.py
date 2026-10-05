import csv

from oddswatch.export_sharpery import COLUMNS, export, to_row
from oddswatch.journal import Journal


def test_row_mapping_matches_sharpery_format():
    r = to_row({"created_at": "2026-09-28T20:31:44+00:00", "kickoff": "2026-09-29T18:45+00:00",
                "league": "nations", "event": "Luxembourg – Iceland", "market": "home",
                "selection": "Luxembourg Sieg (90 Min.)", "source": "bet365", "odds": "3.3990",
                "fair_odds": "3.0999", "min_odds": "3.1929", "ev": "0.0965", "stake_eh": "0.75",
                "estimate": "False", "result": "win", "closing_fair_odds": "3.2", "clv": "0.0622"})
    assert list(r) == COLUMNS
    assert r["Placed At"] == "2026-09-28T20:31:44Z"
    assert r["Kickoff"] == "2026-09-29T18:45:00Z"
    assert r["Event"] == "Luxembourg vs Iceland"
    assert (r["Sport"], r["Market"], r["Period"]) == ("Soccer", "1X2", "Regular Time")
    assert r["Bet Odds"] == 3.4 and r["EV %"] == 9.65 and r["CLV %"] == 6.22
    assert r["Result"] == "won" and r["Stake"] == 0.75 and r["Side"] == "home"


def test_open_bet_is_pending_and_files_written(tmp_path):
    j = Journal(tmp_path / "j")
    j.append("valuebets", [{"league": "nhl", "event": "A – B", "kickoff": "2026-09-29T21:00+00:00",
                            "market": "home", "selection": "A Sieg", "source": "bet365",
                            "odds": 1.83, "ev": 0.04, "stake_eh": 0.5, "estimate": True}])
    xlsx, csvp, n = export(str(tmp_path / "j"), str(tmp_path / "out" / "sharpery"))
    assert n == 1 and xlsx.exists()
    row = next(csv.DictReader(csvp.open(encoding="utf-8")))
    assert row["Result"] == "pending" and row["Sport"] == "Ice Hockey" and row["Market"] == "Moneyline"
    assert "Schaetzung" in row["Tags"]
