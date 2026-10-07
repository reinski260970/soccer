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
from html.parser import HTMLParser
import re
import json
from pathlib import Path

from .. import fetch

BASE = "https://www.soccerstats.com/latest.asp?league="
READER_BASE = "https://r.jina.ai/"
HIST_CACHE = Path("data/journal/soccerstats_priors.json")
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"

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
        user_agent=BROWSER_UA,
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.soccerstats.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    if html is None:
        html, rerr = _reader_text(u, cache_days=cache_days if season_start is None else 30)
        if html is None:
            return None, rerr or err or f"SoccerSTATS {code}: Abruf fehlgeschlagen"
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


def parse_homeaway_text(html: str) -> list[TeamVenuePrior]:
    """Fallback parser for the visible SoccerSTATS Home/Away table text.

    GitHub-hosted runners can receive the normal HTML page while the Jina
    reader fallback is blocked with HTTP 403. This parser strips HTML and
    extracts the visible table rows directly.
    """
    t = _text(html)
    low = t.lower()
    hi = low.find("home table")
    ai = low.find("away table")
    if hi < 0 or ai < 0 or ai <= hi:
        return []

    home_sec = t[hi:ai]
    tail = t[ai:]
    stops = [
        tail.lower().find("relative home / away performance"),
        tail.lower().find("points & goal distribution"),
        tail.lower().find("tables overview"),
    ]
    stops = [x for x in stops if x > 0]
    away_sec = tail[:min(stops)] if stops else tail

    row_re = re.compile(
        r"(?:^|\s)(\d{1,2})\s+"
        r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9 .&'\-]{1,40}?)\s+"
        r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+"
        r"(\d+)\s+(\d+)\s+([+\-]?\d+)\s+(\d+)\s+"
        r"(\d+(?:\.\d+)?)"
    )

    def parse(section: str):
        out = {}
        for m in row_re.finditer(section):
            team = " ".join(m.group(2).split())
            gp = int(m.group(3))
            gf = float(m.group(7))
            ga = float(m.group(8))
            ppg = float(m.group(11))
            if gp <= 0 or not (0 <= ppg <= 3.01):
                continue
            out[team] = {
                "gp": gp,
                "gf_pg": gf / gp,
                "ga_pg": ga / gp,
                "ppg": ppg,
            }
        return out

    home = parse(home_sec)
    away = parse(away_sec)
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
            source="soccerstats/html-text",
        )
        for t in teams
    ]


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
    if season_start is not None:
        cached = _prior_cache_get(code, season_start)
        if cached:
            return cached, None

    u = homeaway_url(code, season_start)
    if not u:
        return [], f"SoccerSTATS: Liga {code} nicht gemappt"

    html, err = fetch.get(
        u,
        cache_days=cache_days,
        user_agent=BROWSER_UA,
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.soccerstats.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    rows = parse_homeaway_html(html) if html else []
    if not rows and html:
        rows = parse_homeaway_text(html)

    if not rows:
        text, rerr = _reader_text(u, cache_days=cache_days)
        if text:
            rows = parse_homeaway_markdown(text)
        if not rows:
            return [], rerr or err or f"SoccerSTATS {code}: Home/Away-Tabelle nicht geparst"

    if season_start is not None:
        _prior_cache_put(code, season_start, rows)
    return rows, None

def _reader_text(target_url: str, cache_days: float = 30.0) -> tuple[str | None, str | None]:
    """Browser-rendered public fallback when SoccerSTATS rejects server IPs."""
    return fetch.get(
        READER_BASE + target_url,
        cache_days=cache_days,
        retries=1,
        user_agent=BROWSER_UA,
        headers={
            "Accept": "text/plain,text/markdown,*/*",
            "X-Engine": "browser",
        },
    )


def _markdown_table(section: str) -> list[list[str]]:
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        vals = [x.strip() for x in line.strip("|").split("|")]
        # Skip markdown separator rows.
        if vals and all(re.fullmatch(r":?-{2,}:?", x or "-") for x in vals):
            continue
        rows.append(vals)
    return rows


def _clean_md_team(value: str) -> str:
    s = value.strip()
    # Jina markdown commonly emits [Team](url); keep only visible label.
    m = re.fullmatch(r"\[([^\]]+)\]\([^\)]+\)", s)
    if m:
        s = m.group(1)
    s = re.sub(r"^[0-9]+\s+", "", s).strip()
    return s


def _parse_venue_markdown_section(section: str) -> dict[str, dict]:
    out = {}
    for raw in section.splitlines():
        line = raw.strip()
        if "|" not in line:
            continue
        vals = [x.strip() for x in line.strip("|").split("|")]
        if len(vals) < 10:
            continue
        if any("GP" == x for x in vals):
            continue

        # Typical row: rank | team | GP | W | D | L | GF | GA | GD | Pts | PPG
        start = 0
        try:
            int(float(vals[0]))
            start = 1
        except (ValueError, TypeError):
            pass
        if len(vals) - start < 10:
            continue

        team = _clean_md_team(vals[start])
        nums = vals[start + 1:start + 10]
        try:
            gp = int(float(nums[0]))
            gf = float(nums[4])
            ga = float(nums[5])
            ppg = float(nums[8])
        except (ValueError, TypeError, IndexError):
            continue
        if not team or gp <= 0 or gf < 0 or ga < 0 or not (0 <= ppg <= 3.01):
            continue
        out[team] = {
            "gp": gp,
            "gf_pg": gf / gp,
            "ga_pg": ga / gp,
            "ppg": ppg,
        }
    return out


def parse_homeaway_markdown(text: str) -> list[TeamVenuePrior]:
    # Tolerate "## Home table", "# Home table", and surrounding prose.
    mh = re.search(r"(?im)^#{1,4}\s*Home table\s*$", text)
    ma = re.search(r"(?im)^#{1,4}\s*Away table\s*$", text)
    if not mh or not ma or ma.start() <= mh.end():
        return []

    home_sec = text[mh.end():ma.start()]
    tail = text[ma.end():]
    mn = re.search(r"(?im)^#{1,4}\s+[^\n]+$", tail)
    away_sec = tail[:mn.start()] if mn else tail

    home = _parse_venue_markdown_section(home_sec)
    away = _parse_venue_markdown_section(away_sec)
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
            source="soccerstats/jina",
        )
        for t in teams
    ]


def _prior_cache_load() -> dict:
    try:
        data = json.loads(HIST_CACHE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _prior_cache_get(code: str, season_start: int):
    data = _prior_cache_load()
    raw = data.get(f"{code}:{season_start}")
    if not isinstance(raw, list):
        return []
    out = []
    for r in raw:
        try:
            out.append(TeamVenuePrior(**r))
        except (TypeError, ValueError):
            continue
    return out


def _prior_cache_put(code: str, season_start: int, rows: list[TeamVenuePrior]) -> None:
    if not rows:
        return
    data = _prior_cache_load()
    data[f"{code}:{season_start}"] = [
        {
            "team": r.team,
            "home_gp": r.home_gp,
            "home_gf_pg": r.home_gf_pg,
            "home_ga_pg": r.home_ga_pg,
            "home_ppg": r.home_ppg,
            "away_gp": r.away_gp,
            "away_gf_pg": r.away_gf_pg,
            "away_ga_pg": r.away_ga_pg,
            "away_ppg": r.away_ppg,
            "source": r.source,
        }
        for r in rows
    ]
    HIST_CACHE.parent.mkdir(parents=True, exist_ok=True)
    HIST_CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
