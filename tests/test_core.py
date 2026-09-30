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
    val = {"nfl:1x2": {"validated": True, "w": 0.25, "clv": 0.01, "n": 300}}
    cands = evaluate_fixture(fx, val)
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


def test_daily_news_key_ignores_price_moves_but_not_results(tmp_path):
    from oddswatch import daily
    from oddswatch.journal import Journal
    j = Journal(tmp_path)
    j.append("valuebets", [{"event": "A – B", "market": "home", "ref": "KX1", "odds": 2.0,
                            "stake_eh": 1.0}])
    k1 = daily.news_key(j)
    rows = j.read("valuebets")
    rows[0]["odds"] = 2.1                      # nur Kursbewegung
    j.write("valuebets", rows)
    assert daily.news_key(j) == k1
    j.settle("valuebets", "A – B", "home", True)
    assert daily.news_key(j) != k1             # Ergebnis = Neuigkeit


def _news_target():
    from oddswatch.news import Target
    return Target("PLAY", "nfl", "Carolina Panthers – Detroit Lions", "2026-10-05T00:20+00:00",
                  "home", "Carolina Panthers Sieg (inkl. OT)", 2.66, 2.50, 2.57,
                  ["Carolina Panthers", "Carolina", "Panthers", "CAR"],
                  ["Detroit Lions", "Detroit", "Lions", "DET"])


def test_news_alert_for_own_team_injury_and_no_false_matches():
    from datetime import datetime, timezone
    from oddswatch import news
    from oddswatch.news import Item
    now = datetime(2026, 9, 28, 20, tzinfo=timezone.utc)
    pub = datetime(2026, 9, 28, 18, tzinfo=timezone.utc)
    items = [
        Item("ESPN", "nfl", "Panthers CB Jaycee Horn out indefinitely with torn quad", "", "u1", pub,
             ["Carolina Panthers"]),
        Item("CBS Sports", "nfl", "Panthers lose Jaycee Horn, headed for injured reserve", "", "u2", pub),
        # Gegner nur im Text erwähnt -> betrifft die Jets, nicht Detroit
        Item("ESPN", "nfl", "Jets RB Breece Hall week-to-week with quad injury",
             "suffered in the loss to the Lions", "u3", pub, ["New York Jets"]),
        # Sammelartikel mit vielen Teams
        Item("ESPN", "nfl", "Big Week 3 losses: Seahawks, Pats, Panthers", "injuries", "u4", pub,
             ["Seattle Seahawks", "New England Patriots", "Carolina Panthers"]),
    ]
    alerts = news.find_alerts([_news_target()], items, set(), now)
    assert {a.item.link for a in alerts} == {"u1"}          # u2 = gleiche Geschichte (Horn)
    a = next(a for a in alerts if a.item.link == "u1")
    assert a.category == "Ausfall" and a.severe and a.confirmed_by == ["CBS Sports"]
    txt = news.alert_text(alerts, "28.09.2026")
    assert "Freigabe prüfen/aussetzen" in txt and "Entscheidung beim CEO" in txt
    # bereits gemeldete Artikel kommen nicht wieder
    assert news.find_alerts([_news_target()], items, news.seen_keys(alerts), now) == []


def test_news_forum_never_confirms_and_rss_dates():
    from oddswatch import news
    assert news.classify("Bears expected to start Case Keenum at QB")[1] is True
    assert news.classify("Kreuzbandriss: Stürmer fällt monatelang aus")[0] == "Ausfall"
    d = news._parse_date("Mon, 28 Sep 2026 11:24:00 AM PDT")
    assert d and d.hour == 11 and d.utcoffset().total_seconds() == -7 * 3600
    xml = ('<rss><channel><item><title>Rapid: Kapitän verletzt</title><link>x</link>'
           '<pubDate>Mon, 28 Sep 2026 10:00:00 GMT</pubDate></item></channel></rss>')
    it = news.parse_rss(xml, "Austrian Soccer Board", "austria")[0]
    assert it.title.startswith("Rapid") and it.published.hour == 10
    assert "Austrian Soccer Board" in news.FORUMS


# ---------------------------------------------------------------- UEFA / Elo
def test_eloratings_results_reconstruct_pre_match_elo():
    from oddswatch.sources.eloratings import parse_results, parse_ratings, code_for, parse_teams
    txt = ("2025\t01\t02\tVN\tTH\t2\t1\tSEA\t\t21\t1327\t1408\t+5\t−5\t130\t102\n"
           "2025\t01\t04\tBH\tOM\t2\t1\tGLF\tKW\t21\t1530\t1513\t+3\t−4\t77\t80\n")
    r = parse_results(txt)
    assert (r[0].elo_home, r[0].elo_away) == (1306, 1429)   # nachher -/+ Änderung
    assert r[0].home_edge == 1 and r[1].home_edge == 0      # Spielort KW = neutral
    assert parse_ratings("1\t1\tES\t2277\t1\n2\t2\tAR\t2173\t1\n") == {"ES": 2277.0, "AR": 2173.0}
    teams = parse_teams("IE\tIreland\nEI\tNorthern Ireland\tN Ireland\nTR\tTurkey\n")
    assert code_for("Northern Ireland", teams) == "EI"
    assert code_for("Republic of Ireland", teams) == "IE"
    assert code_for("Türkiye", teams) == "TR"


