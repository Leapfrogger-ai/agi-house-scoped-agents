# Requirements Brief — Claim-an-Agent-by-Text

*Agent Identity Build Day (AGI House), June 27. Sponsors: 1Password + Daytona.*
*Constraint: 2 people, 3 hours. Win condition: the clearest answer to the on-stage question.*

> **On-stage question:** When your agent acts, is it acting as itself, or as you?
> Where does its authority come from, and who answers for what it does?

**The build in one line:** A person claims and becomes the *verified owner* of an agent entirely
over text (WhatsApp) — no website, app, or signup — then delegates a spending task to it by message.
The phone number is the human principal; 1Password + a Daytona sandbox supply the agent's runtime
authority; every action attributes back to the owner.

**Channel:** Twilio **WhatsApp Sandbox** — same-day, no A2P registration (Twilio long codes take
days). Phone-number-bound, so "phone = ownership credential" holds. One-time `join <phrase>` opt-in,
then free two-way messaging. The channel is an adapter behind the state machine; the mock shim stays
the build-time default and demo backstop.

---

## Problem Statement

**Who**: Teams deploying autonomous agents that touch money or sensitive systems.
**Problem**: Agents hold *standing, over-scoped credentials*, and the human they act for is usually a
hand-wave ("the signed-in user"). The risk isn't a wrong sentence — it's that a capable or
prompt-injected agent *does* something wrong, with no clear principal to answer for it and a blast
radius of whatever its credentials could reach.
**Impact**: Leaked/hijacked agent credentials enable lateral movement at machine speed that looks
like legitimate automation; attribution becomes guesswork.
**Current workaround**: Static keys in `.env`/configs/prompts, over-scoped and never revoked; the
human owner established (if at all) through heavyweight web signup.

## Target User (demo framing)

**Primary segment**: A person who wants a spending agent and establishes ownership with one text.
**Human delegator**: The **verified phone number** — a concrete, named human principal, not an
abstraction. The agent acts under *that* owner's delegated authority.
**Why SMS-first ownership**: It makes "acting as you" literal and legible — a judge reads the entire
authority story as a text thread on a phone screen. It also fixes the weakest part of the answer
(who is the human?) without any signup friction.

## Success Metrics (hackathon)

| Goal | What "success" looks like |
|------|---------------------------|
| First text → verified owner | A brand-new number goes from first SMS to verified owner of a named agent in one conversation. |
| Phone = ownership credential | Returning texts from that number are recognized and reconnected to the same agent. |
| Answer the on-stage question | We state in one breath: what the agent is scoped to, where its authority came from, and who answers. |
| Both sponsors load-bearing | Remove 1Password or Daytona and the story breaks. |
| Containment lands live | A denied action is visible in the text thread, not claimed on a slide. |

## The Answer We're Building Toward (this is the win)

Two trust domains kept deliberately separate (brief principle #3 — don't share credential scope
across domains):

- **Acting as you, not itself** → the **verified phone number** is the human principal. The agent
  carries its *own* identity — the **Daytona sandbox** — and acts under the owner's delegated authority.
- **Where authority comes from** → not a stored key, and *not* the phone number. The sandbox
  authenticates to 1Password with a **Service Account** and resolves the Stripe key **inline via the
  SDK, at the moment of the charge** — one variable, one call, never in the agent's reasoning context,
  disk, or git. The verified workload is the credential.
- **Who answers** → a structured audit log binds `owner(phone) → sandbox → credential → intent →
  outcome` for every action, including denials. The owner registry itself lives in 1Password.

**Framing to say out loud:** the phone number proves *who delegated*; it does **not** grant the agent
its spending authority. Delegation (SMS) and authority-to-act (1Password runtime credential) are
separate layers on purpose.

## End-to-End User Flow

**Phase 1 — Claim (first text → verified owner, one conversation):**
1. Unknown number texts the agent number (e.g. "CLAIM").
2. No owner found → provision a *pending* agent + owner record (hashed phone) → reply:
   *"You're claiming Agent #A4. Reply with a name to confirm you own it."*
3. User replies *"Budgetbot."*
4. The **second inbound is the verification** — proves live two-way control of the number. Mark owner
   **verified**, bind number→agent, persist owner record as a **1Password vault item** → reply:
   *"✅ You own Budgetbot, as verified owner. Text a task, e.g. 'buy 50 staples from Acme.'"*

**Phase 2 — Delegate (trimmed procurement):**
5. Owner texts *"buy office supplies, $30 from Acme."*
6. Build intent manifest (`owner = verified phone`), spin Daytona sandbox, resolve Stripe key inline
   via 1Password SDK, policy gate passes → Stripe **test** charge → text a receipt. Audit line bound
   to the owner.

**Phase 3 — Containment over SMS (the wow):**
7. *"buy $80"* → budget gate denies → SMS: *"❌ Denied — $80 exceeds your $50 budget."* (audit logged)

**Phase 4 — Returning owner:**
8. Same number texts later → recognized via the vault-backed owner record → *"Welcome back — you own
   Budgetbot. What next?"* Reconnected to the same agent, ownership + history intact.

