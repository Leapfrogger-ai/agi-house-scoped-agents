"""Policy gate (Story 2.3) — the ONLY place ALLOW/DENY is decided.

Deterministic, no I/O, no model output. Containment is physical, not a monitor:
identical inputs always yield an identical verdict (NFR003), so the live denial
demo cannot flake.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.manifest import IntentManifest


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    reason: str  # "" when allowed; machine reason ("over-budget"/"off-allowlist") when denied


ALLOW = Verdict(True, "")


def DENY(reason: str) -> Verdict:  # noqa: N802 - reads as a constructor at call sites
    return Verdict(False, reason)


def evaluate(m: IntentManifest) -> Verdict:
    return evaluate_fields(m.amount_cents, m.vendor, m.budget_cents, m.vendor_allowlist)


def evaluate_fields(amount_cents: int, vendor: str, budget_cents: int, allowlist: list[str]) -> Verdict:
    """Per-item gate — used for both single charges and each item in a multi-item loop."""
    if amount_cents > budget_cents:
        return DENY("over-budget")
    if not _on_allowlist(vendor, allowlist):
        return DENY("off-allowlist")
    return ALLOW


def _on_allowlist(vendor: str, allowlist: list[str]) -> bool:
    return vendor.strip().casefold() in {v.strip().casefold() for v in allowlist}
