"""Scoreboard ingestion and overdue recovery; no publishing side effects."""
import json
from urllib.request import urlopen, Request
from datetime import datetime, timezone, timedelta
from .store import ingest, capture_closing
from .evaluation import evaluate
PATHS={'nba':'basketball/nba','nfl':'football/nfl'}


def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'SportsResearch/1.0'}),timeout=30) as r:
        return json.load(r)


def parse(data,league,observed):
    if league not in PATHS: raise ValueError('unsupported league')
    result=[]
    for event in data.get('events',[]):
        comp=event['competitions'][0]
        teams={c['homeAway']:c for c in comp['competitors']}
        h,a=teams['home'],teams['away']
        st=event.get('season',data.get('season',{}))
        kind=st.get('type',2)
        if isinstance(kind,dict): kind=kind.get('type',kind.get('id'))
        kind={1:'preseason',2:'regular',3:'postseason'}.get(int(kind))
        if kind is None: raise ValueError('unknown season type')
        status=event['status']['type']['name']
        result.append(dict(event_id=f'{league}:espn:{event["id"]}',league=league,source='ESPN',source_event_id=event['id'],
          home_team_id=h['team']['id'],away_team_id=a['team']['id'],home_name=h['team']['displayName'],away_name=a['team']['displayName'],
          kickoff=event['date'],season=st['year'],season_type=kind,status=status,
          home_score=h.get('score') if status=='STATUS_FINAL' else None,away_score=a.get('score') if status=='STATUS_FINAL' else None,
          observed_at=observed))
    return result


def run(conn, start, days=3, leagues=('nba','nfl')):
    if not 1<=days<=31: raise ValueError('days must be 1..31')
    total=0
    for league in leagues:
        path=PATHS[league]
        dates={start+timedelta(days=n) for n in range(-1,days)}
        # Recover every pending prediction regardless of age, including postponed games.
        pending=conn.execute("SELECT DISTINCT e.kickoff FROM sports.events e JOIN sports.predictions p USING(event_id) "
          "LEFT JOIN sports.prediction_evaluations v USING(prediction_id) WHERE e.league=%s AND v.prediction_id IS NULL",(league,)).fetchall()
        dates.update(r['kickoff'].date() for r in pending)
        for day in sorted(dates):
            url=f'https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard?dates={day:%Y%m%d}&limit=1000'
            data=fetch(url); observed=datetime.now(timezone.utc)
            if 'events' not in data: raise ValueError('invalid scoreboard')
            bundle={'events':parse(data,league,observed),'raw_payloads':[dict(source='ESPN',resource=url,observed_at=observed,payload=data)]}
            total+=ingest(conn,bundle).get('events',0)
        # Summary endpoint locates overdue events even after a changed kickoff date.
        ids=conn.execute("SELECT DISTINCT e.source_event_id FROM sports.events e JOIN sports.predictions p USING(event_id) "
          "LEFT JOIN sports.prediction_evaluations v USING(prediction_id) WHERE e.league=%s AND e.source='ESPN' "
          "AND v.prediction_id IS NULL AND e.kickoff<now()",(league,)).fetchall()
        for row in ids:
            url=f'https://site.api.espn.com/apis/site/v2/sports/{path}/summary?event={row["source_event_id"]}'
            data=fetch(url); header=data['header']; observed=datetime.now(timezone.utc)
            comp=header['competitions'][0]
            event={**header,'date':comp['date'],'status':comp['status']}
            ingest(conn,{'events':parse({'events':[event]},league,observed),
              'raw_payloads':[dict(source='ESPN',resource=url,observed_at=observed,payload=data)]})
    return {'events':total,'evaluated':evaluate(conn),'closing':capture_closing(conn)}
