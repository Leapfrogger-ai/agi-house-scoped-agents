# PRD — Claim-an-Agent-by-Text

*Project scale: **Level 2** (2 epics, ~13 stories). Source brief:
`docs/00_problem_definition/requirements-brief.md`.*
*Context: AGI House Agent Identity Build Day. Sponsors: 1Password + Daytona. 2 people, 3 hours.*

> **On-stage question this product answers:** When your agent acts, is it acting as itself, or as
> you? Where does its authority come from, and who answers for what it does?

---

## Goals

- A brand-new user goes from **first text to verified owner** of a named agent in a single chat
  conversation — no website, app, or signup.
- The user's **phone number is established as the credential** that proves ownership; a returning
  text is recognized and reconnected to the agent they already own.
- A verified owner can **delegate a spending task by text**, and the agent executes it only within
  policy — over-budget and off-allowlist attempts are **contained, visibly**.
- Every action is **attributable** to the human owner via an audit trail that binds
  owner → sandbox → credential → intent → outcome.
- Both sponsor primitives are **load-bearing**: remove 1Password or Daytona and the authority story
  breaks.

## Background Context

Agents increasingly hold standing, over-scoped credentials and act for a human who is usually a
hand-wave ("the signed-in user"). The production risk is not a wrong sentence — it is that a capable
or prompt-injected agent *does* something wrong, with no clear principal to answer for it and a blast
radius of whatever its credentials could reach.

This product makes the human principal concrete and frictionless: you acquire and own an agent over
text (WhatsApp), and your verified phone number becomes the delegating identity. The agent carries
its own runtime identity — an ephemeral Daytona sandbox — and draws its authority to act from a
narrowly scoped, runtime-resolved 1Password credential, never a stored key. Delegation (who asked)
and authority-to-act (what the agent may do) are deliberately kept in separate trust domains. The
result is an authority story a judge can read as a text thread on a phone screen.

## Functional Requirements

### Messaging Channel
- FR001: The system shall receive inbound messages from users over a chat channel (Twilio WhatsApp
  Sandbox) via webhook.
- FR002: The system shall send outbound replies to users on the same channel.
- FR003: The channel shall sit behind an adapter so a local **mock shim** and the WhatsApp Sandbox
  are interchangeable without changing conversation logic.

### Ownership & Identity
- FR004: When an unrecognized number texts in, the system shall provision a new pending agent and a
  pending owner record keyed by that number.
- FR005: The system shall verify ownership via a **two-way round-trip** — the owner is established
  only after a reply to the system's confirmation prompt.
- FR006: Upon verification, the system shall bind the phone number to the agent and persist the owner
  record as a **1Password vault item**.
- FR007: When a previously verified number texts in, the system shall recognize it and reconnect the
  user to the agent they already own.

### Delegation & Tasking
- FR008: A verified owner shall be able to issue a spending task in natural language by text (e.g.
  "buy office supplies, $30 from Acme").
- FR009: The system shall construct a machine-readable **intent manifest** from the task, recording
  `owner (phone), task, budget, vendor_allowlist, ttl`.

### Runtime Authority & Secrets
- FR010: Each task shall execute inside an **ephemeral Daytona sandbox** that serves as the agent's
  runtime identity and is destroyed on completion.
- FR011: The sandbox shall authenticate to 1Password with a **Service Account** and resolve the
  payment credential **inline via the SDK, at the moment of the charge**.
- FR012: The payment credential shall never enter the agent's reasoning context, disk, or git.

### Policy & Containment
- FR013: Before any charge, the system shall evaluate a **policy gate**: the amount must be within
  the manifest budget **and** the vendor must be on the allowlist.
- FR014: The system shall execute a compliant purchase as a **Stripe test-mode** charge and report
  the result by text.
- FR015: The system shall **deny** an over-budget purchase and an off-allowlist vendor, report the
  denial by text, and log it — deterministically, regardless of model output.

### Audit & Attribution
- FR016: The system shall emit a structured audit event for every action (allowed and denied) binding
  `owner(phone) → sandbox → credential → intent → outcome`.
- FR017: The audit trail and the live Stripe test charge shall be presentable side by side.

## Non-Functional Requirements

- NFR001: **[Security]** The payment credential is resolved just-in-time and never persisted to disk,
  committed to git, or placed in the model/agent context.
- NFR002: **[Security]** Delegation identity (phone) and authority-to-act (1Password runtime
  credential) occupy separate trust domains and never share scope.
