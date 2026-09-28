"""Vollständiger Scan: Daten laden -> Modelle fitten -> faire Preise ->
Kalshi-Vergleich -> max. 5 Value-Kandidaten -> Journal, Bericht, Telegram-Text.

Entscheidungswahrscheinlichkeit
-------------------------------
p_model ist die unabhängige Modellschätzung. Wo ein unabhängiger
Referenzmarkt vorliegt (DraftKings-Linie über ESPN, de-vigged), wird
p_final = w * p_model + (1 - w) * p_ref gebildet; w ist die angenommene
Modellzuverlässigkeit je Sport (MODEL_WEIGHT). Ohne Referenz dient der
de-vigged Kalshi-Mittelkurs als Referenz. So erzeugt Modellrauschen allein
keinen Kandidaten. Alle Gewichte sind Annahmen und im Bericht ausgewiesen.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import matching, pricing
from .journal import Journal
from .models.poisson import Match, PoissonModel, hockey_regulation_to_moneyline
from .models.ratings import Game, PointsModel
from .selection import Candidate, Offer, evaluate, pick
from .sources import espn, football_data, kalshi, nhl
from . import fetch

MODEL_WEIGHT = {"soccer": 0.5, "nfl": 0.25, "nhl": 0.25}
# Weicht das Modell stärker als das vom Referenzmarkt ab, fehlt ihm meist eine
# Information (QB, Kader, Trainer) – dann keine Freigabe, sondern Prüfung.
MAX_DIVERGENCE = 0.15
SOCCER_LEAGUES = {"bundesliga": "Bundesliga", "2bundesliga": "2. Bundesliga",
                  "austria": "Admiral Bundesliga (AT)"}


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
    kalshi: dict[str, kalshi.KalshiQuote] = field(default_factory=dict)


@dataclass
class ScanResult:
    stand: str
    fixtures: list[Fixture]
    candidates: list[Candidate]
    picks: list[Candidate]
    issues: list[str]
    notes: list[str]


# ---------------------------------------------------------------- helpers
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


def _devig_kalshi(qs: dict[str, kalshi.KalshiQuote], keys: list[str]) -> dict[str, float]:
    mids = []
    for k in keys:
        q = qs.get(k)
        if not q or q.yes_ask <= 0:
            return {}
        mids.append(q.mid if q.yes_bid > 0 else q.yes_ask)
    s = sum(mids)
    return {k: m / s for k, m in zip(keys, mids)} if s > 0 else {}


def _attach_kalshi(fx: Fixture, quotes: list[kalshi.KalshiQuote]) -> None:
    g = fx.game
    by_ev: dict[str, list[kalshi.KalshiQuote]] = {}
    for q in quotes:
        by_ev.setdefault(q.event_ticker, []).append(q)
    for qs in by_ev.values():
        found: dict[str, kalshi.KalshiQuote] = {}
        for q in qs:
            if q.outcome == "draw":
                found["draw"] = q
            elif matching.match_label(q.label, g.home.aliases()) or matching.same(q.label, g.home.name):
                found["home"] = q
            elif matching.match_label(q.label, g.away.aliases()) or matching.same(q.label, g.away.name):
                found["away"] = q
        if "home" in found and "away" in found:
            ko = qs[0].kickoff
            try:
                kt = datetime.fromisoformat(ko.replace("Z", "+00:00"))
                if abs((kt - g.kickoff).total_seconds()) > 40 * 3600:
                    continue
            except ValueError:
                pass
            fx.kalshi = found
            return


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
    ger, ger_ms = _soccer_model(["D1", "D2"], issues)
    aut, aut_ms = _aut_model(issues)
    kq: list[kalshi.KalshiQuote] = []
    for lg in ("bundesliga", "2bundesliga"):
        q, err = kalshi.fetch_series(kalshi.SERIES[lg])
        if err:
            issues.append(f"Kalshi {lg}: {err}")
        kq += q
    for lg, label in SOCCER_LEAGUES.items():
        games, errs = espn.upcoming(lg, start, days)
        issues += errs
        model, ms = (aut, aut_ms) if lg == "austria" else (ger, ger_ms)
        games = [g for g in games if g.status == "STATUS_SCHEDULED"]
        if not games:
            notes.append(f"{label}: keine Spiele bis {start + timedelta(days=days):%d.%m.}")
            continue
        if model is None:
            issues.append(f"{label}: kein Modell (Daten fehlen)")
            continue
        teams = list(model.attack)
        for g in games:
            h = matching.find(g.home.name, teams) or matching.find(g.home.short, teams)
            a = matching.find(g.away.name, teams) or matching.find(g.away.short, teams)
            if not h or not a:
                issues.append(f"{label}: Team nicht zugeordnet ({g.title})")
                continue
            mk = model.markets(h, a, neutral=g.neutral)
            kd = g.kickoff.date()
            ctx = [f"Form {h} {_form(ms, h, kd)}, {a} {_form(ms, a, kd)}",
                   f"Pause {_rest_days(ms, h, kd)}/{_rest_days(ms, a, kd)} Tage"]
            xg_note = "Tore+xG 50/50" if lg != "austria" else "nur Tore (keine xG-Quelle für AT)"
            fx = Fixture(lg, "soccer", g, {"home": mk["1"], "draw": mk["X"], "away": mk["2"]},
                         f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f} ({xg_note}), "
                         f"O2.5 {mk['O2.5'] * 100:.0f} %", ctx,
                         ref_probs=_devig_ref(g, three_way=True),
                         estimate=lg == "austria")
            _attach_kalshi(fx, kq)
            out.append(fx)
    return out


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
            games.append(Game(g.kickoff.date(), g.home.name, g.away.name,
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
    kq, err = kalshi.fetch_series(kalshi.SERIES["nfl"])
    if err:
        issues.append(f"Kalshi NFL: {err}")
    ups, errs = espn.upcoming("nfl", start, days)
    issues += errs
    as_ms = [Match(g.date, g.home, g.away, g.home_pts, g.away_pts) for g in games]
    out = []
    for g in ups:
        if g.status != "STATUS_SCHEDULED":
            continue
        try:
            mk = model.markets(g.home.name, g.away.name, neutral=g.neutral)
        except KeyError as e:
            issues.append(f"NFL: {e}")
            continue
        kd = g.kickoff.date()
        ctx = [f"Form {g.home.abbr} {_form(as_ms, g.home.name, kd)}, "
               f"{g.away.abbr} {_form(as_ms, g.away.name, kd)}",
               f"Pause {_rest_days(as_ms, g.home.name, kd)}/{_rest_days(as_ms, g.away.name, kd)} Tage"]
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
        _attach_kalshi(fx, kq)
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
    kq, err = kalshi.fetch_series(kalshi.SERIES["nhl"])
    if err:
        issues.append(f"Kalshi NHL: {err}")
    ups, errs = espn.upcoming("nhl", start, days)
    issues += errs
    abbr_by_name = {v: k for k, v in names.items()}
    out = []
    for g in ups:
        if g.status != "STATUS_SCHEDULED":
            continue
        h = abbr_by_name.get(matching.find(g.home.name, list(abbr_by_name)) or "")
        a = abbr_by_name.get(matching.find(g.away.name, list(abbr_by_name)) or "")
        if not h or not a or h not in model.attack or a not in model.attack:
            issues.append(f"NHL: Team nicht zugeordnet ({g.title})")
            continue
        mk = model.markets(h, a)
        ph, pa = hockey_regulation_to_moneyline(mk["1"], mk["X"], mk["2"])
        ctx = []
        for t, ab in ((g.home.name, h), (g.away.name, a)):
            st = stats.get(matching.find(t, list(stats)) or "")
            if st:
                ctx.append(f"{ab} Vorsaison: 5v5-GF% {st.gf_pct_5v5 * 100:.0f} %, "
                           f"PP {st.pp_pct * 100:.0f} %, PK {st.pk_pct * 100:.0f} %")
        fx = Fixture("nhl", "nhl", g, {"home": ph, "away": pa},
                     f"erw. Tore {mk['xg_home']:.2f}:{mk['xg_away']:.2f}, "
                     f"60-Min-Remis {mk['X'] * 100:.0f} % (OT-Aufteilung geschätzt)", ctx,
                     ref_probs=_devig_ref(g, three_way=False), estimate=True)
        _attach_kalshi(fx, kq)
        out.append(fx)
    return out


# ---------------------------------------------------------------- Bewertung
def _label(fx: Fixture, side: str) -> str:
    g = fx.game
    if side == "draw":
        return "Unentschieden (90 Min.)"
    t = g.home.name if side == "home" else g.away.name
    return f"{t} Sieg" + (" (90 Min.)" if fx.sport == "soccer" else " (inkl. OT)")


def evaluate_fixture(fx: Fixture, release_until: datetime) -> list[Candidate]:
    keys = list(fx.probs)
    ref = fx.ref_probs or _devig_kalshi(fx.kalshi, keys)
    ref_src = "DraftKings" if fx.ref_probs else ("Kalshi-Mitte" if ref else "")
    w = MODEL_WEIGHT.get(fx.sport, 0.5)
    out = []
    for side in keys:
        q = fx.kalshi.get(side)
        if not q or q.yes_ask <= 0 or q.yes_ask >= 0.99:
            continue
        p_model = fx.probs[side]
        p_ref = ref.get(side)
        p_final = w * p_model + (1 - w) * p_ref if p_ref is not None else p_model
        odds = pricing.kalshi_decimal_odds(q.yes_ask * 100, contracts=100)
        flags = list(fx.flags.get(side, []))
        if p_ref is not None and abs(p_model - p_ref) > MAX_DIVERGENCE:
            flags.append(f"Modell weicht {abs(p_model - p_ref) * 100:.0f} Pp vom Markt ab – "
                         "fehlende Kader-/QB-Info wahrscheinlicher als Value")
        if fx.game.kickoff > release_until:
            flags.append("Anstoß außerhalb des Freigabefensters – nur Watchlist")
        reason = (f"{fx.detail}. Modell {p_model * 100:.1f} %"
                  + (f", {ref_src} {p_ref * 100:.1f} %" if p_ref is not None else ", keine Referenz")
                  + f", Entscheidung {p_final * 100:.1f} % (Modellgewicht {w:.0%}). "
                  + "; ".join(fx.context))
        off = Offer(fx.game.title, fx.game.kickoff.isoformat(timespec="minutes"), side,
                    _label(fx, side), odds, "kalshi", q.observed_at,
                    liquidity=q.liquidity or None, ref=q.ticker, league=fx.league)
        out.append(evaluate(off, p_model, estimate=fx.estimate, reason=reason,
                            p_ref=p_ref, p_final=p_final, flags=flags))
    return out


def run(start: date | None = None, days: int = 7, watch_days: int = 14,
        sports: tuple[str, ...] = ("soccer", "nfl", "nhl"),
        journal: Journal | None = None) -> ScanResult:
    start = start or date.today()
    now = datetime.now(timezone.utc)
    issues: list[str] = []
    notes: list[str] = []
    fixtures: list[Fixture] = []
    if "soccer" in sports:
        fixtures += scan_soccer(start, watch_days, issues, notes)
        notes.append("UEFA-Wettbewerbe: nächster Spieltag außerhalb des Fensters bzw. "
                     "kein ligaübergreifendes Stärkemodell – kein Trade")
    if "nfl" in sports:
        fixtures += scan_nfl(start, days, issues, notes)
    if "nhl" in sports:
        fixtures += scan_nhl(start, days, issues, notes)
    notes.append("NBA: Regular Season startet erst am 20.10. – Preseason wird nicht bewertet")
    notes.append("Europ. Eishockey (DEL/ICEHL): keine offenen Kalshi-Märkte, keine "
                 "verifizierten Orbit/bet365-Preise – nicht bewertet")
    notes.append("Orbit/bet365: in dieser Umgebung nicht direkt abrufbar (bet365 HTTP 403); "
                 "nur Kalshi-Preise sind verifiziert")
    release_until = datetime.combine(start + timedelta(days=days + 1), datetime.min.time(),
                                     tzinfo=timezone.utc)
    cands = [c for fx in fixtures for c in evaluate_fixture(fx, release_until)]
    picks = pick(cands)
    stand = now.strftime("%d.%m.%Y %H:%M UTC")
    if journal is not None:
        _log(journal, fixtures, picks)
    snapshot(fixtures)
    return ScanResult(stand, fixtures, cands, picks, issues, notes)


def _log(j: Journal, fixtures: list[Fixture], picks: list[Candidate]) -> None:
    w = MODEL_WEIGHT
    rows = []
    for fx in fixtures:
        ref = fx.ref_probs or _devig_kalshi(fx.kalshi, list(fx.probs))
        for side, p in fx.probs.items():
            pr = ref.get(side)
            pf = w.get(fx.sport, 0.5) * p + (1 - w.get(fx.sport, 0.5)) * pr if pr is not None else p
            rows.append({"league": fx.league, "event_id": fx.game.id, "event": fx.game.title,
                         "kickoff": fx.game.kickoff.isoformat(timespec="minutes"),
                         "market": side, "p_model": p, "p_ref": pr if pr is not None else "",
                         "p_final": pf, "fair_odds": 1 / pf, "estimate": fx.estimate,
                         "model": fx.sport, "inputs": fx.detail})
    j.append("forecasts", rows)
    open_vb = {(r["event"], r["market"], r["source"]) for r in j.read("valuebets")
               if not r.get("result")}
    new = [c.as_row() for c in picks if (c.event, c.market, c.source) not in open_vb]
    j.append("valuebets", new)


def snapshot(fixtures: list[Fixture], root: str = "data/snapshots") -> None:
    """Kalshi-Preise je Lauf sichern – Basis für die Closing Line (CLV)."""
    Path(root).mkdir(parents=True, exist_ok=True)
    p = Path(root) / f"kalshi-{date.today():%Y-%m}.jsonl"
    with p.open("a", encoding="utf-8") as f:
        for fx in fixtures:
            for side, q in fx.kalshi.items():
                f.write(json.dumps({"ticker": q.ticker, "event_ticker": q.event_ticker,
                                    "side": side, "bid": q.yes_bid, "ask": q.yes_ask,
                                    "observed_at": q.observed_at,
                                    "kickoff": fx.game.kickoff.isoformat()}) + "\n")
