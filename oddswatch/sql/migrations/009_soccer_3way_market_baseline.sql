-- Proper market benchmark for soccer 1X2.
-- Soccer is a three-outcome market: HOME/DRAW/AWAY must be de-vigged together.
-- Only coherent model triplets (all three outcomes within five minutes, probabilities
-- summing to ~1) are admitted. Hockey/US full-game moneylines keep the strict 2-way path.

CREATE OR REPLACE VIEW sports.forward_market_comparison AS
WITH latest AS (
  SELECT DISTINCT ON (
    p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules
  )
    p.*,e.league,e.kickoff,e.home_score,e.away_score,e.status
  FROM sports.predictions p
  JOIN sports.events e USING(event_id)
  WHERE p.as_of < e.kickoff
  ORDER BY
    p.event_id,p.model_id,p.market,p.selection,p.line,p.period,p.settlement_rules,
    p.as_of DESC,p.prediction_id DESC
),
threeway_model AS (
  SELECT
    event_id,model_id,league,market,line,period,settlement_rules,
    MIN(as_of) AS first_as_of,
    MAX(as_of) AS model_as_of,
    MAX(probability) FILTER (WHERE selection='HOME') AS home_p,
    MAX(probability) FILTER (WHERE selection='DRAW') AS draw_p,
    MAX(probability) FILTER (WHERE selection='AWAY') AS away_p,
    SUM(probability) FILTER (WHERE selection IN ('HOME','DRAW','AWAY')) AS probability_sum,
    MAX(home_score) AS home_score,
    MAX(away_score) AS away_score,
    MAX(status) AS status
  FROM latest
  WHERE market='moneyline'
    AND period='REGULATION'
    AND settlement_rules='REGULATION'
    AND selection IN ('HOME','DRAW','AWAY')
  GROUP BY event_id,model_id,league,market,line,period,settlement_rules
  HAVING COUNT(*) FILTER (WHERE selection IN ('HOME','DRAW','AWAY')) = 3
     AND MAX(as_of)-MIN(as_of) <= INTERVAL '5 minutes'
     AND SUM(probability) FILTER (WHERE selection IN ('HOME','DRAW','AWAY'))
         BETWEEN 0.98 AND 1.02
),
threeway_scored AS (
  SELECT
    m.league,m.model_id,m.event_id,m.market,m.period,
    q.source_reference,'3WAY'::text AS market_structure,
    -LN(
      CASE
        WHEN m.home_score > m.away_score THEN m.home_p
        WHEN m.home_score = m.away_score THEN m.draw_p
        ELSE m.away_p
      END
    ) AS model_logloss,
    -LN(
      CASE
        WHEN m.home_score > m.away_score THEN q.home_p
        WHEN m.home_score = m.away_score THEN q.draw_p
        ELSE q.away_p
      END
    ) AS market_logloss
  FROM threeway_model m
  JOIN LATERAL (
    SELECT
      h.bookmaker AS source_reference,
      (1.0/h.odds) / ((1.0/h.odds)+(1.0/d.odds)+(1.0/a.odds)) AS home_p,
      (1.0/d.odds) / ((1.0/h.odds)+(1.0/d.odds)+(1.0/a.odds)) AS draw_p,
      (1.0/a.odds) / ((1.0/h.odds)+(1.0/d.odds)+(1.0/a.odds)) AS away_p
    FROM sports.odds_snapshots h
    JOIN sports.odds_snapshots d
      ON d.event_id=h.event_id AND d.market=h.market
     AND d.line=h.line AND d.period=h.period
     AND d.settlement_rules=h.settlement_rules
     AND d.bookmaker=h.bookmaker AND d.source=h.source
     AND d.observed_at=h.observed_at AND d.selection='DRAW'
    JOIN sports.odds_snapshots a
      ON a.event_id=h.event_id AND a.market=h.market
     AND a.line=h.line AND a.period=h.period
     AND a.settlement_rules=h.settlement_rules
     AND a.bookmaker=h.bookmaker AND a.source=h.source
     AND a.observed_at=h.observed_at AND a.selection='AWAY'
    WHERE h.event_id=m.event_id
      AND h.market=m.market AND h.line=m.line
      AND h.period=m.period AND h.settlement_rules=m.settlement_rules
      AND h.selection='HOME'
      AND NOT h.live AND NOT d.live AND NOT a.live
      AND h.observed_at<=m.model_as_of
      AND h.observed_at>=m.model_as_of-INTERVAL '6 hours'
      AND (h.source_time IS NULL OR h.source_time<=m.model_as_of)
      AND (d.source_time IS NULL OR d.source_time<=m.model_as_of)
      AND (a.source_time IS NULL OR a.source_time<=m.model_as_of)
    ORDER BY CASE WHEN lower(h.bookmaker)='pinnacle' THEN 0
                  WHEN lower(h.bookmaker)='betfair' THEN 1 ELSE 2 END,
             h.observed_at DESC
    LIMIT 1
  ) q ON true
  WHERE m.status='STATUS_FINAL'
    AND m.home_score IS NOT NULL AND m.away_score IS NOT NULL
),
twoway_latest AS (
  SELECT *
  FROM latest
  WHERE market='moneyline'
    AND selection IN ('HOME','AWAY')
    AND period='FULL_GAME'
),
twoway_scored AS (
  SELECT
    p.league,p.model_id,p.event_id,p.market,p.period,
    q.source_reference,'2WAY'::text AS market_structure,
    v.log_loss AS model_logloss,
    -CASE WHEN v.outcome=1 THEN LN(q.reference_probability)
          ELSE LN(1-q.reference_probability) END AS market_logloss
  FROM twoway_latest p
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
      AND o.line=p.line AND NOT o.live AND NOT other.live
      AND o.observed_at<=p.as_of
      AND o.observed_at>=p.as_of-INTERVAL '6 hours'
      AND (o.source_time IS NULL OR o.source_time<=p.as_of)
      AND (other.source_time IS NULL OR other.source_time<=p.as_of)
      AND NOT EXISTS (
        SELECT 1 FROM sports.odds_snapshots x
        WHERE x.event_id=o.event_id AND x.market=o.market
          AND x.line=o.line AND x.period=o.period
          AND x.settlement_rules=o.settlement_rules
          AND x.bookmaker=o.bookmaker AND x.source=o.source
          AND x.observed_at=o.observed_at AND x.selection='DRAW'
      )
    ORDER BY CASE WHEN lower(o.bookmaker)='pinnacle' THEN 0
                  WHEN lower(o.bookmaker)='betfair' THEN 1 ELSE 2 END,
             o.observed_at DESC
    LIMIT 1
  ) q ON true
  WHERE v.outcome IS NOT NULL
),
scored AS (
  SELECT * FROM threeway_scored
  UNION ALL
  SELECT * FROM twoway_scored
)
SELECT
  league,model_id,market,period,source_reference,market_structure,
  COUNT(DISTINCT event_id) AS matches,
  COUNT(*) AS outcomes,
  AVG(model_logloss) AS model_logloss,
  AVG(market_logloss) AS market_logloss,
  AVG(market_logloss)-AVG(model_logloss) AS logloss_gain_vs_market
FROM scored
GROUP BY league,model_id,market,period,source_reference,market_structure;
