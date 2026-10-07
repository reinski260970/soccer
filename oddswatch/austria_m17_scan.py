"""Austria-only M17.11 structural shadow scan."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import bookmaker, fetch, matching, report, soccer_steam, sql_store, telegram
from .m17_at_shadow import fit
from .scan import Fixture
from .sources import espn, football_data, soccerstats, xg_external

TZ = ZoneInfo("Europe/Vienna")
MIN_EV = 0.03
MIN_CLV = 0.01


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


def _load_model():
    text, err = fetch.get(football_data.AUT_URL, cache_days=0)
    if text is None:
        raise RuntimeError(f"AUT history unavailable: {err}")
    matches, _ = football_data.parse_new_league(text)
    # Only completed matches strictly before today enter the live model.
    today = datetime.now(TZ).date()
    matches = [m for m in matches if m.date < today]
    return fit(matches)


def _best_exec(fx: Fixture, side: str):
    offers = fx.offers.get(side, [])
    return max(offers, key=lambda o: o.odds) if offers else None


def _status(p: float, odds: float, steam_row: dict | None) -> tuple[str, float, float, float]:
    ev = p * odds - 1.0
    sharp_fair = float((steam_row or {}).get("sharp_fair") or 0.0)
    clv = (odds / sharp_fair - 1.0) if sharp_fair > 1.0 else 0.0
    sig = (steam_row or {}).get("signal")
    if sig and sig.get("direction") == "DRIFTING":
        return "PASS", ev, clv, max((1.0 + MIN_EV) / p, sharp_fair * (1.0 + MIN_CLV))
    playable = max(
        (1.0 + MIN_EV) / p,
        sharp_fair * (1.0 + MIN_CLV) if sharp_fair > 1.0 else 0.0,
    )
    if ev >= MIN_EV and clv >= MIN_CLV:
        return "SHADOW-PLAY", ev, clv, playable
    if ev > 0 and clv > 0:
        return "WATCH", ev, clv, playable
    return "PASS", ev, clv, playable


def _steam_text(row: dict | None) -> str:
    if not row:
        return "NO_STEAM_DATA"
    sig = row.get("signal")
    if sig:
        move = float(sig.get("lead_move") or 0.0) * 100
        mins = int(sig.get("minutes") or 0)
        if sig.get("direction") == "SHORTENING":
            return f"STEAM+ Pin {move:+.1f}pp/{mins}m"
        return f"STEAM- Pin {move:+.1f}pp/{mins}m"
    gap = float(row.get("gap") or 0.0) * 100
    if gap >= 0.8:
        return f"SHARP_GAP+ {gap:+.1f}pp"
    if gap <= -0.8:
        return f"SHARP_GAP- {gap:+.1f}pp"
    return "NEUTRAL"


def build(today: date | None = None) -> tuple[str, list[Fixture]]:
    friday, sunday = _next_weekend(today)
    model = _load_model()
    issues: list[str] = []

    games, errs = espn.upcoming("austria", friday, 2)
    issues.extend(errs)
    games = [
        g for g in games
        if g.status == "STATUS_SCHEDULED"
        and friday <= g.kickoff.astimezone(TZ).date() <= sunday
    ]

    ext_xg = []
    try:
        ext_xg, xerr = xg_external.snapshot("AUT", datetime.now(timezone.utc))
        if xerr:
            issues.append(f"xG: {xerr}")
    except Exception as exc:
        issues.append(f"xG: {type(exc).__name__}")

    try:
        ss, serr = soccerstats.league_context("AUT")
        if serr:
            issues.append(f"SoccerSTATS: {serr}")
    except Exception:
        ss = None

    model_teams = model.teams()
    xg_names = [r.team for r in ext_xg]
    xg_by_name = {r.team: r for r in ext_xg}

    fixtures: list[Fixture] = []
    for g in games:
        h = matching.find(g.home.name, model_teams) or matching.find(g.home.short, model_teams)
        a = matching.find(g.away.name, model_teams) or matching.find(g.away.short, model_teams)
        if not h or not a:
            issues.append(f"Team mapping failed: {g.title}")
            continue
        probs, meta = model.predict(h, a, g.kickoff.date())

        context = [
            f"M17.11-AT structural fast {meta['home_fast']:.2f}:{meta['away_fast']:.2f}",
            f"slow {meta['home_slow']:.2f}:{meta['away_slow']:.2f}",
            f"history n {meta['home_n']}/{meta['away_n']}",
        ]

        if ext_xg:
            eh = matching.find(g.home.name, xg_names) or matching.find(h, xg_names)
            ea = matching.find(g.away.name, xg_names) or matching.find(a, xg_names)
            if eh and ea:
                xh, xa = xg_by_name[eh], xg_by_name[ea]
                hs = xh.xg_home if xh.xg_home is not None else xh.xg
                hga = xh.xga_home if xh.xga_home is not None else xh.xga
                aas = xa.xg_away if xa.xg_away is not None else xa.xg
                aga = xa.xga_away if xa.xga_away is not None else xa.xga
                context.append(
                    f"aktuelles externes xG Kontext: {h} {hs:.2f}/{hga:.2f} Heim | "
                    f"{a} {aas:.2f}/{aga:.2f} Auswärts"
                )

        if ss and ss.goals_per_match is not None:
            context.append(f"SoccerSTATS Liga {ss.goals_per_match:.2f} Tore/Spiel")

        fixtures.append(Fixture(
            league="austria",
            sport="soccer",
            game=g,
            probs=probs,
            detail=(
                f"M17.11-AT shadow · CV LL {model.cv_logloss:.4f} "
                f"(folds {','.join(f'{x:.4f}' for x in model.fold_logloss)})"
            ),
            context=context,
            estimate=True,
            model="m17.11-at-shadow",
        ))

    bookmaker.attach_prices(fixtures, issues)
    steam_state = soccer_steam.assess(fixtures, now=datetime.now(timezone.utc))

    # Persist every shadow probability + quote, but never create an official PLAY.
    sql_store.sync_scan(fixtures, [])

    lines = [
        f"🇦🇹 M17.11-AT SHADOW · {friday:%d.%m.}–{sunday:%d.%m.%Y}",
        f"Historie {model.history_first:%d.%m.%Y}–{model.history_last:%d.%m.%Y} · "
        f"{model.samples} Trainingszeilen · CV Logloss {model.cv_logloss:.4f}",
        "Fair unabhängig vom Markt · aktuelles xG nur Kontext · kein Sharpery-PLAY",
    ]

    entries = []
    for fx in sorted(fixtures, key=lambda z: z.game.kickoff):
        lines += [
            "",
            f"⚽ {report._kick(fx.game.kickoff.isoformat())} · {fx.game.title}",
            f"FAIR 1/X/2 {1/fx.probs['home']:.2f} / {1/fx.probs['draw']:.2f} / {1/fx.probs['away']:.2f}",
        ]
        for side, label in (("home", "1"), ("draw", "X"), ("away", "2")):
            o = _best_exec(fx, side)
            row = steam_state.get((fx.game.title, side))
            if not o:
                continue
            status, ev, clv, playable = _status(fx.probs[side], o.odds, row)
            sharp = float((row or {}).get("sharp_fair") or 0.0)
            selection = (
                fx.game.home.name if side == "home"
                else "Unentschieden" if side == "draw"
                else fx.game.away.name
            )
            lines.append(
                f"{label}: Markt {o.odds:.2f} {o.source} | "
                f"Pin no-vig {sharp:.2f}" if sharp else
                f"{label}: Markt {o.odds:.2f} {o.source} | Pin no-vig –"
            )
            entries.append((status, ev + max(clv, 0), fx, side, selection, o, row, ev, clv, playable))

    entries.sort(key=lambda x: ({"SHADOW-PLAY":0, "WATCH":1, "PASS":2}[x[0]], -x[1]))
    lines += ["", "📌 ENTRY-GATE"]
    shown = 0
    for status, _, fx, side, selection, o, row, ev, clv, playable in entries:
        if status == "PASS":
            continue
        shown += 1
        sharp = float((row or {}).get("sharp_fair") or 0.0)
        lines += [
            f"{'🟢' if status == 'SHADOW-PLAY' else '🟡'} {status} · {fx.game.title}",
            f"➡️ {selection} @ {o.odds:.2f} ({o.source})",
            f"Fair {1/fx.probs[side]:.2f} · Pin no-vig {sharp:.2f} · "
            f"EV {ev*100:+.1f}% · CLV-Case {clv*100:+.1f}%",
            f"{_steam_text(row)} · spielbar ab {playable:.2f}",
        ]
    if not shown:
        lines.append("Keine Auswahl erfüllt aktuell Fair + Markt + CLV-Gate.")

    lines += [
        "",
        "PLAY-Logik: EV >= 3% + CLV-Case >= 1% + kein bestätigter STEAM−.",
        "Pin no-vig ist aktuell Close-Proxy, keine erfundene Closing-Line-Prognose.",
    ]
    if issues:
        lines += ["", f"Datenhinweise intern: {len(issues)}"]
    return "\n".join(lines) + "\n", fixtures


def run(*, send: bool = False) -> int:
    text, _ = build()
    print(text)
    if not send:
        return 0
    r = telegram.send(text)
    if not r["sent"]:
        print(f"Telegram: NICHT gesendet – {r['error']}")
        return 2
    print(f"Telegram: gesendet, message_id {r['message_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(send=True))
