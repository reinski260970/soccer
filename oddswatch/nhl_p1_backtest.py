"""Walk-forward NHL first-period 1X2 calibration diagnostic (no odds, no PLAY)."""
import argparse,csv,json,math
from collections import defaultdict,deque
from datetime import date
from pathlib import Path
from .nhl_first_period import poisson

def probabilities(lh,la):
    h=x=a=0.
    for i in range(13):
        for j in range(13):
            p=poisson(lh,i)*poisson(la,j)
            if i>j:h+=p
            elif i==j:x+=p
            else:a+=p
    total=h+x+a
    return [h/total,x/total,a/total]

def evaluate(path):
    rows=[]
    with open(path,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            try:
                rows.append((date.fromisoformat(r["date"][:10]),r["home_team"],r["away_team"],int(r["p1_home"]),int(r["p1_away"])))
            except (KeyError,ValueError,TypeError):continue
    rows.sort()
    history=defaultdict(lambda:deque(maxlen=30))
    scored=[];baseline_counts=[1,1,1]
    i=0
    while i<len(rows):
        day=rows[i][0];j=i
        while j<len(rows) and rows[j][0]==day:j+=1
        for _,home,away,hg,ag in rows[i:j]:
            h,a=history[home],history[away]
            if min(len(h),len(a))<10:continue
            lh=max(.05,(sum(v[0] for v in h)/len(h)+sum(v[1] for v in a)/len(a))/2)
            la=max(.05,(sum(v[0] for v in a)/len(a)+sum(v[1] for v in h)/len(h))/2)
            ps=probabilities(lh,la); outcome=0 if hg>ag else (1 if hg==ag else 2)
            base=[n/sum(baseline_counts) for n in baseline_counts]
            scored.append((day,ps,outcome,base))
        for _,home,away,hg,ag in rows[i:j]:
            history[home].append((hg,ag))
            history[away].append((ag,hg))
            baseline_counts[0 if hg>ag else (1 if hg==ag else 2)]+=1
        i=j
    if not scored:raise RuntimeError("No chronologically valid first-period predictions")
    def ll(p,y):return -math.log(max(p[y],1e-12))
    model=sum(ll(p,y) for _,p,y,_ in scored)/len(scored)
    base=sum(ll(b,y) for _,_,y,b in scored)/len(scored)
    # This is an in-sample diagnostic of the fixed, unoptimized formula.
    report={"model":"NHL_P1_POISSON_BASELINE","games_with_periods":len(rows),
            "walk_forward_predictions":len(scored),"first_date":str(scored[0][0]),
            "last_date":str(scored[-1][0]),"model_logloss":round(model,6),
            "rolling_baseline_logloss":round(base,6),
            "logloss_gain_vs_baseline":round(base-model,6),
            "status":"DIAGNOSTIC_ONLY_NO_CLV_NO_MARKET_ODDS_NO_PLAY"}
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--results",required=True)
    p.add_argument("--out",default="data/hockey/nhl_p1_walkforward.json")
    a=p.parse_args();result=evaluate(a.results)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))

if __name__=="__main__":main()
