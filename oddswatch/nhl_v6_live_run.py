"""Run the NHL V6 feature bridge and independent fair-odds scorer.

Reject stale/incomplete games individually. Never create PLAY picks.
"""
import argparse
import json
from datetime import date,timedelta
from pathlib import Path
from .nhl_v6_feature_bridge import build
from .nhl_v6_prematch import score_games
from .nhl_first_period import first_period
from .nhl_moneypuck_features import load_mp_games, SBR_TO_MP, PRIORS, _ema

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
    # Actual rolling xG/xGA per team, using completed games only.
    mp_games=load_mp_games(args.moneypuck)
    for game in result:
        cutoff=date.fromisoformat(game['date'])
        codes={side:SBR_TO_MP[game[side]] for side in ('home','away')}
        states={code:dict(PRIORS) for code in codes.values()}
        for mp in mp_games:
            if mp['date']>=cutoff: break
            for code,stats in ((mp['home_code'],mp['home_stats']),(mp['away_code'],mp['away_stats'])):
                if code in states:
                    for metric in ('xgfall','xgaall','xgf5','xga5'):
                        states[code][metric]=_ema(states[code][metric],stats[metric],.10)
        for side,code in codes.items():
            game[side+'_xg_all']=round(states[code]['xgfall'],3)
            game[side+'_xga_all']=round(states[code]['xgaall'],3)
            game[side+'_xg_5v5']=round(states[code]['xgf5'],3)
            game[side+'_xga_5v5']=round(states[code]['xga5'],3)
        try:
            game.update(first_period(args.results,game))
        except ValueError as exc:
            game['first_period_status']='NO_MODEL: '+str(exc)
        game['value_status']='NO_MARKET_ODDS'
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"scheduled":len(targets),"scored":len(result),
                      "skipped":skipped,"fair_odds":result}))
    if not result:
        raise RuntimeError("No verified V6 fair odds: see skipped reasons above")

if __name__=="__main__":main()
