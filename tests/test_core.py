import random
from datetime import date, timedelta

from oddswatch import pricing
from oddswatch.journal import Journal
from oddswatch.models.poisson import Match, PoissonModel
from oddswatch.models.ratings import Game, PointsModel
from oddswatch.selection import Offer, evaluate, pick
from oddswatch.sources.kalshi import group_1x2, parse_make_snapshots


def _league(seed=1):
    rnd = random.Random(seed)
    strength = {"A": 0.4, "B": 0.1, "C": -0.1, "D": -0.4}
    teams, ms, d0 = list(strength), [], date(2026, 1, 1)
    for k in range(30):
        for h in teams:
            for a in teams:
                if h == a:
                    continue
                import math
                lh = math.exp(0.25 + 0.2 + strength[h] - (-strength[a]) * 0.0 - strength[a] * 0.5)
                la = math.exp(0.25 + strength[a] - strength[h] * 0.5)
                ms.append(Match(d0 + timedelta(days=k), h, a, _pois(rnd, lh), _pois(rnd, la)))
    return ms


def _pois(rnd, lam):
    import math
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rnd.random()
        if p <= L:
            return k
        k += 1


def test_poisson_ranks_and_sums():
    m = PoissonModel.fit(_league(), date(2026, 3, 1), half_life_days=1e6)
    assert m.attack["A"] > m.attack["D"]
    mk = m.markets("A", "D")
    assert abs(mk["1"] + mk["X"] + mk["2"] - 1) < 1e-9
    assert mk["1"] > mk["2"]
    assert abs(mk["O2.5"] + mk["U2.5"] - 1) < 1e-9


def test_points_model():
    rnd = random.Random(3)
    r = {"X": 6, "Y": 0, "Z": -6}
    gs = []
    for k in range(40):
        for h in r:
            for a in r:
                if h != a:
                    base = 110 + rnd.gauss(0, 8)
                    mar = 3 + r[h] - r[a] + rnd.gauss(0, 11)
                    gs.append(Game(date(2026, 1, 1) + timedelta(days=k), h, a, base + mar / 2, base - mar / 2))
    m = PointsModel.fit(gs, date(2026, 3, 1), half_life_days=1e6)
    assert 2 < m.home_adv < 4  # wahr: 3
    mk = m.markets("X", "Z", spread=-10.5, total=220.5)
    assert mk["ML1"] > 0.8
    assert 8 < m.sigma_margin < 14


def test_pricing():
    assert abs(sum(pricing.devig([2.0, 3.5, 4.0])) - 1) < 1e-9
    assert abs(pricing.ev(0.5, 2.1) - 0.05) < 1e-12
    assert abs(pricing.min_odds(0.5, 0.03) - 2.06) < 1e-12
    assert pricing.kalshi_fee_per_contract(0.5) == 0.02
    assert abs(pricing.kalshi_decimal_odds(50) - 1 / 0.52) < 1e-12
    assert pricing.stake_units(0.4, 2.0) == 0.0
    assert 0 < pricing.stake_units(0.6, 2.0) <= 2.0


def test_make_snapshot_parse():
    rules = "If {t} wins the Stuttgart vs Dortmund professional Bundesliga soccer game"
    recs = [
        {"key": "K-VFB", "data": {"ticker": "KXB-26SEP19VFBBVB-VFB", "title": "Stuttgart wins", "ask": 0.4, "bid": 0.39, "rules": rules.format(t="Stuttgart")}},
        {"key": "K-TIE", "data": {"ticker": "KXB-26SEP19VFBBVB-TIE", "title": "Tie is the result", "ask": 0.26, "bid": 0.24, "rules": "If Tie is the result of the Stuttgart vs Dortmund professional"}},
        {"key": "K-BVB", "data": {"ticker": "KXB-26SEP19VFBBVB-BVB", "title": "Dortmund wins", "ask": 0.36, "bid": 0.35, "rules": rules.format(t="Dortmund")}},
        {"key": "BATCH", "data": {"markets": "[]"}},
    ]
    g = group_1x2(parse_make_snapshots(recs))
    assert list(g) == ["KXB-26SEP19VFBBVB"]
    assert g["KXB-26SEP19VFBBVB"]["home"].yes_ask == 0.4