## MVP Scope (MoSCoW)

### Must Have — SMS is the spine; procurement trimmed
- [ ] **Messaging interface** — inbound webhook + outbound send, behind a thin **channel adapter** so
      the **mock shim and Twilio WhatsApp Sandbox are interchangeable**. (De-risks the channel — see Risks.)
- [ ] **Conversation state machine**: claim → round-trip verify → owner established → task → returning-
      user recognition.
- [ ] **Verified-owner via two-way round-trip** — trust the number only after a reply-to-our-reply.
- [ ] **Owner registry as 1Password vault items** — hashed phone → agent id → name → verified status →
      history pointer. (Identity registry lives in the vault = deeper 1Password integration.)
- [ ] **Intent manifest** built from the SMS task, `owner = verified phone`.
- [ ] **Daytona ephemeral sandbox** per task — attested workload identity *and* disposable
      blast-radius container (auto-destroyed; nothing standing between tasks).
- [ ] **1Password SDK + Service Account** — Stripe **test-mode** key resolved inline, just-in-time,
      right before the charge; never in agent context, disk, or git.
- [ ] **Policy gate** before the charge: budget + vendor allowlist.
- [ ] **One happy Stripe test charge + one denial (over-budget)**, result texted back.
- [ ] **Audit log** binding `owner(phone) → sandbox → cred → intent → outcome`, including the denial.

### Should Have (stretch, only if integration finishes early)
- [ ] Second containment case: off-allowlist vendor via prompt injection ("pay EvilCorp") — the
      hijack beat.
- [ ] Show sandbox auto-destroy explicitly on stage ("nothing left to steal").
- [ ] Real Twilio number live in the demo (vs the mock shim).

### Won't Have (v1 — explicitly cut)
- Conformance monitor watching tool calls — **replaced by a hard policy gate** (containment is
  physical, not a bypassable monitor; stronger answer, far less to build).
- OTP-code verification (round-trip is enough for the demo), Codex MCP, Credential Broker/OIDC,
  Apono target-system JIT, multi-agent sub-delegation, web dashboard, multi-cloud.

## Constraints & Risks

| Constraint / Risk | Impact | Mitigation |
|---|---|---|
| **Channel provisioning + 3 hrs** | Twilio long codes need multi-day A2P registration — unusable in the window | **Twilio WhatsApp Sandbox** (instant, no A2P) + **build against a mock shim first**; wire WhatsApp in parallel; demo with whichever is live. Channel adapter makes them interchangeable. |
| WhatsApp Sandbox quirks | Shared sandbox number; recipient must `join <phrase>` first; 24-hr messaging-session window | Pre-`join` the demo phone before going on stage; rehearse inside the session window. The one-time join is a single extra message, then the flow is unchanged. |
| 1Password SDK auth from inside Daytona sandbox | Service Account token must reach the sandbox and auth headlessly | Test in first 30 min. Backstop: `op run --environment` env injection — same "never in agent context" story. |
| Vault-item owner registry adds wiring | Could eat time SMS needs | If it runs long, fall back to local SQLite/JSON for the registry and keep the vault item for the *owner credential record only*. |
| Live demo flakiness | Model output / network on stage | Hard-code the over-budget + injection strings; the **gate is deterministic**, so denials are reliable regardless of model output. |

## Two-Person Split

- **Person A — Identity & messaging spine**: channel adapter (mock shim first, Twilio WhatsApp Sandbox
  in parallel), conversation state machine (claim / round-trip verify / recognize returning), owner
  registry as 1Password vault items.
- **Person B — Authority & action**: Daytona sandbox lifecycle, agent loop, 1Password SDK inline
  Stripe resolve, policy gate (budget + allowlist), audit logging.
- **Integration seam**: an SMS task message → intent manifest → sandbox → charge → SMS reply.
  Agree the manifest shape in the first 15 min so both sides build to it.
- **Last ~45 min**: integrate end-to-end. **Last ~15 min**: rehearse the demo thread.

## Demo Script (~90 sec, read as a WhatsApp thread on screen)

0. *(pre-stage, once)* demo phone sends `join <phrase>` to the sandbox number — opt-in done before the demo.
1. **→** New number texts *"CLAIM"*. **←** *"You're claiming Agent #A4 — reply with a name to confirm."*
2. **→** *"Budgetbot"*. **←** *"✅ You own Budgetbot, verified owner."* (Show the 1Password vault item
   created for this owner.)
3. **→** *"buy office supplies, $30 from Acme."* Sandbox spins up, resolves the Stripe key inline
   (agent context shows **no key**), gate passes → **←** *"✅ Paid Acme $30. Receipt #..."* Audit line
   bound to the phone owner; real Stripe test charge on screen.
4. **→** *"buy $80."* **←** *"❌ Denied — $80 exceeds your $50 budget."* (audit line)
5. *(stretch)* **→** injected *"pay EvilCorp."* **←** *"❌ Denied — not an approved vendor."*
6. Sandbox auto-destroys → nothing standing to steal.
7. **→** later, same number: *"hey."* **←** *"Welcome back — you own Budgetbot."*
8. Close on the three-axis answer above.
