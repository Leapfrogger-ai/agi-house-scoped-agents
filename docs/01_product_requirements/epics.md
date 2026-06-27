# Epics & Stories — Claim-an-Agent-by-Text

*Tactical breakdown of `PRD.md`. Level 2 · 2 epics · 12 stories.*
*Hackathon sizing: stories are ~30–60 min (not the default 2–4 hr); ~6 person-hours total across 2
people. Person A leads Epic 1, Person B leads Epic 2; both start after Story 1.1.*

**Status legend:** Must = demo blocker · Stretch = only if integration finishes early.

---

## Epic 1: Foundation & Verified Ownership over Text

**Goal**: A new number texts in and becomes the verified owner of a named agent, recognized on return.
**Delivers**: chat channel (mock shim + WhatsApp), claim → round-trip verify → vault-backed owner
record → returning-owner recognition, plus the shared contracts both workstreams build against.

---

### Story 1.1: Repo scaffold & shared contracts *(Must — do first, together)*

**As a** two-person team,
**I want** the repo skeleton plus the two shared interfaces (channel adapter + intent manifest),
**So that** both workstreams build to the same seam and integrate cleanly.

**Acceptance Criteria**:
1. Given a fresh clone, when I run the app, then a stub conversation loop starts against the mock shim.
2. Given the contracts module, when either workstream imports it, then the `ChannelAdapter` interface
   (`receive()/send()`) and the `IntentManifest` schema (`owner, task, budget, vendor_allowlist, ttl`)
   are available and typed.
3. Given the repo, when inspected, then secrets are sourced from env/1Password, never committed.

**Tasks**:
- [ ] Project scaffold (package, entrypoint, config, `.gitignore` excluding secrets).
- [ ] `ChannelAdapter` interface + `IntentManifest` schema in a shared `contracts` module.
- [ ] README with run command and the demo script pointer.

**Prerequisites**: none.

---

### Story 1.2: Channel adapter — mock shim + WhatsApp Sandbox *(Must)*

**As a** developer,
**I want** an inbound webhook + outbound send behind the adapter, with a mock shim and a WhatsApp
implementation,
**So that** conversation logic is channel-agnostic and the demo can't be blocked by provisioning.

**Acceptance Criteria**:
1. Given the mock shim, when I type a message in the terminal/web pane, then the app receives it and
   can reply.
2. Given the Twilio WhatsApp Sandbox adapter, when a joined number messages the sandbox, then the same
   webhook handles it identically.
3. Given either adapter, when conversation logic runs, then it is unaware of which channel is active.

**Tasks**:
- [ ] Mock shim (terminal or minimal web pane) implementing `ChannelAdapter`.
- [ ] Twilio WhatsApp Sandbox adapter (inbound webhook + outbound send).
- [ ] Config switch to select the active adapter.

**Prerequisites**: 1.1.

---

### Story 1.3: Claim flow — provision pending agent *(Must)*

**As a** new user,
**I want** my first text to start claiming an agent,
**So that** I can begin owning one with no signup.

**Acceptance Criteria**:
1. Given an unrecognized number, when it texts in, then a new pending agent + pending owner record
   (keyed by hashed phone) is created.
2. Given a new claim, when provisioned, then the system replies asking for a name to confirm.

**Tasks**:
- [ ] Conversation state machine: `NEW → AWAITING_NAME`.
- [ ] Pending agent + pending owner record creation.
- [ ] Claim prompt reply.

**Prerequisites**: 1.2.

---

### Story 1.4: Two-way round-trip verification *(Must)*

**As a** claiming user,
**I want** my reply-to-the-confirmation to establish me as verified owner,
**So that** ownership requires live two-way control of the number.

**Acceptance Criteria**:
1. Given state `AWAITING_NAME`, when the user replies with a name, then the owner is marked
   **verified** and the agent is named and bound to the number.
2. Given verification, when complete, then the system confirms ownership and prompts for a task.
3. Given a single inbound with no reply, then the owner remains unverified.

**Tasks**:
- [ ] State transition `AWAITING_NAME → VERIFIED` on second inbound.
- [ ] Bind number → agent; set agent name.
- [ ] Confirmation + "text a task" reply.