def test_selection_and_journal(tmp_path):
    off = Offer("A vs B", "2026-10-01", "1", "A Sieg", 2.3, "kalshi", "now")
    c = evaluate(off, 0.52, reason="test")
    assert c.ev > 0.19 and c.stake_eh > 0
    assert pick([c, evaluate(off, 0.40)]) == [c]
    j = Journal(tmp_path)
    j.append("valuebets", [c.as_row()])
    assert j.settle("valuebets", "A vs B", "1", True, closing_fair_odds=2.1) == 1
    s = j.summary("valuebets")
    assert s["pnl_eh"] > 0 and s["avg_clv"] > 0


def test_poisson_constant_scores_regression():
    teams = "ABCD"
    ms = [Match(date(2026, 1, 1), h, a, 2, 1) for h in teams for a in teams if h != a]
    m = PoissonModel.fit(ms, date(2026, 2, 1), rho=0, shrink=0)
    lh, la = m.expected_goals("A", "B")
    assert abs(lh - 2) < 1e-6 and abs(la - 1) < 1e-6


def test_points_home_adv_not_halved():
    teams = "ABCD"
    gs = [Game(date(2026, 1, 1), h, a, 105, 95) for h in teams for a in teams if h != a]
    m = PointsModel.fit(gs, date(2026, 2, 1))
    ph, pa = m.expected_points("A", "B")
    assert abs(m.home_adv - 10) < 1e-6
    assert abs(ph - 105) < 1e-6 and abs(pa - 95) < 1e-6


def test_journal_keeps_timestamps(tmp_path):
    off = Offer("A vs B", "k", "1", "A Sieg", 2.0, "kalshi", "2026-09-28T10:00:00Z")
    j = Journal(tmp_path)
    j.append("valuebets", [evaluate(off, 0.6).as_row()])
    row = j.read("valuebets")[0]
    assert row["observed_at"] == "2026-09-28T10:00:00Z"
    assert row["created_at"]


def test_matching_names():
    from oddswatch.matching import find, match_label
    fd = ["M'gladbach", "FC Koln", "Ein Frankfurt", "RB Leipzig", "Bayern Munich", "A. Lustenau", "Ried"]
    assert find("Borussia Mönchengladbach", fd) == "M'gladbach"
    assert find("FC Cologne", fd) == "FC Koln"
    assert find("Eintracht Frankfurt", fd) == "Ein Frankfurt"
    assert find("Austria Lustenau", fd) == "A. Lustenau"
    assert find("SV Josko Ried", fd) == "Ried"
    assert match_label("M´gladbach", ["Borussia Mönchengladbach", "Gladbach", "BMG"])
    assert match_label("Los Angeles C", ["Los Angeles Chargers", "Los Angeles", "Chargers", "LAC"])
    assert not match_label("Los Angeles R", ["Los Angeles Chargers", "Los Angeles", "Chargers", "LAC"])


def test_telegram_chunks_and_missing_token(monkeypatch):
    from oddswatch import telegram
    text = "\n".join("x" * 100 for _ in range(100))
    parts = telegram.chunks(text)
    assert all(len(p) <= telegram.LIMIT for p in parts) and "".join(parts) == text
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    r = telegram.send("hi")
    assert r["sent"] is False and "nicht gesetzt" in r["error"]


def test_espn_moneyline_parse():
    from oddswatch.sources.espn import parse_scoreboard
    ev = {"events": [{"id": "1", "date": "2026-10-04T17:00Z",
                      "status": {"type": {"name": "STATUS_SCHEDULED"}},
                      "competitions": [{"competitors": [
                          {"homeAway": "home", "team": {"displayName": "Washington Commanders"}},
                          {"homeAway": "away", "team": {"displayName": "Indianapolis Colts"}}],
                          "odds": [{"provider": {"name": "DraftKings"}, "details": "IND -3.5",
                                    "moneyline": {"home": {"close": {"odds": "+150"}},
                                                  "away": {"close": {"odds": "-180"}}}}]}]}]}
    g = parse_scoreboard(ev, "nfl")[0]
    assert abs(g.ref_line["ml_home"] - 2.5) < 1e-9
    assert abs(g.ref_line["ml_away"] - (1 + 100 / 180)) < 1e-9


