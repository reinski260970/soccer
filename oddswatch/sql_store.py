"""SQL persistence for sports predictions, PLAY signals and evaluation.

SPORTS_DATABASE_URL:
  sqlite:///data/sports.db                 (default, local/dev)
  postgresql+psycopg://user:pass@host/db   (production)

Mongo football/tennis sources remain untouched. This store mirrors model output and
PLAY releases so every published valuebet can be settled and evaluated internally.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, MetaData, String, Table, Text,
    create_engine, select, update,
)

META = MetaData()

games = Table(
    "games", META,
    Column("id", Integer, primary_key=True),
    Column("event_id", String(96), unique=True, nullable=False),
    Column("sport", String(32), nullable=False),
    Column("league", String(64), nullable=False),
    Column("event", String(255), nullable=False),
    Column("kickoff", DateTime(timezone=True), nullable=False),
    Column("home", String(128)),
    Column("away", String(128)),
    Column("status", String(32), default="scheduled"),
    Column("home_score", Float),
    Column("away_score", Float),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

model_runs = Table(
    "model_runs", META,
    Column("id", Integer, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("sport", String(32), nullable=False),
    Column("league", String(64), nullable=False),
    Column("model", String(96), nullable=False),
    Column("details", Text),
)

predictions = Table(
    "predictions", META,
    Column("id", Integer, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("event_id", String(96), nullable=False, index=True),
    Column("sport", String(32), nullable=False),
    Column("league", String(64), nullable=False),
    Column("market", String(64), nullable=False),
    Column("selection", String(255)),
    Column("p_model", Float, nullable=False),
    Column("p_ref", Float),
    Column("p_final", Float),
    Column("fair_odds", Float, nullable=False),
    Column("estimate", Boolean, nullable=False, default=False),
    Column("model", String(96)),
    Column("inputs", Text),
    Column("outcome", Float),
)

odds = Table(
    "odds", META,
    Column("id", Integer, primary_key=True),
    Column("event_id", String(96), nullable=False, index=True),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("market", String(64), nullable=False),
    Column("selection", String(255)),
    Column("source", String(64), nullable=False),
    Column("odds", Float, nullable=False),
    Column("liquidity", Float),
    Column("ref", String(255)),
    Column("executable", Boolean, nullable=False, default=True),
)

signals = Table(
    "signals", META,
    Column("id", Integer, primary_key=True),
    Column("signal_key", String(64), unique=True, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("event_id", String(96), nullable=False, index=True),
    Column("sport", String(32), nullable=False),
    Column("league", String(64), nullable=False),
    Column("market", String(64), nullable=False),
    Column("selection", String(255), nullable=False),
    Column("status", String(16), nullable=False),  # PLAY / WATCH / INFO
    Column("reason", Text),
)

plays = Table(
    "plays", META,
    Column("id", Integer, primary_key=True),
    Column("play_key", String(64), unique=True, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("event_id", String(96), nullable=False, index=True),
    Column("event", String(255), nullable=False),
    Column("kickoff", DateTime(timezone=True), nullable=False),
    Column("sport", String(32), nullable=False),
    Column("league", String(64), nullable=False),
    Column("market", String(64), nullable=False),
    Column("selection", String(255), nullable=False),
    Column("source", String(64), nullable=False),
    Column("odds", Float, nullable=False),
    Column("fair_odds", Float, nullable=False),
    Column("min_odds", Float),
    Column("p_model", Float),
    Column("p_ref", Float),
    Column("p_final", Float),
    Column("edge", Float),
    Column("ev", Float),
    Column("stake_eh", Float, nullable=False),
    Column("estimate", Boolean, nullable=False, default=False),
    Column("reason", Text),
    Column("ref", String(255)),
    Column("result", String(16), nullable=False, default="pending"),
    Column("closing_fair_odds", Float),
    Column("clv", Float),
    Column("pnl_eh", Float),
    Column("settled_at", DateTime(timezone=True)),
)


def database_url() -> str:
    url = os.getenv("SPORTS_DATABASE_URL", "").strip()
    if url:
        return url
    Path("data").mkdir(exist_ok=True)
    return "sqlite:///data/sports.db"


def engine():
    return create_engine(database_url(), future=True, pool_pre_ping=True)


def init_db() -> None:
    META.create_all(engine())


def _dt(value) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _key(*parts: object) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _upsert(conn, table: Table, key_col: str, key_value: str, values: dict) -> None:
    row = conn.execute(select(table.c.id).where(getattr(table.c, key_col) == key_value)).first()
    if row:
        conn.execute(update(table).where(table.c.id == row.id).values(**values))
    else:
        conn.execute(table.insert().values(**{key_col: key_value, **values}))


def sync_scan(fixtures, picks) -> int:
    """Persist every prediction/offer and mirror every published PLAY.

    WATCH/INFO may be added to signals by callers later, but only picks passed here
    become PLAY rows. This keeps performance accounting clean.
    """
    init_db()
    now = datetime.now(timezone.utc)
    fx_by_event = {f.game.title: f for f in fixtures}
    nplays = 0
    with engine().begin() as conn:
        for fx in fixtures:
            g = fx.game
            _upsert(conn, games, "event_id", str(g.id), {
                "sport": fx.sport, "league": fx.league, "event": g.title,
                "kickoff": _dt(g.kickoff), "home": g.home.name, "away": g.away.name,
                "status": "final" if g.final else "scheduled",
                "home_score": g.home_score, "away_score": g.away_score,
                "updated_at": now,
            })
            conn.execute(model_runs.insert().values(
                created_at=now, sport=fx.sport, league=fx.league,
                model=fx.model or fx.sport, details=fx.detail,
            ))
            for side, p in fx.probs.items():
                pr = fx.ref_probs.get(side)
                # p_final is written as model p here; the caller's decision blend is
                # retained on PLAY rows, where it matters for value accounting.
                conn.execute(predictions.insert().values(
                    created_at=now, event_id=str(g.id), sport=fx.sport, league=fx.league,
                    market=side, selection=side, p_model=float(p), p_ref=pr,
                    p_final=float(p), fair_odds=1.0 / float(p), estimate=bool(fx.estimate),
                    model=fx.model or fx.sport, inputs=fx.detail,
                ))
            for side, offers in fx.offers.items():
                for o in offers:
                    conn.execute(odds.insert().values(
                        event_id=str(g.id), observed_at=_dt(o.observed_at), market=side,
                        selection=o.selection, source=o.source, odds=float(o.odds),
                        liquidity=o.liquidity, ref=o.ref, executable=True,
                    ))

        for p in picks:
            fx = fx_by_event.get(p.event)
            event_id = str(fx.game.id) if fx else (p.ref or _key(p.event, p.kickoff))
            sport = fx.sport if fx else _sport_for_league(p.league)
            pk = _key(event_id, p.market, p.selection, p.source, round(float(p.odds), 4))
            common = {
                "created_at": _dt(p.observed_at), "event_id": event_id,
                "sport": sport, "league": p.league, "market": p.market,
                "selection": p.selection,
            }
            _upsert(conn, signals, "signal_key", pk, {
                **common, "status": "PLAY", "reason": p.reason,
            })
            _upsert(conn, plays, "play_key", pk, {
                **common, "event": p.event, "kickoff": _dt(p.kickoff),
                "source": p.source, "odds": float(p.odds),
                "fair_odds": float(p.fair_odds), "min_odds": float(p.min_odds),
                "p_model": float(p.p_model), "p_ref": p.p_ref, "p_final": p.p_final,
                "edge": float(p.edge), "ev": float(p.ev), "stake_eh": float(p.stake_eh),
                "estimate": bool(p.estimate), "reason": p.reason, "ref": p.ref,
                "result": "pending",
            })
            nplays += 1
    return nplays


def mirror_journal_plays(rows: list[dict]) -> int:
    """Mirror existing PLAY rows from valuebets.csv, useful for migrations."""
    init_db()
    n = 0
    with engine().begin() as conn:
        for r in rows:
            if (r.get("result") or "").lower() == "withdrawn":
                continue
            event_id = r.get("event_id") or r.get("ref") or _key(r.get("event"), r.get("kickoff"))
            pk = _key(event_id, r.get("market"), r.get("selection"), r.get("source"), r.get("odds"))
            _upsert(conn, plays, "play_key", pk, {
                "created_at": _dt(r.get("created_at")), "event_id": str(event_id),
                "event": r.get("event", ""), "kickoff": _dt(r.get("kickoff")),
                "sport": _sport_for_league(r.get("league", "")), "league": r.get("league", ""),
                "market": r.get("market", ""), "selection": r.get("selection", ""),
                "source": r.get("source", ""), "odds": float(r.get("odds") or 0),
                "fair_odds": float(r.get("fair_odds") or 0),
                "min_odds": float(r.get("min_odds") or 0) or None,
                "p_model": _float(r.get("p_model")), "p_ref": _float(r.get("p_ref")),
                "p_final": _float(r.get("p_final")), "edge": _float(r.get("edge")),
                "ev": _float(r.get("ev")), "stake_eh": float(r.get("stake_eh") or 0),
                "estimate": str(r.get("estimate", "")).lower() in ("1", "true", "yes"),
                "reason": r.get("reason", ""), "ref": r.get("ref", ""),
                "result": r.get("result") or "pending",
                "closing_fair_odds": _float(r.get("closing_fair_odds")),
                "clv": _float(r.get("clv")), "pnl_eh": _float(r.get("pnl_eh")),
            })
            n += 1
    return n


def _float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sport_for_league(league: str) -> str:
    if league == "nba":
        return "nba"
    if league == "nfl":
        return "nfl"
    if league == "nhl":
        return "nhl"
    if league in {"del", "icehl", "shl", "liiga", "nl", "khl"}:
        return "hockey"
    if league.startswith("tennis") or league in {"atp", "wta"}:
        return "tennis"
    return "soccer"


_TOTAL_RE = re.compile(r"^([OU])(?:NDER|VER)?\s*([0-9]+(?:\.[0-9]+)?)$", re.I)


def grade_market(market: str, home_score: float, away_score: float) -> bool | None:
    """Return True/False, or None for push/unsupported/void."""
    m = (market or "").strip().replace("_", "").replace(" ", "")
    ml = m.lower()
    if ml in {"home", "1"}:
        return home_score > away_score
    if ml in {"away", "2"}:
        return away_score > home_score
    if ml in {"draw", "x"}:
        return home_score == away_score
    if ml in {"bttsyes", "bttsja"}:
        return home_score > 0 and away_score > 0
    if ml in {"bttsno", "bttsnein"}:
        return not (home_score > 0 and away_score > 0)
    mt = _TOTAL_RE.match(m)
    if mt:
        side, line = mt.group(1).upper(), float(mt.group(2))
        total = home_score + away_score
        if total == line:
            return None
        return total > line if side == "O" else total < line
    return None


def _closing_fair(g, market: str) -> float | None:
    """Closing no-vig decimal odds from ESPN when the final scoreboard exposes them."""
    from . import pricing
    r = g.ref_line or {}
    m = (market or "").strip().replace("_", "").replace(" ", "").lower()
    if m in {"home", "away", "draw", "1", "2", "x"}:
        if r.get("ml_draw") and all((r.get(k) or 0) > 1 for k in ("ml_home", "ml_draw", "ml_away")):
            ps = pricing.devig([r["ml_home"], r["ml_draw"], r["ml_away"]])
            p = {"home": ps[0], "1": ps[0], "draw": ps[1], "x": ps[1],
                 "away": ps[2], "2": ps[2]}[m]
            return 1.0 / p
        if all((r.get(k) or 0) > 1 for k in ("ml_home", "ml_away")):
            ps = pricing.devig([r["ml_home"], r["ml_away"]])
            p = {"home": ps[0], "1": ps[0], "away": ps[1], "2": ps[1]}.get(m)
            return 1.0 / p if p else None
    mt = _TOTAL_RE.match((market or "").replace(" ", ""))
    if mt and r.get("total_line") is not None:
        line = float(mt.group(2))
        if abs(float(r["total_line"]) - line) < 1e-9 and all(
            (r.get(k) or 0) > 1 for k in ("ml_over", "ml_under")
        ):
            ps = pricing.devig([r["ml_over"], r["ml_under"]])
            return 1.0 / (ps[0] if mt.group(1).upper() == "O" else ps[1])
    return None


def settle_pending() -> dict:
    """Settle pending SQL PLAY rows from ESPN final scoreboards.

    Supports ML/1X2, O/U and BTTS. AH/spreads remain pending until a line-aware
    grader is added. CLV is recorded when ESPN exposes a usable closing reference.
    """
    from .sources import espn
    init_db()
    done = skipped = errors = 0
    now = datetime.now(timezone.utc)
    with engine().begin() as conn:
        pending = list(conn.execute(select(plays).where(plays.c.result == "pending")).mappings())
        for p in pending:
            league = p["league"]
            if league not in espn.PATHS:
                skipped += 1
                continue
            try:
                gs, err = espn.scoreboard_day(league, p["kickoff"].date())
            except Exception:
                errors += 1
                continue
            if err:
                errors += 1
                continue
            g = next((x for x in gs if str(x.id) == str(p["event_id"])), None)
            if g is None:
                g = next((x for x in gs if x.title == p["event"]), None)
            if g is None or not g.final or g.home_score is None or g.away_score is None:
                skipped += 1
                continue
            won = grade_market(p["market"], g.home_score, g.away_score)
            # Unsupported markets stay pending; exact-line total push grades void.
            supported = (
                p["market"].lower() in {"home", "away", "draw", "1", "2", "x",
                                        "btts_yes", "btts_no", "bttsja", "bttsnein"}
                or bool(_TOTAL_RE.match((p["market"] or "").replace(" ", "")))
            )
            if not supported:
                skipped += 1
                continue
            result = "void" if won is None else ("win" if won else "loss")
            stake = float(p["stake_eh"])
            pnl = 0.0 if won is None else (stake * (float(p["odds"]) - 1.0) if won else -stake)
            closing_fair = _closing_fair(g, p["market"])
            clv = (float(p["odds"]) / closing_fair - 1.0) if closing_fair else None
            conn.execute(update(plays).where(plays.c.id == p["id"]).values(
                result=result, pnl_eh=pnl, settled_at=now,
                closing_fair_odds=closing_fair, clv=clv,
            ))
            conn.execute(update(games).where(games.c.event_id == str(g.id)).values(
                status="final", home_score=g.home_score, away_score=g.away_score, updated_at=now,
            ))
            # Prediction outcome for the three canonical sides.
            outcomes = {
                "home": 1.0 if g.home_score > g.away_score else 0.0,
                "away": 1.0 if g.away_score > g.home_score else 0.0,
                "draw": 1.0 if g.home_score == g.away_score else 0.0,
            }
            for market, outcome in outcomes.items():
                conn.execute(update(predictions).where(
                    (predictions.c.event_id == str(g.id)) & (predictions.c.market == market)
                ).values(outcome=outcome))
            done += 1
    return {"settled": done, "pending_or_unsupported": skipped, "errors": errors}


def sync_settled_to_journal(j) -> int:
    """Push SQL settlements back into the legacy CSV journal used by Telegram/Sharpery."""
    init_db()
    with engine().connect() as conn:
        rows = list(conn.execute(
            select(plays).where(plays.c.result.in_(("win", "loss", "void")))
        ).mappings())
    n = 0
    for p in rows:
        won = None if p["result"] == "void" else p["result"] == "win"
        n += j.settle(
            "valuebets", p["event"], p["market"], won,
            closing_fair_odds=p["closing_fair_odds"], ref=p["ref"] or None,
        )
        n += j.settle(
            "placed", p["event"], p["market"], won,
            closing_fair_odds=p["closing_fair_odds"], ref=p["ref"] or None,
        )
    return n


def summary() -> dict:
    init_db()
    with engine().connect() as conn:
        rows = list(conn.execute(select(plays)).mappings())
    settled = [r for r in rows if r["result"] in ("win", "loss", "void")]
    stake = sum(float(r["stake_eh"]) for r in settled if r["result"] != "void")
    pnl = sum(float(r["pnl_eh"] or 0) for r in settled)
    clv = [float(r["clv"]) for r in settled if r["clv"] is not None]
    return {
        "plays": len(rows), "settled": len(settled), "stake_eh": stake, "pnl_eh": pnl,
        "roi": (pnl / stake if stake else None),
        "avg_clv": (sum(clv) / len(clv) if clv else None), "clv_n": len(clv),
    }
