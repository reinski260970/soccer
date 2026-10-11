"""Research-only market benchmark and fail-closed profitability release audit.

Separate model skill from trading performance: timestamped reference odds can
measure paired outcome logloss but CANNOT stand in for executable bets or CLV.
Each game counts at most once; forecast and reference are strictly prematch.
No model or betting strategy is auto-approved by this module.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable

# A meaningful sample and genuinely paired closing odds are prerequisites.
MIN_OOS_MATCHES = 250
MIN_CLV_BETS = 100
MIN_PERIOD_MATCHES = 50
CONFIDENCE_Z = 1.96
DEFAULT_COMMISSION = 0.03

# Raw odds are reference observations ONLY, not verified executable quotes.
# HOME 2-way moneylines are used to avoid counting both sides as two matches.
HOCKEY_PAIR_SQL = """
WITH forecast AS (
    SELECT DISTINCT ON (p.event_id) p.event_id, e.league, e.kickoff,
       p.model_id, p.as_of, p.probability AS p_home,
       e.home_score, e.away_score,
       p.period, p.settlement_rules
    FROM sports.predictions p
    JOIN sports.events e USING(event_id)
    WHERE e.league IN ('nhl','del','icehl','liiga','shl','extraliga','nl')
      AND e.status='STATUS_FINAL' AND e.season_type='regular'
      AND e.home_score IS NOT NULL AND e.away_score IS NOT NULL
      AND e.home_score <> e.away_score
      AND p.market='moneyline' AND p.selection='HOME'
      AND p.period='FULL_GAME' AND p.settlement_rules IN ('INCLUDING_OT','INCLUDING_OT_SO')
      AND p.as_of<e.kickoff AND p.as_of>=e.kickoff-INTERVAL '48 hours'
      AND p.probability BETWEEN 0.000001 AND 0.999999
    ORDER BY p.event_id,p.as_of DESC,p.prediction_id DESC
)
SELECT f.event_id,f.league,f.kickoff,f.model_id,f.as_of,
       f.p_home,f.home_score>f.away_score AS home_won,
       q.bookmaker, q.observed_at AS reference_observed_at,
       q.p_market,
       q.source_time_provided
