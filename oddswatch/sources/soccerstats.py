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


@dataclass
class TeamVenuePrior:
    team: str
    home_gp: int
    home_gf_pg: float
    home_ga_pg: float
    home_ppg: float
    away_gp: int
    away_gf_pg: float
    away_ga_pg: float
    away_ppg: float
    source: str = "soccerstats"


class _Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table = []
        elif self.table is not None and tag == "tr":
            self.row = []
        elif self.row is not None and tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            if self.table:
                self.tables.append(self.table)
            self.table = None


def _venue_rows(table):
    """Parse a SoccerSTATS home/away table to team venue stats.

    Expected logical columns include Team, GP, W, D, L, GF, GA, GD, Pts, PPG.
    The parser tolerates leading rank columns and decorative cells.
    """
    out = {}
    for row in table:
        vals = [x.strip() for x in row if x.strip()]
        if len(vals) < 8:
            continue
        # Find a plausible team cell followed by GP/W/D/L/GF/GA.
        for i in range(max(1, len(vals) - 9)):
            team = vals[i]
            if not re.search(r"[A-Za-zÀ-ÿ]", team):
                continue
            nums = vals[i + 1:i + 10]
            if len(nums) < 8:
                continue
            try:
                gp = int(float(nums[0]))
                gf = float(nums[4])
                ga = float(nums[5])
                ppg = float(nums[8]) if len(nums) > 8 else float(nums[-1])
            except (ValueError, TypeError):
                continue
            if gp <= 0 or gf < 0 or ga < 0 or not (0 <= ppg <= 3.01):
                continue
            out[team] = {
                "gp": gp,
                "gf_pg": gf / gp,
                "ga_pg": ga / gp,
                "ppg": ppg,
            }
            break
    return out


def parse_homeaway_html(html: str) -> list[TeamVenuePrior]:
    p = _Tables()
    p.feed(html)
    candidates = []
    for table in p.tables:
        rows = _venue_rows(table)
        if len(rows) >= 6:
            candidates.append(rows)
    if len(candidates) < 2:
        return []

    # SoccerSTATS homeaway.asp exposes Home table before Away table.
    home, away = candidates[0], candidates[1]
    teams = sorted(set(home) & set(away))
    return [
        TeamVenuePrior(
            team=t,
            home_gp=home[t]["gp"],
            home_gf_pg=home[t]["gf_pg"],
            home_ga_pg=home[t]["ga_pg"],
            home_ppg=home[t]["ppg"],
            away_gp=away[t]["gp"],
            away_gf_pg=away[t]["gf_pg"],
            away_ga_pg=away[t]["ga_pg"],
            away_ppg=away[t]["ppg"],
        )
        for t in teams
    ]


def homeaway_url(code: str, season_start: int | None = None) -> str | None:
    slug = LEAGUES.get(code)
    if not slug:
        return None
    if season_start is not None:
        slug = f"{slug}_{season_start + 1}"
    return f"https://www.soccerstats.com/homeaway.asp?league={slug}"


def team_homeaway(code: str, season_start: int | None = None,
                  cache_days: float = 30.0) -> tuple[list[TeamVenuePrior], str | None]:
    u = homeaway_url(code, season_start)
    if not u:
        return [], f"SoccerSTATS: Liga {code} nicht gemappt"
    html, err = fetch.get(
        u,
        cache_days=cache_days,
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    if html is None:
        return [], err or f"SoccerSTATS {code}: Home/Away-Abruf fehlgeschlagen"
    rows = parse_homeaway_html(html)
    if not rows:
        return [], f"SoccerSTATS {code}: Home/Away-Tabelle nicht geparst"
    return rows, None
