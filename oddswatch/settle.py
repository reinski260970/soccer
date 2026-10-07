"""Settle published PLAYs and keep legacy CSV journals intact."""
from .journal import Journal


def settle_all(j: Journal) -> list[str]:
    log = []

    # New SQL path: every PLAY is evaluated internally. ESPN-backed leagues
    # settle automatically; unsupported markets remain pending rather than guessed.
    try:
        from . import sql_store
        shadow = sql_store.settle_shadow_predictions()
        r = sql_store.settle_pending()
        synced = sql_store.sync_settled_to_journal(j)
        s = sql_store.summary()
        roi = "–" if s["roi"] is None else f"{s['roi'] * 100:+.1f}%"
        clv = "–" if s["avg_clv"] is None else f"{s['avg_clv'] * 100:+.1f}%"
        log.append(
            f"SQL Shadow: {shadow['settled_events']} Events neu abgerechnet, "
            f"{shadow['pending']} offen, {shadow['unsupported']} nicht unterstützt, "
            f"{shadow['errors']} Fehler"
        )
        log.append(
            f"SQL PLAYs: {r['settled']} neu abgerechnet, "
            f"{r['pending_or_unsupported']} offen/noch nicht unterstützt, {r['errors']} Fehler; "
            f"{synced} CSV-Zeilen synchronisiert"
        )
        log.append(
            f"SQL Bilanz: {s['settled']}/{s['plays']} abgerechnet, "
            f"Einsatz {s['stake_eh']:.2f} EH, G/V {s['pnl_eh']:+.2f} EH, "
            f"ROI {roi}, Ø CLV {clv}"
        )
    except Exception as exc:
        log.append(f"SQL-Auswertung nicht verfügbar: {type(exc).__name__}: {exc}")

    # Legacy CSV remains for current reporting and Sharpery compatibility.
    for name in ("valuebets", "placed"):
        pending = sum(not r.get("result") for r in j.read(name))
        if pending:
            log.append(
                f"{name}: {pending} offene CSV-Einträge; SQL ist die automatische "
                "Auswertung, CSV bleibt Kompatibilitäts-/Exportpfad."
            )
        s = j.summary(name)
        log.append(
            f"Bilanz {name}: {s['settled']} abgerechnet, Einsatz {s['stake_eh']:.2f} EH, "
            f"G/V {s['pnl_eh']:+.2f} EH"
        )
    return log
