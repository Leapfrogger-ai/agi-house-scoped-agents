"""RUNS INSIDE THE DAYTONA SANDBOX. Standalone — imports nothing from `app` so it
can run in a bare python:3.11-slim image with only onepassword-sdk + stripe.

Flow (Stories 2.2-2.4): authenticate to 1Password with the Service Account ->
enforce the policy gate -> on ALLOW, resolve the Stripe key INLINE into a local
variable and charge immediately -> print a single JSON line for the orchestrator.

The Stripe key never touches disk, git, logs, or any model context (FR011/FR012):
it lives only in `key` for the duration of one create() call.
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


async def _resolve_and_charge(m: dict) -> dict:
    from onepassword.client import Client

    allowed, reason = _gate(m)
    if not allowed:
        return {"outcome": "denied", "reason": reason, "charge_id": None}

    token = os.environ["OP_SERVICE_ACCOUNT_TOKEN"]
    vault = os.environ.get("OP_VAULT", "agent-identity")
    client = await Client.authenticate(
        auth=token,
        integration_name="claim-by-text-sandbox",
        integration_version="0.1.0",
    )
    # INLINE resolve — one variable, used immediately, never persisted.
    key = await client.secrets.resolve(f"op://{vault}/stripe/test_key")

    import stripe

    stripe.api_key = key
    vendor = m["vendor"]
    intent = stripe.PaymentIntent.create(
        amount=m["amount_cents"],
        currency="usd",
        payment_method="pm_card_visa",
        confirm=True,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        # Vendor up front in the description + as structured metadata, so the Stripe
        # dashboard clearly shows who was paid and on whose authority.
        description=f"{vendor} — {m['task']}",
        metadata={
            "vendor": vendor,
            "owner_phone": m["owner_phone"],
            "intent": m["task"],
            "amount_cents": str(m["amount_cents"]),
        },
    )
    del key  # drop it the instant the charge is made
    return {"outcome": "allowed", "reason": "", "charge_id": intent.id}


def main() -> None:
    manifest = json.loads(os.environ["MANIFEST_JSON"])
    try:
        result = asyncio.run(_resolve_and_charge(manifest))
    except Exception as exc:
        result = {"outcome": "denied", "reason": "charge-error", "charge_id": None, "error": str(exc)}
    print(json.dumps(result))  # orchestrator reads the last line


if __name__ == "__main__":
    main()
