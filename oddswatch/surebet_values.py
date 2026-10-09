"""Bet365 Valuebet watch from the configured Valuebet API feed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
import re
from zoneinfo import ZoneInfo

from . import telegram
from . import matching
from . import period_totals
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


def _score_matrix(lh: float, la: float, max_goals: int = 14):
    ph = [math.exp(-lh) * lh**k / math.factorial(k) for k in range(max_goals + 1)]
    pa = [math.exp(-la) * la**k / math.factorial(k) for k in range(max_goals + 1)]
    rows = [(i, j, ph[i] * pa[j]) for i in range(len(ph)) for j in range(len(pa))]
    z = sum(p for _, _, p in rows)
    return [(i, j, p / z) for i, j, p in rows]


def _asian_legs(line: float) -> list[float]:
    q = round(line * 4) / 4
    if abs(q * 2 - round(q * 2)) < 1e-9:
        return [q]
    return [q - 0.25, q + 0.25]


def _fair_from_fractional_outcomes(rows, value_fn, odds: float) -> tuple[float | None, float | None, float | None]:
    win = loss = 0.0
    for item in rows:
        p = item[-1]
        vals = value_fn(item)
        vals = vals if isinstance(vals, list) else [vals]
        frac = 1.0 / len(vals)
        for v in vals:
            if v > 1e-12:
                win += p * frac
            elif v < -1e-12:
                loss += p * frac
    if win <= 0:
        return None, None, None
    fair = 1.0 + loss / win
    ev = win * (odds - 1.0) - loss
    return fair, 1.0 / fair, ev


def _poisson_market_fair(v: surebet.SurebetValue, fx) -> tuple[float | None, float | None, float | None, str]:
    xg = _expected_goals_from_detail(fx)
    if not xg:
        return None, None, None, "keine Torerwartung im Modell"
    lh, la = xg
    rows = _score_matrix(lh, la)
    code = (v.bet_type or "").strip()
    cond = None
    try:
        cond = float(v.condition)
    except (TypeError, ValueError):
        pass
    period = (v.period or "").casefold()
    full_reg = period in {"regulartime", "fulltime", "match", ""}
    if not full_reg:
        return None, None, None, "Periodenmarkt braucht eigenes Periodenmodell"

    # 1X2 / double chance / DNB.
    p1 = sum(p for h, a, p in rows if h > a)
    px = sum(p for h, a, p in rows if h == a)
    p2 = 1.0 - p1 - px
    if code in {"win1", "win2", "draw"}:
        p = {"win1": p1, "draw": px, "win2": p2}[code]
        return 1.0 / p, p, p * v.odds - 1.0, "Poisson 1X2"
    if code in {"1x", "x1", "x2", "2x", "_12", "12"}:
        p = {
            "1x": p1 + px, "x1": p1 + px,
            "x2": px + p2, "2x": px + p2,
            "_12": p1 + p2, "12": p1 + p2,
        }[code]
        return 1.0 / p, p, p * v.odds - 1.0, "Poisson Double Chance"
    if code in {"win1RetX", "win2RetX"}:
        pw, pl = (p1, p2) if code == "win1RetX" else (p2, p1)
        if pw <= 0:
            return None, None, None, "DNB nicht berechenbar"
        fair = 1.0 + pl / pw
        ev = pw * (v.odds - 1.0) - pl
        return fair, 1.0 / fair, ev, "Poisson DNB"

    # Totals and team totals, including Asian quarter lines.
    if code in {"over", "under"} and cond is not None:
        legs = _asian_legs(cond)
        base = (v.base or "overall").casefold()
        over = code == "over"
        def values(item):
            h, a, _ = item
            total = h + a
            if base in {"team1", "home", "1", "first"} or "team1" in base or "home" in base:
                total = h
            elif base in {"team2", "away", "2", "second"} or "team2" in base or "away" in base:
                total = a
            return [(total - leg) if over else (leg - total) for leg in legs]
        fair, p, ev = _fair_from_fractional_outcomes(rows, values, v.odds)
        label = "Poisson Teamtotal" if base not in {"overall", "total", "match", ""} else "Poisson Total"
        return fair, p, ev, label

    # Asian handicap, selection perspective.
    if code in {"ah1", "ah2"} and cond is not None:
        legs = _asian_legs(cond)
        home_sel = code == "ah1"
        def values(item):
            h, a, _ = item
            margin = (h - a) if home_sel else (a - h)
            return [margin + leg for leg in legs]
        fair, p, ev = _fair_from_fractional_outcomes(rows, values, v.odds)
        return fair, p, ev, "Poisson Asian Handicap"

    # European handicap: condition is applied to team 1, then 3-way result.
    if code in {"eh1", "ehx", "eh2"} and cond is not None:
        probs = {"eh1": 0.0, "ehx": 0.0, "eh2": 0.0}
        for h, a, p in rows:
            m = (h + cond) - a
            k = "eh1" if m > 0 else ("ehx" if abs(m) < 1e-12 else "eh2")
            probs[k] += p
        p = probs[code]
        return (1.0 / p, p, p * v.odds - 1.0, "Poisson Europäisches Handicap") if p > 0 else (None, None, None, "EH nicht berechenbar")

    # BTTS when the feed maps yes/no to the market.
    if code in {"yes", "no"}:
        py = sum(p for h, a, p in rows if h > 0 and a > 0)
        p = py if code == "yes" else 1.0 - py
        return 1.0 / p, p, p * v.odds - 1.0, "Poisson BTTS"

    return None, None, None, "Marktart im aktuellen Fair-Modell nicht unterstützt"


def _model_probability(v: surebet.SurebetValue, fx) -> tuple[float | None, float | None, float | None, str]:
    """Return fair odds, equivalent fair probability, EV at candidate odds, note."""
    code = (v.bet_type or "").strip()
    period = (v.period or "").casefold()

    # Hockey/NBA 2-way winner including extra time where our fixture probabilities
    # are already full-game moneyline probabilities.
    if code in {"winOnly1", "winOnly2"} or (
        code in {"win1", "win2"} and period in {"overtime", "shootout"}
    ):
        side = "home" if code in {"winOnly1", "win1"} else "away"
        direct = matching.same(v.teams[0], fx.game.home.name) if v.teams else True
        if not direct:
            side = "away" if side == "home" else "home"
        p = fx.probs.get(side)
        if p is not None and p > 0:
            return 1.0 / p, p, p * v.odds - 1.0, "2-Wege-Moneyline-Modell"

    # Soccer/hockey regulation markets come from the model's score distribution.
    if fx.sport in {"soccer", "hockey", "nhl"}:
        return _poisson_market_fair(v, fx)

    # NBA/NFL: moneyline only here; spread/total are added when exact model
    # parameters/lines are exposed by the fixture path.
    side = _candidate_side(v)
    if side in {"home", "away"}:
        direct = matching.same(v.teams[0], fx.game.home.name) if v.teams else True
        if not direct:
            side = "away" if side == "home" else "home"
        p = fx.probs.get(side)
        if p is not None and p > 0:
            return 1.0 / p, p, p * v.odds - 1.0, "Moneyline-Modell"
    return None, None, None, "Marktart im aktuellen Fair-Modell nicht unterstützt"


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

    This is independent of the Valuebet-API probability and is used only when the
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


def _period_kind(v: surebet.SurebetValue) -> str | None:
    p = (v.period or "").casefold().strip()
    m = (v.market or "").casefold()
    sport = (v.sport or "").casefold()

    if sport in {"basketball", "american football"}:
        aliases = {
            "q1": "q1", "quarter1": "q1", "p1": "q1", "period1": "q1",
            "q2": "q2", "quarter2": "q2", "p2": "q2", "period2": "q2",
            "q3": "q3", "quarter3": "q3", "p3": "q3", "period3": "q3",
            "q4": "q4", "quarter4": "q4", "p4": "q4", "period4": "q4",
            "1h": "1h", "half1": "1h",
            "2h": "2h", "half2": "2h",
        }
        if p in aliases:
            return aliases[p]
        for i in range(1, 5):
            if f"{i}. viertel" in m or f"{i}st quarter" in m or f"{i}th quarter" in m:
                return f"q{i}"
        if "1. halbzeit" in m or "1st half" in m:
            return "1h"
        if "2. halbzeit" in m or "2nd half" in m:
            return "2h"

    if sport == "hockey":
        aliases = {
            "p1": "p1", "period1": "p1",
            "p2": "p2", "period2": "p2",
            "p3": "p3", "period3": "p3",
        }
        if p in aliases:
            return aliases[p]
        for i in range(1, 4):
            if f"{i}. drittel" in m:
                return f"p{i}"

    return None


def _period_total_fair(v: surebet.SurebetValue, cache: dict):
    """Exact candidate-driven period total fair for NBA/NFL/NHL."""
    kind = _period_kind(v)
    if kind is None or (v.bet_type or "").strip() not in {"over", "under"}:
        return None

    if len(v.teams) != 2 or v.kickoff is None:
        return (None, None, None, "Periodenmarkt ohne eindeutiges Event")

    base = (v.base or "overall").casefold()
    if base not in {"overall", "total", "match", ""}:
        return (None, None, None, "Perioden-Teamtotal noch nicht freigegeben")

    try:
        line = float(v.condition)
    except (TypeError, ValueError):
        return (None, None, None, "Perioden-Total-Linie nicht erkannt")

    tournament = (v.tournament or "").casefold()
    sport = (v.sport or "").casefold()
    if sport == "basketball":
        if "nba" not in tournament:
            return (None, None, None, "Periodenmodell aktuell nur NBA")
        model_sport = "nba"
    elif sport == "american football":
        if "nfl" not in tournament:
            return (None, None, None, "Periodenmodell aktuell nur NFL")
        model_sport = "nfl"
    elif sport == "hockey":
        if "nhl" not in tournament:
            return None  # EU hockey keeps its existing period model below.
        model_sport = "nhl"
    else:
        return None

    pf, err, issues = period_totals.fair_total(
        model_sport,
        kind,
        v.teams[0],
        v.teams[1],
        v.kickoff,
        line,
        (v.bet_type or "").strip() == "over",
        cache,
    )
    if pf is None:
        note = err or "Periodenmodell nicht verfügbar"
        if issues:
            note += f"; Datenhinweise {len(issues)}"
        return (None, None, None, note)

    ev = pf.probability * v.odds - 1.0
    note = (
        f"{pf.model} · erwartetes Total {pf.expected_total:.2f} · "
        f"{pf.sample_games} historische Periodenspiele"
    )
    return pf.fair_odds, pf.probability, ev, note


def audit_values(values: list[surebet.SurebetValue], fixtures) -> list[Audit]:
    out: list[Audit] = []
    period_cache: dict = {}
    for v in values:
        if v.bookmaker != "bet365":
            continue
        if not v.back:
            out.append(Audit(v, "LAY_REFERENZ", note="Lay-Quote wird nicht als Back-Value bestätigt"))
            continue

        hits = [fx for fx in fixtures if _same_event(v, fx)]
        fair = p = our_ev = None
        model_note = ""
        ref = None

        # Exact period totals are always evaluated by their own period model,
        # never by scaling the full-game expectation.
        period_result = _period_total_fair(v, period_cache)
        if period_result is not None:
            fair, p, our_ev, model_note = period_result
        elif v.sport == "Hockey" and "1. drittel" in (v.market or "").casefold():
            # European hockey keeps its historical period-score Poisson.
            p1, model_note = _hockey_period1_probability(v, period_cache)
            if p1 is not None and p1 > 0:
                p = p1
                fair = 1.0 / p
                our_ev = p * v.odds - 1.0
        elif len(hits) == 1:
            fx = hits[0]
            fair, p, our_ev, model_note = _model_probability(v, fx)
            side = _candidate_side(v)
            if side is not None:
                direct = matching.same(v.teams[0], fx.game.home.name) if v.teams else True
                model_side = side
                if not direct and side in {"home", "away"}:
                    model_side = "away" if side == "home" else "home"
                ref = fx.ref_probs.get(model_side)
        elif v.sport == "Hockey":
            p1, model_note = _hockey_period1_probability(v, period_cache)
            if p1 is not None and p1 > 0:
                p = p1
                fair = 1.0 / p
                our_ev = p * v.odds - 1.0
        else:
            out.append(Audit(v, "NO_MATCH", note="kein eindeutiges Modell-Spiel gefunden"))
            continue

        if fair is None or p is None or our_ev is None:
            is_period = _period_kind(v) is not None
            status = "NO_MODEL" if is_period or hits else "NO_MATCH"
            out.append(Audit(v, status, note=model_note or "keine Modellwahrscheinlichkeit für exakten Markt"))
            continue

        api_ev = v.ev
        if our_ev < 0:
            status = "WIDERLEGT"
        elif our_ev < 0.03:
            status = "REDUZIERT"
        else:
            status = "BESTÄTIGT"

        if ref is not None and ref > 0 and v.odds * ref - 1.0 < -0.02 and status == "BESTÄTIGT":
            status = "KONFLIKT"

        api = f"Valuebet-EV {api_ev:+.1%}" if api_ev is not None else "Valuebet-EV unbekannt"
        note = f"{model_note}; {api}" if model_note else api
        out.append(Audit(
            v, status,
            our_probability=p,
            our_fair=fair,
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
                f"Valuebet-EV: {api} · Referenz-Fair: {ref}",
            ]

    lay = [a for a in audits if a.status == "LAY_REFERENZ"]
    no_model = [a for a in audits if a.status == "NO_MODEL"]
    if lay or no_model:
        out += ["", "📋 NOCH NICHT ALS PLAY BEWERTET"]
        if lay:
            out.append(f"↔️ {len(lay)} Lay-Signale: nur Markt-Referenz, kein Back-Value.")
        if no_model:
            out.append(f"⚪ {len(no_model)} Märkte ohne passenden Fair-Preis im aktuellen Modell.")

    # Never present an unverified feed item as "value". Only unresolved Bet365
    # candidates are shown here, explicitly marked as NOT checked.
    unresolved = [a for a in audits if a.status == "NO_MODEL"]
    if unresolved:
        out += ["", "❔ BET365-KANDIDATEN · NOCH NICHT GEPRÜFT"]
        for a in unresolved[:10]:
            v = a.value
            out += [
                f"• {_kick(v.kickoff)} · {v.tournament or 'Liga unbekannt'}",
                f"  {v.event}",
                f"  ➡️ {v.selection} @ {_q(v.odds)}",
                f"  {v.market}",
                f"  Status: {a.status} · {a.note}",
            ]

    books = {}
    for v in values:
        key = names.get(v.bookmaker, v.bookmaker)
        books[key] = books.get(key, 0) + 1
    book_summary = " · ".join(f"{k} {n}" for k, n in sorted(books.items()))
    out += [
        "",
        f"📊 Feed: {len(values)} Signale · {book_summary}",
        "ℹ️ Valuebet-API entdeckt nur Kandidaten. Als VALUE gilt hier erst, was unser unabhängiges Modell für den exakten Markt bestätigt.",
    ]
    return "\n".join(out)


def _fetch_candidate_values(limit: int = 100):
    core_values, core_err = surebet.fetch_valuebets(
        sports=("Football", "Hockey", "Basketball"),
        books=("bet365",),
        limit=limit,
    )
    nfl_values, nfl_err = surebet.fetch_valuebets(
        sports=("American football",),
        books=("bet365",),
        limit=limit,
    )
    values = core_values + nfl_values

    seen = set()
    unique = []
    for v in values:
        key = (v.id, v.sport, v.teams, v.selection, v.market, v.bookmaker, round(v.odds, 6))
        if key in seen:
            continue
        seen.add(key)
        unique.append(v)
    values = [v for v in unique if v.bookmaker == "bet365" and v.back]

    warnings = []
    if core_err:
        warnings.append(f"Core-Feed: {core_err}")
    if nfl_err:
        warnings.append(f"NFL-Feed: {nfl_err}")
    err = "; ".join(warnings) if not values and warnings else None
    return values, warnings, err


def run(send: bool = False, limit: int = 100) -> list[str]:
    # 1) Candidate-first. NFL is isolated from the core feed so an NFL-only
    # provider error cannot suppress Football/Hockey/Basketball.
    values, feed_warnings, err = _fetch_candidate_values(limit)

    audits: list[Audit] = []
    if values:
        try:
            from . import scan

            # 2) Run only the model families needed by the ingested candidates.
            sports_needed: list[str] = []
            if any(v.sport == "Football" for v in values):
                sports_needed.append("soccer")
            if any(v.sport == "Hockey" for v in values):
                sports_needed.extend(["nhl", "hockey_eu"])
            if any(v.sport == "Basketball" for v in values):
                # NBA model is available in the shared scanner. European
                # basketball candidates remain NO_MODEL until their own model
                # has a fair price for the exact market.
                sports_needed.append("nba")
            if any(v.sport == "American football" for v in values):
                sports_needed.append("nfl")

            # Candidate horizon instead of an unconditional broad scan.
            now = datetime.now(_TZ)
            future = [v.kickoff.astimezone(_TZ) for v in values if v.kickoff and v.kickoff > now]
            max_days = 1
            if future:
                max_days = max(1, min(14, max((dt.date() - now.date()).days + 1 for dt in future)))

            res = scan.run(
                days=max_days,
                watch_days=max_days,
                sports=tuple(dict.fromkeys(sports_needed)),
                journal=None,
            )

            # 3) Challenge every candidate against our independent fair model.
            audits = audit_values(values, res.fixtures)
            try:
                from .sql.valuebet import persist_audits
                sql_status = persist_audits(audits, res.fixtures)
            except Exception as exc:
                sql_status = {"error": f"{type(exc).__name__}: {exc}"}
        except Exception as exc:
            err = f"Modell-Audit fehlgeschlagen: {type(exc).__name__}: {exc}"

    # 4) Telegram reports the result of our audit, never the raw feed as VALUE.
    sql_status = locals().get("sql_status", {})
    txt = telegram_text(values, err, audits)
    counts = {}
    for a in audits:
        counts[a.status] = counts.get(a.status, 0) + 1
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) if counts else "kein Modell-Audit"
    lines = [
        txt,
        f"Eingelesene Bet365-Kandidaten: {len(values)}",
        f"Audit: {summary}",
    ]
    if feed_warnings:
        lines.append("Feed-Hinweise: " + " | ".join(feed_warnings))
    if sql_status:
        lines.append("CLV-Tracking: " + ", ".join(f"{k}={v}" for k, v in sql_status.items()))
    if send and values:
        r = telegram.send(txt)
        lines.append(
            f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}"
        )
    elif send and not values:
        lines.append("Telegram: keine Kandidaten – nichts gesendet")
    return lines


def run_clv_snapshot() -> list[str]:
    """Lightweight quote snapshot + sampled CLV close; no model scan."""
    values, err = surebet.fetch_valuebets(books=("bet365",), limit=500)
    if err:
        return [f"Valuebet-CLV: {err}"]
    values = [v for v in values if v.bookmaker == "bet365" and v.back]
    try:
        from .sql.valuebet import snapshot_open_candidates, capture_sampled_clv
        snap = snapshot_open_candidates(values)
        close = capture_sampled_clv()
        return [
            f"Valuebet-CLV Snapshot: {snap}",
            f"Valuebet-CLV Close: closed={len(close['closed'])}, NO_CLOSE={close['no_close']}",
        ]
    except Exception as exc:
        return [f"Valuebet-CLV Fehler: {type(exc).__name__}: {exc}"]
