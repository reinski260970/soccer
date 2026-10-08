-- Existing scanner predictions retain their original IDs and provenance.
-- No model version/training cutoff is fabricated during this bridge.
CREATE TABLE sports.scanner_evaluations (
 source_prediction_id bigint PRIMARY KEY,event_id text NOT NULL,league text NOT NULL,
 model text,predicted_at timestamptz NOT NULL,market text NOT NULL,
 probability numeric NOT NULL,outcome integer,brier numeric,log_loss numeric,
 home_score numeric NOT NULL,away_score numeric NOT NULL,evaluated_at timestamptz NOT NULL
);
CREATE VIEW sports.scanner_metrics AS
 WITH latest AS (
 SELECT DISTINCT ON (event_id,league,model,market) * FROM sports.scanner_evaluations
 ORDER BY event_id,league,model,market,predicted_at DESC,source_prediction_id DESC
 )
 SELECT league,model,market,count(*) AS evaluated,count(outcome) AS scored,
 count(*) FILTER(WHERE outcome IS NULL) AS pushes,avg(outcome) AS selection_win_rate,
 avg(brier) AS brier_score,avg(log_loss) AS log_loss
 FROM latest GROUP BY league,model,market;
