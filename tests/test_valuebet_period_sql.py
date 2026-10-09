from datetime import datetime, timezone

from oddswatch import surebet_values
from oddswatch.sources.surebet import SurebetValue
from oddswatch.sql import valuebet as vb


class _DummyConn:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


def _audit(sport="American football", tournament="NFL", period="1h"):
    v = SurebetValue(
        id="evt1",
        sport=sport,
        tournament=tournament,
        teams=("Home", "Away"),
        kickoff=datetime(2026, 10, 12, 18, 0, tzinfo=timezone.utc),
        selection="Gesamt-Punkte Über 22.5",
        market="Gesamt-Punkte · 1. Halbzeit",
        odds=1.95,
        probability=None,
        overvalue=None,
        bookmaker="bet365",
        back=True,
        bet_type="over",
        condition="22.5",
        period=period,
        base="overall",
    )
    return surebet_values.Audit(
        value=v,
        status="BESTÄTIGT",
        our_probability=0.56,
        our_fair=1/0.56,
        our_ev=0.092,
        note="NFL 1h PointsModel",
    )


def test_descriptor_normalizes_short_period_codes():
    d = vb._descriptor(_audit(period="1h").value)
    assert d is not None
    assert d[0] == "total"
    assert d[3] == "FIRST_HALF"

    q = _audit(sport="Basketball", tournament="NBA", period="q1")
    d2 = vb._descriptor(q.value)
    assert d2[3] == "FIRST_QUARTER"


def test_period_audit_persists_without_fullgame_fixture(monkeypatch):
    captured = {}

    monkeypatch.setenv("SPORTS_DATABASE_URL", "postgresql://dummy")
    monkeypatch.setattr(vb, "connect", lambda: _DummyConn())
    monkeypatch.setattr(vb, "migrate", lambda conn: None)

    def fake_ingest(conn, bundle):
        captured.update(bundle)
        return {"events": len(bundle.get("events", [])),
                "predictions": len(bundle.get("predictions", [])),
                "signals": len(bundle.get("signals", [])),
                "odds_snapshots": len(bundle.get("odds_snapshots", []))}

    monkeypatch.setattr(vb, "ingest", fake_ingest)

    out = vb.persist_audits([_audit()], fixtures=[])
    assert out["stored"] if "stored" in out else out["events"] == 1
    assert captured["events"][0]["league"] == "nfl"
    assert captured["predictions"][0]["period"] == "FIRST_HALF"
    assert captured["predictions"][0]["market"] == "total"
    assert captured["signals"][0]["signal_type"] == "WATCH"
