"""Price-only watcher for already-created M17.19 forward predictions.

No model inference happens here. The job only refreshes 1X2 market snapshots for
scheduled M17.19 EPL/Primeira events, so closing prices and steam can be measured
without contaminating the fair model.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from . import sql_store
from .sources import apifootball

MODEL = "m17.19-forward-shadow"
SIDES = ("home","draw","away")

def run(hours_ahead: int = 192) -> list[str]:
    now = datetime.now(timezone.utc)
    end = now.timestamp() + hours_ahead * 3600
    sql_store.init_db()

    with sql_store.engine().connect() as conn:
        rows = list(conn.execute(
            select(sql_store.games).where(
                (sql_store.games.c.status == "scheduled")
                & (sql_store.games.c.kickoff > now)
            )
        ).mappings())
        model_events = {
            str(r["event_id"])
            for r in conn.execute(
                select(sql_store.predictions.c.event_id).where(
                    sql_store.predictions.c.model == MODEL
                )
            ).mappings()
        }
    games = [r for r in rows if str(r["event_id"]) in model_events and r["kickoff"].timestamp() <= end]

    days = {}
    books = {}
    inserted = 0
    issues = []
    with sql_store.engine().begin() as conn:
        for g in games:
            day = g["kickoff"].astimezone(timezone.utc).date().isoformat()
            if day not in days:
                days[day], err = apifootball.fixtures_on(day)
                if err:
                    issues.append(err)
            hit = apifootball.find_fixture(
                days.get(day, []),
                [g["home"]], [g["away"]], g["kickoff"]
            )
            if hit is None:
                # Schedule feeds can disagree by calendar day after late changes.
                # Search only adjacent days and still require one unique team pair.
                around = []
                for delta in (-1, 1):
                    d2 = (g["kickoff"].astimezone(timezone.utc).date() + timedelta(days=delta)).isoformat()
                    if d2 not in days:
                        days[d2], err = apifootball.fixtures_on(d2)
                        if err:
                            issues.append(err)
                    around.extend(days.get(d2, []))
                team_hits = [
                    x for x in around
                    if apifootball._hit(x.home, [g["home"]])
                    and apifootball._hit(x.away, [g["away"]])
                ]
                hit = team_hits[0] if len(team_hits) == 1 else None
            if hit is None:
                issues.append(f"NO_MATCH {g['event']}")
                continue
            if hit.id not in books:
                books[hit.id], err = apifootball.odds(hit.id)
                if err:
                    issues.append(err)
            data = books.get(hit.id, {})
            obs = datetime.now(timezone.utc)
            for source in ("Pinnacle","Bet365","Betfair"):
                mk = data.get(source) or {}
                for side in SIDES:
                    odd = mk.get(side)
                    if odd is None or float(odd) <= 1:
                        continue
                    conn.execute(sql_store.odds.insert().values(
                        event_id=str(g["event_id"]),
                        observed_at=obs,
                        market=side,
                        selection=side,
                        source=source.lower(),
                        odds=float(odd),
                        liquidity=None,
                        ref=f"apifootball:{hit.id}:{side}:{source.lower()}",
                        executable=(source != "Pinnacle"),
                    ))
                    inserted += 1
    return [
        f"M17.19 market watch: events={len(games)} odds_rows={inserted}",
        *[f"WARN {x}" for x in issues[:20]],
    ]

if __name__ == "__main__":
    for line in run():
        print(line)
