"""Multi-league structural shadow for football leagues without Understat."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import bookmaker, matching, report, soccer_steam, sql_store
from .m17_11_external_shadow import fair as structural_fair
from .scan import Fixture, _aut_model, _soccer_model
from .sources import espn, football_data, oddalerts, soccerstats, xg_external

TZ = ZoneInfo("Europe/Vienna")

SCOPE = {
    "2bundesliga": ("2. Bundesliga", "D2"),
    "championship": ("Championship", "E1"),
    "eredivisie": ("Eredivisie", "N1"),
    "primeira": ("Primeira Liga", "P1"),
    "belgium": ("Belgian Pro League", "B1"),
    "turkey": ("Süper Lig", "T1"),
    "scotland": ("Scottish Premiership", "SC0"),
    "greece": ("Super League Greece", "G1"),
    "austria": ("Admiral Bundesliga", "AUT"),
    "switzerland": ("Swiss Super League", "SUI"),
    "sweden": ("Allsvenskan", "SWE"),
    "norway": ("Eliteserien", "NOR"),
    "denmark": ("Danish Superliga", "DEN"),
    "poland": ("Ekstraklasa", "POL"),
}

MIN_EV = 0.03
MIN_CLV = 0.01


def _history(code: str, issues: list[str]):
    if code == "AUT":
        _, ms = _aut_model(issues)
        return ms
    if code in football_data.LEAGUES:
        _, ms = _soccer_model([code], issues)
        return ms
    return []


def _team_for_history(name: str, short: str, matches):
    if not matches:
        return name
    teams = sorted({m.home for m in matches} | {m.away for m in matches})
    return matching.find(name, teams) or matching.find(short, teams) or name


def _best_exec(fx: Fixture, side: str):
    rows = [q for q in fx.market_quotes.get(side, []) if getattr(q, "executable", True)]
    return max(rows, key=lambda q: q.odds) if rows else None


def _status(ev: float, clv: float, steam):
    sig = (steam or {}).get("signal")
    if sig and sig.get("direction") == "DRIFTING":
        return "PASS"
    if ev >= MIN_EV and clv >= MIN_CLV:
        return "SHADOW-PLAY"
    if ev > 0 and clv > 0:
        return "WATCH"
    return "PASS"


def _steam_text(row):
    if not row:
        return "NO_STEAM"
    sig = row.get("signal")
    if sig:
        move = float(sig.get("lead_move") or 0) * 100
        mins = int(sig.get("minutes") or 0)
        return ("STEAM+" if sig.get("direction") == "SHORTENING" else "STEAM-") + f" {move:+.1f}pp/{mins}m"
    gap = float(row.get("gap") or 0)
    if gap >= .008:
        return f"SHARP_GAP+ {gap*100:+.1f}pp"
    if gap <= -.008:
        return f"SHARP_GAP- {gap*100:+.1f}pp"
    return "NEUTRAL"


def build(start: date | None = None, days: int = 7):
    start = start or datetime.now(TZ).date()
    now = datetime.now(timezone.utc)
    issues = []
    notes = []
    fixtures = []

    for league, (label, code) in SCOPE.items():
        games, errs = espn.upcoming(league, start, days)
        issues += errs
        games = [g for g in games if g.status == "STATUS_SCHEDULED"]
        if not games:
            notes.append(f"{label}: keine Spiele")
            continue

        snapshots, xerr = xg_external.snapshot(code, now)
        if not snapshots:
            notes.append(f"{label}: NO_XG ({xerr})")
            continue
        xg_external.persist_snapshot(code, snapshots, now)

        venue, verr = soccerstats.team_homeaway(code, cache_days=0.10)
        if verr and not venue:
            notes.append(f"{label}: SoccerSTATS Venue fehlt ({verr})")

        oa, oaerr = oddalerts.team_xg(code)
        alt = {r.team: (r.xg_per90, r.xga_per90) for r in oa}
        if oaerr:
            notes.append(f"{label}: OddAlerts Crosscheck fehlt ({oaerr})")

        hist = _history(code, issues)

        for g in games:
            h = _team_for_history(g.home.name, g.home.short, hist)
            a = _team_for_history(g.away.name, g.away.short, hist)
            try:
                sf = structural_fair(
                    h, a, g.kickoff.date(),
                    snapshots=snapshots,
                    venue_rows=venue,
                    matches=hist,
                    alt_xg=alt,
                )
            except KeyError as exc:
                issues.append(f"{label}: {exc} ({g.title})")
                continue

            # A single current xG signal without venue or recent history is too
            # weak to call M17.11-structural. Keep it out rather than invent.
            if sf.signals_used < 2:
                notes.append(f"{label}: {g.title} NO_MODEL – nur {sf.signals_used} Struktursignal")
                continue

            disagreement = (
                f", xG-source-disagreement {sf.xg_source_disagreement:.3f}"
                if sf.xg_source_disagreement is not None else ""
            )
            ctx = [
                f"xG primary {snapshots[0].source}; alt {'oddalerts' if alt else 'none'}{disagreement}",
                f"signals {sf.signals_used}; recent {sf.home_recent_n}/{sf.away_recent_n}",
            ]
            if sf.home_ppg is not None and sf.away_ppg is not None:
                ctx.append(f"SoccerSTATS PPG H/A {sf.home_ppg:.2f}/{sf.away_ppg:.2f}")

            flags = {
                "home": ["m17.11 external shadow – keine PLAY-Freigabe"],
                "draw": ["m17.11 external shadow – keine PLAY-Freigabe"],
                "away": ["m17.11 external shadow – keine PLAY-Freigabe"],
            }
            fixtures.append(Fixture(
                league, "soccer", g, sf.probs,
                (
                    f"M17.11 external structural xG {sf.home_xg:.2f}:{sf.away_xg:.2f}; "
                    f"fast {sf.home_fast:.2f}:{sf.away_fast:.2f}"
                    + (f"; slow {sf.home_slow:.2f}:{sf.away_slow:.2f}" if sf.home_slow is not None else "")
                    + (f"; venue {sf.home_venue:.2f}:{sf.away_venue:.2f}" if sf.home_venue is not None else "")
                ),
                context=ctx,
                flags=flags,
                estimate=True,
                model="m17.11-external-shadow",
            ))

    bookmaker.attach_prices(fixtures, issues)
    steam = soccer_steam.assess(fixtures, now=now)

    # Every shadow probability and quote is persisted, but no official PLAY.
    sql_store.sync_scan(fixtures, [])

    entries = []
    for fx in fixtures:
        for side in ("home", "draw", "away"):
            offer = _best_exec(fx, side)
            if not offer:
                continue
            p = float(fx.probs[side])
            ev = p * float(offer.odds) - 1
            edge = p - 1/float(offer.odds)
            st = steam.get((fx.game.title, side))
            clv = float((st or {}).get("clv_to_sharp") or 0)
            status = _status(ev, clv, st)
            entries.append((status, ev + max(clv, 0), fx, side, offer, ev, edge, clv, st))
    entries.sort(key=lambda x: ({"SHADOW-PLAY":0, "WATCH":1, "PASS":2}[x[0]], -x[1]))

    lines = [
        f"⚽ NON-UNDERSTAT SHADOW · {start:%d.%m.}–{start + timedelta(days=days):%d.%m.%Y}",
        f"M17.11 external structural · {len(fixtures)} Spiele modelliert",
        "Fair unabhängig → Markt → CLV/Steam · keine Sharpery-Freigabe",
        "",
        "📚 LIGA-ABDECKUNG",
    ]
    for league, (label, _) in SCOPE.items():
        n = sum(1 for fx in fixtures if fx.league == league)
        if n:
            lines.append(f"• {label}: {n} Spiele")

    shown = [x for x in entries if x[0] != "PASS"]
    lines += ["", f"📌 ENTRY-GATE · {len(shown)} positive Shadow-Kandidaten"]
    for status, _, fx, side, offer, ev, edge, clv, st in shown[:25]:
        sharp = (st or {}).get("sharp_fair")
        selection = {
            "home": fx.game.home.name,
            "draw": "Unentschieden",
            "away": fx.game.away.name,
        }[side]
        lines += [
            f"{'🟢' if status == 'SHADOW-PLAY' else '🟡'} {status} · {report._league(fx.league)} · {fx.game.title}",
            f"  {selection} @ {offer.odds:.2f} ({offer.source}) · Fair {1/fx.probs[side]:.2f}",
            f"  EV {ev*100:+.1f}% · Edge {edge*100:+.1f}pp · CLV-Case {clv*100:+.1f}% · {_steam_text(st)}"
            + (f" · Pin no-vig {sharp:.2f}" if sharp else ""),
        ]

    if not shown:
        lines.append("Keine Auswahl erfüllt aktuell Fair + ausführbaren Preis + positives CLV-Gate.")

    if notes:
        lines += ["", "ℹ️ DATENSTATUS"] + [f"• {x}" for x in notes[:30]]
    if issues:
        lines += ["", f"⚠️ {len(issues)} interne Zuordnungs-/Abrufhinweise"]

    return "\n".join(lines) + "\n", fixtures, entries, notes, issues


def run():
    text, *_ = build()
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
