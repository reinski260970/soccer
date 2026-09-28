"""Teamnamen zwischen Quellen abgleichen (ESPN, football-data, Kalshi, NHL)."""

from __future__ import annotations

import re
import unicodedata

_DROP = {"fc", "sc", "sv", "vfb", "vfl", "tsg", "rb", "ein", "eintracht", "werder",
         "bayer", "borussia", "1", "04", "05", "07", "09", "1846", "1899", "1860", "fk",
         "ac", "as", "sk", "cf", "club", "de", "sport", "tsv", "ksv", "spvgg", "the",
         "hertha", "bsc", "ssv", "fsv", "sg", "wsg"}

_ALIASES = {
    "munich": "bayern", "munchen": "bayern", "bayern munich": "bayern",
    "gladbach": "mgladbach", "monchengladbach": "mgladbach",
    "koln": "koln", "cologne": "koln", "frankfurt": "frankfurt",
    "leipzig": "leipzig", "hamburger": "hamburg", "hsv": "hamburg",
    "st pauli": "pauli", "wolfsberger": "wolfsberg", "wolfsberger ac": "wolfsberg",
    "salzburg": "salzburg", "lustenau": "lustenau", "austria wien": "austria vienna",
    "rapid wien": "rapid vienna", "rapid": "rapid vienna", "sk rapid": "rapid vienna",
    "a lustenau": "lustenau", "austria lustenau": "lustenau",
    "josko ried": "ried", "swarovski tirol": "tirol", "wsg tirol": "tirol",
    "fc cologne": "koln",
}


def norm(name: str) -> str:
    s = re.sub(r"[´`'’]", "", name)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[.\-/]", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = " ".join(s.split())
    if s in _ALIASES:
        return _ALIASES[s]
    toks = [t for t in s.split() if t not in _DROP]
    s = " ".join(toks) or s
    return _ALIASES.get(s, s)


def same(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    ta, tb = set(na.split()), set(nb.split())
    # "New York R" vs "New York Rangers": gemeinsamer Präfix + Initiale
    if na.startswith(nb) or nb.startswith(na):
        short, long_ = (na, nb) if len(na) < len(nb) else (nb, na)
        return len(short) >= 4 and (len(short.split()) > 1 or len(long_.split()) == 1
                                    or short.split()[0] == long_.split()[0])
    return bool(ta & tb) and min(len(ta), len(tb)) == 1 and len((ta & tb).pop()) >= 5


def find(name: str, candidates: list[str]) -> str | None:
    """Bester Treffer aus candidates oder None (bei Mehrdeutigkeit None)."""
    exact = [c for c in candidates if norm(c) == norm(name)]
    if len(exact) == 1:
        return exact[0]
    hits = [c for c in candidates if same(name, c)]
    return hits[0] if len(hits) == 1 else None


def match_label(label: str, aliases: list[str]) -> bool:
    """Kalshi-Label ('Los Angeles C', 'New York R', 'Kansas City') gegen die
    Namensvarianten eines Teams."""
    nl = norm(label)
    for a in aliases:
        na = norm(a)
        if not na:
            continue
        if nl == na:
            return True
        # Stadt + Initiale des Teamnamens: "los angeles c" ~ "los angeles chargers"
        if len(nl.split()) >= 2 and len(nl.split()[-1]) == 1:
            city = " ".join(nl.split()[:-1])
            if na.startswith(city + " " + nl.split()[-1]):
                return True
    return False
