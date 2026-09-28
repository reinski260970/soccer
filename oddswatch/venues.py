"""Heimspielorte NBA/NFL/NHL: Koordinaten, Zeitzone, Höhe, Dach/Klima.

Grundlage für Reiseweg, Zeitzonenwechsel, Höhenlage und (NFL) Klimawechsel.
Schlüssel: NBA/NFL = ESPN-Teamname, NHL = NHL-Kürzel (wie im Tormodell).
roof: "dome" (Halle/geschlossenes Dach), "open" (Freiluft) – nur NFL relevant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Venue:
    lat: float
    lon: float
    tz: str
    alt: int = 0          # Meter über NN
    roof: str = "dome"


E, C, M, P, AZ = ("America/New_York", "America/Chicago", "America/Denver",
                  "America/Los_Angeles", "America/Phoenix")

_ATL = Venue(33.76, -84.40, E, 320)
_BOS = Venue(42.37, -71.06, E, 5)
_NYC = Venue(40.75, -73.99, E, 10)
_CHA = Venue(35.23, -80.84, E, 230)
_CHI = Venue(41.88, -87.67, C, 180)
_CLE = Venue(41.50, -81.69, E, 200)
_DAL = Venue(32.79, -96.81, C, 140)
_DEN = Venue(39.75, -105.01, M, 1609)
_DET = Venue(42.34, -83.06, E, 190)
_HOU = Venue(29.75, -95.36, C, 15)
_IND = Venue(39.76, -86.16, E, 220)
_LA = Venue(34.04, -118.27, P, 90)
_MIA = Venue(25.78, -80.19, E, 2)
_MIN = Venue(44.98, -93.27, C, 260)
_NOL = Venue(29.95, -90.08, C, 1)
_ORL = Venue(28.54, -81.38, E, 30)
_PHI = Venue(39.90, -75.17, E, 10)
_PHX = Venue(33.45, -112.07, AZ, 330)
_SAC = Venue(38.58, -121.50, P, 10)
_SF = Venue(37.77, -122.39, P, 10)
_SLC = Venue(40.77, -111.90, M, 1300)
_TOR = Venue(43.64, -79.38, E, 80)
_WAS = Venue(38.90, -77.02, E, 10)
_TPA = Venue(27.94, -82.45, E, 10)
_PIT = Venue(40.44, -80.00, E, 230)
_SEA = Venue(47.62, -122.35, P, 50)
_NSH = Venue(36.16, -86.78, C, 170)
_LV = Venue(36.10, -115.18, "America/Los_Angeles", 620)
_BUF = Venue(42.88, -78.88, E, 180)
_STL = Venue(38.63, -90.20, C, 140)

NBA: dict[str, Venue] = {
    "Atlanta Hawks": _ATL, "Boston Celtics": _BOS, "Brooklyn Nets": Venue(40.68, -73.98, E, 10),
    "Charlotte Hornets": _CHA, "Chicago Bulls": _CHI, "Cleveland Cavaliers": _CLE,
    "Dallas Mavericks": _DAL, "Denver Nuggets": _DEN, "Detroit Pistons": _DET,
    "Golden State Warriors": _SF, "Houston Rockets": _HOU, "Indiana Pacers": _IND,
    "LA Clippers": Venue(33.94, -118.34, P, 30), "Los Angeles Lakers": _LA,
    "Memphis Grizzlies": Venue(35.14, -90.05, C, 80), "Miami Heat": _MIA,
    "Milwaukee Bucks": Venue(43.05, -87.92, C, 190), "Minnesota Timberwolves": _MIN,
    "New Orleans Pelicans": _NOL, "New York Knicks": _NYC,
    "Oklahoma City Thunder": Venue(35.46, -97.52, C, 370), "Orlando Magic": _ORL,
    "Philadelphia 76ers": _PHI, "Phoenix Suns": _PHX,
    "Portland Trail Blazers": Venue(45.53, -122.67, P, 15), "Sacramento Kings": _SAC,
    "San Antonio Spurs": Venue(29.43, -98.44, C, 200), "Toronto Raptors": _TOR,
    "Utah Jazz": _SLC, "Washington Wizards": _WAS,
}

_O = "open"
NFL: dict[str, Venue] = {
    "Arizona Cardinals": Venue(33.53, -112.26, AZ, 330), "Atlanta Falcons": _ATL,
    "Baltimore Ravens": Venue(39.28, -76.62, E, 10, _O), "Buffalo Bills": Venue(42.77, -78.79, E, 190, _O),
    "Carolina Panthers": Venue(35.23, -80.85, E, 230, _O), "Chicago Bears": Venue(41.86, -87.62, C, 180, _O),
    "Cincinnati Bengals": Venue(39.10, -84.52, E, 150, _O), "Cleveland Browns": Venue(41.51, -81.70, E, 180, _O),
    "Dallas Cowboys": Venue(32.75, -97.09, C, 180), "Denver Broncos": Venue(39.74, -105.02, M, 1609, _O),
    "Detroit Lions": _DET, "Green Bay Packers": Venue(44.50, -88.06, C, 200, _O),
    "Houston Texans": _HOU, "Indianapolis Colts": _IND,
    "Jacksonville Jaguars": Venue(30.32, -81.64, E, 5, _O), "Kansas City Chiefs": Venue(39.05, -94.48, C, 270, _O),
    "Las Vegas Raiders": _LV, "Los Angeles Chargers": Venue(33.95, -118.34, P, 30),
    "Los Angeles Rams": Venue(33.95, -118.34, P, 30), "Miami Dolphins": Venue(25.96, -80.24, E, 2, _O),
    "Minnesota Vikings": _MIN, "New England Patriots": Venue(42.09, -71.26, E, 90, _O),
    "New Orleans Saints": _NOL, "New York Giants": Venue(40.81, -74.07, E, 5, _O),
    "New York Jets": Venue(40.81, -74.07, E, 5, _O), "Philadelphia Eagles": Venue(39.90, -75.17, E, 10, _O),
    "Pittsburgh Steelers": Venue(40.45, -80.02, E, 230, _O), "San Francisco 49ers": Venue(37.40, -121.97, P, 10, _O),
    "Seattle Seahawks": Venue(47.60, -122.33, P, 50, _O), "Tampa Bay Buccaneers": Venue(27.98, -82.50, E, 10, _O),
    "Tennessee Titans": Venue(36.17, -86.77, C, 130, _O), "Washington Commanders": Venue(38.91, -76.86, E, 60, _O),
}

NHL: dict[str, Venue] = {
    "ANA": Venue(33.81, -117.88, P, 50), "BOS": _BOS, "BUF": _BUF, "CAR": Venue(35.80, -78.72, E, 130),
    "CBJ": Venue(39.97, -83.01, E, 240), "CGY": Venue(51.04, -114.05, "America/Edmonton", 1045),
    "CHI": _CHI, "COL": _DEN, "DAL": _DAL, "DET": _DET,
    "EDM": Venue(53.55, -113.50, "America/Edmonton", 670), "FLA": Venue(26.16, -80.33, E, 3),
    "LAK": _LA, "MIN": Venue(44.94, -93.10, C, 240), "MTL": Venue(45.50, -73.57, "America/Toronto", 40),
    "NJD": Venue(40.73, -74.17, E, 10), "NSH": _NSH, "NYI": Venue(40.72, -73.72, E, 20),
    "NYR": _NYC, "OTT": Venue(45.30, -75.93, "America/Toronto", 90), "PHI": _PHI, "PIT": _PIT,
    "SEA": _SEA, "SJS": Venue(37.33, -121.90, P, 25), "STL": _STL, "TBL": _TPA,
    "TOR": _TOR, "UTA": _SLC, "VAN": Venue(49.28, -123.11, "America/Vancouver", 10),
    "VGK": _LV, "WPG": Venue(49.89, -97.14, "America/Winnipeg", 230), "WSH": _WAS,
}

LEAGUES = {"nba": NBA, "nfl": NFL, "nhl": NHL}


def zone(v: Venue) -> str:
    """Grobe Klimazone des Standorts (Näherung aus Lage und Höhe)."""
    if v.alt >= 1000:
        return "Höhenklima"
    if v.tz in (AZ,) or (v.lon < -110 and v.lat < 37.5 and v.alt > 300):
        return "Wüste"
    if v.lat < 31:
        return "subtropisch"
    if v.lon < -117 and v.lat < 39:
        return "mediterran"
    if v.lon < -120:
        return "ozeanisch"
    if v.lat >= 41.5:
        return "kontinental-kalt"
    return "gemäßigt"


def travel_hours(km_: float) -> float:
    """Geschätzte Anreisezeit Tür zu Tür: Bus bis 300 km, sonst Charterflug
    (≈ 800 km/h plus 1,5 h Transfer)."""
    if km_ <= 0:
        return 0.0
    return km_ / 80 if km_ <= 300 else km_ / 800 + 1.5


def km(a: Venue, b: Venue) -> float:
    """Großkreisdistanz in km."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def utc_offset(v: Venue, when: datetime) -> float:
    """UTC-Versatz in Stunden am Spieltag (inkl. Sommerzeit bzw. Arizona ohne)."""
    return when.astimezone(ZoneInfo(v.tz)).utcoffset().total_seconds() / 3600
