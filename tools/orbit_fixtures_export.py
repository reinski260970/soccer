"""Orbit-Spielplan und letzte Vorspiel-Kurse -> Neon (nur lesen auf Orbit-Seite).

Liest aus orbit_quotes.sqlite3 (vom Orbit Steam-Wächter) alle anstehenden
Eishockey-Spiele der nächsten Tage und schreibt sie in die Neon-Tabelle
sports.orbit_fixtures. Dazu kommt je Auswahl der letzte Back/Lay-Kurs vor
Spielbeginn in sports.orbit_prices. Die GitHub-Scans lesen beides von dort.

Einrichtung (einmalig):
  1. In denselben Ordner wie orbit_quotes.sqlite3 legen.
  2. pip install "psycopg[binary]"
  3. Neon-Verbindung als Umgebungsvariable NEON_DATABASE_URL setzen
     ODER in eine Datei neon_url.txt im selben Ordner schreiben
     (derselbe Wert wie das GitHub-Secret SPORTS_DATABASE_URL).
Start:   python orbit_fixtures_export.py            (einmal)
         python orbit_fixtures_export.py --loop 60  (alle 60 Minuten)
"""
import argparse
import os
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "orbit_quotes.sqlite3"
SPORTS = ("Eishockey",)

DDL = """
CREATE SCHEMA IF NOT EXISTS sports;
CREATE TABLE IF NOT EXISTS sports.orbit_fixtures (
  event_id text PRIMARY KEY,
  sport text NOT NULL,
  competition text,
  event_name text NOT NULL,
  home text,
  away text,
  start_utc timestamptz NOT NULL,
  total_matched double precision,
  seen_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS orbit_fixtures_start_idx ON sports.orbit_fixtures(start_utc);
CREATE TABLE IF NOT EXISTS sports.orbit_prices (
  market_id text NOT NULL,
  selection_id bigint NOT NULL,
  event_id text NOT NULL,
  market_type text,
  runner text,
  back double precision,
  back_amount double precision,
  lay double precision,
  lay_amount double precision,
  traded double precision,
  market_matched double precision,
  tick_ts timestamptz NOT NULL,
  seen_at timestamptz NOT NULL,
  PRIMARY KEY (market_id, selection_id)
);
CREATE INDEX IF NOT EXISTS orbit_prices_event_idx ON sports.orbit_prices(event_id);
"""


def neon_url() -> str:
    url = (os.getenv("NEON_DATABASE_URL") or "").strip()
    f = BASE / "neon_url.txt"
    if not url and f.exists():
        url = f.read_text(encoding="utf-8").strip()
    if not url:
        raise SystemExit("Keine Neon-Verbindung: NEON_DATABASE_URL setzen oder neon_url.txt anlegen.")
    # SQLAlchemy-Schreibweise aus dem GitHub-Secret auch hier akzeptieren.
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def split_teams(name: str):
    """Orbit/Betfair: 'Heim v Gast' (Europa) bzw. 'Gast @ Heim' (Nordamerika)."""
    if " @ " in name:
        away, home = name.split(" @ ", 1)
        return home.strip(), away.strip()
    for sep in (" v ", " vs ", " - "):
        if sep in name:
            home, away = name.split(sep, 1)
            return home.strip(), away.strip()
    return None, None


def read_fixtures(days: int):
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    src = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    rows = src.execute(
        f"""SELECT event_id, sport, competition, event_name, start_utc,
                   MAX(total_matched) AS total_matched, MAX(updated_at) AS updated_at
            FROM markets
            WHERE sport IN ({",".join("?" * len(SPORTS))})
              AND start_utc IS NOT NULL AND event_id IS NOT NULL
            GROUP BY event_id""",
        SPORTS,
    ).fetchall()
    src.close()
    out = []
    for r in rows:
        try:
            start = datetime.fromisoformat(r["start_utc"])
        except (TypeError, ValueError):
            continue
        if not (now < start <= until):
            continue
        home, away = split_teams(r["event_name"] or "")
        if not home or not away:
            continue
        out.append((str(r["event_id"]), r["sport"], r["competition"], r["event_name"],
                    home, away, start, r["total_matched"], now))
    return out


