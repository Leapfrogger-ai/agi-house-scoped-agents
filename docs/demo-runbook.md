# Demo Runbook — Claim-an-Agent-by-Text

*The single doc to drive the live demo. Consolidates the SMS onboarding flow
(`03_ux_design/conversation-design.md`), the budget/allowlist commands
(`02_architecture/budget-allowlist-commands.md`), and the lean intent check
(`01_product_requirements/PRD-intent-check-lean.md`). Read top-to-bottom while presenting.*

**Target length on stage: ~2 minutes.** The whole authority story should read as one WhatsApp thread.

---

## The story in one breath (open + close with this)

> *She owns it (her phone) → it really spent her money (Stripe) → it stayed on the task she set
> (intent check) → and every move answers to her (audit). The agent acts **as her**, with authority
> **proven at runtime**, and **she answers** for what it does.*

---

## Pre-demo checklist (do BEFORE going on stage)

- [ ] **WhatsApp**: demo phone has sent `join <phrase>` to the Twilio Sandbox number (session is live;
      24-hr window — re-join if stale).
- [ ] **Railway**: orchestrator deployed, webhook URL set in Twilio, logs view open.
- [ ] **Three-up screen** arranged: **(1)** phone mirror / WhatsApp · **(2)** Stripe **test** dashboard
      · **(3)** audit log (Railway logs or `tail -f`).
- [ ] **1Password**: `ClaimByText` vault open to show the owner item being created + the separate
      `Stripe` item (the secret the agent never sees).
- [ ] **Stripe** in **test mode** confirmed (no real charges).
- [ ] **Fallback ready**: `python run_mock.py` runs the identical script offline if WhatsApp/Railway
      stalls (see bottom).
- [ ] **Off-task injection** staged: the `espresso machine` item in the mock catalog / injection payload.
- [ ] Owner number is **unclaimed** (delete the test owner item so the claim flow runs fresh).

---

## Beat-by-beat

| # | You send (WhatsApp) | Bot replies | On screen | Say |
|---|---|---|---|---|
| 1 | `CLAIM` | 👋 You're claiming *Agent #A4* — reply with a name to confirm. | phone | "No app, no signup — she just texts in." |
| 2 | `Budgetbot` | ✅ You own *Budgetbot* 🔑 Starting limits: budget *$50*, vendors *Acme*. Change with "budget 400" or "allow Acme, Staples". | **1Password vault** — owner item appears | "The second text proves she controls the number. Her identity now lives in 1Password — the phone **is** the credential." |
| 3 | `budget 400` | 💰 Budget set to *$400*. | phone | "She sets the scope herself." |
| 4 | `allow Acme, Staples` | 🔒 Approved vendors: *Acme*, *Staples*. | phone | — |
| 5 | `Set up the new hire's desk: keyboard, mouse, monitor from Acme and Staples — it's for the desk setup.` | 💸 Bought *keyboard* $40 · *mouse* $25 from *Acme*. 💸 Bought *monitor* $300 from *Staples*. ($365/$400) | **Stripe** — 3 real test charges appear; **audit** — lines stream | "Each charge runs in a fresh Daytona sandbox; the Stripe key is pulled from 1Password **inside** the sandbox at charge time — never in the model's context." |
| 6 | *(injected)* `espresso machine $250 from Acme` | 🛑 Skipped — an *espresso machine* isn't part of "desk setup". Didn't charge it. | **audit** — DENY intent-drift; Stripe shows **no** new charge | **The climax:** "In budget. Approved vendor. Allowed action. **Every rule passes** — only checking it against her stated intent stops it. That's the unsolved part, and it works because intent is *declared*." |
| 7 | `hey` *(later, same number)* | 👋 Welcome back — you own *Budgetbot*. What's the task? | phone | "Same number, reconnected — ownership persists." |

*(Optional rule-based beat, only if time: send `buy a $500 chair from Acme` → 🛑 over your $400 budget.
Shows the deterministic gate vs. the intent check are different layers.)*

---

## What each screen proves (map to the on-stage question)

- **Phone (WhatsApp)** → *acting as you*: a real human principal (the verified number) delegating.
- **1Password vault** → *where authority comes from*: identity in the vault; the Stripe secret resolved
  at runtime in the sandbox, never stored in the agent.
- **Stripe test dashboard** → the agent *really* acted (within scope).
- **Audit log** → *who answers*: every action binds `owner(phone) → sandbox → credential → intent →
  outcome`, including the denied espresso machine.

---

## If something breaks (fallback)

- **WhatsApp / Railway down** → run `python run_mock.py` and type the **same** messages (col. 2). The
  conversation logic is identical; only the channel differs. Narrate from the same beats.
- **Live grounding call flakes** → the off-task catch is also covered by the scripted test
  (`epics-intent-check-lean.md` Story 3.3); show the passing test as proof the behavior is
  deterministic, then continue.
- **A Stripe charge errors** → it's test mode; re-send the task; the gate/intent logic is unaffected.

---

## Timing

| Segment | Beats | ~Time |
|---|---|---|
| Claim → verified owner | 1–2 | 25s |
| Set scope | 3–4 | 15s |
| Multi-item buy | 5 | 35s |
| **Intent-drift catch** | 6 | 30s |
| Returning owner + close | 7 | 15s |

Keep beat 6 unrushed — it's the whole point.
