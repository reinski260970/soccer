"""Tipsport Extraliga: Ergebnisse der laufenden Saison von ceskyhokej.cz.

Offizielle Seite des Tschechischen Eishockeyverbands. Die Spielliste ist
seitenweise (50 Spiele je Seite). Jedes beendete Spiel hat die Drittelergebnisse
("0:1, 2:1, 1:3", ggf. " - 0:1" für Verlängerung/Penaltys); daraus wird das
60-Minuten-Ergebnis summiert, das das Modell braucht.
"""
from __future__ import annotations

import html
import re
import time
from datetime import datetime

from .. import fetch
from .hockeyarchives import HockeyResult

BASE = "https://ceskyhokej.cz"
COMPETITION = {2026: 14}          # Saisonstart -> Wettbewerbs-ID Tipsport extraliga
MAX_PAGES = 20

# ceskyhokej.cz-Namen -> hockeyarchives-Namen (Modellhistorie)
NAMES = {
    "HC DYNAMO PARDUBICE": "Pardubice", "Mountfield HK, a.s.": "Hradec Králové",
    "HC Sparta Praha": "Sparta Prague", "BANES Motor České Budějovice": "České Budějovice",
    "BK Mladá Boleslav": "Mladá Boleslav", "HC ŠKODA PLZEŇ": "Plzeň",
    "Bílí Tygři Liberec": "Liberec", "Rytíři Kladno": "Kladno",
    "HC Oceláři Třinec": "Třinec", "HC KOMETA BRNO": "Brno",
    "HC Energie Karlovy Vary": "Karlovy Vary", "HC Olomouc": "Olomouc",
    "HC VÍTKOVICE RIDERA": "Vítkovice", "HC Verva Litvínov": "Litvínov",
    "HC Litvínov": "Litvínov",
}

_ITEM = re.compile(r'<a href="/game/detail/(\d+)" class="game-item">(.*?)</a>', re.S)
_TEAM = re.compile(r'<h4 class="h4">(.*?)</h4>', re.S)
_PERIODS = re.compile(r"(\d+):(\d+),\s*(\d+):(\d+),\s*(\d+):(\d+)(?:\s*-\s*(\d+):(\d+))?")
_DATE = re.compile(r"(\d{2})\.\s*(\d{2})\.\s*(\d{4}),\s*(\d{1,2}):(\d{2})")
_MARK = re.compile(r">\s*(P|SN)\s*<")


def canonical(name: str) -> str:
    name = " ".join(html.unescape(name).split())
    return NAMES.get(name, name)


def parse_page(text: str) -> dict[str, HockeyResult]:
    out: dict[str, HockeyResult] = {}
    for gid, block in _ITEM.findall(text):
        teams = [canonical(t) for t in _TEAM.findall(block)]
        info = block.split('class="game-info"', 1)[-1]
        p, d = _PERIODS.search(info), _DATE.search(info)
        if len(teams) != 2 or not p or not d:
            continue                     # angesetzt, noch ohne Ergebnis
        g = [int(x) for x in p.groups()[:6]]
        periods = ((g[0], g[1]), (g[2], g[3]), (g[4], g[5]))
        extra = ""
        if p.group(7) is not None:
            extra = "SO" if _MARK.search(block) and "SN" in _MARK.findall(block) else "OT"
        day = datetime(int(d.group(3)), int(d.group(2)), int(d.group(1))).date()
        out[gid] = HockeyResult(day, teams[0], teams[1],
                                g[0] + g[2] + g[4], g[1] + g[3] + g[5], extra, periods)
    return out


def season_results(season_start: int) -> tuple[list[HockeyResult], str | None]:
    cid = COMPETITION.get(season_start)
    if cid is None:
        return [], f"ceskyhokej.cz: keine Wettbewerbs-ID für Saison {season_start}"
    found: dict[str, HockeyResult] = {}
    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE}/competition/games/{cid}"
        if page > 1:
            url += f"?gameListWidget-page={page}&do=gameListWidget-changePage"
        text, err = fetch.get(url, cache_days=0.25, user_agent="Mozilla/5.0 oddswatch")
        if err:
            return list(found.values()), (None if found else f"ceskyhokej.cz: {err}")
        new = {k: v for k, v in parse_page(text or "").items() if k not in found}
        if not new and page > 1:
            break
        found.update(new)
        if "gameListWidget-page=" + str(page + 1) not in (text or ""):
            break
        time.sleep(0.5)
    return sorted(found.values(), key=lambda r: r.date), None
