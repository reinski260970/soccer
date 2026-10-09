"""Internal evaluation of ALL predictions, independent of publication or stakes."""
import math
from datetime import datetime, timezone
from decimal import Decimal


HOCKEY_LEAGUES = {"nhl", "liiga", "icehl", "shl", "del", "khl", "nl"}


def _half_line(line):
    d = Decimal(str(line))
    return d * 2 == (d * 2).to_integral_value()


def outcome(p, home, away, league=None):
    rules = p["settlement_rules"]
    period = p["period"]

    # Hockey final scores include OT/SO. Only full-game 2-way moneyline is
    # safely derivable from them.
    if rules in ("INCLUDING_OT", "INCLUDING_OT_SO"):
        if period != "FULL_GAME" or p["market"] != "moneyline" or p["selection"] not in ("HOME", "AWAY"):
            return None
        if home == away:
            return None
        return "WIN" if (home > away) == (p["selection"] == "HOME") else "LOSE"

    # Legacy US-sports full-game grading.
    if rules == "INCLUDING_OT_PUSH_ON_TIE":
        if period != "FULL_GAME":
            return None
        h, a = Decimal(str(home)), Decimal(str(away))
        line = Decimal(str(p["line"]))
        if p["market"] in ("moneyline", "spread") and p["selection"] in ("HOME", "AWAY"):
            margin = h-a if p["selection"] == "HOME" else a-h
            if p["market"] == "spread":
                if not _half_line(line):
                    return None
                margin += line
        elif p["market"] == "total" and p["selection"] in ("OVER", "UNDER"):
            if not _half_line(line):
                return None
            margin = (h+a-line) * (1 if p["selection"] == "OVER" else -1)
        else:
            return None
        return "WIN" if margin > 0 else "LOSE" if margin < 0 else "PUSH"

    # Soccer REGULATION results are written as verified 90-minute scores by
    # soccer_settlement. Never reinterpret hockey full-game scores as regulation.
    if not str(rules).startswith("REGULATION") or period != "REGULATION":
        return None
    if league in HOCKEY_LEAGUES:
        return None

    h, a = Decimal(str(home)), Decimal(str(away))
    line = Decimal(str(p["line"]))
    market, selection = p["market"], p["selection"]

    if market == "moneyline" and selection in ("HOME", "DRAW", "AWAY"):
        won = ((selection == "HOME" and h > a)
               or (selection == "DRAW" and h == a)
               or (selection == "AWAY" and a > h))
        return "WIN" if won else "LOSE"

    if market == "dnb" and selection in ("HOME", "AWAY"):
        if h == a:
            return "PUSH"
        won = (h > a) if selection == "HOME" else (a > h)
        return "WIN" if won else "LOSE"

    if market == "double_chance":
        won = {
            "HOME_OR_DRAW": h >= a,
            "DRAW_OR_AWAY": a >= h,
            "HOME_OR_AWAY": h != a,
        }.get(selection)
        return None if won is None else ("WIN" if won else "LOSE")

    if market == "btts" and selection in ("YES", "NO"):
        yes = h > 0 and a > 0
        return "WIN" if yes == (selection == "YES") else "LOSE"

    if market == "total" and selection in ("OVER", "UNDER"):
        if not _half_line(line):
            return None
        margin = (h+a-line) * (1 if selection == "OVER" else -1)
        return "WIN" if margin > 0 else "LOSE" if margin < 0 else "PUSH"

    if market == "team_total" and selection in ("OVER", "UNDER"):
        if not _half_line(line):
            return None
        if rules.endswith("TEAM_TOTAL_HOME"):
            goals = h
        elif rules.endswith("TEAM_TOTAL_AWAY"):
            goals = a
        else:
            return None
        margin = (goals-line) * (1 if selection == "OVER" else -1)
        return "WIN" if margin > 0 else "LOSE" if margin < 0 else "PUSH"

    if market == "spread" and selection in ("HOME", "AWAY"):
        if not _half_line(line):
            return None
        margin = (h-a if selection == "HOME" else a-h) + line
        return "WIN" if margin > 0 else "LOSE" if margin < 0 else "PUSH"

    if market == "european_handicap" and selection in ("HOME", "DRAW", "AWAY"):
        # Integer 3-way handicap only.
        if line != line.to_integral_value():
            return None
        adjusted = h + line - a
        won = ((selection == "HOME" and adjusted > 0)
               or (selection == "DRAW" and adjusted == 0)
               or (selection == "AWAY" and adjusted < 0))
        return "WIN" if won else "LOSE"

    return None


def evaluate(conn):
    updated = 0
    with conn.transaction():
        rows = conn.execute(
            "SELECT p.*,e.home_score,e.away_score,e.observed_at,e.source,e.league "
            "FROM sports.predictions p JOIN sports.events e USING(event_id) "
            "WHERE e.status='STATUS_FINAL' AND e.home_score IS NOT NULL "
            "AND e.away_score IS NOT NULL AND e.season_type<>'preseason'"
        ).fetchall()
        for p in rows:
            result = outcome(p, p["home_score"], p["away_score"], league=p["league"])
            if result is None:
                continue
            y = None if result == "PUSH" else int(result == "WIN")
            prob = float(p["probability"])
            brier = None if y is None else (prob-y)**2
            loss = None if y is None else -math.log(prob if y else 1-prob)
            updated += conn.execute(
                "INSERT INTO sports.prediction_evaluations VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT(prediction_id) DO UPDATE SET result=excluded.result,outcome=excluded.outcome,"
                "brier=excluded.brier,log_loss=excluded.log_loss,evaluated_at=excluded.evaluated_at,"
                "result_observed_at=excluded.result_observed_at,home_score=excluded.home_score,"
                "away_score=excluded.away_score,source=excluded.source "
                "WHERE (sports.prediction_evaluations.home_score,sports.prediction_evaluations.away_score) "
                "IS DISTINCT FROM (excluded.home_score,excluded.away_score)",
                (p["prediction_id"], result, y, brier, loss, datetime.now(timezone.utc),
                 p["observed_at"], p["home_score"], p["away_score"], p["source"])
            ).rowcount
    return updated
