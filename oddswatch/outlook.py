"""Ausblick je Sportart: Fußball, Eishockey Europa, NHL, NBA, NFL, Tennis.

Je Sportart: Spiele der nächsten Tage (davon mit handelbarem Preis),
Freigaben und die Märkte, die der spielbaren Mindestquote am nächsten sind.
Tennis kommt aus tennis_db (MongoDB Atlas) und ist nie freigegeben (INFO).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .report import _kick, _league, _pct, _q
from .selection import Candidate

SPORTS = [
    ("⚽", "Fußball", {"bundesliga", "2bundesliga", "austria", "ucl", "uel", "uecl", "nations",
                      "epl", "laliga", "seriea"}),
    ("🏒", "Eishockey Europa", {"del", "nl", "shl", "liiga", "khl", "icehl"}),
    ("🏒", "NHL", {"nhl"}),
    ("🏀", "NBA", {"nba"}),
    ("🏈", "NFL", {"nfl"}),
]


def _sport(league: str) -> str | None:
    return next((name for _, name, lgs in SPORTS if league in lgs), None)


def _ko(iso: str) -> datetime | None:
    try:
        return datetime.fromisoformat(iso).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def build(fixtures: list, candidates: list[Candidate], picks: list[Candidate],
          days: int = 7, now: datetime | None = None, top: int = 2) -> list[dict]:
    """Je Sportart: {icon, name, games, priced, leagues, picks, near}."""
    now = now or datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    picked = {(c.event, c.market) for c in picks}
    out = []
    for icon, name, lgs in SPORTS:
        fx = [f for f in fixtures if f.league in lgs and now < f.game.kickoff <= until]
        cs = [c for c in candidates if c.league in lgs and (k := _ko(c.kickoff)) and now < k <= until
              and (c.event, c.market) not in picked]
        # Mit Marktreferenz (DraftKings) zuerst; sonst nur Modell (z. B. Eishockey Europa)
        ref = [c for c in cs if c.p_ref is not None]
        near = sorted(ref or cs, key=lambda c: -c.ev)[:top]
        later = sorted(f.game.kickoff for f in fixtures if f.league in lgs and f.game.kickoff > until)
        out.append({"icon": icon, "name": name, "games": len(fx),
                    "priced": sum(bool(f.kalshi) for f in fx),
                    "leagues": sorted({_league(f.league) for f in fx}),
                    "picks": [c for c in picks if c.league in lgs], "near": near,
                    "model_only": bool(near) and not ref,
                    "next": (later[0], sum(k <= later[0] + timedelta(days=3) for k in later))
                    if later else None})
    return out


def _tennis(top: int = 2) -> tuple[list[str], list[str]]:
    """(Telegram-Zeilen, Bericht-Zeilen) für Tennis aus tennis_db."""
    from .sources import tennis_atlas
    from .tennis import _head, validated
    bets, tr, err = tennis_atlas.fetch()
    if err:
        msg = f"keine Daten ({err.split(':')[0]})"
        return [f"🎾 Tennis: {msg}"], [f"- 🎾 **Tennis**: {msg}"]
    tag = "KANDIDAT" if validated(tr) else "INFO, nicht freigegeben"
    head = f"🎾 Tennis: {len(bets)} offene Valuebet(s) des Runners ({tag})"
    tg, md = [head], [f"- 🎾 **Tennis**: {len(bets)} offene Valuebet(s) des Runners ({tag})"]
    for b in sorted(bets, key=lambda b: -b.ev)[:top]:
        line = f"{b.event} · {_head(b)}: {b.selection} @ {_q(b.odds)} (EV {_pct(b.ev)})"
        tg.append(f"   • {line}")
        md.append(f"  - {line}")
    return tg, md


def _near(c: Candidate, model_only: bool = False) -> str:
    return (f"{c.event} · {_kick(c.kickoff)}: {c.selection} @ {_q(c.odds)}, "
            f"spielbar ab {_q(c.min_odds)} (EV {_pct(c.ev)}{', nur Modell – nicht validiert' if model_only else ''})")


def _none(r: dict, days: int) -> str:
    if r["next"]:
        k, n = r["next"]
        return f"keine Spiele in {days} Tagen – nächster Spieltag ab {_kick(k.isoformat())} ({n} Spiele)"
    return f"keine Spiele in {days} Tagen"


def telegram_lines(rows: list[dict], days: int = 7, tennis: bool = True,
                   notes: list[str] | None = None) -> list[str]:
    out = ["", f"🔭 AUSBLICK NACH SPORTART (nächste {days} Tage)"]
    for r in rows:
        head = f"{r['icon']} {r['name']}: "
        if not r["games"]:
            out.append(head + _none(r, days))
            continue
        out.append(head + f"{r['games']} Spiele ({r['priced']} mit Kalshi-Preis), "
                   f"{len(r['picks'])} PLAY")
        out += [f"   • {_near(c, r['model_only'])}" for c in r["near"]]
    if tennis:
        out += _tennis()[0]
    out += [f"ℹ️ {n}" for n in notes or []]
    return out


def report_lines(rows: list[dict], days: int = 7, tennis: bool = True,
                 notes: list[str] | None = None) -> list[str]:
    out = ["", f"## Ausblick nach Sportart (nächste {days} Tage)", ""]
    for r in rows:
        if not r["games"]:
            out.append(f"- {r['icon']} **{r['name']}**: {_none(r, days)}")
            continue
        out.append(f"- {r['icon']} **{r['name']}** ({', '.join(r['leagues'])}): {r['games']} Spiele, "
                   f"{r['priced']} mit Kalshi-Preis, {len(r['picks'])} PLAY")
        out += [f"  - am nächsten an spielbar: {_near(c, r['model_only'])}" for c in r["near"]]
    if tennis:
        out += _tennis()[1]
    out += [f"- ℹ️ {n}" for n in notes or []]
    return out


def soccer_note(notes: list[str], issues: list[str] | None = None) -> list[str]:
    """Wichtige Hinweise aus dem Scan: Fußball-Sperre, NBA-Saisonstart, fehlende Daten."""
    out = []
    if any(n.startswith("Fußball: Freigaben ausgesetzt") for n in notes):
        out.append("Fußball: Freigaben ausgesetzt, bis der Backtest die Liga validiert – nur Watchlist")
    out += [n for n in notes if n.startswith("NBA:") and "Saisonstart" in n]
    issues = issues or []
    if any("eloratings" in i for i in issues):
        out.append("Nations League/Länderspiele nicht bewertet – Elo-Quelle (eloratings.net) nicht erreichbar")
    if any("ClubElo" in i for i in issues):
        out.append("Champions/Europa/Conference League nicht bewertet – ClubElo nicht erreichbar")
    return out
