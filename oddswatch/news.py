"""News-Agent: scannt Sportseiten zu allen Freigaben und Watchlist-Spielen,
erkennt materielle Meldungen (Ausfälle, Sperren, Rückkehr, Trainerwechsel),
prüft sie gegen eine zweite Quelle und warnt den CEO per Telegram.

Der Agent zieht keine Freigabe selbst zurück – er warnt, der CEO entscheidet.
Gemeldete Artikel werden in data/journal/news_seen.txt vermerkt (keine
Wiederholungen), alle Treffer in data/journal/news.csv protokolliert.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from . import fetch
from .journal import Journal
from .report import _kick, _league, _q

ESPN = "https://site.api.espn.com/apis/site/v2/sports"

# Liga -> [(Quellenname, URL, Format)]
SOURCES: dict[str, list[tuple[str, str, str]]] = {
    "nfl": [("ESPN", f"{ESPN}/football/nfl/news?limit=100", "espn"),
            ("CBS Sports", "https://www.cbssports.com/rss/headlines/nfl/", "rss"),
            ("RotoWire", "https://www.rotowire.com/rss/news.php?sport=NFL", "rss")],
    "nba": [("ESPN", f"{ESPN}/basketball/nba/news?limit=100", "espn"),
            ("CBS Sports", "https://www.cbssports.com/rss/headlines/nba/", "rss"),
            ("RotoWire", "https://www.rotowire.com/rss/news.php?sport=NBA", "rss")],
    "nhl": [("ESPN", f"{ESPN}/hockey/nhl/news?limit=100", "espn"),
            ("NHL.com", "https://www.nhl.com/rss/news", "rss"),
            ("RotoWire", "https://www.rotowire.com/rss/news.php?sport=NHL", "rss")],
    "bundesliga": [("ESPN", f"{ESPN}/soccer/ger.1/news?limit=100", "espn"),
                   ("kicker", "https://newsfeed.kicker.de/news/bundesliga", "rss"),
                   ("Sportschau", "https://www.sportschau.de/fussball/bundesliga/index~rss2.xml", "rss")],
    "2bundesliga": [("ESPN", f"{ESPN}/soccer/ger.2/news?limit=100", "espn"),
                    ("kicker", "https://newsfeed.kicker.de/news/2-bundesliga", "rss")],
    "nations": [("ESPN", f"{ESPN}/soccer/uefa.nations/news?limit=100", "espn"),
                ("kicker", "https://newsfeed.kicker.de/news/nationalmannschaft", "rss")],
    "ucl": [("ESPN", f"{ESPN}/soccer/uefa.champions/news?limit=100", "espn"),
            ("kicker", "https://newsfeed.kicker.de/news/champions-league", "rss")],
    "uel": [("ESPN", f"{ESPN}/soccer/uefa.europa/news?limit=100", "espn"),
            ("kicker", "https://newsfeed.kicker.de/news/europa-league", "rss")],
    "uecl": [("ESPN", f"{ESPN}/soccer/uefa.europa.conf/news?limit=100", "espn")],
    "austria": [("ORF", "https://rss.orf.at/sport.xml", "rss"),
                ("derStandard", "https://www.derstandard.at/rss/sport", "rss"),
                ("abseits.at", "https://abseits.at/feed/", "rss"),
                ("Austrian Soccer Board", "https://www.austriansoccerboard.at/discover/all.xml", "rss")],
}
# Quellen, deren Titel oft nur den Spieler nennen – Teamname im Text genügt
TEXT_MATCH = {"RotoWire", "Austrian Soccer Board"}
# Foren liefern frühe Hinweise, zählen aber nie als Bestätigung
FORUMS = {"Austrian Soccer Board"}

# (Muster, Kategorie, schwer?) – Reihenfolge = Priorität
MATERIAL = [
    (r"\btraded?\b|trades for|acquires?|acquired|waived|released by|signs with|verpflichtet"
     r"|wechselt (zu|nach)|transfer", "Trade/Wechsel", False),
    (r"ruled out|out for (the )?(season|year|weeks?|game)|season-ending|torn|surgery|fractur"
     r"|injured reserve|placed on IR|will miss|to miss|won'?t play|will not play|sidelined",
     "Ausfall", True),
    (r"kreuzband|fällt (\w+ )?aus|fehlt (\w+ )?(wochen|monate|mehrere)|muskelfaser|operiert"
     r"|bruch|saisonaus|verletzungsbedingt", "Ausfall", True),
    (r"suspend|ejected|banned|gesperrt|sperre|rote karte|platzverweis", "Sperre", True),
    (r"\bfired\b|dismissed|parted ways|interim (head )?coach|entlassen|freigestellt"
     r"|beurlaubt|trainerwechsel|neuer trainer", "Trainerwechsel", True),
    (r"questionable|doubtful|day-to-day|game-time decision|limited in practice|did not practice"
     r"|\bDNP\b|fraglich|angeschlagen|wackelt|einsatz (ist )?offen", "fraglich", False),
    (r"activated|returns?\b|return to|back in (the )?lineup|(will|to|expected to) start|named (the )?starter|clear(ed|ing|s)\b"
     r"|comeback|rückkehr|kehrt zurück|wieder (fit|im training|dabei)|einsatzbereit",
     "Rückkehr/Startelf", False),
    (r"concussion|injur|hamstring|ankle|knee|illness|verletz|erkrankt|krank", "Verletzung", False),
    (r"\brest(ed|ing)?\b|load management|rotation|geschont|rotiert", "Schonung", False),
]


@dataclass
class Item:
    source: str
    league: str
    title: str
    text: str
    link: str
    published: datetime | None
    teams: list[str] = field(default_factory=list)   # ESPN-Kategorien

    @property
    def uid(self) -> str:
        return hashlib.sha1((self.link or self.title).encode()).hexdigest()[:16]


@dataclass
class Target:
    """Ein Spiel mit Freigabe oder Watchlist-Eintrag."""
    status: str            # PLAY / WATCH
    league: str
    event: str
    kickoff: str
    market: str
    selection: str
    odds: float
    fair: float
    min_odds: float
    home: list[str]
    away: list[str]


@dataclass
class Alert:
    target: Target
    side: str              # home / away
    team: str
    item: Item
    category: str
    severe: bool
    confirmed_by: list[str]
    names: set[str] = field(default_factory=set)


# ---------------------------------------------------------------- Parsing
def _parse_date(s: str) -> datetime | None:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    # RotoWire: "Mon, 28 Sep 2026 11:24:00 AM PDT"
    m = re.match(r"\w+, (\d+ \w+ \d{4}) (\d+):(\d+):(\d+) (AM|PM) (\w+)", s)
    if m:
        h = int(m.group(2)) % 12 + (12 if m.group(5) == "PM" else 0)
        off = {"PDT": -7, "PST": -8, "MDT": -6, "MST": -7, "CDT": -5, "CST": -6,
               "EDT": -4, "EST": -5}.get(m.group(6), 0)
        d = datetime.strptime(m.group(1), "%d %b %Y").replace(
            hour=h, minute=int(m.group(3)), tzinfo=timezone(timedelta(hours=off)))
        return d
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        pass
    return None


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()


def parse_rss(xml: str, source: str, league: str) -> list[Item]:
    try:
        root = ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    except ET.ParseError:
        return []
    out = []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        f = {c.tag.rsplit("}", 1)[-1]: c for c in el}
        link = f.get("link")
        href = (link.get("href") or link.text or "") if link is not None else ""
        txt = lambda k: (f[k].text or "") if k in f else ""
        out.append(Item(source, league, _strip(txt("title")),
                        _strip(txt("description") or txt("summary") or txt("encoded")),
                        href.strip(), _parse_date(txt("pubDate") or txt("published")
                                                  or txt("updated") or txt("date"))))
    return out


def parse_espn(data: dict, source: str, league: str) -> list[Item]:
    out = []
    for a in data.get("articles", []):
        teams = [c.get("description", "") for c in a.get("categories", [])
                 if c.get("type") == "team"]
        link = ((a.get("links") or {}).get("web") or {}).get("href", "")
        out.append(Item(source, league, a.get("headline", ""), a.get("description", ""),
                        link, _parse_date(a.get("published", "")), teams))
    return out


def collect(leagues: set[str], issues: list[str]) -> list[Item]:
    items = []
    for lg in leagues:
        for name, url, fmt in SOURCES.get(lg, []):
            if fmt == "espn":
                d, err = fetch.get_json(url, cache_days=0)
                items += parse_espn(d, name, lg) if d else []
            else:
                t, err = fetch.get(url, cache_days=0)
                items += parse_rss(t, name, lg) if t else []
            if err:
                issues.append(f"{name} ({_league(lg)}): {err}")
    return items


# ---------------------------------------------------------------- Bewertung
def classify(title: str, text: str = "") -> tuple[str, bool] | None:
    """Kategorie aus dem Titel, ersatzweise aus dem Text – aus dem Text nur schwere
    Kategorien (sonst zu viele Zufallstreffer). QB-Themen sind schwer."""
    for part in (title, text):
        for pat, cat, severe in MATERIAL:
            if part is text and not severe:
                continue
            if part and re.search(pat, part, re.I):
                qb = re.search(r"\bQB\b|quarterback", title, re.I)
                return cat, severe or bool(qb and cat != "Schonung")
    return None


def _in(text: str, aliases: list[str]) -> bool:
    return any(len(a) >= 4 and re.search(rf"(?<!\w){re.escape(a)}(?!\w)", text, re.I)
               for a in aliases)


# Ortsnamen mehrerer Teams einer Liga – kein eindeutiger Alias
AMBIGUOUS = {"new york", "los angeles", "la", "ny", "nyc"}
# "loss to the Vikings", "win over Detroit": dort ist das Team nur Gegner
_OPPONENT = re.compile(r"\b(loss|losses|lose|losing|lost|win|wins|won|victory|defeat\w*|rout\w*"
                       r"|game|matchup|clash)\s+(to|over|against|vs\.?|at|with)\s+(the\s+)?"
                       r"[\w'.-]+(\s+[A-Z][\w'.-]+)?", re.I)


def _mentions(item: Item, aliases: list[str]) -> bool:
    """Team ist Hauptthema: im Titel genannt (nicht nur als Gegner) bzw. unter den
    ESPN-Teamkategorien. Sammelartikel (> 2 Teams als Kategorie) zählen nicht."""
    aliases = [a for a in aliases if a.lower() not in AMBIGUOUS]
    if len(item.teams) > 2:
        return False
    if item.teams:
        # ESPN ordnet Artikel Teams zu – ist das Team nicht dabei, geht es nicht um es
        return any(t.lower() == a.lower() for t in item.teams for a in aliases)
    if _in(_OPPONENT.sub(" ", item.title), aliases):
        return True
    # Feeds ohne Teamangabe im Titel (z. B. RotoWire "Spieler: Notiz"): Text, falls keine Kategorien
    return not item.teams and item.source in TEXT_MATCH and _in(item.text, aliases)


_STOP = {"sources", "source", "report", "reports", "latest", "breaking", "grades", "grading",
         "trade", "trades", "deadline", "updates", "update", "news", "week", "what", "when",
         "why", "how", "who", "will", "after", "could", "should", "with", "from", "into",
         "this", "that", "their", "season", "game", "games", "injury", "status", "notes",
         "live", "odds", "picks", "preview", "takeaways", "power", "rankings", "nach", "gegen",
         "auch", "sich", "ohne", "über", "trainer", "verletzung", "saison", "spiel", "bundesliga"}


def _names(item: Item, aliases: list[str]) -> set[str]:
    """Eigennamen (Spieler/Trainer) aus dem Titel, ohne Teamnamen und Füllwörter."""
    team_words = {w.lower() for a in aliases for w in a.split()}
    words = re.findall(r"\b[A-ZÄÖÜ][\wäöüßé'-]{3,}\b", item.title)
    return {w.rstrip("'s").rstrip("'") for w in words
            if w.lower() not in team_words and w.lower().rstrip("'s") not in _STOP}


def story_keys(event: str, names: set[str]) -> set[str]:
    """Eine Geschichte = Spiel + Person. Weitere Artikel dazu sind keine Neuigkeit."""
    return {"story:" + hashlib.sha1(f"{event}|{n.lower()}".encode()).hexdigest()[:12]
            for n in names}


def find_alerts(targets: list[Target], items: list[Item], seen: set[str],
                now: datetime, max_age_h: int = 72) -> list[Alert]:
    alerts = []
    for t in targets:
        try:
            ko = datetime.fromisoformat(t.kickoff)
        except ValueError:
            ko = now + timedelta(days=14)
        if ko <= now:
            continue
        for side, aliases in (("home", t.home), ("away", t.away)):
            rel = [i for i in items if i.league == t.league and _mentions(i, aliases)
                   and (i.published is None or now - timedelta(hours=max_age_h) <= i.published <= ko)]
            for it in rel:
                if it.uid in seen:
                    continue
                c = classify(it.title, it.text)
                if not c:
                    continue
                names = _names(it, aliases)
                conf = sorted({o.source for o in rel if o.source != it.source
                               and o.source not in FORUMS and classify(o.title, o.text)
                               and (not names or names & _names(o, aliases))})
                alerts.append(Alert(t, side, aliases[0], it, c[0], c[1], conf, names))
    # je Spiel nur ein Artikel pro Geschichte (Person) – auch über Läufe hinweg;
    # bevorzugt schwer, bestätigt, früh veröffentlicht
    alerts.sort(key=lambda a: (not a.severe, not a.confirmed_by,
                               a.item.published or now))
    out, taken = [], set(seen)
    for a in alerts:
        keys = story_keys(a.target.event, a.names) | {f"{a.target.event}|{a.item.uid}"}
        if keys & taken:
            continue
        taken |= keys
        out.append(a)
    return sorted(out, key=lambda a: (not a.severe, a.target.status != "PLAY", a.target.kickoff))


def alert_text(alerts: list[Alert], stand: str) -> str:
    out = [f"🚨 NEWS-AGENT {stand}", "Nur Warnung – Entscheidung beim CEO."]
    for a in alerts:
        t = a.target
        own = (t.market == a.side)
        icon = "✅ PLAY" if t.status == "PLAY" else "👀 WATCH"
        pub = f", {_kick(a.item.published.isoformat())}" if a.item.published else ""
        out += ["", f"{'🔴' if a.severe else '🟡'} {a.category.upper()} · {_league(t.league)} · {_kick(t.kickoff)}",
                f"🆚 {t.event}",
                f"{icon}: {t.selection} @ {_q(t.odds)} | fair {_q(t.fair)} | min {_q(t.min_odds)}",
                f"📰 {a.item.title} ({a.item.source}{pub})"]
        if a.item.text and a.item.text != a.item.title:
            out.append(f"   {a.item.text[:220]}")
        if a.item.source in FORUMS:
            out.append("💬 Forum-Hinweis" + (" – bestätigt: " + ", ".join(a.confirmed_by)
                                             if a.confirmed_by else " – Gerücht, unbestätigt"))
        else:
            out.append("✔️ bestätigt: " + ", ".join(a.confirmed_by) if a.confirmed_by
                       else "⚠️ nur eine Quelle – unbestätigt")
        if own and t.status == "PLAY":
            rec = ("Freigabe prüfen/aussetzen – Ausfall ist im Modell nicht enthalten"
                   if a.category in ("Ausfall", "Sperre", "Trainerwechsel", "fraglich", "Verletzung", "Schonung")
                   else "positiv für den Tipp – Preis kann anziehen, Einstieg prüfen")
        elif t.status == "PLAY":
            rec = ("Gegner geschwächt – Tipp gestützt, Preis kann sich verschieben"
                   if a.category not in ("Rückkehr/Startelf",) else "Gegner gestärkt – Freigabe prüfen")
        else:
            rec = "Watchlist neu bewerten"
        out.append(f"➡️ {rec} (betrifft {a.team})")
        if a.item.link:
            out.append(f"🔗 {a.item.link}")
    return "\n".join(out)


# ---------------------------------------------------------------- Zustand
WATCH_FILE = Path("data/journal/watchlist.json")
SEEN_FILE = Path("data/journal/news_seen.txt")


def save_targets(fixtures: list, picks: list, watch: list, path: Path = WATCH_FILE) -> None:
    """Nach jedem Scan: Freigaben und Watchlist mit Team-Aliassen sichern."""
    by_title = {fx.game.title: fx for fx in fixtures}
    rows = []
    for status, cs in (("PLAY", picks), ("WATCH", watch)):
        for c in cs:
            fx = by_title.get(c.event)
            if not fx:
                continue
            rows.append({"status": status, "league": c.league, "event": c.event,
                         "kickoff": c.kickoff, "market": c.market, "selection": c.selection,
                         "odds": c.odds, "fair": c.fair_odds, "min_odds": c.min_odds,
                         "home": fx.game.home.aliases(), "away": fx.game.away.aliases()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def load_targets(j: Journal, path: Path = WATCH_FILE) -> list[Target]:
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    known = {(r["event"], r["market"]) for r in rows}
    # offene Freigaben früherer Scans ergänzen (Aliasse aus dem Spieltitel)
    for r in j.read("valuebets"):
        if r.get("result") or (r["event"], r["market"]) in known:
            continue
        h, _, a = r["event"].partition(" – ")
        rows.append({"status": "PLAY", "league": r["league"], "event": r["event"],
                     "kickoff": r["kickoff"], "market": r["market"], "selection": r["selection"],
                     "odds": float(r["odds"]), "fair": float(r["fair_odds"]),
                     "min_odds": float(r["min_odds"]), "home": [h, h.split()[-1]],
                     "away": [a, a.split()[-1]]})
        known.add((r["event"], r["market"]))
    return [Target(**{k: r[k] for k in Target.__dataclass_fields__}) for r in rows]


def run(j: Journal, now: datetime | None = None) -> tuple[list[Alert], list[str], int]:
    now = now or datetime.now(timezone.utc)
    issues: list[str] = []
    targets = load_targets(j)
    items = collect({t.league for t in targets}, issues)
    seen = set(SEEN_FILE.read_text().split()) if SEEN_FILE.exists() else set()
    return find_alerts(targets, items, seen, now), issues, len(items)


def seen_keys(alerts: list[Alert]) -> set[str]:
    """Artikel-IDs und Geschichten-Schlüssel gemeldeter Warnungen."""
    return {a.item.uid for a in alerts}.union(
        *(story_keys(a.target.event, a.names) for a in alerts))


def mark_seen(alerts: list[Alert], j: Journal) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with SEEN_FILE.open("a") as f:
        for k in sorted(seen_keys(alerts)):
            f.write(k + "\n")
    j.append("news", [{"published": a.item.published.isoformat() if a.item.published else "",
                       "league": a.target.league, "event": a.target.event,
                       "status": a.target.status, "team": a.team, "side": a.side,
                       "category": a.category, "severe": a.severe, "source": a.item.source,
                       "confirmed_by": "; ".join(a.confirmed_by), "title": a.item.title,
                       "link": a.item.link} for a in alerts])
