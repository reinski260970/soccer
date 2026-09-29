"""Schnellscan: Kalshi gegen DraftKings, ohne Modell, für den 15-Minuten-Takt.

Kalshi hinkt DraftKings/Pinnacle nach News oder Linienbewegungen teils
hinterher. Der Schnellscan lädt nur Spielpläne mit DraftKings-Linien (ESPN)
und die Kalshi-Orderbücher – kein Modell-Fit – und meldet, sobald Kalshi
inkl. Gebühr ≥ 3 % über dem de-vigged DraftKings-Kurs liegt:
Sieger (1X2 bzw. Moneyline), Über/Unter und Handicap auf identischer Linie.

Neue Freigaben gehen ins Journal (valuebets) und – einmal je Tipp und
Preisstufe – per Telegram raus. Jeder Lauf sichert die Kalshi-Preise offener
Tipps (Closing Line) und rechnet beendete Tipps ab.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import lines, report, settle, telegram
from .journal import Journal
from .scan import Fixture, _attach_kalshi, _devig_ref, evaluate_fixture, snapshot
from .selection import Candidate, pick
from .sources import espn, kalshi

# Liga -> (ESPN-Pfad, Kalshi-Serie Sieger, Sportart, Dreiweg?)
LEAGUES = {
    "nfl": ("football/nfl", "KXNFLGAME", "nfl", False),
    "nhl": ("hockey/nhl", "KXNHLGAME", "nhl", False),
    "nba": ("basketball/nba", "KXNBAGAME", "nba", False),
    "bundesliga": ("soccer/ger.1", "KXBUNDESLIGAGAME", "soccer", True),
    "2bundesliga": ("soccer/ger.2", "KXBUNDESLIGA2GAME", "soccer", True),
    "ucl": ("soccer/uefa.champions", "KXUCLGAME", "soccer", True),
    "uel": ("soccer/uefa.europa", "KXUELGAME", "soccer", True),
    "uecl": ("soccer/uefa.europa.conf", "KXUECLGAME", "soccer", True),
    "nations": ("soccer/uefa.nations", "KXUEFANLGAME", "soccer", True),
    "epl": ("soccer/eng.1", "KXEPLGAME", "soccer", True),
    "laliga": ("soccer/esp.1", "KXLALIGAGAME", "soccer", True),
    "seriea": ("soccer/ita.1", "KXSERIEAGAME", "soccer", True),
}
LINE_SERIES = {"epl": ("KXEPLTOTAL", "KXEPLSPREAD", "Tore"),
               "laliga": ("KXLALIGATOTAL", "KXLALIGASPREAD", "Tore"),
               "seriea": ("KXSERIEATOTAL", "KXSERIEASPREAD", "Tore")}
STATE = Path("data/journal/quick_alerts.json")


def fixtures(start: date, days: int, issues: list[str]) -> list[Fixture]:
    out = []
    for lg, (path, series, sport, three) in LEAGUES.items():
        espn.PATHS.setdefault(lg, path)
        games, errs = espn.upcoming(lg, start, days)
        issues += errs[:2]
        games = [g for g in games if g.status == "STATUS_SCHEDULED" and g.ref_line]
        if not games:
            continue
        kq, err = kalshi.fetch_series(series)
        if err:
            issues.append(f"Kalshi {lg}: {err}")
        for g in games:
            ref = _devig_ref(g, three_way=three)
            if not ref:
                continue
            fx = Fixture(lg, sport, g, dict(ref), "Schnellscan (Preisvergleich ohne Modell)",
                         ref_probs=ref, model="market")
            _attach_kalshi(fx, kq)
            if fx.kalshi:
                out.append(fx)
    return out


def _key(c: Candidate) -> str:
    # Neue Meldung erst, wenn sich die Quote um ≥ 5 % verbessert
    return f"{c.ref}|{int(c.odds * 20)}"


def run(j: Journal | None = None, send: bool = False, days: int = 7,
        now: datetime | None = None) -> list[str]:
    j = j or Journal()
    now = now or datetime.now(timezone.utc)
    issues: list[str] = []
    notes: list[str] = []
    for lg, s in LINE_SERIES.items():
        lines.SERIES.setdefault(lg, s)
    fx = fixtures(now.date(), days, issues)
    cands = [c for f in fx for c in evaluate_fixture(f, {})] + lines.candidates(fx, issues, notes)
    picks = pick(cands)
    log = [f"Schnellscan {now:%d.%m.%Y %H:%M} UTC: {len(fx)} Spiele mit DraftKings- und Kalshi-Preis, "
           f"{len(cands)} Märkte verglichen, {len(picks)} Freigabe(n)"]
    snapshot(fx)
    log += settle.snapshot_open(j)
    try:
        seen = set(json.loads(STATE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        seen = set()
    open_vb = {(r["event"], r["market"], r["source"]) for r in j.read("valuebets") if not r.get("result")}
    j.append("valuebets", [c.as_row() for c in picks if (c.event, c.market, c.source) not in open_vb])
    new = [c for c in picks if _key(c) not in seen]
    for c in picks:
        log.append(f"  PLAY {c.event}: {c.selection} @ {c.odds:.2f} (spielbar ab {c.min_odds:.2f}, "
                   f"EV {c.ev * 100:+.1f} %)" + ("  [neu]" if c in new else ""))
    if send and new:
        txt = report.telegram_text(now.strftime("%d.%m.%Y %H:%M UTC"), new, [])
        r = telegram.send("⚡ Schnellscan – Kalshi günstiger als DraftKings\n" + txt)
        log.append("Telegram: " + (f"gesendet {r['message_ids']}" if r["sent"] else f"NICHT gesendet – {r['error']}"))
        if r["sent"]:
            seen |= {_key(c) for c in new}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(sorted(seen)), encoding="utf-8")
    log += settle.settle_all(j)[-2:]
    log += [f"  Hinweis: {i}" for i in issues[:5]]
    return log
