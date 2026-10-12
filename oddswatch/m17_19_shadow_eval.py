"""Forward CLV and market comparison for M17.19 shadow predictions."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from sqlalchemy import select

from . import pricing, sql_store

MODEL = "m17.19-forward-shadow"
SIDES = ("home","draw","away")
SOURCE_PRIORITY = ("pinnacle","betfair","bet365")


def _complete_close(quotes, kickoff):
    by = defaultdict(lambda: defaultdict(dict))
    for r in quotes:
        if r["observed_at"] >= kickoff:
            continue
        side = str(r["market"]).lower()
        if side not in SIDES:
            continue
        by[str(r["source"]).lower()][r["observed_at"]][side] = float(r["odds"])
    for source in SOURCE_PRIORITY:
        groups = by.get(source) or {}
        for ts in sorted(groups, reverse=True):
            g = groups[ts]
            if all(s in g and g[s] > 1 for s in SIDES):
                probs = pricing.devig([g[s] for s in SIDES])
                return source, ts, dict(zip(SIDES, probs))
    return None, None, None


def _entry_best(quotes, created_at, side):
    lo = created_at - timedelta(minutes=15)
    hi = created_at + timedelta(minutes=15)
    vals = [
        float(r["odds"]) for r in quotes
        if bool(r["executable"])
        and str(r["market"]).lower() == side
        and lo <= r["observed_at"] <= hi
        and float(r["odds"]) > 1
    ]
    return max(vals) if vals else None


def run():
    sql_store.init_db()
    with sql_store.engine().connect() as conn:
        preds = list(conn.execute(
            select(sql_store.predictions).where(
                sql_store.predictions.c.model == MODEL
            )
        ).mappings())
        games = {
            str(r["event_id"]): r for r in conn.execute(select(sql_store.games)).mappings()
        }
        quotes = list(conn.execute(select(sql_store.odds)).mappings())

    q_by_event = defaultdict(list)
    for r in quotes:
        q_by_event[str(r["event_id"])].append(r)

    # Use the first model snapshot per event/side as the fixed forward call.
    first = {}
    for p in sorted(preds, key=lambda r:r["created_at"]):
        key = (str(p["event_id"]), str(p["market"]).lower())
        first.setdefault(key, p)

    rows = []
    for (event_id, side), p in first.items():
        g = games.get(event_id)
        if not g or side not in SIDES:
            continue
        qs = q_by_event.get(event_id, [])
        entry = _entry_best(qs, p["created_at"], side)
        source, close_ts, close_probs = _complete_close(qs, g["kickoff"])
        close_p = close_probs.get(side) if close_probs else None
        ev = float(p["p_model"]) * entry - 1.0 if entry else None
        clv = entry * close_p - 1.0 if entry and close_p else None
        rows.append({
            "event": g["event"], "league": g["league"], "kickoff": g["kickoff"],
            "side": side, "p_model": float(p["p_model"]),
            "fair_odds": float(p["fair_odds"]), "entry_odds": entry, "entry_ev": ev,
            "close_source": source, "close_at": close_ts,
            "close_prob": close_p, "shadow_clv": clv,
            "outcome": p["outcome"],
        })

    candidates = [r for r in rows if r["entry_ev"] is not None and r["entry_ev"] > 0]
    closed = [r for r in candidates if r["shadow_clv"] is not None]
    settled = [r for r in candidates if r["outcome"] is not None]
    avg_clv = sum(r["shadow_clv"] for r in closed)/len(closed) if closed else None
    pos = sum(r["shadow_clv"] > 0 for r in closed)/len(closed) if closed else None

    print(f"M17.19 SHADOW candidates={len(candidates)} closed={len(closed)} settled={len(settled)}")
    if avg_clv is not None:
        print(f"CLV avg={avg_clv*100:+.2f}% positive={pos*100:.1f}%")
    for r in sorted(candidates, key=lambda x:(x["kickoff"],-(x["entry_ev"] or -9))):
        clv = "OPEN" if r["shadow_clv"] is None else f"{r['shadow_clv']*100:+.2f}%"
        print(
            f"{r['league']} | {r['event']} | {r['side']} | "
            f"p={r['p_model']:.3f} fair={r['fair_odds']:.2f} "
            f"entry={r['entry_odds']:.2f} EV={r['entry_ev']*100:+.1f}% CLV={clv}"
        )
    return rows


if __name__ == "__main__":
    run()
