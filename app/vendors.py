"""Vendor roster — name → Stripe connected-account id (routing, not policy).

Kept deliberately separate from the allowlist:
  * allowlist (OwnerRecord.vendor_allowlist) = POLICY — which vendor names the owner permits.
  * roster (this module)                     = ROUTING — which permitted vendors are payable.

A task may be allowed by policy yet have no payout account; that surfaces as a distinct
"approved but not payable" outcome rather than a silent success. The roster is provided
via the VENDOR_ROSTER env (JSON) and passed into the sandbox at charge time.

Only relevant when STRIPE_MODE=connect; in the default "simple" mode the roster is unused.
"""
from __future__ import annotations

import json


def load_roster(raw: str | None) -> dict[str, str]:
    try:
        data = json.loads(raw or "{}")
        return {str(k): str(v) for k, v in data.items()}
    except (ValueError, AttributeError):
        return {}


def resolve(vendor: str, roster: dict[str, str]) -> str | None:
    """Case-insensitive name → connected-account id, or None if not payable."""
    target = vendor.strip().casefold()
    for name, acct in roster.items():
        if name.strip().casefold() == target:
            return acct
    return None
