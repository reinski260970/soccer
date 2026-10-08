-- Extend normalized sports storage to the soccer leagues used by oddswatch
-- and allow the exact market families audited from the Valuebet feed.

ALTER TABLE sports.events DROP CONSTRAINT events_league_check;
ALTER TABLE sports.events ADD CONSTRAINT events_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba',
    'bundesliga','2bundesliga','epl','championship','laliga','seriea','ligue1',
    'eredivisie','primeira','belgium','turkey','scotland','greece','austria',
    'switzerland','sweden','poland','nations','ucl','uel','uecl'
  ));

ALTER TABLE sports.stats_snapshots DROP CONSTRAINT stats_snapshots_league_check;
ALTER TABLE sports.stats_snapshots ADD CONSTRAINT stats_snapshots_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba',
    'bundesliga','2bundesliga','epl','championship','laliga','seriea','ligue1',
    'eredivisie','primeira','belgium','turkey','scotland','greece','austria',
    'switzerland','sweden','poland','nations','ucl','uel','uecl'
  ));

ALTER TABLE sports.news_snapshots DROP CONSTRAINT news_snapshots_league_check;
ALTER TABLE sports.news_snapshots ADD CONSTRAINT news_snapshots_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba',
    'bundesliga','2bundesliga','epl','championship','laliga','seriea','ligue1',
    'eredivisie','primeira','belgium','turkey','scotland','greece','austria',
    'switzerland','sweden','poland','nations','ucl','uel','uecl'
  ));

ALTER TABLE sports.model_versions DROP CONSTRAINT model_versions_league_check;
ALTER TABLE sports.model_versions ADD CONSTRAINT model_versions_league_check
  CHECK (league IN (
    'nba','nfl','nhl','del','icehl','liiga','shl','nl','khl',
    'extraliga','slovakia','norway','denmark','chl',
    'euroleague','eurocup','bbl','acb','lnb','lba','bsl','aba',
    'bundesliga','2bundesliga','epl','championship','laliga','seriea','ligue1',
    'eredivisie','primeira','belgium','turkey','scotland','greece','austria',
    'switzerland','sweden','poland','nations','ucl','uel','uecl'
  ));

ALTER TABLE sports.odds_snapshots DROP CONSTRAINT odds_snapshots_market_check;
ALTER TABLE sports.odds_snapshots ADD CONSTRAINT odds_snapshots_market_check
  CHECK (market IN (
    'moneyline','spread','total','team_total','double_chance',
    'dnb','european_handicap','btts'
  ));
