"""Tennis-Valuebets aus MongoDB Atlas (tennis_db), nur lesend.

Die Datenbank gehört zum separaten Tennis-Runner (ML-Modell v28.x, Quoten von
tennisexplorer). oddswatch liest daraus nur:

- ``valuebets_active``: offene, freigegebene Valuebets (``is_valuebet``,
  ``PUBLICATION_APPROVED``, Status ``open``) ab heute,
- ``valuebets_history``: abgerechnete Tipps für Bilanz und CLV.

Verbindung über die Umgebungsvariable ``MONGODB_URI`` bzw. ``MONGO_URI`` (Connection-String eines
Read-only-Datenbankbenutzers), Datenbankname über ``MONGODB_DB`` (Standard
``tennis_db``). Ohne URI oder bei Verbindungsfehlern kommt ein Fehlertext zurück –
es wird nie auf alte oder erfundene Daten zurückgefallen.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from statistics import median

DB_DEFAULT = "tennis_db"
_ACTIVE_FILTER = {"is_valuebet": True, "status": "open",
                  "publication_status": "PUBLICATION_APPROVED"}
_ACTIVE_FIELDS = ["p1", "p2", "selection", "selected_odds", "market_odds", "prob", "ev",
                  "stake_eh", "tour", "tournament", "tier", "surface", "match_day",
                  "scheduled_time_vienna", "start_time_verified", "odds_source",
                  "runner_version", "valuebet_key", "te_match_id"]
_HISTORY_FIELDS = ["status", "stake_eh", "profit_eh", "clv_odds_pct", "closing_status",
                   "match_day", "tour"]


@dataclass
class TennisBet:
    key: str
    tour: str
    tournament: str
    tier: str
    surface: str
    match_day: str            # YYYY-MM-DD
    time_vienna: str          # HH:MM (Ortszeit Wien), "" wenn unbekannt
    time_verified: bool
    event: str                # "Spieler 1 vs Spieler 2"
    selection: str            # Name des getippten Spielers
    odds: float
    prob: float
    stake_eh: float
    odds_source: str
    model: str
    te_match_id: str

    @property
    def fair_odds(self) -> float:
        return 1.0 / self.prob

    @property
    def ev(self) -> float:
        return self.prob * self.odds - 1.0

    @property
    def min_odds(self) -> float:
        """Spielbar ab: EV ≥ 3 % gegen die Modellwahrscheinlichkeit (wie im Rest von oddswatch)."""
        return 1.03 / self.prob


@dataclass
class TrackRecord:
    settled: int
    won: int
    stake_eh: float
    profit_eh: float
    clv_n: int
    clv_median_pct: float | None
    first_day: str
    last_day: str

    @property
    def roi(self) -> float:
        return self.profit_eh / self.stake_eh if self.stake_eh else 0.0


def to_bet(doc: dict) -> TennisBet | None:
    """Atlas-Dokument -> TennisBet; None, wenn Pflichtfelder fehlen oder unplausibel sind."""
    sel = doc.get("selection")
    p1, p2 = doc.get("p1"), doc.get("p2")
    odds = doc.get("selected_odds") or doc.get("market_odds")
    prob = doc.get("prob")
    if sel not in ("P1", "P2") or not p1 or not p2 or not odds or not prob:
        return None
    odds, prob = float(odds), float(prob)
    if odds <= 1.0 or not 0.0 < prob < 1.0:
        return None
    return TennisBet(
        key=str(doc.get("valuebet_key") or ""), tour=doc.get("tour") or "",
        tournament=doc.get("tournament") or "", tier=doc.get("tier") or "",
        surface=doc.get("surface") or "", match_day=doc.get("match_day") or "",
        time_vienna=doc.get("scheduled_time_vienna") or "",
        time_verified=bool(doc.get("start_time_verified")),
        event=f"{p1} vs {p2}", selection=p1 if sel == "P1" else p2,
        odds=odds, prob=prob, stake_eh=float(doc.get("stake_eh") or 0.0),
        odds_source=doc.get("odds_source") or "", model=doc.get("runner_version") or "",
        te_match_id=str(doc.get("te_match_id") or ""))


def track_record(docs: list[dict]) -> TrackRecord:
    """Bilanz aus valuebets_history. CLV nur mit erfasster Closing-Quote (Median, robust gegen Ausreißer)."""
    done = [d for d in docs if d.get("status") in ("won", "lost")]
    clv = [float(d["clv_odds_pct"]) for d in done
           if d.get("clv_odds_pct") is not None and d.get("closing_status") == "captured"]
    days = sorted(d["match_day"] for d in done if d.get("match_day"))
    return TrackRecord(
        settled=len(done), won=sum(d["status"] == "won" for d in done),
        stake_eh=sum(float(d.get("stake_eh") or 0) for d in done),
        profit_eh=sum(float(d.get("profit_eh") or 0) for d in done),
        clv_n=len(clv), clv_median_pct=median(clv) if clv else None,
        first_day=days[0] if days else "", last_day=days[-1] if days else "")


def _db(uri: str | None, db_name: str | None):
    uri = uri or os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI")
    if not uri:
        return None, "MONGODB_URI/MONGO_URI nicht gesetzt – Tennis (tennis_db) nicht abrufbar"
    try:
        from pymongo import MongoClient
    except ImportError:
        return None, "Paket pymongo fehlt (pip install -r requirements.txt)"
    client = MongoClient(uri, serverSelectionTimeoutMS=15000, appname="oddswatch")
    return client[db_name or os.environ.get("MONGODB_DB") or DB_DEFAULT], None


def fetch(uri: str | None = None, db_name: str | None = None,
          today: date | None = None) -> tuple[list[TennisBet], TrackRecord | None, str | None]:
    """Offene Valuebets ab heute + Bilanz. Rückgabe (bets, bilanz, fehler)."""
    db, err = _db(uri, db_name)
    if err:
        return [], None, err
    day = (today or date.today()).isoformat()
    try:
        active = list(db.valuebets_active.find(
            {**_ACTIVE_FILTER, "match_day": {"$gte": day}},
            {f: 1 for f in _ACTIVE_FIELDS}))
        hist = list(db.valuebets_history.find(
            {"publication_status": "PUBLICATION_APPROVED"}, {f: 1 for f in _HISTORY_FIELDS}))
    except Exception as e:  # noqa: BLE001 – Fehlertext ist die Auskunft
        return [], None, f"tennis_db nicht erreichbar: {type(e).__name__}: {e}"
    bets = [b for b in map(to_bet, active) if b]
    bets.sort(key=lambda b: (b.match_day, b.time_vienna, -b.ev))
    return bets, track_record(hist), None
