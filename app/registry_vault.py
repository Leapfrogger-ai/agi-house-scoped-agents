"""1Password vault-backed owner registry (Story 1.5).

The identity registry itself lives in the vault: each verified owner is a vault
item keyed by hashed phone. Imported only when OP_SERVICE_ACCOUNT_TOKEN is set;
any failure makes get_registry() fall back to JSON (1.5 AC3).

The onepassword SDK is async; we wrap it behind the sync Registry interface with
asyncio.run so callers stay simple. Verified live once the SA token is in hand.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict

from app.config import config
from app.registry import OwnerRecord, hash_phone

_ITEM_PREFIX = "owner-"
_FIELD = "record"  # JSON blob of the OwnerRecord


class VaultRegistry:
    def __init__(self) -> None:
        self._vault = config.op_vault
        self._client = asyncio.run(self._connect())

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
            blob = asyncio.run(self._client.secrets.resolve(ref))
        except Exception:
            return None
        return OwnerRecord(**json.loads(blob))

    def upsert(self, record: OwnerRecord) -> None:
        asyncio.run(self._upsert(record))

    async def _upsert(self, record: OwnerRecord) -> None:
        from onepassword import ItemCategory, ItemCreateParams, ItemField, ItemFieldType

        title = f"{_ITEM_PREFIX}{record.hashed_phone}"
        blob = json.dumps(asdict(record))
        fields = [ItemField(id=_FIELD, title=_FIELD, field_type=ItemFieldType.CONCEALED, value=blob)]

        # upsert: try to find an existing item; create if absent.
        existing = await self._find(title)
        if existing is not None:
            existing.fields = fields
            await self._client.items.put(existing)
            return
        await self._client.items.create(
            ItemCreateParams(
                title=title,
                category=ItemCategory.API_CREDENTIAL,
                vault_id=await self._vault_id(),
                fields=fields,
            )
        )

    async def _vault_id(self) -> str:
        async for v in await self._client.vaults.list_all():
            if v.title == self._vault:
                return v.id
        raise RuntimeError(f"vault {self._vault!r} not found")

    async def _find(self, title: str):
        async for it in await self._client.items.list_all(await self._vault_id()):
            if it.title == title:
                return await self._client.items.get(await self._vault_id(), it.id)
        return None
