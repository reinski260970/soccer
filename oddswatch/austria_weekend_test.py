"""Austria-only weekend shadow scan.

Scope is deliberately restricted to the Austrian Bundesliga. No other leagues,
sports or models are queried.

Fair probabilities are computed first. Market prices are attached only after
the model output exists. Steam/CLV is an entry layer, never a model feature.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import bookmaker, matching, report, soccer_steam, sql_store, telegram
from .scan import (
    Fixture,
    _aut_model,
    _devig_ref,
    _form,
    _rest_days,
    _xg_line,
    evaluate_fixture,
)
from .sources import espn, soccerstats, xg_external

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
        direction = sig.get("direction")
        if direction == "SHORTENING":
            return (
                f"STEAM+ Pinnacle {float(sig.get('lead_move') or 0)*100:+.1f}pp/"
                f"{int(sig.get('minutes') or 0)}m"
            )
        return (
            f"STEAM- Pinnacle {float(sig.get('lead_move') or 0)*100:+.1f}pp/"
            f"{int(sig.get('minutes') or 0)}m"
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


def build(today: date | None = None):
    friday, sunday = _next_weekend(today)
    issues: list[str] = []
    model, ms = _aut_model(issues)
    if model is None:
        raise RuntimeError("Austria-Modell konnte nicht geladen werden")

    games, errs = espn.upcoming("austria", friday, 2)
    issues += errs
    games = [
        g for g in games
        if g.status == "STATUS_SCHEDULED"
        and friday <= g.kickoff.astimezone(TZ).date() <= sunday
    ]

    ext_xg = []
    try:
        now = datetime.now(timezone.utc)
        ext_xg, err = xg_external.snapshot("AUT", now)
        if err:
            issues.append(f"Externes xG AUT: {err}")
        if ext_xg:
            xg_external.persist_snapshot("AUT", ext_xg, now)
    except Exception as exc:
        issues.append(f"Externes xG AUT: {type(exc).__name__}: {exc}")

    try:
        ss_ctx, ss_err = soccerstats.league_context("AUT")
        if ss_err:
            issues.append(f"SoccerSTATS AUT: {ss_err}")
    except Exception as exc:
        ss_ctx = None
        issues.append(f"SoccerSTATS AUT: {type(exc).__name__}: {exc}")

    teams = list(model.attack)
    fixtures: list[Fixture] = []
    for g in games:
        h = matching.find(g.home.name, teams) or matching.find(g.home.short, teams)
        a = matching.find(g.away.name, teams) or matching.find(g.away.short, teams)
        if not h or not a:
            issues.append(f"Team nicht zugeordnet: {g.title}")
            continue

        mk = model.markets(h, a, neutral=g.neutral)
        kd = g.kickoff.date()
        ctx = [
            f"Form {h} {_form(ms, h, kd)}, {a} {_form(ms, a, kd)}",
            f"Pause {_rest_days(ms, h, kd)}/{_rest_days(ms, a, kd)} Tage",
        ]
        ctx += [x for x in (_xg_line(ms, h, kd)[0], _xg_line(ms, a, kd)[0]) if x]

        if ext_xg:
            names = [r.team for r in ext_xg]
            eh = matching.find(g.home.name, names) or matching.find(h, names)
            ea = matching.find(g.away.name, names) or matching.find(a, names)
            by_name = {r.team: r for r in ext_xg}
            if eh and ea:
                xh, xa = by_name[eh], by_name[ea]
                hs = xh.xg_home if xh.xg_home is not None else xh.xg
                hga = xh.xga_home if xh.xga_home is not None else xh.xga
                aas = xa.xg_away if xa.xg_away is not None else xa.xg
                aga = xa.xga_away if xa.xga_away is not None else xa.xga
                ctx.append(
                    f"Externes xG: {h} {hs:.2f}/{hga:.2f} Heim | "
                    f"{a} {aas:.2f}/{aga:.2f} Auswärts"
                )

        if ss_ctx:
            bits = []
            if ss_ctx.goals_per_match is not None:
                bits.append(f"{ss_ctx.goals_per_match:.2f} Tore/Spiel")
            if ss_ctx.over25_pct is not None:
                bits.append(f"O2.5 {ss_ctx.over25_pct*100:.0f}%")
            if ss_ctx.btts_pct is not None:
                bits.append(f"BTTS {ss_ctx.btts_pct*100:.0f}%")
            if bits:
                ctx.append("SoccerSTATS: " + " | ".join(bits))

        fixtures.append(Fixture(
            "austria", "soccer", g,
            {"home": mk["1"], "draw": mk["X"], "away": mk["2"]},
            f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f}, O2.5 {mk['O2.5']*100:.0f}%",
            ctx,
            ref_probs=_devig_ref(g, three_way=True),
            estimate=True,
            model="poisson-baseline-austria",
        ))

    bookmaker.attach_prices(fixtures, issues)
    steam_state = soccer_steam.assess(fixtures, now=datetime.now(timezone.utc))

    candidates = [c for fx in fixtures for c in evaluate_fixture(fx, {})]
    soccer_steam.annotate_candidates(candidates, steam_state)

    # Shadow only: persist model predictions and odds, never official PLAYs.
    sql_store.sync_scan(fixtures, [])

    best = {}
    for c in candidates:
        key = (c.event, c.market)
        if key not in best or float(c.odds) > float(best[key].odds):
            best[key] = c

    ranked = []
    for key, c in best.items():
        row = steam_state.get(key)
        model_ev = float(c.p_model) * float(c.odds) - 1.0
        clv = float((row or {}).get("clv_to_sharp") or 0.0)
        status = _status(model_ev, clv, row)
        ranked.append((status, model_ev + max(clv, 0.0), c, row, model_ev, clv))
    ranked.sort(key=lambda x: ({"SHADOW-PLAY":0, "WATCH":1, "PASS":2}[x[0]], -x[1]))

    lines = [
        f"🇦🇹 ÖSTERREICH BUNDESLIGA TEST · {friday:%d.%m.}–{sunday:%d.%m.%Y}",
        "Nur Österreich · SHADOW · keine Sharpery-Freigabe",
        "",
        f"Spiele: {len(fixtures)}",
    ]

    for fx in sorted(fixtures, key=lambda x: x.game.kickoff):
        lines += [
            "",
            f"⚽ {report._kick(fx.game.kickoff.isoformat())} · {fx.game.title}",
            f"FAIR 1/X/2: {1/fx.probs['home']:.2f} / {1/fx.probs['draw']:.2f} / {1/fx.probs['away']:.2f}",
            f"MARKT: {_market_line(fx)}",
            f"{fx.detail}",
        ]

    lines += ["", "📌 ENTRY-GATE"]
    for status, _, c, row, model_ev, clv in ranked:
        if status == "PASS":
            continue
        sharp = (row or {}).get("sharp_fair")
        lines += [
            f"{'🟢' if status == 'SHADOW-PLAY' else '🟡'} {status} · {c.event}",
            f"➡️ {c.selection} @ {float(c.odds):.2f} ({c.source})",
            f"Modell fair {1/float(c.p_model):.2f} · "
            + (f"Pinnacle no-vig {float(sharp):.2f}" if sharp else "Pinnacle no-vig –"),
            f"Modell-EV {model_ev*100:+.1f}% · CLV-Case {clv*100:+.1f}% · {_steam_text(row)}",
        ]

    if not any(x[0] in {"SHADOW-PLAY", "WATCH"} for x in ranked):
        lines.append("Keine Auswahl erfüllt aktuell Fair + Markt + CLV-Gate.")

    lines += [
        "",
        "Hinweis: Austria-Live-Modell ist aktuell poisson-baseline-austria und bleibt ESTIMATE.",
        "M17.11 ist noch nicht als Austria-Live-Scorer aktiviert.",
        "Steam/Markt beeinflusst niemals die Fair Probability.",
    ]
    return "\n".join(lines) + "\n"


def run(send: bool = True) -> int:
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
    raise SystemExit(run())
