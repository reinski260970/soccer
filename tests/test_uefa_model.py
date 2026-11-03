import math
import random
from datetime import date, datetime, timedelta, timezone

import pytest

from oddswatch import uefa_model as U
from oddswatch.sources.xg_external import XGSnapshot


def _pois(rnd, lam):
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= L:
            return k
        k += 1


def _world(seed=3, n_matches=600, goals=1.40, home=50.0):
    rnd = random.Random(seed)
    feds = ["England", "Spain", "Austria", "Czech Republic"]
    clubs = {}
    for i in range(48):
        fed = feds[i % 4]
        name = f"Club{i:02d} {fed[:3]}"
        clubs[name] = U.Club(name, 1500 + rnd.gauss(0, 130) + (120 if fed in ("England", "Spain") else 0), fed, 1)
    truth = U.Calibration(goals, home, U.slope_for(goals), 0, "truth")
    names = list(clubs)
    rows = []
    for _ in range(n_matches):
        h, a = rnd.sample(names, 2)
        lh, la = truth.lambdas(clubs[h].elo, clubs[a].elo)
        rows.append((clubs[h].elo, clubs[a].elo, False, _pois(rnd, lh), _pois(rnd, la)))
    return clubs, rows


def test_slope_matches_clubelo_expectancy():
    b = U.slope_for(1.35)
    a = math.log(1.35)
    for d in (-1.0, -0.25, 0.25, 1.0):
        assert abs(U._we_model(a, b, d) - U._we_logistic(d)) < 0.02


def test_calibration_recovers_home_and_level():
    _, rows = _world(n_matches=1500)
    cal = U.fit_calibration(rows, "test")
    assert abs(cal.fit_goals - 1.40) < 0.08
    assert abs(cal.fit_home - 50) < 25
    # Schrumpfung Richtung Prior, aber Daten dominieren bei n=1500
    assert min(cal.fit_home, U.PRIOR_HOME) - 1 <= cal.home <= max(cal.fit_home, U.PRIOR_HOME) + 1


def test_calibration_falls_back_to_prior():
    cal = U.fit_calibration([], "test")
    assert cal.goals == U.PRIOR_GOALS and cal.home == U.PRIOR_HOME and "Prior" in cal.source


def test_xg_adjustment_direction_and_cap():
    cal = U.Calibration(1.35, 60, U.slope_for(1.35), 0, "x")
    clubs = {"A": U.Club("A", 1700, "England"), "B": U.Club("B", 1700, "England")}
    dom = {"A": {"n": 10, "resid": 0.6, "tempo_ratio": 1.2, "line": "A"},
           "B": {"n": 10, "resid": -5.0, "tempo_ratio": 0.8, "line": "B"}}
    adj = U.team_adjustments({"A", "B"}, clubs, dom, {}, cal)
    assert adj["A"].elo_adj > 0
    assert adj["B"].elo_adj == -U.XG_CAP
    assert adj["A"].tempo > 1 > adj["B"].tempo
    assert 1 - U.TEMPO_CAP <= adj["B"].tempo


def test_uefa_xg_residual_uses_elo_expectation():
    cal = U.Calibration(1.35, 60, U.slope_for(1.35), 0, "x")
    clubs = {"Strong": U.Club("Strong", 1900, "Spain"), "Weak": U.Club("Weak", 1500, "Austria")}
    f = U.UefaFixture(1, "ucl", datetime(2026, 10, 1, tzinfo=timezone.utc), "Strong", "Weak", 1, 2, "FT",
                      "League Stage - 2", 1, 0)
    # Starkes Team dominiert erwartungsgemäß: xG 2.6:0.4 -> Residuum klein
    r = U.uefa_xg_resid([f], {1: (2.6, 0.4)}, {1: "Strong", 2: "Weak"}, clubs, cal, 2026)
    exp = cal.expected_gd(400, 1)
    assert r["Strong"]["resid"] == pytest.approx(2.2 - exp)
    assert r["Weak"]["resid"] == pytest.approx(-(2.2 - exp))


def test_match_club_uses_federation_and_aliases():
    clubs = {"Rangers": U.Club("Rangers", 1650, "Scotland"),
             "QPR": U.Club("QPR", 1550, "England"),
             "Slavia Praha": U.Club("Slavia Praha", 1700, "Czech Republic"),
             "Paris SG": U.Club("Paris SG", 1950, "France")}
    al = U.API_ALIASES
    assert U.match_club("Rangers", "Scotland", clubs, al) == "Rangers"
    assert U.match_club("Slavia Praha", "Czech-Republic", clubs, al) == "Slavia Praha"
    assert U.match_club("Paris Saint Germain", "France", clubs, al) == "Paris SG"
    assert U.match_club("Unknown FC", "Spain", clubs, al) is None


