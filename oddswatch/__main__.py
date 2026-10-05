"""CLI.

  python -m oddswatch scan [--days 7] [--watch-days 14] [--sports soccer,nfl,nhl,nba,hockey_eu] [--send]
  python -m oddswatch daily [--no-scan] [--send] [--force]   # Auswertung, Profit, Ausblick; sendet nur bei Neuigkeiten
  python -m oddswatch news [--send] [--digest]   # News-Agent: Warnungen bzw. Übersicht
  python -m oddswatch settle            # Valuebets/gespielte Wetten abrechnen + CLV
  python -m oddswatch tune              # Fußball-Modell: Tuning auf Saison N, Test auf N+1
  python -m oddswatch backtest          # Modell gegen Markt (Walk-forward, CLV) -> data/validation.json
  python -m oddswatch research          # Modellvarianten gegen den Markt (Tuning/Holdout)
  python -m oddswatch m8-research       # M8 Hybridmodell, reiner OOS-Test ohne Markt-Blend
  python -m oddswatch m9-research       # M9 Dual-Poisson, reiner OOS-Test ohne Markt-Blend
  python -m oddswatch m10-research      # M10 Specialist-Gate auf M9
  python -m oddswatch quick [--send]    # Fußball-Quotenwächter (API-Football)
  python -m oddswatch guard [--send]    # Quotenwächter: CEO-Tipps gegen Pinnacle/Bet365/Betfair (API-Football)
  python -m oddswatch tennis [--send] [--all]   # Tennis-Valuebets aus MongoDB Atlas (tennis_db, nur lesend)
  python -m oddswatch place --ref <Valuebet-Referenz> --odds 2.1 --stake 1 --bookmaker bet365
  python -m oddswatch send <datei>      # Telegram-Text senden (Bot API)
  python -m oddswatch summary
  python -m oddswatch telegram-chatid   # Chat-ID(s) aus getUpdates anzeigen
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
                   and c.ev >= 0.0 and c.edge > 0 and c.p_ref is not None],
                  key=lambda c: -c.ev)[:5]


def _scan(a) -> int:
    from . import scan
    j = Journal()
    res = scan.run(days=a.days, watch_days=a.watch_days, sports=tuple(a.sports.split(",")),
                   journal=None if a.dry else j)
    watch = _watchlist(res)
    if not a.dry:
        from . import news
        news.save_targets(res.fixtures, res.picks, watch)
    from . import outlook
    rows = outlook.build(res.fixtures, res.candidates, res.picks)
    note = outlook.soccer_note(res.notes, res.issues)
    md = report.ceo_report(res.stand, res.picks, len(res.fixtures), res.issues, res.notes,
                           fixtures=res.fixtures, watch=watch,
                           outlook=outlook.report_lines(rows, notes=note))
    tg = report.telegram_text(res.stand, res.picks, watch,
                              outlook=outlook.telegram_lines(rows, notes=note))
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
    picks, watch, ol = [], [], None
    if not a.no_scan:
        from . import outlook, scan
        res = scan.run(sports=tuple(a.sports.split(",")), journal=j)
        picks, watch = res.picks, _watchlist(res)
        from . import news
        news.save_targets(res.fixtures, picks, watch)
        ol = outlook.telegram_lines(outlook.build(res.fixtures, res.candidates, picks),
                                    notes=outlook.soccer_note(res.notes, res.issues))
    txt = daily.daily_text(j, picks=picks, watch=watch, outlook=ol)
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
    if a.digest:
        from datetime import datetime, timezone
        from pathlib import Path as _P
        targets = news.load_targets(j)
        issues: list[str] = []
        items = news.collect({t.league for t in targets}, issues)
        alerts = news.find_alerts(targets, items, set(), datetime.now(timezone.utc))
        txt = news.digest_text(alerts, report.stand())
        print(f"{len(items)} Artikel geprüft, {len(alerts)} Meldungen in der Übersicht")
        print("--- Telegram ---\n" + txt)
        if a.send:
            r = telegram.send(txt)
            print(f"Telegram: {'gesendet, message_id ' + str(r['message_ids']) if r['sent'] else 'NICHT gesendet – ' + r['error']}")
            return 0 if r["sent"] else 2
        return 0
    alerts, issues, n = news.run(j)
    for i in issues:
        print(f"Quelle nicht erreichbar: {i}")
    print(f"{n} Artikel geprüft, {len(alerts)} neue materielle Meldungen")
    if not alerts:
        print("Telegram: keine neuen News – nicht gesendet")
        return 0
    from datetime import datetime, timezone
    txt = news.alert_text(alerts, report.stand())
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


def _research(a) -> int:
    from . import research
    for line in research.run():
        print(line)
    return 0


def _m8_research(a) -> int:
    from . import m8_research
    leagues = a.leagues.split(",") if getattr(a, "leagues", "") else None
    for line in m8_research.run(leagues=leagues):
        print(line)
    return 0


def _m9_research(a) -> int:
    from . import m9_research
    leagues = a.leagues.split(",") if getattr(a, "leagues", "") else None
    for line in m9_research.run(leagues=leagues):
        print(line)
    return 0


def _m10_research(a) -> int:
    from . import m10_research
    leagues = a.leagues.split(",") if getattr(a, "leagues", "") else None
    for line in m10_research.run(leagues=leagues):
        print(line)
    return 0


def _m12_research(a) -> int:
    from . import m12_research
    leagues = a.leagues.split(",") if getattr(a, "leagues", "") else None
    for line in m12_research.run(leagues=leagues):
        print(line)
    return 0


def _m13_research(a) -> int:
    from . import m13_research
    leagues = a.leagues.split(",") if getattr(a, "leagues", "") else None
    for line in m13_research.run(leagues=leagues):
        print(line)
    return 0


def _football_mongo(a) -> int:
    from .sources.football_mongo import run
    return run()


def _football_mongo_profile(a) -> int:
    from .sources.football_mongo import run_profile
    return run_profile()


def _football_mongo_audit(a) -> int:
    from .sources.football_mongo import run_audit
    return run_audit()



def _quick(a) -> int:
    from . import quick
    try:
        for line in quick.run(send=a.send, days=a.days, full=a.full):
            print(line)
        return 0
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 2


def _guard(a) -> int:
    from . import guard
    try:
        for line in guard.run(send=a.send, strict=True):
            print(line)
        return 0
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 2


def _tennis(a) -> int:
    from . import tennis
    for line in tennis.run(send=a.send, all_bets=a.all):
        print(line)
    return 0


def _tune(a) -> int:
    from . import tune
    for line in tune.run():
        print(line)
    return 0


def _backtest(a) -> int:
    from . import backtest
    for line in backtest.run():
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
    nw.add_argument("--digest", action="store_true", help="Übersicht aller Meldungen (72 h), auch bereits gemeldete")
    nw.set_defaults(fn=_news)
    sub.add_parser("settle").set_defaults(fn=_settle)
    sub.add_parser("backtest").set_defaults(fn=_backtest)
    sub.add_parser("tune").set_defaults(fn=_tune)
    sub.add_parser("research").set_defaults(fn=_research)
    m8 = sub.add_parser("m8-research")
    m8.add_argument("--leagues", default="", help="kommagetrennte Ligakürzel")
    m8.set_defaults(fn=_m8_research)
    m9 = sub.add_parser("m9-research")
    m9.add_argument("--leagues", default="", help="kommagetrennte Ligakürzel")
    m9.set_defaults(fn=_m9_research)
    m10 = sub.add_parser("m10-research")
    m10.add_argument("--leagues", default="", help="kommagetrennte Ligakürzel")
    m10.set_defaults(fn=_m10_research)
    m12 = sub.add_parser("m12-research")
    m12.add_argument("--leagues", default="", help="kommagetrennte Ligakürzel")
    m12.set_defaults(fn=_m12_research)
    m13 = sub.add_parser("m13-research")
    m13.add_argument("--leagues", default="", help="kommagetrennte Ligakürzel")
    m13.set_defaults(fn=_m13_research)
    sub.add_parser("football-mongo").set_defaults(fn=_football_mongo)
    sub.add_parser("football-mongo-profile").set_defaults(fn=_football_mongo_profile)
    sub.add_parser("football-mongo-audit").set_defaults(fn=_football_mongo_audit)
    qk = sub.add_parser("quick")
    qk.add_argument("--send", action="store_true")
    qk.add_argument("--days", type=int, default=7)
    qk.add_argument("--full", action="store_true",
                    help="alle heutigen API-Football-Fixtures gegen Pinnacle/Bet365/Betfair scannen")
    qk.set_defaults(fn=_quick)
    gd = sub.add_parser("guard")
    gd.add_argument("--send", action="store_true")
    gd.set_defaults(fn=_guard)
    tn = sub.add_parser("tennis")
    tn.add_argument("--send", action="store_true")
    tn.add_argument("--all", action="store_true", help="alle offenen Tipps senden, nicht nur neue")
    tn.set_defaults(fn=_tennis)
    pl = sub.add_parser("place")
    pl.add_argument("--ref", required=True)
    pl.add_argument("--odds", type=float, required=True)
    pl.add_argument("--stake", type=float, required=True)
    pl.add_argument("--bookmaker", required=True)
    pl.add_argument("--event")
    pl.add_argument("--market")
    pl.add_argument("--selection")
    pl.set_defaults(fn=_place)
    se = sub.add_parser("send")
    se.add_argument("file")
    se.set_defaults(fn=_send)
    sub.add_parser("summary").set_defaults(fn=_summary)
    sub.add_parser("telegram-chatid").set_defaults(fn=_chatid)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
