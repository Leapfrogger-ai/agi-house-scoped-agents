# PRD — Intent Check (Feature, Lean)

*Feature-scoped PRD. Covers **only** the lean intent check and the changes it implies. Does **not**
rewrite the master `PRD.md`. Scoped for a ~45-min build inside a 1.5-hr window.*

*Scale: **Level 2** feature addition (~3 stories). FR numbering continues from `PRD.md` (ends FR017);
NFRs from NFR005. Inspired by one insight from TELBENCH/DRIFT (arXiv:2606.02060): an action can pass
every rule yet be off-task. We take only that idea and deliberately leave the rest (see Out of Scope).*

*Lean alternative to the fuller `PRD-intent-conformance.md`. Pick one to build; this is the 1.5-hr cut.*

---

## Overview

Extend the agent from a single charge to a **short multi-item workflow** with a one-call **intent
check**: before each charge, after the existing budget/allowlist gate passes, ask whether the item is
part of the owner's declared **goal**. Halt on the first off-task charge. This catches the case rules
can't — in-budget, on-allowlist, but off-task — and is the demo centerpiece. Everything from the
single-charge flow is reused.

## Goals

- Let a verified owner delegate a task with a few items, executed as a short loop toward a declared goal.
- **Catch and halt the first off-task charge** with a plain-language reason — the in-policy-but-off-task
  case the deterministic gate can't see.
- Show that intent-conformance becomes tractable once intent is **declared** (the manifest `goal`) —
  the intent-based-access thesis, live.

## Background Context

The single-charge demo can't show intent drift — one charge has no room to wander. TELBENCH/DRIFT shows
that, for agents with *implicit* goals, detecting off-task commitments is hard. Our version is the easy
cousin: the goal is declared, so a single LLM grounding check per charge suffices — no trajectory model,
ledger, or multi-role auditor. That contrast is the on-stage point.

## Functional Requirements

- FR018: The intent manifest shall gain an optional `goal` (declared purpose). Single-charge tasks work
  unchanged when it is absent.
- FR019: The agent shall execute a task of a few items as a short loop, bounded by a small `max_items`.
- FR020: Before each charge, the existing deterministic gate (budget + vendor allowlist) shall run
  (reused unchanged).
- FR021: After the gate passes, a single **grounding check** (one LLM call) shall decide whether the
  item is part of `goal` → `CONFORM` | `DEVIATE(intent-drift)`.
- FR022: On any `DEVIATE` (gate or grounding), the system shall **halt** the loop, make no further
  charges, and text the owner the reason.
- FR023: Each charge and the halting denial shall be written to the existing audit trail, including
  `goal` and the reason.
- FR024: A scripted test shall assert the grounding verdict for a fixed item list (grounding stubbable,
  no live LLM required).
- FR025: The system shall support injecting an off-task item to demonstrate intent-drift live.

## Non-Functional Requirements

- NFR006: **[Containment]** The deterministic gate verdicts are reproducible and independent of model
  output.
- NFR007: **[Reliability]** Checks run **before** each charge (fail-closed); nothing charges until it
  passes both gate and grounding.
- NFR008: **[Testability]** The grounding step is stubbable so deviation behavior is testable without a
  live LLM.
- NFR009: **[Performance]** ≤ one grounding call per item; the loop is bounded by `max_items`.

## User Journey: Short Task with an Intent Check

**Persona**: A verified owner. **Goal**: equip a new hire's desk within budget.

### Steps (clean path)
1. Owner texts: *"Set up the new hire's desk: keyboard, mouse, monitor — from Acme, under $400."*
2. Agent builds the manifest with `goal = "new-hire desk setup"` and the item list.
3. For each item: gate passes → grounding check returns `CONFORM` → charge (Stripe test) → receipt.
4. Agent reports completion.

### Alternative Path (deviation — the climax)
- An injected item *"espresso machine, $250 from Acme"* enters the list. Gate passes (Acme allowed, in
  budget). The grounding check returns `DEVIATE(intent-drift)` — not part of "desk setup".
- The loop **halts**; the owner is texted: *"🛑 Skipped — an espresso machine isn't part of 'desk
  setup'. Didn't charge it."*

### Error States
- Over-budget / off-allowlist item → deterministic `DEVIATE`, halt with the reason.
- `max_items` reached → stop and report what was bought.

## UX/UI Vision

- **Chat thread** — the agent narrates each buy and the halt reason in the established voice.
- **Operator view** — reuses the three-up demo; the audit pane shows each charge plus the off-task halt
  line. No new view.
- **Constraint** — chat-only; the denial reason must be legible ("not part of the task").

## Epic List

### Epic 3: Intent Check  *(new — centerpiece, lean)*
**Goal**: Run a short multi-item spending loop where each charge is checked against the declared goal,
halting on the first off-task charge.
**Estimated Stories**: ~3 (manifest `goal` + loop; grounding check + halt; scripted/live deviation test).
**Depends on**: existing Epic 2 (charge, gate, audit — reused). No forward dependencies.
**Delivers**: goal-grounded multi-item charging with the in-policy-but-off-task catch.

*(Detailed stories can go in a companion `epics.md`, generated separately.)*

## Changes to Existing Requirements

*Extensions only — nothing rewritten.*

| Existing item | Change implied |
|---|---|
| **FR009** (task → manifest) | Manifest gains optional `goal` (FR018). Single-charge unaffected. |
| **FR014** (Stripe test charge) | Charge becomes the loop body (FR019), called once per item. Behavior unchanged. |
| **FR016–FR017** (audit) | Audit entries add `goal` + denial `reason` (FR023). Existing fields kept. |
| **Policy gate** (`policy.py`) | Reused unchanged; now called once per item instead of once. |
| **Architecture** | One small addition: a `grounding_check()` (one Nebius call) + a short loop in the agent path. No new modules required. |
| **Conversation design** | Add per-item buy narration + the off-task halt line. |

## Out of Scope (deferred — cut for time)

- Span trajectory model, stage tags, commitment ledger.
- Exploration-vs-commitment distinction and first-deviation localization / propagation.
- Audit-mode post-hoc localization; the `price_lookup` tool; cumulative-vs-per-charge budgets.
- Auto-remediation / replanning after a deviation — the loop simply halts.

*All of the above are the richer TELBENCH/DRIFT-inspired design; revisit only if the lean version lands
with time to spare.*
