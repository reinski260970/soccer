"""Publish reviewed news from the outbox through the existing Telegram sender."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from .telegram import send

def publish(root=Path("."), sender=send, now=None):
    now = now or datetime.now(timezone.utc)
    receipts = root / "data/journal/telegram_outbox"
    receipts.mkdir(parents=True, exist_ok=True)
    for path in sorted((root / "reports/telegram_outbox").glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = payload["telegram_text"]
        if not isinstance(text, str) or not text.strip() or len(text) > 3500:
            raise ValueError("Outbox text must contain 1-3500 characters")
        digest = hashlib.sha256(text.encode()).hexdigest()
        receipt = receipts / (digest + ".json")
        if receipt.exists():
            continue
        expiry = datetime.fromisoformat(payload["expires_at"])
        if expiry.tzinfo is None:
            raise ValueError("expires_at requires timezone")
        if expiry <= now:
            print(f"Expired: {path.name}")
            continue
        result = sender(text)
        if not result.get("sent") or not result.get("message_ids"):
            raise RuntimeError("Telegram delivery not confirmed; inspect sender configuration")
        receipt.write_text(json.dumps({
            "source": path.name, "sha256": digest,
            "sent_at": now.isoformat(), "message_ids": result["message_ids"]
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Telegram confirmed: {path.name}, message_ids={result['message_ids']}")

if __name__ == "__main__":
    publish()
