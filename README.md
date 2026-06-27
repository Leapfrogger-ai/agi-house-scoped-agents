# Claim-an-Agent-by-Text

Claim and become the **verified owner** of an agent entirely over text — no website,
app, or signup — then delegate a spending task to it. Your **phone number is the
ownership credential**; **1Password** + a **Daytona** sandbox supply the agent's
runtime authority; every action attributes back to you.

> **The question this answers:** When your agent acts, is it acting as itself or as you?
> Where does its authority come from, and who answers for what it does?

Two trust domains, kept **physically** separate:

- **Who delegated** → your verified phone number (the orchestrator, on Railway).
- **Authority to act** → a Stripe key resolved **inline from 1Password at charge time**,
  inside an **ephemeral Daytona sandbox** that is destroyed when the task ends.

## Quick start (offline, no accounts)

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python run_mock.py
```

Then type the demo script:

```
CLAIM
Budgetbot
buy office supplies, $30 from Acme     # ✅ paid (simulated until creds are wired)
buy $80 of supplies from Acme          # 🛑 over budget — no charge
pay EvilCorp $20                        # 🛑 off allowlist — no charge
hey                                     # 👋 welcome back
```

Without `DAYTONA_API_KEY` + `OP_SERVICE_ACCOUNT_TOKEN`, the charge is **simulated**
through the *real* policy gate, so the conversation demo runs fully offline (NFR005).
With both set, the charge runs for real inside a Daytona sandbox.

## Tests

```bash
uv pip install pytest
pytest            # policy gate (the correctness guarantee) + conversation flow
```

## Layout

| Path | Role |
|---|---|
| `app/channel/` | `ChannelAdapter` contract + mock shim + WhatsApp adapter (FR001-003) |
| `app/manifest.py` | `IntentManifest` contract + task-text parse (Nebius / regex fallback) |
| `app/conversation.py` | state machine: `NEW → AWAITING_NAME → READY` |
| `app/registry.py` / `registry_vault.py` | owner records: JSON fallback + 1Password vault items |
| `app/policy.py` | deterministic ALLOW/DENY gate — **the** containment guarantee |
| `app/sandbox.py` | Daytona ephemeral lifecycle (create → run → destroy) |
| `app/workload/execute_charge.py` | **runs in the sandbox**: 1P resolve → gate → Stripe charge |
| `app/audit.py` | JSONL audit: `owner → sandbox → credential_ref → intent → outcome` |
| `app/main.py` | FastAPI `POST /webhook` (Twilio) |

## Configuration

Copy `.env.example` → `.env`. The **Stripe key is deliberately not an env var** — it
lives only in 1Password (`op://agent-identity/stripe/test_key`) and is resolved inside
the sandbox at charge time (FR011/FR012). Channel selected by `CHANNEL=mock|whatsapp`.

## Deploy (Railway)

Nixpacks auto-detects Python from `requirements.txt`; `Procfile` runs uvicorn. Set the
env vars from `.env.example` (minus the Stripe key), then point the Twilio WhatsApp
Sandbox inbound webhook at `https://<app>.up.railway.app/webhook`. Railway logs are the
live audit stream.

See `docs/` for the PRD, architecture, epics, conversation design, and provisioning guide.
