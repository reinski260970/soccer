from datetime import datetime

from oddswatch import mongo_sync as ms

MAINS = "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H\n" \
        "E0,03/10/2026,15:00,Arsenal,Everton,2,1,H,1.50\n" \
        "E0,25/10/26,15:00,Spurs,Leeds,0,0,D,2.10\n" \
        ",,,,,,,,\n"
NEW = "Country,League,Season,Date,Time,Home,Away,HG,AG,Res\n" \
      "Sweden,Allsvenskan,2026,01/08/2026,18:00,Malmo FF,AIK,2,0,H\n"


def test_dates_are_day_first():
    assert ms.parse_date("03/10/2026") == datetime(2026, 10, 3)
    assert ms.parse_date("25/10/26") == datetime(2026, 10, 25)
    assert ms.parse_date("") is None


def test_parse_csv_types_and_skips_empty():
    rows = ms.parse_csv(MAINS, "mains")
    assert len(rows) == 2
    assert rows[0]["Date"] == datetime(2026, 10, 3) and rows[0]["FTHG"] == 2 and rows[0]["B365H"] == 1.5
    extra = ms.parse_csv(NEW, "extra")
    assert extra[0]["Season"] == "2026" and extra[0]["HG"] == 2 and extra[0]["Date"] == datetime(2026, 8, 1)


def test_compare_detects_swapped_dates():
    fresh = ms.parse_csv(MAINS, "mains")
    existing = [
        {"Div": "E0", "HomeTeam": "Arsenal", "AwayTeam": "Everton", "FTHG": 2, "FTAG": 1,
         "Date": datetime(2026, 3, 10)},                       # alter Scraper: vertauscht
        {"Div": "E0", "HomeTeam": "Spurs", "AwayTeam": "Leeds", "FTHG": 0, "FTAG": 0,
         "Date": datetime(2026, 10, 25)},                      # Tag > 12: richtig
    ]
    c = ms.compare(existing, fresh, ms._key_m)
    assert (c["vertauscht"], c["richtig"], c["neu"]) == (1, 1, 0)


def test_season_helpers():
    from datetime import date
    assert ms.season_start(date(2026, 10, 22)) == 2026 and ms.season_start(date(2027, 3, 1)) == 2026
    assert ms.season_code(2026) == "2627"
