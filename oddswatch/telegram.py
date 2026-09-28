"""Telegram-Versand direkt über die Bot API (ohne Make).

Benötigt TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID als Umgebungsvariablen.
Ein Versand gilt nur als erledigt, wenn Telegram ok=true und eine message_id
zurückgibt; alles andere wird als Fehler gemeldet.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

LIMIT = 4000  # Telegram erlaubt 4096 Zeichen je Nachricht


def chunks(text: str, limit: int = LIMIT) -> list[str]:
    out, cur = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if cur:
                out.append(cur)
                cur = ""
            out.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) > limit:
            out.append(cur)
            cur = ""
        cur += line
    if cur.strip():
        out.append(cur)
    return out


def send(text: str, token: str | None = None, chat_id: str | None = None,
         timeout: float = 20.0) -> dict:
    """Sendet text (ggf. in Teilen). Rückgabe:
    {'sent': bool, 'message_ids': [...], 'error': str|None}"""
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return {"sent": False, "message_ids": [],
                "error": "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID nicht gesetzt – nichts gesendet"}
    ids = []
    for part in chunks(text):
        body = urllib.parse.urlencode({"chat_id": chat_id, "text": part,
                                       "disable_web_page_preview": "true"}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                res = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                res = json.loads(e.read().decode())
            except ValueError:
                res = {"ok": False, "description": f"HTTP {e.code}"}
        except (urllib.error.URLError, OSError) as e:
            res = {"ok": False, "description": str(getattr(e, "reason", e))}
        mid = (res.get("result") or {}).get("message_id") if res.get("ok") else None
        if not mid:
            return {"sent": False, "message_ids": ids,
                    "error": f"Telegram: {res.get('description', 'unbekannter Fehler')}"
                             + (f" (nach {len(ids)} gesendeten Teilen)" if ids else "")}
        ids.append(mid)
    return {"sent": True, "message_ids": ids, "error": None}


def chat_ids(token: str | None = None, timeout: float = 20.0) -> tuple[list[tuple[int, str]], str | None]:
    """Chats, die dem Bot zuletzt geschrieben haben (getUpdates): [(id, name)]."""
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return [], "TELEGRAM_BOT_TOKEN nicht gesetzt"
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates",
                                    timeout=timeout) as r:
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return [], f"Telegram: HTTP {e.code}"
    except (urllib.error.URLError, OSError) as e:
        return [], f"Telegram: {getattr(e, 'reason', e)}"
    if not res.get("ok"):
        return [], f"Telegram: {res.get('description')}"
    seen: dict[int, str] = {}
    for u in res.get("result", []):
        msg = u.get("message") or u.get("channel_post") or u.get("my_chat_member") or {}
        chat = msg.get("chat") or {}
        if "id" in chat:
            seen[chat["id"]] = chat.get("title") or chat.get("username") or chat.get("first_name", "")
    return list(seen.items()), None
