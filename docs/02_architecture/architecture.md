# Architecture — Claim-an-Agent-by-Text

*Lean hackathon architecture. 2 people, 3 hours. Source: `docs/01_product_requirements/PRD.md` +
`epics.md`. Deliberately minimal — see "What we are NOT doing" at the end.*

## Executive Summary

A Python monolith **orchestrator on Railway** handles the WhatsApp conversation (claim → verify →
delegate), and per task spins an **ephemeral Daytona sandbox** that resolves the Stripe key from
**1Password at charge time**, enforces a deterministic policy gate, and is destroyed on completion.
Two runtimes make the thesis a deployment fact: *who delegated* (verified phone, on Railway) is
separate from *authority to act* (runtime-resolved credential, in the sandbox).

## Decision Summary

| Concern | Decision | Rationale | Affects |
|---|---|---|---|
| Language | **Python 3.11+** | All four SDKs (1Password, Daytona, Stripe, OpenAI-compat) are clean in Python; fastest for the agent loop | All |
| Orchestrator host | **Railway** | Public HTTPS webhook out of the box (no ngrok); stable URL for Twilio; logs = live audit stream | Epic 1 |
| Web framework | **FastAPI + uvicorn** | One `POST /webhook`; async; trivial | Epic 1 |
| Chat channel | **Twilio WhatsApp Sandbox** + **mock shim** | Same-day, no A2P; mock shim = offline backstop | Epic 1 |
| Agent sandbox | **Daytona** (Python SDK) | Ephemeral attested workload; remote API callable from Railway | Epic 2 |
| Secrets (agent) | **1Password SDK + Service Account**, resolved **in-sandbox at charge time** | Stripe key never in Railway, disk, git, or agent context | Epic 2 |
| Secrets (operational) | **Railway env vars** | Twilio/Nebius/Daytona/SA-token plumbing; the *demoed* secret stays in 1Password | All |
| LLM (manifest parse) | **Nebius Token Factory**, `meta-llama/Llama-3.3-70B-Instruct` (alt `Qwen/Qwen2.5-7B-Instruct`) via `openai` client + JSON mode | Reliable structured extraction; OpenAI-compatible | Epic 2 |
| Payments | **Stripe test mode** (PaymentIntent + `pm_card_visa`) | No real funds; one call | Epic 2 |
| Owner registry | **1Password vault item** per owner + **local JSON** cache/fallback | Identity registry in the vault; JSON keeps the loop fast/resilient | Epic 1 |
| Policy gate | **Plain Python**, deterministic | Containment can't depend on model output | Epic 2 |
| Audit | **JSONL to stdout** (+ file) | Railway log view is the demo's live audit stream; no OTel | Epic 2 |

*Versions: install latest stable, pin in `requirements.txt` at first install. Confirm Nebius model
IDs in their model list (they rename occasionally).*

## Project Structure

```
claim-by-text/
├── app/
│   ├── main.py              # FastAPI app + POST /webhook (Twilio); shared inbound handler
│   ├── conversation.py      # state machine: NEW → AWAITING_NAME → READY
│   ├── channel/
│   │   ├── base.py          # ChannelAdapter: receive(req)->Msg, send(to, text)
│   │   ├── whatsapp.py      # Twilio WhatsApp Sandbox adapter
│   │   └── mock.py          # CLI mock shim (same interface)
│   ├── registry.py          # owner records: 1P vault item + JSON fallback
│   ├── manifest.py          # IntentManifest (pydantic) + Nebius parse(text)->manifest
│   ├── policy.py            # evaluate(manifest) -> ALLOW | DENY(reason)  [deterministic]
│   ├── sandbox.py           # Daytona create → run workload → destroy
│   ├── audit.py             # emit(event) -> JSONL stdout + file
│   └── workload/
│       └── execute_charge.py  # RUNS INSIDE DAYTONA: 1P resolve → gate → Stripe → audit → JSON out
├── run_mock.py              # local entrypoint using mock.py (offline demo backstop)
├── requirements.txt
├── Procfile                 # web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
└── README.md
```

**Epic → code map:** Epic 1 → `main.py`, `conversation.py`, `channel/`, `registry.py`, `manifest.py`
(schema). Epic 2 → `sandbox.py`, `workload/execute_charge.py`, `policy.py`, `audit.py`, `manifest.py`
(parse).

## Novel Pattern: Delegation/Authority Split via Two Runtimes

**Purpose**: Keep *who delegated* and *authority to act* in separate trust domains — physically, not
just logically.

| Component | Runtime | Responsibility |
|---|---|---|
| Orchestrator | Railway | WhatsApp I/O, verify owner (phone), build manifest, invoke sandbox, stream audit |
| Sandbox workload | Daytona (ephemeral) | Resolve Stripe key from 1P, enforce policy gate, charge, return outcome, self-destruct |

