CREATE TABLE sports.prediction_evaluations (
 prediction_id text PRIMARY KEY REFERENCES sports.predictions,
 result text NOT NULL CHECK(result IN ('WIN','LOSE','PUSH')),
 outcome integer CHECK(outcome IN (0,1)), brier numeric, log_loss numeric,
 evaluated_at timestamptz NOT NULL, result_observed_at timestamptz NOT NULL,
 home_score numeric NOT NULL, away_score numeric NOT NULL,
 source text NOT NULL,
 CHECK ((result='PUSH' AND outcome IS NULL AND brier IS NULL AND log_loss IS NULL)
 OR (result IN ('WIN','LOSE') AND outcome IS NOT NULL AND brier IS NOT NULL AND log_loss IS NOT NULL))
);
CREATE VIEW sports.model_metrics AS
 SELECT e.league,p.model_id,p.market,p.period,p.settlement_rules,
 count(*) AS evaluated,count(v.outcome) AS scored,
 count(*) FILTER(WHERE v.result='PUSH') AS pushes,
 avg(v.outcome) AS selection_win_rate,
 avg((v.outcome=(p.probability>=0.5)::integer)::integer) AS classification_accuracy,
 avg(v.brier) AS brier_score,avg(v.log_loss) AS log_loss
 FROM sports.predictions p JOIN sports.events e USING(event_id)
 JOIN sports.prediction_evaluations v USING(prediction_id)
 GROUP BY e.league,p.model_id,p.market,p.period,p.settlement_rules;
CREATE VIEW sports.calibration AS
 SELECT e.league,p.model_id,p.market,least(9,floor(p.probability*10)) AS bucket,
 count(*) AS n,avg(p.probability) AS predicted,avg(v.outcome) AS observed
 FROM sports.predictions p JOIN sports.events e USING(event_id)
 JOIN sports.prediction_evaluations v USING(prediction_id) WHERE v.outcome IS NOT NULL
 GROUP BY e.league,p.model_id,p.market,least(9,floor(p.probability*10));
