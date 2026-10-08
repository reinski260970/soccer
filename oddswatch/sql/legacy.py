"""Evaluate existing scanner predictions without inventing model provenance."""
import math
from datetime import datetime, timezone


def available(conn):
    return conn.execute("SELECT to_regclass('public.predictions') IS NOT NULL AND to_regclass('public.games') IS NOT NULL AS ok").fetchone()['ok']


def pending_games(conn, league):
    if not available(conn): return []
    return conn.execute("SELECT DISTINCT g.event_id,g.kickoff FROM public.games g JOIN public.predictions p USING(event_id) "
      "WHERE g.league=%s AND p.league=%s AND p.created_at<g.kickoff AND g.kickoff<now() "
      "AND NOT EXISTS (SELECT 1 FROM sports.scanner_evaluations v WHERE v.source_prediction_id=p.id)",(league,league)).fetchall()


def evaluate_scanner(conn):
    if not available(conn): return 0
    count=0
    rows=conn.execute("SELECT p.id,p.event_id,p.league,p.model,p.created_at,p.market,p.p_model,e.home_score,e.away_score,e.observed_at "
      "FROM public.predictions p JOIN sports.events e ON e.source_event_id=p.event_id AND e.league=p.league "
      "WHERE p.league IN ('nba','nfl') AND p.created_at<e.kickoff AND e.status='STATUS_FINAL' "
      "AND e.season_type<>'preseason' AND e.home_score IS NOT NULL AND e.away_score IS NOT NULL").fetchall()
    with conn.transaction():
        for p in rows:
            if p['market'] not in ('home','away') or not 0<float(p['p_model'])<1: continue
            h,a=p['home_score'],p['away_score']
            y=None if h==a else int((h>a)==(p['market']=='home'))
            prob=float(p['p_model'])
            count+=conn.execute('INSERT INTO sports.scanner_evaluations '
              '(source_prediction_id,event_id,league,model,predicted_at,market,probability,outcome,brier,log_loss,home_score,away_score,evaluated_at) '
              'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(source_prediction_id) DO UPDATE '
              'SET outcome=excluded.outcome,brier=excluded.brier,log_loss=excluded.log_loss,home_score=excluded.home_score,'
              'away_score=excluded.away_score,evaluated_at=excluded.evaluated_at '
              'WHERE (sports.scanner_evaluations.home_score,sports.scanner_evaluations.away_score) IS DISTINCT FROM '
              '(excluded.home_score,excluded.away_score)',
              (p['id'],p['event_id'],p['league'],p['model'],p['created_at'],p['market'],prob,y,
               None if y is None else (prob-y)**2,None if y is None else -math.log(prob if y else 1-prob),h,a,datetime.now(timezone.utc))).rowcount
    return count
