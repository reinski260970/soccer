"""Bet365 Valuebet watch from SureBet API."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from . import telegram
from . import matching
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



def _event_key(v: surebet.SurebetValue) -> tuple:
    teams = tuple(sorted(matching.norm(x) for x in v.teams if x))
    if v.kickoff:
        # Different books can differ slightly in listed start time; 30-minute bucket.
        minute = (v.kickoff.minute // 30) * 30
        kick = v.kickoff.replace(minute=minute, second=0, microsecond=0).isoformat()
    else:
        kick = ""
    return (v.sport, kick, teams)


def _bet_key(v: surebet.SurebetValue) -> tuple:
    return (_event_key(v), matching.norm(v.selection), v.market.lower())


def matched(values: list[surebet.SurebetValue]) -> list[list[surebet.SurebetValue]]:
    groups: dict[tuple, list[surebet.SurebetValue]] = {}
    for v in values:
        groups.setdefault(_bet_key(v), []).append(v)
    rows = []
    for group in groups.values():
        books = {v.bookmaker for v in group}
        if len(books) >= 2:
            rows.append(sorted(group, key=lambda v: v.odds, reverse=True))
    rows.sort(key=lambda g: (-(len({v.bookmaker for v in g})), -(g[0].odds if g else 0)))
    return rows

def telegram_text(values: list[surebet.SurebetValue], error: str | None = None) -> str:
    now = datetime.now(_TZ).strftime("%d.%m.%Y %H:%M")
    out = [f"💰 Bet365 · Betfair · OrbitX Value-Match · {now}"]
    if error:
        return "\n".join(out + [f"⚠️ {error}"])
    if not values:
        return "\n".join(out + ["Keine Valuebets für Fußball, Hockey oder Basketball."])

    names = {"bet365": "Bet365", "betfair": "Betfair", "orbitxch": "OrbitX"}
    pairs = matched(values)
    if pairs:
        out += ["", "🔗 GEMATCHTE MÄRKTE"]
        for group in pairs[:20]:
            v = group[0]
            out += ["", f"{_kick(v.kickoff)} · {v.sport} · {v.tournament or 'Liga unbekannt'}",
                    f"{v.event}", f"➡️ {v.selection} · {v.market}"]
            for q in group:
                side = "" if q.back else " LAY"
                out.append(f"   {names.get(q.bookmaker, q.bookmaker)}{side}: {_q(q.odds)}"
                           + (f" | EV {_pct(q.ev)}" if q.ev is not None else ""))

    out += ["", "📡 ALLE SUREBET-VALUE-SIGNALE"]
    labels = {"Football": "⚽ Fußball", "Hockey": "🏒 Eishockey", "Basketball": "🏀 Basketball"}
    for sport in ("Football", "Hockey", "Basketball"):
        rows = [v for v in values if v.sport == sport]
        if not rows:
            continue
        out += ["", labels[sport]]
        for v in rows[:20]:
            side = "" if v.back else " LAY"
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
                f"  ➡️ {v.selection} @ {_q(v.odds)} ({names.get(v.bookmaker, v.bookmaker)}{side})",
                ("  " + " | ".join(calc)) if calc else "  SureBet: Value-Signal",
            ]
    out += ["", "ℹ️ Match = gleiches Event + gleiche Markt-/Auswahlstruktur. PLAY-Freigabe durch unser Modell bleibt separat."]
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
