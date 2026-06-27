"""Channel adapters. Conversation logic is unaware of which one is active (FR003)."""
from __future__ import annotations

from app.channel.base import ChannelAdapter, Inbound
from app.config import config


def get_adapter() -> ChannelAdapter:
    """Select the active adapter from config (Story 1.2: config switch)."""
    if config.channel == "whatsapp":
        from app.channel.whatsapp import WhatsAppAdapter

        return WhatsAppAdapter()
    from app.channel.mock import MockAdapter

    return MockAdapter()


__all__ = ["ChannelAdapter", "Inbound", "get_adapter"]
