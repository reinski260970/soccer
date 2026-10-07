"""Austria-only M17.11 structural shadow test.

Only Austrian Bundesliga fixtures are queried. The fair model is independent
from market prices. Market/steam/CLV are applied only after fair probabilities
exist. No official PLAY or Sharpery row is created.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import bookmaker, matching, report, soccer_steam, sql_store, telegram
from .m17_11_aut_shadow import fair as structural_fair
from .scan import Fixture, _aut_model
from .sources import espn, xg_external, soccerstats

TZ = ZoneInfo("Europe/Vienna")
MIN_MODEL_EV = 0.03
MIN_CLV_CASE = 0.01


def _next_weekend(today: date | None = None) -> tuple[date, date]:
    today = today or datetime.now(TZ).date()
    wd = today.weekday()
    if wd <= 4:
        friday = today + timedelta(days=4 - wd)
    elif wd == 5:
        friday = today - timedelta(days=1)
    else:
        friday = today - timedelta(days=2)
    return friday, friday + timedelta(days=2)


def _resolve_aut_team(name: str, short: str | None, teams: list[str]) -> str | None:
    candidates = [name, short]
    alias_map = {
        "WSG Swarovski Tirol": ["WSG Tirol", "Tirol", "WSG Wattens"],
        "WSG Tirol": ["Tirol", "WSG Wattens"],
        "SV Josko Ried": ["SV Ried", "Ried"],
        "SV Ried": ["Ried"],
        "RB Salzburg": ["Red Bull Salzburg", "Salzburg"],
        "Red Bull Salzburg": ["Salzburg"],
        "Austria Vienna": ["Austria Wien"],
        "Rapid Vienna": ["Rapid Wien"],
        "SC Rheindorf Altach": ["SCR Altach", "Altach"],
        "Wolfsberger": ["Wolfsberger AC"],
    }
    candidates += alias_map.get(name, [])
    for cand in candidates:
        if not cand:
            continue
        hit = matching.find(cand, teams)
        if hit:
            return hit
    return None


def _best_exec(fx: Fixture, side: str):
    rows = [
        q for q in (getattr(fx, "market_quotes", None) or {}).get(side, [])
        if getattr(q, "executable", True)
    ]
    return max(rows, key=lambda q: q.odds) if rows else None


def _market_line(fx: Fixture) -> str:
    parts = []
    for side, label in (("home", "1"), ("draw", "X"), ("away", "2")):
        qs = (getattr(fx, "market_quotes", None) or {}).get(side, [])
        if not qs:
            parts.append(f"{label} –")
            continue
        best = max(qs, key=lambda q: q.odds)
        kind = "E" if getattr(best, "executable", True) else "R"
        parts.append(f"{label} {best.odds:.2f} {best.source}[{kind}]")
    return " | ".join(parts)


def _steam_text(row: dict | None) -> str:
    if not row:
        return "NO_STEAM_DATA"
    sig = row.get("signal")
    if sig:
        move = float(sig.get("lead_move") or 0.0) * 100
        mins = int(sig.get("minutes") or 0)
        return (
            f"STEAM+ Pinnacle {move:+.1f}pp/{mins}m"
            if sig.get("direction") == "SHORTENING"
            else f"STEAM- Pinnacle {move:+.1f}pp/{mins}m"
        )
    gap = float(row.get("gap") or 0.0)
    if gap >= 0.008:
        return f"SHARP_GAP+ {gap*100:+.1f}pp"
    if gap <= -0.008:
        return f"SHARP_GAP- {gap*100:+.1f}pp"
    return "NEUTRAL"


def _status(model_ev: float, clv: float, row: dict | None) -> str:
    sig = (row or {}).get("signal")
    if sig and sig.get("direction") == "DRIFTING":
        return "PASS"
    if model_ev >= MIN_MODEL_EV and clv >= MIN_CLV_CASE:
        return "SHADOW-PLAY"
    if model_ev > 0 and clv > 0:
        return "WATCH"
    return "PASS"


def build(today: date | None = None) -> str:
    friday, sunday = _next_weekend(today)
    issues: list[str] = []

    # Historical Austria match stream is used only for slow structural context
    # and home/away league baseline. Its old Poisson fair is NOT used.
    old_model, matches = _aut_model(issues)
    if old_model is None or not matches:
        raise RuntimeError("Austria-Historie konnte nicht geladen werden")
    teams = list(old_model.attack)

    now = datetime.now(timezone.utc)
    snapshots, xerr = xg_external.snapshot("AUT", now)
    if xerr or not snapshots:
        raise RuntimeError(f"Austria xG fehlt: {xerr or 'keine Daten'}")
    xg_external.persist_snapshot("AUT", snapshots, now)

    venue_rows, verr = soccerstats.team_homeaway("AUT", cache_days=0.10)
    if verr:
        issues.append(f"SoccerSTATS Venue: {verr}")

    games, errs = espn.upcoming("austria", friday, 2)
    issues += errs
    games = [
        g for g in games
        if g.status == "STATUS_SCHEDULED"
        and friday <= g.kickoff.astimezone(TZ).date() <= sunday
    ]

    fixtures: list[Fixture] = []
    diagnostics = {}
    for g in games:
        h = _resolve_aut_team(g.home.name, g.home.short, teams)
        a = _resolve_aut_team(g.away.name, g.away.short, teams)
        if not h or not a:
            issues.append(f"Team nicht zugeordnet: {g.title}")
            continue
        try:
            sf = structural_fair(
                h, a, g.kickoff.date(), matches, snapshots, venue_rows
            )
        except KeyError as exc:
            issues.append(str(exc))
            continue

        fx = Fixture(
            "austria",
            "soccer",
            g,
            sf.probs,
            (
                f"M17.11-Structural AUT: xG consensus {sf.home_xg:.2f}:{sf.away_xg:.2f}; "
                f"fast {sf.home_fast:.2f}:{sf.away_fast:.2f}; "
                f"slow {sf.home_slow:.2f}:{sf.away_slow:.2f}"
            ),
            context=[
                f"xG sample {sf.home_xg_matches}/{sf.away_xg_matches}",
                f"recent sample {sf.home_recent_n}/{sf.away_recent_n}",
            ],
            estimate=True,
            model="m17.11-structural-aut-shadow",
        )
        fixtures.append(fx)
        diagnostics[g.title] = sf

    bookmaker.attach_prices(fixtures, issues)
    steam_state = soccer_steam.assess(fixtures, now=now)

    # Persist ONLY predictions/quotes for forward evaluation.
    sql_store.sync_scan(fixtures, [])

    entries = []
    for fx in fixtures:
        for side, label in (
            ("home", f"{fx.game.home.name} Sieg"),
            ("draw", "Unentschieden"),
            ("away", f"{fx.game.away.name} Sieg"),
        ):
            offer = _best_exec(fx, side)
            if not offer:
                continue
            p = float(fx.probs[side])
            ev = p * float(offer.odds) - 1.0
            edge = p - 1.0 / float(offer.odds)
            st = steam_state.get((fx.game.title, side))
            clv = float((st or {}).get("clv_to_sharp") or 0.0)
            status = _status(ev, clv, st)
            entries.append((status, ev + max(clv, 0), fx, side, label, offer, st, ev, edge, clv))

    rank = {"SHADOW-PLAY": 0, "WATCH": 1, "PASS": 2}
    entries.sort(key=lambda x: (rank[x[0]], -x[1]))

    lines = [
        f"🇦🇹 M17.11-STRUCTURAL SHADOW · {friday:%d.%m.}–{sunday:%d.%m.%Y}",
        "Nur Österreich Bundesliga · Fair zuerst · Markt/Steam danach",
        "Kein Portugal-Classifier-Transfer, kein offizieller PLAY.",
        "",
        f"xG-Quelle: {snapshots[0].source} · {len(snapshots)} Teams",
        f"SoccerSTATS Home/Away: {len(venue_rows)} Teams",
        f"Spiele modelliert: {len(fixtures)}/6",
    ]

    for fx in sorted(fixtures, key=lambda z: z.game.kickoff):
        sf = diagnostics[fx.game.title]
        lines += [
            "",
            f"⚽ {report._kick(fx.game.kickoff.isoformat())} · {fx.game.title}",
            f"FAIR 1/X/2: {1/fx.probs['home']:.2f} / {1/fx.probs['draw']:.2f} / {1/fx.probs['away']:.2f}",
            f"xG STRUCTURAL: {sf.home_xg:.2f}:{sf.away_xg:.2f} "
            f"(fast {sf.home_fast:.2f}:{sf.away_fast:.2f}; slow {sf.home_slow:.2f}:{sf.away_slow:.2f})",
            (
                f"SoccerSTATS Venue: {sf.home_venue:.2f}:{sf.away_venue:.2f} "
                f"| PPG H/A {sf.home_ppg:.2f}/{sf.away_ppg:.2f}"
                if sf.home_venue is not None and sf.away_venue is not None
                else "SoccerSTATS Venue: kein sauberes Team-Mapping"
            ),
            f"MARKT: {_market_line(fx)}",
        ]

    lines += ["", "📌 ENTRY-GATE"]
    shown = 0
    for status, _, fx, side, label, offer, st, ev, edge, clv in entries:
        if status == "PASS":
            continue
        shown += 1
        sharp = (st or {}).get("sharp_fair")
        lines += [
            f"{'🟢' if status == 'SHADOW-PLAY' else '🟡'} {status} · {fx.game.title}",
            f"➡️ {label} @ {float(offer.odds):.2f} ({offer.source})",
            f"Fair {1/float(fx.probs[side]):.2f} · "
            + (f"Pinnacle no-vig {float(sharp):.2f}" if sharp else "Pinnacle no-vig –"),
            f"EV {ev*100:+.1f}% · Edge {edge*100:+.1f}pp · "
            f"CLV-Case {clv*100:+.1f}% · {_steam_text(st)}",
        ]
    if not shown:
        lines.append("Keine Auswahl erfüllt aktuell Fair + ausführbaren Preis + CLV-Gate.")

    if issues:
        lines += ["", f"Interne Datenhinweise: {len(issues)}"]

    lines += [
        "",
        "STATUS: SHADOW. Erst Forward-Logloss/CLV entscheidet über Austria-Release.",
    ]
    return "\n".join(lines) + "\n"


def run(send: bool = False) -> int:
    txt = build()
    print(txt)
    if not send:
        return 0
    r = telegram.send(txt)
    if not r["sent"]:
        print(f"Telegram: NICHT gesendet – {r['error']}")
        return 2
    print(f"Telegram: gesendet, message_id {r['message_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(send=False))
