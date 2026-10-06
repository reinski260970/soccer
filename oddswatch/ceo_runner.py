"""CEO-Matchday-Report: frischer Scan + News + CLV, optional direkt zu Telegram.

Nutzt ausschließlich die bereits vorhandenen Umgebungsvariablen
TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID. Marktpreise bleiben vom Modell
getrennt; der Report veröffentlicht nur die von scan.run() freigegebenen PLAYs
und kennzeichnet WATCH ausdrücklich als nicht freigegeben.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import news, outlook, report, scan, settle, telegram
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
    return [
        "📈 CLV / PERFORMANCE",
        _portfolio_line(j.read("valuebets"), "Modell-Freigaben"),
        _portfolio_line(j.read("placed"), "Gespielt"),
        "CLV ist Freigabemaßstab; kurzfristiger ROI überstimmt schwachen CLV nicht.",
    ]


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
    lines += [""] + core
    lines += [""] + _clv_lines(j)

    issues = list(res.issues) + list(news_issues)
    if settlement_issue:
        issues.append(settlement_issue)
    if issues:
        lines += ["", f"⚠️ DATENLAGE: {len(issues)} offene Hinweise"]
        lines += [f"• {x}" for x in issues[:3]]

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
