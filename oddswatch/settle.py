"""Nachkontrolle: Kalshi-Ergebnisse abrufen, Wetten abrechnen, CLV berechnen.

Closing Line = letzter eigener Kalshi-Snapshot vor Anstoß (data/snapshots),
de-vigged über alle Outcomes des Events (Mittelkurse). Ohne Snapshot vor
Anstoß bleibt der CLV leer statt geschätzt.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .journal import Journal
from .sources import kalshi


def closing_fair_odds(ticker: str, root: str = "data/snapshots") -> float | None:
    rows = []
    for p in sorted(Path(root).glob("kalshi-*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    mine = [r for r in rows if r["ticker"] == ticker]
    if not mine:
        return None
    ev, ko = mine[0]["event_ticker"], datetime.fromisoformat(mine[0]["kickoff"])
    pre = [r for r in rows if r["event_ticker"] == ev
           and datetime.fromisoformat(r["observed_at"].replace("Z", "+00:00")) <= ko]
    if not pre:
        return None
    last_obs = max(r["observed_at"] for r in pre)
    snap = {r["ticker"]: r for r in pre if r["observed_at"] == last_obs}
    if ticker not in snap:
        return None
    mids = {t: ((r["bid"] + r["ask"]) / 2 if r["bid"] > 0 else r["ask"]) for t, r in snap.items()}
    s = sum(mids.values())
    p = mids[ticker] / s if s else 0
    return 1 / p if p > 0 else None


def settle_all(j: Journal) -> list[str]:
    log = []
    for name in ("valuebets", "placed"):
        done: set[tuple[str, str]] = set()
        for r in j.read(name):
            if r.get("result") or not r.get("ref", "").startswith("KX"):
                continue
            if (r["ref"], r["market"]) in done:
                continue
            done.add((r["ref"], r["market"]))
            m, err = kalshi.fetch_market(r["ref"])
            if err or not m:
                log.append(f"{name}: {r['event']} – Abruf fehlgeschlagen ({err})")
                continue
            res = (m.get("result") or "").lower()
            if res not in ("yes", "no"):
                log.append(f"{name}: {r['event']} – offen (Status {m.get('status')})")
                continue
            # Importierte Kalshi-Fills führen die gekaufte Seite (yes/no) als market
            side = r["market"] if r["market"] in ("yes", "no") else "yes"
            won = res == side
            cfo = closing_fair_odds(r["ref"])
            if cfo and side == "no":
                cfo = 1 / (1 - 1 / cfo) if cfo > 1 else None
            n = j.settle(name, r["event"], r["market"], won, cfo, ref=r["ref"])
            log.append(f"{name}: {r['event']} {r['selection']} -> {'Gewinn' if won else 'Verlust'}"
                       + (f", Closing fair {cfo:.2f}" if cfo else ", kein Closing-Snapshot")
                       + f" ({n} Zeile/n)")
    for name in ("valuebets", "placed"):
        s = j.summary(name)
        clv = f"{s['avg_clv'] * 100:+.1f} % (n={s['clv_n']})" if s["avg_clv"] is not None else "–"
        log.append(f"Bilanz {name}: {s['settled']} abgerechnet, Einsatz {s['stake_eh']:.2f} EH, "
                   f"G/V {s['pnl_eh']:+.2f} EH, ROI {s['roi'] * 100:+.1f} %, Ø CLV {clv}")
    return log
