"""European basketball normalized persistence for Neon/Postgres.

Storage only. No PLAY approval is implied. The purpose is to collect fixtures,
advanced/team stats, market snapshots and model outputs for forward validation.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

from .store import ingest


EU_BASKETBALL_LEAGUES = {
    "euroleague", "eurocup", "bbl", "acb", "lnb", "lba", "bsl", "aba",
}


def _key(*parts: object) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _team_id(league: str, name: str) -> str:
    return f"{league}:team:{_key(league, name)[:24]}"


def _season_start(kickoff: datetime) -> int:
    return kickoff.year if kickoff.month >= 7 else kickoff.year - 1


def build_bundle(fixtures, observed_at: datetime | None = None) -> dict:
    now = observed_at or datetime.now(timezone.utc)
    events, stats, odds, predictions = [], [], [], []
    models = {}

    for fx in fixtures:
        if fx.league not in EU_BASKETBALL_LEAGUES:
            continue
        g = fx.game
        kickoff = g.kickoff if g.kickoff.tzinfo else g.kickoff.replace(tzinfo=timezone.utc)
        event_id = f"{fx.league}:oddswatch:{g.id}"
        model_name = fx.model or "euro-basketball-shadow"
        model_id = f"{model_name}:{fx.league}:{now:%Y%m%d}"
        models[model_id] = {
            "model_id": model_id,
            "league": fx.league,
            "trained_through": now,
            "created_at": now,
            "method": model_name,
            "parameters": {
                "storage_version": 1,
                "competition_adjusted": True,
                "approved_for_play": False,
            },
            "validation": {
                "status": "SHADOW",
                "reason": "European basketball requires forward Logloss and CLV validation before PLAY approval",
            },
            "approved": False,
        }
        events.append({
            "event_id": event_id,
            "league": fx.league,
            "source": "oddswatch",
            "source_event_id": str(g.id),
            "home_team_id": _team_id(fx.league, g.home.name),
            "away_team_id": _team_id(fx.league, g.away.name),
            "home_name": g.home.name,
            "away_name": g.away.name,
            "kickoff": kickoff,
            "season": _season_start(kickoff),
            "season_type": "regular",
            "status": "STATUS_FINAL" if getattr(g, "final", False) else getattr(g, "status", "STATUS_SCHEDULED"),
            "home_score": getattr(g, "home_score", None) if getattr(g, "final", False) else None,
            "away_score": getattr(g, "away_score", None) if getattr(g, "final", False) else None,
            "observed_at": now,
        })

        for side, team in (("home", g.home), ("away", g.away)):
            stats.append({
                "event_id": event_id,
                "league": fx.league,
                "entity_type": "team",
                "entity_id": _team_id(fx.league, team.name),
                "source": "oddswatch-model-input",
                "observed_at": now,
                "data_through": now,
                "metrics": {
                    "side": side,
                    "detail": fx.detail,
                    "context": list(getattr(fx, "context", []) or []),
                    "estimate": bool(getattr(fx, "estimate", False)),
                    "model": model_name,
                },
            })

        for side, probability in (fx.probs or {}).items():
            if side not in {"home", "away"}:
                continue
            predictions.append({
                "prediction_id": _key(event_id, model_id, now.isoformat(), "moneyline", side),
                "event_id": event_id,
                "model_id": model_id,
                "as_of": now,
                "market": "moneyline",
                "selection": side.upper(),
                "line": 0,
                "period": "FULL_GAME",
                "settlement_rules": "INCLUDING_OT",
                "probability": float(probability),
                "quality": "LOW" if getattr(fx, "estimate", False) else "MEDIUM",
                "features": {
                    "detail": fx.detail,
                    "context": list(getattr(fx, "context", []) or []),
                    "p_ref": (fx.ref_probs or {}).get(side),
                    "estimate": bool(getattr(fx, "estimate", False)),
                },
            })

        quote_map = getattr(fx, "market_quotes", None) or getattr(fx, "offers", {})
        for side, rows in (quote_map or {}).items():
            if side not in {"home", "away"}:
                continue
            for q in rows:
                observed = getattr(q, "observed_at", None) or now
                odds.append({
                    "quote_id": _key(event_id, side, getattr(q, "source", ""), observed,
                                     getattr(q, "ref", ""), getattr(q, "odds", "")),
                    "event_id": event_id,
                    "market": "moneyline",
                    "selection": side.upper(),
                    "line": 0,
                    "period": "FULL_GAME",
                    "settlement_rules": "INCLUDING_OT",
                    "bookmaker": str(getattr(q, "source", "") or "unknown"),
                    "source": str(getattr(q, "source", "") or "unknown"),
                    "source_url": None,
                    "observed_at": observed,
                    "source_time": None,
                    "odds": float(q.odds),
                    "commission": 0,
                    "executable": bool(getattr(q, "executable", False)),
                    "live": False,
                    "liquidity": getattr(q, "liquidity", None),
                })

    return {
        "events": events,
        "model_versions": list(models.values()),
        "stats_snapshots": stats,
        "odds_snapshots": odds,
        "predictions": predictions,
    }


def persist_if_configured(fixtures) -> dict:
    if not os.getenv("SPORTS_DATABASE_URL", "").strip():
        return {"configured": False}
    from .store import connect, migrate
    with connect() as conn:
        migrate(conn)
        result = ingest(conn, build_bundle(fixtures))
    return {"configured": True, **result}
