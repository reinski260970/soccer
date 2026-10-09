import argparse
import json
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo
from .store import connect, migrate, ingest, capture_closing
from .evaluation import evaluate
from .runner import run


def main():
    parser=argparse.ArgumentParser(description='NBA/NFL internal PostgreSQL store')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('migrate','evaluate','clv','report','hockey-settle','soccer-settle'): sub.add_parser(name)
    imp=sub.add_parser('ingest'); imp.add_argument('file')
    sync=sub.add_parser('sync'); sync.add_argument('--start',type=date.fromisoformat,default=datetime.now(ZoneInfo('Europe/Vienna')).date())
    sync.add_argument('--days',type=int,default=3)
    args=parser.parse_args()
    with connect() as conn:
        migrate(conn)
        if args.command=='ingest':
            with open(args.file) as f: result=ingest(conn,json.load(f))
            result['evaluated']=evaluate(conn)
        elif args.command=='sync': result=run(conn,args.start,args.days)
        elif args.command=='hockey-settle':
            from .hockey_settlement import run as settle_hockey
            result=settle_hockey(conn)
        elif args.command=='soccer-settle':
            from .soccer_settlement import run as settle_soccer
            result=settle_soccer(conn)
        elif args.command=='evaluate': result={'evaluated':evaluate(conn)}
        elif args.command=='clv': result=capture_closing(conn)
        elif args.command=='report':
            result={name:conn.execute(f'SELECT * FROM sports.{name}').fetchall() for name in ('model_metrics','calibration','performance','scanner_metrics','forward_market_comparison','result_coverage')}
            result['pending']=conn.execute("SELECT e.league,count(*) AS pending,min(e.kickoff) AS oldest FROM sports.predictions p JOIN sports.events e USING(event_id) LEFT JOIN sports.prediction_evaluations v USING(prediction_id) WHERE v.prediction_id IS NULL AND e.kickoff<now() GROUP BY e.league").fetchall()
        else: result={'migration':'OK'}
    print(json.dumps(result,default=str,ensure_ascii=False))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'SQL runner failed ({type(exc).__name__}); inspect configuration/source availability. Credentials redacted.',file=sys.stderr)
        sys.exit(1)
