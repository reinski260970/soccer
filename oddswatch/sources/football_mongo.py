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
        raise ValueError("MONGO must select a football database, not tennis/system")
    collections = sorted(db.list_collection_names())
    if not collections:
        raise ValueError("Football database has no accessible collections")
    if len(collections) > 100:
        raise ValueError("More than 100 collections: narrow the database scope")
    result = {"database": db.name, "mode": "schema_only", "collections": []}
    for name in collections:
        if name.startswith("system."):
            continue
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
    uri = (os.environ.get("MONGO") or "").strip()
    if not uri:
        print("::error::MONGO fehlt: Fußball-Mongo-Scan nicht ausgeführt")
        return 2
    try:
        from pymongo import MongoClient, timeout
        with timeout(90):
            with MongoClient(uri, serverSelectionTimeoutMS=15000,
                             connectTimeoutMS=10000, socketTimeoutMS=10000,
                             appname="oddswatch-football-readonly") as client:
                result = inspect(client, os.environ.get("MONGO_DB") or None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("Fußball-Mongo: Verbindung und Schema gelesen; noch keine Valuebet-Freigabe.")
        return 0
    except Exception as exc:
        # Exception text can contain URI, host names or credentials: never print it.
        print("::error::Fußball-Mongo-Scan fehlgeschlagen (" + type(exc).__name__ +
              "). MONGO, MONGO_DB, Leserechte und Atlas Network Access prüfen.")
        return 2
