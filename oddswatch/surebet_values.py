"""Bet365 Valuebet watch from SureBet API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
import re
from zoneinfo import ZoneInfo

from . import telegram
from . import matching
from .sources import hockeyarchives, surebet
from .models.poisson import Match, PoissonModel, hockey_regulation_to_moneyline

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


def _expected_goals_from_detail(fx) -> tuple[float, float] | None:
    m = re.search(r"erw\. Tore\s+([0-9]+(?:\.[0-9]+)?):([0-9]+(?:\.[0-9]+)?)", fx.detail or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


def _poisson_total_probability(lam: float, line: float, over: bool) -> float | None:
    # Only half-goal lines have binary settlement and can be compared directly
    # with decimal odds without push handling.
    if abs((line * 2) - round(line * 2)) > 1e-9 or int(round(line * 2)) % 2 == 0:
        return None
    k = math.floor(line)
    under_or_equal = sum(math.exp(-lam) * lam**i / math.factorial(i) for i in range(k + 1))
    return 1.0 - under_or_equal if over else under_or_equal


def _model_probability(v: surebet.SurebetValue, fx) -> tuple[float | None, str]:
    """Independent fair probability for the exact SureBet market when supported."""
    market = (v.market or "").casefold()
    selection = (v.selection or "").casefold()

    # Plain winner / draw.
    side = _candidate_side(v)
    if side is not None:
        direct = matching.same(v.teams[0], fx.game.home.name) if v.teams else True
        model_side = side
        if not direct and side in {"home", "away"}:
            model_side = "away" if side == "home" else "home"
        p = fx.probs.get(model_side)
        return (p, "1X2/ML") if p is not None else (None, "keine Modellwahrscheinlichkeit")

    # Draw-no-bet can be derived exactly from 1X2 probabilities.
    if "draw no bet" in market and len(v.teams) >= 2:
        if "dnb" not in selection:
            return None, "DNB-Auswahl nicht erkannt"
        target = "home" if v.teams[0].casefold() in selection else (
            "away" if v.teams[1].casefold() in selection else None
        )
        if target and all(k in fx.probs for k in ("home", "draw", "away")):
            denom = fx.probs["home"] + fx.probs["away"]
            if denom > 0:
                return fx.probs[target] / denom, "DNB aus 1X2-Modell"
        return None, "DNB nicht sauber ableitbar"

    # Regulation full-game soccer/hockey goal totals from our Poisson expected goals.
    if "gesamt-tore" in market and "reguläre spielzeit" in market:
        mm = re.search(r"(über|unter)\s+([0-9]+(?:\.[0-9]+)?)", selection)
        xg = _expected_goals_from_detail(fx)
        if not mm or not xg:
            return None, "Tor-Total nicht sauber ableitbar"
        p = _poisson_total_probability(xg[0] + xg[1], float(mm.group(2)), mm.group(1) == "über")
        return (p, "Poisson-Gesamttore") if p is not None else (None, "Push-Linie noch nicht unterstützt")

    return None, "Marktart im aktuellen Fair-Modell nicht unterstützt"


_HOCKEY_TOURNAMENTS = {
    "czechia extraliga": "extraliga",
    "czech extraliga": "extraliga",
    "finland liiga": "liiga",
    "liiga": "liiga",
    "sweden shl": "shl",
    "shl": "shl",
    "ice hockey league": "icehl",
    "austria ice hockey league": "icehl",
    "khl": "khl",
}


def _hockey_league(v: surebet.SurebetValue) -> str | None:
    t = (v.tournament or "").casefold().strip()
    for label, code in _HOCKEY_TOURNAMENTS.items():
        if label in t:
            return code
    return None


def _hockey_period1_probability(v: surebet.SurebetValue, cache: dict) -> tuple[float | None, str]:
    """Candidate-driven 1st-period total model from historical period scores.

    This is independent of the SureBet probability and is used only when the
    exact event is not available in the normal scanner.
    """
    if v.sport != "Hockey" or len(v.teams) != 2 or v.kickoff is None:
        return None, "kein Hockey-Periodenmodell"
    market = (v.market or "").casefold()
    selection = (v.selection or "").casefold()
    if "1. drittel" not in market or "gesamt-tore" not in market:
        return None, "kein unterstützter Periodenmarkt"
    mm = re.search(r"(über|unter)\s+([0-9]+(?:\.[0-9]+)?)", selection)
    if not mm:
        return None, "Drittel-Total nicht erkannt"
    league = _hockey_league(v)
    if not league:
        return None, "Liga noch nicht im Drittelmodell"
    season = v.kickoff.year if v.kickoff.month >= 7 else v.kickoff.year - 1
    key = (league, season)
    if key not in cache:
        rows = []
        for sy, age in ((season - 1, 30.0), (season, 0.25)):
            rs, err = hockeyarchives.season_results(league, sy, age)
            if err and sy == season:
                continue
            rows += rs
        p1 = [
            Match(r.date, r.home, r.away, r.periods[0][0], r.periods[0][1])
            for r in rows if len(r.periods) >= 1
        ]
        if len(p1) < 120:
            cache[key] = (None, p1)
        else:
            cache[key] = (
                PoissonModel.fit(p1, v.kickoff.date(), half_life_days=240,
                                 xg_weight=0.0, shrink=8.0, rho=0.0, max_goals=7),
                p1,
            )
    model, rows = cache[key]
    if model is None:
        return None, f"zu wenig Dritteldaten ({len(rows)})"
    names = list(model.attack)
    home = matching.find_strict(v.teams[0], names) or matching.find(v.teams[0], names)
    away = matching.find_strict(v.teams[1], names) or matching.find(v.teams[1], names)
    if not home or not away:
        return None, "Teams im Drittelmodell nicht eindeutig"
    mk = model.markets(home, away)
    line = float(mm.group(2))
    keym = ("O" if mm.group(1) == "über" else "U") + str(line)
    if keym not in mk:
        return None, "Drittel-Linie nicht unterstützt"
    return float(mk[keym]), f"1.-Drittel-Poisson ({len(rows)} Spiele)"


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
