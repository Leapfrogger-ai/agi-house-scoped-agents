"""User-facing copy — single source of truth so both devs use identical wording.

Voice (conversation-design spec): playful, short, trustworthy. One idea per
message. One emoji as a status marker, always paired with words. Entities bold
with *asterisks*. No internal jargon (no "manifest"/"gate"/"sandbox") to the user.
Status set: 👋 greet · ✅ own · 💸 charge · 🛑 denied · 🤔 didn't-understand.
"""
from __future__ import annotations


def claim_prompt(agent_id: str) -> str:
    return f"👋 New agent incoming! You're claiming *{agent_id}*.\nReply with a name to lock it in."


def owned(name: str) -> str:
    return (
        f"✅ Done — you own *{name}*, and your number is the key 🔑\n"
        'Text me a task, like "buy 50 staples from Acme".'
    )


def receipt(vendor: str, dollars: str, remaining: str, charge_id: str) -> str:
    return f"💸 Paid *{vendor}* *${dollars}*. ${remaining} left on this task.\nReceipt #{charge_id} ✅"


def denied_budget(amount: str, budget: str) -> str:
    return f"🛑 That's *${amount}* — over your *${budget}* budget. Didn't charge a cent."


def denied_allowlist(vendor: str) -> str:
    return f"🛑 *{vendor}* isn't on your approved list, so I sat this one out. No charge."


def welcome_back(name: str) -> str:
    return f"👋 Welcome back — *{name}* here. What's the task?"


# --- Error & recovery states ---
NEED_A_NAME = "🙂 Just need a name for your agent — reply with one word."
NO_AGENT_YET = "👋 You don't own an agent yet. Reply *CLAIM* to start."
BAD_TASK = '🤔 Didn\'t catch an amount + vendor. Try "buy *$30* from *Acme*".'
ALREADY_OWN = "👋 You already own *{name}*. Just text me a task."
CHARGE_BROKE = "⚠️ Something broke on my end — no charge went through. Try again in a sec."
