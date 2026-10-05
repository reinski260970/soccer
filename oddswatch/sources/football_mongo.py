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
