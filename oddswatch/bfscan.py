"""Betfair-Scan: Betfair/Bet365 (über API-Football) gegen Pinnacle-fair.

Für alle Spiele der nächsten 7 Tage in den Fußball-Ligen unten: Pinnacle
(de-vigged je Markt) ist der faire Kurs, Betfair- und Bet365-Sportsbook sind
die spielbaren Preise. Märkte: 1X2, Über/Unter und Asian Handicap auf
halben Linien (x,5 – kein Push). Freigabe bei EV ≥ 3 % gegen Pinnacle-fair.

Hinweis: API-Football liefert das Betfair-*Sportsbook* (Marge 106–111 % im
1X2), nicht die Börse – Treffer sind daher selten und meist kurzlebig.

Journal-Referenz "AF:<Fixture-ID>:<Markt>"; Abrechnung über das API-Football-
Ergebnis, Closing Line = letzter Pinnacle-Snapshot vor Anstoß
(data/snapshots/apifootball-YYYY-MM.jsonl).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import pricing
from .journal import Journal
from .selection import Candidate, Offer, evaluate
from .sources import apifootball

# Liga -> API-Football-ID
LEAGUES = {"bundesliga": 78, "2bundesliga": 79, "austria": 218, "epl": 39, "laliga": 140,
           "seriea": 135, "ligue1": 61, "ucl": 2, "uel": 3, "uecl": 848, "nations": 5}
BOOKS = {4: "Pinnacle", 3: "Betfair", 8: "Bet365"}
PLAYABLE = ("Betfair", "Bet365")
MIN_EV = 0.03
SNAP = Path("data/snapshots")


def _season(d: date) -> int:
    return d.year if d.month >= 7 else d.year - 1


def _pages(path: str) -> tuple[list[dict], str | None]:
    out, page = [], 1
    while True:
        data, err = apifootball._get(f"{path}&page={page}")
        if data is None:
            return out, err
        out += data.get("response") or []
        total = (data.get("paging") or {}).get("total") or 1
        if page >= total:
            return out, None
        page += 1


def _market(bet: str, value: str) -> tuple[str, str, str] | None:
    """(Markt-Code, Gruppe, Beschriftung) oder None. Gruppe = gemeinsam de-viggen."""
    if bet == "Match Winner":
        k = {"Home": "home", "Draw": "draw", "Away": "away"}.get(value)
        return (k, "1x2", k) if k else None
    side, _, line = value.partition(" ")
    try:
        L = float(line)
    except ValueError:
        return None
    if abs(L * 2) % 2 != 1:                       # nur halbe Linien
        return None
    if bet == "Goals Over/Under" and side in ("Over", "Under"):
        return ((f"O{L:g}" if side == "Over" else f"U{L:g}"), f"ou{L:g}",
                f"{'Über' if side == 'Over' else 'Unter'} {L:g} Tore")
    if bet == "Asian Handicap" and side in ("Home", "Away"):
        # API-Football nennt bei beiden Seiten die Heim-Linie: "Away -0.5" = Gast +0,5
        own = L if side == "Home" else -L          # Linie aus Sicht der gewählten Seite
        return (f"AH{own:+g}:{side.lower()}", f"ah{L:+g}", f"{side} {own:+g}")
    return None


def parse(odds_rows: list[dict]) -> dict[int, dict[str, dict[str, tuple[float, str, str]]]]:
    """{Fixture: {Buchmacher: {Markt: (Quote, Gruppe, Beschriftung)}}}."""
    out: dict[int, dict] = {}
    for r in odds_rows:
        fid = int(r["fixture"]["id"])
        for b in r.get("bookmakers") or []:
            name = BOOKS.get(b.get("id"))
            if not name:
                continue
            mk = out.setdefault(fid, {}).setdefault(name, {})
            for bet in b.get("bets") or []:
                for v in bet.get("values") or []:
                    m = _market(bet.get("name", ""), str(v.get("value", "")))
                    try:
                        o = float(v.get("odd"))
                    except (TypeError, ValueError):
                        continue
                    if m and o > 1.0:
                        mk[m[0]] = (o, m[1], m[2])
    return out


def fair(pin: dict[str, tuple[float, str, str]]) -> dict[str, float]:
    """Pinnacle de-vigged je Gruppe (1X2 dreifach, Linien paarweise)."""
    groups: dict[str, list[str]] = {}
    for k, (_, g, _) in pin.items():
        groups.setdefault(g, []).append(k)
    out = {}
    for g, keys in groups.items():
        need = 3 if g == "1x2" else 2
        if len(keys) != need:
            continue
        ps = pricing.devig([pin[k][0] for k in keys])
        out.update(dict(zip(keys, ps)))
    return out


def _label(code: str, lab: str, home: str, away: str) -> str:
    if code in ("home", "away"):
        return f"{home if code == 'home' else away} Sieg (90 Min.)"
    if code == "draw":
        return "Unentschieden (90 Min.)"
    if code.startswith("AH"):
        side, line = lab.split(" ")
        return f"{home if side == 'Home' else away} {line} (Asian Handicap)"
    return lab


def scan(now: datetime | None = None, days: int = 7, leagues: dict[str, int] | None = None
         ) -> tuple[list[Candidate], list[dict], list[str]]:
    """Kandidaten, Pinnacle-Snapshots (für CLV), Hinweise."""
    now = now or datetime.now(timezone.utc)
    season = _season(now.date())
    frm, to = now.date().isoformat(), (now.date() + timedelta(days=days)).isoformat()
    cands, snaps, issues = [], [], []
    for lg, lid in (leagues or LEAGUES).items():
        data, err = apifootball._get(f"/fixtures?league={lid}&season={season}&from={frm}&to={to}"
                                     "&timezone=UTC")           # /fixtures kennt kein page
        fx = (data or {}).get("response") or []
        if err:
            issues.append(f"{lg}: {err}")
            continue
        info = {int(f["fixture"]["id"]): f for f in fx
                if (f["fixture"].get("status") or {}).get("short") in ("NS", "TBD")}
        if not info:
            continue
        rows = []
        for bid in BOOKS:
            r, err = _pages(f"/odds?league={lid}&season={season}&bookmaker={bid}")
            rows += r
            if err:
                issues.append(f"{lg} {BOOKS[bid]}: {err}")
        books = parse(rows)
        for fid, f in info.items():
            b = books.get(fid, {})
            if "Pinnacle" not in b:
                continue
            p = fair(b["Pinnacle"])
            home, away = f["teams"]["home"]["name"], f["teams"]["away"]["name"]
            ko = datetime.fromisoformat(f["fixture"]["date"])
            event = f"{home} – {away}"
            for code, pf in p.items():
                snaps.append({"ref": f"AF:{fid}:{code}", "p_fair": pf, "kickoff": ko.isoformat(),
                              "observed_at": now.isoformat(timespec="seconds")})
                for book in PLAYABLE:
                    if code not in b.get(book, {}):
                        continue
                    odds, _, lab = b[book][code]
                    off = Offer(event, ko.isoformat(timespec="minutes"), code,
                                _label(code, lab, home, away), odds, book.lower(),
                                now.isoformat(timespec="seconds"), ref=f"AF:{fid}:{code}", league=lg)
                    reason = (f"{book} {odds:.2f} gegen Pinnacle-fair {1 / pf:.2f} "
                              f"({pf * 100:.1f} %, de-vigged). Reiner Preisvergleich, API-Football.")
                    c = evaluate(off, pf, reason=reason, p_ref=pf, p_final=pf)
                    cands.append(c)
    return cands, snaps, issues


def save_snapshots(snaps: list[dict], refs: set[str], now: datetime) -> None:
    """Pinnacle-fair nur für Märkte offener Tipps sichern (Closing Line)."""
    rows = [s for s in snaps if s["ref"] in refs]
    if not rows:
        return
    SNAP.mkdir(parents=True, exist_ok=True)
    with (SNAP / f"apifootball-{now:%Y-%m}.jsonl").open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def closing_fair_odds(ref: str, root: Path = SNAP) -> float | None:
    last = None
    for p in sorted(root.glob("apifootball-*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r["ref"] == ref and r["observed_at"] <= r["kickoff"]:
                if last is None or r["observed_at"] > last["observed_at"]:
                    last = r
    return 1 / last["p_fair"] if last and last["p_fair"] > 0 else None


def won(market: str, hg: int, ag: int) -> bool:
    if market in ("home", "draw", "away"):
        return {"home": hg > ag, "draw": hg == ag, "away": hg < ag}[market]
    if market.startswith("O"):
        return hg + ag > float(market[1:])
    if market.startswith("U"):
        return hg + ag < float(market[1:])
    if market.startswith("AH"):
        line, _, side = market[2:].partition(":")
        L = float(line)
        return hg + L > ag if side == "home" else ag + L > hg
    raise ValueError(market)


def settle(j: Journal, now: datetime | None = None) -> list[str]:
    """Offene AF-Tipps (valuebets/placed) über das API-Football-Ergebnis abrechnen
    (erst ab 110 Minuten nach Anstoß abgefragt)."""
    now = now or datetime.now(timezone.utc)
    log = []
    for name in ("valuebets", "placed"):
        done: set[str] = set()
        for r in j.read(name):
            ref = r.get("ref", "")
            if r.get("result") or not ref.startswith("AF:") or ref in done:
                continue
            done.add(ref)
            try:
                if datetime.fromisoformat(r["kickoff"]) + timedelta(minutes=110) > now:
                    continue
            except (KeyError, ValueError):
                pass
            fid = ref.split(":")[1]
            data, err = apifootball._get(f"/fixtures?id={fid}")
            f = ((data or {}).get("response") or [None])[0]
            if not f:
                log.append(f"{name}: {r['event']} – Abruf fehlgeschlagen ({err})")
                continue
            if (f["fixture"].get("status") or {}).get("short") not in ("FT", "AET", "PEN"):
                continue
            ft = (f.get("score") or {}).get("fulltime") or {}
            hg, ag = ft.get("home"), ft.get("away")
            if hg is None or ag is None:
                continue
            w = won(r["market"], int(hg), int(ag))
            n = j.settle(name, r["event"], r["market"], w, closing_fair_odds(ref), ref=ref)
            log.append(f"{name}: {r['event']} {r['selection']} {hg}:{ag} -> "
                       f"{'Gewinn' if w else 'Verlust'} ({n} Zeile/n)")
    return log


def open_refs(j: Journal) -> set[str]:
    return {r["ref"] for n in ("valuebets", "placed") for r in j.read(n)
            if not r.get("result") and r.get("ref", "").startswith("AF:")}
