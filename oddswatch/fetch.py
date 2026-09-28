"""Netzwerkzugriff mit ehrlicher Fehlermeldung.

Jeder Abruf liefert (text, fehler). Ist ein Host gesperrt, steht der Grund im
Bericht – es wird nie still auf alte oder erfundene Daten zurückgefallen.
"""

from __future__ import annotations

import urllib.error
import urllib.request


def get(url: str, timeout: float = 20.0) -> tuple[str | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "oddswatch/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        return None, f"{url}: HTTP {e.code}"
    except (urllib.error.URLError, OSError) as e:
        return None, f"{url}: {getattr(e, 'reason', e)}"