FROM forecast f
JOIN LATERAL (
    SELECT h.bookmaker,h.observed_at,
      (1.0/h.odds)/((1.0/h.odds)+(1.0/a.odds)) AS p_market,
      (h.source_time IS NOT NULL AND a.source_time IS NOT NULL) AS source_time_provided
    FROM sports.odds_snapshots h
    JOIN sports.odds_snapshots a
      ON a.event_id=h.event_id AND a.market=h.market
     AND a.selection='AWAY' AND a.period=h.period
     AND a.settlement_rules=h.settlement_rules AND a.line=h.line
     AND a.bookmaker=h.bookmaker AND a.source=h.source
     AND a.observed_at=h.observed_at
    WHERE h.event_id=f.event_id
      AND h.market='moneyline' AND h.selection='HOME' AND h.period=f.period
      AND h.settlement_rules=f.settlement_rules AND h.line=0
      AND NOT h.live AND NOT a.live
      AND h.odds>1 AND a.odds>1
      AND h.observed_at<=f.as_of
      AND h.observed_at>=f.as_of-INTERVAL '6 hours'
      AND (h.source_time IS NULL OR h.source_time<=f.as_of)
      AND (a.source_time IS NULL OR a.source_time<=f.as_of)
    ORDER BY
      CASE WHEN lower(h.bookmaker)='pinnacle' THEN 0
           WHEN lower(h.bookmaker)='betfair' THEN 1 ELSE 2 END,
      h.observed_at DESC
    LIMIT 1
) q ON true
ORDER BY f.league,f.kickoff,f.event_id
"""


@dataclass(frozen=True)
class PairedResult:
    event_id: str
    league: str
    day: str
    gain_vs_market: float
    source_time_provided: bool


def exact_market_ev(probability: float, odds: float, commission: float = DEFAULT_COMMISSION) -> float:
    """Exchange commission is levied on net winnings, not the whole stake."""
    if not (math.isfinite(probability) and 0 <= probability <= 1):
        raise ValueError("probability must be between zero and one")
    if not (math.isfinite(odds) and odds > 1):
        raise ValueError("decimal odds must exceed one")
    if not (math.isfinite(commission) and 0 <= commission < 1):
        raise ValueError("commission must be between zero and one")
    return probability * (1.0 + (odds-1.0)*(1.0-commission)) - 1.0


def playable_to(probability: float, commission: float = DEFAULT_COMMISSION,
                minimum_ev: float = 0.02) -> float:
    """Minimum odds required to achieve target EV, not a recommendation to bet."""
    if not math.isfinite(probability) or not 0 < probability <= 1:
        raise ValueError("invalid probability")
    if not 0 <= minimum_ev < 1:
        raise ValueError("invalid target")
    if not 0 <= commission < 1:
        raise ValueError("invalid commission")
    return 1.0 + ((1.0 + minimum_ev) / probability - 1.0) / (1.0-commission)


def paired_result(row: dict) -> PairedResult:
    p, q = float(row["p_home"]), float(row["p_market"])
    if not 0 < p < 1 or not 0 < q < 1:
        raise ValueError("invalid paired probability")
    y = bool(row["home_won"])
    model_loss = -math.log(p if y else (1-p))
    reference_loss = -math.log(q if y else (1-q))
    kickoff = row["kickoff"]
    return PairedResult(str(row["event_id"]), str(row["league"]),
                        kickoff.date().isoformat(), reference_loss-model_loss,
                        bool(row["source_time_provided"]))


def confidence_lower(values: list[float]) -> float | None:
    """Conservative normal lower confidence bound; never sufficient alone."""
    if len(values) < 2:
        return None
    return mean(values)-CONFIDENCE_Z*stdev(values)/math.sqrt(len(values))


def audit_market(rows: Iterable[PairedResult], *,
                 closed_bet_clvs: Iterable[float] = (),
                 independently_verified_closes: bool = False) -> dict:
    """Use one result per event; duplicate source rows never inflate confidence."""
    unique: dict[str, PairedResult] = {}
    for row in rows:
        if not math.isfinite(row.gain_vs_market):
            raise ValueError("nonfinite paired logloss gain")
        if row.event_id in unique:
            raise ValueError(f"duplicate event in paired benchmark: {row.event_id}")
        unique[row.event_id] = row
    values = list(unique.values())
    gains = [v.gain_vs_market for v in values]
    periods = defaultdict(list)
    for v in values:
        periods[v.day[:7]].append(v.gain_vs_market)
    # Months are only diagnostic cohorts, NOT an additional holdout.
    period_summary = {
        month: {"matches":len(x),"average_gain":round(mean(x),6)}
        for month,x in sorted(periods.items())
    }
    clvs = list(closed_bet_clvs)
    if not all(math.isfinite(x) for x in clvs):
        raise ValueError("invalid CLV")
    clv_lower = confidence_lower(clvs) if independently_verified_closes else None
    reasons = []
    if len(values) < MIN_OOS_MATCHES:
        reasons.append(f"OOS_SAMPLE_LT_{MIN_OOS_MATCHES}")
    if confidence_lower(gains) is None or confidence_lower(gains) <= 0:
        reasons.append("NO_CONFIDENT_POSITIVE_PAIRED_LOGLOSS_GAIN")
    if sum(1 for x in periods.values() if len(x)>=MIN_PERIOD_MATCHES) < 2:
        reasons.append("NO_TWO_SEPARATE_TIME_COHORTS")
    if not independently_verified_closes:
        reasons.append("NO_AUTHENTICATED_CLOSING_LINES")
    if len(clvs) < MIN_CLV_BETS:
        reasons.append(f"MEASURED_CLV_SAMPLE_LT_{MIN_CLV_BETS}")
    if clv_lower is None or clv_lower<=0:
        reasons.append("NO_CONFIDENT_POSITIVE_CLV")
    # An audited market reference is not an approved model. Actual release
    # further requires independently validated strategy and book execution.
    reasons.append("REQUIRES_EXPLICIT_INDEPENDENT_MODEL_AND_ENTRY_APPROVAL")
    return {
        "status": "RESEARCH_ONLY_NOT_APPROVED",
        "betting_release": False,
        "unique_matches": len(values),
        "matched_reference_with_source_timestamps": sum(v.source_time_provided for v in values),
        "paired_logloss_gain_mean": round(mean(gains),6) if gains else None,
        "paired_gain_95pct_lower": round(confidence_lower(gains),6) if confidence_lower(gains) is not None else None,
        "months": period_summary,
        "verified_clv_bets": len(clvs) if independently_verified_closes else 0,
        "clv_95pct_lower": round(clv_lower,6) if clv_lower is not None else None,
        "hold_reasons": reasons,
        "notes": [
            "Reference snapshots are observational and not executable Orbit offers",
            "Model probabilities must not use bookmaker prices as features",
            "No genuine paired closing lines implies unknown CLV, never CLV=0 or positive",
            "Repeated home/away and model-snapshot observations of one event count once",
            "Financial ROI remains unproven until actually placed, settled bets are recorded",
        ]
    }


def main(path: str = "data/hockey/profitability_gate.json") -> None:
    from .sql.store import connect
    with connect() as conn:
        rows=conn.execute(HOCKEY_PAIR_SQL).fetchall()
        # sports.clv_log currently has no authentic close records; never
        # substitute model/market reference snapshots for true settled CLV.
        verified_clvs=[]
        output={}
        for league in ("nhl","del","icehl","liiga","shl","extraliga","nl"):
            pairs=[paired_result(r) for r in rows if r["league"]==league]
            output[league]=audit_market(pairs,closed_bet_clvs=verified_clvs,
                                        independently_verified_closes=False)
    data={"generated_at":datetime.now(timezone.utc).isoformat(),
          "mode":"AUDIT_ONLY_NO_AUTOMATIC_RELEASE",
          "exchange_commission":DEFAULT_COMMISSION,
          "leagues":output}
    dest=Path(path)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:{"matched_unique_games":v["unique_matches"],
                         "paired_gain":v["paired_logloss_gain_mean"],
                         "release":v["betting_release"],"reasons":v["hold_reasons"]}
                      for k,v in output.items()},ensure_ascii=False))


if __name__ == "__main__":
    main()
