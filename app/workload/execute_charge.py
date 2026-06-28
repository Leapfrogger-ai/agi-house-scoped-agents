"""RUNS INSIDE THE DAYTONA SANDBOX. Standalone — imports nothing from `app` so it
can run in a bare python:3.11-slim image with only onepassword-sdk + stripe.

Two modes (orchestrator picks via env):
  * MANIFEST_JSON — single charge (Epic 2): gate -> inline resolve -> charge.
  * ITEMS_JSON    — multi-item (Epic 3): resolve once, charge each pre-vetted item.

The Stripe key never touches disk, git, logs, or any model context (FR011/FR012):
it lives only in `key` for the duration of the charge calls, then is dropped.
"""
import asyncio
import json
import os


def _gate(m: dict) -> tuple[bool, str]:
    """Deterministic policy gate, mirrored from app/policy.py (intentionally duplicated
    so the canonical decision happens inside the isolated sandbox)."""
    if m["amount_cents"] > m["budget_cents"]:
        return False, "over-budget"
    allow = {v.strip().casefold() for v in m["vendor_allowlist"]}
    if m["vendor"].strip().casefold() not in allow:
        return False, "off-allowlist"
    return True, ""


async def _resolve_key():
    from onepassword.client import Client

    token = os.environ["OP_SERVICE_ACCOUNT_TOKEN"]
    vault = os.environ.get("OP_VAULT", "agent-identity")
    client = await Client.authenticate(
        auth=token, integration_name="claim-by-text-sandbox", integration_version="0.1.0",
    )
    # INLINE resolve — used immediately, never persisted.
    return await client.secrets.resolve(f"op://{vault}/stripe/test_key")


def _charge(stripe, *, amount_cents, vendor, owner_phone, intent) -> dict:
    params = dict(
        amount=amount_cents, currency="usd", payment_method="pm_card_visa", confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        # Vendor up front in the description + as metadata, so the Stripe dashboard
        # clearly shows who was paid and on whose authority.
        description=f"{vendor} — {intent}",
        metadata={"vendor": vendor, "owner_phone": owner_phone, "intent": intent,
                  "amount_cents": str(amount_cents)},
    )
    # STRIPE_MODE=connect: destination charge to the vendor's connected account.
    if os.environ.get("STRIPE_MODE", "simple") == "connect":
        roster = json.loads(os.environ.get("VENDOR_ROSTER", "{}"))
        acct = next((a for n, a in roster.items() if n.strip().casefold() == vendor.strip().casefold()), None)
        if not acct:
            return {"outcome": "denied", "reason": "vendor-not-payable", "charge_id": None}
        params["transfer_data"] = {"destination": acct}
    intent_obj = stripe.PaymentIntent.create(**params)
    return {"outcome": "allowed", "reason": "", "charge_id": intent_obj.id}


async def _single(m: dict) -> dict:
    allowed, reason = _gate(m)
    if not allowed:
        return {"outcome": "denied", "reason": reason, "charge_id": None}
    key = await _resolve_key()
    import stripe

    stripe.api_key = key
    result = _charge(stripe, amount_cents=m["amount_cents"], vendor=m["vendor"],
                     owner_phone=m["owner_phone"], intent=m["task"])
    del key
    return result


async def _items(items: list) -> list:
    key = await _resolve_key()
    import stripe

    stripe.api_key = key
    owner = os.environ.get("OWNER_PHONE", "")
    out = []
    for it in items:  # already vetted (gate + grounding) by the orchestrator
        out.append({"description": it["description"], **_charge(
            stripe, amount_cents=it["amount_cents"], vendor=it["vendor"],
            owner_phone=owner, intent=it["description"])})
    del key
    return out


def main() -> None:
    try:
        if os.environ.get("ITEMS_JSON"):
            result = asyncio.run(_items(json.loads(os.environ["ITEMS_JSON"])))
        else:
            result = asyncio.run(_single(json.loads(os.environ["MANIFEST_JSON"])))
    except Exception as exc:
        result = {"outcome": "denied", "reason": "charge-error", "charge_id": None, "error": str(exc)}
    print(json.dumps(result))  # orchestrator reads the last line


if __name__ == "__main__":
    main()
