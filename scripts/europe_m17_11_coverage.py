"""Independent no-send M17.11 European fixture / data coverage audit.

Produces inspectable JSON for every fixture and explicit gaps; never labels a
missing model prediction as PLAY or fills it with made-up numbers.
"""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone, date
from pathlib import Path
from oddswatch import scan

def main():
    now = datetime.now(timezone.utc)
    start = now.date()
    issues, notes = [], []
    games = scan.scan_soccer(start, 4, issues, notes)
    by_league = Counter(x.league for x in games)
    fixture_rows = []
    for f in games:
        fixture_rows.append({
            "league": f.league,
            "event": f.game.title,
            "kickoff": f.game.kickoff.isoformat(),
            "model": f.model,
            "status": "PREDICTION_SHADOW" if f.estimate else "PREDICTION",
            "probabilities": {k: round(v, 6) for k, v in f.probs.items()},
            "model_features": f.detail,
            "market_reference": f.ref_probs,
        })
    configured = sorted(scan.SOCCER_LEAGUES)
    data = {
        "generated_at": now.isoformat(), "scan_from": start.isoformat(),
        "horizon_days": 4, "telegram_sent": False,
        "configured_leagues": configured, "predictions_by_league": dict(by_league),
        "prediction_count": len(fixture_rows),
        "fixtures": fixture_rows, "issues": issues, "notes": notes,
    }
    path = Path("reports") / f"{start}-europe-m17_11-coverage.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {path}; {len(fixture_rows)} predictions across {len(by_league)} leagues")
    for league in configured:
        print(f"{league}: {by_league[league]} predictions")
    for issue in issues:
        if "NO_MODEL" in issue or "NO_XG" in issue or "nicht zugeordnet" in issue:
            print("GAP:", issue)
    # Do not hide complete provider failures behind an apparently green job.
    if not fixture_rows:
        raise SystemExit("NO_PREDICTIONS: investigate data provider / ESPN failures")

if __name__ == "__main__":
    main()
