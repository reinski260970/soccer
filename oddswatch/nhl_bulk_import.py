"""One-shot import of the public NHL 10-year odds archive.

Downloads one pinned static GitHub raw file (not a scraper), validates it and
writes a compact normalized CSV used by the historical NHL market backtest.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE_COMMIT = "1a820e50c6fbd0276cde073c22bfffae78930868"
SOURCE_URL = (
    "https://raw.githubusercontent.com/flancast90/sportsbookreview-scraper/"
    f"{SOURCE_COMMIT}/data/nhl_archive_10Y.json"
)
DEST = Path("data/hockey/market/nhl_sbr_2011_2021.csv")
PROVENANCE = Path("data/hockey/market/nhl_sbr_2011_2021.provenance.json")

FIELDS = [
    "season","date","home_team","away_team",
    "reg_home","reg_away","final_home","final_away",
    "home_open_ml","away_open_ml","home_close_ml","away_close_ml",
    "open_total","open_total_odds","close_total","close_total_odds",
]


def _int(v):
    if v is None or v == "":
        return None
    return int(float(v))


def _num(v):
    if v is None or v == "":
        return None
    return float(v)


def normalize(rows: list[dict]) -> tuple[list[dict], dict]:
    out, seen = [], set()
    rejected = 0
    for raw in rows:
        try:
            season = int(raw["season"])
            day = str(int(float(raw["date"])))
            home = str(raw["home_team"]).strip()
            away = str(raw["away_team"]).strip()
            p1h, p1a = _int(raw["home_1stPeriod"]), _int(raw["away_1stPeriod"])
            p2h, p2a = _int(raw["home_2ndPeriod"]), _int(raw["away_2ndPeriod"])
            p3h, p3a = _int(raw["home_3rdPeriod"]), _int(raw["away_3rdPeriod"])
            fh, fa = _int(raw["home_final"]), _int(raw["away_final"])
            ho, ao = _int(raw["home_open_ml"]), _int(raw["away_open_ml"])
            hc, ac = _int(raw["home_close_ml"]), _int(raw["away_close_ml"])
            if not (20100101 <= int(day) <= 20301231 and home and away and home != away):
                raise ValueError
            if None in (p1h,p1a,p2h,p2a,p3h,p3a,fh,fa,ho,ao,hc,ac):
                raise ValueError
            if fh == fa or ho == 0 or ao == 0 or hc == 0 or ac == 0:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            rejected += 1
            continue

        key = (day, home, away)
        if key in seen:
            rejected += 1
            continue
        seen.add(key)
        out.append({
            "season": season,
            "date": day,
            "home_team": home,
            "away_team": away,
            "reg_home": p1h+p2h+p3h,
            "reg_away": p1a+p2a+p3a,
            "final_home": fh,
            "final_away": fa,
            "home_open_ml": ho,
            "away_open_ml": ao,
            "home_close_ml": hc,
            "away_close_ml": ac,
            "open_total": _num(raw.get("open_over_under")),
            "open_total_odds": _num(raw.get("open_over_under_odds")),
            "close_total": _num(raw.get("close_over_under")),
            "close_total_odds": _num(raw.get("close_over_under_odds")),
        })

    out.sort(key=lambda r: (r["date"], r["home_team"], r["away_team"]))
    seasons = {}
    for r in out:
        seasons[str(r["season"])] = seasons.get(str(r["season"]), 0) + 1
    return out, {"rows": len(out), "rejected": rejected, "seasons": seasons}


def fetch_source() -> list[dict]:
    req = Request(SOURCE_URL, headers={"User-Agent":"oddswatch-bulk-import/1.0"})
    with urlopen(req, timeout=90) as response:
        data = json.load(response)
    if not isinstance(data, list):
        raise ValueError("source is not a JSON list")
    return data


def run(dest: Path = DEST) -> dict:
    rows, stats = normalize(fetch_source())
    if stats["rows"] < 10000:
        raise RuntimeError(f"bulk source unexpectedly small: {stats['rows']}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    provenance = {
        "source_repository":"flancast90/sportsbookreview-scraper",
        "source_commit":SOURCE_COMMIT,
        "source_file":"data/nhl_archive_10Y.json",
        "source_license":"MIT repository",
        "download_mode":"single pinned static GitHub file; no scraping",
        **stats,
    }
    PROVENANCE.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance))
    return provenance


if __name__ == "__main__":
    run()
