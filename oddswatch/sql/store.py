"""Transactions, idempotent imports and conservative closing capture (Postgres 15+)."""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path


def timestamp(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else value
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('timezone-aware timestamp required')
    return value


def connect():
    import os
    import psycopg
    from psycopg.rows import dict_row
    dsn = os.environ.get('SPORTS_DATABASE_URL')
    if not dsn:
        raise ValueError('SPORTS_DATABASE_URL is not configured')
    return psycopg.connect(dsn, connect_timeout=15, row_factory=dict_row,
                          options='-c statement_timeout=60000')


def migrate(conn):
    with conn.transaction():
        conn.execute('SELECT pg_advisory_xact_lock(79261007)')
        conn.execute('CREATE SCHEMA IF NOT EXISTS sports')
        conn.execute('CREATE TABLE IF NOT EXISTS sports.schema_migrations '
                     '(version text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())')
        for path in sorted((Path(__file__).parent/'migrations').glob('*.sql')):
            content = path.read_text()
            checksum = hashlib.sha256(content.encode()).hexdigest()
            old = conn.execute('SELECT checksum FROM sports.schema_migrations WHERE version=%s', (path.name,)).fetchone()
            if old:
                if old['checksum'] != checksum:
                    raise ValueError('applied migration changed; create a new migration')
                continue
            conn.execute(content)
            conn.execute('INSERT INTO sports.schema_migrations(version,checksum) VALUES(%s,%s)', (path.name,checksum))


# Explicit allowlist; identifiers never come directly from a payload.
FIELDS = {
 'events': 'event_id league source source_event_id home_team_id away_team_id home_name away_name kickoff season season_type status home_score away_score observed_at',
 'odds_snapshots': 'quote_id event_id market selection line period settlement_rules bookmaker source source_url observed_at source_time odds commission executable live liquidity',
 'model_versions': 'model_id league trained_through created_at method parameters validation approved',
 'predictions': 'prediction_id event_id model_id as_of market selection line period settlement_rules probability quality features',
 'stats_snapshots': 'event_id league entity_type entity_id source observed_at data_through metrics',
 'news_snapshots': 'news_id event_id league entity_id published_at observed_at source verified category payload',
 'raw_payloads': 'source resource observed_at payload',
 'signals': 'signal_id prediction_id entry_quote_id signal_type created_at stake_eh',
}
JSON_FIELDS = {'parameters','validation','features','metrics','payload'}
TIME_FIELDS = {'kickoff','observed_at','source_time','trained_through','created_at','as_of','data_through','published_at'}
MATCH_FIELDS = ('event_id','market','selection','line','period','settlement_rules')


def insert(conn, table, record):
    from psycopg.types.json import Jsonb
    if table not in FIELDS or not record or set(record)-set(FIELDS[table].split()):
        raise ValueError('unknown table or fields')
    row = dict(record)
    for key in TIME_FIELDS & row.keys():
        if row[key] is not None:
            row[key] = timestamp(row[key])
    if table == 'predictions':
        event = conn.execute('SELECT * FROM sports.events WHERE event_id=%s', (row['event_id'],)).fetchone()
        model = conn.execute('SELECT * FROM sports.model_versions WHERE model_id=%s', (row['model_id'],)).fetchone()
        if not event or not model or event['league'] != model['league']:
            raise ValueError('prediction league/event/model mismatch')
        if not model['trained_through'] <= model['created_at'] <= row['as_of'] < event['kickoff']:
            raise ValueError('prediction contains future information')
        if event['season_type']=='preseason':
            raise ValueError('preseason predictions excluded')
    if table == 'signals':
        p=conn.execute('SELECT * FROM sports.predictions WHERE prediction_id=%s', (row['prediction_id'],)).fetchone()
        q=conn.execute('SELECT * FROM sports.odds_snapshots WHERE quote_id=%s', (row['entry_quote_id'],)).fetchone()
        if not p or not q or any(p[k]!=q[k] for k in MATCH_FIELDS):
            raise ValueError('signal market mismatch')
        e=conn.execute('SELECT * FROM sports.events WHERE event_id=%s', (p['event_id'],)).fetchone()
        if q['live'] or not max(p['as_of'],q['observed_at']) <= row['created_at'] < e['kickoff']:
            raise ValueError('signal is not prematch')
        if row['signal_type']=='PLAY':
            m=conn.execute('SELECT * FROM sports.model_versions WHERE model_id=%s', (p['model_id'],)).fetchone()
            net=1+(q['odds']-1)*(1-q['commission'])
            if not m['approved'] or p['quality']=='LOW' or not q['executable'] or p['probability']*net<=1:
                raise ValueError('PLAY gate failed')
    cols=list(row)
    values=[Jsonb(row[k]) if k in JSON_FIELDS else row[k] for k in cols]
    sql=f"INSERT INTO sports.{table} ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})"
    if table=='events':
        update=[k for k in cols if k not in {'event_id','league','source','source_event_id'}]
        sql+=' ON CONFLICT(event_id) DO UPDATE SET '+','.join(f'{k}=excluded.{k}' for k in update)
        sql+=' WHERE excluded.observed_at >= sports.events.observed_at'
    else:
        sql+=' ON CONFLICT DO NOTHING'
    result=conn.execute(sql,values).rowcount
    if table=='events':
        conn.execute('INSERT INTO sports.event_observations(event_id,observed_at,kickoff,status,home_score,away_score) '
                     'VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                     tuple(row.get(k) for k in ('event_id','observed_at','kickoff','status','home_score','away_score')))
    return result


def ingest(conn, bundle):
    if set(bundle)-set(FIELDS):
        raise ValueError('unknown bundle tables')
    counts={}
    with conn.transaction():
        for table in FIELDS:
            if table in bundle:
                counts[table]=sum(insert(conn,table,r) for r in bundle[table])
    return counts


def capture_closing(conn, now=None, max_age_minutes=15):
    """Same-source/line/rules last observed prematch quote, never a live price.

    This is sampled CLV, not proof of the exact market's final tick. Raw CLV only;
    no-vig requires a complete simultaneous outcome book and is not synthesized.
    """
    now=timestamp(now or datetime.now(timezone.utc))
    if not 1 <= max_age_minutes <= 60:
        raise ValueError('closing freshness must be 1..60 minutes')
    closed=[]
    with conn.transaction():
        rows=conn.execute("SELECT s.signal_id,s.entry_quote_id,e.kickoff FROM sports.signals s "
            "JOIN sports.predictions p USING(prediction_id) JOIN sports.events e USING(event_id) "
            "WHERE s.clv_status='OPEN' AND e.kickoff<=%s AND e.status IN ('STATUS_IN_PROGRESS','STATUS_FINAL') "
            "FOR UPDATE OF s SKIP LOCKED",(now,)).fetchall()
        for s in rows:
            q=conn.execute('SELECT * FROM sports.odds_snapshots WHERE quote_id=%s',(s['entry_quote_id'],)).fetchone()
            keys=(*MATCH_FIELDS,'bookmaker','source','commission')
            where=' AND '.join(k+'=%s' for k in keys)
            closing=conn.execute('SELECT * FROM sports.odds_snapshots WHERE '+where+
                ' AND NOT live AND observed_at<%s AND observed_at>=%s AND observed_at>=%s '
                'AND (source_time IS NULL OR source_time>=%s) '
                'ORDER BY observed_at DESC,quote_id LIMIT 1',
                tuple(q[k] for k in keys)+(s['kickoff'],s['kickoff']-timedelta(minutes=max_age_minutes),
                    q['observed_at'],s['kickoff']-timedelta(minutes=max_age_minutes))).fetchone()
            if not closing:
                continue
            entry=float(q['odds']);close=float(closing['odds'])
            raw=100*(entry/close-1);pp=100*(1/close-1/entry)
            conn.execute('INSERT INTO sports.clv_log VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                         (s['signal_id'],closing['quote_id'],now,raw,pp,'Last sampled pregame quote; raw odds CLV, not no-vig or fee-adjusted'))
            conn.execute("UPDATE sports.signals SET clv_status='CLOSED' WHERE signal_id=%s",(s['signal_id'],))
            closed.append({'signal_id':s['signal_id'],'entry_odds':entry,'closing_odds':close,'raw_clv_percent':raw,'clv_pp':pp})
    return closed
