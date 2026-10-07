"""MatchPulse public xG tables for leagues outside Understat.

No API key required. This provider parses the server-rendered public xG table.

Important:
- These are CURRENT season aggregates, suitable for live/pre-match context.
- They must NOT be injected retroactively into historical backtests.
- Persist snapshots from today forward if historical pre-match use is desired.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

from .. import fetch

BASE = "https://www.matchpulsestats.com/en/league"

# Verified public league IDs (2026-10-07).
LEAGUE_IDS = {
    "D1": 78,
    "D2": 79,
    "AUT": 218,
    "N1": 88,
    "P1": 94,
    "B1": 144,
    "T1": 203,
    "SC0": 179,
    "SUI": 207,
    "SWE": 113,
    "NOR": 103,
    "DEN": 119,
    "POL": 106,
}


@dataclass
class TeamXG:
    team: str
    matches: int
    xgf: float
    xgf_per_game: float
    xga: float
    xga_per_game: float
    source: str = "matchpulse"


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tr = False
        self.in_cell = False
        self.cur = []
        self.rows = []
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_tr = True
            self.cur = []
        elif self.in_tr and tag in ("td", "th"):
            self.in_cell = True
            self.buf = []

    def handle_data(self, data):
        if self.in_cell:
            self.buf.append(data)

    def handle_endtag(self, tag):
        if self.in_tr and tag in ("td", "th") and self.in_cell:
            text = " ".join("".join(self.buf).split())
            self.cur.append(text)
            self.in_cell = False
            self.buf = []
        elif tag == "tr" and self.in_tr:
            if self.cur:
                self.rows.append(self.cur)
            self.in_tr = False
            self.cur = []


def _f(v: str):
    try:
        return float(v.replace(",", "."))
    except (TypeError, ValueError):
        return None


def _i(v: str):
    try:
        return int(float(v.replace(",", ".")))
    except (TypeError, ValueError):
        return None


def parse_xg_html(text: str) -> list[TeamXG]:
    p = _TableParser()
    p.feed(text)

    out = []
    for row in p.rows:
        # Expected public table:
        # # | Team | MP | xGF | xGF/g | xGA | xGA/g | GF | GA | Diff
        if len(row) < 7:
            continue
        mp = _i(row[2])
        xgf = _f(row[3])
        xgfg = _f(row[4])
        xga = _f(row[5])
        xgag = _f(row[6])
        team = row[1].strip() if len(row) > 1 else ""
        if not team or mp is None or mp <= 0:
            continue
        if None in (xgf, xgfg, xga, xgag):
            continue
        # Reject obvious placeholder/locked rows.
        if xgf == 0 and xga == 0:
            continue
        out.append(TeamXG(team, mp, xgf, xgfg, xga, xgag))
    return out


def team_xg(code: str, cache_days: float = 0.10) -> tuple[list[TeamXG], str | None]:
    lid = LEAGUE_IDS.get(code)
    if lid is None:
        return [], f"MatchPulse: Liga {code} nicht gemappt"
    url = f"{BASE}/{lid}/xg"
    text, err = fetch.get(
        url,
        cache_days=cache_days,
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    if text is None:
        return [], err or f"MatchPulse {code}: Abruf fehlgeschlagen"
    rows = parse_xg_html(text)
    if not rows:
        return [], f"MatchPulse {code}: keine xG-Tabelle geparst"
    return rows, None
