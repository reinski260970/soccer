"""Tennis-Bericht aus tennis_db (externes Modell, nur lesend).

Die Tipps stammen vom Tennis-Runner (eigenes ML-Modell gegen tennisexplorer-Quoten),
nicht von oddswatch. Sie werden deshalb nie als PLAY freigegeben: Status ist
KANDIDAT nur, wenn die Bilanz des Runners belegt, dass er besser als der Markt ist
(≥ 200 abgerechnete Tipps, ROI > 0 und Median-CLV > 0), sonst INFO.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from .report import _eh, _pct, _q
from .sources import tennis_atlas
from .sources.tennis_atlas import TennisBet, TrackRecord

STATE = Path("data/journal/tennis_alerts.json")
_WD = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def validated(tr: TrackRecord | None) -> bool:
    return bool(tr and tr.settled >= 200 and tr.roi > 0
                and tr.clv_median_pct is not None and tr.clv_median_pct > 0)


def _when(b: TennisBet) -> str:
    try:
        d = date.fromisoformat(b.match_day)
        day = f"{_WD[d.weekday()]} {d:%d.%m.}"
    except ValueError:
        day = b.match_day or "Datum unbekannt"
    if not b.time_vienna:
        return day
    return f"{day} {b.time_vienna}" + ("" if b.time_verified else " (Zeit unbestätigt)")


def _head(b: TennisBet) -> str:
    return " · ".join(x for x in (b.tour, b.tournament, b.tier, b.surface, _when(b)) if x)


def _record_line(tr: TrackRecord | None) -> str:
    if not tr or not tr.settled:
        return "Bilanz des Runners: keine abgerechneten Tipps."
    clv = (f"Median-CLV {_pct(tr.clv_median_pct / 100)} ({tr.clv_n} mit Closing)"
           if tr.clv_median_pct is not None else "CLV: keine Closing-Quoten")
    return (f"Bilanz des Runners ({tr.first_day} bis {tr.last_day}): {tr.settled} Tipps, "
            f"{tr.won} gewonnen, Einsatz {_eh(tr.stake_eh)} EH, Ergebnis "
            f"{'+' if tr.profit_eh >= 0 else ''}{_eh(tr.profit_eh)} EH, ROI {_pct(tr.roi)}, {clv}.")


def report(bets: list[TennisBet], tr: TrackRecord | None, error: str | None, stand: str) -> str:
    lines = [f"# Tennis (tennis_db) – Stand {stand}", ""]
    if error:
        return "\n".join(lines + [f"⚠️ Datenlage: {error}"]) + "\n"
    ok = validated(tr)
    lines += [_record_line(tr),
              "Status: " + ("KANDIDAT – Bilanz belegt einen Vorteil gegen den Markt." if ok else
                            "INFO – Vorteil gegen den Markt nicht belegt (ROI/CLV), keine Freigabe."),
              "Quelle: externes ML-Modell des Tennis-Runners, Quoten von tennisexplorer; "
              "von oddswatch nicht gegen eine unabhängige Referenz geprüft.", ""]
    if not bets:
        return "\n".join(lines + ["Keine offenen Valuebets ab heute."]) + "\n"
    lines += ["| Spiel | Termin | Tipp | Quote | fair (Modell) | spielbar ab | EV | Einsatz |",
              "|---|---|---|---|---|---|---|---|"]
    for b in bets:
        lines.append(f"| {b.event} | {_head(b)} | {b.selection} | {_q(b.odds)} | "
                     f"{_q(b.fair_odds)} ({_pct(b.prob)}) | {_q(b.min_odds)} | {_pct(b.ev)} | "
                     f"{_eh(b.stake_eh)} EH |")
    return "\n".join(lines) + "\n"


def telegram_text(bets: list[TennisBet], tr: TrackRecord | None, stand: str) -> str:
    tag = "🎾 KANDIDAT" if validated(tr) else "🎾 INFO (nicht freigegeben)"
    out = [f"🎾 Tennis-Valuebets {stand}", _record_line(tr)]
    for b in bets:
        out += ["", f"{tag} · {_head(b)}", f"🆚 {b.event}",
                f"➡️ {b.selection} @ {_q(b.odds)} ({b.odds_source or 'Quelle unbekannt'})",
                f"   fair {_q(b.fair_odds)} | min {_q(b.min_odds)} | EV {_pct(b.ev)} | {_eh(b.stake_eh)} EH"]
    return "\n".join(out)


def new_bets(bets: list[TennisBet], state: Path = STATE) -> list[TennisBet]:
    """Nur Tipps, die noch nicht (zu dieser Quote) gemeldet wurden."""
    seen = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
    return [b for b in bets if seen.get(b.key) != round(b.odds, 2)]


def mark_sent(bets: list[TennisBet], state: Path = STATE) -> None:
    seen = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
    seen.update({b.key: round(b.odds, 2) for b in bets})
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(seen, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def run(send: bool = False, all_bets: bool = False) -> list[str]:
    from . import telegram
    stand = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    bets, tr, err = tennis_atlas.fetch()
    md = report(bets, tr, err, stand)
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / f"{date.today():%Y-%m-%d}-tennis.md").write_text(md, encoding="utf-8")
    lines = [md.rstrip()]
    if err:
        return lines
    fresh = bets if all_bets else new_bets(bets)
    if not fresh:
        return lines + ["Telegram: keine neuen Tennis-Tipps – nicht gesendet"]
    tg = telegram_text(fresh, tr, stand)
    lines.append("--- Telegram ---\n" + tg)
    if send:
        r = telegram.send(tg)
        if r["sent"]:
            mark_sent(fresh)
        lines.append(f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}")
    return lines