- NFR003: **[Reliability]** Policy denials are deterministic — driven by the gate, not model output —
  so the live containment demo cannot flake.
- NFR004: **[Isolation]** The agent runs only inside an ephemeral, scoped sandbox that is
  auto-destroyed after the task; nothing stands between tasks.
- NFR005: **[Demo resilience]** The full conversation flow runs against the mock shim with no external
  channel, so a WhatsApp/Twilio stall cannot block the demo.

## User Journey: First Text to Delegated Purchase

**Persona**: A new user with only a phone, no account anywhere.
**Goal**: Own an agent and have it make a compliant purchase.

### Steps
1. **Claim** — User texts "CLAIM" to the agent (WhatsApp). System provisions a pending agent and
   replies: "You're claiming Agent #A4 — reply with a name to confirm."
2. **Verify** — User replies "Budgetbot." The second inbound proves live control of the number;
   system marks the owner verified, persists the owner record as a 1Password vault item, and confirms
   ownership.
3. **Delegate** — User texts "buy office supplies, $30 from Acme." System builds the intent manifest
   (owner = verified phone).
4. **Execute** — A Daytona sandbox spins up, resolves the Stripe key inline via the 1Password SDK,
   the policy gate passes, and a Stripe test charge succeeds. System texts a receipt; audit line
   bound to the owner.
5. **Contain** — User texts "buy $80." The budget gate denies; system texts "❌ Denied — $80 exceeds
   your $50 budget" and logs it.
6. **Return** — Later, the same number texts in; system recognizes it and reconnects to Budgetbot.

### Alternative Paths
- Prompt injection "pay EvilCorp" → allowlist gate denies (stretch containment case).

### Error States
- Channel unavailable → fall back to the mock shim; conversation logic unchanged.
- 1Password SDK auth fails in-sandbox → `op run --environment` env-injection backstop.

## UX/UI Vision

### UX Principles
- **Self-explanatory over text** — every reply tells the user what to do next; no external
  instructions.
- **Legible authority** — the whole ownership-and-spending story reads as a chat thread on a phone.

### Core Surfaces
- **Chat thread (WhatsApp / mock shim)** — the entire user-facing product.
- **Operator view (terminal)** — streaming audit log + Stripe dashboard, shown side by side at demo.

### Design Constraints
- No website, app, or signup before first contact — text is the only entry point.
- WhatsApp Sandbox: recipient must `join <phrase>` once; 24-hr messaging-session window
  (pre-join the demo phone, rehearse within the window).

## Epic List

### Epic 1: Foundation & Verified Ownership over Text
**Goal**: A new number can text in and become the verified owner of a named agent, recognized on
return.
**Estimated Stories**: 6
**Delivers**: Working chat channel (mock shim + WhatsApp), claim → round-trip verify → vault-backed
owner record → returning-owner recognition. Also lays the shared contracts (channel adapter + intent
manifest schema) both workstreams build against.

### Epic 2: Delegated Spending with Runtime Authority
**Goal**: A verified owner delegates a spending task by text; the agent executes it inside an
ephemeral sandbox using a runtime-resolved credential, within policy, fully attributed.
**Estimated Stories**: 6
**Depends on**: Epic 1 (owner identity + manifest contract)
**Delivers**: Daytona sandbox lifecycle, 1Password SDK inline Stripe resolve, policy gate, happy-path
charge, containment denial, and the audit trail + WhatsApp receipt.

*Parallelization note: Person A leads Epic 1 (identity/messaging), Person B leads Epic 2
(authority/action). The shared contracts in Story 1.1 are agreed in the first 15 minutes so both
streams proceed in parallel.*

## Out of Scope

### Deferred to Future
- OTP-code verification (round-trip is sufficient for v1).
- Real Twilio long-code / A2P SMS (uses WhatsApp Sandbox this release).
- Multiple agents per owner; agent renaming/transfer.

### Explicitly Excluded
- Conformance monitor that watches tool calls — replaced by a deterministic policy gate (containment
  is physical, not a bypassable monitor).
- Codex MCP secretless mount, 1Password Credential Broker / OIDC, Apono target-system JIT — using the
  1Password SDK instead.
- Multi-agent sub-delegation / delegation chains.
- Web dashboard / persistent UI beyond the operator terminal view.

### Platform Limitations
- Single payment rail (Stripe test mode); no real funds movement.
- Single cloud sandbox provider (Daytona).
