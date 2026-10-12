-- Generalize the persistent watchlist so every sport can use the same state machine.
ALTER TABLE sports.watchlist
  RENAME COLUMN xg_gate TO gate_state;
ALTER TABLE sports.watchlist
  RENAME COLUMN xg_direction TO model_direction;

ALTER TABLE sports.watchlist_observations
  RENAME COLUMN xg_gate TO gate_state;
ALTER TABLE sports.watchlist_observations
  RENAME COLUMN xg_direction TO model_direction;

ALTER TABLE sports.watchlist
  ADD COLUMN IF NOT EXISTS sport text NOT NULL DEFAULT 'unknown',
  ADD COLUMN IF NOT EXISTS gate_type text NOT NULL DEFAULT 'MODEL',
  ADD COLUMN IF NOT EXISTS watch_source text NOT NULL DEFAULT 'model';

ALTER TABLE sports.watchlist_observations
  ADD COLUMN IF NOT EXISTS gate_type text NOT NULL DEFAULT 'MODEL',
  ADD COLUMN IF NOT EXISTS watch_source text NOT NULL DEFAULT 'model';

UPDATE sports.watchlist
SET sport='hockey', gate_type='VENUE_XG', watch_source='nhl-v5.1'
WHERE league='nhl' AND sport='unknown';

CREATE INDEX IF NOT EXISTS watchlist_sport_open_idx
  ON sports.watchlist(sport,status,expires_at,last_checked_at);
