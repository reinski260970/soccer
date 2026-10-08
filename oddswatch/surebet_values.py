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
    """Map only plain win markets to model sides.

    Market descriptions are human-readable, so use both market type and selection.
    Handicaps, DNB and totals stay NO_MODEL until their own fair models exist.
    """
    m = (v.market or "").casefold()
    s = (v.selection or "").casefold()
    if any(x in m for x in ("handicap", "draw no bet", "gesamt-", "teamtotal")):
        return None
    if "unentschieden" in s:
        return "draw"
    if len(v.teams) >= 1 and matching.same(v.selection.replace(" Sieg", "").replace(" (2-Wege)", ""), v.teams[0]):
        return "home"
    if len(v.teams) >= 2 and matching.same(v.selection.replace(" Sieg", "").replace(" (2-Wege)", ""), v.teams[1]):
        return "away"
    if len(v.teams) >= 1 and v.teams[0].casefold() in s and "sieg" in s:
        return "home"
    if len(v.teams) >= 2 and v.teams[1].casefold() in s and "sieg" in s:
        return "away"
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
    out = [f"🎯 VALUE-AUDIT · {now}"]
    if error:
        return "\n".join(out + [f"⚠️ {error}"])
    if not values:
        return "\n".join(out + ["Keine Value-Signale für Fußball, Hockey oder Basketball."])

    names = {"bet365": "Bet365", "betfair": "Betfair", "orbitxch": "OrbitX"}
    audits = audits or []
    rank = {"BESTÄTIGT": 0, "REDUZIERT": 1, "KONFLIKT": 2, "WIDERLEGT": 3}
    icons = {"BESTÄTIGT": "✅", "REDUZIERT": "🟡", "KONFLIKT": "⚠️", "WIDERLEGT": "❌"}

    actionable = [a for a in audits if a.status in rank and a.value.back]
    actionable.sort(key=lambda a: (rank[a.status], -(a.our_ev if a.our_ev is not None else -99)))

    if actionable:
        out += ["", "🧪 VON UNSEREM MODELL GEPRÜFT"]
        for a in actionable[:20]:
            v = a.value
            own = _pct(a.our_ev)
            fair = _q(a.our_fair)
            ref = _q(a.reference_fair)
            api = _pct(v.ev)
            out += [
                "",
                f"{icons[a.status]} {a.status} · {_kick(v.kickoff)} · {v.tournament or 'Liga unbekannt'}",
                f"{v.event}",
                f"➡️ {v.selection} @ {_q(v.odds)} · {names.get(v.bookmaker, v.bookmaker)}",
                f"Markt: {v.market}",
                f"Unser Fair: {fair} · Unser EV: {own}",
                f"SureBet-EV: {api} · Referenz-Fair: {ref}",
            ]

    lay = [a for a in audits if a.status == "LAY_REFERENZ"]
    no_model = [a for a in audits if a.status == "NO_MODEL"]
    no_match = [a for a in audits if a.status == "NO_MATCH"]
    if lay or no_model or no_match:
        out += ["", "📋 NOCH NICHT ALS PLAY BEWERTET"]
        if lay:
            out.append(f"↔️ {len(lay)} Lay-Signale: nur Markt-Referenz, kein Back-Value.")
        if no_model:
            out.append(f"⚪ {len(no_model)} Märkte ohne passenden Fair-Preis im aktuellen Modell.")
        if no_match:
            out.append(f"🔎 {len(no_match)} Events noch nicht eindeutig unserem Spiel zugeordnet.")

    # Show genuine Bet365 candidates compactly, because these are the prices the
    # user ultimately wants to challenge with the independent model.
    bet365 = [v for v in values if v.bookmaker == "bet365" and v.back]
    if bet365:
        out += ["", "🏷️ BET365-KANDIDATEN"]
        for v in bet365[:20]:
            out += [
                f"• {_kick(v.kickoff)} · {v.tournament or 'Liga unbekannt'}",
                f"  {v.event}",
                f"  ➡️ {v.selection} @ {_q(v.odds)}",
                f"  {v.market} · SureBet-EV {_pct(v.ev)}",
            ]

    books = {}
    for v in values:
        key = names.get(v.bookmaker, v.bookmaker)
        books[key] = books.get(key, 0) + 1
    book_summary = " · ".join(f"{k} {n}" for k, n in sorted(books.items()))
    out += [
        "",
        f"📊 Feed: {len(values)} Signale · {book_summary}",
        "ℹ️ SureBet entdeckt Kandidaten. PLAY gibt es nur, wenn unser unabhängiges Modell den Markt bestätigt.",
    ]
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
    lines = [txt, f"Gefunden: {len(values)} Value-Signale", f"Audit: {summary}"]
    if send:
        r = telegram.send(txt)
        lines.append(
            f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}"
        )
    return lines