def test_parse_statistics_xg_and_fixtures():
    stats = {"response": [
        {"team": {"id": 10}, "statistics": [{"type": "Ball Possession", "value": "55%"},
                                             {"type": "expected_goals", "value": "1.87"}]},
        {"team": {"id": 20}, "statistics": [{"type": "expected_goals", "value": "0.45"}]}]}
    assert U.parse_statistics_xg(stats) == {10: 1.87, 20: 0.45}
    fx = {"response": [{
        "fixture": {"id": 7, "date": "2026-10-21T19:00:00+00:00", "status": {"short": "AET"}},
        "league": {"round": "Final"},
        "teams": {"home": {"id": 10, "name": "A"}, "away": {"id": 20, "name": "B"}},
        "goals": {"home": 2, "away": 1}, "score": {"fulltime": {"home": 1, "away": 1}}}]}
    f = U.parse_fixtures(fx, "ucl")[0]
    assert (f.hg, f.ag) == (1, 1) and f.neutral and f.finished  # 90-Min.-Ergebnis zählt


def test_assess_value_and_divergence():
    probs = {"1": 0.55, "X": 0.25, "2": 0.20, "O2.5": 0.50, "U2.5": 0.50}
    books = {"Pinnacle": {"home": 1.95, "draw": 3.8, "away": 4.2, "O2.5": 2.0, "U2.5:no": 1.9},
             "Bet365": {"home": 2.05, "draw": 3.6, "away": 4.0, "O2.5": 1.95, "U2.5:no": 1.85}}
    res = {r["markt"]: r for r in U.assess(probs, books)}
    assert res["1"]["status"] == "VALUE"            # 0.55*2.05-1 = +12.75 %
    assert res["X"]["status"] == ""
    probs2 = dict(probs, **{"2": 0.45})
    res2 = {r["markt"]: r for r in U.assess(probs2, books)}
    assert res2["2"]["status"].startswith("PRÜFEN")  # Modell 45 % vs Pinnacle ~23 %


