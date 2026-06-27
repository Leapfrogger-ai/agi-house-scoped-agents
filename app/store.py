"""In-memory demo store for the operator view (chat thread + transactions).

Single-instance, process-local, capped ring buffers — resets on redeploy. That's
fine for the live demo; the durable record of truth is the JSONL audit stream in
the Railway logs and the owner registry in 1Password.
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone

_LOCK = threading.Lock()
MESSAGES: deque[dict] = deque(maxlen=400)       # {ts, phone, direction: in|out, text}
TRANSACTIONS: deque[dict] = deque(maxlen=200)   # audit events (allowed + denied)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_message(phone: str, direction: str, text: str) -> None:
    with _LOCK:
        MESSAGES.append({"ts": _now(), "phone": phone, "direction": direction, "text": text})


def add_transaction(event: dict) -> None:
    with _LOCK:
        TRANSACTIONS.append(event)


def latest_phone() -> str | None:
    with _LOCK:
        for m in reversed(MESSAGES):
            if m["direction"] == "in":
                return m["phone"]
    return None


def snapshot(phone: str | None, hashed_phone: str | None) -> dict:
    with _LOCK:
        msgs = [m for m in MESSAGES if not phone or m["phone"] == phone]
        txns = [t for t in TRANSACTIONS if not hashed_phone or t.get("owner_phone") == hashed_phone]
    return {"phone": phone, "messages": msgs, "transactions": txns}
