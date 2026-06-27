"""User-facing copy — single source of truth so both devs use identical wording.

Voice (conversation-design spec): playful, short, trustworthy. One idea per
message. One emoji as a status marker, always paired with words. Entities bold
with *asterisks*. No internal jargon (no "manifest"/"gate"/"sandbox") to the user.
Status set: 👋 greet · ✅ own · 💸 charge · 🛑 denied · 🤔 didn't-understand.
"""
from __future__ import annotations


def claim_prompt(agent_id: str) -> str:
    return f"👋 New agent incoming! You're claiming *{agent_id}*.\nReply with a name to lock it in."


def _money(cents: int) -> str:
    """120000 -> '1,200', 3000 -> '30', 9950 -> '99.50'. Whole amounts drop the cents."""
    s = f"{cents / 100:,.2f}"
    return s[:-3] if s.endswith(".00") else s


def _bold_list(vendors: list[str]) -> str:
    return ", ".join(f"*{v}*" for v in vendors) if vendors else "*none*"


def owned(name: str, budget_cents: int, vendors: list[str]) -> str:
    return (
        f"✅ Done — you own *{name}* 🔑\n"
        f"Starting limits: budget *${_money(budget_cents)}*, vendors {_bold_list(vendors)}.\n"
        'Change anytime: "budget 100" or "allow Acme, Staples".\n'
        'Text a task like "buy $30 from Acme".'
    )


# --- Settings commands (budget / allowlist) ---
def budget_set(cents: int) -> str:
    return f"💰 Budget set to *${_money(cents)}*."


def budget_show(cents: int) -> str:
    return f"💰 Your budget is *${_money(cents)}*."


def allow_set(vendors: list[str]) -> str:
    return f"🔒 Approved vendors: {_bold_list(vendors)}."


def allow_show(vendors: list[str]) -> str:
    return f"🔒 Approved vendors: {_bold_list(vendors)}."


BUDGET_HINT = '🤔 Try "budget 100" — a dollar amount.'
ALLOW_HINT = '🤔 Try "allow Acme, Staples".'


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
