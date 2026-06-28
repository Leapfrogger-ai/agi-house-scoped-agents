"""Delegation hot path (Stories 2.4/2.5): task text -> manifest -> charge -> reply.

The actual ALLOW/DENY + credential resolve + charge happen inside the Daytona
sandbox (app/sandbox.py -> app/workload/execute_charge.py). When the sponsor
credentials aren't wired yet, a local simulation runs the SAME deterministic gate
so the conversation demo works fully offline — clearly flagged in the audit line.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app import audit, catalog, copy, grounding
from app.config import config
from app.manifest import IntentManifest, Item, ParseError, parse_task
from app.policy import evaluate, evaluate_fields
from app.registry import OwnerRecord, Registry


MAX_ITEMS = 5


@dataclass(frozen=True)
class ChargeResult:
    outcome: str            # "allowed" | "denied"
    reason: str             # "" | "over-budget" | "off-allowlist" | "charge-error"
    charge_id: str | None
    sandbox_id: str | None
    simulated: bool


def delegate(record: OwnerRecord, text: str, registry: Registry) -> str:
    """Route a purchase. Catalog items -> the intent-check loop; anything else ->
    the original single-charge path (unchanged)."""
    goal = catalog.extract_goal(text)
    if goal and goal != record.active_goal:
        record.active_goal = goal           # declared goal persists for later items
        registry.upsert(record)

    items = catalog.scan(text)
    if items:
        return _multi(record, items)
    return _single(record, text)


def _single(record: OwnerRecord, text: str) -> str:
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

    # Deterministic policy gate at the orchestrator: a denial is decided HERE, instantly,
    # and no sandbox is ever spun for an out-of-policy task (NFR003 + NFR004 — containment
    # so complete the denied task gets no runtime). The same gate runs again inside the
    # sandbox on the allowed path, as defense-in-depth.
    verdict = evaluate(manifest)
    if not verdict.allowed:
        result = ChargeResult("denied", verdict.reason, charge_id=None, sandbox_id=None, simulated=False)
    elif config.daytona_configured and config.op_configured:
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
        vendor=manifest.vendor,
        amount_cents=manifest.amount_cents,
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
        if r.reason == "vendor-not-payable":
            return copy.denied_not_payable(m.vendor)
        return copy.CHARGE_BROKE
    remaining = max(0, m.budget_cents - m.amount_cents)
    return copy.receipt(m.vendor, _d(m.amount_cents), _d(remaining), r.charge_id or "pending")


def _d(cents: int) -> str:
    return f"{cents / 100:.2f}"


# --- Intent Check: multi-item loop (Epic 3) -------------------------------------
def _multi(record: OwnerRecord, items: list[Item]) -> str:
    """Vet each item at the orchestrator (gate, then grounding vs the declared goal),
    halting at the FIRST gate-deny or intent-drift, then charge the conforming prefix
    in one sandbox. Both checks run before any charge (fail-closed)."""
    goal = record.active_goal
    approved: list[Item] = []
    halt: tuple[Item, str] | None = None
    for it in items[:MAX_ITEMS]:
        gate = evaluate_fields(it.amount_cents, it.vendor, record.budget_cents, record.vendor_allowlist)
        if not gate.allowed:
            halt = (it, gate.reason)
            break
        if goal:
            conform, _reason = grounding.check(goal, it.description)
            if not conform:
                halt = (it, "intent-drift")
                break
        approved.append(it)

    results = _charge_items(record, approved)
    for it, r in zip(approved, results):
        audit.emit(
            owner_phone=record.hashed_phone, agent_id=record.agent_id, sandbox_id=r["sandbox_id"],
            credential_ref=config.stripe_credential_ref, intent=it.description, goal=goal or "",
            action="charge", outcome="allowed", reason="simulated" if r.get("simulated") else "",
            charge_id=r["charge_id"], vendor=it.vendor, amount_cents=it.amount_cents,
        )
    if halt:
        it, reason = halt
        audit.emit(
            owner_phone=record.hashed_phone, agent_id=record.agent_id, sandbox_id=None,
            credential_ref=config.stripe_credential_ref, intent=it.description, goal=goal or "",
            action="charge", outcome="denied", reason=reason, charge_id=None,
            vendor=it.vendor, amount_cents=it.amount_cents,
        )
    return _multi_reply(record, results, halt, goal)


def _charge_items(record: OwnerRecord, items: list[Item]) -> list[dict]:
    if not items:
        return []
    if config.daytona_configured and config.op_configured:
        from app.sandbox import run_items

        return run_items(items, record.hashed_phone)
    out = []
    for it in items:  # offline: fake the charges, no funds, no network
        fid = "sim_" + hashlib.sha1(f"{it.vendor}{it.amount_cents}{it.description}".encode()).hexdigest()[:10]
        out.append({"description": it.description, "amount_cents": it.amount_cents,
                    "vendor": it.vendor, "charge_id": fid, "sandbox_id": "(simulated)", "simulated": True})
    return out


def _multi_reply(record: OwnerRecord, results: list[dict], halt, goal: str | None) -> str:
    lines = [copy.bought(r["description"], _d(r["amount_cents"]), r["vendor"]) for r in results]
    if results:
        spent = sum(r["amount_cents"] for r in results)
        lines.append(copy.items_total(_d(spent), _d(record.budget_cents)))
    if halt:
        it, reason = halt
        if reason == "intent-drift":
            lines.append(copy.denied_intent(it.description, goal or "the task"))
        elif reason == "over-budget":
            lines.append(copy.denied_budget(_d(it.amount_cents), _d(record.budget_cents)))
        elif reason == "off-allowlist":
            lines.append(copy.denied_allowlist(it.vendor))
        elif reason == "vendor-not-payable":
            lines.append(copy.denied_not_payable(it.vendor))
        else:
            lines.append(copy.CHARGE_BROKE)
    return "\n".join(lines) if lines else copy.BAD_TASK