def test_divergence_blocks_release():
    from datetime import datetime, timezone
    from oddswatch.scan import Fixture, evaluate_fixture
    from oddswatch.sources.espn import EspnGame, Team
    from oddswatch.sources.kalshi import KalshiQuote
    g = EspnGame("1", "nfl", datetime(2026, 10, 4, 17, tzinfo=timezone.utc),
                 Team("Home Team"), Team("Away Team"), "STATUS_SCHEDULED")
    q = lambda s, a: KalshiQuote("", "E", f"E-{s}", s, s, a - 0.01, a, 0, 0, "now")
    fx = Fixture("nfl", "nfl", g, {"home": 0.70, "away": 0.30}, "", ref_probs={"home": 0.45, "away": 0.55},
                 kalshi={"home": q("home", 0.46), "away": q("away", 0.56)})
    cands = evaluate_fixture(fx, datetime(2026, 10, 10, tzinfo=timezone.utc))
    home = [c for c in cands if c.market == "home"][0]
    assert home.flags and "weicht" in home.flags[0]
    assert pick(cands) == []


def test_kalshi_sign_and_fill_import(tmp_path, monkeypatch):
    import base64
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from oddswatch import portfolio
    from oddswatch.sources import kalshi_auth
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                            serialization.NoEncryption()).decode()
    # einzeilig mit literalen \n, wie oft in Umgebungsvariablen eingefügt
    loaded = kalshi_auth._load_key(pem.replace("\n", "\\n"))
    sig = kalshi_auth.sign(loaded, "1700000000000", "get", "/trade-api/v2/portfolio/fills?limit=5")
    key.public_key().verify(base64.b64decode(sig), b"1700000000000GET/trade-api/v2/portfolio/fills",
                            padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                        salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())

    class FakeClient:
        def fills(self):
            return [{"fill_id": "f1", "ticker": "KXNFLGAME-26OCT04DETCAR-CAR", "side": "yes",
                     "action": "buy", "count_fp": "10", "yes_price_dollars": "0.36", "is_taker": True},
                    {"fill_id": "f2", "ticker": "KXNFLGAME-26OCT04DETCAR-CAR", "side": "yes",
                     "action": "sell", "count_fp": "5", "yes_price_dollars": "0.40"}]
    monkeypatch.setattr(portfolio.kalshi, "fetch_market",
                        lambda t: ({"yes_sub_title": "Carolina", "event_ticker": "KXNFLGAME-26OCT04DETCAR"}, None))
    monkeypatch.setattr(portfolio, "_event_title", lambda e, c: "DET Lions vs CAR Panthers")
    j = Journal(tmp_path)
    j.append("valuebets", [{"ref": "KXNFLGAME-26OCT04DETCAR-CAR", "event": "x", "market": "home"}])
    log = portfolio.import_fills(j, client=FakeClient(), eh_usd=10)
    assert "1 neu verbucht" in log[0] and "1 Verkäufe" in log[0]
    row = j.read("placed")[0]
    assert row["selection"] == "Carolina" and row["valuebet_ref"]
    assert abs(float(row["odds_taken"]) - 10 / (3.6 + 0.17)) < 1e-3  # Gebühr ceil(0.07*10*.36*.64)=0.17
    portfolio.import_fills(j, client=FakeClient(), eh_usd=10)
    assert len(j.read("placed")) == 1  # dedupliziert


def test_settle_by_ticker_and_no_side(tmp_path, monkeypatch):
    from oddswatch import settle
    j = Journal(tmp_path)
    j.append("placed", [
        {"event": "E", "market": "yes", "selection": "A", "odds_taken": 2.0, "stake_eh": 1, "ref": "KX-E-A"},
        {"event": "E", "market": "yes", "selection": "TIE", "odds_taken": 4.0, "stake_eh": 1, "ref": "KX-E-TIE"},
        {"event": "E", "market": "no", "selection": "NICHT B", "odds_taken": 1.5, "stake_eh": 1, "ref": "KX-E-B"}])
    res = {"KX-E-A": "yes", "KX-E-TIE": "no", "KX-E-B": "no"}
    monkeypatch.setattr(settle.kalshi, "fetch_market", lambda t: ({"result": res[t]}, None))
    monkeypatch.setattr(settle, "closing_fair_odds", lambda t: None)
    settle.settle_all(j)
    got = {r["ref"]: r["result"] for r in j.read("placed")}
    assert got == {"KX-E-A": "win", "KX-E-TIE": "loss", "KX-E-B": "win"}