def test_elo_goal_model_fit_and_markets():
    import math
    from oddswatch.models.elo import EloGoals
    rnd = random.Random(3)
    rows = []
    for _ in range(3000):
        diff = rnd.uniform(-400, 400)
        d = (diff + 100) / 400
        rows.append((diff, 1, _pois(rnd, math.exp(0.2 + 0.7 * d)), _pois(rnd, math.exp(0.2 - 0.7 * d))))
    m = EloGoals.fit(rows, home=100)
    assert abs(m.a - 0.2) < 0.05 and abs(m.b - 0.7) < 0.08
    mk = m.markets(1800, 1600)
    assert abs(mk["1"] + mk["X"] + mk["2"] - 1) < 1e-9
    assert mk["1"] > mk["2"]
    n = m.markets(1700, 1700, neutral=True)
    assert abs(n["1"] - n["2"]) < 1e-9


def test_clubelo_page_parse_and_strict_matching():
    from oddswatch import matching
    from oddswatch.sources.clubelo import parse_page
    html = ('"data-1": [{"Colour": "#d00027", "Elo": 1937.1, "Federation": "England", '
            '"Level": 1, "Name": "Liverpool", "TLC": "LIV"}, {"Elo": 1812.0, '
            '"Federation": "France", "Name": "Lille"}]')
    assert parse_page(html) == {"Liverpool": (1937.1, "England"), "Lille": (1812.0, "France")}
    names = ["Lille", "Sparta", "Sparta Praha", "Celje", "Omonia", "Omonia Aradippou",
             "Red Star", "Crvena Zvezda", "Paris SG", "Paris FC"]
    assert matching.find_strict("Lillestrom", names) is None          # kein Präfix-Treffer
    assert matching.find_strict("NK Celje", names) == "Celje"
    assert matching.find_strict("Omonia Nicosia", names) == "Omonia"
    assert matching.find_strict("Paris Saint-Germain", names) is None  # mehrdeutig -> kein Tipp
    al = {"Sparta Prague": "Sparta Praha", "Red Star Belgrade": "Crvena Zvezda"}
    assert matching.find_strict("Sparta Prague", names, al) == "Sparta Praha"
    assert matching.find_strict("Red Star Belgrade", names, al) == "Crvena Zvezda"


def test_xg_line_uses_xg_xga_and_goals():
    from oddswatch.scan import _xg_line
    ms = [Match(date(2026, 9, 1), "A", "B", 3, 0, 1.0, 1.5),
          Match(date(2026, 9, 8), "C", "A", 1, 1, 2.0, 0.5)]
    line, st = _xg_line(ms, "A", date(2026, 9, 10))
    assert st == {"n": 2, "gf": 2.0, "ga": 0.5, "xg": 0.75, "xga": 1.75}
    assert "xG 0.75, xGA 1.75, Tore 2.00:0.50" in line


def test_snapshot_open_gives_closing_line(tmp_path):
    from datetime import datetime, timezone
    from oddswatch import settle
    j = Journal(tmp_path / "j")
    j.append("placed", [{"event": "Luxembourg – Iceland", "kickoff": "2026-09-29T18:45+00:00",
                         "market": "home", "selection": "Luxembourg Sieg", "odds_taken": 3.4,
                         "stake_eh": 0.75, "ref": "KXUEFANLGAME-26SEP29LUXISL-LUX"}])
    ev = {"markets": [
        {"ticker": "KXUEFANLGAME-26SEP29LUXISL-LUX", "yes_sub_title": "Luxembourg",
         "yes_bid_dollars": "0.30", "yes_ask_dollars": "0.31"},
        {"ticker": "KXUEFANLGAME-26SEP29LUXISL-ISL", "yes_sub_title": "Iceland",
         "yes_bid_dollars": "0.41", "yes_ask_dollars": "0.42"},
        {"ticker": "KXUEFANLGAME-26SEP29LUXISL-TIE", "yes_sub_title": "Tie",
         "yes_bid_dollars": "0.28", "yes_ask_dollars": "0.29"}]}
    snaps = str(tmp_path / "s")
    before = datetime(2026, 9, 29, 18, 35, tzinfo=timezone.utc)
    log = settle.snapshot_open(j, snaps, fetch_event=lambda e: (ev, None), now=before)
    assert "Luxembourg 0.30/0.31" in log[0]
    after = datetime(2026, 9, 29, 19, 0, tzinfo=timezone.utc)
    assert settle.snapshot_open(j, snaps, fetch_event=lambda e: (ev, None), now=after) == \
        ["keine offenen Tipps vor Anstoß"]
    cfo = settle.closing_fair_odds("KXUEFANLGAME-26SEP29LUXISL-LUX", snaps)
    assert abs(cfo - 1 / (0.305 / (0.305 + 0.415 + 0.285))) < 1e-9


