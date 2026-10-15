"""Export completed NHL game scores from Neon to the V6 feature bridge.

The Neon 2024/25 dataset contains final scores but not verified regulation
scores. Do not substitute final scores for regulation scores: fail closed.
A separate validated regulation-goals source must supply those fields.
"""
import argparse
import csv
import os
from pathlib import Path
import psycopg


def export(conn, destination):
    sql = """
    SELECT game_id, game_date, season, team_name, opponent_name,
           home_away, score, opponent_score
    FROM sports.nhl_github_team_games
    WHERE home_away = 'home'
    ORDER BY game_date
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        games = cur.fetchall()
    p = Path(destination)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("game_id","date","season","home_team","away_team",
                         "final_home","final_away"))
        for gid,day,season,home,away,hg,ag in games:
            writer.writerow((gid,day.date().isoformat(),season,home,away,hg,ag))
    return len(games)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="data/hockey/neon_nhl_final_scores.csv")
    args=ap.parse_args()
    url=os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is missing; configure GitHub Actions secret")
    with psycopg.connect(url,connect_timeout=20) as conn:
        n=export(conn,args.out)
    print(f"Exported {n} completed NHL home-team score rows; regulation goals NOT available.")


if __name__=="__main__":
    main()
