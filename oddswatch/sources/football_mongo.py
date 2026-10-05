"""Read-only schema discovery for the separate football secret MONGO.

Never exports document values or connection/error details. No predictions are
inferred from unknown schemas. Database selection: MONGO_DB, URI default, then
unambiguous football/soccer database name. Never falls back to tennis.
"""
from __future__ import annotations

import json
import os


def choose_database(names):
    candidates = [n for n in names if any(x in n.lower() for x in ("football", "soccer"))
                  and "tennis" not in n.lower()]
    if len(candidates) != 1:
        raise ValueError("Set MONGO_DB to the football database name")
    return candidates[0]


SOCCER_COLLECTIONS = ("mains", "extra_leagues")


def inspect(client, db_name=None):
    if db_name:
        db = client[db_name]
    else:
        from pymongo.errors import ConfigurationError
        try:
            db = client.get_default_database()
        except ConfigurationError:
            db = None
        if db is None:
            db = client[choose_database(client.list_database_names())]
    if db.name.lower() in ("admin", "local", "config") or "tennis" in db.name.lower():
        raise ValueError("MONGO_SOCCER must select a football database, not tennis/system")

    available = set(db.list_collection_names())
    missing = [name for name in SOCCER_COLLECTIONS if name not in available]
    if missing:
        raise ValueError("Required soccer collections missing: " + ", ".join(missing))

    result = {
        "database": db.name,
        "mode": "schema_only",
        "collections": [],
        "scope": list(SOCCER_COLLECTIONS),
    }
    for name in SOCCER_COLLECTIONS:
        collection = db[name]
        # Bounded recent-insertion sample; _id order is NOT fixture date order.
        docs = list(collection.find({}).sort("_id", -1).limit(10).max_time_ms(5000))
        fields = {}
        for doc in docs:
            for key, value in doc.items():
                fields.setdefault(key, set()).add(type(value).__name__)
        result["collections"].append({"name": name,
            "sample_count": len(docs),
            "fields": {k: sorted(v) for k, v in sorted(fields.items())}})
    return result


