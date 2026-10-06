"""Hockey-Datenbackfill und Qualitätsaudit.

Ziel:
- nur Top-Liga-Spiele (keine DEL2/Mestis/Alps/I. liga)
- mehrere Saisonen historischer 60-Minuten-Ergebnisse
- NHL aus offizieller NHL-API
- Europa aus hockeyarchives, laufende Liiga/ICEHL bevorzugt aus offiziellen Feeds
- Markt-/Closing-Abdeckung separat aus data/hockey/market/*.csv prüfen

Dieser Audit entscheidet NICHT über Value/Freigabe. Er beantwortet nur:
"Haben wir genug saubere Trainings-/Validierungsdaten und wie groß ist die
Closing-Line-Abdeckung für CLV?"
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .sources import hockeyarchives, nhl

FOCUS = ("nhl", "del", "icehl", "liiga", "extraliga")
DATA_DIR = Path("data/hockey")
MARKET_DIR = DATA_DIR / "market"
HISTORY_FILE = DATA_DIR / "history.csv"
AUDIT_FILE = DATA_DIR / "data_audit.json"

# Rein als Datenqualitäts-Ziele, nicht als Betting-Release-Gate.
MIN_HISTORY_GAMES = 900
MIN_COMPLETE_SEASONS = 3
MIN_MARKET_GAMES = 300

_MARKET_ALIASES = {
    "NHL": "nhl",
    "DEL": "del",
    "ICEHL": "icehl",
    "LIIGA": "liiga",
    "CZE_EXTRALIGA": "extraliga",
    "EXTRALIGA": "extraliga",
}


def _season_start(today: date | None = None) -> int:
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def _season_label(start: int) -> str:
    return f"{start}/{str(start + 1)[-2:]}"


def _row(league: str, season: int, r, source: str) -> dict:
    return {
        "league": league,
        "season": _season_label(season),
        "date": r.date.isoformat(),
        "home_team": r.home,
        "away_team": r.away,
        "reg_home": int(r.reg_home),
        "reg_away": int(r.reg_away),
        "extra": r.extra or "",
        "source": source,
    }


def _dedupe(rows: list[dict]) -> list[dict]:
    # Gleicher Tag/Teams = gleiches Spiel. Offizieller Feed hat Vorrang.
    priority = {"nhl-api": 3, "icehl-api": 3, "liiga-api": 3, "hockeyarchives": 1}
    out: dict[tuple, dict] = {}
    for r in rows:
        k = (r["league"], r["date"], r["home_team"], r["away_team"])
        old = out.get(k)
        if old is None or priority.get(r["source"], 0) >= priority.get(old["source"], 0):
            out[k] = r
    return sorted(out.values(), key=lambda r: (r["league"], r["date"], r["home_team"], r["away_team"]))


def _eu_history(league: str, first: int, current: int, issues: list[str]) -> list[dict]:
    rows: list[dict] = []
    for season in range(first, current + 1):
        # Laufende Liiga/ICEHL: offizielle Feeds bevorzugen.
        if season == current and league == "liiga":
            done, _, err = hockeyarchives.liiga(season + 1)
            if err:
                issues.append(f"liiga-api {season}: {err}")
            else:
                rows += [_row(league, season, r, "liiga-api") for r in done]
                continue
        if season == current and league == "icehl":
            done, _, err = hockeyarchives.icehl(season)
            if err:
                issues.append(f"icehl-api {season}: {err}")
            else:
                for r in done:
                    r.home = hockeyarchives.canonical_icehl(r.home)
                    r.away = hockeyarchives.canonical_icehl(r.away)
                rows += [_row(league, season, r, "icehl-api") for r in done]
                continue

        done, err = hockeyarchives.season_results(
            league, season, cache_days=30.0 if season < current else 0.5
        )
        if err:
            issues.append(f"hockeyarchives {league} {season}: {err}")
            continue
        rows += [_row(league, season, r, "hockeyarchives") for r in done]
    return rows


def _nhl_history(first: int, current: int, issues: list[str]) -> list[dict]:
    rows: list[dict] = []
    for season in range(first, current + 1):
        season_id = f"{season}{season + 1}"
        games, _, errs = nhl.season_games(
            season_id, cache_days=30.0 if season < current else 0.0
        )
        issues += [f"nhl {season_id}: {e}" for e in errs[:3]]
        for g in games:
            # NHL-Quelle liefert nach Shootout bereinigten Endstand;
            # für Trainingszwecke hier als 60/OT-Ergebnis ohne SO-Bonustor.
            class R:
                pass
            r = R()
            r.date, r.home, r.away = g.date, g.home, g.away
            r.reg_home, r.reg_away = int(g.home_goals), int(g.away_goals)
            r.extra = ""
            rows.append(_row("nhl", season, r, "nhl-api"))
    return rows


def collect_history(seasons: int = 5, today: date | None = None) -> tuple[list[dict], list[str]]:
    current = _season_start(today)
    first = current - max(1, seasons) + 1
    issues: list[str] = []
    rows = _nhl_history(first, current, issues)
    for lg in ("del", "icehl", "liiga", "extraliga"):
        rows += _eu_history(lg, first, current, issues)
    return _dedupe(rows), issues


def _read_market_rows() -> list[dict]:
    rows: list[dict] = []
    if not MARKET_DIR.exists():
        return rows
    for p in sorted(MARKET_DIR.glob("*.csv")):
        try:
            with p.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    raw = (r.get("league") or "").strip()
                    lg = _MARKET_ALIASES.get(raw.upper(), raw.lower())
                    if lg not in FOCUS:
                        continue
                    # Mindestens eine echte Closing-Quote muss vorhanden sein.
                    closes = [r.get("close_home"), r.get("close_draw"), r.get("close_away")]
                    if not any(str(x or "").strip() for x in closes):
                        continue
                    rows.append({"league": lg, "date": r.get("date", ""), "file": p.name})
        except (OSError, csv.Error):
            continue
    # Spiel-Dedupe über Liga+Datum+Quelldatei ist absichtlich konservativ;
    # unterschiedliche Dateien dürfen erst nach Match-Normalisierung zusammengeführt werden.
    return rows


def audit(rows: list[dict], issues: list[str] | None = None) -> dict:
    issues = issues or []
    current = _season_label(_season_start())
    market = _read_market_rows()
    out = {
        "generated_for_season": current,
        "targets": {
            "history_games": MIN_HISTORY_GAMES,
            "complete_seasons": MIN_COMPLETE_SEASONS,
            "market_closing_games": MIN_MARKET_GAMES,
        },
        "leagues": {},
        "issues": issues,
    }
    for lg in FOCUS:
        xs = [r for r in rows if r["league"] == lg]
        seasons: dict[str, int] = {}
        teams: set[str] = set()
        for r in xs:
            seasons[r["season"]] = seasons.get(r["season"], 0) + 1
            teams.update((r["home_team"], r["away_team"]))
        # Eine Saison mit >=200 Top-Liga-Spielen zählt als substantiell vollständig.
        complete = sum(n >= 200 for n in seasons.values())
        m = [r for r in market if r["league"] == lg]
        out["leagues"][lg] = {
            "history_games": len(xs),
            "seasons": seasons,
            "substantial_seasons": complete,
            "teams": len(teams),
            "date_from": min((r["date"] for r in xs), default=None),
            "date_to": max((r["date"] for r in xs), default=None),
            "training_data_ready": len(xs) >= MIN_HISTORY_GAMES and complete >= MIN_COMPLETE_SEASONS,
            "market_closing_rows": len(m),
            "market_data_ready": len(m) >= MIN_MARKET_GAMES,
        }
    return out


def save(rows: list[dict], result: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MARKET_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "league", "season", "date", "home_team", "away_team",
        "reg_home", "reg_away", "extra", "source",
    ]
    with HISTORY_FILE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    AUDIT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(seasons: int = 5) -> list[str]:
    rows, issues = collect_history(seasons=seasons)
    result = audit(rows, issues)
    save(rows, result)
    lines = [f"Hockey-Datenaudit: {len(rows)} saubere Top-Liga-Spiele über bis zu {seasons} Saisonen"]
    for lg in FOCUS:
        r = result["leagues"][lg]
        lines.append(
            f"{lg.upper()}: history={r['history_games']}, substantial_seasons={r['substantial_seasons']}, "
            f"market_closing={r['market_closing_rows']} | "
            f"training={'OK' if r['training_data_ready'] else 'FEHLT'} | "
            f"market={'OK' if r['market_data_ready'] else 'FEHLT'}"
        )
    if issues:
        lines.append(f"Quellenhinweise: {len(issues)}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
