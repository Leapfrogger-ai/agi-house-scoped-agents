"""Owner settings commands handled inside READY (Story 1.7): view/change budget and
allowlist over text. Deterministic — no LLM — so the agent can never change its own
policy; only the verified principal can, from their verified number.

Zero data-model change: reuses OwnerRecord.budget_cents / vendor_allowlist and the
existing registry.upsert() write path. Both set-commands OVERWRITE (no merge).
"""
from __future__ import annotations

from dataclasses import dataclass

from app import copy
from app.registry import OwnerRecord, Registry


@dataclass(frozen=True)
class ShowBudget: ...


@dataclass(frozen=True)
class SetBudget:
    cents: int


@dataclass(frozen=True)
class ShowAllow: ...


@dataclass(frozen=True)
class SetAllow:
    vendors: list[str]


class SettingsError(ValueError):
    """Carries the in-voice hint to send back on a bad command."""


def parse_money(s: str) -> int:
    """'$1,200' -> 120000 cents. Raises ValueError on non-positive / non-numeric."""
    n = float(s.replace("$", "").replace(",", "").strip())
    if n <= 0:
        raise ValueError("non-positive")
    return round(n * 100)


def parse_settings_command(text: str):
    """Return a settings command, or None if this isn't one (falls through to tasks).

    Raises SettingsError (with a user-facing hint) on a recognised-but-malformed command.
    """
    t = text.strip()
    low = t.lower()
    if low == "budget" or low.startswith("budget "):
        arg = t[6:].strip()
        if not arg:
            return ShowBudget()
        try:
            return SetBudget(parse_money(arg))
        except ValueError:
            raise SettingsError(copy.BUDGET_HINT) from None
    if low == "allow" or low.startswith("allow "):
        arg = t[5:].strip()
        if not arg:
            return ShowAllow()
        vendors = [v.strip() for v in arg.split(",") if v.strip()]
        if not vendors:
            raise SettingsError(copy.ALLOW_HINT)
        return SetAllow(vendors)
    return None


def apply(owner: OwnerRecord, cmd, registry: Registry) -> str:
    """Apply a parsed command, persisting set-commands via the existing upsert path."""
    if isinstance(cmd, ShowBudget):
        return copy.budget_show(owner.budget_cents)
    if isinstance(cmd, SetBudget):
        owner.budget_cents = cmd.cents
        registry.upsert(owner)
        return copy.budget_set(cmd.cents)
    if isinstance(cmd, ShowAllow):
        return copy.allow_show(owner.vendor_allowlist)
    if isinstance(cmd, SetAllow):
        owner.vendor_allowlist = cmd.vendors
        registry.upsert(owner)
        return copy.allow_set(cmd.vendors)
    raise TypeError(f"unknown settings command: {cmd!r}")
