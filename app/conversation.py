"""Conversation state machine (Stories 1.3, 1.4, 1.6): NEW -> AWAITING_NAME -> READY.

Channel-agnostic: it takes (phone, text) and returns a reply string. The single
inbound handler in main.py drives it for every channel.
"""
from __future__ import annotations

import re

from app import copy
from app.registry import (
    AWAITING_NAME,
    READY,
    OwnerRecord,
    Registry,
    get_registry,
    hash_phone,
)
from app.tasking import delegate

# A message is a purchase intent if it mentions money or a buy/pay verb.
_PURCHASE = re.compile(r"\$|\d|\b(buy|pay|purchase|order|spend)\b", re.IGNORECASE)
_HAS_WORD = re.compile(r"\w")


def agent_id_for(phone: str) -> str:
    """Deterministic short agent id, e.g. 'Agent #A4' — no RNG, reproducible per number."""
    return "Agent #A" + hash_phone(phone)[:2].upper()


def handle(phone: str, text: str, registry: Registry | None = None) -> str:
    registry = registry or get_registry()
    text = text.strip()
    record = registry.get_by_phone(phone)

    # First contact from an unknown number -> start the claim (J1).
    if record is None:
        record = OwnerRecord(
            hashed_phone=hash_phone(phone),
            agent_id=agent_id_for(phone),
            state=AWAITING_NAME,
        )
        registry.upsert(record)
        return copy.claim_prompt(record.agent_id)

    # Second inbound is the verification — the name locks ownership (J1, Story 1.4).
    if record.state == AWAITING_NAME:
        if not _HAS_WORD.search(text):
            return copy.NEED_A_NAME
        record.name = text
        record.verified = True
        record.state = READY
        registry.upsert(record)
        return copy.owned(record.name)

    # READY: a verified owner. Purchase intent -> delegate; anything else -> greet (J4/Story 1.6).
    if record.state == READY:
        if text.upper() == "CLAIM":
            return copy.ALREADY_OWN.format(name=record.name)
        if _PURCHASE.search(text):
            return delegate(record, text)
        return copy.welcome_back(record.name or record.agent_id)

    return copy.welcome_back(record.name or record.agent_id)
