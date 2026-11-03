"""Eigene Elo-Rechnung im ClubElo-Stil – Ersatz, solange ClubElo gesperrt ist.

Seit 25.10.2026 blockiert clubelo.com GitHub-Server (Cloudflare 403, CSV-API
502). Diese Rechnung hält die Werte selbst aktuell:

1. Ergebnisse: alle Ligaspiele der Heimligen der Europapokal-Teams und alle
   Europapokalspiele, Saisons 2024–2026 (API-Football, Endstand nach 90 Min.).
2. Lauf 1 (Einlauf): alle Teams starten bei 1500, Elo-Update K=30 mit
   Tordifferenz-Faktor. Liefert die Stärkeverhältnisse innerhalb der Ligen.
3. Verankerung: Am Ankertag (letzter echter ClubElo-Abruf) wird jede Liga um
   den mittleren Abstand ihrer Europapokal-Teams zu ClubElo verschoben
   (geschrumpft Richtung Gesamtmittel). Teams mit ClubElo-Wert starten exakt
   mit diesem Wert.
4. Lauf 2: ab dem Ankertag laufende Updates mit K=20 wie ClubElo.

Ergebnis: aktuelle Werte für alle Teams und Vor-Spiel-Werte für jedes
Europapokalspiel (für eine Kalibrierung ohne Rückschaufehler).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Callable

INIT = 1500.0
K_HIST = 30.0
K_LIVE = 20.0
H_ENGINE = 65.0
MIN_GAMES_FOR_OFFSET = 10
FINISHED = {"FT", "AET", "PEN"}

TEAM_LEAGUES = Path("data/journal/uefa_team_leagues.json")

Api = Callable[..., tuple[dict | None, str | None]]


@dataclass
class EGame:
    id: int
    t: datetime
    h: int
    a: int
    hg: int
    ag: int
    neutral: bool
    comp: str          # "L<id>" Liga, sonst ucl/uel/uecl


@dataclass
class EloResult:
    current: dict[int, float]
    prematch: dict[int, tuple[float, float]]
    league_of: dict[int, str]
    offsets: dict[str, float]
    global_offset: float
    anchor_date: date
    anchored: int
    post_games: int
    games: int
    placed: dict[str, tuple[float, int]] = field(default_factory=dict)  # Gruppe -> (Verschiebung, Spiele)


def margin(gd: int) -> float:
    gd = abs(gd)
    return 1.0 if gd <= 1 else 1.5 if gd == 2 else (11 + gd) / 8


def expect(d: float) -> float:
    return 1.0 / (1.0 + 10 ** (-d / 400))


def _update(r: dict, g: EGame, k: float) -> tuple[float, float]:
    rh, ra = r[g.h], r[g.a]
    d = rh - ra + (0.0 if g.neutral else H_ENGINE)
    res = 1.0 if g.hg > g.ag else 0.5 if g.hg == g.ag else 0.0
    delta = k * margin(g.hg - g.ag) * (res - expect(d))
    r[g.h] = rh + delta
    r[g.a] = ra - delta
    return rh, ra


def primary_league(games: list[EGame], until: datetime | None = None) -> dict[int, str]:
    """Häufigste Liga je Team in den letzten 12 Monaten vor 'until'."""
    cnt: dict[int, Counter] = defaultdict(Counter)
    last = until or max((g.t for g in games), default=None)
    for g in games:
        if not g.comp.startswith("L"):
            continue
        if last is not None and (last - g.t).days > 365:
            continue
        cnt[g.h][g.comp] += 1
        cnt[g.a][g.comp] += 1
    return {t: c.most_common(1)[0][0] for t, c in cnt.items()}


def run_engine(games: list[EGame], anchor: dict[int, float], anchor_date: date) -> EloResult:
    seen, gs = set(), []
    for g in sorted(games, key=lambda x: (x.t, x.id)):
        if g.id not in seen:
            seen.add(g.id)
            gs.append(g)
    league_of = primary_league(gs)

    # Lauf 1: Einlauf ab 1500
    r1: dict[int, float] = defaultdict(lambda: INIT)
    n_before: Counter = Counter()
    pre1: dict[int, tuple[float, float]] = {}
    snap: dict[int, float] | None = None
    for g in gs:
        if snap is None and g.t.date() >= anchor_date:
            snap = dict(r1)
        pre1[g.id] = _update(r1, g, K_HIST)
        if g.t.date() < anchor_date:
            n_before[g.h] += 1
            n_before[g.a] += 1
    if snap is None:
        snap = dict(r1)

    # Verankerung je Liga: Verschiebung o_L, die zugleich zu den ClubElo-Ankern
    # der Liga (je Team SD 60) und zu den Europapokal-Ergebnissen ihrer Teams
    # gegen andere Ligen passt; schwacher Prior (SD 150) um das Gesamtmittel.
    # So werden auch Ligen mit einem oder keinem Anker (Andorra, Gibraltar)
    # über ihre echten Ergebnisse eingeordnet statt beim Mittel zu landen.
    def group(t: int) -> str:
        return league_of.get(t, f"T{t}")

    diffs: dict[str, list[float]] = defaultdict(list)
    for t, e in anchor.items():
        if n_before[t] >= MIN_GAMES_FOR_OFFSET and t in snap:
            diffs[group(t)].append(e - snap[t])
    alld = [d for v in diffs.values() for d in v]
    g_off = sum(alld) / len(alld) if alld else 0.0
    offsets = {lg: _place(v, [], g_off) for lg, v in diffs.items()}

    cup = []
    for g in gs:
        if g.comp.startswith("L") or g.t.date() >= anchor_date:
            continue
        gh, ga = group(g.h), group(g.a)
        if gh == ga:
            continue
        h1, a1 = pre1[g.id]
        res = 1.0 if g.hg > g.ag else 0.5 if g.hg == g.ag else 0.0
        cup.append((gh, ga, h1 + (0.0 if g.neutral else H_ENGINE), a1, res, margin(g.hg - g.ag)))
    n_cup: Counter = Counter()
    for _ in range(3):
        obs: dict[str, list[tuple[float, float, float, float]]] = defaultdict(list)
        for gh, ga, hr, ar, res, w in cup:
            if ga in offsets:
                obs[gh].append((hr, ar + offsets[ga], res, w))
            if gh in offsets:
                obs[ga].append((ar, hr + offsets[gh], 1.0 - res, w))
        n_cup = Counter({k: len(v) for k, v in obs.items()})
        offsets = {grp: _place(diffs.get(grp, []), obs.get(grp, []), g_off)
                   for grp in set(diffs) | set(obs)}
    placed = {grp: (offsets[grp], n_cup[grp]) for grp in offsets if grp not in diffs}

    def off(t: int) -> float:
        return offsets.get(group(t), g_off)

    def start(t: int) -> float:
        return anchor[t] if t in anchor else snap.get(t, INIT) + off(t)

    prematch: dict[int, tuple[float, float]] = {}
    r2: dict[int, float] = {}
    post = 0
    for g in gs:
        if g.t.date() < anchor_date:
            h1, a1 = pre1[g.id]
            prematch[g.id] = (h1 + off(g.h), a1 + off(g.a))
            continue
        for t in (g.h, g.a):
            if t not in r2:
                r2[t] = start(t)
        prematch[g.id] = _update(r2, g, K_LIVE)
        post += 1

    teams = {g.h for g in gs} | {g.a for g in gs} | set(anchor)
    current = {t: r2.get(t, start(t)) for t in teams}
    return EloResult(current, prematch, league_of, offsets, g_off, anchor_date,
                     sum(1 for t in anchor if t in teams), post, len(gs), placed)


PLACE_PRIOR_SD = 150.0


SIGMA_ANCHOR = 60.0


def _place(anchors: list[float], obs: list[tuple[float, float, float, float]],
           prior: float) -> float:
    """Verschiebung o einer Liga: Anker-Abstände (ClubElo minus Einlaufwert,
    je SD 60), Europapokal-Ergebnisse obs = (eigene Wertung inkl. Heimvorteil,
    Gegner, Ergebnis 1/0.5/0, Gewicht) als Bernoulli-Likelihood, Prior SD 150."""
    import math
    best, best_ll = prior, -float("inf")
    for i in range(241):
        o = -800.0 + 5.0 * i
        ll = -((o - prior) / PLACE_PRIOR_SD) ** 2 / 2
        ll -= sum(((o - d) / SIGMA_ANCHOR) ** 2 / 2 for d in anchors)
        for own, opp, res, w in obs:
            p = min(max(expect(own + o - opp), 1e-6), 1 - 1e-6)
            ll += w * (res * math.log(p) + (1 - res) * math.log(1 - p))
        if ll > best_ll:
            best, best_ll = o, ll
    return best


# ------------------------------------------------------------------ Daten
def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def team_leagues(team_ids: list[int], season: int, api: Api, max_calls: int,
                 errs: list[str]) -> dict[int, list[int]]:
    """Heimliga(en) je Team (Typ 'League'), dauerhaft im Journal gecacht."""
    cache = _load(TEAM_LEAGUES, {})
    calls = 0
    missing = 0
    for tid in team_ids:
        if str(tid) in cache:
            continue
        if calls >= max_calls:
            missing += 1
            continue
        found: list[int] = []
        for s in (season, season - 1):
            calls += 1
            data, err = api(f"/leagues?team={tid}&season={s}")
            if data is None:
                errs.append(f"Liga von Team {tid}: {err}")
                break
            found = [int(r["league"]["id"]) for r in data.get("response") or []
                     if str((r.get("league") or {}).get("type", "")).lower() == "league"]
            if found:
                break
        if data is not None:
            cache[str(tid)] = found
    if missing:
        errs.append(f"Heimligen: {missing} Teams noch ohne Zuordnung (Abruflimit) – folgen im nächsten Lauf")
    _save(TEAM_LEAGUES, cache)
    return {int(k): v for k, v in cache.items()}


def parse_games(data: dict, comp: str) -> tuple[list[EGame], dict[int, tuple[str, str]]]:
    games, teams = [], {}
    for f in (data or {}).get("response") or []:
        try:
            lg = f.get("league") or {}
            th, ta = f["teams"]["home"], f["teams"]["away"]
            country = str(lg.get("country") or "")
            if comp.startswith("L"):
                teams[int(th["id"])] = (th["name"], country)
                teams[int(ta["id"])] = (ta["name"], country)
            if str((f["fixture"].get("status") or {}).get("short")) not in FINISHED:
                continue
            ft = (f.get("score") or {}).get("fulltime") or {}
            hg = ft.get("home") if ft.get("home") is not None else (f.get("goals") or {}).get("home")
            ag = ft.get("away") if ft.get("away") is not None else (f.get("goals") or {}).get("away")
            if hg is None or ag is None:
                continue
            games.append(EGame(int(f["fixture"]["id"]),
                               datetime.fromisoformat(f["fixture"]["date"].replace("Z", "+00:00")),
                               int(th["id"]), int(ta["id"]), int(hg), int(ag),
                               str(lg.get("round") or "").strip().lower() == "final", comp))
        except (KeyError, TypeError, ValueError):
            continue
    return games, teams


def league_games(league_ids: set[int], seasons: list[int], api: Api, errs: list[str]
                 ) -> tuple[list[EGame], dict[int, tuple[str, str]]]:
    games: list[EGame] = []
    teams: dict[int, tuple[str, str]] = {}
    for lid in sorted(league_ids):
        for s in seasons:
            data, err = api(f"/fixtures?league={lid}&season={s}&timezone=UTC", cache_days=0.5)
            if data is None:
                errs.append(f"Liga {lid}/{s}: {err}")
                continue
            g, t = parse_games(data, f"L{lid}")
            games += g
            teams.update(t)
    return games, teams
