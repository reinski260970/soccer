-- Persistent model watchlist with append-only observations.
CREATE TABLE IF NOT EXISTS sports.watchlist (
  watch_id text PRIMARY KEY,
  event_id text NOT NULL REFERENCES sports.events(event_id) ON DELETE CASCADE,
  league text NOT NULL,
  market text NOT NULL,
  selection text NOT NULL,
  line numeric NOT NULL DEFAULT 0,
  period text NOT NULL,
  settlement_rules text NOT NULL,
  model_id text,
  fair_probability double precision NOT NULL CHECK (fair_probability > 0 AND fair_probability < 1),
  fair_odds double precision NOT NULL CHECK (fair_odds > 1),
  trigger_odds double precision NOT NULL CHECK (trigger_odds > 1),
  current_odds double precision,
  current_bookmaker text,
  price_type text NOT NULL DEFAULT 'NONE'
    CHECK (price_type IN ('NONE','REFERENCE','EXECUTABLE')),
  xg_gate text NOT NULL,
  xg_direction text NOT NULL,
  status text NOT NULL DEFAULT 'WATCH'
    CHECK (status IN ('WATCH','TRIGGERED','REJECTED','EXPIRED')),
  reason text NOT NULL,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  last_checked_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(event_id,market,selection,line,period,settlement_rules)
);

CREATE INDEX IF NOT EXISTS watchlist_open_idx
  ON sports.watchlist(status,expires_at,last_checked_at);

CREATE TABLE IF NOT EXISTS sports.watchlist_observations (
  watch_id text NOT NULL REFERENCES sports.watchlist(watch_id) ON DELETE CASCADE,
  observed_at timestamptz NOT NULL,
  fair_probability double precision NOT NULL,
  fair_odds double precision NOT NULL,
  trigger_odds double precision NOT NULL,
  current_odds double precision,
  current_bookmaker text,
  price_type text NOT NULL
    CHECK (price_type IN ('NONE','REFERENCE','EXECUTABLE')),
  xg_gate text NOT NULL,
  xg_direction text NOT NULL,
  status text NOT NULL
    CHECK (status IN ('WATCH','TRIGGERED','REJECTED','EXPIRED')),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY(watch_id,observed_at)
);
