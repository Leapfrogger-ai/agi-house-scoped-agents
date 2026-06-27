"""Delegation hot path (Stories 2.4/2.5): task text -> manifest -> charge -> reply.

The actual ALLOW/DENY + credential resolve + charge happen inside the Daytona
sandbox (app/sandbox.py -> app/workload/execute_charge.py). When the sponsor
credentials aren't wired yet, a local simulation runs the SAME deterministic gate
so the conversation demo works fully offline — clearly flagged in the audit line.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app import audit, copy
from app.config import config
from app.manifest import IntentManifest, ParseError, parse_task
from app.policy import evaluate
from app.registry import OwnerRecord


@dataclass(frozen=True)
class ChargeResult:
    outcome: str            # "allowed" | "denied"
    reason: str             # "" | "over-budget" | "off-allowlist" | "charge-error"
    charge_id: str | None
    sandbox_id: str | None
    simulated: bool


def delegate(record: OwnerRecord, text: str) -> str:
    try:
        # owner_phone = the verified principal (hashed); proves who delegated.
        manifest = parse_task(
            record.hashed_phone,
            text,
            budget_cents=record.budget_cents,
            allowlist=record.vendor_allowlist,
        )
    except ParseError:
        return copy.BAD_TASK

    if config.daytona_configured and config.op_configured:
        from app.sandbox import run_charge

        result = run_charge(manifest)
    else:
        result = _simulate(manifest)

    audit.emit(
        owner_phone=manifest.owner_phone,
        agent_id=record.agent_id,
        sandbox_id=result.sandbox_id,
        credential_ref=config.stripe_credential_ref,
        intent=manifest.task,
        action="charge",
        outcome=result.outcome,
        reason=result.reason if result.outcome == "denied" else ("simulated" if result.simulated else ""),
        charge_id=result.charge_id,
    )
    return _reply(manifest, result)


def _simulate(m: IntentManifest) -> ChargeResult:
    """Offline path: run the real gate, fake the Stripe call. No funds, no network."""
    verdict = evaluate(m)
    if not verdict.allowed:
        return ChargeResult("denied", verdict.reason, None, "(simulated)", True)
    fake_id = "sim_" + hashlib.sha1(f"{m.vendor}{m.amount_cents}".encode()).hexdigest()[:10]
    return ChargeResult("allowed", "", fake_id, "(simulated)", True)


def _reply(m: IntentManifest, r: ChargeResult) -> str:
    if r.outcome == "denied":
        if r.reason == "off-allowlist":
            return copy.denied_allowlist(m.vendor)
        if r.reason == "over-budget":
            return copy.denied_budget(_d(m.amount_cents), _d(m.budget_cents))
        return copy.CHARGE_BROKE
    remaining = max(0, m.budget_cents - m.amount_cents)
    return copy.receipt(m.vendor, _d(m.amount_cents), _d(remaining), r.charge_id or "pending")


def _d(cents: int) -> str:
    return f"{cents / 100:.2f}"
