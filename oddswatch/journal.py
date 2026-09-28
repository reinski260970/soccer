"""Getrennte Ledger: Prognosen, freigegebene Valuebets, gespielte Wetten.

CSV-Dateien unter data/journal/. Abrechnung: Gewinn in EH und CLV.
CLV = genommene Quote / faire Closing-Quote - 1 (Closing de-vigged).
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

LEDGERS = {
    "forecasts": ["created_at", "league", "event_id", "event", "kickoff", "market",
                  "p_model", "p_ref", "p_final", "fair_odds", "estimate", "model", "inputs",
                  "outcome"],
    "valuebets": ["created_at", "observed_at", "league", "event", "kickoff", "market",
                  "selection", "source", "ref", "odds", "p_model", "p_ref", "p_final",
                  "fair_odds", "min_odds", "edge", "ev", "stake_eh", "estimate", "reason",
                  "result", "closing_fair_odds", "clv", "pnl_eh"],
    "news": ["seen_at", "published", "league", "event", "status", "team", "side", "category",
             "severe", "source", "confirmed_by", "title", "link"],
    "placed": ["placed_at", "event", "kickoff", "market", "selection", "bookmaker",
               "odds_taken", "stake_eh", "stake_usd", "valuebet_ref", "ref", "fill_id", "result",
               "closing_fair_odds", "clv", "pnl_eh"],
}


class Journal:
    def __init__(self, root: str | os.PathLike = "data/journal"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, name: str) -> Path:
        return self.root / f"{name}.csv"

    def read(self, name: str) -> list[dict]:
        p = self.path(name)
        if not p.exists():
            return []
        with p.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def append(self, name: str, rows: list[dict]) -> None:
        cols = LEDGERS[name]
        p = self.path(name)
        new = not p.exists()
        with p.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            if new:
                w.writeheader()
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            for r in rows:
                r = {**r}
                for ts in ("created_at", "placed_at", "seen_at"):
                    if ts in cols and not r.get(ts):
                        r[ts] = now
                w.writerow({k: _fmt(r.get(k, "")) for k in cols})

    def write(self, name: str, rows: list[dict]) -> None:
        cols = LEDGERS[name]
        with self.path(name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: _fmt(r.get(k, "")) for k in cols})

    def settle(self, name: str, event: str, market: str, won: bool | None,
               closing_fair_odds: float | None = None, ref: str | None = None) -> int:
        """won=None -> Push/Void (Einsatz zurück). ref grenzt auf einen
        Kalshi-Ticker ein (mehrere Outcomes eines Events). Gibt Anzahl Treffer zurück."""
        rows = self.read(name)
        odds_key = "odds" if name == "valuebets" else "odds_taken"
        n = 0
        for r in rows:
            if r["event"] != event or r["market"] != market or r.get("result"):
                continue
            if ref is not None and r.get("ref") != ref:
                continue
            odds, stake = float(r[odds_key]), float(r["stake_eh"])
            r["result"] = "void" if won is None else ("win" if won else "loss")
            r["pnl_eh"] = 0.0 if won is None else (stake * (odds - 1) if won else -stake)
            if closing_fair_odds:
                r["closing_fair_odds"] = closing_fair_odds
                r["clv"] = odds / closing_fair_odds - 1
            n += 1
        self.write(name, rows)
        return n

    def summary(self, name: str) -> dict:
        rows = [r for r in self.read(name) if r.get("result")]
        stake = sum(float(r["stake_eh"]) for r in rows if r["result"] != "void")
        pnl = sum(float(r["pnl_eh"] or 0) for r in rows)
        clvs = [float(r["clv"]) for r in rows if r.get("clv")]
        return {"settled": len(rows), "stake_eh": stake, "pnl_eh": pnl,
                "roi": pnl / stake if stake else 0.0,
                "avg_clv": sum(clvs) / len(clvs) if clvs else None,
                "clv_n": len(clvs)}


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return v
