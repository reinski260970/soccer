"""Belastung: Ruhezeit, Reiseweg, Zeitzonen, Höhe und (NFL) Klimawechsel.

Merkmale je Team und Spiel (aus dem Spielplan, Ergebnis nicht nötig):
  short     kurze Pause (NBA/NHL: Back-to-back, NFL: ≤ 5 Tage, z. B. TNF)
  long      lange Pause (NBA/NHL: ≥ 3 Tage, NFL: ≥ 10 Tage, z. B. Bye)
  travel    Reiseweg seit dem letzten Spielort in 1000 km
  tz        Zeitzonen-Abstand des Spielorts zur Heimat in Stunden (Körperuhr)
  altitude  Spiel ≥ 1000 m ü. NN für ein Team aus dem Flachland (Denver, Utah, Calgary)
  climate   NFL: Team aus Halle/Süden (< 34° N) im Freien bei ≥ 39° N, Nov–Feb
  zone      Klimazone des Spielorts ≠ Klimazone der Heimat (alle Ligen)

Die Wirkung wird nicht angenommen, sondern geschätzt: Ridge-Regression der
Marge-Residuen des Stärkemodells auf die Merkmalsdifferenz Heim − Gast.
Der Ridge-Term zieht schwach belegte Effekte Richtung 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone

from .. import venues as V

FEATURES = ("short", "long", "travel", "tz", "altitude", "climate", "zone")
LABELS = {"short": "kurze Pause", "long": "lange Pause", "travel": "Reise/1000 km",
          "tz": "Zeitzonen-Std.", "altitude": "Höhe", "climate": "Kälte (NFL)",
          "zone": "Klimazonenwechsel"}
_REST = {"nba": (1, 3), "nhl": (1, 3), "nfl": (5, 10)}
_SEASON_GAP = 30  # Tage: danach startet ein Team wieder vom Heimort (neue Saison)


@dataclass
class Slot:
    day: date           # Ortsdatum des Spiels
    home: str
    away: str
    neutral: bool = False


@dataclass
class TeamLoad:
    rest: int | None
    km: float
    tz: float
    feats: dict[str, float]
    zones: tuple[str, str] = ("", "")   # Heimat, Spielort
    at_home: bool = False

    def text(self) -> str:
        r = "Saisonstart" if self.rest is None else f"{self.rest} T Pause"
        out = [r]
        if self.km and self.at_home:
            out.append(f"Heimspiel nach Rückreise {self.km:.0f} km")
        elif self.km:
            out.append(f"Anreise {self.km:.0f} km ≈ {V.travel_hours(self.km):.1f} h".replace(".", ","))
        elif self.at_home:
            out.append("Heimspiel")
        if self.tz:
            out.append(f"Zeitzone {self.tz:+.0f} h")
        if self.feats.get("zone"):
            out.append(f"Klima {self.zones[0]} → {self.zones[1]}")
        out += [LABELS[k] for k in ("altitude", "climate") if self.feats.get(k)]
        return ", ".join(out)


def local_day(kickoff: datetime, venue: V.Venue | None) -> date:
    from zoneinfo import ZoneInfo
    return kickoff.astimezone(ZoneInfo(venue.tz)).date() if venue else kickoff.date()


def _noon(d: date) -> datetime:
    return datetime.combine(d, time(12), tzinfo=timezone.utc)


def team_load(sport: str, team: str, day: date, venue: V.Venue | None,
              last: tuple[date, V.Venue | None] | None) -> TeamLoad:
    table = V.LEAGUES[sport]
    home = table.get(team)
    short_max, long_min = _REST[sport]
    rest = (day - last[0]).days if last else None
    if rest is not None and rest > _SEASON_GAP:
        rest, last = None, None
    prev = (last[1] if last else None) or home
    f = dict.fromkeys(FEATURES, 0.0)
    km = tz = 0.0
    zones = ("", "")
    if rest is not None:
        f["short"] = float(rest <= short_max)
        f["long"] = float(rest >= long_min)
    else:
        f["long"] = 1.0
    if venue and prev:
        km = V.km(prev, venue)
        f["travel"] = km / 1000
    if venue and home:
        tz = V.utc_offset(venue, _noon(day)) - V.utc_offset(home, _noon(day))
        f["tz"] = abs(tz)
        f["altitude"] = float(venue.alt >= 1000 and home.alt < 1000)
        zones = (V.zone(home), V.zone(venue))
        f["zone"] = float(zones[0] != zones[1])
        if sport == "nfl":
            f["climate"] = float(venue.roof == "open" and venue.lat >= 39
                                 and day.month in (11, 12, 1, 2)
                                 and (home.roof == "dome" or home.lat < 34))
    return TeamLoad(rest, km, tz, f, zones, at_home=venue is not None and venue == home)


def loads(sport: str, slots: list[Slot]) -> list[tuple[TeamLoad, TeamLoad]]:
    """Belastung (Heim, Gast) je Spiel, in der Reihenfolge von slots."""
    table = V.LEAGUES[sport]
    order = sorted(range(len(slots)), key=lambda i: slots[i].day)
    last: dict[str, tuple[date, V.Venue | None]] = {}
    out: list = [None] * len(slots)
    for i in order:
        s = slots[i]
        venue = None if s.neutral else table.get(s.home)
        out[i] = (team_load(sport, s.home, s.day, venue, last.get(s.home)),
                  team_load(sport, s.away, s.day, venue, last.get(s.away)))
        last[s.home] = last[s.away] = (s.day, venue)
    return out


def diff(h: TeamLoad, a: TeamLoad) -> list[float]:
    return [h.feats[k] - a.feats[k] for k in FEATURES]


@dataclass
class Effects:
    coef: dict[str, float] = field(default_factory=dict)  # Marge (Heim-Sicht) je Einheit
    n: int = 0

    def margin_adj(self, h: TeamLoad, a: TeamLoad) -> float:
        return sum(self.coef.get(k, 0.0) * x for k, x in zip(FEATURES, diff(h, a)))

    def text(self, unit: str) -> str:
        return ", ".join(f"{LABELS[k]} {v:+.2f}" for k, v in self.coef.items()
                         if abs(v) >= 0.005) + f" {unit} (n={self.n})"

    @classmethod
    def fit(cls, xs: list[list[float]], residuals: list[float], ridge: float = 100.0) -> "Effects":
        k = len(FEATURES)
        a = [[sum(x[i] * x[j] for x in xs) + (ridge if i == j else 0.0) for j in range(k)]
             for i in range(k)]
        b = [sum(x[i] * y for x, y in zip(xs, residuals)) for i in range(k)]
        return cls(dict(zip(FEATURES, _solve(a, b))), len(xs))


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gauß-Elimination mit Pivotsuche (kleines, positiv definites System)."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c and m[c][c]:
                f = m[r][c] / m[c][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c])]
    return [m[i][n] / m[i][i] if m[i][i] else 0.0 for i in range(n)]
