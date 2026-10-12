"""NHL bulk model v6: V5 plus dual-timescale interaction features.

V6 is a research iteration motivated by regime diagnostics. It does not use
bookmaker prices as forecast inputs. Model hyperparameters remain selected on
the previous season only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .nhl_bulk_backtest import SOURCE, MIN_EV, _devig_home, _ll, load_rows
from .nhl_bulk_v5 import build_rows as build_v5_rows, FEATURES as V5_FEATURES

OUT = Path("data/hockey/nhl_bulk_v6_backtest.json")

INTERACTIONS = [
    "ix_xg_share_product",
    "ix_xg_share_abs_gap",
    "ix_xg_share_agreement",
    "ix_svaxgf_product",
    "ix_svaxga_product",
    "ix_corsi_share_product",
    "ix_xg_per_sog_for_product",
    "ix_xg_per_sog_against_product",
    "ix_hd_share_for_product",
    "ix_hd_share_against_product",
    "ix_non5v5_xgf_product",
    "ix_non5v5_xga_product",
]
FEATURES = list(V5_FEATURES) + INTERACTIONS
CS = (0.005, 0.01, 0.03, 0.1, 0.3, 1.0)
SHRINKS = (0.45, 0.60, 0.75, 0.90, 1.0)
MIN_CAL = 400
MIN_TEST = 400


def _prod(r, base):
    return float(r[f"slow_{base}"]) * float(r[f"fast_{base}"])


def _augment_interactions(r):
    q = dict(r)
    s = float(r["slow_mp_xg_share_diff"])
    f = float(r["fast_mp_xg_share_diff"])
    q["ix_xg_share_product"] = s * f
    q["ix_xg_share_abs_gap"] = abs(s - f)
    q["ix_xg_share_agreement"] = (
        1.0 if abs(s) >= .01 and abs(f) >= .01 and s*f > 0
        else -1.0 if abs(s) >= .01 and abs(f) >= .01
        else 0.0
    )
    for out, base in [
        ("ix_svaxgf_product", "mp_svaxgf_diff"),
        ("ix_svaxga_product", "mp_svaxga_diff"),
        ("ix_corsi_share_product", "mp_corsi_share_diff"),
        ("ix_xg_per_sog_for_product", "mp_xg_per_sog_for_diff"),
        ("ix_xg_per_sog_against_product", "mp_xg_per_sog_against_diff"),
        ("ix_hd_share_for_product", "mp_hd_share_for_diff"),
        ("ix_hd_share_against_product", "mp_hd_share_against_diff"),
        ("ix_non5v5_xgf_product", "mp_non5v5_xgf_diff"),
        ("ix_non5v5_xga_product", "mp_non5v5_xga_diff"),
    ]:
        q[out] = _prod(r, base)
    return q


def build_rows(raw):
    rows, u1, u2 = build_v5_rows(raw)
    return [_augment_interactions(r) for r in rows], u1, u2


def _xy(rows):
    x = np.asarray([[float(r[k]) for k in FEATURES] for r in rows], dtype=float)
    y = np.asarray([int(r["target"]) for r in rows], dtype=int)
    return x, y


def _fit(c, rows):
    x, y = _xy(rows)
    m = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=float(c), max_iter=2500, solver="lbfgs"),
    )
    m.fit(x, y)
    return m


def _pred(m, rows):
    if not rows:
        return np.asarray([])
    x, _ = _xy(rows)
    return m.predict_proba(x)[:, 1]


def _base(rows):
    return (sum(int(r["target"]) for r in rows)+1)/(len(rows)+2)


def _blend(p, b, w):
    return w*float(p)+(1-w)*b


def _select(rows, season):
    train = [r for r in rows if r["season"] < season-1]
    cal = [r for r in rows if r["season"] == season-1]
    if len(train) < 1000 or len(cal) < MIN_CAL:
        return None
    b = _base(train)
    cand = []
    for c in CS:
        m = _fit(c, train)
        raw = _pred(m, cal)
        for w in SHRINKS:
            ps = [_blend(p, b, w) for p in raw]
            ll = sum(_ll(p, bool(r["target"])) for r, p in zip(cal, ps))/len(cal)
            cand.append((ll, c, w))
    ll, c, w = min(cand, key=lambda z: (z[0], z[1], z[2]))
    return {"C": c, "shrink": w, "calibration_logloss": ll}


def evaluate(rows, season):
    train = [r for r in rows if r["season"] < season]
    test = [r for r in rows if r["season"] == season]
    choice = _select(rows, season)
    if choice is None or len(test) < MIN_TEST:
        return {"status":"INSUFFICIENT_HISTORY_OR_TEST","train_n":len(train),"test_n":len(test)}
    m = _fit(choice["C"], train)
    b = _base(train)
    probs = [_blend(p, b, choice["shrink"]) for p in _pred(m, test)]

    ml=ql=profit=clv=ev=0.0
    bets=wins=pos=0
    for r,p in zip(test, probs):
        y=bool(r["target"])
        q=_devig_home(r["home_close"], r["away_close"])
        ml += _ll(p,y); ql += _ll(q,y)
        eh=p*r["home_open"]-1
        ea=(1-p)*r["away_open"]-1
        if max(eh,ea) < MIN_EV:
            continue
        home=eh>=ea
        entry=r["home_open"] if home else r["away_open"]
        closep=q if home else 1-q
        e=eh if home else ea
        cv=closep*entry-1
        win=y if home else not y
        bets += 1; ev += e; clv += cv; pos += cv > 0
        if win:
            wins += 1; profit += entry-1
        else:
            profit -= 1
    n=len(test)
    return {
        "status":"EVALUATED","train_n":len(train),"test_n":n,
        "C":choice["C"],"shrink":choice["shrink"],
        "calibration_logloss":round(choice["calibration_logloss"],6),
        "model_logloss":round(ml/n,6),
        "market_logloss":round(ql/n,6),
        "logloss_gain_vs_market":round((ql-ml)/n,6),
        "bets":bets,"wins":wins,
        "profit_units":profit,
        "flat_roi":round(profit/bets,6) if bets else None,
        "mean_entry_ev":round(ev/bets,6) if bets else None,
        "mean_archive_clv":round(clv/bets,6) if bets else None,
        "positive_clv_rate":round(pos/bets,6) if bets else None,
        "_ml":ml,"_ql":ql,"_clv":clv,"_ev":ev,"_pos":pos,
    }


def run(path=SOURCE, dest=OUT):
    raw=load_rows(path)
    rows,u1,u2=build_rows(raw)
    seasons=sorted({r["season"] for r in rows})
    reports={str(s):evaluate(rows,s) for s in seasons if s>=2014}
    pooled=[r for r in reports.values() if r.get("status")=="EVALUATED"]
    scored=sum(r["test_n"] for r in pooled)
    bets=sum(r["bets"] for r in pooled)
    profit=sum(r["profit_units"] for r in pooled)
    ml=sum(r["_ml"] for r in pooled); ql=sum(r["_ql"] for r in pooled)
    clv=sum(r["_clv"] for r in pooled); ev=sum(r["_ev"] for r in pooled)
    pos=sum(r["_pos"] for r in pooled)
    for r in pooled:
        for k in list(r):
            if k.startswith("_"):
                del r[k]

    v5=None
    try:
        v5=json.loads(Path("data/hockey/nhl_bulk_v5_backtest.json").read_text(encoding="utf-8")).get("pooled")
    except Exception:
        pass

    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "source_odds_rows":len(raw),
        "matched_rows":len(rows),
        "slow_unmatched":len(u1),
        "fast_unmatched":len(u2),
        "market_features_used":False,
        "development_note":"interaction family motivated by post-V5 regime diagnostics; 2020/21 are no longer pristine holdouts",
        "features":FEATURES,
        "fixed_min_ev":MIN_EV,
        "release_eligible":False,
        "pooled":{
            "scored_games":scored,
            "model_logloss":round(ml/scored,6) if scored else None,
            "market_logloss":round(ql/scored,6) if scored else None,
            "logloss_gain_vs_market":round((ql-ml)/scored,6) if scored else None,
            "bets":bets,
            "profit_units":round(profit,3),
            "flat_roi":round(profit/bets,6) if bets else None,
            "mean_entry_ev":round(ev/bets,6) if bets else None,
            "mean_archive_clv":round(clv/bets,6) if bets else None,
            "positive_clv_rate":round(pos/bets,6) if bets else None,
        },
        "v5_reference":v5,
        "season_results":reports,
    }
    Path(dest).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=="__main__":
    run()
