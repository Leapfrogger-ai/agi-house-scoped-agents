"""Daytona ephemeral sandbox lifecycle (Stories 2.1/2.2).

create -> upload the workload -> run it (passing the SA token + manifest) ->
ALWAYS destroy in `finally`. The sandbox is the agent's runtime identity; it holds
authority for exactly one task and is then gone (NFR004 — nothing between tasks).

NOTE: the live Daytona API shape is verified once DAYTONA_API_KEY is in hand. Any
failure here degrades to the local simulation in tasking.py so the demo can't be
blocked by a sandbox hiccup (NFR005).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.config import config
from app.manifest import IntentManifest, Item
from app.tasking import ChargeResult, _simulate

_WORKLOAD = Path(__file__).parent / "workload" / "execute_charge.py"


def run_charge(manifest: IntentManifest) -> ChargeResult:
    """Single charge in one ephemeral sandbox (Epic 2 path)."""
    try:
        sandbox_id, data = _run_workload(
            {"MANIFEST_JSON": manifest.model_dump_json()},
            labels={"app": "claim-by-text", "owner": manifest.owner_phone[:16], "intent": manifest.task[:60]},
        )
        return ChargeResult(
            outcome=data["outcome"], reason=data.get("reason", ""),
            charge_id=data.get("charge_id"), sandbox_id=sandbox_id, simulated=False,
        )
    except Exception as exc:  # demo-resilient: fall back, never crash the thread
        print(f"[sandbox] degraded to simulation: {exc}", flush=True)
        return _simulate(manifest)


def run_items(items: list[Item], owner_phone: str) -> list[dict]:
    """Charge the (already-vetted) approved list inside ONE ephemeral sandbox."""
    payload = [{"description": i.description, "amount_cents": i.amount_cents, "vendor": i.vendor} for i in items]
    try:
        sandbox_id, results = _run_workload(
            {"ITEMS_JSON": json.dumps(payload), "OWNER_PHONE": owner_phone},
            labels={"app": "claim-by-text", "owner": owner_phone[:16], "intent": "multi-item"},
        )
        out = []
        for it, r in zip(items, results):
            out.append({"description": it.description, "amount_cents": it.amount_cents, "vendor": it.vendor,
                        "charge_id": r.get("charge_id"), "sandbox_id": sandbox_id, "simulated": False})
        return out
    except Exception as exc:
        print(f"[sandbox] items degraded to simulation: {exc}", flush=True)
        return [{"description": it.description, "amount_cents": it.amount_cents, "vendor": it.vendor,
                 "charge_id": "sim_" + hashlib.sha1(f"{it.vendor}{it.amount_cents}{it.description}".encode()).hexdigest()[:10],
                 "sandbox_id": "(simulated)", "simulated": True} for it in items]


def _run_workload(extra_env: dict, labels: dict):
    """Create a sandbox, run the workload with shared secrets + given env, return
    (sandbox_id, parsed-last-line-JSON). Always destroys the sandbox in `finally`."""
    from daytona import CreateSandboxFromImageParams, Daytona, DaytonaConfig

    client = Daytona(DaytonaConfig(api_key=config.daytona_api_key))
    sandbox = None
    try:
        sandbox = client.create(
            CreateSandboxFromImageParams(
                image="python:3.11-slim",
                ephemeral=config.sandbox_destroy,  # auto-destroy unless a demo keeps it alive
                labels=labels,
                env_vars={
                    "OP_SERVICE_ACCOUNT_TOKEN": config.op_token or "",
                    "OP_VAULT": config.op_vault,
                    "STRIPE_MODE": config.stripe_mode,
                    "VENDOR_ROSTER": config.vendor_roster_json,
                    **extra_env,
                },
            )
        )
        sandbox_id = getattr(sandbox, "id", None)
        sandbox.process.exec("pip install --quiet onepassword-sdk stripe")
        resp = sandbox.process.code_run(_WORKLOAD.read_text())
        out = (getattr(resp, "result", None) or getattr(resp, "stdout", "") or "").strip()
        return sandbox_id, json.loads(out.splitlines()[-1])  # workload prints JSON on its last line
    finally:
        if sandbox is not None and config.sandbox_destroy:
            try:
                sandbox.delete()
                print(f"[sandbox] destroyed {getattr(sandbox, 'id', '?')} — nothing left to steal", flush=True)
            except Exception as exc:
                print(f"[sandbox] teardown warning: {exc}", flush=True)
        elif sandbox is not None:
            print(f"[sandbox] KEPT ALIVE for demo: {getattr(sandbox, 'id', '?')} "
                  f"(SANDBOX_DESTROY=false) — destroy it manually after", flush=True)
