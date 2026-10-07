"""Read-only Mongo audit for roster/coach/transfer-like fields.

Outputs ONLY collection names, candidate field names and presence counts.
No document values are written.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

OUT = Path("data/mongo_change_fields_audit.json")
TOKENS = (
    "coach", "manager", "trainer", "squad", "roster", "lineup",
    "player", "transfer", "injury", "formation", "suspension",
)


def _mongo_db(client):
    from pymongo.errors import ConfigurationError
    try:
        db = client.get_default_database()
    except ConfigurationError:
        db = None
    return db if db is not None else client["euro_football"]


def _candidate(name: str) -> bool:
    s = str(name).lower()
    return any(t in s for t in TOKENS)


def run(out: Path = OUT):
    from pymongo import MongoClient, timeout

    uri = (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGODB_URI") or "").strip()
    if not uri:
        raise RuntimeError("MONGO_SOCCER fehlt")

    result = {"collections": {}, "matching_collection_names": []}

    with timeout(120):
        with MongoClient(
            uri,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
            appname="oddswatch-change-field-audit",
        ) as client:
            db = _mongo_db(client)
            names = db.list_collection_names()
            result["matching_collection_names"] = sorted(
                [n for n in names if _candidate(n)]
            )

            for name in names:
                if name not in {"mains", "extra_leagues"} and not _candidate(name):
                    continue
                col = db[name]
                fields = set()
                for doc in col.find({}, projection=None).limit(500):
                    fields.update(k for k in doc.keys() if _candidate(k))

                counts = {}
                for field in sorted(fields):
                    counts[field] = col.count_documents({
                        field: {"$exists": True, "$ne": None}
                    })
                result["collections"][name] = {
                    "candidate_fields": sorted(fields),
                    "presence_counts": counts,
                }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return [f"Mongo change-field audit gespeichert: {out}"]


if __name__ == "__main__":
    for line in run():
        print(line)
