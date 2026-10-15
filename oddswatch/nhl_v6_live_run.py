"""Run the NHL V6 feature bridge and independent fair-odds scorer.

Reject stale/incomplete games individually. Never create PLAY picks.
"""
import argparse
import json
from datetime import date,timedelta
from pathlib import Path
from .nhl_v6_feature_bridge import build
from .nhl_v6_prematch import score_games

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--results",required=True)
    p.add_argument("--moneypuck",required=True)
    p.add_argument("--schedule",required=True)
    p.add_argument("--out",default="data/hockey/nhl_v6_fair_today.json")
    p.add_argument("--horizon",type=int,default=3)
    args=p.parse_args()
    today=date.today()
    schedule=json.loads(Path(args.schedule).read_text())
    targets=[g for g in schedule if today<=date.fromisoformat(g["date"])<=today+timedelta(days=args.horizon)]
    features=[];skipped=[]
    for target in targets:
        try:
            features.extend(build([target],args.results,args.moneypuck))
        except (ValueError,KeyError,TypeError) as e:
            skipped.append({"game":target,"reason":str(e)})
    result=score_games(features) if features else []
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"scheduled":len(targets),"scored":len(result),
                      "skipped":skipped,"fair_odds":result}))
    if not result:
        raise RuntimeError("No verified V6 fair odds: see skipped reasons above")

if __name__=="__main__":main()
