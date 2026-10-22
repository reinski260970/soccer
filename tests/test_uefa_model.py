import math
import random
from datetime import datetime, timedelta, timezone

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


def test_full_run_with_simulated_sources(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    clubs, _ = _world(n_matches=0)
    names = list(clubs)
    rnd = random.Random(7)
    truth = U.Calibration(1.40, 50, U.slope_for(1.40), 0, "truth")
    now = datetime(2026, 10, 22, 6, 0, tzinfo=timezone.utc)
    tid = {n: i + 100 for i, n in enumerate(names)}

    def fixtures(season):
        out = []
        base = datetime(season, 9, 15, 19, tzinfo=timezone.utc)
        comps = [(2, 0), (3, 1), (848, 2)]
        k = 0
        for lid, ci in comps:
            for m in range(150):
                h, a = rnd.sample(names, 2)
                ko = base + timedelta(days=(m % 30) * 7 // 4)
                st, hg, ag = "FT", None, None
                if season == 2026 and ko >= now:
                    st = "NS"
                else:
                    lh, la = truth.lambdas(clubs[h].elo, clubs[a].elo)
                    hg, ag = _pois(rnd, lh), _pois(rnd, la)
                k += 1
                out.append({"fixture": {"id": season * 10000 + k, "date": ko.isoformat(),
                                        "status": {"short": st}},
                            "league": {"id": lid, "round": "League Stage - 1"},
                            "teams": {"home": {"id": tid[h], "name": h}, "away": {"id": tid[a], "name": a}},
                            "goals": {"home": hg, "away": ag},
                            "score": {"fulltime": {"home": hg, "away": ag}}})
        return out

    data = {2026: fixtures(2026), 2025: fixtures(2025)}
    # Ein Spiel morgen garantiert im Fenster
    h, a = names[0], names[1]
    data[2026].append({"fixture": {"id": 999, "date": (now + timedelta(hours=13)).isoformat(),
                                   "status": {"short": "NS"}}, "league": {"id": 2, "round": "League Stage - 3"},
                       "teams": {"home": {"id": tid[h], "name": h}, "away": {"id": tid[a], "name": a}},
                       "goals": {"home": None, "away": None}, "score": {"fulltime": {}}})
    by_id = {f["fixture"]["id"]: f for s in data.values() for f in s}
    calls = {"stats": 0}

    def fake_api(path, cache_days=0.0):
        if path.startswith("/fixtures?league="):
            lid = int(path.split("league=")[1].split("&")[0])
            season = int(path.split("season=")[1].split("&")[0])
            return {"response": [f for f in data[season] if f["league"]["id"] == lid]}, None
        if path.startswith("/fixtures/statistics"):
            calls["stats"] += 1
            f = by_id[int(path.split("=")[1])]
            return {"response": [
                {"team": {"id": f["teams"]["home"]["id"]},
                 "statistics": [{"type": "expected_goals", "value": f"{f['goals']['home'] + 0.3:.2f}"}]},
                {"team": {"id": f["teams"]["away"]["id"]},
                 "statistics": [{"type": "expected_goals", "value": f"{f['goals']['away'] + 0.1:.2f}"}]}]}, None
        if path.startswith("/teams?id="):
            t = int(path.split("=")[1])
            n = next(n for n, i in tid.items() if i == t)
            return {"response": [{"team": {"country": clubs[n].fed.replace(" ", "-")}}]}, None
        return None, "unbekannt"

    def fake_xg(code, as_of):
        fed = next(f for f, c in U.FED_XG.items() if c == code)
        rows = [XGSnapshot(c, 1.5 + (v.elo - 1600) / 600, 1.3 - (v.elo - 1600) / 700, None, None, None, None,
                           9, "test") for c, v in clubs.items() if v.fed == fed]
        return rows, None if rows else "leer"

    def fake_odds(fid):
        return {"Pinnacle": {"home": 2.0, "draw": 3.5, "away": 3.9, "O2.5": 1.9, "U2.5:no": 1.95},
                "Bet365": {"home": 2.1, "draw": 3.4, "away": 3.8, "O2.5": 1.85, "U2.5:no": 1.95}}, None

    monkeypatch.setattr(U, "clubelo_full", lambda: (clubs, []))
    monkeypatch.setattr(U, "_api", fake_api)
    monkeypatch.setattr(U.xg_external, "snapshot", fake_xg)
    monkeypatch.setattr(U.xg_external, "persist_snapshot", lambda *a, **k: None)
    monkeypatch.setattr(U.apifootball, "odds", fake_odds)
    monkeypatch.setattr(U, "datetime", type("D", (datetime,), {"now": staticmethod(lambda tz=None: now)}))

    md, preds = U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    text = md.read_text(encoding="utf-8")
    assert any(p.fx.id == 999 for p in preds)
    assert "Kalibrierung" in text and "Champions League" in text
    p = next(p for p in preds if p.fx.id == 999)
    assert abs(p.probs["1"] + p.probs["X"] + p.probs["2"] - 1) < 1e-6
    assert calls["stats"] > 0
    # Abruflimit 200 je Lauf: der zweite Lauf holt den Rest, der dritte nichts mehr
    assert calls["stats"] == 200
    U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    before = calls["stats"]
    U.run(now.date(), 3, now=now, out_dir=tmp_path / "rep")
    assert calls["stats"] == before
    assert (tmp_path / "data/journal/uefa_predictions.json").exists()
    assert (tmp_path / "data/journal/uefa_clubelo_snapshots.json").exists()


def test_competition_goal_factor_shrinks_toward_one():
    clubs = {"A": U.Club("A", 1700, "Spain"), "B": U.Club("B", 1700, "Italy")}
    fx = [U.UefaFixture(i, "ucl", datetime(2025, 10, 1, tzinfo=timezone.utc), "A", "B", 1, 2, "FT", "", 3, 2)
          for i in range(40)]
    cal = U.calibrate(fx, {1: "A", 2: "B"}, clubs, {})
    assert 1.0 < cal.comp_factor["ucl"] < 5 / cal.diag["ucl"]["tore_modell"]
