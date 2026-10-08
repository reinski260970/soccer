-- Extend normalized sports storage to European basketball competitions.
-- Storage only: no model is approved and no PLAY is created by this migration.

ALTER TABLE sports.events DROP CONSTRAINT events_league_check;
ALTER TABLE sports.events ADD CONSTRAINT events_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba'
  ));

ALTER TABLE sports.stats_snapshots DROP CONSTRAINT stats_snapshots_league_check;
ALTER TABLE sports.stats_snapshots ADD CONSTRAINT stats_snapshots_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba'
  ));

ALTER TABLE sports.news_snapshots DROP CONSTRAINT news_snapshots_league_check;
ALTER TABLE sports.news_snapshots ADD CONSTRAINT news_snapshots_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba'
  ));

ALTER TABLE sports.model_versions DROP CONSTRAINT model_versions_league_check;
ALTER TABLE sports.model_versions ADD CONSTRAINT model_versions_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba'
  ));
