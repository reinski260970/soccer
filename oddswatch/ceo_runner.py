"""CEO-Matchday-Report: frischer Scan + News + CLV, optional direkt zu Telegram.

Nutzt ausschließlich die bereits vorhandenen Umgebungsvariablen
TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID. Marktpreise bleiben vom Modell
getrennt; der Report veröffentlicht nur die von scan.run() freigegebenen PLAYs
und kennzeichnet WATCH ausdrücklich als nicht freigegeben.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import news, outlook, report, scan, settle, telegram, surebet_values
from .sources import surebet
from .journal import Journal


def _f(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _watchlist(res) -> list:
    picked = {(c.event, c.market) for c in res.picks}
    return sorted(
        [
            c
            for c in res.candidates
            if (c.event, c.market) not in picked
            and c.ev >= 0.0
            and c.edge > 0
            and c.p_ref is not None
        ],
        key=lambda c: -c.ev,
    )[:5]


def _news_lines(alerts: list, article_count: int) -> list[str]:
    out = ["📰 CEO NEWS"]
    if not alerts:
        out.append(f"Keine neuen materiellen Meldungen ({article_count} Artikel geprüft).")
        return out
    severe = sum(bool(a.severe) for a in alerts)
    out.append(f"{len(alerts)} neu · HIGH {severe} · MEDIUM {len(alerts) - severe}")
    for a in alerts[:5]:
        verified = "VERIFIED" if a.confirmed_by else "UNVERIFIED"
        materiality = "HIGH" if a.severe else "MEDIUM"
        recalc = "JA" if a.severe and a.confirmed_by else "NEIN"
        out.append(
            f"• {a.target.event} · {a.category} · {a.team} · "
            f"{verified} · {materiality} · FAIR RECALC: {recalc}"
        )
    return out


def _portfolio_line(rows: list[dict], label: str) -> str:
    done = [
        r for r in rows
        if r.get("result") and r.get("result") not in ("void", "withdrawn")
    ]
    stake = sum(_f(r.get("stake_eh")) for r in done)
    pnl = sum(_f(r.get("pnl_eh")) for r in done)
    clv = [_f(r.get("clv")) for r in done if r.get("clv") not in (None, "")]
    roi = pnl / stake if stake else None
    clv_txt = f"{sum(clv) / len(clv) * 100:+.1f}% (n={len(clv)})" if clv else "–"
    roi_txt = f"{roi * 100:+.1f}%" if roi is not None else "–"
    return f"{label}: ROI {roi_txt} · Ø CLV {clv_txt} · {len(done)} abgerechnet"


def _clv_lines(j: Journal) -> list[str]:
    out = [
        "📈 CLV / PERFORMANCE",
        _portfolio_line(j.read("valuebets"), "Modell-Freigaben"),
        _portfolio_line(j.read("placed"), "Gespielt"),
        "CLV ist Freigabemaßstab; kurzfristiger ROI überstimmt schwachen CLV nicht.",
    ]
    try:
        from . import sql_store
        shadow = sql_store.shadow_summary("soccer")
    except Exception:
        shadow = []
    if shadow:
        out.append("🔬 FORWARD-SHADOW FUSSBALL · latest pre-kickoff")
        for r in sorted(shadow, key=lambda x: (-x["events"], x["league"]))[:6]:
            market = r.get("market_logloss")
            if market is None:
                cmp = "Marktreferenz –"
            else:
                gain = r["gain_vs_market"]
                cmp = f"Markt LL {market:.4f} · Δ {gain:+.4f}"
            out.append(
                f"{r['league']} · {r['model']} · n={r['events']} · "
                f"Modell LL {r['model_logloss']:.4f} · {cmp}"
            )
        out.append("Shadow ist Evaluation, kein PLAY-Gate ohne ausreichende Forward-Stichprobe.")
    return out


def _sport_name(fx) -> str:
    if fx.league == "nhl":
        return "NHL"
    if fx.league == "nfl":
        return "NFL"
    if fx.league == "nba":
        return "NBA"
    if fx.sport == "hockey":
        return "Eishockey Europa"
    return "Fußball"


def _best_quote(fx, side: str):
    quotes = (getattr(fx, "market_quotes", None) or {}).get(side, [])
    if not quotes:
        return None
    # Für Vergleich immer die beste aktuell beobachtete Dezimalquote ausweisen.
    return max(quotes, key=lambda q: q.odds)


def _market_quote_text(fx) -> str:
    labels = (("home", "1"), ("draw", "X"), ("away", "2"))
    parts = []
    for side, label in labels:
        q = _best_quote(fx, side)
        if q:
            kind = "E" if getattr(q, "executable", True) else "R"
            parts.append(f"{label} {q.odds:.2f} {q.source}[{kind}]")
    return " | ".join(parts)


def _today_lines(res, hours: int = 36) -> list[str]:
    now = datetime.now(timezone.utc)
    until = now + timedelta(hours=hours)
    fx = sorted(
        [f for f in res.fixtures if now < f.game.kickoff <= until],
        key=lambda f: f.game.kickoff,
    )
    out = [f"🗓 TODAY / NEXT {hours}H"]
    if not fx:
        return out + ["Keine bewerteten Spiele im Zeitfenster."]
    groups: dict[str, list] = {}
    for f in fx:
        groups.setdefault(_sport_name(f), []).append(f)
    order = ("Fußball", "Eishockey Europa", "NHL", "NFL", "NBA")
    for name in order:
        rows = groups.get(name) or []
        if not rows:
            continue
        out.append(f"{name}: {len(rows)} Spiele")
        for f in rows[:4]:
            market = _market_quote_text(f)
            suffix = f" · Markt {market}" if market else " · NO_PRICE"
            if f.offers:
                suffix += " · ausführbar"
            out.append(
                f"• {report._league(f.league)} · {report._kick(f.game.kickoff.isoformat())} · "
                f"{f.game.title}{suffix}"
            )
        if len(rows) > 4:
            out.append(f"  + {len(rows) - 4} weitere")
    return out


def _market_diag_lines(res) -> list[str]:
    """Modell gegen vorhandene No-Vig-Marktreferenz, auch wenn kein ausführbarer
    Orbit/bet365-Preis vorhanden ist. Nie als PLAY kennzeichnen."""
    rows = []
    for f in res.fixtures:
        if f.offers or not f.ref_probs or f.sport == "soccer":
            continue
        # Kein "Value-Signal" ausgeben, solange das Modell einen materiellen
        # Kader-/QB-Vorbehalt trägt. Erst Fair neu rechnen, dann Marktvergleich.
        if any(f.flags.get(side) for side in f.flags):
            continue
        best = None
        for side, pm in f.probs.items():
            pr = f.ref_probs.get(side)
            if not pr or pm <= 0 or pr <= 0:
                continue
            d = pm - pr
            if best is None or d > best[0]:
                best = (d, side, pm, pr)
        if best is not None:
            rows.append((best[0], f, *best[1:]))
    rows.sort(key=lambda x: -x[0])
    out = ["📐 MODELL ↔ MARKTREFERENZ (kein PLAY ohne ausführbaren Preis)"]
    if not rows:
        return out + ["Keine verwertbare unabhängige Marktreferenz."]
    used: dict[str, int] = {}
    shown = 0
    for d, f, side, pm, pr in rows:
        name = _sport_name(f)
        if used.get(name, 0) >= 2:
            continue
        used[name] = used.get(name, 0) + 1
        shown += 1
        selection = f.game.home.name if side == "home" else f.game.away.name
        q = _best_quote(f, side)
        qtxt = (f" · Marktquote {q.odds:.2f} ({q.source}, "
                f"{'ausführbar' if getattr(q, 'executable', True) else 'Referenz'})") if q else ""
        out += [
            f"• {name} · {f.game.title} · {selection}",
            f"  Modell {pm * 100:.1f}% (fair {1/pm:.2f}) · Markt-No-Vig {pr * 100:.1f}% "
            f"(fair {1/pr:.2f}) · Δ {d * 100:+.1f} pp{qtxt}",
            f"  {f.detail}",
        ]
        if shown >= 6:
            break
    return out


def _soccer_steam_lines(res) -> list[str]:
    state = getattr(res, "steam_state", {}) or {}
    rows = []
    for c in res.candidates:
        if c.league in {"nfl", "nhl", "nba", "del", "icehl", "liiga", "shl", "nl", "khl"}:
            continue
        if c.ev < 0 or c.edge <= 0:
            continue
        s = state.get((c.event, c.market))
        if not s:
            continue
        rows.append((c.ev, c, s))
    rows.sort(key=lambda x: -x[0])

    out = ["⚡ SOCCER STEAM / CLV-GATE"]
    if not rows:
        return out + ["Noch kein verwertbarer Pinnacle/Bet365/Betfair-Snapshot für positive Kandidaten."]

    for _, c, s in rows[:8]:
        sig = s.get("signal")
        if sig:
            if sig.get("direction") == "SHORTENING":
                steam_txt = (
                    f"🟢 STEAM+ · Pinnacle {sig.get('lead_move',0)*100:+.1f}pp/"
                    f"{sig.get('minutes',0)}m · Lead-vs-Slow {sig.get('lag',0)*100:+.1f}pp"
                )
            else:
                steam_txt = (
                    f"🔴 STEAM− · Pinnacle {sig.get('lead_move',0)*100:+.1f}pp/"
                    f"{sig.get('minutes',0)}m · Lead-vs-Slow {sig.get('lag',0)*100:+.1f}pp"
                )
        else:
            gap = float(s.get("gap") or 0.0)
            if gap >= 0.008:
                steam_txt = f"🟡 SHARP GAP+ {gap*100:+.1f}pp · noch kein bestätigter Steam"
            elif gap <= -0.008:
                steam_txt = f"🟠 SHARP GAP− {gap*100:+.1f}pp · noch kein bestätigter Steam"
            else:
                steam_txt = "⚪ NEUTRAL · noch kein bestätigter Steam"

        model_fair = (1.0 / c.p_model) if c.p_model else None
        sharp_fair = s.get("sharp_fair")
        best_odds = s.get("best_odds")
        clv = s.get("clv_to_sharp")
        out += [
            f"• {report._league(c.league)} · {c.event}",
            f"  {c.selection} · Modell fair {model_fair:.2f} · Markt {best_odds:.2f} ({s.get('best_source')})",
            f"  Pinnacle no-vig {sharp_fair:.2f} · CLV-Ziel {clv*100:+.1f}% · EV {c.ev*100:+.1f}%",
            f"  {steam_txt}",
        ]
    out.append("PLAY-Regel: Fair-Edge + positiver CLV-Case; bestätigter STEAM− blockiert die Freigabe.")
    return out


def _euro_hockey_fair_lines(res) -> list[str]:
    now = datetime.now(timezone.utc)
    rows = [f for f in res.fixtures if f.sport == "hockey" and f.game.kickoff > now]
    rows.sort(key=lambda f: (not bool(getattr(f, "market_quotes", None)), f.game.kickoff))
    out = ["🏒 EURO-HOCKEY · FAIR vs MARKT"]
    if not rows:
        return out + ["Keine modellierten europäischen Hockeyspiele."]
    shown = 0
    no_price = 0
    for f in rows:
        ph, pa = f.probs.get("home"), f.probs.get("away")
        if not ph or not pa:
            continue
        market = _market_quote_text(f)
        if not market:
            no_price += 1
            continue
        out += [
            f"• {report._league(f.league)} · {report._kick(f.game.kickoff.isoformat())} · {f.game.title}",
            f"  FAIR: {f.game.home.name} {1/ph:.2f} / {f.game.away.name} {1/pa:.2f}",
            f"  MARKT: {market} · {f.detail}",
        ]
        shown += 1
        if shown >= 6:
            break
    if not shown:
        out.append("NO_PRICE: Für die anstehenden europäischen Hockeyspiele wurde noch keine aktuelle Marktquote gefunden.")
    elif no_price:
        out.append(f"Zusätzlich {no_price} Spiel(e) ohne aktuellen Marktpreis → keine Vergleichs-/PLAY-Freigabe.")
    out.append("Regel: Kein Fair-only Tipp. PLAY nur mit aktuellem, als ausführbar markiertem Marktpreis.")
    return out

def _surebet_value_lines(fixtures: list) -> list[str]:
    """Candidate-first independent model audit. Raw API EV is never a PLAY."""
    now = datetime.now(timezone.utc)
    values, err = surebet.fetch_valuebets(
        sports=("Football", "Hockey", "Basketball"),
        books=("bet365", "betfair", "orbitxch"),
        limit=100,
    )
    out = ["💰 VALUEBET-API · EIGENE MODELLPRÜFUNG"]
    if err:
        return out + [f"Feed nicht verfügbar: {err}"]
    if not values:
        return out + ["Keine aktuellen Valuebet-API-Kandidaten."]

    backs = [v for v in values if v.bookmaker == "bet365" and v.back
             and v.kickoff is not None and v.kickoff > now]
    try:
        audits = surebet_values.audit_values(backs, fixtures)
    except Exception as exc:
        return out + [f"Audit nicht möglich: {type(exc).__name__}: {exc}",
                      "Keine PLAY-Freigabe."]
    counts: dict[str, int] = {}
    for audit in audits:
        counts[audit.status] = counts.get(audit.status, 0) + 1
    out.append(
        f"API-Kandidaten {len(values)} · Bet365 BACK vor Anstoß {len(backs)} · "
        + (", ".join(f"{key} {n}" for key, n in sorted(counts.items())) or "kein Modell-Audit")
    )
    checked = [
        a for a in audits
        if a.status in {"BESTÄTIGT", "REDUZIERT", "WIDERLEGT", "KONFLIKT"}
        and a.our_ev is not None
    ]
    checked.sort(key=lambda a: -(a.our_ev or -1))
    for a in checked[:6]:
        v = a.value
        when = v.kickoff.astimezone(report._TZ).strftime("%d.%m. %H:%M")
        fair = f"{a.our_fair:.2f}" if a.our_fair else "–"
        out += [
            f"• {v.sport} · {when} · {v.event}",
            f"  {v.selection} · {v.market} · Bet365 @ {v.odds:.2f} (API-Referenz)",
            f"  Eigenes Modell fair {fair} · EV {a.our_ev*100:+.1f}% · "
            f"Audit {a.status} · {'WATCH' if a.our_ev > 0 else 'PASS'}, nie automatisch PLAY",
        ]
    if not checked:
        out.append("Kein Kandidat mit eindeutiger eigenständiger Modellbewertung.")
    out.append(
        "API-/Modellprüfung ist keine OOS-/CLV-Freigabe. "
        "Kein PLAY ohne validierte Modellqualität, Preis und exakten Markt."
    )
    return out

def _broad_news_lines(issues: list[str]) -> list[str]:
    """Breiter Sports-Intelligence-Scan zusätzlich zu PLAY/WATCH-spezifischen
    Alerts. Ein einzelner Feed-Treffer ist nur HEADLINE und löst keinen Recalc aus."""
    now = datetime.now(timezone.utc)
    items = news.collect(set(news.SOURCES), issues)
    rows = []
    for item in items:
        cls = news.classify(item.title, item.text)
        if not cls:
            continue
        if item.published and item.published < now - timedelta(hours=24):
            continue
        rows.append((cls[1], item.published or now, cls[0], item))
    rows.sort(key=lambda x: (not x[0], -x[1].timestamp()))
    out = ["🌐 SPORTS-INTELLIGENCE HEADLINES (24h)"]
    if not rows:
        return out + ["Keine neuen materiellen Headlines aus den angebundenen Feeds."]
    for severe, _, category, item in rows[:6]:
        out.append(
            f"• {'HIGH' if severe else 'MEDIUM'} · {report._league(item.league)} · "
            f"{category} · {item.title} ({item.source}) · SOURCE_ONLY"
        )
    out.append("SOURCE_ONLY verändert Fair Odds nicht; Recalc erst nach Bestätigung/Team-Zuordnung.")
    return out


def build_report(
    sports: tuple[str, ...] = ("soccer", "nfl", "nhl", "nba", "hockey_eu"),
) -> tuple[str, list, Journal]:
    j = Journal()

    # Erst offene Tipps abrechnen; Settlement-Fehler sollen den frischen Scan
    # nicht verhindern und werden über dessen bestehende Ausgabe sichtbar.
    try:
        list(settle.settle_all(j))
    except Exception as exc:  # Netzwerk-/Quellenfehler: Report trotzdem erzeugen.
        settlement_issue = f"Settlement: {exc}"
    else:
        settlement_issue = ""

    res = scan.run(sports=sports, journal=j)
    watch = _watchlist(res)

    # Der News-Agent bekommt immer die Targets dieses frischen CEO-Scans.
    news.save_targets(res.fixtures, res.picks, watch)
    alerts, news_issues, article_count = news.run(j)
    broad_news_issues: list[str] = []
    broad_news = _broad_news_lines(broad_news_issues)

    rows = outlook.build(res.fixtures, res.candidates, res.picks)
    note = outlook.soccer_note(res.notes, res.issues)
    outlook_lines = outlook.telegram_lines(rows, notes=note)

    core = report.telegram_text(
        res.stand,
        res.picks,
        watch,
        outlook=outlook_lines,
    ).splitlines()
    # Eigene eindeutige CEO-Überschrift statt der internen Report-Überschrift.
    if core and core[0].startswith("📊 CEO"):
        core = core[1:]

    lines = [f"📊 CEO MATCHDAY REPORT · {res.stand}", ""]
    lines += _news_lines(alerts, article_count)
    lines += [""] + broad_news
    lines += [""] + _today_lines(res)
    lines += [""] + core
    lines += [""] + _market_diag_lines(res)
    lines += [""] + _soccer_steam_lines(res)
    lines += [""] + _surebet_value_lines(res.fixtures)
    lines += [""] + _euro_hockey_fair_lines(res)
    lines += [""] + _clv_lines(j)

    # Technische Quellen-, Mapping- und Parserfehler bleiben intern und werden
    # nicht im CEO-/Telegram-Bericht ausgespielt.
    _internal_issues = list(dict.fromkeys(
        list(res.issues) + list(news_issues) + broad_news_issues
        + ([settlement_issue] if settlement_issue else [])
    ))

    if not res.picks:
        lines += ["", "CEO: kein freigegebener Tipp, 0 EH."]

    return "\n".join(lines).strip() + "\n", alerts, j


def run(
    *,
    send: bool = False,
    slot: str | None = None,
    sports: tuple[str, ...] = ("soccer", "nfl", "nhl", "nba", "hockey_eu"),
) -> int:
    text, alerts, j = build_report(sports=sports)

    out = Path("reports")
    out.mkdir(exist_ok=True)
    suffix = slot or report.stand().replace(" ", "_").replace(":", "")
    path = out / f"{date.today():%Y-%m-%d}-ceo-{suffix}.txt"
    path.write_text(text, encoding="utf-8")

    print("--- CEO / Telegram ---")
    print(text)
    if not send:
        return 0

    result = telegram.send(text)
    if not result["sent"]:
        print(f"Telegram: NICHT gesendet – {result['error']}")
        return 2

    # Erst nach bestätigtem Telegram-Versand gelten News als gemeldet.
    if alerts:
        news.mark_seen(alerts, j)
    print(f"Telegram: gesendet, message_id {result['message_ids']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m oddswatch.ceo_runner")
    p.add_argument("--send", action="store_true")
    p.add_argument("--slot", default="")
    p.add_argument("--sports", default="soccer,nfl,nhl,nba,hockey_eu")
    a = p.parse_args(argv)
    return run(
        send=a.send,
        slot=a.slot or None,
        sports=tuple(s.strip() for s in a.sports.split(",") if s.strip()),
    )


if __name__ == "__main__":
    raise SystemExit(main())
