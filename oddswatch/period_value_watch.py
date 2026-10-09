"""Fast Bet365 period-total Value audit.

Runs independently from the heavier full-game scanner. It evaluates period
totals directly from historical ESPN linescores (NBA/NFL/NHL) and the existing
European-hockey first-period model, persists WATCH/CLV rows in Neon, and sends
only new confirmed values through the shared persistent Telegram dedupe.
"""

from __future__ import annotations

import argparse

from . import telegram
from .surebet_values import (
    _fetch_candidate_values,
    _period_watch_owned,
    audit_values,
)


def _fast_period_candidate(v) -> bool:
    return _period_watch_owned(v)


def _period_alert_text(audits, trends) -> str:
    rows = []
    for a in audits:
        from .sql import valuebet as vb
        trend = trends.get(vb._alert_key(a), {})
        if trend.get("direction") != "SHORTENING":
            continue
        rows.append((a, trend))
    if not rows:
        return ""

    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Europe/Vienna")
    out = [f"⚡ PERIOD-VALUE + STEAM · {datetime.now(tz):%d.%m.%Y %H:%M}"]
    for a, trend in rows[:20]:
        v = a.value
        kick = v.kickoff.astimezone(tz).strftime("%d.%m. %H:%M") if v.kickoff else "Zeit unbekannt"
        move = trend.get("move_pp")
        mins = trend.get("minutes")
        old_o = trend.get("old_odds")
        new_o = trend.get("new_odds")
        out += [
            "",
            f"✅ {v.tournament or v.sport} · {kick}",
            v.event,
            f"➡️ {v.selection} @ {v.odds:.2f} · Bet365",
            f"Markt: {v.market}",
            f"Unser Fair {a.our_fair:.2f} · EV {a.our_ev*100:+.1f}%",
            (
                f"STEAM+ Bet365 {old_o:.2f} → {new_o:.2f} · "
                f"impl. Δ {move:+.1f}pp"
                + (f" / {mins}m" if mins is not None else "")
            ),
            f"Modell: {a.note}",
        ]
    out += [
        "",
        "Gate: Modell-Value + exakter Periodenpreis SHORTENING.",
        "18+ · Keine Gewinn-Garantie.",
    ]
    return "\n".join(out)


def run(send: bool = False, limit: int = 200) -> list[str]:
    values, warnings, err = _fetch_candidate_values(limit)
    if err and not values:
        return [f"Period-Value-Watch: {err}"]

    values = [v for v in values if _fast_period_candidate(v)]
    audits = audit_values(values, fixtures=[])

    try:
        from .sql.valuebet import (
            filter_unsent_actionable,
            mark_actionable_sent,
            period_price_trends,
            persist_audits,
        )
        sql_status = persist_audits(audits, fixtures=[])
        trends = period_price_trends(audits)
    except Exception as exc:
        sql_status = {"error": f"{type(exc).__name__}: {exc}"}
        trends = {}

    counts = {}
    for a in audits:
        counts[a.status] = counts.get(a.status, 0) + 1

    trend_counts = {}
    from .sql import valuebet as vb
    for a in audits:
        direction = trends.get(vb._alert_key(a), {}).get("direction", "NO_HISTORY")
        trend_counts[direction] = trend_counts.get(direction, 0) + 1

    lines = [
        f"Period-Value-Watch: {len(values)} Kandidat(en)",
        "Audit: " + (
            ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            if counts else "kein Perioden-Kandidat"
        ),
        "Preisrichtung: " + (
            ", ".join(f"{k}={v}" for k, v in sorted(trend_counts.items()))
            if trend_counts else "keine History"
        ),
        "CLV-Tracking: " + ", ".join(f"{k}={v}" for k, v in sql_status.items()),
    ]
    if warnings:
        lines.append("Feed-Hinweise: " + " | ".join(warnings))

    if send:
        # Only confirmed model Values with favorable exact-market movement may
        # enter the period Telegram path. NO_HISTORY/NEUTRAL/DRIFTING stay WATCH.
        steam_pass = []
        for a in audits:
            trend = trends.get(vb._alert_key(a), {})
            if (
                a.status == "BESTÄTIGT"
                and a.our_ev is not None
                and a.our_ev >= 0.03
                and trend.get("direction") == "SHORTENING"
            ):
                steam_pass.append(a)
        try:
            fresh, dedupe = filter_unsent_actionable(steam_pass)
        except Exception as exc:
            lines.append(f"Telegram: NICHT gesendet – Dedupe-Fehler {type(exc).__name__}: {exc}")
            return lines

        txt = _period_alert_text(fresh, trends)
        if not txt:
            if dedupe.get("duplicate"):
                lines.append(
                    f"Telegram: nicht gesendet – {dedupe['duplicate']} Steam-Value(s) bereits gemeldet"
                )
            elif audits:
                lines.append("Telegram: nicht gesendet – kein neuer Perioden-Value mit STEAM+")
            else:
                lines.append("Telegram: nicht gesendet – kein Perioden-Kandidat")
            return lines

        r = telegram.send(txt)
        if r["sent"]:
            mark = mark_actionable_sent(fresh)
            lines.append(
                f"Telegram: gesendet, message_id {r['message_ids']} · "
                f"Dedupe gespeichert={mark.get('stored', 0)}"
            )
        else:
            lines.append(f"Telegram: NICHT gesendet – {r['error']}")

    return lines


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--send", action="store_true")
    p.add_argument("--limit", type=int, default=200)
    args = p.parse_args()
    for line in run(send=args.send, limit=args.limit):
        print(line)
