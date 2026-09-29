"""Deutscher CEO-Bericht und Telegram-Text."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .selection import Candidate

_TZ = ZoneInfo("Europe/Berlin")
_WD = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
_LEAGUES = {"bundesliga": "Bundesliga", "2bundesliga": "2. Bundesliga",
            "austria": "Österr. Bundesliga", "ucl": "Champions League",
            "uel": "Europa League", "uecl": "Conference League",
            "nations": "UEFA Nations League", "del": "DEL", "nl": "National League (CH)",
            "shl": "SHL", "liiga": "Liiga", "khl": "KHL", "icehl": "ICE Hockey League", "epl": "Premier League",
            "laliga": "La Liga", "seriea": "Serie A", "nfl": "NFL", "nhl": "NHL", "nba": "NBA"}


def _pct(x: float) -> str:
    return f"{x * 100:.1f} %".replace(".", ",")


def _q(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def _eh(x: float) -> str:
    return _q(x).rstrip("0").rstrip(",")


def _league(code: str) -> str:
    return _LEAGUES.get(code, code.upper())


def _kick(iso: str) -> str:
    """ISO-Anstoß (UTC) -> 'Sa 11.10. 17:30 MESZ' in deutscher Zeit."""
    try:
        t = datetime.fromisoformat(iso).astimezone(_TZ)
    except (TypeError, ValueError):
        return iso or "Anstoß unbekannt"
    tz = {"CEST": "MESZ", "CET": "MEZ"}.get(t.tzname(), t.tzname())
    return f"{_WD[t.weekday()]} {t:%d.%m. %H:%M} {tz}"


def _head(c: Candidate) -> str:
    return " · ".join(x for x in (_league(c.league) if c.league else "", _kick(c.kickoff)) if x)


def _pick_lines(i: int, c: Candidate) -> list[str]:
    tag = " (Schätzung)" if c.estimate else ""
    liq = f", Ask-Tiefe ≈ {c.liquidity:,.0f} $".replace(",", ".") if c.liquidity else ""
    return [
        f"{i}. ✅ **PLAY**: **{c.event}** ({_head(c)}): {c.selection}{tag}",
        f"   Preis {_q(c.odds)} ({c.source}, inkl. Gebühr{liq}) | fair {_q(c.fair_odds)} "
        f"({_pct(c.p_final or c.p_model)}) | spielbar ab {_q(c.min_odds)} | "
        f"Edge {_pct(c.edge)} | EV {_pct(c.ev)} | Einsatz {_eh(c.stake_eh)} EH",
        f"   Begründung: {c.reason}",
    ]


def ceo_report(stand: str, picks: list[Candidate], scanned: int,
               data_issues: list[str], notes: list[str] | None = None,
               fixtures: list | None = None, watch: list[Candidate] | None = None) -> str:
    lines = [f"# Sportanalyse – Stand {stand}", ""]
    lines.append(f"Bewertete Spiele: {scanned}. PLAY, sobald der verifizierte Preis die "
                 f"spielbare Mindestquote (EV ≥ 3 %) erreicht und kein Newsvorbehalt offen ist.")
    lines += ["", "## CEO-Entscheidung"]
    if not picks:
        lines.append("⛔ **NO PLAY**: kein belegter Vorteil nach Gebühren/Marge.")
    for i, c in enumerate(picks, 1):
        lines += _pick_lines(i, c)
    if watch:
        lines += ["", "## WATCH (nicht freigegeben)"]
        for c in watch:
            why = "; ".join(c.flags or []) or "Quote unter spielbar ab"
            lines.append(f"- 👀 WATCH {c.event} ({_head(c)}): {c.selection} @ {_q(c.odds)} | fair {_q(c.fair_odds)} "
                         f"| spielbar ab {_q(c.min_odds)} | EV {_pct(c.ev)}. Grund: {why}")
    if fixtures:
        lines += ["", "## Faire Preise (Modell → Entscheidung)", "",
                  "| Liga | Spiel | Anstoß (UTC) | Modell H/X/A | Referenz | Kalshi Ask | Kennzahlen |",
                  "|---|---|---|---|---|---|---|"]
        for fx in sorted(fixtures, key=lambda f: (f.league, f.game.kickoff)):
            ks = list(fx.probs)
            mod = " / ".join(_pct(fx.probs[k]) for k in ks)
            ref = " / ".join(_pct(fx.ref_probs[k]) for k in ks) if fx.ref_probs else "–"
            ka = " / ".join(f"{fx.kalshi[k].yes_ask * 100:.0f}¢" if k in fx.kalshi else "–"
                            for k in ks) if fx.kalshi else "–"
            lines.append(f"| {fx.league} | {fx.game.title} | {fx.game.kickoff:%d.%m. %H:%M} | "
                         f"{mod} | {ref} | {ka} | {fx.detail} |")
    if data_issues:
        lines += ["", "## Datenlage (ungelöst)"] + [f"- {i}" for i in data_issues]
    if notes:
        lines += ["", "## Hinweise"] + [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"


def telegram_text(stand: str, picks: list[Candidate], watch: list[Candidate] | None = None) -> str:
    if not picks:
        out = [f"📊 CEO-Update {stand}", "⛔ NO PLAY: kein belegter Vorteil."]
    else:
        out = [f"📊 CEO-Freigaben {stand}"]
        for c in picks:
            tag = "\n   ⚠️ Schätzung" if c.estimate else ""
            out += ["", f"✅ PLAY · {_head(c)}", f"🆚 {c.event}",
                    f"➡️ {c.selection} @ {_q(c.odds)} ({c.source})",
                    f"   fair {_q(c.fair_odds)} | min {_q(c.min_odds)} | EV {_pct(c.ev)} | "
                    f"{_eh(c.stake_eh)} EH{tag}"]
    if watch:
        out += ["", "👀 WATCH (nicht freigegeben)"]
        for c in watch[:5]:
            why = "; ".join(c.flags or []) or "Quote unter spielbar ab"
            out += ["", f"• {_head(c)}", f"🆚 {c.event}",
                    f"➡️ {c.selection} @ {_q(c.odds)} | spielbar ab {_q(c.min_odds)} | EV {_pct(c.ev)}",
                    f"   Grund: {why}"]
    return "\n".join(out)