def read_prices(event_ids):
    """Letzter Vorspiel-Tick je Auswahl (in_play = 0) für die exportierten Spiele."""
    if not event_ids:
        return []
    now = datetime.now(timezone.utc)
    src = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    marks = ",".join("?" * len(event_ids))
    rows = src.execute(
        f"""WITH last AS (
                 SELECT market_id, selection_id, MAX(id) AS tick_id FROM ticks
                 WHERE in_play = 0 AND market_id IN (SELECT market_id FROM markets WHERE event_id IN ({marks}))
                 GROUP BY market_id, selection_id)
            SELECT m.market_id, t.selection_id, m.event_id, m.market_type, r.name AS runner,
                   t.back, t.back_amount, t.lay, t.lay_amount, t.traded, m.total_matched, t.ts
            FROM last l
            JOIN ticks t ON t.id = l.tick_id
            JOIN markets m ON m.market_id = l.market_id
            LEFT JOIN runners r ON r.market_id = l.market_id AND r.selection_id = l.selection_id""",
        list(event_ids),
    ).fetchall()
    src.close()
    out = []
    for r in rows:
        try:
            ts = datetime.fromisoformat(r["ts"])
        except (TypeError, ValueError):
            continue
        out.append((str(r["market_id"]), int(r["selection_id"]), str(r["event_id"]), r["market_type"],
                    r["runner"], r["back"], r["back_amount"], r["lay"], r["lay_amount"],
                    r["traded"], r["total_matched"], ts, now))
    return out


def export(days: int) -> tuple[int, int]:
    import psycopg
    rows = read_fixtures(days)
    prices = read_prices([r[0] for r in rows])
    with psycopg.connect(neon_url()) as conn:
        conn.execute(DDL)
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO sports.orbit_fixtures
                   (event_id, sport, competition, event_name, home, away, start_utc, total_matched, seen_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id) DO UPDATE SET
                     competition=EXCLUDED.competition, event_name=EXCLUDED.event_name,
                     home=EXCLUDED.home, away=EXCLUDED.away, start_utc=EXCLUDED.start_utc,
                     total_matched=EXCLUDED.total_matched, seen_at=EXCLUDED.seen_at""",
                rows,
            )
            cur.executemany(
                """INSERT INTO sports.orbit_prices
                   (market_id, selection_id, event_id, market_type, runner, back, back_amount,
                    lay, lay_amount, traded, market_matched, tick_ts, seen_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (market_id, selection_id) DO UPDATE SET
                     market_type=EXCLUDED.market_type, runner=EXCLUDED.runner,
                     back=EXCLUDED.back, back_amount=EXCLUDED.back_amount,
                     lay=EXCLUDED.lay, lay_amount=EXCLUDED.lay_amount, traded=EXCLUDED.traded,
                     market_matched=EXCLUDED.market_matched, tick_ts=EXCLUDED.tick_ts,
                     seen_at=EXCLUDED.seen_at""",
                prices,
            )
        conn.commit()
    return len(rows), len(prices)


def main():
    ap = argparse.ArgumentParser(description="Orbit-Spielplan nach Neon exportieren")
    ap.add_argument("--days", type=int, default=8, help="so viele Tage voraus")
    ap.add_argument("--loop", type=float, default=0, help="alle N Minuten wiederholen (0 = einmal)")
    a = ap.parse_args()
    while True:
        try:
            n, p = export(a.days)
            print(f"[{time.strftime('%H:%M:%S')}] {n} Eishockey-Spiele und {p} Kurse nach Neon geschrieben")
        except Exception as exc:  # weiterlaufen, nächster Versuch beim nächsten Takt
            print(f"[{time.strftime('%H:%M:%S')}] Fehler: {type(exc).__name__}: {exc}")
            if not a.loop:
                raise SystemExit(1)
        if not a.loop:
            break
        time.sleep(a.loop * 60)


if __name__ == "__main__":
    main()
