# NBA/NFL PostgreSQL and internal evaluation

Optional isolated `sports` schema, PostgreSQL 15+. Football and tennis Mongo integrations are unchanged. No Telegram, Sharpery, Polymarket or Kalshi calls.

## Enable

1. Provision PostgreSQL and a database user that owns the `sports` schema. Keep the connection URL in GitHub secret `SPORTS_DATABASE_URL` (use TLS for a remote server).
2. Install `pip install -r requirements-sql.txt`.
3. Run `python -m oddswatch.sql migrate`, then `python -m oddswatch.sql sync` and `python -m oddswatch.sql report`.
4. After merging, the main-branch push starts the initial sync using the existing `SPORTS_DATABASE_URL` secret. The workflow syncs every two hours; manual dispatch is also supported. CI first tests against an isolated PostgreSQL 16 service. Scheduled and manual sync run only on main. A missing database secret fails explicitly.

## Data and evaluation

`sync` fetches ESPN NBA/NFL fixtures/results and retains raw responses, timestamps and score observations. It rechecks ALL overdue unevaluated predictions, regardless of age, also by event ID for rescheduling. Every successful run evaluates all supported finished predictions, including LOW quality and unpublished predictions, without requiring a signal or bet. Final-score corrections update evaluation records. Unsupported rules, missing scores and unfinished games remain pending and appear in the report.

Supported internal settlement: `period=FULL_GAME`, `settlement_rules=INCLUDING_OT_PUSH_ON_TIE`, moneyline HOME/AWAY, spread HOME/AWAY (selection's signed handicap), total OVER/UNDER. Integer/half-point lines only. NFL ties and exact spread/total lines are PUSH, excluded from binary metrics. Regulation-only, quarter, player props and quarter-point splits need a separate evaluator. Preseason predictions are excluded.

`model_metrics` reports sample counts, selection win rate, classification accuracy, Brier score and log loss by league/model/market/rules. `calibration` contains probability bins with sample counts. These are descriptive metrics, not automatic OOS approval; correlated snapshots are not independent samples. `performance` contains actual recorded bets only, never simulated prediction stakes.

## Model and price producers

`python -m oddswatch.sql ingest bundle.json` accepts arrays keyed by the allowlisted tables in `store.FIELDS`. Tables are imported transactionally in dependency order; IDs must be stable and unique. Existing immutable IDs are retained, so changed predictions/models require new IDs. Required columns/defaults are documented by the SQL migrations. Use timezone-aware ISO timestamps, source IDs and independently generated pre-match probabilities; no model or historical data is invented by this module.

No executable odds feed or NBA/NFL model is supplied by this change. Existing producers must emit bundles or call `ingest`. Stats/news snapshots can be imported; they are not automatically collected. ESPN is used for results, not bookmaker odds. Prices must come from user-accessible venues. Actual bet records require a separate explicit execution/settlement integration; this module does not place bets or pretend predictions were staked.

WATCH/PLAY signals always carry 0 EH. PLAY requires a matching pre-match market, approved model, MEDIUM/HIGH quality, executable price and positive commission-adjusted EV. Model approval must represent external validation; this storage layer does not provide it. Producers must enforce feature availability as of prediction time; timestamps alone cannot validate JSON feature contents.

CLV uses the same source/bookmaker/selection/line/period/rules and the latest observed pregame quote within 15 minutes of kickoff. Missing quotes leave signals open. This is sampled raw CLV, not exact closing no-vig. Two-hour sync cannot collect close-to-kickoff odds: a separate odds producer with sufficiently frequent snapshots is required. Postponed/unknown-status events do not close automatically.

Commands: `migrate`, `sync --start YYYY-MM-DD --days 3`, `ingest FILE`, `evaluate`, `clv`, `report`. Network/DB failures produce nonzero exit status; errors redact credentials. Migration checksums prevent silently rewriting applied migrations. Back up the database and use append-only versioned migrations.

## Existing Neon scanner integration

The same Neon database already contains `public.games` and `public.predictions`. The NBA/NFL runner also recovers these games and writes separate internal evaluations to `sports.scanner_evaluations`, without modifying source predictions or inventing training metadata. `scanner_metrics` uses the latest pre-kickoff prediction per event/model/side to avoid counting repeated scans as independent games. Legacy bridge supports full-game HOME/AWAY NBA/NFL predictions; ties are unscored pushes. NBA preseason is excluded. Other sports continue through their existing runner. Both plain PostgreSQL and SQLAlchemy psycopg URLs are accepted.
