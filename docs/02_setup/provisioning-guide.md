# Provisioning Guide — Claim-an-Agent-by-Text

*Setup guide for the AGI House Agent Identity build. Source: `docs/01_product_requirements/PRD.md`
+ `epics.md`.*

**Locked decisions:**
- **Runtime:** Python (3.12 via `uv`)
- **Demo posture:** Mock-shim first; WhatsApp Sandbox is a stretch
- **Deployment:** Railway (orchestrator) + Daytona (ephemeral agent sandbox)

---

## Architecture at a glance

```
text → Twilio WhatsApp ─┐
                        ▼
              Railway container  ← long-lived orchestrator (webhook, state machine,
              (your app)            policy gate, audit log, owner registry)
                        │  HTTPS + DAYTONA_API_KEY
                        ▼
              Daytona cloud ──spawns──▶ ephemeral sandbox (the agent)
                                              │ 1Password SDK: secrets.resolve("op://...")
                                              ▼
                                        Stripe test charge → destroy sandbox → reply
```

- **Railway** = the front door. Never touches the Stripe key.
- **Daytona** = disposable hands. Resolves the credential inline, charges, is destroyed.
- They have **no native integration** — Railway-hosted code just calls the Daytona REST API over HTTPS.
- This separation *is* the authority story (NFR002): delegation identity (phone) and
  authority-to-act (1Password runtime credential) live in different trust domains.

---

## Toolchain status (this machine)

| Tool | Status | Notes |
|------|--------|-------|
| `uv` + Python 3.12 | ✅ ready | System Python is 3.7.4 — too old; use `uv` for a pinned 3.12 venv |
| `railway` 5.18.0 | ✅ | |
| `daytona` 0.173.0 | ✅ | |
| `op` (1Password) 2.34.1 | ✅ installed | |
| `stripe` 1.43.2 | ✅ installed | |
| `twilio` 6.2.4 | ✅ installed | Only needed for the WhatsApp stretch |
| `node` 22, `docker` 28, `gh` 2.59 | ✅ | |

Install commands used (for reference / reprovision on another machine):

```bash
uv python install 3.12
brew install 1password-cli stripe/stripe-cli/stripe twilio/brew/twilio
# railway + daytona CLIs were already present
```

---

## Accounts you must create (human-gated)

These need a browser login, your email, or your phone — they cannot be automated.

| # | Service | What to create | Hand over |
|---|---------|----------------|-----------|
| 1 | **1Password** | Service Account + empty vault `agent-identity` | `OP_SERVICE_ACCOUNT_TOKEN` (`ops_...`) |
| 2 | **Daytona** | API key | `DAYTONA_API_KEY` |
| 3 | **Stripe** | Test-mode secret key | `sk_test_...` |
| 4 | **Anthropic** | API key (or opt for regex parser) | `ANTHROPIC_API_KEY` *(optional)* |
| 5 | **Twilio** | WhatsApp Sandbox + `join <phrase>` from phone | Account SID + Auth Token *(stretch)* |
| 6 | **Railway** | Already have ✅ | `railway login` or a project token |

---

## Step-by-step

### 1. 1Password — Service Account + vault 🔴 highest risk, do first

1. Go to <https://developer.1password.com> → **Service Accounts** → create one.
2. Create a new empty vault, e.g. `agent-identity`, and grant the Service Account access to it.
3. Copy the `ops_...` token.

Verify (run after token is provided):

```bash
export OP_SERVICE_ACCOUNT_TOKEN=ops_...
op whoami
op vault list
```

The owner registry (Story 1.5) and the Stripe key (Story 2.2) both live in this vault.

### 2. Daytona — API key

1. Go to <https://app.daytona.io> → **Keys** → generate an API key.
2. Copy `DAYTONA_API_KEY`.

Smoke-test early (PRD says within first 30 min — highest-risk wiring):

```bash
export DAYTONA_API_KEY=...
# create + destroy one sandbox; confirm 1Password SDK auth works *inside* it
```

Backstop if SDK auth fights inside the sandbox: `op run --environment` env-injection (FR / Story 2.2 AC4).

### 3. Stripe — test key

1. <https://dashboard.stripe.com> → toggle **Test mode** (top right).
2. Developers → API keys → copy the **secret** key `sk_test_...`.

The key is **stored in 1Password, not in env** (that's the point of FR011 — resolved inline at charge
time). Store it:

```bash
op item create --vault agent-identity --title stripe \
  --category "API Credential" test_key="sk_test_..."
# referenced at runtime as op://agent-identity/stripe/test_key
```

### 4. Anthropic — manifest parsing (optional)

Used in Story 2.4 to parse "buy office supplies, $30 from Acme" → intent manifest.
If no key, we use a deterministic regex/simple parser instead.

```bash
export ANTHROPIC_API_KEY=...   # tied to rodolfo@leapfrogger.ai if available
```

### 5. Twilio — WhatsApp Sandbox 🟡 stretch (mock-first)

Deferred. When wiring live:

1. <https://console.twilio.com> → Messaging → Try it out → **WhatsApp Sandbox**.
2. From your phone, send `join <phrase>` to the sandbox number (opens the 24-hr session window —
   pre-join the demo phone and rehearse within the window).
3. Set the inbound webhook to the Railway URL `https://<app>.up.railway.app/webhook`.

```bash
twilio login   # Account SID + Auth Token
```

### 6. Railway — deploy

```bash
railway login                       # interactive, OR paste a project token for headless
railway init
railway variables set OP_SERVICE_ACCOUNT_TOKEN=... DAYTONA_API_KEY=... ANTHROPIC_API_KEY=...
railway up
railway domain                      # → public webhook URL for Twilio
```

Note: the **Stripe key is NOT a Railway env var** — it stays in 1Password and is resolved inside the
Daytona sandbox. Railway only holds what the orchestrator needs to call out.

---

## Environment variables — where each lives

| Variable | Railway env | Daytona sandbox | Notes |
|----------|:-----------:|:---------------:|-------|
| `OP_SERVICE_ACCOUNT_TOKEN` | ✅ | ✅ | Orchestrator reads registry; sandbox resolves Stripe key |
| `DAYTONA_API_KEY` | ✅ | — | Orchestrator spawns sandboxes |
| `ANTHROPIC_API_KEY` | ✅ | — | Manifest parsing (optional) |
| `STRIPE_TEST_KEY` | ❌ | resolved inline | Lives in 1Password `op://agent-identity/stripe/test_key` only |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | ✅ (stretch) | — | Only if WhatsApp is wired |

---

## Fastest unblock order

1. **1Password token + Daytona API key** → unlocks the riskiest integration (secret-resolve inside
   sandbox). Get these to me first.
2. **Stripe key** → enables the actual charge.
3. **Anthropic key** (or "regex") → manifest parsing.
4. **Twilio + Railway deploy** → last, once the flow works locally on the mock shim.

Story 1.1 scaffold (contracts module, mock shim, config, policy-gate skeleton) needs **no accounts**
and can start immediately in parallel.
