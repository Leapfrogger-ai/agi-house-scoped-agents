"""SHARED CONTRACT #1 (Story 1.1) — the channel seam both workstreams build to.

A ChannelAdapter turns a transport-specific inbound (Twilio form post, a typed
terminal line) into a uniform (from_phone, text) pair, and sends text back. The
conversation state machine never imports a concrete channel.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Inbound:
    from_phone: str   # raw phone, e.g. "whatsapp:+1555..." or "+1555..."
    text: str


@runtime_checkable
class ChannelAdapter(Protocol):
    def parse_inbound(self, req: object) -> Inbound:
        """Extract (from_phone, text) from a transport-specific request. (== receive())"""
        ...

    def send(self, to_phone: str, text: str) -> None:
        """Deliver an outbound reply on the same channel."""
        ...
