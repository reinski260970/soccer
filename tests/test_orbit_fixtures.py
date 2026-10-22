import importlib.util
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from oddswatch.sources import orbit_fixtures


def _load_exporter():
    path = Path(__file__).resolve().parents[1] / "tools" / "orbit_fixtures_export.py"
    spec = importlib.util.spec_from_file_location("orbit_fixtures_export", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_league_mapping():
    assert orbit_fixtures.league_of("German DEL") == "del"
    assert orbit_fixtures.league_of("German DEL 2") is None
    assert orbit_fixtures.league_of("Czech Extraliga") == "extraliga"
    assert orbit_fixtures.league_of("Slovakian Extraliga") is None
    assert orbit_fixtures.league_of("Swedish SHL") == "shl"
    assert orbit_fixtures.league_of("NHL") == "nhl"


def test_exporter_splits_team_names():
    ex = _load_exporter()
    assert ex.split_teams("Adler Mannheim v Kolner Haie") == ("Adler Mannheim", "Kolner Haie")
    assert ex.split_teams("Boston Bruins @ New York Rangers") == ("New York Rangers", "Boston Bruins")
    assert ex.split_teams("Nur ein Name") == (None, None)


def test_exporter_reads_upcoming_hockey(tmp_path, monkeypatch):
    ex = _load_exporter()
    db = tmp_path / "orbit_quotes.sqlite3"
    monkeypatch.setattr(ex, "DB", db)
    now = datetime.now(timezone.utc)
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE markets (market_id TEXT PRIMARY KEY, event_id TEXT, event_name TEXT, competition TEXT,"
              " sport TEXT, market_type TEXT, start_utc TEXT, total_matched REAL, updated_at TEXT)")
    rows = [
        ("m1", "e1", "Adler Mannheim v Kolner Haie", "German DEL", "Eishockey", "MATCH_ODDS", (now + timedelta(days=1)).isoformat(), 900),
        ("m2", "e1", "Adler Mannheim v Kolner Haie", "German DEL", "Eishockey", "OVER_UNDER", (now + timedelta(days=1)).isoformat(), 100),
        ("m3", "e2", "Alt v Alt", "German DEL", "Eishockey", "MATCH_ODDS", (now - timedelta(days=1)).isoformat(), 1),
        ("m4", "e3", "A v B", "Premier League", "Fußball", "MATCH_ODDS", (now + timedelta(days=1)).isoformat(), 1),
    ]
    c.executemany("INSERT INTO markets VALUES (?,?,?,?,?,?,?,?,'x')", rows)
    c.commit()
    c.close()
    out = ex.read_fixtures(8)
    assert len(out) == 1
    assert out[0][0] == "e1" and out[0][4:6] == ("Adler Mannheim", "Kolner Haie")
    assert out[0][7] == 900


def test_upcoming_reads_table_and_filters(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'x.db'}"
    now = datetime.now(timezone.utc)
    # SQLite has no schemas; emulate sports.* via an attached database file.
    sports_db = tmp_path / "sports.db"
    from oddswatch import sql_store

    def fake_engine():
        e = create_engine(url)
        from sqlalchemy import event

        @event.listens_for(e, "connect")
        def _attach(dbapi_conn, _):
            dbapi_conn.execute(f"ATTACH DATABASE '{sports_db}' AS sports")
        return e
    monkeypatch.setattr(sql_store, "engine", fake_engine)
    with fake_engine().begin() as conn:
        conn.execute(text("CREATE TABLE sports.orbit_fixtures (event_id TEXT, competition TEXT, home TEXT,"
                          " away TEXT, start_utc TIMESTAMP, seen_at TIMESTAMP)"))
        ins = text("INSERT INTO sports.orbit_fixtures VALUES (:i,:c,:h,:a,:s,:seen)")
        conn.execute(ins, dict(i="1", c="German DEL", h="Adler Mannheim", a="Kolner Haie",
                               s=now + timedelta(hours=5), seen=now))
        conn.execute(ins, dict(i="2", c="German DEL", h="Old", a="Stale",
                               s=now + timedelta(hours=6), seen=now - timedelta(days=2)))
        conn.execute(ins, dict(i="3", c="Czech Extraliga", h="Sparta", a="Pardubice",
                               s=now + timedelta(hours=7), seen=now))
    out, err = orbit_fixtures.upcoming("del", now, now + timedelta(days=1))
    assert err is None
    assert [g["id"] for g in out] == ["orbit:1"]
    assert out[0]["home"] == "Adler Mannheim"
    out, err = orbit_fixtures.upcoming("extraliga", now, now + timedelta(days=1))
    assert [g["home"] for g in out] == ["Sparta"]


def test_upcoming_without_table_reports_error(tmp_path, monkeypatch):
    from oddswatch import sql_store
    monkeypatch.setattr(sql_store, "engine", lambda: create_engine(f"sqlite:///{tmp_path / 'y.db'}"))
    now = datetime.now(timezone.utc)
    out, err = orbit_fixtures.upcoming("del", now, now + timedelta(days=1))
    assert out == [] and "Orbit-Spielplan" in err


def test_exporter_reads_last_prematch_tick(tmp_path, monkeypatch):
    ex = _load_exporter()
    db = tmp_path / "orbit_quotes.sqlite3"
    monkeypatch.setattr(ex, "DB", db)
    c = sqlite3.connect(db)
    c.executescript("""
      CREATE TABLE markets (market_id TEXT PRIMARY KEY, event_id TEXT, event_name TEXT, competition TEXT,
        sport TEXT, market_type TEXT, start_utc TEXT, total_matched REAL, updated_at TEXT);
      CREATE TABLE runners (market_id TEXT, selection_id INTEGER, name TEXT, PRIMARY KEY (market_id, selection_id));
      CREATE TABLE ticks (id INTEGER PRIMARY KEY, ts TEXT NOT NULL, market_id TEXT NOT NULL, selection_id INTEGER NOT NULL,
        back REAL, back_amount REAL, lay REAL, lay_amount REAL, traded REAL, in_play INTEGER);
      INSERT INTO markets VALUES ('m1','e1','A v B','German DEL','Eishockey','MATCH_ODDS','2026-10-23T17:30:00+00:00',500,'x');
      INSERT INTO runners VALUES ('m1',1,'A'),('m1',2,'B');
      INSERT INTO ticks (ts,market_id,selection_id,back,back_amount,lay,lay_amount,traded,in_play) VALUES
        ('2026-10-22T08:00:00+00:00','m1',1,2.0,10,2.1,10,100,0),
        ('2026-10-22T09:00:00+00:00','m1',1,1.9,20,2.0,15,150,0),
        ('2026-10-23T18:00:00+00:00','m1',1,1.2,5,1.3,5,400,1),
        ('2026-10-22T09:00:00+00:00','m1',2,2.2,8,2.3,9,90,0);
    """)
    c.close()
    rows = {(r[0], r[1]): r for r in ex.read_prices(["e1"])}
    assert set(rows) == {("m1", 1), ("m1", 2)}
    a = rows[("m1", 1)]
    assert a[4] == "A" and a[5] == 1.9 and a[7] == 2.0   # last pre-match tick, not in-play
    assert ex.read_prices([]) == []
