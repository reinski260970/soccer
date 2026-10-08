import os
from datetime import datetime,timezone
import pytest
from oddswatch.sql.evaluation import outcome,evaluate
from oddswatch.sql.runner import parse
from oddswatch.sql.store import connect,migrate,ingest

@pytest.mark.parametrize('market,selection,line,h,a,expected',[
 ('moneyline','HOME',0,100,90,'WIN'),('moneyline','AWAY',0,100,90,'LOSE'),
 ('moneyline','HOME',0,20,20,'PUSH'),('spread','AWAY',10,100,90,'PUSH'),
 ('total','UNDER',190.5,100,90,'WIN'),('total','OVER',190,100,90,'PUSH'),
 ('spread','HOME',-1.25,100,90,None)])
def test_outcomes(market,selection,line,h,a,expected):
    p=dict(market=market,selection=selection,line=line,period='FULL_GAME',settlement_rules='INCLUDING_OT_PUSH_ON_TIE')
    assert outcome(p,h,a)==expected
    assert outcome({**p,'period':'REGULATION'},h,a) is None

def test_postgres_internal_evaluation():
    if not os.getenv('SPORTS_DATABASE_URL'): pytest.skip('requires PostgreSQL 15+')
    with connect() as c:
        migrate(c);migrate(c)
        with c.transaction(force_rollback=True):
            c.execute('TRUNCATE sports.events,sports.model_versions CASCADE')
            e=dict(event_id='nba:espn:test',league='nba',source='test',source_event_id='test',home_team_id='a',away_team_id='b',home_name='A',away_name='B',kickoff='2026-01-02T12:00:00Z',season=2026,season_type='regular',status='STATUS_FINAL',home_score=100,away_score=90,observed_at='2026-01-02T15:00:00Z')
            m=dict(model_id='test',league='nba',trained_through='2026-01-01T00:00:00Z',created_at='2026-01-01T01:00:00Z',method='test',parameters={},validation={})
            p=dict(prediction_id='test',event_id=e['event_id'],model_id='test',as_of='2026-01-02T10:00:00Z',market='moneyline',selection='HOME',line=0,period='FULL_GAME',settlement_rules='INCLUDING_OT_PUSH_ON_TIE',probability=.6,quality='LOW',features={})
            bundle={'events':[e],'model_versions':[m],'predictions':[p]}
            ingest(c,bundle);ingest(c,bundle)
            assert evaluate(c)==1
            assert evaluate(c)==0
            metrics=c.execute('SELECT * FROM sports.model_metrics').fetchone()
            assert float(metrics['brier_score'])==pytest.approx(.16)
            assert metrics['scored']==1
            assert c.execute('SELECT * FROM sports.performance').fetchall()==[]
            with pytest.raises(ValueError):
                ingest(c,{'predictions':[{**p,'prediction_id':'future','as_of':'2026-01-03T00:00:00Z'}]})
            ingest(c,{'events':[{**e,'home_score':80,'observed_at':'2026-01-03T00:00:00Z'}]})
            assert evaluate(c)==1
            assert c.execute('SELECT outcome FROM sports.prediction_evaluations').fetchone()['outcome']==0


def test_existing_scanner_predictions_are_evaluated():
    if not os.getenv('SPORTS_DATABASE_URL'): pytest.skip('requires PostgreSQL 15+')
    from oddswatch.sql.legacy import evaluate_scanner
    with connect() as c:
        migrate(c)
        with c.transaction(force_rollback=True):
            c.execute('CREATE TABLE public.games(event_id text,league text,kickoff timestamptz)')
            c.execute('CREATE TABLE public.predictions(id bigint,event_id text,league text,model text,created_at timestamptz,market text,p_model numeric)')
            e=dict(event_id='nfl:espn:bridge',league='nfl',source='ESPN',source_event_id='bridge',home_team_id='a',away_team_id='b',home_name='A',away_name='B',kickoff='2026-01-02T12:00:00Z',season=2026,season_type='regular',status='STATUS_FINAL',home_score=20,away_score=10,observed_at='2026-01-02T15:00:00Z')
            ingest(c,{'events':[e]})
            c.execute("INSERT INTO public.predictions VALUES(1,'bridge','nfl','existing','2026-01-02T10:00:00Z','home',0.6),(2,'bridge','nfl','existing','2026-01-02T11:00:00Z','home',0.7),(3,'bridge','nfl','existing','2026-01-02T13:00:00Z','home',0.9)")
            assert evaluate_scanner(c)==2
            assert evaluate_scanner(c)==0
            row=c.execute('SELECT * FROM sports.scanner_metrics').fetchone()
            assert row['evaluated']==1
            assert float(row['brier_score'])==pytest.approx(.09)
