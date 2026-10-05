"""Netzwerkzugriff mit ehrlicher Fehlermeldung.

Jeder Abruf liefert (text, fehler). Ist ein Host gesperrt, steht der Grund im
Bericht – es wird nie still auf alte oder erfundene Daten zurückgefallen.

Historische, abgeschlossene Daten (Vorsaison) dürfen über cache_days aus
data/cache/ kommen; aktuelle Preise und Spielpläne werden immer frisch geladen.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

CACHE = Path("data/cache")


def get(url: str, timeout: float = 20.0, cache_days: float = 0.0,
        retries: int = 3, user_agent: str = "oddswatch/0.2",
        headers: dict[str, str] | None = None) -> tuple[str | None, str | None]:
    cp = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
    if cache_days > 0 and cp.exists() and time.time() - cp.stat().st_mtime < cache_days * 86400:
        return cp.read_text(encoding="utf-8"), None
    req = urllib.request.Request(url, headers={"User-Agent": user_agent,
                                               "Accept": "application/json, text/csv, */*",
                                               **(headers or {})})
    err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                enc = (r.headers.get("Content-Encoding") or "").lower()
                if enc == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    try:
                        raw = zlib.decompress(raw)
                    except zlib.error:
                        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                text = raw.decode("utf-8", "replace")
            if cache_days > 0:
                CACHE.mkdir(parents=True, exist_ok=True)
                cp.write_text(text, encoding="utf-8")
            return text, None
        except urllib.error.HTTPError as e:
            err = f"{url}: HTTP {e.code}"
            if e.code == 429:
                time.sleep(4.0 * (attempt + 1))
            elif e.code < 500:
                break
        except (urllib.error.URLError, OSError) as e:
            err = f"{url}: {getattr(e, 'reason', e)}"
        time.sleep(1.5 * (attempt + 1))
    return None, err


def get_json(url: str, **kw) -> tuple[dict | list | None, str | None]:
    text, err = get(url, **kw)
    if text is None:
        return None, err
    try:
        return json.loads(text), None
    except ValueError:
        return None, f"{url}: keine gültige JSON-Antwort"