def run():
    uri = (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGO") or "").strip()
    if not uri:
        print("::error::MONGO_SOCCER fehlt: Fußball-Mongo-Scan nicht ausgeführt")
        return 2
    try:
        from pymongo import MongoClient, timeout
        with timeout(90):
            with MongoClient(uri, serverSelectionTimeoutMS=15000,
                             connectTimeoutMS=10000, socketTimeoutMS=10000,
                             appname="oddswatch-football-readonly") as client:
                result = inspect(client, os.environ.get("MONGO_DB") or None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("Fußball-Mongo: mains + extra_leagues gelesen; noch keine Valuebet-Freigabe.")
        return 0
    except Exception as exc:
        # Exception text can contain URI, host names or credentials: never print it.
        print("::error::Fußball-Mongo-Scan fehlgeschlagen (" + type(exc).__name__ +
              "). MONGO_SOCCER, MONGO_DB, Leserechte und Atlas Network Access prüfen.")
        return 2


def profile_for_model(client, db_name=None):
    """Nur strukturierte Aggregationen für Modell-Eignung; keine Dokumentinhalte."""
    if db_name:
        db = client[db_name]
    else:
        from pymongo.errors import ConfigurationError
        try:
            db = client.get_default_database()
        except ConfigurationError:
            db = None
        if db is None:
            db = client[choose_database(client.list_database_names())]

    out = {"database": db.name, "mode": "model_profile", "collections": {}}
    for name in ("mains", "extra_leagues"):
        if name not in db.list_collection_names():
            continue
        col = db[name]
        total = col.count_documents({})
        fields = ["Date","Div","HomeTeam","AwayTeam","FTHG","FTAG","FTR",
                  "HS","AS","HST","AST","B365H","B365D","B365A",
                  "B365CH","B365CD","B365CA","PSH","PSD","PSA","PSCH","PSCD","PSCA",
                  "AvgH","AvgD","AvgA","AvgCH","AvgCD","AvgCA"]
        coverage = {}
        for fld in fields:
            n = col.count_documents({fld: {"$exists": True, "$ne": None}})
            coverage[fld] = {"count": n, "pct": round(100*n/total, 1) if total else 0.0}
        divs = list(col.aggregate([
            {"$match": {"Div": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$Div", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
            {"$limit": 50},
        ]))
        dates = list(col.aggregate([
            {"$match": {"Date": {"$type": "date"}}},
            {"$group": {"_id": None, "min": {"$min": "$Date"}, "max": {"$max": "$Date"}}},
        ]))
        out["collections"][name] = {
            "documents": total,
            "date_range": ({
                "min": dates[0]["min"].isoformat(),
                "max": dates[0]["max"].isoformat(),
            } if dates else None),
            "divisions": [{"div": x["_id"], "n": x["n"]} for x in divs],
            "coverage": coverage,
        }
    return out


def run_profile():
    uri = (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGO") or "").strip()
    if not uri:
        print("::error::MONGO_SOCCER fehlt")
        return 2
    try:
        from pymongo import MongoClient, timeout
        with timeout(120):
            with MongoClient(uri, serverSelectionTimeoutMS=15000,
                             connectTimeoutMS=10000, socketTimeoutMS=15000,
                             appname="oddswatch-football-profile") as client:
                result = profile_for_model(client, os.environ.get("MONGO_DB") or None)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except Exception as exc:
        print("::error::Fußball-Mongo-Profil fehlgeschlagen (" + type(exc).__name__ + ")")
        return 2


def audit_for_m13(client, db_name=None):
    """Read-only Datenqualitätsaudit für M13; gibt nur Aggregationen aus."""
    from datetime import datetime, timezone

    if db_name:
        db = client[db_name]
    else:
        from pymongo.errors import ConfigurationError
        try:
            db = client.get_default_database()
        except ConfigurationError:
            db = None
        if db is None:
            db = client[choose_database(client.list_database_names())]

    col = db["mains"]
    now = datetime.now(timezone.utc)
    completed = {
        "FTHG": {"$exists": True, "$ne": None},
        "FTAG": {"$exists": True, "$ne": None},
    }

    total = col.count_documents({})
    completed_n = col.count_documents(completed)
    future_all = col.count_documents({"Date": {"$gt": now}})
    future_completed = col.count_documents({**completed, "Date": {"$gt": now}})
    missing_teams = col.count_documents({
        "$or": [
            {"HomeTeam": {"$exists": False}}, {"HomeTeam": None}, {"HomeTeam": ""},
            {"AwayTeam": {"$exists": False}}, {"AwayTeam": None}, {"AwayTeam": ""},
        ]
    })
    invalid_goals = col.count_documents({
        "$or": [{"FTHG": {"$lt": 0}}, {"FTAG": {"$lt": 0}}]
    })

    score_result_mismatch = col.count_documents({
        **completed,
        "FTR": {"$exists": True, "$ne": None},
        "$expr": {"$or": [
            {"$and": [{"$gt": ["$FTHG", "$FTAG"]}, {"$ne": ["$FTR", "H"]}]},
            {"$and": [{"$eq": ["$FTHG", "$FTAG"]}, {"$ne": ["$FTR", "D"]}]},
            {"$and": [{"$lt": ["$FTHG", "$FTAG"]}, {"$ne": ["$FTR", "A"]}]},
        ]}
    })

    bad_shots = col.count_documents({
        "$or": [
            {"$expr": {"$gt": ["$HST", "$HS"]}},
            {"$expr": {"$gt": ["$AST", "$AS"]}},
            {"HS": {"$lt": 0}}, {"AS": {"$lt": 0}},
            {"HST": {"$lt": 0}}, {"AST": {"$lt": 0}},
        ]
    })

    dup = list(col.aggregate([
        {"$match": {**completed, "Date": {"$type": "date"},
                    "Div": {"$exists": True, "$ne": None},
                    "HomeTeam": {"$exists": True, "$ne": None},
                    "AwayTeam": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": {"Date": "$Date", "Div": "$Div", "H": "$HomeTeam", "A": "$AwayTeam"},
            "n": {"$sum": 1},
        }},
        {"$match": {"n": {"$gt": 1}}},
        {"$group": {
            "_id": None,
            "duplicate_groups": {"$sum": 1},
            "excess_rows": {"$sum": {"$subtract": ["$n", 1]}},
            "max_copies": {"$max": "$n"},
        }},
    ], allowDiskUse=True))
    dup_stats = dup[0] if dup else {
        "duplicate_groups": 0, "excess_rows": 0, "max_copies": 0
    }
    dup_stats.pop("_id", None)

    pinnacle_both = col.count_documents({
        **completed,
        "PSH": {"$gt": 1}, "PSD": {"$gt": 1}, "PSA": {"$gt": 1},
        "PSCH": {"$gt": 1}, "PSCD": {"$gt": 1}, "PSCA": {"$gt": 1},
    })
    b365_both = col.count_documents({
        **completed,
        "B365H": {"$gt": 1}, "B365D": {"$gt": 1}, "B365A": {"$gt": 1},
        "B365CH": {"$gt": 1}, "B365CD": {"$gt": 1}, "B365CA": {"$gt": 1},
    })
    shot_complete = col.count_documents({
        **completed,
        "HS": {"$exists": True, "$ne": None},
        "AS": {"$exists": True, "$ne": None},
        "HST": {"$exists": True, "$ne": None},
        "AST": {"$exists": True, "$ne": None},
    })

    recent_start = datetime(2017, 7, 1, tzinfo=timezone.utc)
    recent_end = datetime(2026, 7, 1, tzinfo=timezone.utc)
    recent_dup = list(col.aggregate([
        {"$match": {**completed,
                    "Date": {"$gte": recent_start, "$lt": recent_end},
                    "Div": {"$exists": True, "$ne": None},
                    "HomeTeam": {"$exists": True, "$ne": None},
                    "AwayTeam": {"$exists": True, "$ne": None}}},
        {"$group": {
            "_id": {"Date": "$Date", "Div": "$Div", "H": "$HomeTeam", "A": "$AwayTeam"},
            "n": {"$sum": 1},
        }},
        {"$match": {"n": {"$gt": 1}}},
        {"$group": {
            "_id": None,
            "duplicate_groups": {"$sum": 1},
            "excess_rows": {"$sum": {"$subtract": ["$n", 1]}},
            "max_copies": {"$max": "$n"},
        }},
    ], allowDiskUse=True))
    recent_dup_stats = recent_dup[0] if recent_dup else {
        "duplicate_groups": 0, "excess_rows": 0, "max_copies": 0
    }
    recent_dup_stats.pop("_id", None)

    # Prüft die Hypothese Tag/Monat vertauscht bei Future-Ergebnissen.
    # Es werden nur öffentliche Match-Felder verglichen, keine Nutzer-/Accountdaten.
    swap_candidates = 0
    swap_counterparts = 0
    future_docs = list(col.find(
        {**completed, "Date": {"$gt": now},
         "Div": {"$exists": True, "$ne": None},
         "HomeTeam": {"$exists": True, "$ne": None},
         "AwayTeam": {"$exists": True, "$ne": None}},
        {"_id": 0, "Date": 1, "Div": 1, "HomeTeam": 1, "AwayTeam": 1,
         "FTHG": 1, "FTAG": 1},
    ).limit(500))
    for doc in future_docs:
        dt = doc.get("Date")
        if not hasattr(dt, "month") or not hasattr(dt, "day"):
            continue
        if dt.day > 12:
            continue
        try:
            swapped = datetime(dt.year, dt.day, dt.month, tzinfo=timezone.utc)
        except ValueError:
            continue
        if swapped >= now:
            continue
        swap_candidates += 1
        counterpart = col.count_documents({
            "Date": swapped,
            "Div": doc.get("Div"),
            "HomeTeam": doc.get("HomeTeam"),
            "AwayTeam": doc.get("AwayTeam"),
            "FTHG": doc.get("FTHG"),
            "FTAG": doc.get("FTAG"),
        }, limit=1)
        if counterpart:
            swap_counterparts += 1

    future_by_div = list(col.aggregate([
        {"$match": {**completed, "Date": {"$gt": now},
                    "Div": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$Div", "n": {"$sum": 1},
                    "min_date": {"$min": "$Date"}, "max_date": {"$max": "$Date"}}},
        {"$sort": {"n": -1}},
        {"$limit": 30},
    ]))

    recent_by_div = list(col.aggregate([
        {"$match": {**completed,
                    "Date": {"$gte": datetime(2022, 7, 1, tzinfo=timezone.utc)},
                    "Div": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$Div", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
        {"$limit": 40},
    ]))

    def pct(n):
        return round(100.0 * n / completed_n, 2) if completed_n else 0.0

    return {
        "database": db.name,
        "collection": "mains",
        "audit_at": now.isoformat(),
        "documents": total,
        "completed_matches": completed_n,
        "future_rows_all": future_all,
        "future_rows_with_results": future_completed,
        "missing_team_rows": missing_teams,
        "invalid_goal_rows": invalid_goals,
        "score_result_mismatches": score_result_mismatch,
        "invalid_shot_rows": bad_shots,
        "duplicates_completed": dup_stats,
        "duplicates_2017_to_2026_holdout": recent_dup_stats,
        "future_date_swap_check": {
            "swap_candidates": swap_candidates,
            "matching_swapped_counterparts": swap_counterparts,
        },
        "pinnacle_open_and_close": {"count": pinnacle_both, "pct_of_completed": pct(pinnacle_both)},
        "bet365_open_and_close": {"count": b365_both, "pct_of_completed": pct(b365_both)},
        "complete_shot_stats": {"count": shot_complete, "pct_of_completed": pct(shot_complete)},
        "future_results_by_division": [
            {"div": x["_id"], "n": x["n"],
             "min_date": x["min_date"].isoformat(),
             "max_date": x["max_date"].isoformat()}
            for x in future_by_div
        ],
        "recent_completed_by_division": [
            {"div": x["_id"], "n": x["n"]} for x in recent_by_div
        ],
    }


def run_audit():
    uri = (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGO") or "").strip()
    if not uri:
        print("::error::MONGO_SOCCER fehlt")
        return 2
    try:
        from pymongo import MongoClient, timeout
        with timeout(180):
            with MongoClient(uri, serverSelectionTimeoutMS=15000,
                             connectTimeoutMS=10000, socketTimeoutMS=30000,
                             appname="oddswatch-m13-audit") as client:
                result = audit_for_m13(client, os.environ.get("MONGO_DB") or None)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    except Exception as exc:
        print("::error::M13-Datenaudit fehlgeschlagen (" + type(exc).__name__ + ")")
        return 2