def test_play_whenever_odds_reach_min_odds():
    off = Offer("Finland – Belarus", "2026-09-29", "away", "Belarus Sieg", 6.29, "kalshi", "now")
    c = evaluate(off, 1.03 / 5.66 + 0.005)            # Quote über "spielbar ab", Quote > 6
    assert c.odds >= c.min_odds
    assert pick([c]) == [c] and c.stake_eh >= 0.25
    below = evaluate(off, 1.03 / 6.29 - 0.005)        # knapp unter spielbar ab
    assert pick([below]) == []
    flagged = evaluate(off, 0.2, flags=["QB fehlt"])
    assert pick([flagged]) == []


def test_hockeyarchives_parse_and_kalshi_kickoff():
    from oddswatch.scan import _kalshi_kickoff
    from oddswatch.sources.hockeyarchives import parse_page, parse_liiga
    html = ("<A NAME=\"DEL\">1<sup>re</sup> journ&eacute;e (vendredi 18 septembre 2026) "
            "Munich - Mannheim 4-3 t.a.b. (1-0,2-1,0-2,0-0,1-0) "
            "Wolfsburg - Cologne 4-3 a.p. (1-1,2-2,0-0,1-0) "
            "<A NAME=\"Amicaux\">18/08/2026 Zell am See - Villach 4-1 (0-0,3-0,1-1)")
    rs = parse_page(html, 2026)
    assert [(r.home, r.away, r.reg_home, r.reg_away, r.extra) for r in rs] == [
        ("Munich", "Mannheim", 3, 3, "SO"), ("Wolfsburg", "Cologne", 3, 3, "OT")]
    assert rs[0].date == date(2026, 9, 18)
    done, up = parse_liiga([
        {"homeTeam": {"teamName": "Ilves"}, "awayTeam": {"teamName": "TPS"}, "start": "2026-09-01T15:30:00Z",
         "ended": True, "finishedType": "ENDED_DURING_EXTENDED_GAME_TIME",
         "periods": [{"category": "NORMAL", "homeTeamGoals": 1, "awayTeamGoals": 0}] * 2
         + [{"category": "NORMAL", "homeTeamGoals": 0, "awayTeamGoals": 2},
            {"category": "OVERTIME", "homeTeamGoals": 1, "awayTeamGoals": 0}]},
        {"homeTeam": {"teamName": "HPK"}, "awayTeam": {"teamName": "Lukko"}, "start": "2026-10-01T15:30:00Z",
         "ended": False}])
    assert (done[0].reg_home, done[0].reg_away, done[0].extra) == (2, 2, "OT") and len(up) == 1
    ko = _kalshi_kickoff("KXNLGAME-26SEP291345EHCKGEN")
    assert ko.isoformat() == "2026-09-29T17:45:00+00:00"


def test_wide_spread_blocks_release():
    from datetime import datetime, timezone
    from oddswatch.scan import Fixture, evaluate_fixture
    from oddswatch.sources.espn import EspnGame, Team
    from oddswatch.sources.kalshi import KalshiQuote
    g = EspnGame("1", "nl", datetime(2026, 9, 29, 17, 45, tzinfo=timezone.utc),
                 Team("Genève Servette"), Team("EHC Kloten"), "STATUS_SCHEDULED")
    q = lambda s, b, a: KalshiQuote("", "E", f"E-{s}", s, s, b, a, 0, 0, "now")
    fx = Fixture("nl", "hockey", g, {"home": 0.65, "away": 0.35}, "",
                 kalshi={"home": q("home", 0.12, 0.40), "away": q("away", 0.12, 0.78)})
    home = [c for c in evaluate_fixture(fx) if c.market == "home"][0]
    assert any("Spread" in f for f in home.flags) and pick([home]) == []


def test_kalshi_reference_uses_liquid_side():
    from oddswatch.scan import _devig_kalshi
    from oddswatch.sources.kalshi import KalshiQuote
    q = lambda s, b, a: KalshiQuote("", "E", f"E-{s}", s, s, b, a, 0, 0, "now")
    ref = _devig_kalshi({"home": q("home", 0.63, 0.66), "away": q("away", 0.06, 0.40)}, ["home", "away"])
    assert abs(ref["home"] - 0.645) < 1e-9 and abs(ref["away"] - 0.355) < 1e-9
    assert _devig_kalshi({"home": q("home", 0.1, 0.7), "away": q("away", 0.1, 0.7)}, ["home", "away"]) == {}


