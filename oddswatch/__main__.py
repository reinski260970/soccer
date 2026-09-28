"""CLI.

  python -m oddswatch scan [--days 7] [--watch-days 14] [--sports soccer,nfl,nhl,nba,hockey_eu] [--send]
  python -m oddswatch daily [--no-scan] [--send] [--force]   # Auswertung, Profit, Ausblick; sendet nur bei Neuigkeiten
  python -m oddswatch news [--send]      # News-Agent: Warnungen zu Freigaben/Watchlist
  python -m oddswatch settle            # Valuebets/gespielte Wetten abrechnen + CLV
  python -m oddswatch closing           # Kalshi-Preise offener Tipps sichern (Closing Line)
  python -m oddswatch place --ref <Kalshi-Ticker|Valuebet> --odds 2.1 --stake 1 --bookmaker kalshi
  python -m oddswatch send <datei>      # Telegram-Text senden (Bot API)
  python -m oddswatch summary
  python -m oddswatch telegram-chatid   # Chat-ID(s) aus getUpdates anzeigen
  python -m oddswatch kalshi-check      # Key prüfen (Kontostand, nur lesend)
  python -m oddswatch import-fills [--eh-usd 10]   # Kalshi-Trades -> placed.csv
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import report, telegram
from .journal import Journal


def _watchlist(res) -> list:
    picked = {(c.event, c.market) for c in res.picks}
    return sorted([c for c in res.candidates if (c.event, c.market) not in picked
                   and c.ev >= 0.0 and c.edge > 0], key=lambda c: -c.ev)[:5]


def _scan(a) -> int:
    from . import scan
    j = Journal()
    res = scan.run(days=a.days, watch_days=a.watch_days, sports=tuple(a.sports.split(",")),
                   journal=None if a.dry else j)
    watch = _watchlist(res)
    if not a.dry:
        from . import news
        news.save_targets(res.fixtures, res.picks, watch)
    md = report.ceo_report(res.stand, res.picks, len(res.fixtures), res.issues, res.notes,
                           fixtures=res.fixtures, watch=watch)
    tg = report.telegram_text(res.stand, res.picks, watch)
    out = Path("reports")
    out.mkdir(exist_ok=True)
    stem = f"{date.today():%Y-%m-%d}"
    (out / f"{stem}-bericht.md").write_text(md, encoding="utf-8")
    (out / f"{stem}-telegram.txt").write_text(tg, encoding="utf-8")
    print(md)
    print("--- Telegram ---\n" + tg)
    if a.send:
        r = telegram.send(tg)
        print(f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}")
        return 0 if r["sent"] else 2
    return 0


def _daily(a) -> int:
    from . import daily, settle
    j = Journal()
    for line in settle.settle_all(j):
        print(line)
    picks, watch = [], []
    if not a.no_scan:
        from . import scan
        res = scan.run(sports=tuple(a.sports.split(",")), journal=j)
        picks, watch = res.picks, _watchlist(res)
        from . import news
        news.save_targets(res.fixtures, picks, watch)
    txt = daily.daily_text(j, picks=picks, watch=watch)
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / f"{date.today():%Y-%m-%d}-daily.txt").write_text(txt, encoding="utf-8")
    print("--- Telegram ---\n" + txt)
    if a.send:
        state = Path("data/journal/daily_state.txt")
        key = daily.news_key(j, picks, watch)
        last = state.read_text(encoding="utf-8").strip() if state.exists() else ""
        if key == last and not a.force:
            print("Telegram: keine Neuigkeiten seit dem letzten Bericht – nicht gesendet")
            return 0
        r = telegram.send(txt)
        print(f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}")
        if r["sent"]:
            state.write_text(key + "\n", encoding="utf-8")
        return 0 if r["sent"] else 2
    return 0


def _news(a) -> int:
    from . import news
    j = Journal()
    alerts, issues, n = news.run(j)
    for i in issues:
        print(f"Quelle nicht erreichbar: {i}")
    print(f"{n} Artikel geprüft, {len(alerts)} neue materielle Meldungen")
    if not alerts:
        print("Telegram: keine neuen News – nicht gesendet")
        return 0
    from datetime import datetime, timezone
    txt = news.alert_text(alerts, datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"))
    print("--- Telegram ---\n" + txt)
    if a.send:
        r = telegram.send(txt)
        print(f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}")
        if not r["sent"]:
            return 2
        news.mark_seen(alerts, j)   # nur gesendete Meldungen gelten als gemeldet
    return 0


def _settle(a) -> int:
    from . import settle
    for line in settle.settle_all(Journal()):
        print(line)
    return 0


def _closing(a) -> int:
    from . import settle
    for line in settle.snapshot_open(Journal()):
        print(line)
    return 0


def _place(a) -> int:
    j = Journal()
    vb = [r for r in j.read("valuebets") if a.ref in (r.get("ref"), r.get("event"))]
    base = vb[-1] if vb else {}
    j.append("placed", [{
        "event": base.get("event", a.event or a.ref), "kickoff": base.get("kickoff", ""),
        "market": base.get("market", a.market or ""), "selection": base.get("selection", a.selection or ""),
        "bookmaker": a.bookmaker, "odds_taken": a.odds, "stake_eh": a.stake,
        "valuebet_ref": base.get("created_at", ""), "ref": base.get("ref", a.ref)}])
    print("gespeichert" + ("" if vb else " (ohne zugehörige Valuebet-Freigabe)"))
    return 0


def _send(a) -> int:
    r = telegram.send(Path(a.file).read_text(encoding="utf-8"))
    print(f"gesendet, message_id {r['message_ids']}" if r["sent"] else f"NICHT gesendet – {r['error']}")
    return 0 if r["sent"] else 2


def _summary(a) -> int:
    j = Journal()
    for name in ("valuebets", "placed"):
        print(name, j.summary(name))
    return 0


def _kalshi_check(a) -> int:
    from .sources.kalshi_auth import Client
    try:
        c = Client()
        print(f"Kalshi-Key ok – Kontostand {c.balance_usd():.2f} $")
        return 0
    except Exception as e:  # noqa: BLE001 – Fehlertext ist die Auskunft
        print(f"Kalshi-Key NICHT nutzbar: {e}")
        return 2


def _import_fills(a) -> int:
    from .portfolio import import_fills
    try:
        for line in import_fills(Journal(), eh_usd=a.eh_usd):
            print(line)
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"Import fehlgeschlagen: {e}")
        return 2


def _chatid(a) -> int:
    ids, err = telegram.chat_ids()
    if err:
        print(err)
        return 2
    if not ids:
        print("Keine Chats gefunden – dem Bot zuerst eine Nachricht schreiben (/start).")
        return 1
    for cid, name in ids:
        print(f"TELEGRAM_CHAT_ID={cid}  ({name})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="oddswatch")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--days", type=int, default=7)
    s.add_argument("--watch-days", type=int, default=14)
    s.add_argument("--sports", default="soccer,nfl,nhl,nba,hockey_eu")
    s.add_argument("--send", action="store_true")
    s.add_argument("--dry", action="store_true", help="nichts ins Journal schreiben")
    s.set_defaults(fn=_scan)
    d = sub.add_parser("daily")
    d.add_argument("--no-scan", action="store_true", help="nur Journal auswerten, kein neuer Scan")
    d.add_argument("--sports", default="soccer,nfl,nhl,nba,hockey_eu")
    d.add_argument("--send", action="store_true")
    d.add_argument("--force", action="store_true", help="auch ohne Neuigkeiten senden")
    d.set_defaults(fn=_daily)
    nw = sub.add_parser("news")
    nw.add_argument("--send", action="store_true")
    nw.set_defaults(fn=_news)
    sub.add_parser("settle").set_defaults(fn=_settle)
    sub.add_parser("closing").set_defaults(fn=_closing)
    pl = sub.add_parser("place")
    pl.add_argument("--ref", required=True)
    pl.add_argument("--odds", type=float, required=True)
    pl.add_argument("--stake", type=float, required=True)
    pl.add_argument("--bookmaker", default="kalshi")
    pl.add_argument("--event")
    pl.add_argument("--market")
    pl.add_argument("--selection")
    pl.set_defaults(fn=_place)
    se = sub.add_parser("send")
    se.add_argument("file")
    se.set_defaults(fn=_send)
    sub.add_parser("summary").set_defaults(fn=_summary)
    sub.add_parser("telegram-chatid").set_defaults(fn=_chatid)
    sub.add_parser("kalshi-check").set_defaults(fn=_kalshi_check)
    im = sub.add_parser("import-fills")
    im.add_argument("--eh-usd", type=float, default=None, help="Dollar je Einheit (Default 10 bzw. ODDSWATCH_EH_USD)")
    im.set_defaults(fn=_import_fills)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
