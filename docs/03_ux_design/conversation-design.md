# Conversation Design Spec — Claim-an-Agent-by-Text

*Adapted from the ux-design skill for a **chat-only product**. There is no GUI — the entire
user-facing surface is a WhatsApp thread (mock shim for dev/offline). Visual-design steps (color,
typography, components, responsive, WCAG layout) are intentionally omitted as N/A.*

*Source: `docs/01_product_requirements/PRD.md`, `docs/02_architecture/architecture.md`.*

## 1. Project Context

**Product**: An agent you claim and own entirely over text. The chat IS the product.
**Users**: A person with only a phone, no prior account. On stage: the judges, reading the thread.
**Core problem**: Make agent ownership + delegated spending legible and trustworthy in a medium
anyone already uses — text.
**Surface**: WhatsApp (Twilio Sandbox) + a terminal mock shim that runs the identical flow offline.

## 2. Core Experience

**Defining interaction**: Text a message → become a verified owner → delegate money → watch authority
get enforced, all in one thread.
**Desired feeling**: *"That was easy — and I trust it."* Effortless onboarding, visible guardrails.
**What must be effortless**: Going from first text to verified owner with zero instructions.
**Pattern type**: Novel (conversational ownership + delegated spending) — designed below.

## 3. Voice & Tone

**Voice**: Playful, short, trustworthy. A competent assistant with a wink — never chatty, never
jokey-at-the-expense-of-clarity.

**Rules**:
- **One idea per message.** Short lines. No paragraphs.
- **One emoji per message, as a status marker** — never decoration, never alone (always pair with
  words for accessibility). Status set: 👋 greet · ✅ success/ownership · 💸 charge · 🛑 denied ·
  🤔 didn't-understand.
- **Bold the entities** WhatsApp-style with `*asterisks*`: agent name, vendor, amounts.
- **Always name the guardrail on a denial** ("over your $50 budget", "not on your approved list") —
  the trust comes from showing the rule, not just refusing.
- **Reassure on refusal**: explicitly say no money moved ("Didn't charge a cent.").
- No internal jargon (no "manifest", "policy gate", "sandbox") in user-facing copy — that vocabulary
  is for the operator/audit view only.

## 4. Conversation Journeys (with copy)

State machine: `NEW → AWAITING_NAME → READY` (READY persists for returning owners).

### J1 — Claim → Verified Owner *(first text, one conversation)*
```
User → (any text, e.g. "CLAIM")
Bot  ← 👋 New agent incoming! You're claiming *Agent #A4*.
        Reply with a name to lock it in.            [state: AWAITING_NAME]
User → Budgetbot
Bot  ← ✅ Done — you own *Budgetbot*, and your number is the key 🔑
        Text me a task, like "buy 50 staples from Acme".   [state: READY, owner VERIFIED]
```
*The second inbound (the name) is the verification — proves live two-way control of the number.*

### J2 — Delegate a Task *(happy path, act immediately)*
```
User → buy office supplies, $30 from Acme
Bot  ← 💸 Paid *Acme* *$30.00*. $20 left on this task.
        Receipt #ch_3Nk... ✅
```

### J3 — Containment *(denials — the trust moment)*
```
User → buy $80 of supplies from Acme
Bot  ← 🛑 That's *$80* — over your *$50* budget. Didn't charge a cent.

User → pay EvilCorp $20            (stretch / prompt-injection case)
Bot  ← 🛑 *EvilCorp* isn't on your approved list, so I sat this one out.
```

### J4 — Returning Owner
```
User → hey
Bot  ← 👋 Welcome back — *Budgetbot* here. What's the task?
```

## 5. Error & Recovery States

| Situation | Bot reply |
|---|---|
| Task missing amount/vendor | 🤔 Didn't catch an amount + vendor. Try "buy *$30* from *Acme*". |
| Unknown number sends a "task" before claiming | 👋 You don't own an agent yet. Reply *CLAIM* to start. |
| Reply during `AWAITING_NAME` that isn't a name (e.g. emoji-only/blank) | 🙂 Just need a name for your agent — reply with one word. |
| Charge fails downstream (Stripe/sandbox error) | ⚠️ Something broke on my end — no charge went through. Try again in a sec. |
| Duplicate "CLAIM" from an already-verified owner | 👋 You already own *Budgetbot*. Just text me a task. |

**Recovery principle**: every error says (a) what's wrong, (b) that no money moved if relevant, and
(c) the exact next thing to type.

## 6. Message Formatting Conventions

- Money always `*$NN.NN*` (two decimals, bold).
- Names/vendors always bold.
- Receipts: short id, truncated (`#ch_3Nk...`).
- Keep each message under ~300 characters; split only if truly necessary (prefer fewer turns).
- Status emoji leads the line; never send an emoji-only message.

## 7. Demo Operator View (the "who answers" proof)

**Three-up on the projector:**

```
┌─────────────────┬──────────────────────┬──────────────────────────────┐
│  PHONE (thread) │  STRIPE (test dash)  │  AUDIT LOG (Railway/JSONL)   │
│  the WhatsApp    │  the real $30 charge │  owner→sandbox→cred→intent→  │
│  conversation    │  appearing live      │  outcome, incl. 🛑 denials   │
└─────────────────┴──────────────────────┴──────────────────────────────┘
```

- **Phone**: the human story (claim → own → spend → denied).
- **Stripe test dashboard**: proof the allowed charge is *real*.
- **Audit log**: proof every action — allowed and denied — binds back to the phone owner, with
  `credential_ref` shown as a reference (`op://...`), never a raw secret.

The narration ties them: *"She owns it (phone) → it really spent (Stripe) → and every move answers to
her (log)."*

## 8. Constraints (the chat-medium "accessibility")

- Plain text + emoji only — no buttons, cards, or rich UI (WhatsApp Sandbox limitation).
- Emoji never carry meaning alone (always paired with words) — readable if emoji don't render.
- WhatsApp Sandbox requires a one-time `join <phrase>`; pre-join the demo phone (see architecture).
- 24-hr messaging-session window — rehearse and demo within it.
- Self-explanatory: no message ever assumes the user read instructions elsewhere; the reply always
  contains the next step.

## Appendix

- Related: PRD §User Journey, architecture §Novel Pattern, brief §Demo Script.
- Next: wire these exact strings into `conversation.py`; keep a `copy.py` constants module so both
  devs use identical wording.
