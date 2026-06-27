"""Mock shim (Story 1.2) — terminal channel implementing ChannelAdapter.

The build-time default and the offline demo backstop (NFR005): the full
conversation runs with no WhatsApp/Twilio/Railway in the loop.
"""
from __future__ import annotations

from app.channel.base import Inbound


class MockAdapter:
    DEFAULT_PHONE = "+15555550123"

    def __init__(self, phone: str | None = None) -> None:
        self.phone = phone or self.DEFAULT_PHONE

    def parse_inbound(self, req: object) -> Inbound:
        # req is a raw typed line in the mock; phone is fixed per session.
        return Inbound(from_phone=self.phone, text=str(req))

    def send(self, to_phone: str, text: str) -> None:
        print(f"\nBot → {text}\n")
