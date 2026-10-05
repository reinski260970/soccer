"""M17: independent rolling-feature multinomial fair-odds model.

No bookmaker odds are model features.

Pipeline per league:
- Build strictly pre-match rolling team features from historical matches.
- Train multinomial logistic model on 2017/18-2022/23.
- Choose model regularization/calibration on 2023/24 by outcome logloss only.
- Choose entry gate on 2024/25 by CLV only (market is evaluation/entry, never a feature).
- Diagnose on 2025/26. Since 2025/26 has already been inspected, it is NOT a fresh live-validation holdout.

Features are all pre-match:
goal/xG for-against EWMAs, shot-on-target for-against EWMAs, points form,
home/away splits, rest differential, sample confidence and league baselines.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import pricing
from .m13_research import load_real_xg
from .m14_research import load_league, train_proxy
from .models.poisson import Match

OUT = Path("data/m17_validation.json")

TOP5 = {
    "bundesliga": "D1", "epl": "E0", "laliga": "SP1",
    "seriea": "I1", "ligue1": "F1",
}
EUROPE = {
    "2bundesliga": "D2", "championship": "E1", "eredivisie": "N1",
    "primeira": "P1", "belgium": "B1", "turkey": "T1",
    "scotland": "SC0", "greece": "G1",
}

EDGE_GRID = (0.02, 0.03, 0.05, 0.075, 0.10)
ODDS_CAP = (2.0, 2.5, 3.0, 4.0, 6.0)
SIDES = ("all", "home", "draw", "away")
CALIB = (0.70, 0.85, 1.00, 1.15)
L2_GRID = (0.03, 0.1, 0.3, 1.0, 3.0)


@dataclass
class TeamState:
    n: int = 0
    gf: float = 1.35
    ga: float = 1.35
    xf: float = 1.35
    xa: float = 1.35
    sf: float = 4.5
    sa: float = 4.5
    pts: float = 1.35
    home_gf: float = 1.45
    home_ga: float = 1.20
    away_gf: float = 1.20
    away_ga: float = 1.45
    last_date: date | None = None


def _ew(old: float, new: float, alpha: float) -> float:
    return (1.0 - alpha) * old + alpha * new


def _xg(m: Match, home: bool) -> float:
    v = m.home_xg if home else m.away_xg
    if v is None:
        return float(m.home_goals if home else m.away_goals)
    return float(v)


def _points(gf: float, ga: float) -> float:
    return 3.0 if gf > ga else (1.0 if gf == ga else 0.0)


def _rest(st: TeamState, d: date) -> float:
    if st.last_date is None:
        return 7.0
    return float(max(2, min(14, (d - st.last_date).days)))


def _features(hs: TeamState, as_: TeamState, league: dict, d: date) -> list[float]:
    # Signed home-minus-away strengths and total/uncertainty context.
    conf_h = min(hs.n, 20) / 20.0
    conf_a = min(as_.n, 20) / 20.0
    return [
        1.0,
        hs.gf - as_.ga,
        as_.gf - hs.ga,
        hs.xf - as_.xa,
        as_.xf - hs.xa,
        hs.sf - as_.sa,
        as_.sf - hs.sa,
        hs.pts - as_.pts,
        hs.home_gf - as_.away_ga,
        as_.away_gf - hs.home_ga,
        _rest(hs, d) - _rest(as_, d),
        conf_h - conf_a,
        league["home_rate"] - league["away_rate"],
        league["draw_rate"],
        league["goals"],
    ]


def _update(st: TeamState, gf: float, ga: float, xf: float, xa: float,
            sf: float, sa: float, pts: float, d: date, is_home: bool,
            alpha: float = 0.16) -> None:
    st.n += 1
    st.gf = _ew(st.gf, gf, alpha)
    st.ga = _ew(st.ga, ga, alpha)
    st.xf = _ew(st.xf, xf, alpha)
    st.xa = _ew(st.xa, xa, alpha)
    st.sf = _ew(st.sf, sf, alpha)
    st.sa = _ew(st.sa, sa, alpha)
    st.pts = _ew(st.pts, pts, alpha)
    if is_home:
        st.home_gf = _ew(st.home_gf, gf, alpha)
        st.home_ga = _ew(st.home_ga, ga, alpha)
    else:
        st.away_gf = _ew(st.away_gf, gf, alpha)
        st.away_ga = _ew(st.away_ga, ga, alpha)
    st.last_date = d


def _softmax(z: list[float]) -> list[float]:
    m = max(z)
    ex = [math.exp(v - m) for v in z]
    s = sum(ex)
    return [v / s for v in ex]


def _calibrate(p: list[float], a: float) -> list[float]:
    q = [max(v, 1e-12) ** a for v in p]
    s = sum(q)
    return [v / s for v in q]


def _standardize(train: list[list[float]], other_sets: list[list[list[float]]]):
    p = len(train[0])
    mean = [0.0] * p
    sd = [1.0] * p
    # keep intercept column unchanged
    for j in range(1, p):
        vals = [x[j] for x in train]
        mean[j] = sum(vals) / len(vals)
        var = sum((v - mean[j]) ** 2 for v in vals) / max(len(vals) - 1, 1)
        sd[j] = max(math.sqrt(var), 1e-6)

    def tx(rows):
        return [[x[0]] + [(x[j] - mean[j]) / sd[j] for j in range(1, p)] for x in rows]

    return tx(train), [tx(r) for r in other_sets], mean, sd


def _fit_softmax(x: list[list[float]], y: list[int], l2: float,
                 epochs: int = 600, lr: float = 0.06) -> list[list[float]]:
    n, p = len(x), len(x[0])
    w = [[0.0] * p for _ in range(3)]
    for ep in range(epochs):
        g = [[0.0] * p for _ in range(3)]
        loss_scale = 1.0 / n
        for xi, yi in zip(x, y):
            pr = _softmax([sum(a*b for a,b in zip(wk, xi)) for wk in w])
            for k in range(3):
                e = (pr[k] - (1.0 if yi == k else 0.0)) * loss_scale
                for j in range(p):
                    g[k][j] += e * xi[j]
        for k in range(3):
            for j in range(1, p):
                g[k][j] += l2 * w[k][j] / n
        step = lr / (1.0 + ep / 250.0)
        for k in range(3):
            for j in range(p):
                w[k][j] -= step * g[k][j]
    return w


def _predict(w, x):
    return _softmax([sum(a*b for a,b in zip(wk, x)) for wk in w])


def _logloss(probs, ys):
    if not probs:
        return 99.0
    return -sum(math.log(max(p[y], 1e-12)) for p,y in zip(probs,ys)) / len(ys)


def _build_dataset(matches: list[Match], odds_rows: list[tuple]):
    # odds by canonical fixture
    od = {(d,h,a):(season,hg,ag,op,cl) for season,d,h,a,hg,ag,op,cl in odds_rows}
    states = defaultdict(TeamState)
    league = {"n":0, "home":0, "draw":0, "away":0, "goals":2.7,
              "home_rate":0.45, "draw_rate":0.27, "away_rate":0.28}
    samples = []

    for m in sorted(matches, key=lambda z:z.date):
        h, a, d = m.home, m.away, m.date
        hs, as_ = states[h], states[a]
        if hs.n >= 5 and as_.n >= 5:
            key=(d,h,a)
            if key in od:
                season,hg,ag,op,cl = od[key]
                y = 0 if hg > ag else (1 if hg == ag else 2)
                samples.append({
                    "season":season, "date":d, "home":h, "away":a,
                    "x":_features(hs, as_, league, d), "y":y,
                    "op":op, "cl":cl,
                })

        hg, ag = float(m.home_goals), float(m.away_goals)
        hx, ax = _xg(m, True), _xg(m, False)
        # For non-top5 proxy Match objects, xG proxy exists. For top5 it's real xG.
        # sf/sa use xG itself as a conservative chance-quality proxy when raw SoT
        # isn't carried into canonical Match.
        hpts, apts = _points(hg,ag), _points(ag,hg)
        _update(hs, hg, ag, hx, ax, hx*3.2, ax*3.2, hpts, d, True)
        _update(as_, ag, hg, ax, hx, ax*3.2, hx*3.2, apts, d, False)

        league["n"] += 1
        league["home"] += int(hg > ag)
        league["draw"] += int(hg == ag)
        league["away"] += int(hg < ag)
        n=league["n"]
        league["home_rate"]=league["home"]/n
        league["draw_rate"]=league["draw"]/n
        league["away_rate"]=league["away"]/n
        league["goals"]=_ew(league["goals"], hg+ag, 0.03)

    return samples


def _entry_stats(rows, edge, cap, side):
    idx={"home":0,"draw":1,"away":2}.get(side)
    bets=0; pnl=0.0; clv=[]
    for r in rows:
        p=r["p"]; op=r["op"]; pc=pricing.devig(r["cl"])
        for k in range(3):
            if idx is not None and k != idx:
                continue
            ev=p[k]*op[k]-1.0
            if ev < edge or op[k] > cap:
                continue
            bets += 1
            pnl += op[k]-1.0 if r["y"]==k else -1.0
            clv.append(op[k]*pc[k]-1.0)
    vals=sorted(clv)
    med=0.0
    if vals:
        n=len(vals); med=vals[n//2] if n%2 else (vals[n//2-1]+vals[n//2])/2
    return {
        "bets":bets, "clv":sum(vals)/len(vals) if vals else 0.0,
        "median_clv":med,
        "positive_clv_rate":sum(v>0 for v in vals)/len(vals) if vals else 0.0,
        "roi":pnl/bets if bets else 0.0,
    }


def _choose_gate(rows):
    best=None
    for edge in EDGE_GRID:
        for cap in ODDS_CAP:
            for side in SIDES:
                s=_entry_stats(rows,edge,cap,side)
                if s["bets"] < 35 or s["clv"] <= 0 or s["median_clv"] <= 0:
                    continue
                score=s["clv"]*math.sqrt(s["bets"])
                if best is None or score > best["score"]:
                    best={"edge":edge,"cap":cap,"side":side,"stats":s,"score":score}
    return best


def _run_league(matches, odds_rows, league):
    data=_build_dataset(matches, odds_rows)
    train=[r for r in data if r["season"] <= 2022]
    val=[r for r in data if r["season"] == 2023]
    gate_rows=[r for r in data if r["season"] == 2024]
    diag=[r for r in data if r["season"] == 2025]
    if min(len(train),len(val),len(gate_rows),len(diag)) < 80:
        return {"validated":False,"reason":"too little split data",
                "counts":[len(train),len(val),len(gate_rows),len(diag)]}

    xtr=[r["x"] for r in train]
    sets=[[r["x"] for r in z] for z in (val,gate_rows,diag)]
    xtr,(xv,xg,xd),mean,sd=_standardize(xtr,sets)
    ytr=[r["y"] for r in train]

    best=None
    for l2 in L2_GRID:
        w=_fit_softmax(xtr,ytr,l2)
        pv0=[_predict(w,x) for x in xv]
        for a in CALIB:
            pv=[_calibrate(p,a) for p in pv0]
            ll=_logloss(pv,[r["y"] for r in val])
            if best is None or ll < best["logloss"]:
                best={"l2":l2,"calib":a,"w":w,"logloss":ll}

    def attach(rows, xx):
        out=[]
        for r,x in zip(rows,xx):
            z=dict(r)
            z["p"]=_calibrate(_predict(best["w"],x),best["calib"])
            out.append(z)
        return out

    vr=attach(val,xv); gr=attach(gate_rows,xg); dr=attach(diag,xd)
    gate=_choose_gate(gr)
    diag_stats=_entry_stats(dr,gate["edge"],gate["cap"],gate["side"]) if gate else {
        "bets":0,"clv":0.0,"median_clv":0.0,"positive_clv_rate":0.0,"roi":0.0}
    # Market logloss diagnostics only
    diag_model_ll=_logloss([r["p"] for r in dr],[r["y"] for r in dr])
    diag_open_ll=_logloss([pricing.devig(r["op"]) for r in dr],[r["y"] for r in dr])

    return {
        "validated":False,
        "counts":{"train":len(train),"val2023":len(val),"gate2024":len(gate_rows),"diag2025":len(diag)},
        "l2":best["l2"],"calib":best["calib"],"val_logloss":best["logloss"],
        "gate":gate,
        "diagnostic_2025":diag_stats,
        "diagnostic_logloss":{"model":diag_model_ll,"opening":diag_open_ll,
                              "gain":diag_open_ll-diag_model_ll},
    }


def run(out: Path=OUT):
    result={"_method":"M17 rolling-feature multinomial; no market features",
            "_splits":{"train":"<=2022","model_select":2023,"entry_gate":2024,
                       "diagnostic_only":"2025"},
            "_note":"2025 is diagnostic only, not fresh validation"}
    log=["M17 rolling-feature multinomial; independent fair odds"]

    for league,code in TOP5.items():
        ms,rows,cov=load_real_xg(code)
        r=_run_league(ms,rows,league)
        result[league]=r
        d=r.get("diagnostic_2025",{})
        log.append(f"{league}: gate={r.get('gate')} | 2025 n={d.get('bets',0)} "
                   f"CLV={d.get('clv',0)*100:+.2f}% med={d.get('median_clv',0)*100:+.2f}% "
                   f"ROI={d.get('roi',0)*100:+.2f}%")

    proxy=train_proxy()
    result["_proxy"]={"n":proxy["n"],"rmse":proxy["rmse"],"beta":proxy["beta"]}
    for league,code in EUROPE.items():
        ms,rows,cov=load_league(code,proxy)
        r=_run_league(ms,rows,league)
        result[league]=r
        d=r.get("diagnostic_2025",{})
        log.append(f"{league}: gate={r.get('gate')} | 2025 n={d.get('bets',0)} "
                   f"CLV={d.get('clv',0)*100:+.2f}% med={d.get('median_clv',0)*100:+.2f}% "
                   f"ROI={d.get('roi',0)*100:+.2f}%")

    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=1,ensure_ascii=False,default=str),encoding="utf-8")
    return log


if __name__=="__main__":
    for line in run():
        print(line)
