"""Modelle und unabhängige Referenzen; Fußballpreise über API-Football."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import matching, pricing, report
from .journal import Journal
from .models import fatigue
from .models.elo import EloGoals
from .models.m8 import M8Model, M8Params
from .models.fatigue import Effects, Slot, TeamLoad
from .models.poisson import Match, PoissonModel, hockey_regulation_to_moneyline
from .models.ratings import Game, PointsModel
from .selection import Candidate, Offer, evaluate, pick
from .sources import clubelo, eloratings, espn, football_data, hockeyarchives, nhl, soccerstats, xg_external
from . import fetch, venues

VALIDATION = Path("data/validation.json")
M8_VALIDATION = Path("data/m8_validation.json")
UEFA_CLUB = {"ucl": "Champions League", "uel": "Europa League", "uecl": "Conference League"}
CLUB_HOME_ELO = 65.0      # Annahme, nicht kalibriert
CLUB_GOALS = 1.35         # Tore je Team bei gleicher Stärke (Annahme, Vereinsfußball)
# ESPN -> ClubElo, wo Name/Übersetzung abweicht (Prague/Praha, ø/æ, Kurzformen)
CLUBELO_ALIASES = {
    "Slavia Prague": "Slavia Praha", "Sparta Prague": "Sparta Praha",
    "Bodo/Glimt": "Bodø/Glimt", "Lillestrom": "Lillestrøm", "FC Nordsjælland": "Nordsjaelland",
    "Manchester City": "Man City", "Manchester United": "Man United",
    "Paris Saint-Germain": "Paris SG", "Shakhtar Donetsk": "Shakhtar", "AEK Athens": "AEK",
    "AZ Alkmaar": "AZ", "Hapoel Be'er": "Beer-Sheva", "Hapoel Beer Sheva": "Beer-Sheva",
    "Union St.-Gilloise": "St Gillis", "Olympiacos": "Olympiakos", "Stade Rennais": "Rennes",
    "OFI CRETE": "OFI", "AGF": "Aarhus", "Pafos": "Paphos", "F.C. København": "FC Kobenhavn",
    "FC Copenhagen": "FC Kobenhavn", "Heart of Midlothian": "Hearts",
    "Sint-Truidense": "St Truiden", "CSU Craiova": "Craiova", "Riga FC": "FK Riga",
    "Red Star Belgrade": "Crvena Zvezda", "Mjällby AIF": "Mjällby", "Sporting CP": "Sporting",
    "Bayern Munich": "Bayern München", "Internazionale": "Internazionale",
}
# ClubElo-Verband -> football-data-Liga (xG/xGA ab 2026/27)
XG_LEAGUES = {"England": "E0", "Spain": "SP1", "Italy": "I1", "France": "F1",
              "Germany": "D1", "Netherlands": "N1", "Portugal": "P1", "Belgium": "B1",
              "Turkey": "T1", "Scotland": "SC0", "Greece": "G1"}
# ClubElo -> football-data, wo der strenge Abgleich nicht greift
FD_ALIASES = {"Internazionale": "Inter", "Paris SG": "Paris SG", "Sporting": "Sp Lisbon", "Braga": "Sp Braga",
              "Atlético": "Ath Madrid", "St Gillis": "St. Gilloise", "Bayern München": "Bayern Munich",
              "Forest": "Nott'm Forest", "Sittard": "For Sittard", "Real Sociedad": "Sociedad"}
XG_SHRINK_GAMES = 10.0    # Pseudo-Spiele: bei n Spielen wirkt n/(n+10) der Differenz
XG_SHARE = 0.5            # Anteil der xG-minus-Tore-Differenz, der ins Elo geht (Annahme)
# Weicht das Modell stärker als das vom Referenzmarkt ab, fehlt ihm meist eine
# Information (QB, Kader, Trainer) – dann keine Freigabe, sondern Prüfung.
MAX_DIVERGENCE = 0.15
SOCCER_LEAGUES = {
    "bundesliga": ("Bundesliga", "D1"),
    "2bundesliga": ("2. Bundesliga", "D2"),
    "epl": ("Premier League", "E0"),
    "championship": ("Championship", "E1"),
    "laliga": ("La Liga", "SP1"),
    "seriea": ("Serie A", "I1"),
    "ligue1": ("Ligue 1", "F1"),
    "eredivisie": ("Eredivisie", "N1"),
    "primeira": ("Primeira Liga", "P1"),
    "belgium": ("Belgian Pro League", "B1"),
    "turkey": ("Süper Lig", "T1"),
    "scotland": ("Scottish Premiership", "SC0"),
    "greece": ("Super League Greece", "G1"),
    "austria": ("Admiral Bundesliga (AT)", None),
}


@dataclass
class Fixture:
    league: str
    sport: str
    game: espn.EspnGame
    probs: dict[str, float]                  # "home"/"draw"/"away" -> p_model
    detail: str                              # erwartete Tore/Punkte etc.
    context: list[str] = field(default_factory=list)
    ref_probs: dict[str, float] = field(default_factory=dict)
    flags: dict[str, list[str]] = field(default_factory=dict)  # Seite -> Vorbehalte
    estimate: bool = False
    offers: dict[str, list[Offer]] = field(default_factory=dict)  # nur ausführbare Preise
    market_quotes: dict[str, list[Offer]] = field(default_factory=dict)  # alle Preisquellen, inkl. Referenz
    model: str = ""                          # Modellkennung fürs Journal (Standard: sport)


@dataclass
class ScanResult:
    stand: str
    fixtures: list[Fixture]
    candidates: list[Candidate]
    picks: list[Candidate]
    issues: list[str]
    notes: list[str]


# ---------------------------------------------------------------- helpers
def _validation() -> dict:
    try:
        return json.loads(VALIDATION.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}



def _m8_validation() -> dict:
    try:
        return json.loads(M8_VALIDATION.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _m8_params(league: str) -> M8Params | None:
    row = _m8_validation().get(league) or {}
    if not row.get("validated"):
        return None
    try:
        return M8Params(**row["params"])
    except (KeyError, TypeError, ValueError):
        return None


def soccer_freeze(cands: list[Candidate], soccer_leagues: set[str], val: dict) -> int:
    """Fußball nur marktartspezifisch freigeben.

    1X2 kann durch M8 separat validiert werden. Totals/AH bleiben an der
    bisherigen Validierungsdatei hängen, bis dafür eigene OOS-Tests existieren.
    """
    n = 0
    m8 = _m8_validation()
    for c in cands:
        if c.league not in soccer_leagues:
            continue
        is_1x2 = c.market in ("home", "draw", "away")
        if is_1x2 and (m8.get(c.league) or {}).get("validated"):
            continue
        mtypes = ("1x2",) if is_1x2 else ("ou", "ah")
        if any((val.get(f"{c.league}:{m}") or {}).get("validated") for m in mtypes):
            continue
        c.flags = (c.flags or []) + ["Fußball-Freigaben ausgesetzt: kein positiver OOS-Nachweis "
                                     "für diese Liga/Marktart – nur Watchlist"]
        n += 1
    return n


def model_weight(league: str, mtype: str, val: dict | None = None) -> tuple[float, str]:
    """Modellgewicht aus dem Backtest: > 0 nur, wenn das Modell für Liga und
    Marktart nachweislich besser war als der Markt; sonst 0 mit Begründung."""
    v = (val if val is not None else _validation()).get(f"{league}:{mtype}")
    if not v:
        return 0.0, "Modell nicht validiert (kein Backtest mit historischen Quoten möglich)"
    if not v.get("validated"):
        return 0.0, (f"Modell nicht besser als der Markt (Backtest: {v['n']} Tipps, "
                     f"CLV {v['clv'] * 100:+.1f} %)")
    return float(v["w"]), f"Modell validiert (Backtest-CLV {v['clv'] * 100:+.1f} %, n={v['n']})"


def _form(matches: list, team: str, before: date, n: int = 5) -> str:
    """Letzte n Ergebnisse als S/U/N plus Tordifferenz."""
    rows = [m for m in matches if (m.home == team or m.away == team) and m.date < before]
    rows.sort(key=lambda m: m.date)
    rows = rows[-n:]
    out, gd = "", 0.0
    for m in rows:
        f, a = (m.home_goals, m.away_goals) if m.home == team else (m.away_goals, m.home_goals)
        gd += f - a
        out += "S" if f > a else ("U" if f == a else "N")
    return f"{out or '–'} ({gd:+.0f})"


def _xg_line(matches: list, team: str, before: date) -> tuple[str, dict[str, float] | None]:
    """xG, xGA und tatsächliche Tore/Gegentore je Spiel (nur Spiele mit xG)."""
    gf = ga = xf = xa = 0.0
    n = 0
    for m in matches:
        if m.date >= before or m.home_xg is None or m.away_xg is None:
            continue
        if m.home == team:
            gf, ga, xf, xa, n = gf + m.home_goals, ga + m.away_goals, xf + m.home_xg, xa + m.away_xg, n + 1
        elif m.away == team:
            gf, ga, xf, xa, n = gf + m.away_goals, ga + m.home_goals, xf + m.away_xg, xa + m.home_xg, n + 1
    if not n:
        return "", None
    st = {"n": n, "gf": gf / n, "ga": ga / n, "xg": xf / n, "xga": xa / n}
    return (f"{team}: xG {st['xg']:.2f}, xGA {st['xga']:.2f}, Tore {st['gf']:.2f}:"
            f"{st['ga']:.2f} je Spiel ({n} Sp.)"), st


def _rest_days(matches: list, team: str, kickoff: date) -> int | None:
    ds = [m.date for m in matches if (m.home == team or m.away == team) and m.date < kickoff]
    return (kickoff - max(ds)).days if ds else None


def _devig_ref(g: espn.EspnGame, three_way: bool) -> dict[str, float]:
    r = g.ref_line
    keys = ["home", "draw", "away"] if three_way else ["home", "away"]
    odds = [r.get("ml_" + k) for k in keys]
    if any(o is None or o <= 1 for o in odds):
        return {}
    return dict(zip(keys, pricing.devig(odds)))


# ---------------------------------------------------------------- Belastung
def _fatigue(sport: str, hist: list[tuple[Slot, float, float]], ups: list[Slot]
             ) -> tuple[Effects, list[tuple[TeamLoad, TeamLoad]]]:
    """hist: (Spiel, tatsächliche Marge, Modellmarge). Schätzt die Effekte von
    Ruhezeit/Reise/Zeitzone/Höhe/Klima auf die Residuen und liefert die
    Belastung der anstehenden Spiele (Spielplan inkl. Vorspielen)."""
    ld = fatigue.loads(sport, [h[0] for h in hist] + ups)
    xs = [fatigue.diff(*l) for l in ld[:len(hist)]]
    eff = Effects.fit(xs, [y - m for _, y, m in hist])
    return eff, ld[len(hist):]


def _points_fatigue(sport: str, model: PointsModel, games: list[Game], ups: list[espn.EspnGame]
                    ) -> tuple[Effects, list[tuple[TeamLoad, TeamLoad]]]:
    hist = []
    for g in games:
        try:
            ph, pa = model.expected_points(g.home, g.away, g.neutral)
        except KeyError:
            continue
        hist.append((Slot(g.date, g.home, g.away, g.neutral), g.home_pts - g.away_pts, ph - pa))
    return _fatigue(sport, hist, [_slot(sport, g.home.name, g.away.name, g.kickoff, g.neutral)
                                  for g in ups])


def _load_ctx(h: str, a: str, lh: TeamLoad, la: TeamLoad, adj: float, unit: str) -> str:
    return (f"Belastung {h}: {lh.text()} | {a}: {la.text()} → {adj:+.1f} {unit} Heim-Sicht")


def _slot(sport: str, home: str, away: str, kickoff: datetime, neutral: bool) -> Slot:
    v = None if neutral else venues.LEAGUES[sport].get(home)
    return Slot(fatigue.local_day(kickoff, v), home, away, neutral)


# ---------------------------------------------------------------- soccer
def _soccer_model(leagues: list[str], issues: list[str]) -> tuple[PoissonModel | None, list[Match]]:
    texts = []
    for lg in leagues:
        for yr in (2025, 2026):
            t, err = fetch.get(football_data.csv_url(lg, yr), cache_days=0 if yr == 2026 else 30)
            if t is None:
                issues.append(f"football-data {lg} {yr}: {err}")
            else:
                texts.append(t)
    ms: list[Match] = []
    for t in texts:
        ms += football_data.parse(t)[0]
    if not ms:
        return None, []
    m = PoissonModel.fit(ms, date.today(), half_life_days=180, xg_weight=0.5, shrink=3.0,
                         rho=-0.05)
    return m, ms


def _m8_history(code: str, issues: list[str]) -> list[Match]:
    ms: list[Match] = []
    for yr in (2025, 2026):
        t, err = fetch.get(football_data.csv_url(code, yr), cache_days=0 if yr == 2026 else 30)
        if t is None:
            issues.append(f"football-data {code} {yr} (M8): {err}")
            continue
        ms += football_data.parse(t, shots_as_xg=True)[0]
    return ms


def _calibrate_1x2(mk: dict[str, float], a: float) -> dict[str, float]:
    q = [max(mk[k], 1e-9) ** a for k in ("1", "X", "2")]
    z = sum(q)
    out = dict(mk)
    for k, v in zip(("1", "X", "2"), q):
        out[k] = v / z
    return out


def _aut_model(issues: list[str]) -> tuple[PoissonModel | None, list[Match]]:
    t, err = fetch.get(football_data.AUT_URL)
    if t is None:
        issues.append(f"football-data AUT: {err}")
        return None, []
    ms = football_data.parse_new_league(t, {"2025/2026", "2026/2027"})[0]
    if not ms:
        return None, []
    return PoissonModel.fit(ms, date.today(), half_life_days=180, xg_weight=0.0,
                            shrink=3.0, rho=-0.05), ms


def scan_soccer(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    out: list[Fixture] = []
    aut, aut_ms = _aut_model(issues)
    cache: dict[str, tuple[PoissonModel | None, list[Match]]] = {}
    m8_cache: dict[str, tuple[M8Model, list[Match], float] | None] = {}
    m8v = _m8_validation()
    for lg, (label, code) in SOCCER_LEAGUES.items():
        games, errs = espn.upcoming(lg, start, days)
        issues += errs
        games = [g for g in games if g.status == "STATUS_SCHEDULED"]
        if not games:
            notes.append(f"{label}: keine Spiele bis {start + timedelta(days=days):%d.%m.}")
            continue

        m8_row = m8v.get(lg) or {}
        params = _m8_params(lg) if code else None
        if params and code:
            if code not in m8_cache:
                hist = _m8_history(code, issues)
                try:
                    mm = M8Model.fit(hist, start, params)
                    m8_cache[code] = (mm, hist, float(m8_row.get("calib", 1.0)))
                    notes.append(f"{label}: M8 1X2 OOS-validiert und aktiv")
                except (ValueError, KeyError) as e:
                    issues.append(f"{label}: M8 konnte nicht geladen werden ({e})")
                    m8_cache[code] = None
            active_m8 = m8_cache.get(code)
        else:
            active_m8 = None

        if lg == "austria":
            model, ms = aut, aut_ms
        else:
            if code not in cache:
                cache[code] = _soccer_model([code], issues)
            model, ms = cache[code]
        if model is None:
            issues.append(f"{label}: kein Modell (Daten fehlen)")
            continue

        # Externes echtes xG: Understat (Top-5) oder FootyStats (breite Ligaabdeckung).
        # Noch kein automatischer Fair-Odds-Eingriff, bis ligaweise OOS validiert.
        xg_code = "AUT" if lg == "austria" else code
        ext_xg = []
        ext_xg_err = None
        ss_ctx = None
        ss_err = None
        if xg_code:
            try:
                xg_now = datetime.now(timezone.utc)
                ext_xg, ext_xg_err = xg_external.snapshot(xg_code, xg_now)
                if ext_xg:
                    xg_external.persist_snapshot(xg_code, ext_xg, xg_now)
            except Exception as e:
                ext_xg_err = f"{type(e).__name__}: {e}"
        if ext_xg_err:
            notes.append(f"{label}: externes xG nicht verfügbar ({ext_xg_err})")
        try:
            ss_ctx, ss_err = soccerstats.league_context(xg_code)
        except Exception as e:
            ss_err = f"{type(e).__name__}: {e}"
        if ss_err:
            notes.append(f"{label}: SoccerSTATS-Kontext nicht verfügbar ({ss_err})")

        teams = list(active_m8[0].poisson.attack) if active_m8 else list(model.attack)
        for g in games:
            h = matching.find(g.home.name, teams) or matching.find(g.home.short, teams)
            a = matching.find(g.away.name, teams) or matching.find(g.away.short, teams)
            if not h or not a:
                issues.append(f"{label}: Team nicht zugeordnet ({g.title})")
                continue
            kd = g.kickoff.date()
            if active_m8:
                mm, m8_ms, calib = active_m8
                mk = _calibrate_1x2(mm.markets(h, a, kickoff=kd, neutral=g.neutral), calib)
                use_ms = m8_ms
                model_name = "m8"
                xg_note = "M8: Poisson/xG + Elo + Form + Rest, OOS-validiert"
            else:
                mk = model.markets(h, a, neutral=g.neutral)
                use_ms = ms
                model_name = "poisson-baseline"
                xg_note = "Tore+xG 50/50" if lg != "austria" else "nur Tore (keine xG-Quelle für AT)"
            ctx = [f"Form {h} {_form(use_ms, h, kd)}, {a} {_form(use_ms, a, kd)}",
                   f"Pause {_rest_days(use_ms, h, kd)}/{_rest_days(use_ms, a, kd)} Tage"]
            ctx += [x for x in (_xg_line(use_ms, h, kd)[0], _xg_line(use_ms, a, kd)[0]) if x]

            if ext_xg:
                names = [r.team for r in ext_xg]
                eh = matching.find(g.home.name, names) or matching.find(h, names)
                ea = matching.find(g.away.name, names) or matching.find(a, names)
                by_name = {r.team: r for r in ext_xg}
                if eh and ea:
                    xh, xa = by_name[eh], by_name[ea]
                    hs = xh.xg_home if xh.xg_home is not None else xh.xg
                    hga = xh.xga_home if xh.xga_home is not None else xh.xga
                    aas = xa.xg_away if xa.xg_away is not None else xa.xg
                    aga = xa.xga_away if xa.xga_away is not None else xa.xga
                    src = xh.source if xh.source == xa.source else f"{xh.source}/{xa.source}"
                    ctx.append(
                        f"Externes xG ({src}): {h} {hs:.2f}/{hga:.2f} xG/xGA Heim | "
                        f"{a} {aas:.2f}/{aga:.2f} xG/xGA Auswärts"
                    )

            if ss_ctx:
                bits = []
                if ss_ctx.goals_per_match is not None:
                    bits.append(f"{ss_ctx.goals_per_match:.2f} Tore/Spiel")
                if ss_ctx.over25_pct is not None:
                    bits.append(f"O2.5 {ss_ctx.over25_pct*100:.0f}%")
                if ss_ctx.btts_pct is not None:
                    bits.append(f"BTTS {ss_ctx.btts_pct*100:.0f}%")
                if ss_ctx.home_win_pct is not None and ss_ctx.away_win_pct is not None:
                    bits.append(
                        f"H/A {ss_ctx.home_win_pct*100:.0f}/{ss_ctx.away_win_pct*100:.0f}%"
                    )
                if bits:
                    ctx.append("SoccerSTATS Liga: " + " | ".join(bits))
            fx = Fixture(lg, "soccer", g, {"home": mk["1"], "draw": mk["X"], "away": mk["2"]},
                         f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f} ({xg_note}), "
                         f"O2.5 {mk['O2.5'] * 100:.0f} %", ctx,
                         ref_probs=_devig_ref(g, three_way=True),
                         estimate=lg == "austria", model=model_name)
            out.append(fx)
    return out


# ---------------------------------------------------------------- UEFA
def _nations_model(start: date, issues: list[str]
                   ) -> tuple[EloGoals | None, list[eloratings.EloResult]]:
    res: list[eloratings.EloResult] = []
    for y in range(start.year - 4, start.year + 1):
        t, err = fetch.get(eloratings.results_url(y), cache_days=0 if y == start.year else 30)
        if t is None:
            issues.append(f"eloratings {y}: {err}")
            continue
        res += eloratings.parse_results(t)
    rows = [(r.elo_home - r.elo_away, r.home_edge, r.home_goals, r.away_goals) for r in res]
    try:
        return EloGoals.fit(rows, home=100.0), res
    except ValueError as e:
        issues.append(f"Elo-Kalibrierung: {e}")
        return None, res


def _upcoming_scheduled(lg: str, start: date, days: int, issues: list[str]) -> list[espn.EspnGame]:
    games, errs = espn.upcoming(lg, start, days)
    issues += errs
    return [g for g in games if g.status == "STATUS_SCHEDULED"]


def scan_nations(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    """UEFA Nations League: World-Football-Elo (eloratings.net), Tor-Kalibrierung
    auf allen Länderspielen der letzten fünf Jahre."""
    games = _upcoming_scheduled("nations", start, days, issues)
    if not games:
        notes.append(f"UEFA Nations League: keine offenen Spiele bis "
                     f"{start + timedelta(days=days):%d.%m.}")
        return []
    rt, err = fetch.get(eloratings.RATINGS_URL)
    tt, err2 = fetch.get(eloratings.TEAMS_URL, cache_days=30)
    if rt is None or tt is None:
        issues.append(f"eloratings: {err or err2}")
        return []
    elo, teams = eloratings.parse_ratings(rt), eloratings.parse_teams(tt)
    model, res = _nations_model(start, issues)
    if model is None:
        return []
    notes.append(f"UEFA Nations League: Elo-Tormodell aus {len(res)} Länderspielen "
                 f"(eloratings.net), Heimvorteil {model.home:.0f} Elo, "
                 f"Tore bei Gleichstand {math.exp(model.a):.2f} je Team, Steigung {model.b:.2f}")
    ms = [Match(r.date, r.home, r.away, r.home_goals, r.away_goals) for r in res]
    out = []
    for g in games:
        h, a = eloratings.code_for(g.home.name, teams), eloratings.code_for(g.away.name, teams)
        if not h or not a or h not in elo or a not in elo:
            issues.append(f"Nations League: Team nicht zugeordnet ({g.title})")
            continue
        mk = model.markets(elo[h], elo[a], neutral=g.neutral)
        kd = g.kickoff.date()
        ctx = [f"Elo {g.home.name} {elo[h]:.0f}, {g.away.name} {elo[a]:.0f}"
               + (" (neutraler Ort)" if g.neutral else f" (+{model.home:.0f} Heim)"),
               f"Form {h} {_form(ms, h, kd)}, {a} {_form(ms, a, kd)}",
               f"Pause {_rest_days(ms, h, kd)}/{_rest_days(ms, a, kd)} Tage"]
        fx = Fixture("nations", "soccer", g, {"home": mk["1"], "draw": mk["X"], "away": mk["2"]},
                     f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f} (Elo-Modell), "
                     f"O2.5 {mk['O2.5'] * 100:.0f} %", ctx,
                     ref_probs=_devig_ref(g, three_way=True), model="elo-national")
        out.append(fx)
    return out


def scan_club_cups(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    """Champions/Europa/Conference League: ClubElo, Tor-Steigung aus dem
    Länderspielmodell, Heimvorteil und Torniveau als Annahme (Schätzung)."""
    games = {lg: _upcoming_scheduled(lg, start, days, issues) for lg in UEFA_CLUB}
    if not any(games.values()):
        notes.append("UEFA-Vereinswettbewerbe: keine Spiele bis "
                     f"{start + timedelta(days=days):%d.%m.} (nächster Spieltag später)")
        return []
    elo, errs = clubelo.ratings()
    issues += errs[:3]
    if not elo:
        issues.append("UEFA-Vereinswettbewerbe: keine ClubElo-Werte – nicht bewertet")
        return []
    nat, _ = _nations_model(start, issues)
    model = EloGoals(a=math.log(CLUB_GOALS), b=nat.b if nat else 0.7, home=CLUB_HOME_ELO)
    elo_per_goal = 400 / (2 * CLUB_GOALS * model.b)
    xg_ms: dict[str, list[Match]] = {}
    for fed, lg_code in XG_LEAGUES.items():
        t, err = fetch.get(football_data.csv_url(lg_code, start.year if start.month >= 7
                                                  else start.year - 1))
        if t is None:
            issues.append(f"football-data {lg_code} (xG): {err}")
            continue
        xg_ms[fed] = football_data.parse(t)[0]
    notes.append(f"UEFA-Vereinswettbewerbe: ClubElo ({len(elo)} Vereine), Heimvorteil "
                 f"{CLUB_HOME_ELO:.0f} Elo und {CLUB_GOALS:.2f} Tore je Team angenommen – Schätzung. "
                 f"xG-Korrektur: {XG_SHARE:.0%} von (xG-Diff. − Tordiff.) je Spiel × "
                 f"{elo_per_goal:.0f} Elo/Tor × n/(n+{XG_SHRINK_GAMES:.0f}), Ligen: "
                 f"{', '.join(sorted(xg_ms))}")
    names = list(elo)

    def rating(club: str, espn_name: str, kd: date) -> tuple[float, str]:
        e, fed = elo[club]
        ms = xg_ms.get(fed)
        if not ms:
            return e, f"{club} {e:.0f} ({fed}, keine xG-Quelle)"
        teams = sorted({m.home for m in ms} | {m.away for m in ms})
        fd = (matching.find_strict(club, teams, FD_ALIASES)
              or matching.find_strict(espn_name, teams, FD_ALIASES))
        line, st = _xg_line(ms, fd, kd) if fd else ("", None)
        if not st:
            return e, f"{club} {e:.0f} ({fed}, xG nicht zugeordnet)"
        luck = (st["xg"] - st["xga"]) - (st["gf"] - st["ga"])
        adj = XG_SHARE * luck * elo_per_goal * st["n"] / (st["n"] + XG_SHRINK_GAMES)
        return e + adj, f"{line} → ClubElo {e:.0f} {adj:+.0f} = {e + adj:.0f}"

    out = []
    for lg, gs in games.items():
        if not gs:
            continue
        for g in gs:
            h = (matching.find_strict(g.home.name, names, CLUBELO_ALIASES)
                 or matching.find_strict(g.home.short, names, CLUBELO_ALIASES))
            a = (matching.find_strict(g.away.name, names, CLUBELO_ALIASES)
                 or matching.find_strict(g.away.short, names, CLUBELO_ALIASES))
            if not h or not a:
                issues.append(f"{UEFA_CLUB[lg]}: Team nicht in ClubElo zugeordnet ({g.title})")
                continue
            kd = g.kickoff.date()
            (eh, ch), (ea, ca) = rating(h, g.home.name, kd), rating(a, g.away.name, kd)
            mk = model.markets(eh, ea, neutral=g.neutral)
            fx = Fixture(lg, "soccer", g, {"home": mk["1"], "draw": mk["X"], "away": mk["2"]},
                         f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f} "
                         f"(ClubElo, xG-korrigiert), O2.5 {mk['O2.5'] * 100:.0f} %", [ch, ca],
                         ref_probs=_devig_ref(g, three_way=True), estimate=True,
                         model="elo-club")
            out.append(fx)
    return out


def scan_uefa(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    return (scan_nations(start, days, issues, notes)
            + scan_club_cups(start, days, issues, notes))


# ---------------------------------------------------------------- NFL
def _nfl_games(season_now: int, issues: list[str]) -> list[Game]:
    raw: list[espn.EspnGame] = []
    for wk in range(1, 19):
        g, err = espn.nfl_week(season_now - 1, wk, 2, cache_days=30)
        if err:
            issues.append(err)
        raw += g
    for wk in range(1, 6):
        g, _ = espn.nfl_week(season_now - 1, wk, 3, cache_days=30)
        raw += g
    for wk in range(1, 19):
        g, err = espn.nfl_week(season_now, wk, 2)
        if err:
            issues.append(err)
        if g and not any(x.final for x in g):
            break
        raw += g
    seen, games = set(), []
    for g in raw:
        if g.final and g.id not in seen and g.home_score is not None:
            seen.add(g.id)
            day = fatigue.local_day(g.kickoff, None if g.neutral else venues.NFL.get(g.home.name))
            games.append(Game(day, g.home.name, g.away.name,
                              g.home_score, g.away_score, g.neutral))
    return games


def scan_nfl(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    games = _nfl_games(start.year, issues)
    if len(games) < 100:
        issues.append(f"NFL: nur {len(games)} Spiele geladen – kein Modell")
        return []
    model = PointsModel.fit(games, start, half_life_days=120, ridge=3.0)
    notes.append(f"NFL-Modell: {len(games)} Spiele, Heimvorteil {model.home_adv:.1f} Pkt, "
                 f"σ Marge {model.sigma_margin:.1f}")
    ups, errs = espn.upcoming("nfl", start, days)
    issues += errs
    as_ms = [Match(g.date, g.home, g.away, g.home_pts, g.away_pts) for g in games]
    eff, loads = _points_fatigue("nfl", model, games, ups)
    notes.append(f"NFL-Belastung (Punkte je Einheit): {eff.text('Pkt')}")
    out = []
    for g, (lh, la) in zip(ups, loads):
        if g.status != "STATUS_SCHEDULED":
            continue
        adj = eff.margin_adj(lh, la)
        try:
            mk = model.markets(g.home.name, g.away.name, neutral=g.neutral,
                               home_adj=adj / 2, away_adj=-adj / 2)
        except KeyError as e:
            issues.append(f"NFL: {e}")
            continue
        kd = g.kickoff.date()
        ctx = [f"Form {g.home.abbr} {_form(as_ms, g.home.name, kd)}, "
               f"{g.away.abbr} {_form(as_ms, g.away.name, kd)}",
               f"Pause {_rest_days(as_ms, g.home.name, kd)}/{_rest_days(as_ms, g.away.name, kd)} Tage"]
        ctx.append(_load_ctx(g.home.abbr, g.away.abbr, lh, la, adj, "Pkt"))
        if g.ref_line.get("details"):
            ctx.append(f"DK-Linie {g.ref_line['details']}, O/U {g.ref_line.get('total')}")
        flags: dict[str, list[str]] = {}
        inj, ierr = espn.injuries("nfl", g.id)
        if ierr:
            issues.append(f"NFL-Verletzungen {g.title}: {ierr}")
        for side, t in (("home", g.home), ("away", g.away)):
            qbs = [f"{n} ({s})" for n, pos, s in inj.get(t.name, [])
                   if pos == "QB" and s in ("Out", "Doubtful", "Injured Reserve")]
            if qbs:
                ctx.append(f"QB-Ausfall {t.abbr}: {', '.join(qbs)}")
                flags.setdefault(side, []).append(f"QB {', '.join(qbs)} – im Punktemodell nicht enthalten")
        fx = Fixture("nfl", "nfl", g, {"home": mk["ML1"], "away": mk["ML2"]},
                     f"erw. Punkte {mk['pts_home']:.1f}:{mk['pts_away']:.1f} "
                     f"(Marge {mk['margin']:+.1f}, Total {mk['total']:.1f})", ctx,
                     ref_probs=_devig_ref(g, three_way=False), flags=flags)
        out.append(fx)
    return out


# ---------------------------------------------------------------- NHL
def scan_nhl(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    prev = f"{start.year - 1}{start.year}" if start.month >= 7 else f"{start.year - 2}{start.year - 1}"
    cur = f"{int(prev[:4]) + 1}{int(prev[4:]) + 1}"
    ms, names, errs = nhl.season_games(prev, cache_days=30)
    issues += errs[:3]
    ms_cur, names_cur, _ = nhl.season_games(cur)
    names.update(names_cur)
    ms += ms_cur
    if len(ms) < 300:
        issues.append(f"NHL: nur {len(ms)} Spiele geladen – kein Modell")
        return []
    # Offseason: starke Regression (shrink 10 Pseudo-Spiele), lange Halbwertszeit
    model = PoissonModel.fit(ms, start, half_life_days=365, xg_weight=0.0, shrink=10.0, rho=0.0)
    stats, serr = nhl.team_stats(prev, cache_days=7)
    issues += serr
    notes.append(f"NHL-Modell: {len(ms)} Spiele ({len(ms_cur)} aus {cur}), "
                 f"Vorsaison stark regressiert – Kaderwechsel nicht modelliert")
    ups, errs = espn.upcoming("nhl", start, days)
    issues += errs
    abbr_by_name = {v: k for k, v in names.items()}

    def abbr(name: str) -> str:
        return abbr_by_name.get(matching.find(name, list(abbr_by_name)) or "", "")
    pairs = [(g, abbr(g.home.name), abbr(g.away.name)) for g in ups]
    pairs = [(g, h, a) for g, h, a in pairs if h and a]
    hist = []
    for m in ms:
        if m.home in model.attack and m.away in model.attack:
            lh, la = model.expected_goals(m.home, m.away)
            hist.append((Slot(m.date, m.home, m.away), m.home_goals - m.away_goals, lh - la))
    eff, loads = _fatigue("nhl", hist, [_slot("nhl", h, a, g.kickoff, g.neutral)
                                        for g, h, a in pairs])
    notes.append(f"NHL-Belastung (Tore je Einheit): {eff.text('Tore')}")
    load_by_id = {g.id: l for (g, _, _), l in zip(pairs, loads)}
    out = []
    for g in ups:
        if g.status != "STATUS_SCHEDULED":
            continue
        h, a = abbr(g.home.name), abbr(g.away.name)
        if not h or not a or h not in model.attack or a not in model.attack:
            issues.append(f"NHL: Team nicht zugeordnet ({g.title})")
            continue
        lh, la = model.expected_goals(h, a)
        l_h, l_a = load_by_id[g.id]
        adj = eff.margin_adj(l_h, l_a)
        # Margenkorrektur je zur Hälfte auf beide Torerwartungen (log-Skala)
        mk = model.markets(h, a, home_adj=math.log(max(lh + adj / 2, 0.2) / lh),
                           away_adj=math.log(max(la - adj / 2, 0.2) / la))
        ph, pa = hockey_regulation_to_moneyline(mk["1"], mk["X"], mk["2"])
        ctx = []
        for t, ab in ((g.home.name, h), (g.away.name, a)):
            st = stats.get(matching.find(t, list(stats)) or "")
            if st:
                ctx.append(f"{ab} Vorsaison: 5v5-GF% {st.gf_pct_5v5 * 100:.0f} %, "
                           f"PP {st.pp_pct * 100:.0f} %, PK {st.pk_pct * 100:.0f} %")
        ctx.append(_load_ctx(h, a, l_h, l_a, adj, "Tore"))
        fx = Fixture("nhl", "nhl", g, {"home": ph, "away": pa},
                     f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f}, "
                     f"60-Min-Remis {mk['X'] * 100:.0f} % (OT-Aufteilung geschätzt)", ctx,
                     ref_probs=_devig_ref(g, three_way=False), estimate=True)
        out.append(fx)
    return out


# ---------------------------------------------------------------- Eishockey Europa
# Team-Aliasse der historischen Ergebnisquellen
HOCKEY_ALIASES = {
    "del": {"Adler Mannheim": "Mannheim", "Augsburger Panther": "Augsbourg",
            "ERC Ingolstadt": "Ingolstadt", "Eisbären Berlin": "Berlin",
            "Fischtown Pinguins": "Bremerhaven", "Grizzlys Wolfsburg": "Wolfsburg",
            "Iserlohn Roosters": "Iserlohn", "Kolner Haie": "Cologne", "Krefeld Pinguine": "Krefeld",
            "Lowen Frankfurt": "Francfort", "Nuremberg Ice Tigers": "Nuremberg",
            "Red Bull Munich": "Munich", "Schwenninger Wild Wings": "Schwenningen",
            "Straubing Tigers": "Straubing", "Dresdner Eislöwen": "Dresde"},
    "nl": {"EHC Biel": "Bienne", "EHC Kloten": "Kloten", "EV Zug": "Zoug",
           "Fribourg Gottéron": "Fribourg", "Genève Servette": "Genève-Servette", "HC Ajoie": "Ajoie",
           "HC Ambri-Piotta": "Ambrì-Piotta", "HC Davos": "Davos", "HC Lausanne": "Lausanne",
           "HC Lugano": "Lugano", "SC Bern": "Berne", "SC Langnau Tigers": "Langnau",
           "SC Rapperswil-Jona Lakers": "Rapperswil", "ZSC Lions": "ZSC Lions"},
    "shl": {"Brynas IF": "Brynäs", "Djurgardens IF": "Djurgården", "Frolunda HC": "Frölunda",
            "Färjestad": "Färjestad", "HC Orebro": "Örebro", "HV71": "HV 71",
            "IF Bjorkloven": "Björklöven", "Linkoping HC": "Linköping", "Lulea Hockey": "Luleå",
            "Malmo Redhawks": "Malmö", "Rogle BK": "Rögle", "Skellefteå": "Skellefteå",
            "Timra IK": "Timrå", "Växjö Lakers": "Växjö", "Leksands IF": "Leksand",
            "Djurgårdens IF": "Djurgården", "HV71": "HV 71", "Brynäs IF": "Brynäs",
            "Skellefteå AIK": "Skellefteå"},
    "liiga": {"HPK Hameenlinna": "HPK Hämeenlinna", "JYP Jyvaskyla": "JYP Jyväskylä",
              "Lahti Pelicans": "Pelicans Lahti", "Mikkelin Jukurit": "Jukurit Mikkeli",
              "Oulun Karpat": "Kärpät Oulu", "Porin Assat": "Ässät Pori",
              "Tampereen Ilves": "Ilves Tampere", "Vaasan Sport": "Sport Vaasa",
              # Liiga-API-Kurznamen
              "HIFK": "HIFK Helsinki", "HPK": "HPK Hämeenlinna", "Ilves": "Ilves Tampere",
              "JYP": "JYP Jyväskylä", "Jokerit": "Jokerit Helsinki", "Jukurit": "Jukurit Mikkeli",
              "K-Espoo": "Kiekko-Espoo", "KalPa": "KalPa Kuopio", "KooKoo": "KooKoo Kouvola",
              "Kärpät": "Kärpät Oulu", "Lukko": "Lukko Rauma", "Pelicans": "Pelicans Lahti",
              "SaiPa": "SaiPa Lappeenranta", "Sport": "Sport Vaasa", "TPS": "TPS Turku",
              "Tappara": "Tappara Tampere", "Ässät": "Ässät Pori"},
    "khl": {"Avtomobilist Yekaterinburg": "Avtomobilist Ekaterinburg", "CSKA Moscow": "CSKA Moscou",
            "HC Barys": "Barys Astana", "HC Dynamo Moscow": "Dynamo Moscou", "HC Sochi": "HK Sotchi",
            "HK Avangard Omsk": "Avangard Omsk", "Kunlun Red Star": "Shanghai Dragons",
            "Neftekhimik Nizhnekamsk": "Neftekhimik Nijnekamsk",
            "SKA St. Petersburg": "SKA Saint-Pétersbourg", "Salavat Yulaev UFA": "Salavat Yulaev Ufa",
            "Spartak Moscow": "Spartak Moscou", "Torpedo Nizhny Novgorod": "Torpedo Nijni Novgorod"},
}
# Schreibvarianten innerhalb von hockeyarchives vereinheitlichen
HA_CANON = {"Rapperswil-Jona": "Rapperswil", "Bietigheim-Bissingen": "Bietigheim"}


def _hockey_results(lg: str, season_start: int, issues: list[str]
                    ) -> tuple[list[Match], int]:
    """Vorsaison + laufende Saison als 60-Minuten-Ergebnisse; Anzahl aktueller
    Spiele. Fehlt die laufende Saison bei hockeyarchives, kommen Liiga/SHL aus
    den offiziellen APIs; deren Namen werden auf hockeyarchives abgebildet."""
    al = HOCKEY_ALIASES.get(lg, {})
    prev, err = hockeyarchives.season_results(lg, season_start - 1, 30.0)
    if err:
        issues.append(f"hockeyarchives {lg} {season_start - 1}/{season_start}: {err}")
    cur, _ = hockeyarchives.season_results(lg, season_start, 0.5)
    known = sorted({HA_CANON.get(n, n) for r in prev + cur for n in (r.home, r.away)})

    def name(n: str, api: bool) -> str:
        n = HA_CANON.get(n, n)
        return (matching.find_strict(n, known, al) or n) if api else n
    api = False
    if not cur and lg in ("liiga", "shl"):
        cur, _, err2 = (hockeyarchives.liiga(season_start + 1) if lg == "liiga"
                        else hockeyarchives.shl(season_start))
        api = True
        if err2:
            issues.append(f"{lg}-API: {err2}")
    ms = [Match(r.date, name(r.home, False), name(r.away, False), r.reg_home, r.reg_away)
          for r in prev]
    ms += [Match(r.date, name(r.home, api), name(r.away, api), r.reg_home, r.reg_away) for r in cur]
    return ms, len(cur)


def scan_hockey_eu(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    now = datetime.now(timezone.utc)
    until = datetime.combine(start + timedelta(days=days + 1), datetime.min.time(), tzinfo=timezone.utc)
    issues.append("Eishockey Europa: DEL/CH/KHL-Spielplanquelle entfernt; Abdeckung unvollständig")
    out = _scan_icehl(start, until, now, issues, notes)
    season = start.year if start.month >= 7 else start.year - 1
    for lg in ("liiga", "shl"):
        _, upcoming, err = (hockeyarchives.liiga(season + 1) if lg == "liiga" else hockeyarchives.shl(season))
        if err:
            issues.append(f"{lg}: {err}")
            continue
        upcoming = [g for g in upcoming if now < g["start"] <= until]
        if not upcoming:
            continue
        ms, _ = _hockey_results(lg, season, issues)
        if len(ms) < 150:
            issues.append(f"{lg}: zu wenige Ergebnisse für ein Modell")
            continue
        model = PoissonModel.fit(ms, start, half_life_days=240, xg_weight=0.0, shrink=8.0, rho=0.0)
        for g in upcoming:
            h = matching.find_strict(g["home"], list(model.attack), HOCKEY_ALIASES.get(lg, {}))
            a = matching.find_strict(g["away"], list(model.attack), HOCKEY_ALIASES.get(lg, {}))
            if not h or not a:
                issues.append(f"{lg}: Team nicht zugeordnet ({g['home']} / {g['away']})")
                continue
            mk = model.markets(h, a)
            ph, pa = hockey_regulation_to_moneyline(mk["1"], mk["X"], mk["2"])
            game = espn.EspnGame(f"{lg}:{g['start'].isoformat()}:{h}:{a}", lg, g["start"],
                                 espn.Team(g["home"]), espn.Team(g["away"]), "STATUS_SCHEDULED")
            out.append(Fixture(lg, "hockey", game, {"home": ph, "away": pa},
                               f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f}",
                               estimate=True, model="poisson-hockey-eu"))
    return out


def _scan_icehl(start: date, until: datetime, now: datetime, issues: list[str],
                notes: list[str]) -> list[Fixture]:
    """ICE Hockey League: Spielplan und Ergebnisse aus dem ICEHL-Datenfeed.
    Nur faire Quoten im Bericht, solange kein Buchmacherpreis angebunden ist."""
    season_start = start.year if start.month >= 7 else start.year - 1
    prev, _, err = hockeyarchives.icehl(season_start - 1, cache_days=30)
    cur, up, err2 = hockeyarchives.icehl(season_start)
    if err or err2:
        issues.append(f"ICEHL-Feed: {err or err2}")
    ms = [Match(r.date, hockeyarchives.canonical_icehl(r.home), hockeyarchives.canonical_icehl(r.away),
                r.reg_home, r.reg_away) for r in prev + cur]
    if len(ms) < 150:
        issues.append(f"ICEHL: nur {len(ms)} Spiele geladen – kein Modell")
        return []
    model = PoissonModel.fit(ms, start, half_life_days=240, xg_weight=0.0, shrink=8.0, rho=0.0)
    notes.append(f"ICE Hockey League: Poisson aus {len(ms)} Spielen (ICEHL-Feed), davon "
                 f"{len(cur)} aktuelle Saison – Marktpreis wird separat über Preisquellen geprüft")
    out = []
    for u in sorted(up, key=lambda x: x["start"]):
        ko = u["start"].astimezone(timezone.utc)
        h = hockeyarchives.canonical_icehl(u["home"])
        a = hockeyarchives.canonical_icehl(u["away"])
        if not (now < ko <= until) or h not in model.attack or a not in model.attack:
            continue
        mk = model.markets(h, a)
        ph, pa = hockey_regulation_to_moneyline(mk["1"], mk["X"], mk["2"])
        g = espn.EspnGame(f"icehl-{ko:%Y%m%d%H%M}-{h}", "icehl", ko, espn.Team(u["home"]),
                          espn.Team(u["away"]), "STATUS_SCHEDULED")
        kd = ko.date()
        out.append(Fixture("icehl", "hockey", g, {"home": ph, "away": pa},
                           f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f}, 60-Min-Remis "
                           f"{mk['X'] * 100:.0f} % (OT-Aufteilung geschätzt)",
                           [f"Form {u['home']} {_form(ms, h, kd)}, "
                            f"{u['away']} {_form(ms, a, kd)} (60 Min.)"],
                           estimate=True, model="poisson-hockey-eu"))
    return out


# ---------------------------------------------------------------- NBA
def _nba_games(season: int, issues: list[str], cache_days: float) -> list[Game]:
    ids, err = espn.team_ids("nba")
    if err:
        issues.append(f"NBA-Teams: {err}")
    seen, games = set(), []
    for tid in ids:
        for st in (2, 3):
            gs, err = espn.team_schedule("nba", tid, season, st, cache_days=cache_days)
            if err and st == 2:
                issues.append(f"NBA-Spielplan {tid}/{season}: {err}")
            for g in gs:
                if g.final and g.id not in seen and g.home_score is not None:
                    seen.add(g.id)
                    v = None if g.neutral else venues.NBA.get(g.home.name)
                    games.append(Game(fatigue.local_day(g.kickoff, v), g.home.name, g.away.name,
                                      g.home_score, g.away_score, g.neutral))
    return games


def scan_nba(start: date, days: int, issues: list[str], notes: list[str]) -> list[Fixture]:
    cur = start.year + 1 if start.month >= 8 else start.year   # ESPN-Saisonjahr = Endjahr
    prev_games = _nba_games(cur - 1, issues, cache_days=30)
    cur_games = _nba_games(cur, issues, cache_days=0)
    games = prev_games + cur_games
    if len(games) < 500:
        issues.append(f"NBA: nur {len(games)} Spiele geladen – kein Modell")
        return []
    ups, errs = espn.upcoming("nba", start, days)
    issues += errs
    regular = [g for g in ups if g.season_type == 2]
    if not regular:
        first = "20.10." if not cur_games else "–"
        notes.append(f"NBA: keine Regular-Season-Spiele bis {start + timedelta(days=days):%d.%m.} "
                     f"(Preseason wird nicht bewertet; Saisonstart {first})")
        return []
    # Saisonbeginn: Vorsaison mit Halbwertszeit 90 Tage und Ridge 8 (Kaderwechsel)
    model = PointsModel.fit(games, start, half_life_days=90, ridge=8.0)
    n_cur: dict[str, int] = {}
    for g in cur_games:
        n_cur[g.home] = n_cur.get(g.home, 0) + 1
        n_cur[g.away] = n_cur.get(g.away, 0) + 1
    notes.append(f"NBA-Modell: {len(prev_games)} Vorsaison- + {len(cur_games)} aktuelle Spiele, "
                 f"Heimvorteil {model.home_adv:.1f} Pkt, σ Marge {model.sigma_margin:.1f}")
    eff, loads = _points_fatigue("nba", model, games, ups)
    notes.append(f"NBA-Belastung (Punkte je Einheit): {eff.text('Pkt')}")
    keys, kerr = espn.key_players("nba", cur - 1)
    issues += kerr[:2]
    as_ms = [Match(g.date, g.home, g.away, g.home_pts, g.away_pts) for g in cur_games]
    out = []
    for g, (lh, la) in zip(ups, loads):
        if g.status != "STATUS_SCHEDULED" or g.season_type != 2:
            continue
        adj = eff.margin_adj(lh, la)
        try:
            mk = model.markets(g.home.name, g.away.name, neutral=g.neutral,
                               home_adj=adj / 2, away_adj=-adj / 2)
        except KeyError as e:
            issues.append(f"NBA: {e}")
            continue
        kd = g.kickoff.date()
        ctx = [_load_ctx(g.home.abbr, g.away.abbr, lh, la, adj, "Pkt")]
        if as_ms:
            ctx.append(f"Form {g.home.abbr} {_form(as_ms, g.home.name, kd)}, "
                       f"{g.away.abbr} {_form(as_ms, g.away.name, kd)}")
        if g.ref_line.get("details"):
            ctx.append(f"DK-Linie {g.ref_line['details']}, O/U {g.ref_line.get('total')}")
        flags: dict[str, list[str]] = {}
        inj, ierr = espn.injuries("nba", g.id)
        if ierr:
            issues.append(f"NBA-Verletzungen {g.title}: {ierr}")
        for side, t in (("home", g.home), ("away", g.away)):
            lst = inj.get(t.name, [])
            out_keys = [f"{n} ({keys[n][1]:.0f} PPG, {s})" for n, _, s in lst
                        if n in keys and keys[n][1] >= 15 and s in ("Out", "Doubtful")]
            dtd = [n for n, _, s in lst if n in keys and keys[n][1] >= 15 and s == "Day-To-Day"]
            if out_keys:
                ctx.append(f"Ausfall Leistungsträger {t.abbr}: {', '.join(out_keys)}")
                flags.setdefault(side, []).append(
                    f"Leistungsträger {', '.join(out_keys)} fehlt – im Teamrating nicht abgezogen")
            if dtd:
                ctx.append(f"fraglich {t.abbr}: {', '.join(dtd)}")
        early = min(n_cur.get(g.home.name, 0), n_cur.get(g.away.name, 0)) < 10
        fx = Fixture("nba", "nba", g, {"home": mk["ML1"], "away": mk["ML2"]},
                     f"erw. Punkte {mk['pts_home']:.1f}:{mk['pts_away']:.1f} "
                     f"(Marge {mk['margin']:+.1f}, Total {mk['total']:.1f})"
                     + (", Saisonstart: Rating aus Vorsaison" if early else ""), ctx,
                     ref_probs=_devig_ref(g, three_way=False), flags=flags, estimate=early)
        out.append(fx)
    return out


# ---------------------------------------------------------------- Bewertung
def _label(fx: Fixture, side: str) -> str:
    g = fx.game
    if side == "draw":
        return "Unentschieden (90 Min.)"
    t = g.home.name if side == "home" else g.away.name
    return f"{t} Sieg" + (" (90 Min.)" if fx.sport == "soccer" else " (inkl. OT)")


def evaluate_fixture(fx: Fixture, val: dict | None = None) -> list[Candidate]:
    w, wnote = model_weight(fx.league, "1x2", val)
    out = []
    for side, offers in fx.offers.items():
        if side not in fx.probs:
            continue
        pm, pr = fx.probs[side], fx.ref_probs.get(side)
        pf = w * pm + (1 - w) * pr if pr is not None else pm
        flags = list(fx.flags.get(side, []))
        if pr is None:
            flags.append("keine unabhängige Marktreferenz")
        if w > 0 and pr is not None and abs(pm - pr) > MAX_DIVERGENCE:
            flags.append("Modell weicht stark vom Markt ab – Kader-/Newsprüfung nötig")
        reason = f"Unabhängige Referenz {pr}, Modell {pm:.3f} – {wnote}. {fx.detail}. " + "; ".join(fx.context)
        for offer in offers:
            out.append(evaluate(offer, pm, estimate=fx.estimate, reason=reason,
                                p_ref=pr, p_final=pf, flags=flags))
    return out


def run(start: date | None = None, days: int = 7, watch_days: int = 14,
        sports: tuple[str, ...] = ("soccer", "nfl", "nhl", "nba", "hockey_eu"),
        journal: Journal | None = None) -> ScanResult:
    start = start or date.today()
    now = datetime.now(timezone.utc)
    issues: list[str] = []
    notes: list[str] = []
    fixtures: list[Fixture] = []
    if "soccer" in sports:
        fixtures += scan_soccer(start, watch_days, issues, notes)
        fixtures += scan_uefa(start, watch_days, issues, notes)
    if "nfl" in sports:
        fixtures += scan_nfl(start, days, issues, notes)
    if "nhl" in sports:
        fixtures += scan_nhl(start, days, issues, notes)
    if "nba" in sports:
        fixtures += scan_nba(start, days, issues, notes)
    if "hockey_eu" in sports:
        fixtures += scan_hockey_eu(start, days, issues, notes)
    from .bookmaker import attach_prices
    attach_prices(fixtures, issues)
    notes.append("Preisregel: Modell-Fair immer gegen aktuelle Marktquote prüfen; ohne Marktpreis NO_PRICE und keine Freigabe.")
    notes.append("Quellen: API-Football, API-Hockey, Pinnacle/Bet365/Betfair sowie Polymarket/Kalshi als zusätzliche Marktquellen.")
    val = _validation()
    cands = [c for fx in fixtures for c in evaluate_fixture(fx, val)]
    soccer = {fx.league for fx in fixtures if fx.sport == "soccer"}
    if soccer_freeze(cands, soccer, val):
        notes.append("Fußball: Freigaben ausgesetzt, bis der Backtest die Liga validiert "
                     "(Bundesliga-1X2 bisher CLV −7,6 %, ROI −42 % bei 100 Tipps) – nur Watchlist")
    picks = pick(cands)
    stand = report.stand(now)
    if journal is not None:
        _log(journal, fixtures, picks)
        try:
            from . import sql_store
            sql_store.sync_scan(fixtures, picks)
        except Exception as exc:  # SQL darf Scan/Telegram nicht blockieren.
            issues.append(f"SQL-Tracking: {type(exc).__name__}: {exc}")
    return ScanResult(stand, fixtures, cands, picks, issues, notes)


def _log(j: Journal, fixtures: list[Fixture], picks: list[Candidate]) -> None:
    val = _validation()
    rows = []
    for fx in fixtures:
        ref = fx.ref_probs
        w = model_weight(fx.league, "1x2", val)[0]
        for side, p in fx.probs.items():
            pr = ref.get(side)
            pf = w * p + (1 - w) * pr if pr is not None else p
            rows.append({"league": fx.league, "event_id": fx.game.id, "event": fx.game.title,
                         "kickoff": fx.game.kickoff.isoformat(timespec="minutes"),
                         "market": side, "p_model": p, "p_ref": pr if pr is not None else "",
                         "p_final": pf, "fair_odds": 1 / pf, "estimate": fx.estimate,
                         "model": fx.model or fx.sport, "inputs": fx.detail})
    j.append("forecasts", rows)
    open_vb = {(r["event"], r["market"], r["source"]) for r in j.read("valuebets")
               if not r.get("result")}
    new = [c.as_row() for c in picks if (c.event, c.market, c.source) not in open_vb]
    j.append("valuebets", new)
