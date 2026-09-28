"""Kalshi-Portfolio (nur lesend): Kontostand und ausgeführte Trades (Fills).

Authentifizierung nach Kalshi-API v2: Header KALSHI-ACCESS-KEY,
KALSHI-ACCESS-TIMESTAMP (ms) und KALSHI-ACCESS-SIGNATURE =
base64(RSA-PSS-SHA256(timestamp + METHODE + Pfad ohne Query)).

Umgebungsvariablen: KALSHI_API_KEY_ID und KALSHI_PRIVATE_KEY (PEM-Text; auch
mit literalen "\\n" möglich) oder KALSHI_PRIVATE_KEY_PATH (Datei).
Dieses Modul sendet ausschließlich GET-Anfragen – es platziert keine Orders.
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .kalshi import API

PREFIX = "/trade-api/v2"


def _load_key(pem: str | None = None):
    from cryptography.hazmat.primitives import serialization
    pem = pem or os.environ.get("KALSHI_PRIVATE_KEY", "")
    path = os.environ.get("KALSHI_PRIVATE_KEY_PATH")
    if not pem and path:
        pem = open(path, encoding="utf-8").read()
    if not pem:
        raise RuntimeError("KALSHI_PRIVATE_KEY bzw. KALSHI_PRIVATE_KEY_PATH nicht gesetzt")
    pem = pem.replace("\\n", "\n").strip()
    if "-----BEGIN" in pem and "\n" not in pem.split("-----")[2]:
        # Einzeilig eingefügt: Kopf/Fuß erhalten, Körper umbrechen
        head, body, foot = pem.split("-----")[1], pem.split("-----")[2], pem.split("-----")[3]
        body = "\n".join(body.strip().split())
        pem = f"-----{head}-----\n{body}\n-----{foot}-----"
    return serialization.load_pem_private_key(pem.encode(), password=None)


def sign(key, timestamp_ms: str, method: str, path: str) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    msg = (timestamp_ms + method.upper() + path.split("?")[0]).encode()
    sig = key.sign(msg, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                    salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return base64.b64encode(sig).decode()


class Client:
    def __init__(self, key_id: str | None = None, pem: str | None = None):
        self.key_id = key_id or os.environ.get("KALSHI_API_KEY_ID", "")
        if not self.key_id:
            raise RuntimeError("KALSHI_API_KEY_ID nicht gesetzt")
        self.key = _load_key(pem)

    def get(self, path: str, params: dict | None = None) -> dict:
        full = PREFIX + path
        ts = str(int(time.time() * 1000))
        url = API.rsplit(PREFIX, 1)[0] + full + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(url, headers={
            "KALSHI-ACCESS-KEY": self.key_id, "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": sign(self.key, ts, "GET", full),
            "Accept": "application/json", "User-Agent": "oddswatch/0.2"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"Kalshi {path}: HTTP {e.code} {body}") from None

    def balance_usd(self) -> float:
        d = self.get("/portfolio/balance")
        if d.get("balance_dollars") not in (None, ""):
            return float(d["balance_dollars"])
        return float(d.get("balance", 0)) / 100

    def fills(self, min_ts: int | None = None) -> list[dict]:
        out, cursor = [], None
        while True:
            params = {"limit": 200}
            if cursor:
                params["cursor"] = cursor
            if min_ts:
                params["min_ts"] = min_ts
            d = self.get("/portfolio/fills", params)
            out += d.get("fills", [])
            cursor = d.get("cursor")
            if not cursor or not d.get("fills"):
                return out


@dataclass
class Fill:
    fill_id: str
    ticker: str
    side: str        # "yes" | "no"
    action: str      # "buy" | "sell"
    count: float
    price: float     # 0..1 je Kontrakt für die gekaufte Seite
    fee: float       # $ gesamt (gemeldet oder geschätzt)
    created: str
    is_taker: bool


def _f(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def parse_fill(d: dict) -> Fill:
    side = (d.get("side") or "yes").lower()
    key = "yes_price" if side == "yes" else "no_price"
    if d.get(key + "_dollars") not in (None, ""):
        price = _f(d[key + "_dollars"])
    elif d.get(key + "_fixed") not in (None, ""):
        price = _f(d[key + "_fixed"])
    else:
        price = _f(d.get(key)) / 100
    count = _f(d.get("count_fp", d.get("count")))
    is_taker = bool(d.get("is_taker", True))
    if d.get("fee_cost") not in (None, ""):
        fee = _f(d["fee_cost"])
    else:  # Schätzung nach Kalshi-Tarif (Taker 7 %, Maker 1,75 %)
        rate = 0.07 if is_taker else 0.0175
        fee = int(rate * count * price * (1 - price) * 100 + 0.999999) / 100
    return Fill(str(d.get("fill_id") or d.get("trade_id") or ""), d.get("ticker", ""), side,
                (d.get("action") or "buy").lower(), count, price, fee,
                d.get("created_time", ""), is_taker)
