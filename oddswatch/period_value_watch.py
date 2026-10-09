"""Fast Bet365 period-total Value audit.

Runs independently from the heavier full-game scanner. It evaluates period
totals directly from historical ESPN linescores (NBA/NFL/NHL) and the existing
European-hockey first-period model, persists WATCH/CLV rows in Neon, and sends
only new confirmed values through the shared persistent Telegram dedupe.
"""

from __future__ import annotations

from . import telegram
from .surebet_values import (
    _fetch_candidate_values,
    _is_independent_period_total,
    _period_kind,
    audit_values,
    telegram_actionable_text,
)


def _fast_period_candidate(v) -> bool:
    if (v.bet_type or "").strip() not in {"over", "under"}:
        return False
    base = (v.base or "overall").casefold()
    if base not in {"overall", "total", "match", ""}:
        return False
    if _is_independent_period_total(v):
        return True
    # European hockey already has an independent 1st-period Poisson path.
    return v.sport == "Hockey" and _period_kind(v) == "p1"


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
            persist_audits,
        )
        sql_status = persist_audits(audits, fixtures=[])
    except Exception as exc:
        sql_status = {"error": f"{type(exc).__name__}: {exc}"}

    counts = {}
    for a in audits:
        counts[a.status] = counts.get(a.status, 0) + 1

    lines = [
        f"Period-Value-Watch: {len(values)} Kandidat(en)",
        "Audit: " + (
            ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
            if counts else "kein Perioden-Kandidat"
        ),
        "CLV-Tracking: " + ", ".join(f"{k}={v}" for k, v in sql_status.items()),
    ]
    if warnings:
        lines.append("Feed-Hinweise: " + " | ".join(warnings))

    if send:
        try:
            fresh, dedupe = filter_unsent_actionable(audits)
        except Exception as exc:
            lines.append(f"Telegram: NICHT gesendet – Dedupe-Fehler {type(exc).__name__}: {exc}")
            return lines

        txt = telegram_actionable_text(fresh)
        if not txt:
            if dedupe.get("duplicate"):
                lines.append(
                    f"Telegram: nicht gesendet – {dedupe['duplicate']} Value(s) bereits gemeldet"
                )
            else:
                lines.append("Telegram: nicht gesendet – kein neuer bestätigter Perioden-Value")
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
    for line in run(send=False):
        print(line)
