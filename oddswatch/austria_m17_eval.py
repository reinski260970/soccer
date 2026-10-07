"""OOS diagnostic for M17.11-AT shadow vs available Austria closing market."""

from __future__ import annotations

import math

from . import fetch, pricing
from .m17_at_shadow import _build, _choose_hyper
from .m17_1_research import _calibrate, _fit, _logloss, _pred, _standardizer, _tx
from .sources import football_data


def run() -> list[str]:
    text, err = fetch.get(football_data.AUT_URL, cache_days=0)
    if text is None:
        raise RuntimeError(err)
    matches, odds = football_data.parse_new_league(text)
    rows, _, _, _ = _build(matches)
    hyper = _choose_hyper(rows)

    train = [r for r in rows if r["season"] < 2025]
    test = [r for r in rows if r["season"] == 2025]
    mean, sd = _standardizer([r["x"] for r in train])
    w = _fit(_tx([r["x"] for r in train], mean, sd),
             [r["y"] for r in train], hyper["l2"])
    pp = [
        _calibrate(_pred(w, x), hyper["calib"])
        for x in _tx([r["x"] for r in test], mean, sd)
    ]
    model_ll = _logloss(pp, [r["y"] for r in test])

    pmap = {
        (o.date, o.home, o.away): pricing.devig(o.b365_closing)
        for o in odds if o.b365_closing is not None
    }
    matched_model = []
    matched_market = []
    matched_y = []
    for r, p in zip(test, pp):
        m = pmap.get((r["date"], r["home"], r["away"]))
        if m is None:
            continue
        matched_model.append(p)
        matched_market.append(m)
        matched_y.append(r["y"])

    if matched_y:
        model_matched_ll = _logloss(matched_model, matched_y)
        market_ll = _logloss(matched_market, matched_y)
    else:
        model_matched_ll = market_ll = float("nan")

    def brier(probs, ys):
        if not ys:
            return float("nan")
        s = 0.0
        for p, y in zip(probs, ys):
            for k in range(3):
                s += (p[k] - (1.0 if y == k else 0.0)) ** 2
        return s / len(ys)

    return [
        f"AUT M17.11-AT hyper l2={hyper['l2']} calib={hyper['calib']} CV_LL={hyper['cv_logloss']:.6f}",
        f"2025 OOS events={len(test)} model_LL={model_ll:.6f}",
        f"2025 market-matched n={len(matched_y)} model_LL={model_matched_ll:.6f} closing_LL={market_ll:.6f} gain={market_ll-model_matched_ll:+.6f}",
        f"2025 matched Brier model={brier(matched_model, matched_y):.6f} closing={brier(matched_market, matched_y):.6f}",
        "RELEASE=" + ("YES" if matched_y and model_matched_ll < market_ll else "NO"),
    ]


if __name__ == "__main__":
    for line in run():
        print(line)
