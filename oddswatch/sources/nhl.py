"""NHL: Ergebnisse (api-web.nhle.com) und Teamstatistik (api.nhle.com/stats).

Ergebnisse je Team über club-schedule-season, dedupliziert per Spiel-ID.
Shootout-Siege zählen im Endstand als +1 Tor; das Modell nutzt den Stand nach
Verlängerung ohne diesen Shootout-Treffer.

Teamstatistik: 5v5-Tore für/gegen (goalsforbystrength / -againstbystrength),
Powerplay-/Penalty-Kill-Quote (summary) und 5v5-Schussanteil (summaryshooting).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .. import fetch
from ..models.poisson import Match

WEB = "https://api-web.nhle.com/v1"
STATS = "https://api.nhle.com/stats/rest/en/team"

TEAMS = ["ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET",
         "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT",
         "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK",
         "WPG", "WSH"]


def season_games(season: str, cache_days: float = 0.0) -> tuple[list[Match], dict[str, str], list[str]]:
    """Reguläre Saisonspiele (gameType 2) mit Endstand.

    Gibt Matches (Teamkürzel), Kürzel->voller Name und Fehler zurück."""
    seen, out, names, errs = set(), [], {}, []
    for t in TEAMS:
        data, err = fetch.get_json(f"{WEB}/club-schedule-season/{t}/{season}", cache_days=cache_days)
        if data is None:
            errs.append(err)
            continue
        for g in data.get("games", []):
            for side in ("homeTeam", "awayTeam"):
                tm = g.get(side, {})
                nm = (tm.get("placeName") or {}).get("default", "")
                cn = (tm.get("commonName") or {}).get("default", "")
                if tm.get("abbrev") and (nm or cn):
                    names[tm["abbrev"]] = f"{nm} {cn}".strip()
            if g.get("gameType") != 2 or g["id"] in seen:
                continue
            h, a = g["homeTeam"], g["awayTeam"]
            if h.get("score") is None or a.get("score") is None:
                continue
            seen.add(g["id"])
            hs, as_ = float(h["score"]), float(a["score"])
            if (g.get("gameOutcome") or {}).get("lastPeriodType") == "SO":
                if hs > as_:
                    hs -= 1
                else:
                    as_ -= 1
            out.append(Match(date.fromisoformat(g["gameDate"]), h["abbrev"], a["abbrev"], hs, as_))
    return out, names, errs


@dataclass
class TeamStats:
    team: str
    gp: float
    gf5v5: float
    ga5v5: float
    pp_pct: float
    pk_pct: float
    shots5v5_share: float | None = None

    @property
    def gf_pct_5v5(self) -> float:
        tot = self.gf5v5 + self.ga5v5
        return self.gf5v5 / tot if tot else 0.5


def team_stats(season: str, cache_days: float = 0.0) -> tuple[dict[str, TeamStats], list[str]]:
    exp = f"cayenneExp=seasonId={season}%20and%20gameTypeId=2"
    errs = []
    summ, e1 = fetch.get_json(f"{STATS}/summary?{exp}", cache_days=cache_days)
    gf, e2 = fetch.get_json(f"{STATS}/goalsforbystrength?{exp}", cache_days=cache_days)
    ga, e3 = fetch.get_json(f"{STATS}/goalsagainstbystrength?{exp}", cache_days=cache_days)
    errs += [e for e in (e1, e2, e3) if e]
    if not summ or not gf:
        return {}, errs
    by_name: dict[str, TeamStats] = {}
    gf_map = {r["teamFullName"]: r for r in gf["data"]}
    ga_map = {r["teamFullName"]: r for r in (ga or {}).get("data", [])}
    for r in summ["data"]:
        n = r["teamFullName"]
        g = gf_map.get(n, {})
        a = ga_map.get(n, {})
        by_name[n] = TeamStats(
            team=n, gp=float(r.get("gamesPlayed") or 0),
            gf5v5=float(g.get("goalsFor5On5") or 0),
            ga5v5=float(a.get("goalsAgainst5On5") or 0),
            pp_pct=float(r.get("powerPlayPct") or 0),
            pk_pct=float(r.get("penaltyKillPct") or 0))
    return by_name, errs