def test_icehl_feed_parse():
    from oddswatch.sources.hockeyarchives import parse_icehl
    per = lambda h, g: {"score_home": h, "score_guest": g}
    data = {"matches": [
        {"start_date": "2026-09-18 18:30:00", "status": "AFTER_MATCH",
         "home": {"name": "FTC-Telekom"}, "guest": {"name": "Olimpija Ljubljana"},
         "results": {"extra_time": True, "shooting": False, "score": {
             "final": per(3, 2), "first_period": per(1, 1), "second_period": per(1, 0),
             "third_period": per(0, 1)}}},
        {"start_date": "2026-09-30 18:30:00", "status": "BEFORE_MATCH",
         "home": {"name": "FTC-Telekom"}, "guest": {"name": "Steinbach Black Wings Linz"}}]}
    done, up = parse_icehl(data)
    assert (done[0].reg_home, done[0].reg_away, done[0].extra) == (2, 2, "OT")
    assert up[0]["start"].utcoffset().total_seconds() == 7200     # Wien, Sommerzeit


def test_verify_against_live_price(tmp_path):
    from oddswatch import verify
    j = Journal(tmp_path)
    j.append("valuebets", [{"event": "Luxembourg – Iceland", "kickoff": "2026-09-29T18:45+00:00",
                            "league": "nations", "market": "home", "selection": "Luxembourg Sieg",
                            "ref": "KXUEFANLGAME-26SEP29LUXISL-LUX", "odds": 3.4, "p_model": 0.3751,
                            "p_ref": 0.2876, "p_final": 0.3226, "min_odds": 3.1929}])
    j.append("forecasts", [{"event": "Luxembourg – Iceland", "market": "home", "league": "nations",
                            "event_id": "401861086"}])
    live = lambda t: ({"status": "active", "yes_bid_dollars": "0.27", "yes_ask_dollars": "0.28"}, None)
    out = "\n".join(verify.verify(j, fetch_market=live))
    assert "| 27/28 ¢ | 3.40 | 3.19 | ✅ PLAY |" in out
    assert "1 / (0.28 + 0.0142 Gebühr) = 3.40" in out
    assert "https://www.espn.com/soccer/match/_/gameId/401861086" in out
    moved = lambda t: ({"status": "active", "yes_bid_dollars": "0.31", "yes_ask_dollars": "0.32"}, None)
    assert "❌ unter Mindestquote" in "\n".join(verify.verify(j, fetch_market=moved))


def test_release_only_when_better_than_market():
    from datetime import datetime, timezone
    from oddswatch.scan import Fixture, evaluate_fixture
    from oddswatch.sources.espn import EspnGame, Team
    from oddswatch.sources.kalshi import KalshiQuote
    g = EspnGame("1", "bundesliga", datetime(2026, 10, 10, 13, 30, tzinfo=timezone.utc),
                 Team("SC Paderborn 07"), Team("VfB Stuttgart"), "STATUS_SCHEDULED")
    q = lambda s, b, a: KalshiQuote("", "E", f"E-{s}", s, s, b, a, 0, 0, "now")
    kal = {"home": q("home", 0.18, 0.20), "draw": q("draw", 0.22, 0.24), "away": q("away", 0.58, 0.60)}
    ref = {"home": 0.187, "draw": 0.233, "away": 0.58}
    fx = Fixture("bundesliga", "soccer", g, {"home": 0.33, "draw": 0.25, "away": 0.42}, "",
                 ref_probs=ref, kalshi=kal)
    # Modell sieht Paderborn bei 33 %, Markt bei 18,7 %: ohne Validierung kein PLAY
    no_val = {"bundesliga:1x2": {"validated": False, "w": 0.0, "clv": -0.067, "n": 520}}
    c = [x for x in evaluate_fixture(fx, no_val) if x.market == "home"][0]
    assert abs(c.p_final - 0.187) < 1e-9 and pick([c]) == []
    assert "nicht besser als der Markt" in c.reason
    # echter Preisfehler bei Kalshi (Ask 15 ¢ bei fairen 18,7 %) -> PLAY auch ohne Modell
    fx.kalshi["home"] = q("home", 0.14, 0.15)
    c = [x for x in evaluate_fixture(fx, no_val) if x.market == "home"][0]
    assert pick([c]) == [c]
    # ohne DraftKings-Linie keine unabhängige Referenz -> keine Freigabe
    fx.ref_probs = {}
    assert all(pick([x]) == [] for x in evaluate_fixture(fx, no_val))


