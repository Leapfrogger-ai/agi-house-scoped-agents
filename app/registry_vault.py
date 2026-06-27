"""1Password vault-backed owner registry (Story 1.5).

The identity registry itself lives in the vault: each verified owner is a vault
item keyed by hashed phone. Imported only when OP_SERVICE_ACCOUNT_TOKEN is set;
any failure makes get_registry() fall back to JSON (1.5 AC3).

The onepassword SDK is async; we drive it from a single dedicated background event
loop so the sync Registry interface works from BOTH sync routes (/sim) and async
routes (/webhook). Using asyncio.run() directly would crash inside the webhook's
running loop and silently fall back to JSON. Verified live with the SA token.
"""
from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import asdict

from app.config import config
from app.registry import OwnerRecord, hash_phone

_ITEM_PREFIX = "owner-"
_FIELD = "record"  # JSON blob of the OwnerRecord

# One persistent loop in a daemon thread. The 1Password client is created and used
# on this loop, so it's never touched from the caller's (possibly running) loop.
_loop: asyncio.AbstractEventLoop | None = None
_loop_lock = threading.Lock()


def _run(coro):
    global _loop
    with _loop_lock:
        if _loop is None:
            _loop = asyncio.new_event_loop()
            threading.Thread(target=_loop.run_forever, daemon=True).start()
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()


class VaultRegistry:
    def __init__(self) -> None:
        self._vault = config.op_vault
        self._client = _run(self._connect())

    async def _connect(self):
        from onepassword.client import Client

        return await Client.authenticate(
            auth=config.op_token,
            integration_name="claim-by-text-orchestrator",
            integration_version="0.1.0",
        )

    def get_by_phone(self, phone: str) -> OwnerRecord | None:
        ref = f"op://{self._vault}/{_ITEM_PREFIX}{hash_phone(phone)}/{_FIELD}"
        try:
            blob = _run(self._client.secrets.resolve(ref))
        except Exception:
            return None
        return OwnerRecord(**json.loads(blob))

    def upsert(self, record: OwnerRecord) -> None:
        _run(self._upsert(record))

    async def _upsert(self, record: OwnerRecord) -> None:
        from onepassword import ItemCategory, ItemCreateParams, ItemField, ItemFieldType

        title = f"{_ITEM_PREFIX}{record.hashed_phone}"
        blob = json.dumps(asdict(record))
        vault_id = await self._vault_id()

        # upsert: update the existing item's field if present, else create.
        existing = await self._find(vault_id, title)
        if existing is not None:
            for f in existing.fields:
                if f.id == _FIELD or f.title == _FIELD:
                    f.value = blob
                    break
            else:
                existing.fields.append(
                    ItemField(id=_FIELD, title=_FIELD, field_type=ItemFieldType.CONCEALED, value=blob)
                )
            await self._client.items.put(existing)
            return
        await self._client.items.create(
            ItemCreateParams(
                title=title,
                category=ItemCategory.APICREDENTIALS,
                vault_id=vault_id,
                fields=[ItemField(id=_FIELD, title=_FIELD, field_type=ItemFieldType.CONCEALED, value=blob)],
            )
        )

    async def _vault_id(self) -> str:
        for v in await self._client.vaults.list():
            if v.title == self._vault:
                return v.id
        raise RuntimeError(f"vault {self._vault!r} not found")

    async def _find(self, vault_id: str, title: str):
        for it in await self._client.items.list(vault_id):
            if it.title == title:
                return await self._client.items.get(vault_id, it.id)
        return None
