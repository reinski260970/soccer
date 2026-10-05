"""Bestehende Journale erhalten; keine Ergebnisabrufe bei entfernten Anbietern."""
from .journal import Journal


def settle_all(j: Journal) -> list[str]:
    log = []
    for name in ("valuebets", "placed"):
        pending = sum(not r.get("result") for r in j.read(name))
        if pending:
            log.append(f"{name}: {pending} offene Einträge; automatische Ergebnisquelle nicht angebunden. Manuelle Prüfung erforderlich.")
        s = j.summary(name)
        log.append(f"Bilanz {name}: {s['settled']} abgerechnet, Einsatz {s['stake_eh']:.2f} EH, G/V {s['pnl_eh']:+.2f} EH")
    return log
