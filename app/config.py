"""Central config, sourced from env only — never hard-coded secrets (Story 1.1 AC3)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Config:
    channel: str = os.getenv("CHANNEL", "mock")

    # 1Password
    op_token: str | None = os.getenv("OP_SERVICE_ACCOUNT_TOKEN") or None
    op_vault: str = os.getenv("OP_VAULT", "agent-identity")

    # Stripe charge routing. "simple" = card charge into the platform (proven default).
    # "connect" = destination charge that routes funds to the vendor's connected account
    # (requires Connect enabled + a populated VENDOR_ROSTER). See app/vendors.py.
    stripe_mode: str = os.getenv("STRIPE_MODE", "simple")
    vendor_roster_json: str = os.getenv("VENDOR_ROSTER", "{}")  # {"Acme":"acct_...",...}

    # Daytona
    daytona_api_key: str | None = os.getenv("DAYTONA_API_KEY") or None
    # Default true (auto-destroy = the thesis). Set false for a demo where you want to
    # watch the sandbox persist in the Daytona dashboard before tearing it down.
    sandbox_destroy: bool = os.getenv("SANDBOX_DESTROY", "true").lower() not in ("0", "false", "no")

    # Nebius (manifest parse) — OpenAI-compatible
    nebius_api_key: str | None = os.getenv("NEBIUS_API_KEY") or None
    nebius_base_url: str = os.getenv("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1")
    nebius_model: str = os.getenv("NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

    # Twilio (stretch)
    twilio_sid: str | None = os.getenv("TWILIO_ACCOUNT_SID") or None
    twilio_token: str | None = os.getenv("TWILIO_AUTH_TOKEN") or None
    twilio_from: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Owner defaults applied at claim time
    default_budget_cents: int = int(os.getenv("DEFAULT_BUDGET_CENTS", "5000"))
    default_allowlist: list[str] = field(
        default_factory=lambda: _csv(os.getenv("DEFAULT_ALLOWLIST", "Acme"))
    )

    # Where the Stripe key is referenced — the value never leaves 1Password.
    @property
    def stripe_credential_ref(self) -> str:
        return f"op://{self.op_vault}/stripe/test_key"

    @property
    def op_configured(self) -> bool:
        return bool(self.op_token)

    @property
    def daytona_configured(self) -> bool:
        return bool(self.daytona_api_key)

    @property
    def nebius_configured(self) -> bool:
        return bool(self.nebius_api_key)


config = Config()