def test_backtest_validates_only_when_better_than_market():
    from oddswatch.backtest import evaluate
    rnd = random.Random(7)
    good, bad = [], []
    for _ in range(3000):
        p_true = rnd.uniform(0.3, 0.7)
        y = rnd.random() < p_true
        p_mkt = min(max(p_true + rnd.gauss(0, 0.06), 0.05), 0.95)   # Markt verrauscht
        odds = [1 / p_mkt * 0.97, 1 / (1 - p_mkt) * 0.97]
        close = [p_true, 1 - p_true]
        good.append(([p_true, 1 - p_true], [p_mkt, 1 - p_mkt], [y, not y], odds, close))
        noisy = min(max(p_mkt + rnd.gauss(0, 0.1), 0.05), 0.95)          # Modell schlechter
        bad.append(([noisy, 1 - noisy], [p_mkt, 1 - p_mkt], [y, not y], odds, close))
    assert evaluate(good)["validated"] and evaluate(good)["w"] > 0
    assert not evaluate(bad)["validated"] and evaluate(bad)["w"] == 0.0


def test_lines_total_and_spread_vs_draftkings(monkeypatch):
    from datetime import datetime, timezone
    from oddswatch import lines
    from oddswatch.scan import Fixture
    from oddswatch.selection import pick as _pick
    from oddswatch.sources.espn import EspnGame, Team
    from oddswatch.sources.kalshi import KalshiQuote
    g = EspnGame("401872964", "nfl", datetime(2026, 10, 2, 0, 15, tzinfo=timezone.utc),
                 Team("Cleveland Browns", "Cleveland", "Browns", "CLE"),
                 Team("Pittsburgh Steelers", "Pittsburgh", "Steelers", "PIT"), "STATUS_SCHEDULED",
                 ref_line={"total_line": 38.5, "ml_over": 1.91, "ml_under": 1.91, "spread_home": 2.5,
                           "odds_spread_home": 2.0, "spread_away": -2.5, "odds_spread_away": 1.83})
    q = KalshiQuote("", "KXNFLGAME-26OCT01PITCLE", "KXNFLGAME-26OCT01PITCLE-CLE", "home", "Cleveland",
                    0.43, 0.44, 0, 0, "now")
    fx = Fixture("nfl", "nfl", g, {"home": 0.45, "away": 0.55}, "", kalshi={"home": q})
    events = {
        "KXNFLTOTAL": {"26OCT01PITCLE": [{"ticker": "T-39", "floor_strike": 38.5,
                                          "yes_bid_dollars": "0.44", "yes_ask_dollars": "0.45"}]},
        "KXNFLSPREAD": {"26OCT01PITCLE": [{"ticker": "S-PIT3", "floor_strike": 2.5,
                                           "yes_sub_title": "PIT Steelers wins by over 2.5 points",
                                           "yes_bid_dollars": "0.52", "yes_ask_dollars": "0.53"}]}}
    monkeypatch.setattr(lines, "_events", lambda s: (events.get(s, {}), None))
    cs = lines.candidates([fx], [], [])
    by = {c.market: c for c in cs}
    assert set(by) == {"O38.5", "U38.5:no", "HC-2.5 PIT", "HC+2.5 CLE:no"}
    assert abs(by["O38.5"].p_final - 0.5) < 1e-9          # DK -110/-110 de-vigged
    assert [c.market for c in _pick(cs)] == ["O38.5"]    # 45 ¢ inkl. Gebühr < fair 50 % -> Wert
    assert abs(by["U38.5:no"].odds - pricing.kalshi_decimal_odds(56, contracts=100)) < 1e-9


def test_clubelo_stops_after_repeated_failures(monkeypatch):
    from oddswatch.sources import clubelo
    calls = []

    def fake_get(url, **kw):
        calls.append(url)
        return None, f"{url}: HTTP 504"
    monkeypatch.setattr(clubelo.fetch, "get", fake_get)
    out, errs = clubelo.ratings()
    assert out == {} and len(calls) == 3 and "abgebrochen" in errs[0]


