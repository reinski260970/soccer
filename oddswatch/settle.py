"""Nachkontrolle: Kalshi-Ergebnisse abrufen, Wetten abrechnen, CLV berechnen.

Closing Line = letzter eigener Kalshi-Snapshot vor Anstoß (data/snapshots),
de-vigged über alle Outcomes des Events (Mittelkurse). Ohne Snapshot vor
Anstoß bleibt der CLV leer statt geschätzt.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
    if "TOTAL" in ev or "SPREAD" in ev:
        p = mids[ticker]            # Linien-Leiter: jede Linie ist ein eigener Ja/Nein-Markt
    else:
        s = sum(mids.values())
        p = mids[ticker] / s if s else 0
    return 1 / p if p > 0 else None


def _fetch_event(event_ticker: str) -> tuple[dict | None, str | None]:
    from . import fetch
    return fetch.get_json(f"{kalshi.API}/events/{event_ticker}?with_nested_markets=true")


def snapshot_open(j: Journal, root: str = "data/snapshots", fetch_event=_fetch_event,
                  now: datetime | None = None) -> list[str]:
    """Kalshi-Preise aller offenen Tipps (valuebets + placed) vor Anstoß sichern –
    der letzte Snapshot vor Anstoß ist die Closing Line. Anstoß aus dem Journal
    (Kalshi-occurrence_datetime ist das erwartete Spielende)."""
    now = now or datetime.now(timezone.utc)
    events: dict[str, str] = {}
    for name in ("valuebets", "placed"):
        for r in j.read(name):
            ref, ko = r.get("ref", ""), r.get("kickoff", "")
            if r.get("result") or not ref.startswith("KX") or not ko:
                continue
            if datetime.fromisoformat(ko.replace("Z", "+00:00")) > now:
                events.setdefault(ref.rsplit("-", 1)[0], ko)
    log, rows = [], []
    obs = now.isoformat(timespec="seconds")
    for ev, ko in sorted(events.items()):
        d, err = fetch_event(ev)
        if d is None:
            log.append(f"{ev}: Abruf fehlgeschlagen ({err})")
            continue
        ms = d.get("markets") or (d.get("event") or {}).get("markets") or []
        for m in ms:
            q = kalshi.parse_event_markets({"events": [{"event_ticker": ev, "markets": [m]}]})[0]
            rows.append({"ticker": q.ticker, "event_ticker": ev, "side": q.label,
                         "bid": q.yes_bid, "ask": q.yes_ask, "observed_at": obs,
                         "kickoff": datetime.fromisoformat(ko.replace("Z", "+00:00")).isoformat()})
        log.append(f"{ev} (Anstoß {ko}): " + ", ".join(
            f"{r['side']} {r['bid']:.2f}/{r['ask']:.2f}" for r in rows if r["event_ticker"] == ev))
    if rows:
        Path(root).mkdir(parents=True, exist_ok=True)
        with (Path(root) / f"kalshi-{now:%Y-%m}.jsonl").open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    return log or ["keine offenen Tipps vor Anstoß"]


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
            # Über/Unter & Handicap: NEIN-Seite als "...:no" im Markt-Code
            side = ("no" if r["market"].endswith(":no") else
                    r["market"] if r["market"] in ("yes", "no") else "yes")
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