def _sim_world(seed=7):
    """48 Vereine in 4 Verbänden, je eine Liga; Liga- und Europapokalspiele
    2024–2026 aus einem bekannten Wahrheitsmodell."""
    clubs, _ = _world(n_matches=0)
    names = list(clubs)
    rnd = random.Random(seed)
    truth = U.Calibration(1.40, 50, U.slope_for(1.40), 0, "truth")
    now = datetime(2026, 10, 22, 6, 0, tzinfo=timezone.utc)
    tid = {n: i + 100 for i, n in enumerate(names)}
    feds = sorted({c.fed for c in clubs.values()})
    league_id = {f: 1000 + i for i, f in enumerate(feds)}
    k = [0]

    def fx(fid, ko, lid, h, a, rnd_label, country=""):
        st, hg, ag = "FT", None, None
        if ko >= now:
            st = "NS"
        else:
            lh, la = truth.lambdas(clubs[h].elo, clubs[a].elo)
            hg, ag = _pois(rnd, lh), _pois(rnd, la)
        return {"fixture": {"id": fid, "date": ko.isoformat(), "status": {"short": st}},
                "league": {"id": lid, "round": rnd_label, "country": country},
                "teams": {"home": {"id": tid[h], "name": h}, "away": {"id": tid[a], "name": a}},
                "goals": {"home": hg, "away": ag}, "score": {"fulltime": {"home": hg, "away": ag}}}

    cup = {}
    for season in (2024, 2025, 2026):
        out = []
        base = datetime(season, 9, 15, 19, tzinfo=timezone.utc)
        for lid in (2, 3, 848):
            for m in range(150):
                h, a = rnd.sample(names, 2)
                k[0] += 1
                label = "2nd Qualifying Round" if m < 20 else "League Stage - 1"
                out.append(fx(season * 100000 + k[0], base + timedelta(days=(m % 30) * 7 // 4), lid, h, a, label))
        cup[season] = out
    dom = {}
    for f, lid in league_id.items():
        teams = [n for n in names if clubs[n].fed == f]
        for season in (2024, 2025, 2026):
            out, day = [], datetime(season, 8, 1, 15, tzinfo=timezone.utc)
            for h in teams:
                for a in teams:
                    if h != a:
                        k[0] += 1
                        day += timedelta(days=2)
                        out.append(fx(9000000 + k[0], day, lid, h, a, "Regular Season", f))
            dom[(lid, season)] = out
    h, a = names[0], names[1]
    cup[2026].append(fx(999, now + timedelta(hours=13), 2, h, a, "League Stage - 3"))
    return clubs, names, tid, league_id, cup, dom, now


def _patch_sources(monkeypatch, clubs, names, tid, league_id, cup, dom, live=True):
    by_id = {f["fixture"]["id"]: f for s in cup.values() for f in s}
    calls = {"stats": 0}
    inv = {i: n for n, i in tid.items()}

    def fake_api(path, cache_days=0.0):
        if path.startswith("/fixtures?league="):
            lid = int(path.split("league=")[1].split("&")[0])
            season = int(path.split("season=")[1].split("&")[0])
            if lid in (2, 3, 848):
                return {"response": [f for f in cup.get(season, []) if f["league"]["id"] == lid]}, None
            return {"response": dom.get((lid, season), [])}, None
        if path.startswith("/fixtures/statistics"):
            calls["stats"] += 1
            f = by_id[int(path.split("=")[1])]
            return {"response": [
                {"team": {"id": f["teams"]["home"]["id"]},
                 "statistics": [{"type": "expected_goals", "value": f"{f['goals']['home'] + 0.3:.2f}"}]},
                {"team": {"id": f["teams"]["away"]["id"]},
                 "statistics": [{"type": "expected_goals", "value": f"{f['goals']['away'] + 0.1:.2f}"}]}]}, None
        if path.startswith("/teams?id="):
            n = inv[int(path.split("=")[1])]
            return {"response": [{"team": {"country": clubs[n].fed.replace(" ", "-")}}]}, None
        if path.startswith("/leagues?team="):
            n = inv[int(path.split("team=")[1].split("&")[0])]
            return {"response": [{"league": {"id": league_id[clubs[n].fed], "type": "League"}}]}, None
        return None, "unbekannt"

    def fake_xg(code, as_of):
        fed = next(f for f, c in U.FED_XG.items() if c == code)
        rows = [XGSnapshot(c, 1.5 + (v.elo - 1600) / 600, 1.3 - (v.elo - 1600) / 700, None, None, None, None,
                           9, "test") for c, v in clubs.items() if v.fed == fed]
        return rows, None if rows else "leer"

    def fake_odds(fid):
        return {"Pinnacle": {"home": 2.0, "draw": 3.5, "away": 3.9, "O2.5": 1.9, "U2.5:no": 1.95},
                "Bet365": {"home": 2.1, "draw": 3.4, "away": 3.8, "O2.5": 1.85, "U2.5:no": 1.95}}, None

    monkeypatch.setattr(U, "clubelo_full", (lambda: (clubs, [])) if live else (lambda: ({}, ["HTTP 403"])))
    monkeypatch.setattr(U, "_api", fake_api)
    monkeypatch.setattr(U.xg_external, "snapshot", fake_xg)
    monkeypatch.setattr(U.xg_external, "persist_snapshot", lambda *a, **k: None)
    monkeypatch.setattr(U.apifootball, "odds", fake_odds)
    return calls


def test_full_run_live_clubelo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    clubs, names, tid, league_id, cup, dom, now = _sim_world()
    calls = _patch_sources(monkeypatch, clubs, names, tid, league_id, cup, dom, live=True)
    md, preds = U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    text = md.read_text(encoding="utf-8")
    p = next(p for p in preds if p.fx.id == 999)
    assert abs(p.probs["1"] + p.probs["X"] + p.probs["2"] - 1) < 1e-6
    assert "ClubElo live (48 Teams" in text
    assert "Quali-/Play-off-Spiele ausgeschlossen" in text
    # Live-Werte sind der Anker und damit heute exakt die Elo-Werte
    assert p.elo_h - p.adj_h.elo_adj == pytest.approx(clubs[names[0]].elo, abs=0.06)
    assert calls["stats"] == 200
    U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    before = calls["stats"]
    U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    assert calls["stats"] == before
    assert (tmp_path / "data/journal/uefa_elo_anchor.json").exists()


def test_full_run_fallback_when_clubelo_blocked(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    clubs, names, tid, league_id, cup, dom, now = _sim_world()
    # Nur der alte Namens-Schnappschuss liegt vor (wie im Repo bis 24.10.)
    snap_day = (now - timedelta(days=10)).date().isoformat()
    U._save(U.SNAPSHOTS, {snap_day: {n: round(c.elo, 1) for n, c in clubs.items()}})
    _patch_sources(monkeypatch, clubs, names, tid, league_id, cup, dom, live=False)
    md, preds = U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    text = md.read_text(encoding="utf-8")
    assert "eigene Elo-Rechnung" in text and "48 Teams" in text
    assert "ClubElo heute nicht erreichbar" in text
    p = next(p for p in preds if p.fx.id == 999)
    # 10 Tage Fortschreibung: nahe am Ankerwert, aber nicht identisch erzwungen
    assert abs((p.elo_h - p.adj_h.elo_adj) - clubs[names[0]].elo) < 60
    assert U._load(U.ANCHOR, {})["date"] == snap_day


def test_engine_anchor_and_league_offset():
    from oddswatch import uefa_elo as E
    t0 = datetime(2025, 8, 1, tzinfo=timezone.utc)
    games, gid = [], 0
    rnd = random.Random(1)
    # Liga A (Teams 1-4) und Liga B (5-8): innerhalb gleich stark
    for lg, teams in (("L1", [1, 2, 3, 4]), ("L2", [5, 6, 7, 8])):
        for r in range(6):
            for h in teams:
                for a in teams:
                    if h != a:
                        gid += 1
                        games.append(E.EGame(gid, t0 + timedelta(days=gid % 300), h, a,
                                             rnd.randint(0, 2), rnd.randint(0, 2), False, lg))
    anchor = {1: 1800.0, 5: 1500.0}
    res = E.run_engine(games, anchor, date(2026, 6, 1))
    assert res.current[1] == 1800.0 and res.current[5] == 1500.0   # keine Spiele nach dem Anker
    # Ligakollegen werden mit der Liga verschoben – bei nur einem Ankerteam
    # je Liga bewusst zur Mitte geschrumpft (Ankerabstand 300 Elo)
    assert 50 < res.offsets["L1"] - res.offsets["L2"] < 300
    assert sum(res.current[t] for t in (2, 3, 4)) / 3 > sum(res.current[t] for t in (6, 7, 8)) / 3 + 50


def test_calibration_separates_home_fav_and_dog():
    rnd = random.Random(5)
    goals, b = 1.35, U.slope_for(1.35)
    rows = []
    for _ in range(4000):
        eh, ea = 1500 + rnd.gauss(0, 150), 1500 + rnd.gauss(0, 150)
        H = 90.0 if eh >= ea else 20.0
        d = (eh - ea + H) / 400
        lh, la = math.exp(math.log(goals) + b * d), math.exp(math.log(goals) - b * d)
        rows.append((eh, ea, False, _pois(rnd, lh), _pois(rnd, la)))
    cal = U.fit_calibration(rows, "test")
    assert cal.fit_home - cal.fit_home_dog > 35
    assert abs(cal.fit_mult - 1.0) < 0.15
    assert cal.home_for(10) == cal.home and cal.home_for(-10) == cal.home_dog


def test_main_round_filter():
    assert U.is_main_round("League Stage - 4")
    assert U.is_main_round("Knockout Round Play-offs")
    assert U.is_main_round("Round of 16") and U.is_main_round("Final")
    assert not U.is_main_round("3rd Qualifying Round")
    assert not U.is_main_round("Play-offs")
    assert not U.is_main_round("Preliminary Round")


def test_competition_goal_factor_shrinks_toward_one():
    rows = [(1700.0, 1700.0, False, 3, 2, "ucl") for _ in range(40)]
    cal = U.calibrate(rows, "test")
    assert 1.0 < cal.comp_factor["ucl"] < 5 / cal.diag["ucl"]["tore_modell"]


def test_unanchored_league_placed_by_cup_results():
    from oddswatch import uefa_elo as E
    t0 = datetime(2025, 8, 1, tzinfo=timezone.utc)
    rnd = random.Random(2)
    games, gid = [], 0
    strong, weak = [1, 2, 3, 4], [11, 12, 13, 14]
    for lg, teams in (("L1", strong), ("L9", weak)):
        for _ in range(4):
            for h in teams:
                for a in teams:
                    if h != a:
                        gid += 1
                        games.append(E.EGame(gid, t0 + timedelta(days=gid % 250), h, a,
                                             rnd.randint(0, 2), rnd.randint(0, 2), False, lg))
    # Schwache Liga verliert im Europapokal fast immer klar
    for i in range(30):
        gid += 1
        h, a = (weak[i % 4], strong[i % 4]) if i % 2 else (strong[i % 4], weak[i % 4])
        hg, ag = (0, 3) if h in weak else (3, 0)
        games.append(E.EGame(gid, t0 + timedelta(days=5 + 8 * i), h, a, hg, ag, False, "ucl"))
    anchor = {t: 1700.0 for t in strong}
    res = E.run_engine(games, anchor, date(2026, 6, 1))
    assert "L9" in res.placed
    assert sum(res.current[t] for t in weak) / 4 < 1700 - 250   # nicht beim Gesamtmittel
