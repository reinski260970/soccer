"""Independent NHL first-period goal model with transparent provisional status."""
import csv
import math
from collections import defaultdict
from datetime import date

def poisson(lam,k):
    return math.exp(-lam)*lam**k/math.factorial(k)

def first_period(results_path, game, lookback=30):
    day=date.fromisoformat(game["date"])
    history=defaultdict(list)
    with open(results_path,encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            try:
                d=date.fromisoformat(r["date"][:10])
                if d>=day:continue
                hg,ag=int(r["p1_home"]),int(r["p1_away"])
                history[r["home_team"]].append((d,hg,ag))
                history[r["away_team"]].append((d,ag,hg))
            except (KeyError,ValueError,TypeError):continue
    home,away=game["home"],game["away"]
    h=sorted(history[home],reverse=True)[:lookback]
    a=sorted(history[away],reverse=True)[:lookback]
    if min(len(h),len(a))<10:
        raise ValueError("Insufficient first-period history")
    def mean(rows,idx):
        return sum(r[idx] for r in rows)/len(rows)
    # Independent attack/defence average, not full-game V6 probabilities.
    lh=max(.05,(mean(h,1)+mean(a,2))/2)
    la=max(.05,(mean(a,1)+mean(h,2))/2)
    ph=px=pa=over=0.
    for i in range(16):
        for j in range(16):
            prob=poisson(lh,i)*poisson(la,j)
            if i>j:ph+=prob
            elif i==j:px+=prob
            else:pa+=prob
            if i+j>=2:over+=prob
    return {"p1_home_expected_goals":round(lh,3),"p1_away_expected_goals":round(la,3),
            "p1_home_fair":round(1/ph,3),"p1_draw_fair":round(1/px,3),
            "p1_away_fair":round(1/pa,3),
            "p1_over_1_5_fair":round(1/over,3),
            "p1_under_1_5_fair":round(1/(1-over),3),
            "p1_status":"PROVISIONAL_UNVALIDATED_NO_PLAY",
            "p1_home_sample":len(h),"p1_away_sample":len(a)}
