"""Deutscher CEO-Bericht und Telegram-Text."""

from __future__ import annotations

from .selection import Candidate


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _q(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def ceo_report(stand: str, picks: list[Candidate], scanned: int,
               data_issues: list[str], notes: list[str] | None = None) -> str:
    lines = [f"# Sportanalyse – Stand {stand}", ""]
    lines.append(f"Gescannte Spiele mit Preis und Modell: {scanned}")
    if data_issues:
        lines += ["", "## Datenlage (ungelöst)"] + [f"- {i}" for i in data_issues]
    lines += ["", "## Entscheidung"]
    if not picks:
        lines.append("Kein Trade: kein belegter Vorteil nach Gebühren/Marge.")
    for i, c in enumerate(picks, 1):
        tag = " (Schätzung)" if c.estimate else ""
        liq = f", Liquidität {c.liquidity:,.0f} $" if c.liquidity else ""
        lines += [
            f"{i}. **{c.event}** – {c.selection}{tag}",
            f"   Preis {_q(c.odds)} ({c.source}{liq}) | fair {_q(c.fair_odds)} "
            f"({_pct(c.p_model)}) | spielbar ab {_q(c.min_odds)} | "
            f"Edge {_pct(c.edge)} | EV {_pct(c.ev)} | Einsatz {c.stake_eh:g} EH",
            f"   Begründung: {c.reason}",
        ]
    if notes:
        lines += ["", "## Hinweise"] + [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"


def telegram_text(stand: str, picks: list[Candidate]) -> str:
    if not picks:
        return f"📊 Update {stand}\nKein Trade – kein belegter Vorteil."
    out = [f"📊 Value-Kandidaten {stand}"]
    for c in picks:
        tag = " ⚠️Schätzung" if c.estimate else ""
        out.append(f"• {c.event}: {c.selection} @ {_q(c.odds)} ({c.source}) | "
                   f"fair {_q(c.fair_odds)} | min {_q(c.min_odds)} | "
                   f"{c.stake_eh:g} EH{tag}")
    return "\n".join(out)
