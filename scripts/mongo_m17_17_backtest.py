"""Read-only M17.17 soccer walk-forward evaluation from Soccer Mongo.

No production PLAY release: 2024 is retrospective stress (previously inspected),
2025 is diagnostic, and new forward/shadow CLV is still required.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from oddswatch import m17_17_research as model

LEAGUE_GROUPS = {
    "germany": {"bundesliga": "D1", "2bundesliga": "D2"},
    "top5-other": {"epl": "E0", "laliga": "SP1", "seriea": "I1", "ligue1": "F1"},
    "europe": {
        "championship": "E1",
        "eredivisie": "N1",
        "primeira": "P1",
        "belgium": "B1",
        "turkey": "T1",
        "scotland": "SC0",
        "greece": "G1",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=tuple(LEAGUE_GROUPS), required=True)
    args = parser.parse_args()
    if not (os.environ.get("MONGO_SOCCER") or os.environ.get("MONGODB_URI")):
        raise RuntimeError("Soccer Mongo credentials missing; no backtest run")
    model.FOCUS = LEAGUE_GROUPS[args.group]
    out = Path(f"reports/mongo_m17_17_{args.group}.json")
    for line in model.run(out=out):
        print(line, flush=True)
    result = json.loads(out.read_text(encoding="utf-8"))
    good = 0
    print("xG proxy train seasons:", result.get("_proxy", {}).get("train_seasons"), flush=True)
    print("Chronology:", result.get("_temporal_integrity"), flush=True)
    print("\n=== LIGAERGEBNISSE ===", flush=True)
    for name, row in result["leagues"].items():
        stress = row.get("retrospective_stress_2024") or {}
        ll = row.get("retrospective_stress_logloss_2024") or {}
        validation = row.get("entry_validation_2023") or {}
        coverage = row.get("coverage") or {}
        diag = row.get("probability_diagnostics") or {}
        if row.get("samples", 0) and ll.get("model", 0) < 8:
            good += 1
        print(json.dumps({
            "league": name,
            "samples": row.get("samples"),
            "proxy_coverage": coverage.get("proxy_coverage"),
            "odds_rows": coverage.get("odds_rows"),
            "canonical_score_matched": coverage.get("canonical_team_score_fixed"),
            "2024_model_oos_games": (diag.get("2024") or {}).get("n"),
            "2024_calibration_gaps": (diag.get("2024") or {}).get("gap_pred_minus_actual"),
            "2025_diagnostic_games": (diag.get("2025") or {}).get("n"),
            "2023_gate_survived": row.get("gate_survived_2023"),
            "2023_bets": validation.get("bets"),
            "2023_clv": validation.get("clv"),
            "2024_bets": stress.get("bets"),
            "2024_mean_clv": stress.get("clv"),
            "2024_positive_clv_rate": stress.get("positive_clv_rate"),
            "2024_roi": stress.get("roi"),
            "2024_model_logloss": ll.get("model"),
            "2024_market_logloss": ll.get("opening"),
            "2024_logloss_gain": ll.get("gain"),
            "release_eligible": False,
            "error": row.get("reason"),
        }, ensure_ascii=False), flush=True)
    if not good:
        raise RuntimeError(f"No valid soccer backtest results in {args.group}; check Mongo or coverage")


if __name__ == "__main__":
    main()
