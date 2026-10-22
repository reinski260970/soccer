from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from openpyxl import load_workbook

from oddswatch.export_sharpery import COLUMNS, export_scan
from oddswatch.scan import Fixture
from oddswatch.selection import Offer, evaluate
from oddswatch.sources.espn import EspnGame, Team


def test_export_scan_writes_bets_and_forecasts(tmp_path):
    ko = datetime.now(timezone.utc) + timedelta(hours=6)
    g = EspnGame("orbit:1", "nl", ko, Team("HC Davos"), Team("SC Bern"), "STATUS_SCHEDULED")
    fx = Fixture("nl", "hockey", g, {"home": 0.68, "away": 0.32}, "erw. Tore 3.2:2.4")
    o = Offer(event=g.title, kickoff=ko.isoformat(), market="home", selection="HC Davos Sieg (inkl. OT)",
              odds=1.60, source="orbit", observed_at=ko.isoformat(), league="nl")
    fx.market_quotes = {"home": [o]}
    c = evaluate(o, 0.68, estimate=True)
    c2 = evaluate(Offer(**{**o.__dict__, "market": "away", "selection": "SC Bern", "odds": 2.2}), 0.32)
    res = SimpleNamespace(candidates=[c, c2], fixtures=[fx])
    path, nb, nf = export_scan(res, str(tmp_path / "x"))
    assert (nb, nf) == (1, 1)
    wb = load_workbook(path)
    bets = list(wb["Bets"].values)
    assert list(bets[0]) == COLUMNS
    row = dict(zip(COLUMNS, bets[1]))
    assert row["Sport"] == "Ice Hockey" and row["League"] == "National League"
    assert row["Stake"] > 0
    assert row["Bookmaker"] == "Orbit" and row["Bet Odds"] == 1.6 and row["Result"] == "pending"
    prog = list(wb["Prognosen"].values)
    assert prog[1][2] == "HC Davos – SC Bern" and prog[1][3] == 68.0 and prog[1][9] == 1.6