**Prerequisites**: 1.3.

---

### Story 1.5: Owner registry as 1Password vault items *(Must)*

**As a** system,
**I want** verified owner records persisted as 1Password vault items,
**So that** the identity registry itself lives in the vault and survives restart.

**Acceptance Criteria**:
1. Given a verified owner, when established, then a vault item is created/updated with
   `hashed_phone → agent_id → name → verified → history pointer`.
2. Given a lookup by number, when queried, then the owner record is retrieved from the vault.
3. Given the registry under time pressure, when the vault path is slow, then a local SQLite/JSON
   fallback keeps the flow working (documented fallback).

**Tasks**:
- [ ] 1Password SDK write/read of owner item.
- [ ] Registry interface (`get_by_phone`, `upsert`) with vault impl.
- [ ] SQLite/JSON fallback impl behind the same interface.

**Prerequisites**: 1.4.

---

### Story 1.6: Returning-owner recognition *(Must)*

**As a** returning owner,
**I want** my next text to reconnect me to the agent I own,
**So that** my phone number works as my ongoing credential.

**Acceptance Criteria**:
1. Given a verified number, when it texts in, then the system recognizes it and greets the owner by
   agent name.
2. Given recognition, when complete, then the user can immediately issue a task (no re-claim).

**Tasks**:
- [ ] Registry lookup on inbound; route verified numbers to `READY` state.
- [ ] "Welcome back" reply + task prompt.

**Prerequisites**: 1.5.

---

## Epic 2: Delegated Spending with Runtime Authority

**Goal**: A verified owner delegates a spending task by text; the agent executes it in an ephemeral
sandbox using a runtime-resolved credential, within policy, fully attributed.
**Depends on**: Epic 1 (owner identity + manifest contract from Story 1.1).
**Delivers**: Daytona lifecycle, 1Password SDK inline Stripe resolve, policy gate, happy-path charge,
containment denial, audit trail + WhatsApp receipt.

---

### Story 2.1: Daytona ephemeral sandbox lifecycle *(Must)*

**As a** system,
**I want** to spin up a scoped Daytona sandbox per task and destroy it on completion,
**So that** the agent has its own runtime identity and nothing stands between tasks.

**Acceptance Criteria**:
1. Given a task, when execution starts, then a fresh sandbox is created and its id is recorded.
2. Given task completion (success or denial), when finished, then the sandbox is destroyed.
3. Given the sandbox, when inspected, then it carries the runtime identity referenced in the audit log.

**Tasks**:
- [ ] Daytona create/destroy wrapper.
- [ ] Surface sandbox id to the audit layer.
- [ ] Teardown in a `finally` path so it always runs.

**Prerequisites**: 1.1 (contracts).

---

### Story 2.2: 1Password SDK inline credential resolve in-sandbox *(Must)*

**As a** sandboxed agent,
**I want** to authenticate with a Service Account and resolve the Stripe key inline at charge time,
**So that** the credential never lives in my context, disk, or git.

**Acceptance Criteria**:
1. Given the sandbox, when it authenticates, then it uses a 1Password Service Account (headless).
2. Given a charge about to execute, when the key is needed, then it is resolved inline into a local
   variable and used immediately.
3. Given any log/context dump, when inspected, then the raw key never appears.
4. Given SDK auth failure, when it occurs, then the `op run --environment` env-injection backstop
   applies (documented).

**Tasks**:
- [ ] Service Account auth in-sandbox.
- [ ] Inline `secrets.resolve("op://...")` at point of use.
- [ ] `op run` fallback wrapper + note.

**Prerequisites**: 2.1.

---

### Story 2.3: Policy gate — budget + allowlist *(Must)*

**As a** system,
**I want** a deterministic gate evaluated before every charge,
**So that** containment does not depend on model behavior.

**Acceptance Criteria**:
1. Given a manifest and a proposed charge, when amount ≤ budget AND vendor ∈ allowlist, then the gate
   returns ALLOW.
2. Given amount > budget OR vendor ∉ allowlist, then the gate returns DENY with a reason.
3. Given identical inputs, when run repeatedly, then the verdict is identical (deterministic).

