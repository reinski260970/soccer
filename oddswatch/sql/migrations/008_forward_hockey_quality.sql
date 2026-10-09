-- A later model refresh is not an additional independent match.
-- Evaluate the LAST genuinely prematch forecast per event, model, exact market.
CREATE OR REPLACE VIEW sports.model_metrics AS
WITH latest AS (
 SELECT DISTINCT ON (p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules)
        p.*
 FROM sports.predictions p
 JOIN sports.events e USING(event_id)
 WHERE p.as_of < e.kickoff
 ORDER BY p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules,
          p.as_of DESC,p.prediction_id DESC
)
SELECT e.league,p.model_id,p.market,p.period,p.settlement_rules,
 count(*) AS evaluated,count(v.outcome) AS scored,
 count(*) FILTER (WHERE v.result='PUSH') AS pushes,
 avg(v.outcome) AS selection_win_rate,
 avg((v.outcome=(p.probability>=0.5)::integer)::integer) AS classification_accuracy,
 avg(v.brier) AS brier_score,avg(v.log_loss) AS log_loss
FROM latest p
JOIN sports.events e USING(event_id)
JOIN sports.prediction_evaluations v USING(prediction_id)
GROUP BY e.league,p.model_id,p.market,p.period,p.settlement_rules;

CREATE OR REPLACE VIEW sports.calibration AS
WITH latest AS (
 SELECT DISTINCT ON (p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules)
        p.*
 FROM sports.predictions p
 JOIN sports.events e USING(event_id)
 WHERE p.as_of < e.kickoff
 ORDER BY p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules,
          p.as_of DESC,p.prediction_id DESC
)
SELECT e.league,p.model_id,p.market,least(9,floor(p.probability*10)) AS bucket,
 count(*) AS n,avg(p.probability) AS predicted,avg(v.outcome) AS observed
FROM latest p
JOIN sports.events e USING(event_id)
JOIN sports.prediction_evaluations v USING(prediction_id)
WHERE v.outcome IS NOT NULL
GROUP BY e.league,p.model_id,p.market,least(9,floor(p.probability*10));

-- Use ONLY a contemporaneous complete 2-way book as the market baseline.
-- This is a snapshot comparison, NOT a proof of CLV or executable liquidity.
CREATE OR REPLACE VIEW sports.forward_market_comparison AS
WITH latest AS (
 SELECT DISTINCT ON (p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules)
        p.*
 FROM sports.predictions p
 JOIN sports.events e USING(event_id)
 WHERE p.as_of < e.kickoff
   AND p.market = 'moneyline' AND p.selection IN ('HOME','AWAY')
   AND p.period = 'FULL_GAME'
 ORDER BY p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules,
          p.as_of DESC,p.prediction_id DESC
), scored AS (
 SELECT e.league,p.model_id,p.event_id,p.market,p.period,
        p.as_of,p.probability,v.outcome,v.log_loss AS model_logloss,
        q.reference_probability,q.source_reference
 FROM latest p
 JOIN sports.events e USING(event_id)
 JOIN sports.prediction_evaluations v USING(prediction_id)
 JOIN LATERAL (
    SELECT
       (1.0/o.odds)/((1.0/o.odds)+(1.0/other.odds)) AS reference_probability,
       o.bookmaker AS source_reference
    FROM sports.odds_snapshots o
    JOIN sports.odds_snapshots other
      ON other.event_id=o.event_id AND other.market=o.market
      AND other.period=o.period AND other.settlement_rules=o.settlement_rules
      AND other.line=o.line AND other.bookmaker=o.bookmaker
      AND other.source=o.source AND other.observed_at=o.observed_at
      AND other.selection=CASE WHEN o.selection='HOME' THEN 'AWAY' ELSE 'HOME' END
    WHERE o.event_id=p.event_id AND o.market=p.market
      AND o.selection=p.selection AND o.period=p.period
      AND o.settlement_rules=p.settlement_rules
      AND o.line=p.line AND o.live=false AND other.live=false
      AND o.observed_at<=p.as_of AND o.observed_at>=p.as_of-INTERVAL '6 hours'
      AND (o.source_time IS NULL OR o.source_time<=p.as_of)
      AND (other.source_time IS NULL OR other.source_time<=p.as_of)
    ORDER BY CASE WHEN lower(o.bookmaker)='pinnacle' THEN 0
                  WHEN lower(o.bookmaker)='betfair' THEN 1 ELSE 2 END,
             o.observed_at DESC
    LIMIT 1
 ) q ON true
 WHERE v.outcome IS NOT NULL
)
SELECT league,model_id,market,period,source_reference,
       COUNT(DISTINCT event_id) AS matches,
       COUNT(*) AS outcomes,
       AVG(model_logloss) AS model_logloss,
       AVG(-CASE WHEN outcome=1 THEN LN(reference_probability)
                 ELSE LN(1-reference_probability) END) AS market_logloss,
       AVG(-CASE WHEN outcome=1 THEN LN(reference_probability)
                 ELSE LN(1-reference_probability) END)-AVG(model_logloss)
         AS logloss_gain_vs_market
FROM scored
GROUP BY league,model_id,market,period,source_reference;

CREATE OR REPLACE VIEW sports.result_coverage AS
SELECT e.league,
       COUNT(DISTINCT e.event_id) AS events,
       COUNT(DISTINCT e.event_id) FILTER (WHERE e.status='STATUS_FINAL') AS final_events,
       COUNT(DISTINCT p.prediction_id) AS prediction_rows,
       COUNT(DISTINCT v.prediction_id) AS evaluated_rows
FROM sports.events e
LEFT JOIN sports.predictions p USING(event_id)
LEFT JOIN sports.prediction_evaluations v USING(prediction_id)
GROUP BY e.league;
