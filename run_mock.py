#!/usr/bin/env python3
"""Offline demo backstop (NFR005): drive the whole flow from the terminal.

    python run_mock.py

Type messages as the user; the bot replies inline. No WhatsApp, Twilio, or Railway.
Runs the full claim -> verify -> delegate -> contain -> return script against the
mock shim. Uses fresh owners.json each run unless one exists.

Try:
    CLAIM
    Budgetbot
    buy office supplies, $30 from Acme
    buy $80 of supplies from Acme
    pay EvilCorp $20
    hey
"""
from __future__ import annotations

from app import conversation
from app.channel.mock import MockAdapter


def main() -> None:
    adapter = MockAdapter()
    print("=== claim-an-agent-by-text (mock shim) ===")
    print(f"You are texting from {adapter.phone}. Ctrl-D to quit.\n")
    while True:
        try:
            text = input("You → ").strip()
        except EOFError:
            print("\nbye 👋")
            return
        if not text:
            continue
        inbound = adapter.parse_inbound(text)
        reply = conversation.handle(inbound.from_phone, inbound.text)
        adapter.send(inbound.from_phone, reply)


if __name__ == "__main__":
    main()
