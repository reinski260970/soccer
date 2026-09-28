"""Fußball-Datenbank (MongoDB), ausschließlich lesend.

Die Verbindung kommt aus einer Umgebungsvariablen (Standard: MONGO_URI_FOOTBALL,
bei Bedarf anders benennbar über ODDSWATCH_FOOTBALL_DB_ENV). MONGO_URI ist die
Tennis-Datenbank und wird von oddswatch nicht verwendet.

Leseschutz: Diese Klasse bietet nur list/count/find/aggregate ohne
Schreib-Stages ($out/$merge). Schreibende Methoden existieren nicht; der
Client wird zusätzlich mit readPreference=secondaryPreferred geöffnet.
Am sichersten ist trotzdem ein Datenbank-Benutzer mit reiner Leserolle.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_ENV = "MONGO_URI_FOOTBALL"
_WRITE_STAGES = {"$out", "$merge"}


def _uri() -> str:
    name = os.environ.get("ODDSWATCH_FOOTBALL_DB_ENV", DEFAULT_ENV)
    uri = os.environ.get(name, "")
    if not uri:
        raise RuntimeError(f"{name} nicht gesetzt (Fußball-Datenbank)")
    return uri


class ReadOnlyDB:
    def __init__(self, uri: str | None = None, timeout_ms: int = 8000, client=None):
        if client is None:
            from pymongo import MongoClient
            client = MongoClient(uri or _uri(), serverSelectionTimeoutMS=timeout_ms,
                                 readPreference="secondaryPreferred", appname="oddswatch-readonly")
        self.client = client

    def databases(self) -> list[str]:
        return [d for d in self.client.list_database_names() if d not in ("admin", "local", "config")]

    def collections(self, db: str) -> list[str]:
        return sorted(self.client[db].list_collection_names())

    def count(self, db: str, coll: str, flt: dict | None = None) -> int:
        return self.client[db][coll].count_documents(flt or {})

    def find(self, db: str, coll: str, flt: dict | None = None, limit: int = 100,
             sort: list | None = None, projection: dict | None = None) -> list[dict]:
        cur = self.client[db][coll].find(flt or {}, projection)
        if sort:
            cur = cur.sort(sort)
        return list(cur.limit(limit))

    def aggregate(self, db: str, coll: str, pipeline: list[dict]) -> list[dict]:
        for st in pipeline:
            if _WRITE_STAGES & set(st):
                raise PermissionError("Schreibende Aggregation ($out/$merge) ist gesperrt")
        return list(self.client[db][coll].aggregate(pipeline))

    def schema(self, db: str, coll: str, sample: int = 50) -> dict[str, str]:
        """Feldnamen (auch verschachtelt) mit Beispieltyp aus einer Stichprobe."""
        fields: dict[str, str] = {}

        def walk(d: Any, prefix: str = "") -> None:
            if isinstance(d, dict):
                for k, v in d.items():
                    key = f"{prefix}.{k}" if prefix else k
                    fields.setdefault(key, type(v).__name__)
                    if isinstance(v, dict):
                        walk(v, key)
        for doc in self.client[db][coll].aggregate([{"$sample": {"size": sample}}]):
            walk(doc)
        return dict(sorted(fields.items()))


def overview(db: ReadOnlyDB | None = None) -> list[str]:
    db = db or ReadOnlyDB()
    out = []
    for d in db.databases():
        out.append(f"Datenbank {d}")
        for c in db.collections(d):
            try:
                n = db.count(d, c)
            except Exception as e:  # noqa: BLE001 – z. B. fehlende Rechte auf Views
                n = f"? ({e.__class__.__name__})"
            out.append(f"  {c}: {n} Dokumente")
    return out
