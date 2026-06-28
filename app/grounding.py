"""Intent grounding check (Story 3.2) — the in-policy-but-off-task catch.

One Nebius call per item: is this item part of the owner's declared goal?
CONFORM | DEVIATE(intent-drift). This is the only model-dependent step; it runs
AFTER the deterministic gate and BEFORE the charge (fail-closed, NFR007).

Stubbable: tests monkeypatch `check`. When Nebius isn't configured the check is a
no-op (conform) — single-charge/offline flows never block on it.
"""
from __future__ import annotations

import json

from app.config import config

_SYSTEM = (
    "You decide whether a purchase item belongs to a stated goal. "
    'Return STRICT JSON {"conform": true|false, "reason": "<short>"}. '
    "conform=true ONLY if the item is clearly part of accomplishing the goal. "
    "Office/desk peripherals belong to a desk setup; appliances, food, and "
    "personal treats do not."
)


def check(goal: str, item_desc: str) -> tuple[bool, str]:
    """Return (conform, reason). Fail-closed on a configured-but-erroring LLM."""
    if not config.nebius_configured:
        return True, ""  # no grounding available -> don't block (offline/single-charge)
    from openai import OpenAI

    client = OpenAI(api_key=config.nebius_api_key, base_url=config.nebius_base_url)
    for _ in range(2):  # one retry before failing closed
        try:
            resp = client.chat.completions.create(
                model=config.nebius_model,
                response_format={"type": "json_object"},
                temperature=0,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": f"Goal: {goal}\nItem: {item_desc}"},
                ],
            )
            data = json.loads(resp.choices[0].message.content)
            return bool(data.get("conform")), str(data.get("reason", ""))
        except Exception:
            continue
    return False, "couldn't verify against the task"  # fail-closed
