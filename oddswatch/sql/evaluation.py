"""Internal evaluation of ALL predictions, independent of publication or stakes."""
import math
from datetime import datetime, timezone
from decimal import Decimal


def outcome(p, home, away):
    # Only explicit full-game including OT, push-on-tie contracts supported.
    if p['period'] != 'FULL_GAME' or p['settlement_rules'] != 'INCLUDING_OT_PUSH_ON_TIE':
        return None
    h,a=Decimal(str(home)),Decimal(str(away))
    line=Decimal(str(p['line']))
    if p['market'] in ('moneyline','spread') and p['selection'] in ('HOME','AWAY'):
        margin=h-a if p['selection']=='HOME' else a-h
        if p['market']=='spread':
            if line*2 != (line*2).to_integral_value(): return None
            margin+=line
    elif p['market']=='total' and p['selection'] in ('OVER','UNDER'):
        if line*2 != (line*2).to_integral_value(): return None
        margin=(h+a-line)*(1 if p['selection']=='OVER' else -1)
    else:
        return None
    return 'WIN' if margin>0 else 'LOSE' if margin<0 else 'PUSH'


def evaluate(conn):
    updated=0
    with conn.transaction():
        rows=conn.execute("SELECT p.*,e.home_score,e.away_score,e.observed_at,e.source FROM sports.predictions p "
          "JOIN sports.events e USING(event_id) WHERE e.status='STATUS_FINAL' "
          "AND e.home_score IS NOT NULL AND e.away_score IS NOT NULL AND e.season_type<>'preseason'").fetchall()
        for p in rows:
            result=outcome(p,p['home_score'],p['away_score'])
            if result is None: continue
            y=None if result=='PUSH' else int(result=='WIN')
            prob=float(p['probability'])
            brier=None if y is None else (prob-y)**2
            loss=None if y is None else -math.log(prob if y else 1-prob)
            # Re-evaluate changed official scores; unchanged runs are idempotent.
            updated+=conn.execute('INSERT INTO sports.prediction_evaluations VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
              'ON CONFLICT(prediction_id) DO UPDATE SET result=excluded.result,outcome=excluded.outcome,'
              'brier=excluded.brier,log_loss=excluded.log_loss,evaluated_at=excluded.evaluated_at,'
              'result_observed_at=excluded.result_observed_at,home_score=excluded.home_score,away_score=excluded.away_score,source=excluded.source '
              'WHERE (sports.prediction_evaluations.home_score,sports.prediction_evaluations.away_score) '
              'IS DISTINCT FROM (excluded.home_score,excluded.away_score)',
              (p['prediction_id'],result,y,brier,loss,datetime.now(timezone.utc),p['observed_at'],p['home_score'],p['away_score'],p['source'])).rowcount
    return updated
