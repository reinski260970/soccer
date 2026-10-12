"""Cross-sport persistent WATCH registry.

Any candidate that has already passed a sport-specific audit into
sports.signals(signal_type='WATCH') is copied into the shared Neon watchlist and
kept there until kickoff. This covers soccer, hockey, basketball, NFL and tennis
as soon as their model/audit writes a WATCH signal.

The registry does not create PLAYs. A WATCH becomes TRIGGERED only when a fresh
executable price reaches the sport/market EV trigger; TRIGGERED means re-review.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Jsonb

from .sql.store import connect, migrate, timestamp

PRICE_MAX_AGE_HOURS = 24

SOCCER_LEAGUES = {
    "austria","bundesliga","bundesliga2","liga3","epl","championship","laliga",
    "seriea","ligue1","eredivisie","primeira","belgium","switzerland","turkey",
    "poland","norway","sweden","denmark","scotland","mls","brazil","argentina",
    "ucl","uel","uecl","nations",
}
HOCKEY_LEAGUES = {
    "nhl","del","icehl","liiga","shl","nl","khl","extraliga","slovakia",
    "norway-hockey","denmark-hockey","chl",
}
BASKETBALL_LEAGUES = {"nba","euroleague","eurocup","bbl","acb"}


def sport_for_league(league: str) -> str:
    lg = (league or "").strip().lower()
    if lg in SOCCER_LEAGUES:
        return "soccer"
    if lg in HOCKEY_LEAGUES:
        return "hockey"
    if lg in BASKETBALL_LEAGUES:
        return "basketball"
    if lg == "nfl":
        return "nfl"
    if lg in {"atp","wta","tennis"} or lg.startswith("atp_") or lg.startswith("wta_"):
        return "tennis"
    return "other"


def target_ev(sport: str, market: str) -> float:
    sport = sport.lower()
    market = market.lower()
    if sport == "soccer":
        if market in {"total","team_total"}:
            return 0.015
        if market == "btts":
            return 0.018
        return 0.020
    if sport == "tennis":
        return 0.020
    return 0.030


def trigger_odds(fair_odds: float, sport: str, market: str) -> float:
    if fair_odds <= 1:
        raise ValueError("fair_odds must be > 1")
    return fair_odds * (1.0 + target_ev(sport, market))


def state(
    *,
    kickoff: datetime,
    now: datetime,
    executable_odds: float | None,
    trigger: float,
) -> str:
    if kickoff <= now:
        return "EXPIRED"
    if executable_odds is not None and executable_odds >= trigger:
        return "TRIGGERED"
    return "WATCH"


def _watch_id(signal_id: str) -> str:
    return "watchsig:" + hashlib.sha256(signal_id.encode("utf-8")).hexdigest()


def _rows(conn, now: datetime) -> list[dict]:
    fresh_after = now - timedelta(hours=PRICE_MAX_AGE_HOURS)
    return conn.execute(
        """
        WITH base AS (
          SELECT s.signal_id,s.created_at AS signal_created_at,s.clv_status,
                 p.prediction_id,p.event_id,p.model_id,p.market,p.selection,p.line,
                 p.period,p.settlement_rules,p.probability,p.quality,p.features,
                 e.league,e.home_name,e.away_name,e.kickoff,e.status AS event_status,
                 q.quote_id AS entry_quote_id,q.odds AS entry_odds,
                 q.bookmaker AS entry_bookmaker,q.executable AS entry_executable,
                 q.observed_at AS entry_observed_at
          FROM sports.signals s
          JOIN sports.predictions p USING(prediction_id)
          JOIN sports.events e USING(event_id)
          JOIN sports.odds_snapshots q ON q.quote_id=s.entry_quote_id
          WHERE s.signal_type='WATCH'
            AND e.kickoff>%s
        ),
        latest_book AS (
          SELECT DISTINCT ON (
                   o.event_id,o.market,o.selection,o.line,o.period,o.settlement_rules,
                   o.bookmaker,o.source
                 )
                 o.event_id,o.market,o.selection,o.line,o.period,o.settlement_rules,
                 o.bookmaker,o.source,o.odds,o.observed_at,o.executable
          FROM sports.odds_snapshots o
          JOIN base b
            ON b.event_id=o.event_id AND b.market=o.market
           AND b.selection=o.selection AND b.line=o.line
           AND b.period=o.period AND b.settlement_rules=o.settlement_rules
          WHERE NOT o.live AND o.observed_at >= %s
          ORDER BY o.event_id,o.market,o.selection,o.line,o.period,o.settlement_rules,
                   o.bookmaker,o.source,o.observed_at DESC,o.quote_id DESC
        ),
        prices AS (
          SELECT event_id,market,selection,line,period,settlement_rules,
                 max(odds) AS best_reference_odds,
                 (array_agg(bookmaker ORDER BY odds DESC))[1] AS best_reference_bookmaker,
                 max(odds) FILTER (WHERE executable) AS best_executable_odds,
                 (array_agg(bookmaker ORDER BY odds DESC)
                    FILTER (WHERE executable))[1] AS best_executable_bookmaker,
                 max(observed_at) AS price_observed_at
          FROM latest_book
          GROUP BY event_id,market,selection,line,period,settlement_rules
        )
        SELECT b.*,p.best_reference_odds,p.best_reference_bookmaker,
               p.best_executable_odds,p.best_executable_bookmaker,p.price_observed_at
        FROM base b
        LEFT JOIN prices p
          ON p.event_id=b.event_id AND p.market=b.market
         AND p.selection=b.selection AND p.line=b.line
         AND p.period=b.period AND p.settlement_rules=b.settlement_rules
        ORDER BY b.kickoff,b.league,b.signal_id
        """,
        (now, fresh_after),
    ).fetchall()


def run(now: datetime | None = None) -> dict:
    now = timestamp(now or datetime.now(timezone.utc))
    with connect() as conn:
        migrate(conn)
        rows = _rows(conn, now)
        created = updated = observations = triggered = watches = 0

        with conn.transaction():
            for r in rows:
                p = float(r["probability"])
                if not 0 < p < 1:
                    continue
                sport = sport_for_league(r["league"])
                fair = 1.0 / p
                trigger = trigger_odds(fair, sport, r["market"])

                exe = (
                    float(r["best_executable_odds"])
                    if r["best_executable_odds"] is not None else None
                )
                ref = (
                    float(r["best_reference_odds"])
                    if r["best_reference_odds"] is not None else None
                )
                if exe is not None:
                    cur = exe
                    book = r["best_executable_bookmaker"]
                    price_type = "EXECUTABLE"
                elif ref is not None:
                    cur = ref
                    book = r["best_reference_bookmaker"]
                    price_type = "REFERENCE"
                else:
                    cur = float(r["entry_odds"]) if r["entry_odds"] is not None else None
                    book = r["entry_bookmaker"]
                    price_type = "EXECUTABLE" if r["entry_executable"] else "REFERENCE"

                status = state(
                    kickoff=r["kickoff"], now=now,
                    executable_odds=exe, trigger=trigger,
                )
                watch_id = _watch_id(r["signal_id"])
                reason = (
                    f"Audited {sport} WATCH from sports.signals; "
                    f"fair {fair:.3f}; target EV {target_ev(sport,r['market'])*100:.1f}%; "
                    f"trigger {trigger:.3f}."
                )
                meta = {
                    "signal_id": r["signal_id"],
                    "prediction_id": r["prediction_id"],
                    "entry_quote_id": r["entry_quote_id"],
                    "entry_odds": float(r["entry_odds"]),
                    "entry_bookmaker": r["entry_bookmaker"],
                    "entry_executable": bool(r["entry_executable"]),
                    "prediction_features": r["features"],
                    "prediction_quality": r["quality"],
                    "target_ev": target_ev(sport, r["market"]),
                    "release_policy": "TRIGGERED means re-review only; never automatic PLAY",
                    "best_reference_odds": ref,
                    "best_reference_bookmaker": r["best_reference_bookmaker"],
                    "best_executable_odds": exe,
                    "best_executable_bookmaker": r["best_executable_bookmaker"],
                    "price_observed_at": (
                        r["price_observed_at"].isoformat()
                        if r["price_observed_at"] else None
                    ),
                }

                exists = conn.execute(
                    "SELECT watch_id FROM sports.watchlist WHERE watch_id=%s",
                    (watch_id,),
                ).fetchone()
                if not exists:
                    created += conn.execute(
                        """
                        INSERT INTO sports.watchlist(
                          watch_id,event_id,league,sport,market,selection,line,period,
                          settlement_rules,model_id,fair_probability,fair_odds,
                          trigger_odds,current_odds,current_bookmaker,price_type,
                          gate_type,gate_state,model_direction,watch_source,status,reason,
                          created_at,updated_at,last_checked_at,expires_at,metadata
                        ) VALUES(
                          %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                          'AUDITED_SIGNAL','SUPPORTED',%s,'sports.signals',%s,%s,
                          %s,%s,%s,%s,%s
                        )
                        ON CONFLICT(event_id,market,selection,line,period,settlement_rules)
                        DO NOTHING
                        """,
                        (
                            watch_id,r["event_id"],r["league"],sport,r["market"],
                            r["selection"],r["line"],r["period"],r["settlement_rules"],
                            r["model_id"],p,fair,trigger,cur,book,price_type,
                            r["selection"],status,reason,now,now,now,r["kickoff"],Jsonb(meta),
                        ),
                    ).rowcount
                else:
                    updated += conn.execute(
                        """
                        UPDATE sports.watchlist SET
                          sport=%s,model_id=%s,fair_probability=%s,fair_odds=%s,
                          trigger_odds=%s,current_odds=%s,current_bookmaker=%s,
                          price_type=%s,gate_type='AUDITED_SIGNAL',gate_state='SUPPORTED',
                          model_direction=%s,watch_source='sports.signals',status=%s,
                          reason=%s,updated_at=%s,last_checked_at=%s,expires_at=%s,
                          metadata=%s
                        WHERE watch_id=%s
                        """,
                        (
                            sport,r["model_id"],p,fair,trigger,cur,book,price_type,
                            r["selection"],status,reason,now,now,r["kickoff"],
                            Jsonb(meta),watch_id,
                        ),
                    ).rowcount

                # If a model-native row already owns the exact event/market unique
                # key, update that row's freshness/status instead of duplicating it.
                owner = conn.execute(
                    """
                    SELECT watch_id FROM sports.watchlist
                    WHERE event_id=%s AND market=%s AND selection=%s AND line=%s
                      AND period=%s AND settlement_rules=%s
                    """,
                    (
                        r["event_id"],r["market"],r["selection"],r["line"],
                        r["period"],r["settlement_rules"],
                    ),
                ).fetchone()
                if owner:
                    watch_id = owner["watch_id"]

                observations += conn.execute(
                    """
                    INSERT INTO sports.watchlist_observations(
                      watch_id,observed_at,fair_probability,fair_odds,trigger_odds,
                      current_odds,current_bookmaker,price_type,gate_type,gate_state,
                      model_direction,watch_source,status,metadata
                    ) VALUES(
                      %s,%s,%s,%s,%s,%s,%s,%s,'AUDITED_SIGNAL','SUPPORTED',
                      %s,'sports.signals',%s,%s
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        watch_id,now,p,fair,trigger,cur,book,price_type,
                        r["selection"],status,Jsonb(meta),
                    ),
                ).rowcount
                if status == "TRIGGERED":
                    triggered += 1
                else:
                    watches += 1

            # Expire every sport at kickoff, preserving all history.
            updated += conn.execute(
                """
                UPDATE sports.watchlist
                SET status='EXPIRED',updated_at=%s,last_checked_at=%s
                WHERE status IN ('WATCH','TRIGGERED') AND expires_at<=%s
                """,
                (now,now,now),
            ).rowcount

        summary = conn.execute(
            """
            SELECT sport,status,count(*) AS n
            FROM sports.watchlist
            GROUP BY sport,status
            ORDER BY sport,status
            """
        ).fetchall()

    result = {
        "at": now.isoformat(),
        "signal_rows_checked": len(rows),
        "created": created,
        "updated": updated,
        "observations": observations,
        "watch": watches,
        "triggered": triggered,
        "summary": [dict(r) for r in summary],
        "plays_created": 0,
    }
    print(json.dumps(result,ensure_ascii=False,default=str))
    return result


if __name__ == "__main__":
    run()
