"""Persist audited Bet365 Valuebet candidates and measure sampled closing-line value.

The Valuebet API is candidate discovery only. We persist a WATCH signal only after
our independent model has produced a fair price for the exact same market.

CLV is captured only when a same-source, same-market Bet365 quote was observed
within the final 60 minutes before kickoff. If that quote is missing, the signal
stays OPEN and is reported as NO_CLOSE rather than synthesized.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from .store import connect, ingest, migrate, timestamp


AUDITED_STATUSES = {"BESTÄTIGT", "REDUZIERT", "KONFLIKT", "WIDERLEGT"}


def _alert_key(a) -> str:
    v = a.value
    teams = "|".join(sorted(str(x).strip().casefold() for x in (v.teams or ())))
    kick = v.kickoff.isoformat() if v.kickoff else ""
    parts = (
        v.sport, v.tournament, teams, kick, v.bookmaker,
        v.bet_type, v.condition, v.period, v.base,
    )
    return "vba:" + _id(*parts)


def filter_unsent_actionable(audits):
    """Return new confirmed >=3% model-EV alerts.

    Fail closed when Neon is unavailable: Telegram dedupe must never degrade
    into repeated alerts.
    """
    import os
    eligible = [
        a for a in audits
        if a.status == "BESTÄTIGT"
        and a.our_ev is not None
        and a.our_ev >= 0.03
        and getattr(a.value, "back", False)
    ]
    if not eligible:
        return [], {"configured": bool(os.getenv("SPORTS_DATABASE_URL", "").strip()), "reason": "no_actionable"}
    if not os.getenv("SPORTS_DATABASE_URL", "").strip():
        return [], {"configured": False, "reason": "dedupe_store_missing"}

    with connect() as conn:
        migrate(conn)
        keys = [_alert_key(a) for a in eligible]
        rows = conn.execute(
            "SELECT alert_key FROM sports.value_alerts WHERE alert_key = ANY(%s)",
            (keys,),
        ).fetchall()
        seen = {r["alert_key"] for r in rows}
    fresh = [a for a in eligible if _alert_key(a) not in seen]
    return fresh, {
        "configured": True,
        "eligible": len(eligible),
        "fresh": len(fresh),
        "duplicate": len(eligible) - len(fresh),
    }


def mark_actionable_sent(audits, now=None):
    """Mark alerts only after Telegram send succeeded."""
    if not audits:
        return {"stored": 0}
    now = timestamp(now or datetime.now(timezone.utc))
    from psycopg.types.json import Jsonb
    stored = 0
    with connect() as conn:
        migrate(conn)
        with conn.transaction():
            for a in audits:
                v = a.value
                payload = {
                    "sport": v.sport,
                    "tournament": v.tournament,
                    "teams": list(v.teams or ()),
                    "kickoff": v.kickoff.isoformat() if v.kickoff else None,
                    "selection": v.selection,
                    "market": v.market,
                    "bet_type": v.bet_type,
                    "condition": v.condition,
                    "period": v.period,
                    "base": v.base,
                    "fair": a.our_fair,
                    "model_ev": a.our_ev,
                }
                stored += conn.execute(
                    "INSERT INTO sports.value_alerts("
                    "alert_key,valuebet_id,first_sent_at,last_sent_at,bookmaker,odds,model_ev,payload"
                    ") VALUES(%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT(alert_key) DO NOTHING",
                    (
                        _alert_key(a), v.id or None, now, now, v.bookmaker,
                        float(v.odds), float(a.our_ev), Jsonb(payload),
                    ),
                ).rowcount
    return {"stored": stored}


def _id(*parts) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _descriptor(v):
    code = (v.bet_type or "").strip()
    try:
        line = float(v.condition or 0)
    except (TypeError, ValueError):
        line = 0.0

    if code in {"win1", "winOnly1"}:
        market, selection, line = "moneyline", "HOME", 0.0
    elif code in {"win2", "winOnly2"}:
        market, selection, line = "moneyline", "AWAY", 0.0
    elif code == "draw":
        market, selection, line = "moneyline", "DRAW", 0.0
    elif code == "over":
        market = "team_total" if (v.base or "").casefold() not in {"", "overall", "total", "match"} else "total"
        selection = "OVER"
    elif code == "under":
        market = "team_total" if (v.base or "").casefold() not in {"", "overall", "total", "match"} else "total"
        selection = "UNDER"
    elif code == "ah1":
        market, selection = "spread", "HOME"
    elif code == "ah2":
        market, selection = "spread", "AWAY"
    elif code == "win1RetX":
        market, selection, line = "dnb", "HOME", 0.0
    elif code == "win2RetX":
        market, selection, line = "dnb", "AWAY", 0.0
    elif code in {"1x", "x1"}:
        market, selection, line = "double_chance", "HOME_OR_DRAW", 0.0
    elif code in {"x2", "2x"}:
        market, selection, line = "double_chance", "DRAW_OR_AWAY", 0.0
    elif code in {"_12", "12"}:
        market, selection, line = "double_chance", "HOME_OR_AWAY", 0.0
    elif code == "eh1":
        market, selection = "european_handicap", "HOME"
    elif code == "ehx":
        market, selection = "european_handicap", "DRAW"
    elif code == "eh2":
        market, selection = "european_handicap", "AWAY"
    elif code == "yes":
        market, selection, line = "btts", "YES", 0.0
    elif code == "no":
        market, selection, line = "btts", "NO", 0.0
    else:
        return None

    p = (v.period or "regularTime").casefold()
    periods = {
        "regulartime": "REGULATION",
        "fulltime": "FULL_GAME",
        "match": "FULL_GAME",
        "overtime": "FULL_GAME",
        "shootout": "FULL_GAME",
        "1h": "FIRST_HALF",
        "half1": "FIRST_HALF",
        "2h": "SECOND_HALF",
        "half2": "SECOND_HALF",
        "p1": "FIRST_PERIOD",
        "period1": "FIRST_PERIOD",
        "p2": "SECOND_PERIOD",
        "period2": "SECOND_PERIOD",
        "p3": "THIRD_PERIOD",
        "period3": "THIRD_PERIOD",
        "q1": "FIRST_QUARTER",
        "quarter1": "FIRST_QUARTER",
        "q2": "SECOND_QUARTER",
        "quarter2": "SECOND_QUARTER",
        "q3": "THIRD_QUARTER",
        "quarter3": "THIRD_QUARTER",
        "q4": "FOURTH_QUARTER",
        "quarter4": "FOURTH_QUARTER",
    }
    period = periods.get(p, p.upper() or "REGULATION")
    if p == "shootout":
        rules = "INCLUDING_OT_SO"
    elif p == "overtime":
        rules = "INCLUDING_OT"
    elif period == "FULL_GAME" and v.sport in {"Basketball", "Hockey"}:
        rules = "INCLUDING_OT"
    else:
        rules = "REGULATION"

    # Team-total side belongs in settlement rules so quotes for home/away totals
    # cannot accidentally match each other at close.
    if market == "team_total":
        b = (v.base or "").casefold()
        side = "HOME" if b in {"team1", "home", "1", "first"} or "team1" in b or "home" in b else "AWAY"
        rules += f":TEAM_TOTAL_{side}"
    return market, selection, line, period, rules


def _match_fixture(v, fixtures):
    from .. import matching
    if len(v.teams) != 2 or v.kickoff is None:
        return None
    hits = []
    for fx in fixtures:
        if abs(fx.game.kickoff - v.kickoff) > timedelta(hours=12):
            continue
        direct = matching.same(v.teams[0], fx.game.home.name) and matching.same(v.teams[1], fx.game.away.name)
        reverse = matching.same(v.teams[0], fx.game.away.name) and matching.same(v.teams[1], fx.game.home.name)
        if direct or reverse:
            hits.append(fx)
    return hits[0] if len(hits) == 1 else None


def _fallback_period_league(v):
    t = (v.tournament or "").casefold()
    if v.sport == "Basketball" and "nba" in t:
        return "nba"
    if v.sport == "American football" and "nfl" in t:
        return "nfl"
    if v.sport == "Hockey":
        if "nhl" in t:
            return "nhl"
        hockey = (
            ("czechia extraliga", "extraliga"),
            ("czech extraliga", "extraliga"),
            ("finland liiga", "liiga"),
            ("liiga", "liiga"),
            ("sweden shl", "shl"),
            ("shl", "shl"),
            ("austria ice hockey league", "icehl"),
            ("ice hockey league", "icehl"),
            ("khl", "khl"),
        )
        for label, code in hockey:
            if label in t:
                return code
    return None


def persist_audits(audits, fixtures):
    """Persist model-audited Bet365 candidates as WATCH signals + entry quotes."""
    import os
    if not os.getenv("SPORTS_DATABASE_URL", "").strip():
        return {"configured": False}

    now = datetime.now(timezone.utc)
    bundle = {"events": [], "model_versions": [], "predictions": [], "odds_snapshots": [], "signals": []}
    models = set()

    for a in audits:
        if a.status not in AUDITED_STATUSES or a.our_probability is None:
            continue
        v = a.value
        if v.kickoff is None or v.kickoff <= now:
            continue
        fx = _match_fixture(v, fixtures)
        desc = _descriptor(v)
        if desc is None:
            continue
        market, selection, line, period, rules = desc

        if fx is not None:
            league = fx.league
            source_event_id = str(fx.game.id)
            home_name = fx.game.home.name
            away_name = fx.game.away.name
            kickoff = fx.game.kickoff
            status = fx.game.status
            model_name = fx.model or fx.sport or "independent"
        else:
            # Independent NBA/NFL/NHL period totals do not require the
            # full-game scanner. Build a stable event identity from the
            # candidate itself so CLV can still be tracked.
            if len(v.teams) != 2 or v.kickoff is None:
                continue
            league = _fallback_period_league(v)
            if league is None:
                continue
            home_name, away_name = v.teams[0], v.teams[1]
            kickoff = v.kickoff
            source_event_id = v.id or _id(league, home_name, away_name, kickoff.isoformat())
            status = "STATUS_SCHEDULED"
            model_name = f"period-total:{period}"

        event_id = f"valueaudit:{league}:{source_event_id}"
        model_id = f"valueaudit:{league}:{model_name}:{now:%Y%m%d}"
        if model_id not in models:
            bundle["model_versions"].append({
                "model_id": model_id, "league": league,
                "trained_through": now - timedelta(seconds=2),
                "created_at": now - timedelta(seconds=1),
                "method": model_name,
                "parameters": {"source": "oddswatch independent fair"},
                "validation": {"status": "SHADOW", "purpose": "Valuebet candidate audit + CLV"},
                "approved": False,
            })
            models.add(model_id)

        bundle["events"].append({
            "event_id": event_id, "league": league, "source": "oddswatch",
            "source_event_id": source_event_id,
            "home_team_id": f"{league}:{home_name}",
            "away_team_id": f"{league}:{away_name}",
            "home_name": home_name, "away_name": away_name,
            "kickoff": kickoff, "season": kickoff.year,
            "season_type": "regular", "status": status,
            "home_score": None, "away_score": None, "observed_at": now,
        })

        stamp = int(now.timestamp())
        qid = "vbq:" + _id(event_id, market, selection, line, period, rules, "bet365", stamp)
        pid = "vbp:" + _id(event_id, model_id, market, selection, line, period, rules, stamp)
        sid = "vbs:" + _id(pid, qid)

        bundle["odds_snapshots"].append({
            "quote_id": qid, "event_id": event_id, "market": market,
            "selection": selection, "line": line, "period": period,
            "settlement_rules": rules, "bookmaker": "bet365",
            "source": "valuebet_api", "source_url": None,
            "observed_at": now, "source_time": v.created if getattr(v, "created", None) else None,
            "odds": float(v.odds), "commission": float(v.commission or 0),
            "executable": False, "live": False, "liquidity": None,
        })
        bundle["predictions"].append({
            "prediction_id": pid, "event_id": event_id, "model_id": model_id,
            "as_of": now, "market": market, "selection": selection, "line": line,
            "period": period, "settlement_rules": rules,
            "probability": float(a.our_probability), "quality": "MEDIUM",
            "features": {
                "audit_status": a.status, "our_fair": a.our_fair, "our_ev": a.our_ev,
                "valuebet_ev": v.ev, "valuebet_market": v.market,
                "valuebet_id": v.id, "note": a.note,
            },
        })
        bundle["signals"].append({
            "signal_id": sid, "prediction_id": pid, "entry_quote_id": qid,
            "signal_type": "WATCH", "created_at": now, "stake_eh": 0,
        })

    if not bundle["events"]:
        return {"configured": True, "stored": 0}
    with connect() as conn:
        migrate(conn)
        counts = ingest(conn, bundle)
    return {"configured": True, **counts}


def snapshot_open_candidates(values):
    """Store current Bet365 quotes for already tracked WATCH markets, no model scan."""
    import os
    if not os.getenv("SPORTS_DATABASE_URL", "").strip():
        return {"configured": False}
    now = datetime.now(timezone.utc)
    inserted = 0
    with connect() as conn:
        migrate(conn)
        open_rows = conn.execute(
            "SELECT s.signal_id,p.*,e.home_name,e.away_name,e.kickoff,q.bookmaker,q.source,q.commission "
            "FROM sports.signals s JOIN sports.predictions p USING(prediction_id) "
            "JOIN sports.events e USING(event_id) JOIN sports.odds_snapshots q ON q.quote_id=s.entry_quote_id "
            "WHERE s.clv_status='OPEN' AND p.model_id LIKE 'valueaudit:%' AND e.kickoff>%s",
            (now,),
        ).fetchall()
        bundle = {"odds_snapshots": []}
        from .. import matching
        for row in open_rows:
            for v in values:
                if v.bookmaker != "bet365" or not v.back or v.kickoff is None:
                    continue
                if abs(v.kickoff - row["kickoff"]) > timedelta(hours=12):
                    continue
                direct = matching.same(v.teams[0], row["home_name"]) and matching.same(v.teams[1], row["away_name"])
                reverse = matching.same(v.teams[0], row["away_name"]) and matching.same(v.teams[1], row["home_name"])
                if not (direct or reverse):
                    continue
                desc = _descriptor(v)
                if not desc:
                    continue
                market, selection, line, period, rules = desc
                if any(row[k] != x for k, x in zip(
                    ("market","selection","line","period","settlement_rules"),
                    (market,selection,line,period,rules)
                )):
                    continue
                stamp = int(now.timestamp())
                bundle["odds_snapshots"].append({
                    "quote_id": "vbq:" + _id(row["event_id"], market, selection, line, period, rules, stamp),
                    "event_id": row["event_id"], "market": market, "selection": selection,
                    "line": line, "period": period, "settlement_rules": rules,
                    "bookmaker": "bet365", "source": "valuebet_api", "source_url": None,
                    "observed_at": now, "source_time": None, "odds": float(v.odds),
                    "commission": float(v.commission or 0), "executable": False,
                    "live": False, "liquidity": None,
                })
                break
        if bundle["odds_snapshots"]:
            inserted = ingest(conn, bundle).get("odds_snapshots", 0)
    return {"configured": True, "odds_snapshots": inserted}


def _trend_from_quotes(rows, min_move_pp=0.5):
    """Classify same-market Bet365 movement in implied-probability points."""
    if len(rows) < 2:
        return {"direction": "NO_HISTORY", "samples": len(rows)}
    first = rows[0]
    last = rows[-1]
    o0 = float(first["odds"])
    o1 = float(last["odds"])
    if o0 <= 1 or o1 <= 1:
        return {"direction": "NO_HISTORY", "samples": len(rows)}
    move_pp = 100.0 * (1.0 / o1 - 1.0 / o0)
    if move_pp >= min_move_pp:
        direction = "SHORTENING"
    elif move_pp <= -min_move_pp:
        direction = "DRIFTING"
    else:
        direction = "NEUTRAL"
    t0 = first.get("observed_at")
    t1 = last.get("observed_at")
    minutes = None
    try:
        minutes = int((t1 - t0).total_seconds() / 60)
    except Exception:
        pass
    return {
        "direction": direction,
        "samples": len(rows),
        "old_odds": o0,
        "new_odds": o1,
        "move_pp": move_pp,
        "minutes": minutes,
    }


def period_price_trends(audits, lookback_hours=6):
    """Recent Bet365 direction for exact audited period markets.

    This is not a Pinnacle sharp-steam proxy. It is a same-source exact-line
    price trend used as a CLV/entry timing gate when no period sharp feed exists.
    """
    import os
    if not os.getenv("SPORTS_DATABASE_URL", "").strip():
        return {}

    now = datetime.now(timezone.utc)
    out = {}
    with connect() as conn:
        migrate(conn)
        for a in audits:
            v = a.value
            if v.kickoff is None or len(v.teams) != 2:
                continue
            league = _fallback_period_league(v)
            desc = _descriptor(v)
            if league is None or desc is None:
                continue
            market, selection, line, period, rules = desc
            source_event_id = v.id or _id(
                league, v.teams[0], v.teams[1], v.kickoff.isoformat()
            )
            event_id = f"valueaudit:{league}:{source_event_id}"
            rows = conn.execute(
                "SELECT odds,observed_at FROM sports.odds_snapshots "
                "WHERE event_id=%s AND market=%s AND selection=%s AND line=%s "
                "AND period=%s AND settlement_rules=%s AND bookmaker='bet365' "
                "AND source='valuebet_api' AND observed_at>=%s "
                "ORDER BY observed_at ASC,quote_id ASC",
                (
                    event_id, market, selection, line, period, rules,
                    now - timedelta(hours=lookback_hours),
                ),
            ).fetchall()
            out[_alert_key(a)] = _trend_from_quotes(rows)
    return out


def capture_sampled_clv(now=None, max_age_minutes=60):
    """Close Valuebet WATCH signals with a same-market Bet365 quote near kickoff."""
    now = timestamp(now or datetime.now(timezone.utc))
    closed = []
    no_close = 0
    with connect() as conn:
        migrate(conn)
        with conn.transaction():
            rows = conn.execute(
                "SELECT s.signal_id,s.entry_quote_id,e.kickoff FROM sports.signals s "
                "JOIN sports.predictions p USING(prediction_id) JOIN sports.events e USING(event_id) "
                "WHERE s.clv_status='OPEN' AND p.model_id LIKE 'valueaudit:%' AND e.kickoff<=%s "
                "FOR UPDATE OF s SKIP LOCKED",
                (now,),
            ).fetchall()
            for s in rows:
                q = conn.execute("SELECT * FROM sports.odds_snapshots WHERE quote_id=%s", (s["entry_quote_id"],)).fetchone()
                closing = conn.execute(
                    "SELECT * FROM sports.odds_snapshots WHERE event_id=%s AND market=%s AND selection=%s "
                    "AND line=%s AND period=%s AND settlement_rules=%s AND bookmaker=%s AND source=%s "
                    "AND NOT live AND observed_at<%s AND observed_at>=%s AND observed_at>=%s "
                    "ORDER BY observed_at DESC,quote_id LIMIT 1",
                    (q["event_id"],q["market"],q["selection"],q["line"],q["period"],q["settlement_rules"],
                     q["bookmaker"],q["source"],s["kickoff"],s["kickoff"]-timedelta(minutes=max_age_minutes),
                     q["observed_at"]),
                ).fetchone()
                if not closing or closing["quote_id"] == q["quote_id"]:
                    no_close += 1
                    continue
                entry, close = float(q["odds"]), float(closing["odds"])
                raw = 100 * (entry / close - 1)
                pp = 100 * (1 / close - 1 / entry)
                conn.execute(
                    "INSERT INTO sports.clv_log(signal_id,closing_quote_id,captured_at,raw_clv_percent,clv_pp,note) "
                    "VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (s["signal_id"],closing["quote_id"],now,raw,pp,
                     "Sampled Bet365 CLV from Valuebet API; exact same market/line/period/rules; within 60m pre-kickoff"),
                )
                conn.execute("UPDATE sports.signals SET clv_status='CLOSED' WHERE signal_id=%s", (s["signal_id"],))
                closed.append({"signal_id":s["signal_id"],"entry_odds":entry,"closing_odds":close,"raw_clv_percent":raw,"clv_pp":pp})
    return {"closed": closed, "no_close": no_close}
