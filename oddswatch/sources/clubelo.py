"""ClubElo (clubelo.com): Elo-Werte europäischer Vereine, ligaübergreifend.

Die CSV-API (api.clubelo.com) antwortet derzeit mit HTTP 502. Die Webseiten
betten die Werte als Vega-Datensatz ein ({"Name", "Elo", "Federation",
"Level", ...}). Die Startseite zeigt nur die Top 50, daher werden die
Länderseiten (/GER, /AZE, ...) der UEFA-Verbände geladen – nur diese, weil
Namen weltweit doppelt vorkommen (Liverpool ENG/URU, Barcelona ESP/ECU).
Gibraltar und Andorra haben dort keinen Datensatz. Ohne Browser-User-Agent
laufen Unterseiten teils in Timeouts.
"""

from __future__ import annotations

import json
import re

from .. import fetch

BASE = "https://clubelo.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) oddswatch/0.2"
_OBJ = re.compile(r'\{[^{}]*"Elo":[^{}]*\}')
UEFA = ("ALB AND ARM AUT AZE BEL BIH BLR BUL CRO CYP CZE DEN ENG ESP EST FIN FRA FRO GEO "
        "GER GIB GRE HUN IRL ISL ISR ITA KAZ KOS LTU LUX LVA MDA MKD MLT MNE NED NIR NOR "
        "POL POR ROU RUS SCO SMR SRB SUI SVK SVN SWE TUR UKR WAL").split()


def parse_page(html: str) -> dict[str, tuple[float, str]]:
    """Vereinsname -> (Elo, Verband)."""
    out = {}
    for m in _OBJ.findall(html):
        try:
            o = json.loads(m)
        except ValueError:
            continue
        if o.get("Name") and isinstance(o.get("Elo"), (int, float)):
            out[o["Name"]] = (float(o["Elo"]), o.get("Federation", ""))
    return out


def ratings(cache_days: float = 1.0) -> tuple[dict[str, tuple[float, str]], list[str]]:
    """Alle Vereine der UEFA-Verbände: Name -> (Elo, Verband)."""
    out: dict[str, tuple[float, str]] = {}
    errs = []
    for c in UEFA:
        h, e = fetch.get(f"{BASE}/{c}", timeout=40, cache_days=cache_days, retries=1,
                         user_agent=UA)
        if h is None:
            errs.append(f"ClubElo {c}: {e}")
            continue
        for name, v in parse_page(h).items():
            out.setdefault(name, v)
    return out, errs
