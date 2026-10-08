"""Bet365 Valuebet watch from SureBet API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import telegram
from . import matching
from .sources import surebet

_TZ = ZoneInfo("Europe/Vienna")


@dataclass
class Audit:
    value: surebet.SurebetValue
    status: str
    our_probability: float | None = None
    our_fair: float | None = None
    our_ev: float | None = None
    reference_probability: float | None = None
    reference_fair: float | None = None
    note: str = ""


def _candidate_side(v: surebet.SurebetValue) -> str | None:
    m = (v.market or "").lower()
    if "win1retx" in m or "win2retx" in m or " ah" in m or " eh" in m:
        return None
    if "win1" in m:
        return "home"
    if "win2" in m:
        return "away"
    if "draw" in m:
        return "draw"
    return None


def _same_event(v: surebet.SurebetValue, fx) -> bool:
    if len(v.teams) != 2 or v.kickoff is None:
        return False
    if abs(fx.game.kickoff - v.kickoff) > timedelta(hours=12):
        return False
    direct = matching.same(v.teams[0], fx.game.home.name) and matching.same(v.teams[1], fx.game.away.name)
    reverse = matching.same(v.teams[0], fx.game.away.name) and matching.same(v.teams[1], fx.game.home.name)
    return direct or reverse


def audit_values(values: list[surebet.SurebetValue], fixtures) -> list[Audit]:
    out: list[Audit] = []
    for v in values:
        if not v.back:
            out.append(Audit(v, "LAY_REFERENZ", note="Lay-Quote wird nicht als Back-Value bestätigt"))
            continue
        side = _candidate_side(v)
        if side is None:
            out.append(Audit(v, "NO_MODEL", note="Marktart im aktuellen Fair-Modell nicht unterstützt"))
            continue
        hits = [fx for fx in fixtures if _same_event(v, fx)]
        if len(hits) != 1:
            out.append(Audit(v, "NO_MATCH", note="kein eindeutiges Modell-Spiel gefunden"))
            continue
        fx = hits[0]
        direct = matching.same(v.teams[0], fx.game.home.name)
        model_side = side
        if not direct and side in {"home", "away"}:
            model_side = "away" if side == "home" else "home"
        p = fx.probs.get(model_side)
        if p is None or p <= 0:
            out.append(Audit(v, "NO_MODEL", note="keine Modellwahrscheinlichkeit für Auswahl"))
            continue
        ref = fx.ref_probs.get(model_side)
        our_ev = p * v.odds - 1.0
        api_ev = v.ev
        if our_ev < 0:
            status = "WIDERLEGT"
        elif our_ev < 0.03:
            status = "REDUZIERT"
        else:
            status = "BESTÄTIGT"
        if ref is not None and ref > 0 and v.odds * ref - 1.0 < -0.02 and status == "BESTÄTIGT":
            status = "KONFLIKT"
        note = f"API-EV {api_ev:+.1%}" if api_ev is not None else "API-EV unbekannt"
        out.append(Audit(
            v, status,
            our_probability=p,
            our_fair=1.0 / p,
            our_ev=our_ev,
            reference_probability=ref,
            reference_fair=(1.0 / ref if ref else None),
            note=note,
        ))
    return out


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

def telegram_text(values: list[surebet.SurebetValue], error: str | None = None, audits: list[Audit] | None = None) -> str:
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

    if audits:
        out += ["", "🧪 UNSER MODELL-AUDIT"]
        rank = {"BESTÄTIGT": 0, "REDUZIERT": 1, "KONFLIKT": 2, "WIDERLEGT": 3, "LAY_REFERENZ": 4, "NO_MODEL": 5, "NO_MATCH": 6}
        for a in sorted(audits, key=lambda x: (rank.get(x.status, 9), -(x.our_ev or -99)))[:40]:
            v = a.value
            own = "–" if a.our_ev is None else _pct(a.our_ev)
            fair = _q(a.our_fair)
            ref = _q(a.reference_fair)
            side = " LAY" if not v.back else ""
            out += [
                f"• {a.status} · {_kick(v.kickoff)} · {v.tournament or 'Liga unbekannt'}",
                f"  {v.event} · {v.selection} @ {_q(v.odds)} ({v.bookmaker}{side})",
                f"  Markt: {v.market}",
                f"  unser Fair {fair} | unser EV {own} | Referenz-Fair {ref}",
                f"  {a.note}",
            ]

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
                f"  Markt: {v.market}",
                ("  " + " | ".join(calc)) if calc else "  SureBet: Value-Signal",
            ]
    out += ["", "ℹ️ Match = gleiches Event + gleiche Markt-/Auswahlstruktur. PLAY-Freigabe durch unser Modell bleibt separat."]
    return "\n".join(out)


def run(send: bool = False, limit: int = 100) -> list[str]:
    values, err = surebet.fetch_valuebets(limit=limit)
    audits: list[Audit] = []
    if not err and values:
        try:
            from . import scan
            res = scan.run(
                days=7,
                watch_days=14,
                sports=("soccer", "nhl", "hockey_eu", "nba"),
                journal=None,
            )
            audits = audit_values(values, res.fixtures)
        except Exception as exc:
            err = f"Modell-Audit fehlgeschlagen: {type(exc).__name__}: {exc}"
    txt = telegram_text(values, err, audits)
    counts = {}
    for a in audits:
        counts[a.status] = counts.get(a.status, 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else "kein Modell-Audit"
    lines = [txt, f"Gefunden: {len(values)} Bet365-Valuebets", f"Audit: {summary}"]
    if send:
        r = telegram.send(txt)
        lines.append(
            f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}"
        )
    return lines
