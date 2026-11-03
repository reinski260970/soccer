"""UEFA-Club v1.1 – Modell für Champions League, Europa League, Conference League.

Aufbau (jede Stufe ist im Bericht nachvollziehbar):

1. Stärke: ClubElo-Werte (ligaübergreifend vergleichbar, daher ideal für
   Europapokale mit Teams aus 50 Verbänden).
2. Kalibrierung: Steigung b so gewählt, dass die Poisson/Dixon-Coles-Tormatrix
   genau ClubElos eigene Siegerwartung 1/(1+10^(-dr/400)) reproduziert.
   Torniveau und Heimvorteil werden per Maximum Likelihood an echten
   Europapokal-Ergebnissen (API-Football, aktuelle + Vorsaison) geschätzt und
   Richtung Prior geschrumpft. Solange zu wenige Spiele mit Vor-Spiel-Elo
   (eigene tägliche Schnappschüsse) vorliegen, wird das heutige Elo als
   Näherung benutzt – im Bericht gekennzeichnet.
3. xG-Korrektur (in Elo-Punkten): Wie viel besser/schlechter war die
   xG-Differenz eines Teams, als sein Elo gegen die jeweiligen Gegner erwarten
   lässt? Quellen: Liga-xG (Understat / MatchPulse / football-data, Liga-Schnitt
   über ClubElo der Ligateams) und Europapokal-xG (API-Football-Statistik je
   Spiel). Geschrumpft mit n/(n+10), davon 50 % übernommen.
4. Tempo: (xG + xGA) je Spiel relativ zum eigenen Ligaschnitt verschiebt das
   Torniveau (Über/Unter), geschrumpft und auf ±15 % begrenzt.
5. Märkte: 1X2, Über/Unter, BTTS aus der Tormatrix; Vergleich mit Pinnacle
   (entmargt) als Referenz und Bet365 als Wettquote. Value nur, wenn das Modell
   höchstens 15 Prozentpunkte von Pinnacle abweicht – sonst „prüfen".
6. Schattentest: jede Vorhersage wird vor Anstoß im Journal gespeichert und
   nach dem Spiel gegen Ergebnis und Pinnacle bewertet (Log-Loss, ROI).

Aufruf:  python -m oddswatch.uefa_model --days 3
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from collections import Counter

from . import fetch, matching, uefa_elo
from .models.poisson import PoissonModel, markets_from_matrix
from .sources import apifootball, clubelo, xg_external

VERSION = "UEFA-Club v1.1"
VIENNA = ZoneInfo("Europe/Vienna")

# API-Football Liga-IDs
COMPS = {2: ("ucl", "Champions League"), 3: ("uel", "Europa League"),
         848: ("uecl", "Conference League")}
FINISHED = {"FT", "AET", "PEN"}
UPCOMING = {"NS", "TBD"}

# ---- Annahmen / Priors (werden durch Daten ersetzt, sobald genug vorliegen)
PRIOR_GOALS = 1.35        # Tore je Team bei gleicher Stärke, neutraler Ort
PRIOR_HOME = 60.0         # Heimvorteil in Elo-Punkten
CALIB_PSEUDO = 200.0      # Prior-Gewicht in Spielen
CALIB_MIN_PREMATCH = 120
COMP_SHRINK = 150.0       # Pseudo-Spiele für den Torniveau-Faktor je Wettbewerb  # ab so vielen Spielen mit Vor-Spiel-Elo keine Näherung mehr
RHO = -0.05               # Dixon-Coles
XG_SHARE = 0.5            # Anteil des xG-Residuums, der ins Elo geht
XG_SHRINK = 10.0          # Pseudo-Spiele
XG_CAP = 100.0            # max. ±Elo durch xG
TEMPO_SHARE = 0.5
TEMPO_SHRINK = 15.0
TEMPO_CAP = 0.15
MIN_LEAGUE_MATCHED = 6    # mind. so viele Ligateams in ClubElo für einen Ligaschnitt
VALUE_EDGE = 0.05
MAX_DIVERGENCE = 0.15

# ClubElo-Verband -> xG-Liga (xg_external: Understat, MatchPulse, football-data)
FED_XG = {"England": "E0", "Spain": "SP1", "Italy": "I1", "France": "F1",
          "Germany": "D1", "Netherlands": "N1", "Portugal": "P1", "Belgium": "B1",
          "Turkey": "T1", "Scotland": "SC0", "Greece": "G1", "Austria": "AUT",
          "Switzerland": "SUI", "Sweden": "SWE", "Norway": "NOR", "Denmark": "DEN",
          "Poland": "POL"}

# API-Football -> ClubElo, wo der strenge Namensabgleich nicht greift
API_ALIASES = {
    "Paris Saint Germain": "Paris SG", "Manchester City": "Man City",
    "Manchester United": "Man United", "Nottingham Forest": "Forest",
    "Atletico Madrid": "Atlético", "Inter": "Internazionale", "AC Milan": "Milan",
    "Sporting CP": "Sporting", "FC Porto": "Porto", "SL Benfica": "Benfica",
    "Club Brugge KV": "Brugge", "Union St. Gilloise": "St Gillis",
    "PSV Eindhoven": "PSV", "Olympiakos Piraeus": "Olympiakos",
    "Red Star Belgrade": "Crvena Zvezda", "FK Crvena Zvezda": "Crvena Zvezda",
    "Bodo/Glimt": "Bodø/Glimt", "FC Copenhagen": "FC Kobenhavn",
    "FC Midtjylland": "Midtjylland", "Slavia Praha": "Slavia Praha",
    "Sparta Praha": "Sparta Praha", "Shakhtar Donetsk": "Shakhtar",
    "AEK Athens FC": "AEK", "AEK Athens": "AEK", "Pafos": "Paphos",
    "Bayern München": "Bayern München", "Bayern Munich": "Bayern München",
    "Salzburg": "Salzburg", "Red Bull Salzburg": "Salzburg",
    "Rapid Vienna": "Rapid Wien", "SK Rapid Wien": "Rapid Wien",
    "Austria Vienna": "Austria Wien", "Sturm Graz": "Sturm Graz",
    "Heart Of Midlothian": "Hearts", "Heart of Midlothian": "Hearts",
    "Sint-Truiden": "St Truiden", "AZ Alkmaar": "AZ",
    "Ferencvarosi TC": "Ferencvaros", "Ferencvaros": "Ferencvaros", "KuPS": "Kuopio",
}
FED_SYNONYMS = {"czech republic": "czechia", "bosnia": "bosnia and herzegovina",
                "macedonia": "north macedonia", "turkiye": "turkey"}

JOURNAL = Path("data/journal")
SNAPSHOTS = JOURNAL / "uefa_clubelo_snapshots.json"
XG_CACHE = JOURNAL / "uefa_xg_cache.json"
TEAM_CACHE = JOURNAL / "uefa_team_countries.json"
PREDICTIONS = JOURNAL / "uefa_predictions.json"
ANCHOR = JOURNAL / "uefa_elo_anchor.json"   # letzter ClubElo-Stand je API-Team-ID


# ================================================================== Datentypen
@dataclass
class Club:
    name: str
    elo: float
    fed: str
    level: int = 0


@dataclass
class UefaFixture:
    id: int
    comp: str
    kickoff: datetime
    home: str
    away: str
    home_id: int
    away_id: int
    status: str
    round: str = ""
    hg: int | None = None
    ag: int | None = None

    @property
    def neutral(self) -> bool:
        return self.round.strip().lower() == "final"

    @property
    def finished(self) -> bool:
        return self.status in FINISHED and self.hg is not None and self.ag is not None


@dataclass
class Calibration:
    goals: float           # Tore je Team bei Gleichstand
    home: float            # Heimvorteil Elo
    b: float               # Steigung
    n: int                 # Spiele im Fit
    source: str            # "Vor-Spiel-Elo" | "aktuelles Elo (Näherung)" | "Prior"
    fit_goals: float | None = None
    fit_home: float | None = None
    diag: dict = field(default_factory=dict)
    comp_factor: dict = field(default_factory=dict)  # Torniveau je Wettbewerb
    home_dog: float | None = None   # Heimvorteil, wenn das Heimteam schwächer ist
    b_mult: float = 1.0             # Steigung relativ zur ClubElo-Siegerwartung
    fit_home_dog: float | None = None
    fit_mult: float | None = None

    def __post_init__(self):
        if self.home_dog is None:
            self.home_dog = self.home

    @property
    def a(self) -> float:
        return math.log(self.goals)

    def home_for(self, diff: float) -> float:
        """Heimvorteil: Heimteam favorisiert (diff >= 0) oder Außenseiter."""
        return self.home if diff >= 0 else self.home_dog

    def lambdas(self, elo_h: float, elo_a: float, neutral: bool = False,
                tempo: float = 1.0) -> tuple[float, float]:
        d = (elo_h - elo_a + (0.0 if neutral else self.home_for(elo_h - elo_a))) / 400
        return (math.exp(self.a + self.b * d) * tempo,
                math.exp(self.a - self.b * d) * tempo)

    def expected_gd(self, elo_diff: float, venue: int) -> float:
        """Erwartete Tordifferenz aus Sicht des Teams mit Elo-Vorsprung elo_diff.
        venue: +1 Heim, -1 auswärts, 0 neutral, 2 = Mittel Heim/Auswärts (Liga)."""
        if venue == 2:
            return 0.5 * (self.expected_gd(elo_diff, 1) + self.expected_gd(elo_diff, -1))
        if venue == 0:
            lh, la = self.lambdas(elo_diff, 0.0, neutral=True)
            return lh - la
        if venue == 1:
            lh, la = self.lambdas(elo_diff, 0.0)
            return lh - la
        lh, la = self.lambdas(0.0, elo_diff)
        return la - lh

    @property
    def elo_per_goal(self) -> float:
        return 400.0 / (2.0 * self.goals * self.b)


@dataclass
class TeamAdj:
    elo_adj: float = 0.0
    tempo: float = 1.0
    notes: list[str] = field(default_factory=list)


# ================================================================== Hilfen
def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True),
                    encoding="utf-8")


def season_of(d: date) -> int:
    return d.year if d.month >= 7 else d.year - 1


def _norm_fed(s: str) -> str:
    s = matching.norm(s.replace("-", " "))
    return FED_SYNONYMS.get(s, s)


def same_fed(a: str, b: str) -> bool:
    x, y = _norm_fed(a or ""), _norm_fed(b or "")
    return bool(x and y) and (x == y or x.startswith(y) or y.startswith(x))


# ================================================================== Quellen
def clubelo_full() -> tuple[dict[str, Club], list[str]]:
    """Alle Vereine der UEFA-Verbände inkl. Spielklasse (Level).

    Nutzt dieselben Länderseiten wie sources/clubelo (1 Tag Cache)."""
    out: dict[str, Club] = {}
    errs: list[str] = []
    fails = 0
    for c in clubelo.UEFA:
        h, e = fetch.get(f"{clubelo.BASE}/{c}", timeout=20, cache_days=1.0, retries=0,
                         user_agent=clubelo.UA)
        if h is None:
            errs.append(f"ClubElo {c}: {e}")
            fails += 1
            if fails >= 3:
                errs.insert(0, f"ClubElo nicht erreichbar ({e}) – Abruf abgebrochen")
                break
            continue
        fails = 0
        for m in clubelo._OBJ.findall(h):
            try:
                o = json.loads(m)
            except ValueError:
                continue
            if not o.get("Name") or not isinstance(o.get("Elo"), (int, float)):
                continue
            try:
                lvl = int(o.get("Level") or 0)
            except (TypeError, ValueError):
                lvl = 0
            out.setdefault(o["Name"], Club(o["Name"], float(o["Elo"]),
                                           str(o.get("Federation") or ""), lvl))
    return out, errs


def _api(path: str, cache_days: float = 0.0) -> tuple[dict | None, str | None]:
    key = apifootball.api_key()
    if not key:
        return None, "API-Football: APIKEY nicht gesetzt"
    data, err = fetch.get_json(apifootball.BASE + path, headers={"x-apisports-key": key},
                               retries=1, cache_days=cache_days)
    if err:
        return None, f"API-Football {path}: {err.split(': ', 1)[-1]}"
    if isinstance(data, dict) and data.get("errors"):
        return None, f"API-Football {path}: {data['errors']}"
    return data, None


def parse_fixtures(data: dict, comp: str) -> list[UefaFixture]:
    out = []
    for f in (data or {}).get("response") or []:
        try:
            ft = (f.get("score") or {}).get("fulltime") or {}
            hg = ft.get("home") if ft.get("home") is not None else (f.get("goals") or {}).get("home")
            ag = ft.get("away") if ft.get("away") is not None else (f.get("goals") or {}).get("away")
            out.append(UefaFixture(
                id=int(f["fixture"]["id"]), comp=comp,
                kickoff=datetime.fromisoformat(f["fixture"]["date"].replace("Z", "+00:00")),
                home=f["teams"]["home"]["name"], away=f["teams"]["away"]["name"],
                home_id=int(f["teams"]["home"]["id"]), away_id=int(f["teams"]["away"]["id"]),
                status=str((f["fixture"].get("status") or {}).get("short") or ""),
                round=str((f.get("league") or {}).get("round") or ""),
                hg=None if hg is None else int(hg), ag=None if ag is None else int(ag)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def uefa_fixtures(season: int, cache_days: float) -> tuple[list[UefaFixture], list[str]]:
    out, errs = [], []
    for lid, (comp, label) in COMPS.items():
        data, err = _api(f"/fixtures?league={lid}&season={season}&timezone=UTC", cache_days)
        if data is None:
            errs.append(f"{label} {season}: {err}")
            continue
        out += parse_fixtures(data, comp)
    return out, errs


def parse_statistics_xg(data: dict) -> dict[int, float]:
    """team_id -> expected_goals aus /fixtures/statistics."""
    out = {}
    for r in (data or {}).get("response") or []:
        try:
            tid = int(r["team"]["id"])
        except (KeyError, TypeError, ValueError):
            continue
        for s in r.get("statistics") or []:
            if str(s.get("type", "")).lower() == "expected_goals" and s.get("value") not in (None, ""):
                try:
                    out[tid] = float(s["value"])
                except (TypeError, ValueError):
                    pass
    return out


def uefa_match_xg(fixtures: list[UefaFixture], max_calls: int, errs: list[str]
                  ) -> dict[int, tuple[float, float]]:
    """xG je abgeschlossenem Europapokalspiel (dauerhaft gecacht)."""
    cache = _load(XG_CACHE, {})
    calls = 0
    for f in fixtures:
        if not f.finished or str(f.id) in cache:
            continue
        if calls >= max_calls:
            errs.append(f"UEFA-xG: Abruflimit {max_calls} erreicht – Rest beim nächsten Lauf")
            break
        calls += 1
        data, err = _api(f"/fixtures/statistics?fixture={f.id}")
        if data is None:
            errs.append(f"UEFA-xG {f.home}–{f.away}: {err}")
            continue
        x = parse_statistics_xg(data)
        cache[str(f.id)] = ([x[f.home_id], x[f.away_id]]
                            if f.home_id in x and f.away_id in x else None)
    _save(XG_CACHE, cache)
    return {int(k): (v[0], v[1]) for k, v in cache.items() if v}


def team_countries(ids: set[int], max_calls: int, errs: list[str]) -> dict[int, str]:
    cache = _load(TEAM_CACHE, {})
    calls = 0
    for tid in sorted(ids):
        if str(tid) in cache:
            continue
        if calls >= max_calls:
            break
        calls += 1
        data, err = _api(f"/teams?id={tid}")
        if data is None:
            errs.append(f"Team {tid}: {err}")
            continue
        try:
            cache[str(tid)] = str(data["response"][0]["team"]["country"] or "")
        except (KeyError, IndexError, TypeError):
            cache[str(tid)] = ""
    _save(TEAM_CACHE, cache)
    return {int(k): v for k, v in cache.items()}


# ================================================================== Matching
def _aliases() -> dict[str, str]:
    al = dict(API_ALIASES)
    try:  # ESPN-Aliasliste des Scanners mitnutzen, falls importierbar
        from .scan import CLUBELO_ALIASES
        for k, v in CLUBELO_ALIASES.items():
            al.setdefault(k, v)
    except Exception:
        pass
    return al


def match_club(name: str, country: str, clubs: dict[str, Club],
               aliases: dict[str, str]) -> str | None:
    if name in aliases and aliases[name] in clubs:
        return aliases[name]
    if country:
        pool = [c for c, v in clubs.items() if same_fed(v.fed, country)]
        if pool:
            hit = matching.find_strict(name, pool, aliases)
            if hit:
                return hit
    return matching.find_strict(name, list(clubs), aliases)


def anchor_from_snapshots(info: dict[int, tuple[str, str]], ids: set[int],
                          aliases: dict[str, str]) -> dict:
    """Anker aus dem letzten gespeicherten ClubElo-Schnappschuss (ClubElo-Namen)
    für die Europapokal-Teams; Mehrfachtreffer werden verworfen."""
    snaps = _load(SNAPSHOTS, {})
    days = sorted(d for d, v in snaps.items() if v)
    if not days:
        return {}
    vals = snaps[days[-1]]
    pseudo = {n: Club(n, float(e), "") for n, e in vals.items()}
    hits: dict[int, str] = {}
    for tid in ids:
        if tid in info:
            h = match_club(info[tid][0], "", pseudo, aliases)
            if h:
                hits[tid] = h
    used = Counter(hits.values())
    teams = {str(t): pseudo[h].elo for t, h in hits.items() if used[h] == 1}
    return {"date": days[-1], "source": "ClubElo-Schnappschuss", "teams": teams}


# ================================================================== Kalibrierung
def _we_logistic(d: float) -> float:
    return 1.0 / (1.0 + 10 ** (-d))


def _we_model(a: float, b: float, d: float, rho: float = RHO) -> float:
    lh, la = math.exp(a + b * d), math.exp(a - b * d)
    m = PoissonModel(rho=rho, max_goals=10).score_matrix(lh, la)
    n = len(m)
    p1 = sum(m[i][j] for i in range(n) for j in range(i))
    px = sum(m[i][i] for i in range(n))
    return p1 + 0.5 * px


_SLOPE_CACHE: dict[float, float] = {}


def slope_for(goals: float, rho: float = RHO) -> float:
    """Steigung b, mit der die Tormatrix ClubElos Siegerwartung trifft."""
    key = round(goals, 3)
    if key in _SLOPE_CACHE:
        return _SLOPE_CACHE[key]
    a = math.log(goals)
    ds = [k / 10 for k in range(-15, 16)]

    def loss(b: float) -> float:
        return sum((_we_model(a, b, d, rho) - _we_logistic(d)) ** 2 for d in ds)

    lo, hi = 0.1, 2.5
    g = (math.sqrt(5) - 1) / 2
    for _ in range(40):
        x1, x2 = hi - g * (hi - lo), lo + g * (hi - lo)
        if loss(x1) < loss(x2):
            hi = x2
        else:
            lo = x1
    _SLOPE_CACHE[key] = (lo + hi) / 2
    return _SLOPE_CACHE[key]


def fit_calibration(rows: list[tuple[float, float, bool, int, int]], source: str,
                    rho: float = RHO) -> Calibration:
    """rows: (Elo Heim, Elo Gast, neutral, Tore Heim, Tore Gast).

    Poisson-Maximum-Likelihood für vier Größen: Torniveau, Steigungsfaktor
    (1 = ClubElo-Siegerwartung), Heimvorteil bei favorisiertem Heimteam und
    bei Heim-Außenseiter. Koordinatenweise Gittersuche, danach je nach
    Stichprobe Richtung Prior geschrumpft."""
    n = len(rows)
    if n < 30:
        return Calibration(PRIOR_GOALS, PRIOR_HOME, slope_for(PRIOR_GOALS, rho), n,
                           "Prior (zu wenige Spiele)")
    import numpy as np
    eh = np.array([r[0] for r in rows], float)
    ea = np.array([r[1] for r in rows], float)
    neu = np.array([bool(r[2]) for r in rows])
    hg = np.array([r[3] for r in rows], float)
    ag = np.array([r[4] for r in rows], float)
    raw = (eh - ea) / 400
    fav = eh >= ea
    g_grid = [round(1.0 + 0.02 * i, 2) for i in range(41)]
    slope = {g: slope_for(g, rho) for g in g_grid}
    m_grid = [round(0.6 + 0.02 * i, 2) for i in range(61)]
    h_grid = [-50.0 + 5.0 * i for i in range(51)]

    def ll(g, m, hf, hd):
        a, b = math.log(g), m * slope[g]
        d = raw + np.where(neu, 0.0, np.where(fav, hf, hd)) / 400
        lh, la = np.exp(a + b * d), np.exp(a - b * d)
        return float(np.sum(hg * np.log(lh) - lh + ag * np.log(la) - la))

    g, m, hf, hd = round(PRIOR_GOALS, 2), 1.0, PRIOR_HOME, PRIOR_HOME
    for _ in range(8):
        g = max(g_grid, key=lambda x: ll(x, m, hf, hd))
        m = max(m_grid, key=lambda x: ll(g, x, hf, hd))
        hf = max(h_grid, key=lambda x: ll(g, m, x, hd))
        hd = max(h_grid, key=lambda x: ll(g, m, hf, x))
    w = n / (n + CALIB_PSEUDO)
    goals = w * g + (1 - w) * PRIOR_GOALS
    mult = w * m + (1 - w) * 1.0
    return Calibration(goals, w * hf + (1 - w) * PRIOR_HOME, mult * slope_for(goals, rho), n, source,
                       fit_goals=g, fit_home=hf, home_dog=w * hd + (1 - w) * PRIOR_HOME,
                       b_mult=mult, fit_home_dog=hd, fit_mult=m)


def is_main_round(r: str) -> bool:
    """Ligaphase und K.-o.-Runde; Qualifikation und Quali-Play-offs zählen nicht."""
    s = (r or "").strip().lower()
    return not ("qualifying" in s or "preliminary" in s or s in ("play-offs", "playoffs"))


def calibrate(rows: list[tuple[float, float, bool, int, int, str]], source: str) -> Calibration:
    """rows: (Vor-Spiel-Elo Heim, Gast, neutral, Tore Heim, Gast, Wettbewerb) –
    nur Hauptrunden."""
    cal = fit_calibration([r[:5] for r in rows], source)
    # Diagnose je Wettbewerb: tatsächliche vs. erwartete Tore und Heimsiege
    for comp in sorted({r[5] for r in rows}):
        rs = [r for r in rows if r[5] == comp]
        exp_g = sum(sum(cal.lambdas(r[0], r[1], r[2])) for r in rs) / len(rs)
        act_g = sum(r[3] + r[4] for r in rs) / len(rs)
        w = len(rs) / (len(rs) + COMP_SHRINK)
        cal.comp_factor[comp] = 1 + w * (act_g / exp_g - 1) if exp_g > 0 else 1.0
        cal.diag[comp] = {"n": len(rs), "tore_ist": round(act_g, 2), "tore_modell": round(exp_g, 2),
                          "faktor": round(cal.comp_factor[comp], 3),
                          "heimsiege_ist": round(sum(r[3] > r[4] for r in rs) / len(rs), 3)}
    # Heim-Favorit vs. Heim-Außenseiter: Siegquote ist vs. Modell
    for key, sel in (("heim_favorit", lambda r: r[0] >= r[1]), ("heim_aussenseiter", lambda r: r[0] < r[1])):
        rs = [r for r in rows if sel(r) and not r[2]]
        if not rs:
            continue
        exp_w = 0.0
        for r in rs:
            lh, la = cal.lambdas(r[0], r[1], r[2], cal.comp_factor.get(r[5], 1.0))
            exp_w += markets_from_matrix(PoissonModel(rho=RHO).score_matrix(lh, la), lh, la)["1"]
        cal.diag[key] = {"n": len(rs), "heimsieg_ist": round(sum(r[3] > r[4] for r in rs) / len(rs), 3),
                         "heimsieg_modell": round(exp_w / len(rs), 3)}
    return cal


# ================================================================== xG-Korrektur
def domestic_xg(clubs: dict[str, Club], wanted: set[str], cal: Calibration,
                as_of: datetime, errs: list[str]) -> dict[str, dict]:
    """club -> {n, resid, tempo_ratio, line, source} aus der heimischen Liga."""
    out: dict[str, dict] = {}
    feds = {clubs[c].fed for c in wanted}
    for fed, code in FED_XG.items():
        if not any(same_fed(fed, f) for f in feds):
            continue
        rows, err = xg_external.snapshot(code, as_of)
        if not rows:
            errs.append(f"Liga-xG {fed}: {err}")
            continue
        try:
            xg_external.persist_snapshot(code, rows, as_of)
        except Exception:
            pass
        pool = [c for c, v in clubs.items() if same_fed(v.fed, fed)]
        mapped = {}
        for r in rows:
            hit = matching.find_strict(r.team, pool, API_ALIASES)
            if hit:
                mapped[r.team] = hit
        if len(mapped) < MIN_LEAGUE_MATCHED:
            errs.append(f"Liga-xG {fed}: nur {len(mapped)} Teams zugeordnet – übersprungen")
            continue
        lg_elo = sum(clubs[c].elo for c in mapped.values()) / len(mapped)
        lg_tot = sum(r.xg + r.xga for r in rows) / len(rows)
        for r in rows:
            c = mapped.get(r.team)
            if c not in wanted or r.matches <= 0:
                continue
            exp_gd = cal.expected_gd(clubs[c].elo - lg_elo, 2)
            out[c] = {"n": r.matches, "resid": (r.xg - r.xga) - exp_gd,
                      "tempo_ratio": (r.xg + r.xga) / lg_tot if lg_tot > 0 else 1.0,
                      "source": r.source,
                      "line": f"Liga ({r.source}, {r.matches} Sp.): xG {r.xg:.2f}:{r.xga:.2f}/Sp., "
                              f"Elo-Erwartung {exp_gd:+.2f}"}
    return out


def uefa_xg_resid(finished: list[UefaFixture], xg: dict[int, tuple[float, float]],
                  cmap: dict[int, str], clubs: dict[str, Club], cal: Calibration,
                  season: int, prematch: dict[int, tuple[float, float]] | None = None
                  ) -> dict[str, dict]:
    acc: dict[str, list[float]] = {}
    for f in finished:
        if f.id not in xg or season_of(f.kickoff.date()) != season:
            continue
        h, a = cmap.get(f.home_id), cmap.get(f.away_id)
        if not h or not a:
            continue
        hx, ax = xg[f.id]
        pe = (prematch or {}).get(f.id)
        diff = (pe[0] - pe[1]) if pe else clubs[h].elo - clubs[a].elo
        exp_h = cal.expected_gd(diff, 0 if f.neutral else 1)
        acc.setdefault(h, []).append((hx - ax) - exp_h)
        acc.setdefault(a, []).append((ax - hx) + exp_h)
    return {c: {"n": len(v), "resid": sum(v) / len(v)} for c, v in acc.items()}


def team_adjustments(clubs_needed: set[str], clubs: dict[str, Club], dom: dict,
                     uefa: dict, cal: Calibration) -> dict[str, TeamAdj]:
    out = {}
    for c in clubs_needed:
        ta = TeamAdj()
        d, u = dom.get(c), uefa.get(c)
        nd, nu = (d or {}).get("n", 0), (u or {}).get("n", 0)
        if nd + nu > 0:
            r = ((d["resid"] * nd if d else 0.0) + (u["resid"] * nu if u else 0.0)) / (nd + nu)
            n = nd + nu
            adj = XG_SHARE * r * cal.elo_per_goal * n / (n + XG_SHRINK)
            ta.elo_adj = max(-XG_CAP, min(XG_CAP, adj))
            if d:
                ta.notes.append(d["line"])
            if u:
                ta.notes.append(f"Europapokal ({nu} Sp.): xG-Residuum {u['resid']:+.2f}/Sp.")
            ta.notes.append(f"xG-Korrektur {ta.elo_adj:+.0f} Elo")
        else:
            ta.notes.append("keine xG-Daten – reines ClubElo")
        if d:
            w = TEMPO_SHARE * nd / (nd + TEMPO_SHRINK)
            t = d["tempo_ratio"] ** w if d["tempo_ratio"] > 0 else 1.0
            ta.tempo = max(1 - TEMPO_CAP, min(1 + TEMPO_CAP, t))
        out[c] = ta
    return out


# ================================================================== Märkte
def devig(odds: dict[str, float], keys: list[str]) -> dict[str, float] | None:
    if not all(k in odds and odds[k] > 1.0 for k in keys):
        return None
    inv = {k: 1.0 / odds[k] for k in keys}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


MARKETS = [("1", "home"), ("X", "draw"), ("2", "away"), ("O2.5", "O2.5"), ("U2.5", "U2.5:no")]


def assess(probs: dict[str, float], books: dict[str, dict[str, float]]) -> list[dict]:
    """Je Markt: Modell, Pinnacle (entmargt), Bet365-Quote, Edge, Status."""
    pin = books.get("Pinnacle", {})
    ref = {}
    for keys in (["home", "draw", "away"], ["O2.5", "U2.5:no"]):
        dv = devig(pin, keys)
        if dv:
            ref.update(dv)
    b365 = books.get("Bet365", {})
    out = []
    for mk, ok in MARKETS:
        p = probs[mk]
        o = b365.get(ok)
        r = ref.get(ok)
        edge = p * o - 1 if o else None
        status = ""
        if edge is not None and edge >= VALUE_EDGE:
            if r is None:
                status = "VALUE (ohne Pinnacle-Check)"
            elif abs(p - r) <= MAX_DIVERGENCE:
                status = "VALUE"
            else:
                status = "PRÜFEN (Modell weicht >15 Pp. von Pinnacle ab)"
        out.append({"markt": mk, "p_modell": p, "p_pinnacle": r, "quote_bet365": o,
                    "edge": edge, "status": status})
    return out


# ================================================================== Schattentest
def evaluate_journal(pred: dict, finished_by_id: dict[int, UefaFixture]) -> dict:
    ll_m = ll_p = 0.0
    n_both = 0
    n_all = 0
    ll_all = 0.0
    bets = profit = 0.0
    for fid, rec in pred.items():
        f = finished_by_id.get(int(fid))
        if not f:
            continue
        res = "1" if f.hg > f.ag else "X" if f.hg == f.ag else "2"
        over = f.hg + f.ag > 2.5
        rec["ergebnis"] = f"{f.hg}:{f.ag}"
        pm = rec["probs"][res]
        n_all += 1
        ll_all += -math.log(max(pm, 1e-9))
        pp = (rec.get("pinnacle") or {}).get({"1": "home", "X": "draw", "2": "away"}[res])
        if pp:
            n_both += 1
            ll_m += -math.log(max(pm, 1e-9))
            ll_p += -math.log(max(pp, 1e-9))
        for v in rec.get("values", []):
            if not v["status"].startswith("VALUE"):
                continue
            won = {"1": res == "1", "X": res == "X", "2": res == "2",
                   "O2.5": over, "U2.5": not over}[v["markt"]]
            bets += 1
            profit += (v["quote_bet365"] - 1) if won else -1
    return {"spiele": n_all, "logloss_modell": ll_all / n_all if n_all else None,
            "spiele_mit_pinnacle": n_both,
            "logloss_modell_vs": ll_m / n_both if n_both else None,
            "logloss_pinnacle": ll_p / n_both if n_both else None,
            "value_wetten": int(bets), "gewinn_einheiten": profit,
            "roi": profit / bets if bets else None}


# ================================================================== Lauf
@dataclass
class Prediction:
    fx: UefaFixture
    home_club: str
    away_club: str
    elo_h: float
    elo_a: float
    adj_h: TeamAdj
    adj_a: TeamAdj
    probs: dict
    values: list[dict]


def run(start: date, days: int, with_odds: bool = True, out_dir: Path = Path("reports/uefa"),
        now: datetime | None = None) -> tuple[Path, list[Prediction]]:
    now = now or datetime.now(timezone.utc)
    issues: list[str] = []
    season = season_of(start)

    fx_now, errs = uefa_fixtures(season, cache_days=0.02)
    issues += errs
    fx_prev, errs = uefa_fixtures(season - 1, cache_days=30)
    issues += errs
    fx_old, errs = uefa_fixtures(season - 2, cache_days=30)
    issues += errs
    all_fx = fx_now + fx_prev
    finished = [f for f in all_fx if f.finished]
    window_end = datetime.combine(start + timedelta(days=days), datetime.min.time(), timezone.utc)
    upcoming = sorted([f for f in fx_now if f.status in UPCOMING and now <= f.kickoff < window_end],
                      key=lambda f: f.kickoff)

    # Heimligen der Europapokal-Teams und deren Ligaspiele (API-Football)
    cur_ids = sorted({f.home_id for f in fx_now} | {f.away_id for f in fx_now})
    hist_ids = sorted(({f.home_id for f in fx_prev + fx_old} | {f.away_id for f in fx_prev + fx_old})
                      - set(cur_ids))
    countries = team_countries(set(cur_ids), max_calls=300, errs=issues)
    tl = uefa_elo.team_leagues(cur_ids + hist_ids, season, _api, max_calls=400, errs=issues)
    leagues = {lg for t in cur_ids + hist_ids for lg in tl.get(t, [])}
    dom_games, info = uefa_elo.league_games(leagues, [season - 2, season - 1, season], _api, issues)
    cup_games = [uefa_elo.EGame(f.id, f.kickoff, f.home_id, f.away_id, f.hg, f.ag, f.neutral, f.comp)
                 for f in fx_old + fx_prev + fx_now if f.finished]
    for f in fx_old + fx_prev + fx_now:
        for tid, nm in ((f.home_id, f.home), (f.away_id, f.away)):
            if tid not in info or not info[tid][1]:
                info[tid] = (nm, countries.get(tid, info.get(tid, ("", ""))[1]))

    # Elo-Anker: ClubElo live, sonst letzter gespeicherter ClubElo-Stand
    aliases = _aliases()
    today = now.date().isoformat()
    live, errs = clubelo_full()
    if live:
        amap = {}
        for tid, (nm, ct) in info.items():
            hit = match_club(nm, ct, live, aliases)
            if hit:
                amap[tid] = live[hit].elo
        anchor_doc = {"date": today, "source": "ClubElo", "teams": {str(k): round(v, 1) for k, v in amap.items()}}
        _save(ANCHOR, anchor_doc)
        snaps = _load(SNAPSHOTS, {})
        day: dict[str, float] = {}
        for t in cur_ids:
            hit = match_club(info[t][0], info[t][1], live, aliases) if t in info else None
            if hit:
                day[hit] = round(live[hit].elo, 1)
        snaps[today] = day
        _save(SNAPSHOTS, snaps)
    else:
        issues.append("ClubElo heute nicht erreichbar (" + (errs[0][:120] if errs else "?")
                      + ") – eigene Elo-Rechnung")
        anchor_doc = _load(ANCHOR, {})
        if not anchor_doc.get("teams"):
            anchor_doc = anchor_from_snapshots(info, set(cur_ids), aliases)
            if anchor_doc.get("teams"):
                _save(ANCHOR, anchor_doc)
        if not anchor_doc.get("teams"):
            raise SystemExit("Weder ClubElo noch gespeicherter ClubElo-Anker verfügbar – kein Modelllauf.")
    anchor = {int(k): float(v) for k, v in anchor_doc["teams"].items()}
    res = uefa_elo.run_engine(dom_games + cup_games, anchor, date.fromisoformat(anchor_doc["date"]))

    # Teams: eindeutiger Anzeigename je API-Team
    namecount = Counter(info.get(t, (str(t), ""))[0] for t in res.current)
    clubs: dict[str, Club] = {}
    cmap: dict[int, str] = {}
    for t, e in res.current.items():
        nm, ct = info.get(t, (f"Team {t}", ""))
        key = nm if namecount[nm] == 1 else f"{nm} ({ct})"
        clubs[key] = Club(key, e, ct)
        cmap[t] = key
    unmatched_now = sorted({n for f in upcoming for t, n in ((f.home_id, f.home), (f.away_id, f.away))
                            if t not in cmap})
    meta = {"anchor_date": anchor_doc["date"], "live": bool(live), "anchored": res.anchored,
            "games": res.games, "post": res.post_games, "leagues": len(leagues),
            "teams": len(res.current), "offset": res.global_offset}

    rows = [(*res.prematch[f.id], f.neutral, f.hg, f.ag, f.comp) for f in finished
            if is_main_round(f.round) and f.id in res.prematch]
    cal = calibrate(rows, "Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde")
    meta["excluded"] = sum(1 for f in finished if not is_main_round(f.round))

    needed = {cmap[t] for f in upcoming for t in (f.home_id, f.away_id) if t in cmap}
    xg_u = uefa_match_xg([f for f in fx_now if f.finished], max_calls=200, errs=issues)
    dom = domestic_xg(clubs, needed, cal, now, issues)
    ures = uefa_xg_resid(finished, xg_u, cmap, clubs, cal, season, res.prematch)
    adjs = team_adjustments(needed, clubs, dom, ures, cal)

    preds: list[Prediction] = []
    journal = _load(PREDICTIONS, {})
    for f in upcoming:
        h, a = cmap.get(f.home_id), cmap.get(f.away_id)
        if not h or not a:
            continue
        ah, aa = adjs[h], adjs[a]
        eh, ea = clubs[h].elo + ah.elo_adj, clubs[a].elo + aa.elo_adj
        lh, la = cal.lambdas(eh, ea, f.neutral, tempo=math.sqrt(ah.tempo * aa.tempo)
                             * cal.comp_factor.get(f.comp, 1.0))
        probs = markets_from_matrix(PoissonModel(rho=RHO).score_matrix(lh, la), lh, la)
        books = {}
        if with_odds:
            books, err = apifootball.odds(f.id)
            if err:
                issues.append(f"Quoten {f.home}–{f.away}: {err}")
        values = assess(probs, books)
        preds.append(Prediction(f, h, a, eh, ea, ah, aa, probs, values))
        pin = devig(books.get("Pinnacle", {}), ["home", "draw", "away"])
        journal[str(f.id)] = {
            "erstellt": now.isoformat(), "anstoss": f.kickoff.isoformat(), "wettbewerb": f.comp,
            "spiel": f"{f.home} – {f.away}", "version": VERSION,
            "probs": {k: round(probs[k], 4) for k in ("1", "X", "2", "O2.5", "U2.5", "BTTS_Y")},
            "xg": [round(lh, 2), round(la, 2)], "pinnacle": pin,
            "values": [v for v in values if v["status"]],
        }
    _save(PREDICTIONS, journal)

    by_id = {f.id: f for f in finished}
    evaluation = evaluate_journal({k: v for k, v in journal.items()
                                   if datetime.fromisoformat(v["anstoss"]) < now}, by_id)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"{start.isoformat()}-uefa-modell.md"
    md.write_text(render(start, days, now, clubs, cal, preds, dom, xg_u, evaluation, issues,
                         unmatched_now, len(upcoming), meta), encoding="utf-8")
    write_csv(out_dir / f"{start.isoformat()}-uefa-modell.csv", preds)
    return md, preds


# ================================================================== Ausgabe
_WD = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _ko(dt: datetime) -> str:
    v = dt.astimezone(VIENNA)
    return f"{_WD[v.weekday()]} {v:%d.%m. %H:%M}"


def _pct(x) -> str:
    return "–" if x is None else f"{x * 100:.0f} %"


def render(start, days, now, clubs, cal, preds, dom, xg_u, ev, issues, unmatched, n_up,
           meta: dict | None = None) -> str:
    meta = meta or {}
    L = [f"# {VERSION} – Champions League · Europa League · Conference League",
         f"Stand {now.astimezone(VIENNA):%d.%m.%Y %H:%M} (Wien), Spiele {start:%d.%m.} bis "
         f"{start + timedelta(days=days - 1):%d.%m.%Y}", ""]
    ad = meta.get("anchor_date")
    if meta.get("live"):
        elo_line = f"- Elo: ClubElo live ({meta.get('anchored', 0)} Teams zugeordnet)"
    elif ad:
        elo_line = (f"- Elo: **eigene Elo-Rechnung** (ClubElo von GitHub aus gesperrt), verankert an "
                    f"ClubElo vom {date.fromisoformat(ad):%d.%m.%Y} ({meta.get('anchored', 0)} Teams), "
                    f"seither {meta.get('post', 0)} Spiele eingerechnet")
    else:
        elo_line = f"- Elo: {len(clubs)} Teams"
    L += ["## Datenbasis", elo_line]
    if meta.get("games"):
        L.append(f"- Ergebnisbasis: {meta['games']} Spiele aus {meta.get('leagues', 0)} Ligen + Europapokal "
                 f"(API-Football, seit 2024), {meta.get('teams', 0)} Teams")
    L += [f"- Kalibrierung ({cal.source}): {cal.n} Spiele"
          + (f", {meta['excluded']} Quali-/Play-off-Spiele ausgeschlossen" if meta.get("excluded") else "")
          + f" → {cal.goals:.2f} Tore je Team bei Gleichstand, Steigung {cal.b:.3f} "
          f"(×{cal.b_mult:.2f} ggü. ClubElo-Erwartung, {cal.elo_per_goal:.0f} Elo ≈ 1 Tor)",
          f"- Heimvorteil: Heimteam favorisiert {cal.home:.0f} Elo, Heimteam Außenseiter {cal.home_dog:.0f} Elo"
          + (f" (reiner Fit {cal.fit_home:.0f} / {cal.fit_home_dog:.0f}, Steigung ×{cal.fit_mult:.2f}, "
             f"Tore {cal.fit_goals:.2f}; Richtung Prior geschrumpft)" if cal.fit_home_dog is not None else ""),
          f"- xG: Liga-xG für {len(dom)} Teams, Europapokal-xG aus {len(xg_u)} Spielen", ""]
    comps = [(k, d) for k, d in cal.diag.items() if k in {v[0] for v in COMPS.values()}]
    if comps:
        L += ["| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |",
              "|---|---|---|---|---|---|"]
        for comp, d in comps:
            lab = next(v[1] for v in COMPS.values() if v[0] == comp)
            L.append(f"| {lab} | {d['n']} | {d['tore_ist']:.2f} | {d['tore_modell']:.2f} | ×{d['faktor']:.3f} | "
                     f"{d['heimsiege_ist'] * 100:.0f} % |")
        L.append("")
    hv = [(lab, cal.diag[k]) for k, lab in (("heim_favorit", "Heimteam favorisiert"),
                                            ("heim_aussenseiter", "Heimteam Außenseiter")) if k in cal.diag]
    if hv:
        L += ["| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |", "|---|---|---|---|"]
        L += [f"| {lab} | {d['n']} | {d['heimsieg_ist'] * 100:.1f} % | {d['heimsieg_modell'] * 100:.1f} % |"
              for lab, d in hv]
        L.append("")

    vals = [(p, v) for p in preds for v in p.values if v["status"].startswith("VALUE")]
    L += ["## Value-Kandidaten (Bet365)"]
    if vals:
        L += ["| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |", "|---|---|---|---|---|---|---|"]
        for p, v in sorted(vals, key=lambda x: -x[1]["edge"]):
            L.append(f"| {_ko(p.fx.kickoff)} | {p.fx.home} – {p.fx.away} | "
                     f"{v['markt']} | {_pct(v['p_modell'])} | {_pct(v['p_pinnacle'])} | "
                     f"{v['quote_bet365']:.2f} | {v['edge'] * 100:+.1f} % |")
    else:
        L.append("Keine Wette über der Schwelle (Edge ≥ 5 %, Abweichung zu Pinnacle ≤ 15 Pp.).")
    chk = [(p, v) for p in preds for v in p.values if v["status"].startswith("PRÜFEN")]
    if chk:
        L += ["", "Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):"]
        L += [f"- {p.fx.home} – {p.fx.away}: {v['markt']} Modell {_pct(v['p_modell'])} vs. "
              f"Pinnacle {_pct(v['p_pinnacle'])}" for p, v in chk]
    L.append("")

    for comp, label in [v for v in COMPS.values()]:
        ps = [p for p in preds if p.fx.comp == comp]
        if not ps:
            continue
        L += [f"## {label}", "| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for p in ps:
            pin = {v["markt"]: v["p_pinnacle"] for v in p.values}
            pin_s = "–" if pin.get("1") is None else \
                f"{_pct(pin['1'])} / {_pct(pin['X'])} / {_pct(pin['2'])}"
            L.append(f"| {_ko(p.fx.kickoff)} | {p.fx.home} – {p.fx.away}"
                     f"{' (neutral)' if p.fx.neutral else ''} | {p.elo_h:.0f} : {p.elo_a:.0f} | "
                     f"{p.probs['xg_home']:.2f} : {p.probs['xg_away']:.2f} | {_pct(p.probs['1'])} | "
                     f"{_pct(p.probs['X'])} | {_pct(p.probs['2'])} | {_pct(p.probs['O2.5'])} | "
                     f"{_pct(p.probs['BTTS_Y'])} | {pin_s} |")
        L += ["", "<details><summary>Herleitung je Team</summary>", ""]
        for p in ps:
            for club, e, ta in ((p.home_club, p.elo_h, p.adj_h), (p.away_club, p.elo_a, p.adj_a)):
                L.append(f"- **{club}**: Elo {clubs[club].elo:.0f} → {e:.0f}; "
                         + "; ".join(ta.notes) + (f"; Tempo ×{ta.tempo:.2f}" if ta.tempo != 1 else ""))
        L += ["", "</details>", ""]
    if not preds:
        L += [f"Keine bewertbaren Spiele im Zeitraum ({n_up} angesetzt).", ""]

    L += ["## Schattentest (gespeicherte Vorhersagen vor Anstoß)"]
    if ev["spiele"]:
        L.append(f"- {ev['spiele']} Spiele ausgewertet, Log-Loss 1X2 Modell {ev['logloss_modell']:.3f}")
        if ev["spiele_mit_pinnacle"]:
            L.append(f"- Gegen Pinnacle ({ev['spiele_mit_pinnacle']} Spiele): Modell "
                     f"{ev['logloss_modell_vs']:.3f} vs. Pinnacle {ev['logloss_pinnacle']:.3f} "
                     "(kleiner = besser)")
        if ev["value_wetten"]:
            L.append(f"- Value-Wetten: {ev['value_wetten']}, Ergebnis {ev['gewinn_einheiten']:+.2f} "
                     f"Einheiten, ROI {ev['roi'] * 100:+.1f} %")
        L.append("- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.")
    else:
        L.append("- Noch keine abgeschlossenen Spiele mit gespeicherter Vorhersage.")
    L.append("")

    if unmatched or issues:
        L += ["## Hinweise"]
        L += [f"- Ohne Elo-Wert (nicht bewertet): {', '.join(unmatched)}"] if unmatched else []
        L += [f"- {i}" for i in issues[:25]]
        L.append("")
    L += ["## Methode (Kurzfassung)",
          "Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → "
          "Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit "
          "und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo "
          "geschätzt, Qualifikation ausgeschlossen. "
          f"xG-Korrektur: {XG_SHARE:.0%} des Residuums (xG-Differenz minus Elo-Erwartung) × "
          f"n/(n+{XG_SHRINK:.0f}), max. ±{XG_CAP:.0f} Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. "
          "Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den "
          "Schattentest überprüft."]
    return "\n".join(L) + "\n"


def write_csv(path: Path, preds: list[Prediction]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["anstoss_wien", "wettbewerb", "heim", "gast", "elo_heim", "elo_gast", "xg_heim",
                    "xg_gast", "p1", "pX", "p2", "pO25", "pU25", "pBTTS", "pin1", "pinX", "pin2",
                    "b365_1", "b365_X", "b365_2", "b365_O25", "b365_U25", "value"])
        for p in preds:
            v = {x["markt"]: x for x in p.values}

            def f4(x):
                return "" if x is None else f"{x:.4f}".replace(".", ",")
            w.writerow([p.fx.kickoff.astimezone(VIENNA).strftime("%Y-%m-%d %H:%M"), p.fx.comp,
                        p.fx.home, p.fx.away, f"{p.elo_h:.0f}", f"{p.elo_a:.0f}",
                        f4(p.probs["xg_home"]), f4(p.probs["xg_away"]),
                        *(f4(p.probs[k]) for k in ("1", "X", "2", "O2.5", "U2.5", "BTTS_Y")),
                        *(f4(v[k]["p_pinnacle"]) for k in ("1", "X", "2")),
                        *(f4(v[k]["quote_bet365"]) for k in ("1", "X", "2", "O2.5", "U2.5")),
                        " | ".join(f"{x['markt']} {x['edge'] * 100:+.1f}%" for x in p.values
                                   if x["status"].startswith("VALUE"))])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=VERSION)
    ap.add_argument("--start", help="erster Spieltag YYYY-MM-DD (Standard: heute)")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--no-odds", action="store_true", help="ohne Quotenabruf")
    ap.add_argument("--out", default="reports/uefa")
    a = ap.parse_args(argv)
    start = date.fromisoformat(a.start) if a.start else datetime.now(timezone.utc).date()
    md, preds = run(start, a.days, with_odds=not a.no_odds, out_dir=Path(a.out))
    print(md.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
