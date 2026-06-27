"""Daytona ephemeral sandbox lifecycle (Stories 2.1/2.2).

create -> upload the workload -> run it (passing the SA token + manifest) ->
ALWAYS destroy in `finally`. The sandbox is the agent's runtime identity; it holds
authority for exactly one task and is then gone (NFR004 — nothing between tasks).

NOTE: the live Daytona API shape is verified once DAYTONA_API_KEY is in hand. Any
failure here degrades to the local simulation in tasking.py so the demo can't be
blocked by a sandbox hiccup (NFR005).
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import config
from app.manifest import IntentManifest
from app.tasking import ChargeResult, _simulate

_WORKLOAD = Path(__file__).parent / "workload" / "execute_charge.py"


def run_charge(manifest: IntentManifest) -> ChargeResult:
    try:
        return _run_in_daytona(manifest)
    except Exception as exc:  # demo-resilient: fall back, never crash the thread
        print(f"[sandbox] degraded to simulation: {exc}", flush=True)
        return _simulate(manifest)


def _run_in_daytona(manifest: IntentManifest) -> ChargeResult:
    from daytona import CreateSandboxFromImageParams, Daytona, DaytonaConfig

    client = Daytona(DaytonaConfig(api_key=config.daytona_api_key))
    sandbox = None
    try:
        sandbox = client.create(
            CreateSandboxFromImageParams(
                image="python:3.11-slim",
                # ephemeral only when we'll auto-destroy; kept-alive demos must persist.
                ephemeral=config.sandbox_destroy,
                # labels make the sandbox identifiable in the Daytona dashboard.
                labels={
                    "app": "claim-by-text",
                    "owner": manifest.owner_phone[:16],
                    "intent": manifest.task[:60],
                },
                env_vars={
                    # SA token reaches the sandbox so it can auth headlessly to 1Password.
                    "OP_SERVICE_ACCOUNT_TOKEN": config.op_token or "",
                    "OP_VAULT": config.op_vault,
                    "MANIFEST_JSON": manifest.model_dump_json(),
                },
            )
        )
        sandbox_id = getattr(sandbox, "id", None)

        sandbox.process.exec("pip install --quiet onepassword-sdk stripe")
        code = _WORKLOAD.read_text()
        resp = sandbox.process.code_run(code)
        out = (getattr(resp, "result", None) or getattr(resp, "stdout", "") or "").strip()
        data = json.loads(out.splitlines()[-1])  # workload prints JSON on its last line
        return ChargeResult(
            outcome=data["outcome"],
            reason=data.get("reason", ""),
            charge_id=data.get("charge_id"),
            sandbox_id=sandbox_id,
            simulated=False,
        )
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
