"""Export der PLAY-Freigaben (valuebets.csv) im Sharpery-Importformat.

Aufruf:  python -m oddswatch.export_sharpery [--out exports/sharpery]
Schreibt <out>.xlsx und <out>.csv mit den Sharpery-Spalten. Jede PLAY-Freigabe
gilt als gespielt; für Sharpery gilt 1 EH = 10 EUR. Offene Tipps -> Result "pending".
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
         "nl": "Ice Hockey", "khl": "Ice Hockey", "extraliga": "Ice Hockey"}
LEAGUE = {"bundesliga": "Bundesliga", "2bundesliga": "2. Bundesliga",
          "austria": "Austrian Bundesliga", "ucl": "UEFA Champions League",
          "uel": "UEFA Europa League", "uecl": "UEFA Conference League",
          "nations": "UEFA Nations League", "nfl": "NFL", "nba": "NBA", "nhl": "NHL",
          "del": "DEL", "icehl": "ICE Hockey League", "shl": "SHL", "liiga": "Liiga",
          "nl": "National League", "khl": "KHL", "extraliga": "Czech Extraliga"}
RESULT = {"win": "won", "loss": "lost", "void": "void"}

# Sharpery-Bankrollkonvention: 1 Einsatz-Einheit (EH) = 10 EUR.
# Das interne Journal bleibt weiterhin in EH; nur der Export wird in EUR umgerechnet.
SHARPERY_EH_EUR = 10.0


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


def _is_sharpery_play(r: dict) -> bool:
    """Nur echte PLAY-/Valuebet-Zeilen, keine zurückgezogenen oder Market-only Scans."""
    from .active import eligible
    if not eligible(r):
        return False
    if (r.get("result") or "").lower() == "withdrawn":
        return False
    reason = (r.get("reason") or "").lower()
    blocked = (
        "modell nicht validiert",
        "reiner preisvergleich",
        "schnellscan (preisvergleich ohne modell)",
        "markt (draftkings)",
    )
    return not any(x in reason for x in blocked)


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
        "Stake": (round(_f(r.get("stake_eh")) * SHARPERY_EH_EUR, 2)
                  if _f(r.get("stake_eh")) is not None else None),
        "Result": RESULT.get(r.get("result", ""), "pending"),
        "Liquidity": None,
        "Live": "no",
        "Side": r.get("market", ""),
        "Notes": notes,
        "Tags": ";".join(t for t in tags if t),
    }


def export(journal_root: str = "data/journal", out: str = "exports/sharpery") -> tuple[Path, Path, int]:
    rows = [to_row(r) for r in Journal(journal_root).read("valuebets") if _is_sharpery_play(r)]
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


def _candidate_row(c, now_iso: str) -> dict:
    lg = c.league or ""
    soccer = lg not in SPORT
    play = (c.stake_eh or 0) > 0 and not c.flags
    notes = f"fair {c.fair_odds:.2f}, spielbar ab {c.min_odds:.2f}; Modell {c.p_model * 100:.1f} %"
    if c.source == "orbit":
        notes += "; Quote nach 3 % Orbit-Kommission"
    if c.reason:
        notes += f"; {c.reason}"
    tags = [lg, "PLAY" if play else "MODELL"] + (["Schaetzung"] if c.estimate else [])
    return {
        "Placed At": now_iso,
        "Kickoff": _iso_z(c.kickoff),
        "Event": c.event.replace(" – ", " vs "),
        "Sport": "Soccer" if soccer else SPORT[lg],
        "League": LEAGUE.get(lg, lg.upper()),
        "Market": "1X2" if soccer else "Moneyline",
        "Selection": c.selection,
        "Period": "Regular Time" if soccer else "Game",
        "Bookmaker": (c.source or "").capitalize(),
        "Opening Odds": None,
        "Bet Odds": round(c.odds, 2),
        "Closing Novig Odds": None,
        "EV %": round(c.ev * 100, 2),
        "CLV %": None,
        # Sharpery verlangt einen positiven Einsatz: Modellvorschlag, sonst 1 EH (= 10 EUR).
        "Stake": round(max(c.stake_eh or 0, 1.0) * SHARPERY_EH_EUR, 2),
        "Result": "pending",
        "Liquidity": c.liquidity,
        "Live": "no",
        "Side": c.market,
        "Notes": notes[:250],
        "Tags": ";".join(t for t in tags if t),
    }


FORECAST_COLUMNS = ["Liga", "Anstoß (Wien)", "Spiel", "Modell Heim %", "Modell Remis %", "Modell Gast %",
                    "Fair Heim", "Fair Remis", "Fair Gast", "Bester Kurs Heim", "Bester Kurs Gast",
                    "Quelle", "Kennzahlen"]


def _forecast_row(fx) -> list:
    from zoneinfo import ZoneInfo
    p = fx.probs or {}
    def fair(k):
        return round(1 / p[k], 2) if p.get(k) else None
    def best(side):
        offers = (fx.market_quotes or {}).get(side) or (fx.offers or {}).get(side) or []
        offers = [o for o in offers if getattr(o, "executable", True)]
        return max((o for o in offers), key=lambda o: o.odds, default=None)
    bh, ba = best("home"), best("away")
    ko = fx.game.kickoff.astimezone(ZoneInfo("Europe/Vienna")).strftime("%d.%m. %H:%M")
    pct = lambda k: round(p[k] * 100, 1) if p.get(k) is not None else None
    return [LEAGUE.get(fx.league, fx.league), ko, fx.game.title, pct("home"), pct("draw"), pct("away"),
            fair("home"), fair("draw"), fair("away"),
            round(bh.odds, 2) if bh else None, round(ba.odds, 2) if ba else None,
            ", ".join(sorted({o.source for o in (bh, ba) if o})), fx.detail]


def export_scan(result, out: str) -> tuple[Path, int, int]:
    """Spieltags-Scan als Sharpery-Excel: Blatt 'Bets' (EV > 0) + Blatt 'Prognosen' (alle Spiele)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cands = sorted((c for c in result.candidates if c.ev > 0), key=lambda c: -c.ev)
    rows = [_candidate_row(c, now_iso) for c in cands]
    wb = Workbook()
    ws = wb.active
    ws.title = "Bets"
    ws.append(COLUMNS)
    for r in rows:
        ws.append([r[k] for k in COLUMNS])
    ws2 = wb.create_sheet("Prognosen")
    ws2.append(FORECAST_COLUMNS)
    fx_sorted = sorted(result.fixtures, key=lambda f: (f.game.kickoff, f.league))
    for fx in fx_sorted:
        ws2.append(_forecast_row(fx))
    for sheet in (ws, ws2):
        for c in sheet[1]:
            c.font = Font(bold=True)
        for col in sheet.columns:
            width = max(len(str(c.value or "")) for c in col)
            sheet.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 60)
        sheet.freeze_panes = "A2"
    path = Path(out).with_suffix(".xlsx")
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path, len(rows), len(fx_sorted)


def main() -> None:
    ap = argparse.ArgumentParser(description="PLAY-Freigaben als Sharpery-Import exportieren")
    ap.add_argument("--journal", default="data/journal")
    ap.add_argument("--out", default="exports/sharpery")
    a = ap.parse_args()
    xlsx, csv_path, n = export(a.journal, a.out)
    print(f"{n} Tipps exportiert: {xlsx} und {csv_path}")


if __name__ == "__main__":
    main()
