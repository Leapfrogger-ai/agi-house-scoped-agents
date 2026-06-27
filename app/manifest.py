"""SHARED CONTRACT #2 (Story 1.1) — the IntentManifest both workstreams build to,
plus task-text -> manifest parsing (Story 2.4).

owner_phone is the verified human principal; it proves *who delegated* but grants
NO spending authority of its own (that comes from the 1Password runtime credential).
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.config import config


class IntentManifest(BaseModel):
    owner_phone: str
    task: str
    amount_cents: int
    vendor: str
    budget_cents: int
    vendor_allowlist: list[str]
    ttl_seconds: int = Field(default=300)


class ParseError(ValueError):
    """Raised when a task text has no recoverable amount + vendor."""


# --- Deterministic fallback parser (no network; always available) ----------------
_AMOUNT = re.compile(r"\$?\s*(\d+(?:\.\d{1,2})?)")
_VENDOR = re.compile(r"\bfrom\s+([A-Za-z0-9][\w&.\- ]*?)(?:\s+for\b|[.,!?]|$)", re.IGNORECASE)
# "pay EvilCorp $20" style — vendor is the word after pay/to.
_VENDOR_PAY = re.compile(r"\b(?:pay|to)\s+([A-Za-z0-9][\w&.\-]*)", re.IGNORECASE)


def _regex_parse(text: str) -> tuple[int, str]:
    amount_m = _AMOUNT.search(text)
    if not amount_m:
        raise ParseError("no amount")
    amount_cents = round(float(amount_m.group(1)) * 100)

    vendor_m = _VENDOR.search(text) or _VENDOR_PAY.search(text)
    if not vendor_m:
        raise ParseError("no vendor")
    return amount_cents, vendor_m.group(1).strip()


# --- Nebius LLM parser (preferred; OpenAI-compatible JSON mode) -------------------
def _nebius_parse(text: str) -> tuple[int, str]:
    from openai import OpenAI

    client = OpenAI(api_key=config.nebius_api_key, base_url=config.nebius_base_url)
    resp = client.chat.completions.create(
        model=config.nebius_model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract a purchase intent. Return STRICT JSON: "
                    '{"amount_cents": <int cents>, "vendor": <string>}. '
                    "Dollars to integer cents. If no clear amount or vendor, set the "
                    "missing field to null."
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    import json

    data = json.loads(resp.choices[0].message.content)
    if not data.get("amount_cents") or not data.get("vendor"):
        raise ParseError("LLM could not extract amount + vendor")
    return int(data["amount_cents"]), str(data["vendor"]).strip()


def parse_task(owner_phone: str, text: str, *, budget_cents: int, allowlist: list[str]) -> IntentManifest:
    """Build an IntentManifest from a free-text task.

    Uses Nebius when configured, else the deterministic regex parser (offline backstop).
    Budget + allowlist come from the owner record, NOT the message — the user cannot
    raise their own budget by asking.
    """
    if config.nebius_configured:
        try:
            amount_cents, vendor = _nebius_parse(text)
        except Exception:
            amount_cents, vendor = _regex_parse(text)  # degrade, don't fail the demo
    else:
        amount_cents, vendor = _regex_parse(text)

    return IntentManifest(
        owner_phone=owner_phone,
        task=text,
        amount_cents=amount_cents,
        vendor=vendor,
        budget_cents=budget_cents,
        vendor_allowlist=allowlist,
    )
