"""Bet365 Valuebet watch from SureBet API."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from . import telegram
from .sources import surebet

_TZ = ZoneInfo("Europe/Vienna")


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{x * 100:.1f}%".replace(".", ",")


def _q(x: float | None) -> str:
    return "–" if x is None else f"{x:.2f}".replace(".", ",")


def _kick(dt) -> str:
    if dt is None:
        return "Zeit unbekannt"
    return dt.astimezone(_TZ).strftime("%d.%m. %H:%M")


def telegram_text(values: list[surebet.SurebetValue], error: str | None = None) -> str:
    now = datetime.now(_TZ).strftime("%d.%m.%Y %H:%M")
    out = [f"💰 Bet365 Value-Watch · {now}"]
    if error:
        return "\n".join(out + [f"⚠️ {error}"])
    if not values:
        return "\n".join(out + ["Keine Bet365-Valuebets für Fußball, Hockey oder Basketball."])
    labels = {"Football": "⚽ Fußball", "Hockey": "🏒 Eishockey", "Basketball": "🏀 Basketball"}
    for sport in ("Football", "Hockey", "Basketball"):
        rows = [v for v in values if v.sport == sport]
        if not rows:
            continue
        out += ["", labels[sport]]
        for v in rows[:15]:
            calc = []
            if v.fair_odds is not None:
                calc.append(f"SureBet fair {_q(v.fair_odds)}")
            if v.ev is not None:
                calc.append(f"EV {_pct(v.ev)}")
            if v.overvalue is not None:
                calc.append(f"Overvalue {_pct(v.overvalue)}")
            out += [
                f"• {_kick(v.kickoff)} · {v.tournament or 'Liga unbekannt'}",
                f"  {v.event}",
                f"  ➡️ {v.selection} @ {_q(v.odds)} (Bet365)",
                ("  " + " | ".join(calc)) if calc else "  SureBet: Value-Signal",
            ]
    out += ["", "ℹ️ Quelle: SureBet Valuebets/Bet365. Das ist ein Marktsignal; oddswatch-Modellfreigabe bleibt separat."]
    return "\n".join(out)


def run(send: bool = False, limit: int = 100) -> list[str]:
    values, err = surebet.fetch_valuebets(limit=limit)
    txt = telegram_text(values, err)
    lines = [txt, f"Gefunden: {len(values)} Bet365-Valuebets"]
    if send:
        r = telegram.send(txt)
        lines.append(
            f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}"
        )
    return lines
