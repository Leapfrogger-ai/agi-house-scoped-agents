"""Mock product catalog (Intent Check demo). Maps item name -> (price_cents, vendor).

No live price-lookup tool (deliberately out of scope, PRD-intent-check-lean). An
explicit "$X" / "from Y" in the message overrides the catalog (handles the injected
espresso line). Vendors here should exist in the owner's allowlist + Stripe roster.
"""
from __future__ import annotations

import re

from app.manifest import Item

# name -> (price_cents, vendor). Values match the demo runbook.
CATALOG: dict[str, tuple[int, str]] = {
    "keyboard": (4000, "Acme"),
    "mouse": (2500, "Acme"),
    "monitor": (30000, "Staples"),
    "desk lamp": (3500, "Staples"),
    "notebook": (1500, "Acme"),
    "stapler": (1200, "Staples"),
    "espresso machine": (25000, "Acme"),
    "coffee machine": (25000, "Acme"),
    "chair": (50000, "Acme"),
}

_PRICE = re.compile(r"\$\s*([\d,]+(?:\.\d{1,2})?)")
_FROM = re.compile(r"\bfrom\s+([A-Za-z][\w&.\-]*)", re.IGNORECASE)


def resolve(name: str) -> tuple[int, str] | None:
    key = name.strip().casefold()
    if key in CATALOG:
        return CATALOG[key]
    for k, v in CATALOG.items():  # loose contains match ("a keyboard" -> keyboard)
        if k in key or key in k:
            return v
    return None


def scan(text: str) -> list[Item]:
    """Catalog items mentioned in the text, in order of appearance."""
    low = text.casefold()
    hits = [(low.index(k), k, p, v) for k, (p, v) in CATALOG.items() if k in low]
    # de-dup overlapping keys (e.g. "coffee machine" vs "machine") by earliest position
    hits.sort()
    seen_spans: list[tuple[int, int]] = []
    items: list[Item] = []
    for pos, name, price, vendor in hits:
        span = (pos, pos + len(name))
        if any(a <= pos < b for a, b in seen_spans):
            continue
        seen_spans.append(span)
        items.append(Item(description=name, amount_cents=price, vendor=vendor))
    # single explicit item: let "$X" / "from Y" override the catalog defaults
    if len(items) == 1:
        pm, fm = _PRICE.search(text), _FROM.search(text)
        if pm:
            items[0].amount_cents = round(float(pm.group(1).replace(",", "")) * 100)
        if fm:
            items[0].vendor = fm.group(1)
    return sorted(items, key=lambda it: low.index(it.description))


def has_items(text: str) -> bool:
    return any(k in text.casefold() for k in CATALOG)


def extract_goal(text: str) -> str | None:
    """The clause before a ':' is the declared goal ('Set up the new hire's desk')."""
    if ":" in text:
        goal = text.split(":", 1)[0].strip(" .")
        if goal and len(goal.split()) <= 9:
            return goal
    return None
