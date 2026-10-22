"""football-data.co.uk -> eigene Fußball-Mongo (euro_football.mains / extra_leagues).

Ersetzt den alten Scraper. Quelle der Wahrheit sind die CSVs von football-data.co.uk:
  mains:        https://www.football-data.co.uk/mmz4281/<YYZZ>/<Div>.csv  (dd/mm/yy[yy])
  extra_leagues https://www.football-data.co.uk/new/<CODE>.csv            (alle Saisons)

Der alte Scraper hat bei Tagen <= 12 Tag und Monat vertauscht. Diese Datei liest
das Datum immer als Tag/Monat.

Aufruf (Secret MONGO_SOCCER):
  python -m oddswatch.mongo_sync backup --out backup/          # komplette Sicherung (jsonl.gz)
  python -m oddswatch.mongo_sync plan [--full]                  # nur zählen, nichts schreiben
  python -m oddswatch.mongo_sync apply [--full] --confirm       # schreiben
--full: alle Saisons neu aufbauen (Reparatur). Ohne --full: nur die laufende Saison.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import sys
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path

BASE = "https://www.football-data.co.uk"
FIRST_SEASON = 1993

# "new"-Dateien: Dateikürzel -> Country (wie im Bestand)
NEW_FILES = {"ARG": "Argentina", "AUT": "Austria", "BRA": "Brazil", "CHN": "China",
             "DNK": "Denmark", "FIN": "Finland", "IRL": "Ireland", "JPN": "Japan",
             "MEX": "Mexico", "NOR": "Norway", "POL": "Poland", "ROU": "Romania",
             "RUS": "Russia", "SWE": "Sweden", "SWZ": "Switzerland", "USA": "USA"}
INT_COLS = {"FTHG", "FTAG", "HTHG", "HTAG", "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC",
            "HY", "AY", "HR", "AR", "HG", "AG"}
TEXT_COLS = {"Div", "HomeTeam", "AwayTeam", "FTR", "HTR", "Time", "Referee", "Country",
             "League", "Season", "Home", "Away", "Res"}


# ------------------------------------------------------------------ Parsen

def parse_date(s: str) -> datetime | None:
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _value(k: str, v: str):
    v = (v or "").strip()
    if v == "":
        return None
    if k in TEXT_COLS:
        return v
    try:
        f = float(v)
    except ValueError:
        return v
    return int(f) if k in INT_COLS and f.is_integer() else f


def parse_csv(text: str, kind: str) -> list[dict]:
    out = []
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    for row in reader:
        row = {(k or "").strip(): v for k, v in row.items() if k}
        team = row.get("HomeTeam") if kind == "mains" else row.get("Home")
        d = parse_date(row.get("Date", ""))
        if not team or d is None:
            continue
        doc = {k: _value(k, v) for k, v in row.items() if k != "Date"}
        doc = {k: v for k, v in doc.items() if v is not None}
        doc["Date"] = d
        out.append(doc)
    return out


def season_start(today: date | None = None) -> int:
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def season_code(y: int) -> str:
    return f"{y % 100:02d}{(y + 1) % 100:02d}"


# ------------------------------------------------------------------ Netz

def _get(url: str) -> str | None:
    from . import fetch
    text, err = fetch.get(url, timeout=40.0, retries=3, user_agent="Mozilla/5.0 oddswatch-sync")
    time.sleep(0.4)            # höflich bleiben
    if err or not text or text.lstrip().startswith("<"):
        return None
    return text


# ------------------------------------------------------------------ Mongo

def db():
    from pymongo import MongoClient
    uri = (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGODB_URI") or "").strip().strip("'\"")
    if not uri.startswith("mongodb"):
        raise SystemExit("MONGO_SOCCER fehlt oder ist keine Mongo-Adresse")
    client = MongoClient(uri, serverSelectionTimeoutMS=20000, appname="oddswatch-football-data-sync")
    try:
        d = client.get_default_database()
    except Exception:
        d = None
    return d if d is not None else client["euro_football"]


def backup(out: str) -> None:
    from bson import json_util
    d = db()
    Path(out).mkdir(parents=True, exist_ok=True)
    for name in ("mains", "extra_leagues"):
        path = Path(out) / f"{name}.jsonl.gz"
        n = 0
        with gzip.open(path, "wt", encoding="utf-8") as f:
            for doc in d[name].find({}, batch_size=5000):
                f.write(json_util.dumps(doc) + "\n")
                n += 1
        print(f"Sicherung {name}: {n} Dokumente -> {path} ({path.stat().st_size / 1e6:.1f} MB)")


# ------------------------------------------------------------------ Quelle laden

def source_mains(divs: list[str], seasons: list[int]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for div in divs:
        rows = []
        for y in seasons:
            text = _get(f"{BASE}/mmz4281/{season_code(y)}/{div}.csv")
            if text:
                rows += parse_csv(text, "mains")
        out[div] = rows
    return out


def source_extra(only_current: bool) -> dict[str, list[dict]]:
    out = {}
    for code, country in NEW_FILES.items():
        text = _get(f"{BASE}/new/{code}.csv")
        if not text:
            continue
        rows = parse_csv(text, "extra")
        for r in rows:
            r["Country"] = country
        if only_current and rows:
            latest = max(str(r.get("Season")) for r in rows)
            rows = [r for r in rows if str(r.get("Season")) == latest]
        out[country] = rows
    return out


# ------------------------------------------------------------------ Planen / Anwenden

def _key_m(r):
    return (r.get("Div"), r.get("HomeTeam"), r.get("AwayTeam"), r.get("FTHG"), r.get("FTAG"))


def _key_e(r):
    return (str(r.get("Country") or "").strip(), r.get("Home"), r.get("Away"), r.get("HG"), r.get("AG"))


def _swapped(d: datetime) -> datetime | None:
    try:
        return d.replace(month=d.day, day=d.month) if d.day <= 12 else None
    except ValueError:
        return None


def compare(existing: list[dict], fresh: list[dict], key) -> Counter:
    """Wie viele Quellzeilen stehen schon richtig / mit vertauschtem Datum / fehlen."""
    idx: dict = {}
    for e in existing:
        d = e.get("Date")
        if isinstance(d, datetime):
            idx.setdefault(key(e), set()).add(d.date())
    c = Counter()
    for r in fresh:
        have = idx.get(key(r), set())
        d = r["Date"]
        s = _swapped(d)
        if d.date() in have:
            c["richtig"] += 1
        elif s is not None and s.date() in have:
            c["vertauscht"] += 1
        else:
            c["neu"] += 1
    src_keys = {key(r) for r in fresh}
    uniq = {key(e) for e in existing}
    c["bestand"] = len(existing)
    c["bestand_eindeutig"] = len(uniq)
    c["doppelt"] = len(existing) - len({(key(e), e.get("Date")) for e in existing})
    c["nur_im_bestand"] = len(uniq - src_keys)
    c["quelle"] = len(fresh)
    return c


def dedupe(col, fields: list[str]) -> int:
    """Entfernt exakte Spiel-Dubletten (gleiche Schlüsselfelder), behält je Spiel einen Eintrag."""
    pipe = [{"$group": {"_id": {f: "$" + f for f in fields}, "ids": {"$push": "$_id"}, "n": {"$sum": 1}}},
            {"$match": {"n": {"$gt": 1}}}]
    removed = 0
    for g in col.aggregate(pipe, allowDiskUse=True):
        extra_ids = g["ids"][1:]
        removed += col.delete_many({"_id": {"$in": extra_ids}}).deleted_count
    return removed


MAINS_KEY = ["Div", "Date", "HomeTeam", "AwayTeam"]
EXTRA_KEY = ["Country", "League", "Season", "Date", "Home", "Away"]


def ensure_indexes(mains, extra) -> None:
    """Eindeutigkeits-Index: dasselbe Spiel kann nicht zweimal gespeichert werden."""
    from pymongo.errors import OperationFailure
    for col, fields, name in ((mains, MAINS_KEY, "uniq_match"), (extra, EXTRA_KEY, "uniq_match")):
        n = dedupe(col, fields)
        if n:
            print(f"  {col.name}: {n} Dubletten entfernt")
        try:
            col.create_index([(f, 1) for f in fields], unique=True, name=name,
                             partialFilterExpression={fields[-1]: {"$exists": True}})
            print(f"  {col.name}: Eindeutigkeits-Index aktiv")
        except OperationFailure as exc:
            print(f"  {col.name}: Index nicht angelegt ({exc.code})")


def run(apply: bool, full: bool) -> int:
    d = db()
    cur = season_start()
    seasons = list(range(FIRST_SEASON, cur + 1)) if full else [cur]
    stats = d.command("dbStats")
    print(f"Datenbank {d.name}: data {stats.get('dataSize', 0) / 1e6:.0f} MB, "
          f"storage {stats.get('storageSize', 0) / 1e6:.0f} MB")
    print(f"Modus: {'SCHREIBEN' if apply else 'PLAN (nichts wird geschrieben)'}; "
          f"Saisons {'alle ab ' + str(FIRST_SEASON) if full else str(cur) + '/' + str(cur + 1)}")

    mains, extra = d["mains"], d["extra_leagues"]
    divs = sorted(x for x in mains.distinct("Div") if x)
    total = Counter()

    # ---- mains: je Liga
    src = source_mains(divs, seasons)
    for div in divs:
        rows = src.get(div) or []
        if not rows:
            print(f"  mains {div}: keine Quelldaten – Bestand bleibt unverändert")
            continue
        lo = datetime(min(seasons), 7, 1)
        flt = {"Div": div} if full else {"Div": div, "Date": {"$gte": lo}}
        existing = list(mains.find(flt, {"_id": 0, "Div": 1, "HomeTeam": 1, "AwayTeam": 1,
                                         "FTHG": 1, "FTAG": 1, "Date": 1}))
        # Ohne --full kann der alte Bestand der laufenden Saison mit vertauschtem Datum
        # vor dem 1.7. liegen; diese Zeilen ebenfalls erfassen.
        if not full:
            keys = {_key_m(r) for r in rows}
            existing += [e for e in mains.find({"Div": div, "Date": {"$lt": lo, "$gte": datetime(cur, 1, 1)}},
                                               {"_id": 0, "Div": 1, "HomeTeam": 1, "AwayTeam": 1,
                                                "FTHG": 1, "FTAG": 1, "Date": 1})
                         if _key_m(e) in keys]
        c = compare(existing, rows, _key_m)
        total.update({f"mains_{k}": v for k, v in c.items()})
        print(f"  mains {div}: Quelle {c['quelle']}, Bestand {c['bestand']} (doppelt {c['doppelt']}, "
              f"nur im Bestand {c['nur_im_bestand']}) | richtig {c['richtig']}, "
              f"vertauscht {c['vertauscht']}, neu {c['neu']}")
        if apply and full and c["quelle"] < 0.95 * (c["bestand_eindeutig"] or 0):
            print(f"  mains {div}: Quelle deutlich kleiner als Bestand – zur Sicherheit übersprungen")
            continue
        if apply:
            if full:
                mains.delete_many({"Div": div})
            else:
                mains.delete_many({"Div": div, "Date": {"$gte": lo}})
                stale = [(_key_m(r), _swapped(r["Date"])) for r in rows]
                for (k, sd) in stale:
                    if sd is not None:
                        mains.delete_many({"Div": k[0], "HomeTeam": k[1], "AwayTeam": k[2],
                                           "FTHG": k[3], "FTAG": k[4], "Date": sd})
            mains.insert_many(rows, ordered=False)

    # ---- extra_leagues: je Land
    ex = source_extra(only_current=not full)
    for country, rows in ex.items():
        if not rows:
            continue
        seasons_src = sorted({r.get("Season") for r in rows}, key=str)
        names = [country, country + " "]
        flt = {"Country": {"$in": names}}
        if not full:
            flt["Season"] = {"$in": seasons_src + [int(s) for s in seasons_src if str(s).isdigit()]}
        existing = list(extra.find(flt, {"_id": 0, "Country": 1, "Home": 1, "Away": 1,
                                         "HG": 1, "AG": 1, "Date": 1}))
        c = compare(existing, rows, _key_e)
        total.update({f"extra_{k}": v for k, v in c.items()})
        print(f"  extra {country}: Saisons {seasons_src[0]}..{seasons_src[-1]} Quelle {c['quelle']}, "
              f"Bestand {c['bestand']} (doppelt {c['doppelt']}, nur im Bestand {c['nur_im_bestand']}) | "
              f"richtig {c['richtig']}, vertauscht {c['vertauscht']}, neu {c['neu']}")
        if apply and c["quelle"] < 0.95 * (c["bestand_eindeutig"] or 0):
            print(f"  extra {country}: Quelle deutlich kleiner als Bestand – zur Sicherheit übersprungen")
            continue
        if apply:
            extra.delete_many(flt)
            extra.insert_many(rows, ordered=False)

    if apply:
        ensure_indexes(mains, extra)

    junk = mains.count_documents({"Div": None})
    print(f"Leere Zeilen ohne Liga in mains: {junk}" + (" (werden bei --full entfernt)" if full else ""))
    if apply and full and junk:
        mains.delete_many({"Div": None})
    print("SUMME " + json.dumps(dict(total), ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="football-data.co.uk -> Mongo")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--out", default="backup")
    p = sub.add_parser("plan")
    p.add_argument("--full", action="store_true")
    a = sub.add_parser("apply")
    a.add_argument("--full", action="store_true")
    a.add_argument("--confirm", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "backup":
        backup(args.out)
        return 0
    if args.cmd == "apply" and not args.confirm:
        print("apply braucht --confirm")
        return 2
    return run(apply=args.cmd == "apply", full=getattr(args, "full", False))


if __name__ == "__main__":
    sys.exit(main())
