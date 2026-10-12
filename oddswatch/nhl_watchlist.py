"""Persistent NHL model watchlist in Neon.

This is a monitoring layer, not a betting release path.

Discovery rule for new FULL_GAME moneyline watches:
- V5.1 venue xG gate is AGREE.
- The venue xG direction matches the watched side.
- A fresh prematch reference/executable decimal quote is at or above the
  model's 3% EV trigger: fair_odds * 1.03.

Existing watches remain remembered even if the price drifts below the trigger.
They become:
- TRIGGERED when a fresh executable quote reaches the trigger,
- REJECTED if the xG gate/direction no longer supports the side,
- EXPIRED at kickoff.

TRIGGERED is explicitly NOT PLAY. The NHL model is still SHADOW/unapproved.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Jsonb

from .sql.store import connect, migrate, timestamp

TARGET_EV = 0.03
HORIZON_DAYS = 7
PRICE_MAX_AGE_HOURS = 24


def _id(*parts: object) -> str:
    raw = "|".join(str(p) for p in parts)
    return "watch:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def trigger_odds(fair_odds: float, target_ev: float = TARGET_EV) -> float:
    if fair_odds <= 1:
        raise ValueError("fair_odds must be >1")
    if not 0 <= target_ev <= 1:
        raise ValueError("target_ev must be 0..1")
    return fair_odds * (1.0 + target_ev)


def classify_status(
    *,
    kickoff: datetime,
    now: datetime,
    gate_state: str,
    model_direction: str,
    selection: str,
    executable_odds: float | None,
    trigger: float,
) -> str:
    if kickoff <= now:
        return "EXPIRED"
    if gate_state != "AGREE" or model_direction != selection:
        return "REJECTED"
    if executable_odds is not None and executable_odds >= trigger:
        return "TRIGGERED"
    return "WATCH"


def qualifies_new_watch(
    *,
    kickoff: datetime,
    now: datetime,
    gate_state: str,
    model_direction: str,
    selection: str,
    reference_odds: float | None,
    trigger: float,
) -> bool:
    return (
        kickoff > now
        and gate_state == "AGREE"
        and model_direction == selection
        and reference_odds is not None
        and reference_odds >= trigger
    )


def _candidate_rows(conn, now: datetime) -> list[dict]:
    """One row per HOME/AWAY side with latest xG, model and fresh prices."""
    cutoff = now - timedelta(hours=PRICE_MAX_AGE_HOURS)
    horizon = now + timedelta(days=HORIZON_DAYS)
    return conn.execute(
        """
        WITH ev AS (
          SELECT event_id,league,home_name,away_name,kickoff
          FROM sports.events
          WHERE league='nhl' AND season_type='regular'
            AND status='STATUS_SCHEDULED'
            AND kickoff>%s AND kickoff<=%s
        ),
        xg AS (
          SELECT DISTINCT ON (s.event_id)
                 s.event_id,s.observed_at,s.metrics
          FROM sports.stats_snapshots s
          JOIN ev USING(event_id)
          WHERE s.source='moneypuck-v5.1-entry'
            AND s.metrics->>'side'='HOME'
          ORDER BY s.event_id,s.observed_at DESC
        ),
        pred AS (
          SELECT DISTINCT ON (p.event_id,p.selection)
                 p.event_id,p.selection,p.probability,p.model_id,p.as_of
          FROM sports.predictions p
          JOIN ev USING(event_id)
          WHERE p.model_id LIKE 'hockey-chronocal-v1:nhl:%%'
            AND p.market='moneyline' AND p.period='FULL_GAME'
            AND p.settlement_rules='INCLUDING_OT'
            AND p.selection IN ('HOME','AWAY')
          ORDER BY p.event_id,p.selection,p.as_of DESC,p.prediction_id DESC
        ),
        latest_book AS (
          SELECT DISTINCT ON (o.event_id,o.selection,o.bookmaker,o.source)
                 o.event_id,o.selection,o.bookmaker,o.source,o.odds,
                 o.observed_at,o.executable
          FROM sports.odds_snapshots o
          JOIN ev USING(event_id)
          WHERE o.market='moneyline' AND o.period='FULL_GAME'
            AND o.settlement_rules='INCLUDING_OT'
            AND NOT o.live AND o.observed_at >= %s
            AND o.selection IN ('HOME','AWAY')
          ORDER BY o.event_id,o.selection,o.bookmaker,o.source,o.observed_at DESC,o.quote_id DESC
        ),
        prices AS (
          SELECT event_id,selection,
                 max(odds) AS best_reference_odds,
                 (array_agg(bookmaker ORDER BY odds DESC))[1] AS best_reference_bookmaker,
                 max(odds) FILTER (WHERE executable) AS best_executable_odds,
                 (array_agg(bookmaker ORDER BY odds DESC)
                    FILTER (WHERE executable))[1] AS best_executable_bookmaker,
                 max(observed_at) AS price_observed_at
          FROM latest_book
          GROUP BY event_id,selection
        )
        SELECT e.event_id,e.league,e.home_name,e.away_name,e.kickoff,
               p.selection,p.probability,p.model_id,p.as_of,
               x.metrics->>'venue_xg_agreement' AS gate_state,
               x.metrics->>'venue_xg_direction' AS model_direction,
               (x.metrics->>'fast_matchup_home_xg')::double precision AS fast_matchup_home_xg,
               (x.metrics->>'fast_matchup_away_xg')::double precision AS fast_matchup_away_xg,
               (x.metrics->>'home_home_fast_xgf5')::double precision AS home_fast_xgf5,
               (x.metrics->>'home_home_fast_xga5')::double precision AS home_fast_xga5,
               (x.metrics->>'away_away_fast_xgf5')::double precision AS away_fast_xgf5,
               (x.metrics->>'away_away_fast_xga5')::double precision AS away_fast_xga5,
               pr.best_reference_odds,pr.best_reference_bookmaker,
               pr.best_executable_odds,pr.best_executable_bookmaker,
               pr.price_observed_at
        FROM ev e
        JOIN xg x USING(event_id)
        JOIN pred p USING(event_id)
        LEFT JOIN prices pr ON pr.event_id=e.event_id AND pr.selection=p.selection
        ORDER BY e.kickoff,e.event_id,p.selection
        """,
        (now, horizon, cutoff),
    ).fetchall()


def _existing(conn) -> dict[tuple, dict]:
    rows = conn.execute(
        """
        SELECT * FROM sports.watchlist
        WHERE league='nhl'
          AND market='moneyline'
          AND period='FULL_GAME'
          AND settlement_rules='INCLUDING_OT'
          AND status IN ('WATCH','TRIGGERED')
        """
    ).fetchall()
    return {
        (r["event_id"], r["market"], r["selection"], float(r["line"]),
         r["period"], r["settlement_rules"]): r
        for r in rows
    }


def run(now: datetime | None = None) -> dict:
    now = timestamp(now or datetime.now(timezone.utc))
    with connect() as conn:
        migrate(conn)
        rows = _candidate_rows(conn, now)
        existing = _existing(conn)
        seen_keys = set()
        created = updated = observations = 0
        triggered = watches = rejected = 0

        with conn.transaction():
            for r in rows:
                selection = r["selection"]
                key = (
                    r["event_id"], "moneyline", selection, 0.0,
                    "FULL_GAME", "INCLUDING_OT",
                )
                seen_keys.add(key)

                p = float(r["probability"])
                if not 0 < p < 1:
                    continue
                fair = 1.0 / p
                trigger = trigger_odds(fair)
                ref = (
                    float(r["best_reference_odds"])
                    if r["best_reference_odds"] is not None else None
                )
                exe = (
                    float(r["best_executable_odds"])
                    if r["best_executable_odds"] is not None else None
                )
                old = existing.get(key)

                if old is None and not qualifies_new_watch(
                    kickoff=r["kickoff"], now=now,
                    gate_state=r["gate_state"], model_direction=r["model_direction"],
                    selection=selection, reference_odds=ref, trigger=trigger,
                ):
                    continue

                status = classify_status(
                    kickoff=r["kickoff"], now=now,
                    gate_state=r["gate_state"], model_direction=r["model_direction"],
                    selection=selection, executable_odds=exe, trigger=trigger,
                )
                if exe is not None:
                    current_odds = exe
                    current_book = r["best_executable_bookmaker"]
                    price_type = "EXECUTABLE"
                elif ref is not None:
                    current_odds = ref
                    current_book = r["best_reference_bookmaker"]
                    price_type = "REFERENCE"
                else:
                    current_odds = None
                    current_book = None
                    price_type = "NONE"

                team = r["home_name"] if selection == "HOME" else r["away_name"]
                reason = (
                    f"{team} {selection}: V5.1 venue xG {r['gate_state']} "
                    f"{r['model_direction']}; fair {fair:.3f}; "
                    f"3% EV trigger {trigger:.3f}."
                )
                meta = {
                    "target_ev": TARGET_EV,
                    "release_policy": "TRIGGERED is review only; never automatic PLAY",
                    "xg_source": "moneypuck-v5.1-entry",
                    "forecast_source": r["model_id"],
                    "fast_matchup_home_xg": r["fast_matchup_home_xg"],
                    "fast_matchup_away_xg": r["fast_matchup_away_xg"],
                    "home_fast_xgf5": r["home_fast_xgf5"],
                    "home_fast_xga5": r["home_fast_xga5"],
                    "away_fast_xgf5": r["away_fast_xgf5"],
                    "away_fast_xga5": r["away_fast_xga5"],
                    "reference_odds": ref,
                    "reference_bookmaker": r["best_reference_bookmaker"],
                    "executable_odds": exe,
                    "executable_bookmaker": r["best_executable_bookmaker"],
                    "price_observed_at": (
                        r["price_observed_at"].isoformat()
                        if r["price_observed_at"] else None
                    ),
                }
                watch_id = old["watch_id"] if old else _id(
                    *key
                )
                if old is None:
                    created += conn.execute(
                        """
                        INSERT INTO sports.watchlist(
                          watch_id,event_id,league,sport,market,selection,line,period,
                          settlement_rules,model_id,fair_probability,fair_odds,
                          trigger_odds,current_odds,current_bookmaker,price_type,
                          gate_type,gate_state,model_direction,watch_source,status,reason,
                          created_at,updated_at,last_checked_at,expires_at,metadata
                        ) VALUES(
                          %s,%s,'nhl','hockey','moneyline',%s,0,'FULL_GAME','INCLUDING_OT',
                          %s,%s,%s,%s,%s,%s,%s,'VENUE_XG',%s,%s,'nhl-v5.1',%s,%s,
                          %s,%s,%s,%s,%s
                        )
                        ON CONFLICT(event_id,market,selection,line,period,settlement_rules)
                        DO NOTHING
                        """,
                        (
                            watch_id,r["event_id"],selection,r["model_id"],p,fair,
                            trigger,current_odds,current_book,price_type,
                            r["gate_state"],r["model_direction"],status,reason,
                            now,now,now,r["kickoff"],Jsonb(meta),
                        ),
                    ).rowcount
                else:
                    updated += conn.execute(
                        """
                        UPDATE sports.watchlist SET
                          model_id=%s,fair_probability=%s,fair_odds=%s,trigger_odds=%s,
                          current_odds=%s,current_bookmaker=%s,price_type=%s,
                          sport='hockey',gate_type='VENUE_XG',
                          gate_state=%s,model_direction=%s,watch_source='nhl-v5.1',
                          status=%s,reason=%s,
                          updated_at=%s,last_checked_at=%s,expires_at=%s,metadata=%s
                        WHERE watch_id=%s
                        """,
                        (
                            r["model_id"],p,fair,trigger,current_odds,current_book,
                            price_type,r["gate_state"],r["model_direction"],status,reason,
                            now,now,r["kickoff"],Jsonb(meta),watch_id,
                        ),
                    ).rowcount

                observations += conn.execute(
                    """
                    INSERT INTO sports.watchlist_observations(
                      watch_id,observed_at,fair_probability,fair_odds,trigger_odds,
                      current_odds,current_bookmaker,price_type,gate_type,gate_state,model_direction,
                      watch_source,status,metadata
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'VENUE_XG',%s,%s,'nhl-v5.1',%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        watch_id,now,p,fair,trigger,current_odds,current_book,
                        price_type,r["gate_state"],r["model_direction"],status,Jsonb(meta),
                    ),
                ).rowcount

                if status == "TRIGGERED":
                    triggered += 1
                elif status == "WATCH":
                    watches += 1
                elif status == "REJECTED":
                    rejected += 1

            # Any active watch whose event vanished from the scheduled candidate
            # universe is expired only when kickoff has passed. We do not silently
            # delete history.
            old_rows = conn.execute(
                """
                SELECT w.watch_id,w.event_id,w.market,w.selection,w.line,w.period,
                       w.settlement_rules,w.expires_at,w.status
                FROM sports.watchlist w
                WHERE w.league='nhl' AND w.status IN ('WATCH','TRIGGERED')
                """
            ).fetchall()
            for old in old_rows:
                key = (
                    old["event_id"],old["market"],old["selection"],
                    float(old["line"]),old["period"],old["settlement_rules"],
                )
                if key in seen_keys or old["expires_at"] > now:
                    continue
                updated += conn.execute(
                    """
                    UPDATE sports.watchlist
                    SET status='EXPIRED',updated_at=%s,last_checked_at=%s
                    WHERE watch_id=%s
                    """,
                    (now,now,old["watch_id"]),
                ).rowcount

        open_rows = conn.execute(
            """
            SELECT w.watch_id,e.home_name,e.away_name,e.kickoff,w.selection,
                   w.fair_odds,w.trigger_odds,w.current_odds,w.current_bookmaker,
                   w.price_type,w.gate_state,w.model_direction,w.status
            FROM sports.watchlist w
            JOIN sports.events e USING(event_id)
            WHERE w.league='nhl' AND w.status IN ('WATCH','TRIGGERED')
            ORDER BY e.kickoff,w.selection
            """
        ).fetchall()

    result = {
        "at": now.isoformat(),
        "candidate_rows_checked": len(rows),
        "created": created,
        "updated": updated,
        "observations": observations,
        "watch": watches,
        "triggered": triggered,
        "rejected": rejected,
        "open": [
            {
                **dict(r),
                "kickoff": r["kickoff"].isoformat(),
                "fair_odds": round(float(r["fair_odds"]), 3),
                "trigger_odds": round(float(r["trigger_odds"]), 3),
                "current_odds": (
                    round(float(r["current_odds"]), 3)
                    if r["current_odds"] is not None else None
                ),
            }
            for r in open_rows
        ],
        "plays_created": 0,
    }
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__ == "__main__":
    run()
