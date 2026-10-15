"""First-period model: home/away-aware shrinkage toward pre-match league rates."""
import csv,math
from collections import defaultdict
from datetime import date

def poisson(lam,k):
    return math.exp(-lam)*lam**k/math.factorial(k)

def rates(history,home,away,prior=12,lookback=40):
    # history: chronological (day, home, away, p1_home, p1_away)
    recent=history[-1600:]
    league_home=(sum(r[3] for r in recent)+1)/(len(recent)+1) if recent else .85
    league_away=(sum(r[4] for r in recent)+1)/(len(recent)+1) if recent else .75
    h=[r for r in history if r[1]==home][-lookback:]
    a=[r for r in history if r[2]==away][-lookback:]
    if min(len(h),len(a))<5:raise ValueError("Insufficient venue-specific first-period history")
    def shrink(values,base):
        return (sum(values)+prior*base)/(len(values)+prior)
    h_att=shrink([r[3] for r in h],league_home)
    h_def=shrink([r[4] for r in h],league_away)
    a_att=shrink([r[4] for r in a],league_away)
    a_def=shrink([r[3] for r in a],league_home)
    lh=max(.05,h_att*a_def/max(.1,league_home))
    la=max(.05,a_att*h_def/max(.1,league_away))
    return lh,la,len(h),len(a)

def probabilities(lh,la):
    h=x=a=over=0.
    for i in range(14):
        for j in range(14):
            p=poisson(lh,i)*poisson(la,j)
            if i>j:h+=p
            elif i==j:x+=p
            else:a+=p
            if i+j>=2:over+=p
    total=h+x+a
    return (h/total,x/total,a/total,over/total)

def first_period(results_path,game,lookback=40):
    day=date.fromisoformat(game["date"])
    history=[]
    with open(results_path,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            try:
                d=date.fromisoformat(r["date"][:10])
                if d>=day:continue
                history.append((d,r["home_team"],r["away_team"],int(r["p1_home"]),int(r["p1_away"])))
            except (KeyError,ValueError,TypeError):continue
    history.sort()
    lh,la,nh,na=rates(history,game["home"],game["away"],lookback=lookback)
    ph,px,pa,over=probabilities(lh,la)
    return {"p1_home_expected_goals":round(lh,3),"p1_away_expected_goals":round(la,3),
            "p1_home_fair":round(1/ph,3),"p1_draw_fair":round(1/px,3),
            "p1_away_fair":round(1/pa,3),
            "p1_over_1_5_fair":round(1/over,3),
            "p1_under_1_5_fair":round(1/(1-over),3),
            "p1_status":"PROVISIONAL_UNVALIDATED_NO_PLAY",
            "p1_home_sample":nh,"p1_away_sample":na}
