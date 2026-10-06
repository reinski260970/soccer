"""Sharperty research export for individual M17.1 OOS candidates.

Purpose:
- expose every individual 2025/26 M17.1 research candidate to Sharpery
- fixed rule, not tuned on 2025/26: model EV >= 3%, opening odds <= 6.00
- no negative-EV rows
- market odds are never model features; they are used only after fair probabilities exist
- 1 EH = 10 EUR

Important: M17.1 has no validated entry gate. These rows are RESEARCH/OOS candidates,
not live-approved plays.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from . import pricing
from .m13_research import load_real_xg
from .m14_research import load_league, train_proxy
from .m17_1_research import (
    TOP5, EUROPE, build_dataset, load_real_shots,
    _select_hyper, _fit_predict,
)

COLUMNS = [
    "Placed At", "Kickoff", "Event", "Sport", "League", "Market", "Selection",
    "Period", "Bookmaker", "Opening Odds", "Bet Odds", "Closing Novig Odds",
    "EV %", "CLV %", "Stake", "Result", "Liquidity", "Live", "Side", "Notes", "Tags"
]
SIDE = ("home", "draw", "away")
SEL = ("Home", "Draw", "Away")
MIN_EDGE = 0.03
MAX_ODDS = 6.0
STAKE_EUR = 10.0


def _league_rows(matches, odds_rows, shots, league: str):
    data = build_dataset(matches, odds_rows, shots)
    hyper = _select_hyper(data)
    if hyper is None:
        return [], {"league": league, "reason": "no hyper model"}

    train = [r for r in data if r["season"] <= 2024]
    diag = [r for r in data if r["season"] == 2025]
    if not train or not diag:
        return [], {"league": league, "reason": "no 2025 diagnostic rows"}

    probs = _fit_predict(train, diag, hyper["l2"], hyper["calib"])
    out = []
    for r, p in zip(diag, probs):
        op = r["op"]
        close_p = pricing.devig(r["cl"])
        result_idx = r["y"]
        d = r["date"]
        placed = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).isoformat()

        for k in range(3):
            ev = p[k] * op[k] - 1.0
            if ev < MIN_EDGE or op[k] > MAX_ODDS:
                continue
            clv = op[k] * close_p[k] - 1.0
            fair = 1.0 / max(p[k], 1e-12)
            close_fair = 1.0 / max(close_p[k], 1e-12)
            out.append({
                "Placed At": placed,
                "Kickoff": placed,
                "Event": f"{r['home']} vs {r['away']}",
                "Sport": "Soccer",
                "League": league,
                "Market": "1X2",
                "Selection": SEL[k],
                "Period": "Regular Time",
                "Bookmaker": "Pinnacle",
                "Opening Odds": round(op[k], 4),
                "Bet Odds": round(op[k], 4),
                "Closing Novig Odds": round(close_fair, 4),
                "EV %": round(ev * 100, 2),
                "CLV %": round(clv * 100, 2),
                "Stake": STAKE_EUR,
                "Result": "won" if k == result_idx else "lost",
                "Liquidity": "",
                "Live": "no",
                "Side": SIDE[k],
                "Notes": (
                    f"M17.1 RESEARCH OOS 2025/26; Fair {fair:.3f}; "
                    f"fixed EV >=3%; max odds 6.00; gate=None; not live-approved"
                ),
                "Tags": "BACKTEST;OOS;CLV;M17.1;RESEARCH",
            })
    return out, {
        "league": league,
        "samples": len(data),
        "diag_rows": len(diag),
        "candidates": len(out),
        "l2": hyper["l2"],
        "calib": hyper["calib"],
    }


def run(out_path: str = "exports/m17_1_sharpery_research.csv"):
    bets = []
    diagnostics = []

    for league, code in TOP5.items():
        ms, rows, _ = load_real_xg(code)
        shots = load_real_shots(code)
        rr, dd = _league_rows(ms, rows, shots, league)
        bets.extend(rr)
        diagnostics.append(dd)

    proxy = train_proxy()
    for league, code in EUROPE.items():
        ms, rows, _ = load_league(code, proxy)
        shots = load_real_shots(code)
        rr, dd = _league_rows(ms, rows, shots, league)
        bets.extend(rr)
        diagnostics.append(dd)

    bets.sort(key=lambda r: (r["Kickoff"], r["League"], r["Event"], r["Side"]))
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(bets)

    n = len(bets)
    avg_clv = sum(float(r["CLV %"]) for r in bets) / n if n else 0.0
    pos_clv = sum(1 for r in bets if float(r["CLV %"]) > 0) / n if n else 0.0
    wins = [r for r in bets if r["Result"] == "won"]
    pnl = sum(float(r["Bet Odds"]) - 1.0 for r in wins) - (n - len(wins))
    print(f"M17.1 SHARPERY BETS={n} AVG_CLV={avg_clv:+.3f}% POS_CLV={pos_clv*100:.1f}% ROI={(pnl/n*100 if n else 0):+.2f}%")
    print("DIAG", diagnostics)
    print(p)
    return p, bets, diagnostics


if __name__ == "__main__":
    run()
