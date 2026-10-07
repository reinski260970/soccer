"""Pre-steam / market-lead detection from repeated price snapshots.

Goal: detect a likely next move in slower books, not merely report a move that
already happened. All probabilities supplied here must be de-vigged upstream.

A PRE_STEAM signal requires:
- meaningful move in the lead source (normally Pinnacle),
- slower books moving less in the same interval,
- current lead-vs-slow divergence in the same direction,
- preferably persistence across multiple lead snapshots.

Signals are probabilistic warnings, never automatic PLAY decisions.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

STATE = Path("data/journal/steam_history.json")
MAX_AGE_HOURS = 8
MIN_LOOKBACK_MIN = 10
MAX_LOOKBACK_MIN = 120
MIN_LEAD_MOVE = 0.008       # 0.8 percentage points
MIN_LAG_GAP = 0.007         # 0.7 pp: lead moved more than slow books
MIN_CURRENT_GAP = 0.008     # 0.8 pp current lead-vs-slow divergence
MIN_SCORE = 3


def _load(path: Path = STATE) -> dict[str, list[dict]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict[str, list[dict]], path: Path = STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _parse_ts(v: str) -> datetime | None:
    try:
        return datetime.fromisoformat(v).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _prior(rows: list[dict], now: datetime) -> dict | None:
    candidates = []
    for r in rows:
        ts = _parse_ts(r.get("ts", ""))
        if ts is None:
            continue
        age = now - ts
        if timedelta(minutes=MIN_LOOKBACK_MIN) <= age <= timedelta(minutes=MAX_LOOKBACK_MIN):
            candidates.append((ts, r))
    return max(candidates, default=(None, None), key=lambda x: x[0])[1]


def _avg(vals: list[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def _same_sign(a: float, b: float) -> bool:
    return (a > 0 and b > 0) or (a < 0 and b < 0)


def assess(rows: list[dict], current: dict, now: datetime) -> dict | None:
    """Assess one current snapshot against its recent history."""
    prev = _prior(rows, now)
    if not prev:
        return None

    cur_probs = current.get("probs") or {}
    old_probs = prev.get("probs") or {}
    lead = current.get("lead_source") or "Pinnacle"
    slow_cfg = current.get("slow_sources") or ["Bet365", "Betfair"]
    if lead not in cur_probs or lead not in old_probs:
        return None

    lead_move = float(cur_probs[lead]) - float(old_probs[lead])
    if abs(lead_move) < MIN_LEAD_MOVE:
        return None

    slow_names = [
        b for b in slow_cfg
        if b in cur_probs and b in old_probs
    ]
    if not slow_names:
        return None

    slow_moves = [float(cur_probs[b]) - float(old_probs[b]) for b in slow_names]
    slow_move = _avg(slow_moves)
    slow_now = _avg([float(cur_probs[b]) for b in slow_names])
    if slow_move is None or slow_now is None:
        return None

    lag = lead_move - slow_move
    current_gap = float(cur_probs[lead]) - slow_now
    direction = "SHORTENING" if lead_move > 0 else "DRIFTING"

    score = 0
    reasons = []
    if abs(lead_move) >= MIN_LEAD_MOVE:
        score += 1
        reasons.append(f"{lead} {lead_move * 100:+.1f}pp")
    if _same_sign(lead_move, lag) and abs(lag) >= MIN_LAG_GAP:
        score += 1
        reasons.append(f"Lead-vs-Slow {lag * 100:+.1f}pp")
    if _same_sign(lead_move, current_gap) and abs(current_gap) >= MIN_CURRENT_GAP:
        score += 1
        reasons.append(f"aktueller Gap {current_gap * 100:+.1f}pp")

    # Persistence: previous two Pinnacle snapshots moved in same direction.
    valid = []
    for r in rows[-4:]:
        ts = _parse_ts(r.get("ts", ""))
        p = (r.get("probs") or {}).get(lead)
        if ts and p is not None:
            valid.append((ts, float(p)))
    valid.sort()
    if len(valid) >= 2:
        last_move = valid[-1][1] - valid[-2][1]
        if _same_sign(lead_move, last_move) and abs(last_move) >= 0.003:
            score += 1
            reasons.append("Richtung bestätigt")

    if score < MIN_SCORE:
        return None
    return {
        "direction": direction,
        "score": score,
        "lead_source": lead,
        "lead_move": lead_move,
        "slow_move": slow_move,
        "lag": lag,
        "current_gap": current_gap,
        "slow_books": slow_names,
        "reasons": reasons,
        "minutes": int((now - _parse_ts(prev["ts"])).total_seconds() // 60),
    }


def update_many(records: list[dict], *, now: datetime | None = None,
                path: Path = STATE) -> list[dict]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    data = _load(path)
    cutoff = now - timedelta(hours=MAX_AGE_HOURS)
    signals = []
    for rec in records:
        key = rec["key"]
        rows = data.setdefault(key, [])
        current = {
            "ts": now.isoformat(),
            "event": rec["event"],
            "kickoff": rec["kickoff"],
            "league": rec["league"],
            "market": rec["market"],
            "selection": rec["selection"],
            "lead_source": rec.get("lead_source") or "Pinnacle",
            "slow_sources": list(rec.get("slow_sources") or ["Bet365", "Betfair"]),
            "probs": {k: float(v) for k, v in (rec.get("probs") or {}).items() if v is not None},
            "odds": {k: float(v) for k, v in (rec.get("odds") or {}).items() if v is not None},
        }
        signal = assess(rows, current, now)
        rows[:] = [
            r for r in rows
            if (ts := _parse_ts(r.get("ts", ""))) is not None and ts >= cutoff
        ]
        rows.append(current)
        if signal:
            signal.update({
                "key": key,
                "event": current["event"], "kickoff": current["kickoff"],
                "league": current["league"], "market": current["market"],
                "selection": current["selection"], "probs": current["probs"],
                "odds": current["odds"],
            })
            signals.append(signal)
    _save(data, path)
    return signals


def update(key: str, *, event: str, kickoff: str, league: str, market: str,
           selection: str, probs: dict[str, float], odds: dict[str, float],
           now: datetime | None = None, path: Path = STATE) -> dict | None:
    signals = update_many([{
        "key": key, "event": event, "kickoff": kickoff, "league": league,
        "market": market, "selection": selection, "probs": probs, "odds": odds,
    }], now=now, path=path)
    return signals[0] if signals else None
