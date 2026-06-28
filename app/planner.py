"""Flexible task planner (Nebius) — interprets free-form purchase requests and
fills missing slots conversationally, instead of rejecting anything that isn't
"buy $X from Y" or a catalog keyword.

One LLM call per turn. Returns a structured plan; the caller resolves prices from
the catalog, asks a clarifying question when something's missing, and remembers the
in-progress request (slot-filling) on the owner record.

Grounded by construction: the planner is told NEVER to invent a price — it may only
use a catalog price or one the user explicitly stated. Stubbable for tests; falls
back to the deterministic catalog/parse path when Nebius isn't configured.
"""
from __future__ import annotations

import json

from app import catalog
from app.config import config

_SCHEMA = (
    '{"intent":"purchase|settings|smalltalk|cancel",'
    '"goal":"<short declared purpose or null>",'
    '"items":[{"name":str,"amount_cents":int|null,"vendor":str|null}],'
    '"question":"<one short clarifying question or null>"}'
)


def _system(allowlist: list[str], budget_cents: int) -> str:
    items = ", ".join(f"{k} (${p/100:.0f}, {v})" for k, (p, v) in catalog.CATALOG.items())
    return (
        "You are a procurement planner for a spending agent. Read the user's message and any "
        "in-progress request, and return STRICT JSON: " + _SCHEMA + ". Rules:\n"
        f"- Approved vendors: {', '.join(allowlist)}. Budget per item: ${budget_cents/100:.0f}.\n"
        f"- Known catalog (use these prices/vendors when an item matches): {items}.\n"
        "- NEVER invent a price. Use a catalog price, or a price the user explicitly stated; "
        "otherwise leave amount_cents null and ask ONE concise question naming an approved vendor.\n"
        "- intent=settings if they want to change budget/vendors; smalltalk for greetings/chitchat; "
        "cancel if they abandon the request; else purchase.\n"
        "- If an in-progress request is given, MERGE the new message into it and keep prior items."
    )


def plan(text: str, pending: dict | None, allowlist: list[str], budget_cents: int) -> dict:
    """Return {intent, goal, items, question}. Catalog-resolved; prices never invented."""
    from openai import OpenAI

    client = OpenAI(api_key=config.nebius_api_key, base_url=config.nebius_base_url)
    user = f"In-progress: {json.dumps(pending) if pending else 'none'}\nMessage: {text}"
    resp = client.chat.completions.create(
        model=config.nebius_model, response_format={"type": "json_object"}, temperature=0,
        messages=[{"role": "system", "content": _system(allowlist, budget_cents)},
                  {"role": "user", "content": user}],
    )
    data = json.loads(resp.choices[0].message.content)
    return _resolve(data)


def _resolve(data: dict) -> dict:
    """Fill known items from the catalog; keep prices grounded."""
    items = []
    for it in (data.get("items") or [])[:8]:
        name = (it.get("name") or "").strip()
        if not name:
            continue
        amount, vendor = it.get("amount_cents"), it.get("vendor")
        hit = catalog.resolve(name)
        if hit:  # catalog is authoritative for known items
            amount, vendor = hit[0], hit[1]
        items.append({"name": name, "amount_cents": amount, "vendor": vendor})
    return {
        "intent": data.get("intent", "purchase"),
        "goal": data.get("goal") or None,
        "items": items,
        "question": data.get("question") or None,
    }