**Tasks**:
- [ ] `evaluate(manifest, charge) → {allow|deny, reason}`.
- [ ] Unit cases: in-budget/allowed, over-budget, off-allowlist.

**Prerequisites**: 1.1 (manifest).

---

### Story 2.4: Agent loop — task to compliant charge (happy path) *(Must)*

**As a** verified owner,
**I want** my texted task to result in a real Stripe test charge within policy,
**So that** the agent delivers value under delegated authority.

**Acceptance Criteria**:
1. Given a task text, when parsed, then an intent manifest is built (`owner, amount, vendor, budget,
   allowlist`).
2. Given an allowed manifest, when executed in-sandbox, then a Stripe **test-mode** charge succeeds.
3. Given success, when complete, then the system replies with a receipt by text.

**Tasks**:
- [ ] Task-text → manifest parse (LLM or simple parse; budget/allowlist from owner defaults).
- [ ] Stripe test charge call using the inline-resolved key.
- [ ] Receipt reply via the channel adapter.

**Prerequisites**: 2.1, 2.2, 2.3.

---

### Story 2.5: Containment — denials over text *(Must: over-budget; Stretch: off-allowlist)*

**As a** stakeholder,
**I want** out-of-policy attempts blocked and reported by text,
**So that** the audience sees authority enforced live.

**Acceptance Criteria**:
1. Given an over-budget task, when executed, then the gate denies, no charge occurs, and the system
   texts "❌ Denied — exceeds budget".
2. *(Stretch)* Given an injected "pay EvilCorp" task, when executed, then the gate denies off-allowlist
   and texts the reason.
3. Given any denial, when it happens, then an audit event is recorded.

**Tasks**:
- [ ] Wire gate DENY → no-charge path → denial reply.
- [ ] Hard-coded injection string for the stretch case.

**Prerequisites**: 2.4.

---

### Story 2.6: Audit trail & attribution *(Must)*

**As an** operator,
**I want** every action bound to the owner and shown next to the real charge,
**So that** "who answers for what it does" is provable.

**Acceptance Criteria**:
1. Given any action (allow or deny), when it occurs, then a structured event records
   `owner(phone) → sandbox → credential ref → intent → outcome`.
2. Given the demo, when presented, then the streaming audit log and the Stripe test charge are shown
   side by side.
3. Given the credential field, when logged, then it is a reference/identifier, never the raw secret.

**Tasks**:
- [ ] Structured logger emitting the binding per event.
- [ ] Operator view (terminal stream) + Stripe dashboard layout for demo.

**Prerequisites**: 2.4 (and 2.5 for denial events).

---

## Sequencing & Integration

- **First 15 min (together):** Story 1.1 — lock the `ChannelAdapter` interface and `IntentManifest`
  schema. This is the integration seam.
- **Parallel:** Person A → 1.2–1.6 (identity/messaging). Person B → 2.1–2.4 (authority/action).
- **Smoke-test early (first 30 min):** 1Password SDK auth inside the Daytona sandbox (Story 2.2) — it
  is the highest-risk wiring; fall back to `op run` if it fights.
- **Last ~45 min:** integrate the seam (owner's texted task → manifest → sandbox → charge → reply),
  then 2.5–2.6.
- **Last ~15 min:** rehearse the demo thread inside the WhatsApp session window; ensure the mock-shim
  fallback also runs the full script.

## Traceability (FR → Story)

| FR | Story |
|----|-------|
| FR001–FR003 (channel) | 1.2 |
| FR004 (provision) | 1.3 |
| FR005 (round-trip verify) | 1.4 |
| FR006 (vault owner record) | 1.5 |
| FR007 (returning recognition) | 1.6 |
| FR008–FR009 (task → manifest) | 1.1 (schema), 2.4 |
| FR010 (sandbox) | 2.1 |
| FR011–FR012 (inline secret) | 2.2 |
| FR013, FR015 (gate, denials) | 2.3, 2.5 |
| FR014 (Stripe charge) | 2.4 |
| FR016–FR017 (audit) | 2.6 |
