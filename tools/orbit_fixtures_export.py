"""Orbit-Spielplan -> Neon (nur lesen auf Orbit-Seite, nur Termine).

Liest aus orbit_quotes.sqlite3 (vom Orbit Steam-Wächter) alle anstehenden
Eishockey-Spiele der nächsten Tage und schreibt sie in die Neon-Tabelle
sports.orbit_fixtures. Die GitHub-Scans (DEL, Extraliga) lesen den Spielplan
von dort. Es werden keine Quoten übertragen.

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


def export(days: int) -> int:
    import psycopg
    rows = read_fixtures(days)
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
        conn.commit()
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Orbit-Spielplan nach Neon exportieren")
    ap.add_argument("--days", type=int, default=8, help="so viele Tage voraus")
    ap.add_argument("--loop", type=float, default=0, help="alle N Minuten wiederholen (0 = einmal)")
    a = ap.parse_args()
    while True:
        try:
            n = export(a.days)
            print(f"[{time.strftime('%H:%M:%S')}] {n} Eishockey-Spiele nach Neon geschrieben")
        except Exception as exc:  # weiterlaufen, nächster Versuch beim nächsten Takt
            print(f"[{time.strftime('%H:%M:%S')}] Fehler: {type(exc).__name__}: {exc}")
            if not a.loop:
                raise SystemExit(1)
        if not a.loop:
            break
        time.sleep(a.loop * 60)


if __name__ == "__main__":
    main()
