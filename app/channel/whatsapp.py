"""Twilio WhatsApp Sandbox adapter (Story 1.2, stretch).

Same ChannelAdapter interface as the mock — the conversation logic can't tell them
apart (FR003). Inbound arrives as a Twilio form POST; outbound uses the REST API.
"""
from __future__ import annotations

from app.channel.base import Inbound
from app.config import config


class WhatsAppAdapter:
    def __init__(self) -> None:
        from twilio.rest import Client

        self._client = Client(config.twilio_sid, config.twilio_token)

    def parse_inbound(self, req: dict) -> Inbound:
        # req = parsed form fields from Twilio's webhook POST.
        return Inbound(from_phone=req.get("From", ""), text=req.get("Body", ""))

    def send(self, to_phone: str, text: str) -> None:
        self._client.messages.create(
            from_=config.twilio_from,
            to=to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}",
            body=text,
        )