**Data flow (one delegated task):**
1. Verified owner texts a task → Railway orchestrator parses it (Nebius) into an `IntentManifest`
   (`owner_phone, task, amount_cents, vendor, budget_cents, vendor_allowlist, ttl`).
2. Orchestrator creates a Daytona sandbox, passing the SA token (env) + manifest (input). Records
   `sandbox_id`.
3. Inside the sandbox, `execute_charge.py`: authenticates to 1Password with the SA token → runs
   `policy.evaluate(manifest)` → on ALLOW, resolves `op://Vault/Stripe/credential` **inline** and
   creates a Stripe test charge → emits an audit event → returns JSON `{outcome, reason, charge_id}`.
4. Orchestrator destroys the sandbox (in `finally`), texts the owner the result, streams the audit
   line.

**Why both runtimes earn their place:** Railway = the delegating principal's surface; Daytona = the
disposable, attested workload that holds authority for one task only. Remove either and the story
breaks.

## Key Contracts (the integration seam — agree first)

```python
# channel/base.py
class ChannelAdapter(Protocol):
    def parse_inbound(self, req) -> tuple[str, str]: ...   # (from_phone, text)
    def send(self, to_phone: str, text: str) -> None: ...

# manifest.py
class IntentManifest(BaseModel):
    owner_phone: str          # the verified human principal
    task: str
    amount_cents: int
    vendor: str
    budget_cents: int
    vendor_allowlist: list[str]
    ttl_seconds: int = 300

# policy.py
def evaluate(m: IntentManifest) -> Verdict:   # deterministic, no I/O
    if m.amount_cents > m.budget_cents: return DENY("over-budget")
    if m.vendor not in m.vendor_allowlist: return DENY("off-allowlist")
    return ALLOW
```

**Audit event shape** (`credential_ref` is a reference, never the value):
```json
{"ts","owner_phone","agent_id","sandbox_id","credential_ref":"op://Vault/Stripe/credential",
 "intent","action":"charge","outcome":"allowed|denied","reason","charge_id"}
```

## Conventions (minimal)

- snake_case modules/functions; `IntentManifest`/`Verdict` PascalCase models.
- One conversation state per phone, stored on the owner record (`NEW | AWAITING_NAME | READY`).
- Phone numbers hashed (sha256) as registry keys; raw phone only in WhatsApp transport + audit `owner`.
- Money in **integer cents** everywhere; never floats.
- The policy gate does **no I/O** and is the only place ALLOW/DENY is decided.

## Secrets & Config

| Secret | Lives in | Used by |
|---|---|---|
| `OP_SERVICE_ACCOUNT_TOKEN` | Railway env (and passed to sandbox) | bootstrap auth to 1Password |
| `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | Railway env | send/verify WhatsApp |
| `NEBIUS_API_KEY` (+ base URL) | Railway env | manifest parse |
| `DAYTONA_API_KEY` | Railway env | create/destroy sandbox |
| **Stripe secret key** | **1Password vault only** | resolved **in-sandbox at charge time** — never in Railway/agent context |

*Optional upgrade (skip for 3 hrs): resolve the operational creds from 1Password too, leaving only the
SA token in Railway.*

## Dev & Deploy

**Local (offline backstop):**
```bash
pip install -r requirements.txt
python run_mock.py            # drive the whole flow from the terminal, no WhatsApp/Railway
```

**Railway:**
1. Connect repo; Nixpacks auto-detects Python from `requirements.txt`.
2. `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Set env vars (table above).
4. Point Twilio WhatsApp Sandbox inbound webhook → `https://<app>.up.railway.app/webhook`.
5. Watch Railway logs = live audit stream during the demo.

**First 30-min smoke test (highest risk):** prove `execute_charge.py` runs inside a Daytona sandbox,
authenticates to 1Password with the SA token, and resolves the Stripe key. Fallback if SDK auth
fights: pass the resolved key as a sandbox secret via 1Password Environments injection at create-time
(documented in `sandbox.py`).

## What We Are NOT Doing (anti-overengineering guardrails)

- No database server (JSON file + vault items only). No ORM, no migrations.
- No message queue, no background workers — synchronous request → sandbox → reply.
- No container orchestration beyond Daytona; no Dockerfile (Nixpacks).
- No auth framework, no sessions — the phone number *is* the identity.
- No conformance monitor — the deterministic policy gate replaces it.
- No tests except policy-gate unit cases (the one place correctness must be guaranteed).
- No OpenTelemetry — JSONL to stdout is the audit trail.
- No second 1Password mechanism (Broker/MCP/Apono) — SDK only.
