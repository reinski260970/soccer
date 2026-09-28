"""Tagesbericht für Telegram: Auswertung (letzte 24 h), Profit-Status, Ausblick.

Profit wird getrennt ausgewiesen: 'valuebets' = alle Freigaben mit Modell-
einsatz (Papier-Portfolio), 'placed' = tatsächlich gespielte Wetten.
1 EH = ODDSWATCH_EH_USD Dollar (Default 10).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from .journal import Journal
from .report import _eh, _head, _kick, _league, _pct, _q
from .selection import Candidate

_RES = {"win": "✅ Gewinn", "loss": "❌ Verlust", "void": "↩️ Void"}


def _ko(r: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(r.get("kickoff", "")).astimezone(timezone.utc)
    except ValueError:
        return None


def _f(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _status(rows: list[dict], eh_usd: float) -> list[str]:
    done = [r for r in rows if r.get("result")]
    open_ = [r for r in rows if not r.get("result")]
    stake = sum(_f(r["stake_eh"]) for r in done if r["result"] != "void")
    pnl = sum(_f(r.get("pnl_eh")) for r in done)
    wins = sum(r["result"] == "win" for r in done)
    decided = sum(r["result"] in ("win", "loss") for r in done)
    clvs = [_f(r["clv"]) for r in done if r.get("clv")]
    risk = sum(_f(r["stake_eh"]) for r in open_)
    out = [f"   G/V {pnl:+.2f} EH ({pnl * eh_usd:+.2f} $) | Einsatz {_eh(stake) or '0'} EH | "
           f"ROI {_pct(pnl / stake) if stake else '–'}",
           f"   Bilanz {wins}-{decided - wins} ({len(done)} abgerechnet) | "
           f"Ø CLV {f'{sum(clvs) / len(clvs) * 100:+.1f} % (n={len(clvs)})' if clvs else '–'}",
           f"   Offen: {len(open_)} Wetten, {_eh(risk) or '0'} EH im Risiko"]
    return out


def _odds(r: dict) -> float:
    return _f(r.get("odds") or r.get("odds_taken"))


def daily_text(j: Journal, now: datetime | None = None, eh_usd: float | None = None,
               picks: list[Candidate] | None = None, watch: list[Candidate] | None = None,
               horizon_days: int = 7) -> str:
    now = now or datetime.now(timezone.utc)
    eh_usd = eh_usd or float(os.environ.get("ODDSWATCH_EH_USD", "10"))
    vb, placed = j.read("valuebets"), j.read("placed")
    out = [f"🗞 Tagesbericht {_kick(now.isoformat())}"]

    # Auswertung: abgerechnete Wetten mit Anstoß in den letzten 24 h
    out += ["", "📋 AUSWERTUNG (letzte 24 h)"]
    recent = [(n, r) for n, rows in (("Freigabe", vb), ("Gespielt", placed)) for r in rows
              if r.get("result") and (k := _ko(r)) and now - timedelta(hours=24) <= k <= now]
    if not recent:
        out.append("   Keine abgerechneten Wetten.")
    for n, r in recent:
        pnl = _f(r.get("pnl_eh"))
        clv = f" | CLV {_f(r['clv']) * 100:+.1f} %" if r.get("clv") else ""
        out += [f"• {_league(r.get('league', '')) + ' · ' if r.get('league') else ''}"
                f"{_kick(r['kickoff'])} ({n})",
                f"🆚 {r['event']}",
                f"➡️ {r['selection']} @ {_q(_odds(r))} → {_RES.get(r['result'], r['result'])} "
                f"{pnl:+.2f} EH{clv}"]
    pending = [r for r in vb + placed if not r.get("result") and (k := _ko(r)) and k <= now]
    if pending:
        out.append(f"   ⏳ {len(pending)} gespielt, aber noch nicht abgerechnet")

    # Profit-Status
    out += ["", "💰 PROFIT-STATUS (gesamt)", "📈 Freigaben (Modell-Portfolio)"] + _status(vb, eh_usd)
    out.append("🎯 Gespielte Wetten")
    out += _status(placed, eh_usd) if placed else ["   Noch keine Wetten verbucht (Kalshi-Fills: import-fills)"]

    # Ausblick: offene Freigaben + aktuelle Watchlist
    out += ["", f"🔭 AUSBLICK (nächste {horizon_days} Tage)"]
    until = now + timedelta(days=horizon_days)
    seen: set[tuple[str, str]] = set()
    upcoming = []
    for r in vb + placed:
        k = _ko(r)
        key = (r["event"], r["market"])
        if r.get("result") or not k or not now < k <= until or key in seen:
            continue
        seen.add(key)
        upcoming.append((k, r))
    for c in picks or []:
        if (c.event, c.market) not in seen:
            seen.add((c.event, c.market))
            upcoming.append((_ko(c.as_row()) or until, c.as_row()))
    if not upcoming:
        out.append("   Keine offenen Freigaben.")
    for _, r in sorted(upcoming, key=lambda x: x[0]):
        out += [f"✅ {_league(r.get('league', '')) + ' · ' if r.get('league') else ''}{_kick(r['kickoff'])}",
                f"🆚 {r['event']}",
                f"➡️ {r['selection']} @ {_q(_odds(r))} | {_eh(_f(r['stake_eh']))} EH"]
    if watch:
        out += ["", "👀 Watchlist"]
        for c in watch[:5]:
            out += [f"• {_head(c)}", f"🆚 {c.event}",
                    f"➡️ {c.selection} spielbar ab {_q(c.min_odds)} (jetzt {_q(c.odds)})"]
    return "\n".join(out)


def news_key(j: Journal, picks: list[Candidate] | None = None,
             watch: list[Candidate] | None = None) -> str:
    """Fingerabdruck des berichtsrelevanten Inhalts ohne Zeitstempel und
    laufende Kursbewegungen: Ergebnisse, offene Freigaben, Watchlist-Einträge."""
    import hashlib
    import json
    rows = j.read("valuebets") + j.read("placed")
    key = {
        "settled": sorted(f"{r['event']}|{r['market']}|{r.get('ref', '')}|{r['result']}"
                          for r in rows if r.get("result")),
        "open": sorted({f"{r['event']}|{r['market']}" for r in rows if not r.get("result")}
                       | {f"{c.event}|{c.market}" for c in picks or []}),
        "watch": sorted(f"{c.event}|{c.market}" for c in (watch or [])[:5]),
    }
    return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:16]