def test_quick_scan_alerts_once_per_price_level(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from oddswatch import quick, lines
    from oddswatch.scan import Fixture
    from oddswatch.sources.espn import EspnGame, Team
    from oddswatch.sources.kalshi import KalshiQuote
    g = EspnGame("1", "nfl", datetime(2026, 10, 4, 17, tzinfo=timezone.utc),
                 Team("Chicago Bears"), Team("New York Jets"), "STATUS_SCHEDULED")
    q = lambda s, b, a: KalshiQuote("", "E", f"E-{s}", s, s, b, a, 0, 0, "now")
    fx = Fixture("nfl", "nfl", g, {"home": 0.6, "away": 0.4}, "", ref_probs={"home": 0.6, "away": 0.4},
                 kalshi={"home": q("home", 0.54, 0.55), "away": q("away", 0.44, 0.46)})
    monkeypatch.setattr(quick, "fixtures", lambda *a, **k: [fx])
    monkeypatch.setattr(quick, "snapshot", lambda f: None)
    monkeypatch.setattr(quick, "STATE", tmp_path / "alerts.json")
    monkeypatch.setattr(lines, "candidates", lambda *a, **k: [])
    monkeypatch.setattr(quick.settle, "snapshot_open", lambda j: [])
    monkeypatch.setattr(quick.settle, "settle_all", lambda j: [])
    sent = []
    monkeypatch.setattr(quick.telegram, "send", lambda t: sent.append(t) or {"sent": True, "message_ids": [1]})
    j = Journal(tmp_path / "j")
    quick.run(j, send=True)
    quick.run(j, send=True)                       # gleicher Preis -> keine zweite Meldung
    assert len(sent) == 1 and "Chicago Bears" in sent[0]
    assert [r["market"] for r in j.read("valuebets")] == ["home"]


def test_news_ignores_opponent_mentions_ambiguous_city_and_trade_category():
    from datetime import datetime, timezone
    from oddswatch import news
    from oddswatch.news import Item, Target
    now = datetime(2026, 9, 29, 5, tzinfo=timezone.utc)
    pub = datetime(2026, 9, 28, 20, tzinfo=timezone.utc)
    jets = Target("WATCH", "nfl", "Chicago Bears – New York Jets", "2026-10-04T17:00+00:00", "home",
                  "Chicago Bears Sieg", 2.0, 1.9, 1.95, ["Chicago Bears", "Chicago", "Bears", "CHI"],
                  ["New York Jets", "New York", "Jets", "NYJ"])
    vik = Target("WATCH", "nfl", "Minnesota Vikings – Miami Dolphins", "2026-10-04T20:05+00:00",
                 "home", "Vikings Sieg", 1.5, 1.45, 1.5, ["Minnesota Vikings", "Minnesota", "Vikings", "MIN"],
                 ["Miami Dolphins", "Miami", "Dolphins", "MIA"])
    items = [
        Item("ESPN", "nfl", "J.J. McCarthy traded to Giants: Will he succeed in New York?", "", "a", pub,
             ["New York Giants", "Minnesota Vikings"]),
        Item("CBS Sports", "nfl", "Bucs' Baker Mayfield to miss several weeks after loss to Vikings",
             "", "b", pub),
        Item("CBS Sports", "nfl", "J.J. McCarthy trade: Giants acquire Vikings QB", "", "c", pub),
    ]
    got = {(a.target.event, a.item.link, a.category, a.severe)
           for a in news.find_alerts([jets, vik], items, set(), now)}
    assert ("Chicago Bears – New York Jets", "a", "Trade/Wechsel", True) not in got
    assert not any(link == "b" for _, link, _, _ in got)
    # a und c sind dieselbe Geschichte (McCarthy) -> nur eine Meldung, die schwere (QB)
    vik_alerts = [x for x in got if x[0] == "Minnesota Vikings – Miami Dolphins"]
    assert vik_alerts == [("Minnesota Vikings – Miami Dolphins", "c", "Trade/Wechsel", True)]
    assert news.classify("Lions post 31 points for record-setting third time",
                         "They could return to form") is None


def test_news_same_story_not_repeated_in_later_runs():
    from datetime import datetime, timezone
    from oddswatch import news
    from oddswatch.news import Item
    now = datetime(2026, 9, 28, 20, tzinfo=timezone.utc)
    pub = datetime(2026, 9, 28, 18, tzinfo=timezone.utc)
    first = [Item("ESPN", "nfl", "Panthers CB Jaycee Horn out with torn quad", "", "x1", pub,
                  ["Carolina Panthers"])]
    alerts = news.find_alerts([_news_target()], first, set(), now)
    seen = news.seen_keys(alerts)
    later = [Item("CBS Sports", "nfl", "Grading the Panthers after Jaycee Horn injury", "", "x2", pub),
             Item("ESPN", "nfl", "Panthers QB Bryce Young ruled out", "", "x3", pub, ["Carolina Panthers"])]
    got = news.find_alerts([_news_target()], later, seen, now)
    assert [a.item.link for a in got] == ["x3"]             # Horn nicht erneut, Young neu


def test_news_debut_is_return_and_season_start_is_not_news():
    from oddswatch import news
    assert news.classify("Jonathan Greenard (pectoral) makes Eagles debut on Monday",
                         "He tore his pectoral last year")[0] == "Rückkehr/Startelf"
    assert news.classify("Flyers host the Penguins to start season", "") is None
    assert news.classify("Bears expected to start Case Keenum at QB")[0] == "Rückkehr/Startelf"


def test_tennis_atlas_bets_record_and_alert_state(tmp_path):
    from oddswatch import tennis
    from oddswatch.sources.tennis_atlas import to_bet, track_record
    doc = {"p1": "Vidmanova D.", "p2": "Timofeeva M.", "selection": "P1", "selected_odds": 2.3,
           "prob": 0.5144, "stake_eh": 0.5, "tour": "WTA", "tournament": "Beijing",
           "match_day": "2026-09-30", "scheduled_time_vienna": "04:00", "valuebet_key": "k1"}
    b = to_bet(doc)
    assert b.selection == "Vidmanova D." and round(b.ev, 3) == 0.183
    assert round(b.fair_odds, 2) == 1.94 and round(b.min_odds, 2) == 2.00
    assert to_bet({**doc, "selection": None}) is None
    assert to_bet({**doc, "prob": 1.2}) is None
    assert to_bet({**doc, "selection": "P2"}).selection == "Timofeeva M."
    hist = ([{"status": "won", "stake_eh": 1, "profit_eh": 0.8, "match_day": "2026-01-01",
              "clv_odds_pct": 2.0, "closing_status": "captured"}] * 150
            + [{"status": "lost", "stake_eh": 1, "profit_eh": -1, "match_day": "2026-02-01",
                "clv_odds_pct": -1.0, "closing_status": "captured"}] * 100
            + [{"status": "open", "stake_eh": 1}])
    tr = track_record(hist)
    assert tr.settled == 250 and tr.won == 150 and round(tr.roi, 2) == 0.08
    assert tr.clv_median_pct == 2.0 and tennis.validated(tr)
    losing = track_record(hist[150:])
    assert not tennis.validated(losing)          # ROI < 0 -> nur INFO
    assert "INFO" in tennis.report([b], losing, None, "x")
    assert "MONGODB_URI" in tennis.report([], None, "MONGODB_URI nicht gesetzt", "x")
    st = tmp_path / "s.json"
    assert tennis.new_bets([b], st) == [b]
    tennis.mark_sent([b], st)
    assert tennis.new_bets([b], st) == []
    b.odds = 2.4                                  # neue Quote -> erneut melden
    assert tennis.new_bets([b], st) == [b]


def test_tennis_without_uri_reports_honestly(monkeypatch):
    from oddswatch.sources import tennis_atlas
    monkeypatch.delenv("MONGODB_URI", raising=False)
    bets, tr, err = tennis_atlas.fetch()
    assert bets == [] and tr is None and "MONGODB_URI" in err


def test_news_recovery_story_and_game_comeback():
    from oddswatch import news
    assert news.classify("Inside George Kittle's 243-day recovery from torn Achilles")[0] == "Rückkehr/Startelf"
    assert news.classify("Can the Broncos keep pulling off unlikely comeback victories?") is None
    assert news.classify("Panthers CB Jaycee Horn out indefinitely with torn quad")[0] == "Ausfall"


def test_clubelo_stops_after_consecutive_failures_even_with_partial_data(monkeypatch):
    from oddswatch.sources import clubelo
    calls = []

    def fake_get(url, **kw):
        calls.append(url)
        return ("<html></html>", None) if len(calls) == 1 else (None, f"{url}: timed out")
    monkeypatch.setattr(clubelo.fetch, "get", fake_get)
    monkeypatch.setattr(clubelo, "parse_page", lambda h: {"Club A": (1500.0, "ALB")})
    out, errs = clubelo.ratings()
    assert out and len(calls) == 4 and "abgebrochen" in errs[0]


def test_news_match_report_debut_is_not_return():
    from oddswatch import news
    assert news.classify("Scotland routed by Swiss in Pocognoli's home debut") is None
    assert news.classify("Jonathan Greenard (pectoral) makes Eagles debut on Monday")[0] == "Rückkehr/Startelf"


def test_news_digest_groups_by_game():
    from datetime import datetime, timezone
    from oddswatch import news
    from oddswatch.news import Item
    now = datetime(2026, 9, 28, 20, tzinfo=timezone.utc)
    pub = datetime(2026, 9, 28, 18, tzinfo=timezone.utc)
    items = [Item("ESPN", "nfl", "Panthers CB Jaycee Horn out with torn quad", "", "d1", pub, ["Carolina Panthers"])]
    alerts = news.find_alerts([_news_target()], items, set(), now)
    txt = news.digest_text(alerts, "28.09.2026")
    assert "NEWS-ÜBERSICHT" in txt and "🆚 Carolina Panthers – Detroit Lions" in txt and "Jaycee Horn" in txt
    assert "Keine materiellen" in news.digest_text([], "x")


def test_soccer_freeze_blocks_unvalidated_leagues_only():
    from oddswatch.scan import soccer_freeze
    from oddswatch.selection import Candidate
    def cand(league, market):
        return Candidate(event=f"{league}-{market}", kickoff="", market=market, selection="x",
                         source="kalshi", odds=3.0, p_model=0.4, fair_odds=2.5, min_odds=2.6,
                         edge=0.05, ev=0.2, stake_eh=0.5, estimate=False, reason="", observed_at="",
                         liquidity=None, league=league, flags=[])
    cs = [cand("nations", "away"), cand("bundesliga", "home"), cand("bundesliga", "over"), cand("nfl", "home")]
    val = {"bundesliga:1x2": {"validated": True}, "bundesliga:ou": {"validated": False}}
    assert soccer_freeze(cs, {"nations", "bundesliga"}, val) == 2
    assert cs[0].flags and not cs[1].flags and cs[2].flags and not cs[3].flags


def test_withdrawn_valuebets_excluded_from_balance(tmp_path):
    from oddswatch.journal import Journal
    j = Journal(tmp_path)
    j.append("valuebets", [{"event": "A – B", "market": "away", "league": "nations", "odds": 9.0, "stake_eh": 0.25},
                           {"event": "C – D", "market": "home", "league": "nfl", "odds": 2.0, "stake_eh": 0.5}])
    assert j.withdraw("valuebets", lambda r: r["league"] == "nations", "Test") == 1
    s = j.summary("valuebets")
    assert s["settled"] == 0 and s["stake_eh"] == 0
    rows = j.read("valuebets")
    assert rows[0]["result"] == "withdrawn" and "ZURÜCKGEZOGEN" in rows[0]["reason"] and not rows[1]["result"]


def test_tune_calibration_and_score():
    from datetime import date
    from oddswatch import tune
    p = tune.calibrate([0.6, 0.25, 0.15], 0.6)
    assert abs(sum(p) - 1) < 1e-9 and p[0] < 0.6 and p[2] > 0.15      # a<1 zieht zur Mitte
    s = [(date(2025, 1, 1), [0.5, 0.3, 0.2], [0.5, 0.3, 0.2], [True, False, False], [2.0, 3.4, 5.0], [0.5, 0.3, 0.2])]
    r = tune.score(s, 1.0, 0.0)
    assert r["n"] == 1 and abs(r["gain_vs_market"]) < 1e-12


def test_news_noise_filter_and_impact():
    from oddswatch import news
    assert news.is_noise("Can the Broncos keep pulling off unlikely comeback victories?")
    assert news.is_noise("Scotland routed by Swiss in Pocognoli's home debut")
    assert not news.is_noise("Panthers CB Jaycee Horn out indefinitely with torn quad")
    assert news.impact("Bears expected to start Case Keenum at QB") == "hoch"
    assert news.impact("Torwart fällt wochenlang aus") == "hoch"
    assert news.impact("Backup safety placed on IR") == "gering"
    assert news.impact("Ravens center out 2-3 months") == "mittel"


def test_news_market_view_and_position(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from oddswatch import newsmarket
    from oddswatch.sources.espn import EspnGame, Team
    from oddswatch.sources.kalshi import KalshiQuote
    g = EspnGame("1", "nfl", datetime(2026, 10, 4, 17, tzinfo=timezone.utc),
                 Team("Chicago Bears"), Team("New York Jets"), "STATUS_SCHEDULED",
                 ref_line={"ml_home": 1.60, "ml_away": 2.55})
    monkeypatch.setattr(newsmarket, "_game", lambda lg, ev, ko: g)
    q = lambda s, lab, b, a: KalshiQuote("", "E", f"E-{s}", s, lab, b, a, 0, 0, "now")
    j = Journal(tmp_path)
    j.append("forecasts", [{"event": g.title, "market": "home", "p_ref": 0.70},
                           {"event": g.title, "market": "away", "p_ref": 0.30}])
    # Kalshi hinkt hinterher: Jets noch 34 ¢, DraftKings sieht sie bei ~38 %
    cache = {"KXNFLGAME": [q("home", "Chicago", 0.64, 0.65), q("away", "New York J", 0.33, 0.34)]}
    v = newsmarket.view("nfl", g.title, g.kickoff.isoformat(), j, cache)
    assert v.window and "Fenster offen" in v.verdict and "Jets" in v.verdict
    # Kalshi hat nachgezogen -> eingepreist (DraftKings 30 % -> ~38 %)
    cache = {"KXNFLGAME": [q("home", "Chicago", 0.60, 0.61), q("away", "New York J", 0.39, 0.40)]}
    v = newsmarket.view("nfl", g.title, g.kickoff.isoformat(), j, cache)
    assert not v.window and "eingepreist" in v.verdict
    pos = newsmarket.position(v, "home", 0.5, 1.83)
    assert "Verkauf jetzt" in pos and "Haltewert" in pos


def test_news_match_report_not_an_alert_and_mixed_impact():
    from oddswatch import news
    assert news.impact("Buccaneers put WR McMillan on IR, add QB Rypien to practice squad") == "mittel"
    assert news.is_noise("Spain beat Croatia with Yamal double, unbeaten run now at 40")
    assert not (news.classify("Spain beat Croatia with Yamal double, unbeaten run now at 40") or ("", False))[1]
