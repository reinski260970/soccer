"""US-sports PRE-STEAM: Polymarket CLOB leads, ESPN/DK lags.

This is a timing layer only. It does not create a betting recommendation.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import pricing, report, steam, telegram
from .sources import espn, polymarket

LEAGUES = ("nfl", "nhl", "nba")
DAYS = 4
ALERT_STATE = Path("data/journal/us_steam_alerts.json")
ALERT_COOLDOWN_MIN = 90
MIN_EXTRA_MOVE = 0.015


def _load_alerts() -> dict:
    try:
        x = json.loads(ALERT_STATE.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_alerts(x: dict) -> None:
    ALERT_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE.write_text(json.dumps(x, ensure_ascii=False, indent=1), encoding="utf-8")


def _espn_probs(g) -> tuple[dict[str, float], dict[str, float]] | None:
    h = (g.ref_line or {}).get("ml_home")
    a = (g.ref_line or {}).get("ml_away")
    if not h or not a or h <= 1 or a <= 1:
        return None
    ps = pricing.devig([float(h), float(a)])
    return {"home": ps[0], "away": ps[1]}, {"home": float(h), "away": float(a)}


def _poly_hit(qs, league: str, g):
    hit = polymarket.find(qs, g)
    if hit:
        return hit
    if league != "nfl":
        return None
    q, _ = polymarket.direct_quote(league, g)
    if not q:
        return None
    h = polymarket._team_side(q, g.home.aliases())
    a = polymarket._team_side(q, g.away.aliases())
    if h is None or a is None or h == a:
        return None
    return q, h, a


def _poly_probs(q, hi: int, ai: int) -> tuple[dict[str, float], dict[str, float]]:
    vals = []
    odds = {}
    for side, idx in (("home", hi), ("away", ai)):
        p = float(q.mids[idx])
        b, _ = polymarket.book(q.tokens[idx])
        if b:
            bid, ask = b.get("best_bid"), b.get("best_ask")
            if bid is not None and ask is not None and 0 < bid < ask < 1:
                p = (float(bid) + float(ask)) / 2.0
        vals.append((side, p))
    z = sum(v for _, v in vals)
    probs = {k: v / z for k, v in vals} if z > 0 else {}
    for side, p in probs.items():
        odds[side] = 1.0 / p
    return probs, odds


def collect(now: datetime | None = None) -> tuple[list[dict], list[str]]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    recs: list[dict] = []
    issues: list[str] = []
    for league in LEAGUES:
        qs, err = polymarket.discover(league)
        if err:
            issues.append(f"Polymarket {league.upper()}: {err}")
            qs = []
        games, errs = espn.upcoming(league, now.date(), DAYS)
        issues += [f"ESPN {league.upper()}: {e}" for e in errs]
        for g in games:
            if g.status != "STATUS_SCHEDULED" or g.kickoff <= now:
                continue
            er = _espn_probs(g)
            if not er:
                continue
            hit = _poly_hit(qs, league, g)
            if not hit:
                continue
            q, hi, ai = hit
            pp, po = _poly_probs(q, hi, ai)
            ep, eo = er
            if not pp:
                continue
            for side, team in (("home", g.home.name), ("away", g.away.name)):
                recs.append({
                    "key": f"us:{league}:{g.id}:{side}",
                    "event": g.title,
                    "kickoff": g.kickoff.isoformat(),
                    "league": league,
                    "market": side,
                    "selection": f"{team} ML",
                    "lead_source": "Polymarket",
                    "slow_sources": ["ESPN/DK"],
                    "probs": {
                        "Polymarket": pp[side],
                        "ESPN/DK": ep[side],
                    },
                    "odds": {
                        "Polymarket": po[side],
                        "ESPN/DK": eo[side],
                    },
                })
    return recs, issues


def _new_alerts(signals: list[dict], now: datetime) -> list[dict]:
    state = _load_alerts()
    out = []
    for s in signals:
        key = s["key"]
        prev = state.get(key) or {}
        try:
            pts = datetime.fromisoformat(prev.get("ts", "")).astimezone(timezone.utc)
        except (TypeError, ValueError):
            pts = None
        last_p = float(prev.get("lead_prob", 0.0) or 0.0)
        cur_p = float((s.get("probs") or {}).get("Polymarket", 0.0) or 0.0)
        changed = prev.get("direction") != s.get("direction")
        cooled = pts is None or now - pts >= timedelta(minutes=ALERT_COOLDOWN_MIN)
        extended = abs(cur_p - last_p) >= MIN_EXTRA_MOVE
        if changed or cooled or extended:
            out.append(s)
            state[key] = {
                "ts": now.isoformat(),
                "direction": s.get("direction"),
                "lead_prob": cur_p,
            }
    _save_alerts(state)
    return out


def _text(signals: list[dict], now: datetime) -> str:
    lines = [
        f"⚡ US PRE-STEAM · {report.stand(now)}",
        "Polymarket bewegt sich vor ESPN/DK · Timing-Signal, kein automatisches PLAY.",
    ]
    for s in signals[:10]:
        arrow = "📉 SHORTENING erwartet" if s["direction"] == "SHORTENING" else "📈 DRIFT erwartet"
        o = s.get("odds") or {}
        lines += [
            "",
            f"{arrow} · {report._league(s['league'])}",
            f"🆚 {s['event']}",
            f"➡️ {s['selection']}",
            f"   Polymarket Δ {s['lead_move']*100:+.1f}pp / {s['minutes']}m",
            f"   Lead-vs-ESPN/DK {s['lag']*100:+.1f}pp · aktueller Gap {s['current_gap']*100:+.1f}pp",
            f"   Poly {o.get('Polymarket', 0):.2f} | ESPN/DK {o.get('ESPN/DK', 0):.2f}",
        ]
    return "\n".join(lines)


def run(*, send: bool = False, now: datetime | None = None) -> list[str]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    recs, issues = collect(now)
    signals = steam.update_many(recs, now=now)
    signals = [s for s in signals if str(s.get("key", "")).startswith("us:")]
    fresh = _new_alerts(signals, now)
    log = [
        f"US PRE-STEAM {report.stand(now)}: {len(recs)} Marktseiten beobachtet",
        f"Signale {len(signals)} · neu/sendbar {len(fresh)}",
    ]
    for s in fresh[:10]:
        log.append(
            f"{s['direction']} | {s['event']} | {s['selection']} | "
            f"Poly {s['lead_move']*100:+.1f}pp/{s['minutes']}m | "
            f"Lag {s['lag']*100:+.1f}pp"
        )
    if issues:
        log.append(f"Hinweise: {len(issues)} Quellen-/Matching-Hinweis(e)")
    if send and fresh:
        r = telegram.send(_text(fresh, now))
        log.append("Telegram: " + (
            f"gesendet {r['message_ids']}" if r["sent"] else f"NICHT gesendet – {r['error']}"
        ))
    return log
