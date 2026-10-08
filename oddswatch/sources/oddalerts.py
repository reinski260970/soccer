"""OddAlerts public xG/xGA tables.

Used only as an independent current-season cross-check for leagues outside
Understat. No odds or market information is consumed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser

from .. import fetch

BASE = "https://www.oddalerts.com/xg"

# Verified from the public xG directory / league pages in Oct 2026.
SLUGS = {
    "D2": "2-bundesliga",
    "E1": "championship",
    "AUT": "admiral-bundesliga",
    "N1": "eredivisie",
    "P1": "liga-portugal",
    "B1": "pro-league-belgium",
    "T1": "super-lig",
    "SC0": "premiership",
    "SUI": "super-league-switzerland",
    "SWE": "allsvenskan",
    "NOR": "eliteserien",
    "DEN": "superliga-denmark",
}


@dataclass
class TeamXG:
    team: str
    matches: int
    xg_per90: float
    xga_per90: float
    source: str = "oddalerts"


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
        elif self.row is not None and tag in ("th", "td"):
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
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


def _num(v):
    try:
        return float(str(v).replace(",", ".").replace("+", ""))
    except (TypeError, ValueError):
        return None


def _parse_metric_table(table, metric: str):
    if not table:
        return {}
    header = [x.strip() for x in table[0]]
    if "Team" not in header or metric not in header or "/90" not in header:
        return {}
    try:
        ti = header.index("Team")
        pi = header.index("P")
        mi = header.index("/90")
    except ValueError:
        return {}
    out = {}
    for row in table[1:]:
        if max(ti, pi, mi) >= len(row):
            continue
        team = row[ti].strip()
        p = _num(row[pi])
        per90 = _num(row[mi])
        if not team or p is None or p <= 0 or per90 is None or per90 < 0:
            continue
        out[team] = (int(p), float(per90))
    return out


def parse_html(html: str) -> list[TeamXG]:
    p = _Tables()
    p.feed(html)
    xg = {}
    xga = {}
    for table in p.tables:
        if not table:
            continue
        header = table[0]
        if "xG" in header and "xGA" not in header and not xg:
            xg = _parse_metric_table(table, "xG")
        if "xGA" in header and not xga:
            xga = _parse_metric_table(table, "xGA")
    teams = sorted(set(xg) & set(xga))
    return [
        TeamXG(team=t, matches=min(xg[t][0], xga[t][0]),
               xg_per90=xg[t][1], xga_per90=xga[t][1])
        for t in teams
    ]


def team_xg(code: str, cache_days: float = 0.10):
    slug = SLUGS.get(code)
    if not slug:
        return [], f"OddAlerts: Liga {code} nicht verifiziert"
    html, err = fetch.get(
        f"{BASE}/{slug}",
        cache_days=cache_days,
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    if html is None:
        return [], err or f"OddAlerts {code}: Abruf fehlgeschlagen"
    rows = parse_html(html)
    if not rows:
        return [], f"OddAlerts {code}: keine xG/xGA-Tabelle geparst"
    return rows, None
