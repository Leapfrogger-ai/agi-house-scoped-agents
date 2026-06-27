"""Audit trail (Story 2.6) — JSONL to stdout (+ file). Railway's log view IS the
live audit stream at demo time; no OpenTelemetry.

Every event binds: owner(phone) -> sandbox -> credential_ref -> intent -> outcome.
credential_ref is ALWAYS a reference (op://...), never the raw secret (FR016/AC3).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_AUDIT_FILE = Path("audit.jsonl")


def emit(
    *,
    owner_phone: str,
    agent_id: str,
    sandbox_id: str | None,
    credential_ref: str,
    intent: str,
    action: str,
    outcome: str,            # "allowed" | "denied"
    reason: str = "",
    charge_id: str | None = None,
    vendor: str = "",
    amount_cents: int = 0,
) -> dict:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "owner_phone": owner_phone,
        "agent_id": agent_id,
        "sandbox_id": sandbox_id,
        "credential_ref": credential_ref,
        "intent": intent,
        "vendor": vendor,
        "amount_cents": amount_cents,
        "action": action,
        "outcome": outcome,
        "reason": reason,
        "charge_id": charge_id,
    }
    line = json.dumps(event)
    print(line, file=sys.stdout, flush=True)
    try:
        with _AUDIT_FILE.open("a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass  # stdout is the source of truth; file is a convenience
    from app import store  # local import to avoid any import-order coupling

    store.add_transaction(event)
    return event
