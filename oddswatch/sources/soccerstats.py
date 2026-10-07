"""SoccerSTATS public league context.

This source is used as a supplemental football context/cross-check source.
It is NOT labelled as xG.

Historical safety:
- historical completed-season pages may be used as PREVIOUS-season priors;
- never inject a completed season's final aggregates into earlier matches of
  that same season, because that would leak future information.

No API key required.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re

from .. import fetch

BASE = "https://www.soccerstats.com/latest.asp?league="

LEAGUES = {
    "D1": "germany",
    "D2": "germany2",
    "D3": "germany3",
    "E0": "england",
    "E1": "england2",
    "SP1": "spain",
    "I1": "italy",
    "F1": "france",
    "N1": "netherlands",
    "P1": "portugal",
    "B1": "belgium",
    "T1": "turkey",
    "SC0": "scotland",
    "G1": "greece",
    "AUT": "austria",
    "SUI": "switzerland",
    "SWE": "sweden",
    "NOR": "norway",
    "DEN": "denmark",
    "POL": "poland",
}


@dataclass
class LeagueContext:
    matches_played: int | None = None
    goals_per_match: float | None = None
    home_win_pct: float | None = None
    draw_pct: float | None = None
    away_win_pct: float | None = None
    over15_pct: float | None = None
    over25_pct: float | None = None
    over35_pct: float | None = None
    btts_pct: float | None = None
    source: str = "soccerstats"


def _text(html: str) -> str:
    s = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", html)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return " ".join(unescape(s).replace("\xa0", " ").split())


def _pct(text: str, label: str) -> float | None:
    m = re.search(re.escape(label) + r"\s*:?[ ]*([0-9]+(?:\.[0-9]+)?)%", text, re.I)
    return float(m.group(1)) / 100.0 if m else None


def parse_summary(html: str) -> LeagueContext:
    t = _text(html)
    mp = re.search(r"([0-9]+)\s+matches played", t, re.I)
    gpm = re.search(r"Goals per match\s*:?\s*([0-9]+(?:\.[0-9]+)?)", t, re.I)
    if not gpm:
        # Current pages often show "54 matches played / 306 3.31 goals per match".
        gpm = re.search(r"([0-9]+(?:\.[0-9]+)?)\s+goals per match", t, re.I)
    return LeagueContext(
        matches_played=int(mp.group(1)) if mp else None,
        goals_per_match=float(gpm.group(1)) if gpm else None,
        home_win_pct=_pct(t, "Home wins"),
        draw_pct=_pct(t, "Draws"),
        away_win_pct=_pct(t, "Away wins"),
        over15_pct=_pct(t, "Over 1.5 goals"),
        over25_pct=_pct(t, "Over 2.5 goals"),
        over35_pct=_pct(t, "Over 3.5 goals"),
        btts_pct=_pct(t, "Both teams scored"),
    )


def url(code: str, season_start: int | None = None) -> str | None:
    slug = LEAGUES.get(code)
    if not slug:
        return None
    # SoccerSTATS historical suffix is season END year:
    # Bundesliga 2024/25 -> league=germany_2025.
    if season_start is not None:
        slug = f"{slug}_{season_start + 1}"
    return BASE + slug


def league_context(code: str, season_start: int | None = None,
                   cache_days: float = 0.25) -> tuple[LeagueContext | None, str | None]:
    u = url(code, season_start)
    if not u:
        return None, f"SoccerSTATS: Liga {code} nicht gemappt"
    html, err = fetch.get(
        u,
        cache_days=cache_days if season_start is None else 30,
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    if html is None:
        return None, err or f"SoccerSTATS {code}: Abruf fehlgeschlagen"
    ctx = parse_summary(html)
    if ctx.matches_played is None and ctx.goals_per_match is None:
        return None, f"SoccerSTATS {code}: keine Liga-Zusammenfassung geparst"
    return ctx, None
