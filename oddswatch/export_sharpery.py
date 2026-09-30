"""Export der PLAY-Freigaben (valuebets.csv) im Sharpery-Importformat.

Aufruf:  python -m oddswatch.export_sharpery [--out exports/sharpery]
Schreibt <out>.xlsx und <out>.csv mit den Sharpery-Spalten. Jede PLAY-Freigabe
gilt als gespielt; Einsatz = stake_eh (Einheiten). Offene Tipps -> Result "pending".
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from .journal import Journal

COLUMNS = ["Placed At", "Kickoff", "Event", "Sport", "League", "Market", "Selection",
           "Period", "Bookmaker", "Opening Odds", "Bet Odds", "Closing Novig Odds",
           "EV %", "CLV %", "Stake", "Result", "Liquidity", "Live", "Side", "Notes", "Tags"]

SPORT = {"nfl": "American Football", "nba": "Basketball", "nhl": "Ice Hockey",
         "del": "Ice Hockey", "icehl": "Ice Hockey", "shl": "Ice Hockey", "liiga": "Ice Hockey",
         "nl": "Ice Hockey", "khl": "Ice Hockey"}
LEAGUE = {"bundesliga": "Bundesliga", "2bundesliga": "2. Bundesliga",
          "austria": "Austrian Bundesliga", "ucl": "UEFA Champions League",
          "uel": "UEFA Europa League", "uecl": "UEFA Conference League",
          "nations": "UEFA Nations League", "nfl": "NFL", "nba": "NBA", "nhl": "NHL",
          "del": "DEL", "icehl": "ICE Hockey League", "shl": "SHL", "liiga": "Liiga",
          "nl": "National League", "khl": "KHL"}
RESULT = {"win": "won", "loss": "lost", "void": "void"}


def _iso_z(s: str) -> str:
    if not s:
        return ""
    try:
        t = datetime.fromisoformat(s)
    except ValueError:
        return s
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(s: str) -> float | None:
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def to_row(r: dict) -> dict:
    lg = r.get("league", "")
    soccer = lg not in SPORT
    odds, ev, clv = _f(r.get("odds")), _f(r.get("ev")), _f(r.get("clv"))
    fair, mn = _f(r.get("fair_odds")), _f(r.get("min_odds"))
    notes = f"PLAY-Freigabe; Preis {r.get('source', '')}"
    if fair and mn:
        notes += f"; fair {fair:.2f}, spielbar ab {mn:.2f}"
    tags = [lg, "PLAY"] + (["Schaetzung"] if r.get("estimate") == "True" else [])
    return {
        "Placed At": _iso_z(r.get("created_at", "")),
        "Kickoff": _iso_z(r.get("kickoff", "")),
        "Event": r.get("event", "").replace(" – ", " vs "),
        "Sport": "Soccer" if soccer else SPORT[lg],
        "League": LEAGUE.get(lg, lg.upper()),
        "Market": "1X2" if soccer else "Moneyline",
        "Selection": r.get("selection", ""),
        "Period": "Regular Time" if soccer else "Game",
        "Bookmaker": r.get("source", "").capitalize(),
        "Opening Odds": None,
        "Bet Odds": round(odds, 2) if odds else None,
        "Closing Novig Odds": _f(r.get("closing_fair_odds")),
        "EV %": round(ev * 100, 2) if ev is not None else None,
        "CLV %": round(clv * 100, 2) if clv is not None else None,
        "Stake": _f(r.get("stake_eh")),
        "Result": RESULT.get(r.get("result", ""), "pending"),
        "Liquidity": None,
        "Live": "no",
        "Side": r.get("market", ""),
        "Notes": notes,
        "Tags": ";".join(t for t in tags if t),
    }


def export(journal_root: str = "data/journal", out: str = "exports/sharpery") -> tuple[Path, Path, int]:
    # Zurückgezogene Freigaben gelten als nicht gespielt und werden nicht exportiert.
    rows = [to_row(r) for r in Journal(journal_root).read("valuebets") if r.get("result") != "withdrawn"]
    base = Path(out)
    base.parent.mkdir(parents=True, exist_ok=True)
    csv_path, xlsx_path = base.with_suffix(".csv"), base.with_suffix(".xlsx")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: "" if v is None else v for k, v in r.items()})
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    ws = wb.active
    ws.title = "Bets"
    ws.append(COLUMNS)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in rows:
        ws.append([r[k] for k in COLUMNS])
    for col in ws.columns:
        width = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 60)
    ws.freeze_panes = "A2"
    wb.save(xlsx_path)
    return xlsx_path, csv_path, len(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="PLAY-Freigaben als Sharpery-Import exportieren")
    ap.add_argument("--journal", default="data/journal")
    ap.add_argument("--out", default="exports/sharpery")
    a = ap.parse_args()
    xlsx, csv_path, n = export(a.journal, a.out)
    print(f"{n} Tipps exportiert: {xlsx} und {csv_path}")


if __name__ == "__main__":
    main()
