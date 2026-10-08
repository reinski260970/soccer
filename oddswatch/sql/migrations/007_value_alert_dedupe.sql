-- Persistent Telegram dedupe for audited Valuebet alerts.
-- One alert per event/market/line/period/bookmaker key. Runtime audits may
-- repeat, but Telegram must not resend the same actionable market.

CREATE TABLE IF NOT EXISTS sports.value_alerts (
  alert_key text PRIMARY KEY,
  valuebet_id text,
  first_sent_at timestamptz NOT NULL,
  last_sent_at timestamptz NOT NULL,
  bookmaker text NOT NULL,
  odds double precision,
  model_ev double precision,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS value_alerts_last_sent_idx
  ON sports.value_alerts(last_sent_at DESC);
