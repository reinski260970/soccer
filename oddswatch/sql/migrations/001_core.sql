CREATE SCHEMA IF NOT EXISTS sports;
CREATE TABLE sports.events (
 event_id text PRIMARY KEY, league text NOT NULL CHECK (league IN ('nba','nfl')),
 source text NOT NULL, source_event_id text NOT NULL,
 home_team_id text NOT NULL, away_team_id text NOT NULL,
 home_name text NOT NULL, away_name text NOT NULL,
 kickoff timestamptz NOT NULL, season integer NOT NULL,
 season_type text NOT NULL CHECK (season_type IN ('preseason','regular','postseason')),
 status text NOT NULL, home_score numeric CHECK (home_score >= 0),
 away_score numeric CHECK (away_score >= 0), observed_at timestamptz NOT NULL,
 UNIQUE (source,league,source_event_id), CHECK(home_team_id <> away_team_id)
);
CREATE INDEX events_kickoff ON sports.events(league,kickoff);
CREATE TABLE sports.raw_payloads (
 source text NOT NULL, resource text NOT NULL, observed_at timestamptz NOT NULL,
 payload jsonb NOT NULL, PRIMARY KEY(source,resource,observed_at)
);
CREATE TABLE sports.event_observations (
 event_id text NOT NULL REFERENCES sports.events, observed_at timestamptz NOT NULL,
 kickoff timestamptz NOT NULL, status text NOT NULL, home_score numeric, away_score numeric,
 PRIMARY KEY(event_id,observed_at)
);
CREATE TABLE sports.stats_snapshots (
 event_id text REFERENCES sports.events, league text NOT NULL CHECK (league IN ('nba','nfl')),
 entity_type text NOT NULL CHECK (entity_type IN ('team','player')),
 entity_id text NOT NULL, source text NOT NULL, observed_at timestamptz NOT NULL,
 data_through timestamptz NOT NULL, metrics jsonb NOT NULL,
 CHECK(data_through <= observed_at),
 UNIQUE NULLS NOT DISTINCT(event_id,league,entity_type,entity_id,source,observed_at)
);
CREATE TABLE sports.news_snapshots (
 news_id text PRIMARY KEY, event_id text REFERENCES sports.events,
 league text NOT NULL CHECK (league IN ('nba','nfl')), entity_id text,
 published_at timestamptz NOT NULL, observed_at timestamptz NOT NULL,
 source text NOT NULL, verified boolean NOT NULL DEFAULT false,
 category text NOT NULL, payload jsonb NOT NULL, CHECK(published_at <= observed_at)
);
CREATE TABLE sports.model_versions (
 model_id text PRIMARY KEY, league text NOT NULL CHECK (league IN ('nba','nfl')),
 trained_through timestamptz NOT NULL, created_at timestamptz NOT NULL,
 method text NOT NULL, parameters jsonb NOT NULL, validation jsonb NOT NULL,
 approved boolean NOT NULL DEFAULT false, CHECK(trained_through <= created_at)
);
-- Line is always the selection's line; moneyline uses line=0. Scope identifies
-- regulation vs OT, and settlement_rules identifies pushes/ties/void treatment.
CREATE TABLE sports.odds_snapshots (
 quote_id text PRIMARY KEY, event_id text NOT NULL REFERENCES sports.events,
 market text NOT NULL CHECK (market IN ('moneyline','spread','total')),
 selection text NOT NULL, line numeric NOT NULL DEFAULT 0,
 period text NOT NULL, settlement_rules text NOT NULL,
 bookmaker text NOT NULL, source text NOT NULL, source_url text,
 observed_at timestamptz NOT NULL, source_time timestamptz,
 odds numeric NOT NULL CHECK (odds > 1 AND odds < 1000000),
 commission numeric NOT NULL DEFAULT 0 CHECK (commission >= 0 AND commission < 1),
 executable boolean NOT NULL DEFAULT false, live boolean NOT NULL DEFAULT false,
 liquidity numeric CHECK (liquidity >= 0), CHECK(source_time IS NULL OR source_time <= observed_at),
 CHECK(market <> 'moneyline' OR line=0),
 UNIQUE(event_id,market,selection,line,period,settlement_rules,bookmaker,source,observed_at)
);
CREATE INDEX odds_closing ON sports.odds_snapshots(event_id,market,selection,line,period,bookmaker,observed_at DESC);
CREATE TABLE sports.predictions (
 prediction_id text PRIMARY KEY, event_id text NOT NULL REFERENCES sports.events,
 model_id text NOT NULL REFERENCES sports.model_versions,
 as_of timestamptz NOT NULL, market text NOT NULL, selection text NOT NULL,
 line numeric NOT NULL DEFAULT 0, period text NOT NULL, settlement_rules text NOT NULL,
 probability numeric NOT NULL CHECK (probability > 0 AND probability < 1),
 quality text NOT NULL CHECK (quality IN ('LOW','MEDIUM','HIGH')),
 features jsonb NOT NULL, UNIQUE(event_id,model_id,as_of,market,selection,line,period,settlement_rules)
);
CREATE TABLE sports.signals (
 signal_id text PRIMARY KEY, prediction_id text NOT NULL REFERENCES sports.predictions,
 entry_quote_id text NOT NULL REFERENCES sports.odds_snapshots,
 signal_type text NOT NULL CHECK (signal_type IN ('WATCH','PLAY')),
 created_at timestamptz NOT NULL, stake_eh numeric NOT NULL DEFAULT 0 CHECK(stake_eh=0),
 clv_status text NOT NULL DEFAULT 'OPEN' CHECK(clv_status IN ('OPEN','CLOSED')),
 UNIQUE(prediction_id,entry_quote_id)
);
CREATE TABLE sports.clv_log (
 signal_id text PRIMARY KEY REFERENCES sports.signals,
 closing_quote_id text NOT NULL REFERENCES sports.odds_snapshots,
 captured_at timestamptz NOT NULL, raw_clv_percent numeric NOT NULL,
 clv_pp numeric NOT NULL, note text NOT NULL
);
CREATE TABLE sports.bets (
 bet_id text PRIMARY KEY, signal_id text NOT NULL REFERENCES sports.signals,
 placed_at timestamptz NOT NULL, odds numeric NOT NULL CHECK(odds>1),
 stake_eh numeric NOT NULL CHECK(stake_eh>0),
 result text NOT NULL DEFAULT 'OPEN' CHECK(result IN ('OPEN','WIN','LOSE','VOID','PUSH','HALFW','HALFL')),
 profit_eh numeric, settled_at timestamptz, settlement_source text,
 CHECK((result='OPEN' AND profit_eh IS NULL AND settled_at IS NULL)
 OR (result<>'OPEN' AND profit_eh IS NOT NULL AND settled_at IS NOT NULL AND settlement_source IS NOT NULL))
);
CREATE VIEW sports.performance AS
 SELECT e.league,p.model_id,count(*) FILTER(WHERE b.result<>'OPEN') AS settled,
 sum(b.stake_eh) FILTER(WHERE b.result<>'OPEN') AS stake_eh,
 sum(b.profit_eh) FILTER(WHERE b.result<>'OPEN') AS profit_eh,
 sum(b.profit_eh) FILTER(WHERE b.result<>'OPEN') /
 NULLIF(sum(b.stake_eh) FILTER(WHERE b.result<>'OPEN'),0) AS roi
 FROM sports.bets b JOIN sports.signals s USING(signal_id)
 JOIN sports.predictions p USING(prediction_id) JOIN sports.events e USING(event_id)
 GROUP BY e.league,p.model_id;