def test_telegram_text_shows_league_date_and_opponent():
    from oddswatch import report
    from oddswatch.selection import Candidate
    c = Candidate(event="SC Freiburg – Schalke 04", kickoff="2026-10-11T15:30+00:00",
                  market="away", selection="Schalke 04 Sieg (90 Min.)", source="kalshi",
                  odds=4.98, p_model=0.22, fair_odds=4.53, min_odds=4.66, edge=0.02,
                  ev=0.10, stake_eh=0.0, estimate=False, reason="", observed_at="",
                  liquidity=None, league="bundesliga",
                  flags=["Anstoß außerhalb des Freigabefensters"])
    txt = report.telegram_text("28.09.2026", [], [c])
    assert "Bundesliga · So 11.10. 17:30 MESZ" in txt
    assert "SC Freiburg – Schalke 04" in txt and "Grund: Anstoß außerhalb" in txt


def test_daily_text_evaluation_profit_and_outlook(tmp_path):
    from datetime import datetime, timezone
    from oddswatch import daily
    from oddswatch.journal import Journal
    j = Journal(tmp_path)
    base = {"league": "nhl", "source": "kalshi", "estimate": False, "reason": ""}
    j.append("valuebets", [
        {**base, "event": "A – B", "kickoff": "2026-09-28T00:00+00:00", "market": "home",
         "selection": "A Sieg", "ref": "KX1", "odds": 2.0, "stake_eh": 1.0,
         "result": "win", "pnl_eh": 1.0, "clv": 0.05},
        {**base, "event": "C – D", "kickoff": "2026-09-30T18:00+00:00", "market": "away",
         "selection": "D Sieg", "ref": "KX2", "odds": 3.0, "stake_eh": 0.5}])
    txt = daily.daily_text(j, now=datetime(2026, 9, 28, 12, tzinfo=timezone.utc), eh_usd=10)
    assert "A Sieg @ 2,00 → ✅ Gewinn +1.00 EH | CLV +5.0 %" in txt
    assert "G/V +1.00 EH (+10.00 $)" in txt and "Bilanz 1-0" in txt
    assert "Offen: 1 Wetten, 0,5 EH im Risiko" in txt
    assert "NHL · Mi 30.09. 20:00 MESZ" in txt and "🆚 C – D" in txt


def test_fatigue_back_to_back_travel_and_climate_zone():
    from datetime import date
    from oddswatch.models import fatigue
    from oddswatch.models.fatigue import Slot
    slots = [Slot(date(2026, 11, 1), "Boston Celtics", "Miami Heat"),
             Slot(date(2026, 11, 2), "Denver Nuggets", "Miami Heat"),
             Slot(date(2026, 11, 2), "Boston Celtics", "Utah Jazz")]
    (bh, ba), (dh, da), _ = fatigue.loads("nba", slots)
    assert ba.km > 1500 and ba.feats["zone"] == 1 and ba.zones == ("subtropisch", "kontinental-kalt")
    assert da.rest == 1 and da.feats["short"] == 1          # Miami: Back-to-back
    assert da.feats["altitude"] == 1 and da.feats["tz"] == 2  # Denver: Höhe, 2 Zeitzonen
    assert 2500 < da.km < 3200 and "Anreise" in da.text() and "Höhe" in da.text()
    assert bh.km == 0 and bh.feats["zone"] == 0


def test_fatigue_effects_recover_synthetic_b2b_penalty():
    import random
    from oddswatch.models.fatigue import FEATURES, Effects
    rnd = random.Random(1)
    xs, ys = [], []
    for _ in range(3000):
        x = [0.0] * len(FEATURES)
        x[0] = rnd.choice([-1.0, 0.0, 0.0, 1.0])       # short-Differenz
        xs.append(x)
        ys.append(-2.0 * x[0] + rnd.gauss(0, 12))
    eff = Effects.fit(xs, ys)
    assert -2.8 < eff.coef["short"] < -1.2 and abs(eff.coef["travel"]) < 1e-9
