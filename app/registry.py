"""Owner registry (Stories 1.3-1.6).

Interface: get_by_phone / upsert. Two impls behind it:
  * JsonRegistry  — local file, always available; the documented fallback (1.5 AC3).
  * VaultRegistry — 1Password vault items; wired once OP_SERVICE_ACCOUNT_TOKEN lands.

Phone numbers are hashed (sha256) as the registry key; the raw phone only ever
appears in WhatsApp transport and the audit `owner` field (architecture conventions).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

from app.config import config

# Conversation states (one per phone, stored on the record).
NEW = "NEW"
AWAITING_NAME = "AWAITING_NAME"
READY = "READY"


def hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()


@dataclass
class OwnerRecord:
    hashed_phone: str
    agent_id: str
    state: str = NEW
    name: str | None = None
    verified: bool = False
    budget_cents: int = field(default_factory=lambda: config.default_budget_cents)
    vendor_allowlist: list[str] = field(default_factory=lambda: list(config.default_allowlist))
    history: list[str] = field(default_factory=list)
    active_goal: str | None = None  # current declared goal (Intent Check, Epic 3)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class Registry(Protocol):
    def get_by_phone(self, phone: str) -> OwnerRecord | None: ...
    def upsert(self, record: OwnerRecord) -> None: ...


class JsonRegistry:
    """File-backed registry. Fast, restart-survivable, no external dependency."""

    def __init__(self, path: str | Path = "owners.json") -> None:
        self._path = Path(path)
        self._data: dict[str, dict] = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text() or "{}")

    def get_by_phone(self, phone: str) -> OwnerRecord | None:
        raw = self._data.get(hash_phone(phone))
        return OwnerRecord(**raw) if raw else None

    def upsert(self, record: OwnerRecord) -> None:
        self._data[record.hashed_phone] = asdict(record)
        self._path.write_text(json.dumps(self._data, indent=2))


_registry: Registry | None = None


def get_registry() -> Registry:
    """Vault registry when 1Password is configured AND reachable; else JSON fallback.

    Memoized so we authenticate to 1Password once per process, not per request. The
    vault impl (Story 1.5) is verified live once OP_SERVICE_ACCOUNT_TOKEN is in hand;
    until then every flow uses JSON so development is never blocked.
    """
    global _registry
    if _registry is not None:
        return _registry
    if config.op_configured:
        try:
            from app.registry_vault import VaultRegistry

            _registry = VaultRegistry()
            return _registry
        except Exception:
            pass  # documented fallback — keep the loop alive
    _registry = JsonRegistry()
    return _registry
