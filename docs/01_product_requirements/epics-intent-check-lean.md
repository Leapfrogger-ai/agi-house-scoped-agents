# Epics & Stories — Intent Check (Lean)

*Tactical breakdown of `PRD-intent-check-lean.md`. Level 2 · 1 epic · 3 stories.*
*1.5-hr-window sizing: ~15–20 min each. Builds on existing Epic 2 (charge, gate, audit). Reuses
everything; adds one field, one loop, one grounding call.*

**Status:** Must = centerpiece demo blocker · Stretch = if time allows.

---

## Epic 3: Intent Check  *(centerpiece, lean)*

**Goal**: Run a short multi-item spending loop where each charge is checked against the declared goal,
halting on the first off-task charge — catching the in-policy-but-off-task case the gate can't see.
**Depends on**: Epic 2 (`charge`, `policy.evaluate`, audit). No forward dependencies.
**Delivers**: goal-grounded multi-item charging with the espresso-machine catch.

---

### Story 3.1: `goal` on the manifest + multi-item loop *(Must)*

**As a** verified owner,
**I want** the agent to handle a task with a few items toward a stated goal,
**So that** it can complete a small procurement, not just one charge.

**Acceptance Criteria**:
1. Given a task naming several items + a purpose, when parsed, then the manifest has `goal` (string)
   and an `items` list, plus the existing `budget`/`vendor_allowlist`.
2. Given the manifest, when run, then the agent loops over `items` (bounded by `max_items`), calling the
   existing `charge` once per item.
3. Given an Epic 2 single-charge task with no `goal`/`items`, when run, then it behaves exactly as before.

**Tasks**:
- [ ] Add optional `goal: str` and `items: list` (+ `max_items` default, e.g. 5) to `IntentManifest`.
- [ ] Parser fills `goal` + `items` for multi-item tasks; single-charge path untouched.
- [ ] Loop in the agent path: for each item → `charge` (reused).

**Prerequisites**: Epic 2 (manifest, parse, charge).

---

### Story 3.2: Grounding check + halt *(Must — the climax)*

**As a** system,
**I want** each item checked against the goal before it's charged, and the loop stopped on the first
off-task item,
**So that** an in-budget, on-allowlist, but off-task charge is contained.

**Acceptance Criteria**:
1. Given an item that passed the deterministic gate, when checked, then `grounding_check(goal, item)`
   returns `CONFORM` or `DEVIATE(intent-drift)` via one LLM call.
2. Given `CONFORM`, when returned, then the charge executes and a receipt is texted.
3. Given `DEVIATE` (or a gate failure), when returned, then the loop halts, no further items are
   charged, and the owner is texted the reason ("…isn't part of '{goal}'. Didn't charge it.").
4. Given any item, when processed, then the gate runs **before** the grounding check (cheap/deterministic
   first), and both run **before** the charge (fail-closed).

**Tasks**:
- [ ] `grounding_check(goal, item) -> (conform: bool, reason: str)` — one Nebius call, JSON out.
- [ ] Wire per item: `policy.evaluate` → `grounding_check` → `charge` | halt.
- [ ] Halt path + denial copy (per `conversation-design.md`).
- [ ] Audit each charge + the halt with `goal` + reason.

**Prerequisites**: 3.1, Epic 2 (`policy.evaluate`, audit).

---

### Story 3.3: Scripted + live deviation test *(Must: scripted; Stretch: live injection)*

**As a** team,
**I want** the off-task catch tested deterministically,
**So that** the centerpiece can't flake on stage.

**Acceptance Criteria**:
1. Given a fixed item list with a **stubbed** grounding result, when run, then a clean list charges all
   items and a list containing the espresso machine halts at it — asserted without a live LLM.
2. Given the deterministic gate, when an over-budget / off-allowlist item appears, then it halts with the
   right reason (regression: gate untouched).
3. *(Stretch)* Given a live run with the espresso machine injected into `items`, when processed, then the
   real grounding call halts it.

**Tasks**:
- [ ] Test driving fixed `items` + stubbed `grounding_check`; assert charged-vs-halted + reason.
- [ ] Reuse Epic 2 gate tests (no change expected).
- [ ] Mock catalog entry for the injected espresso machine (live demo).

**Prerequisites**: 3.2.

---

## Traceability (FR → Story)

| FR (from `PRD-intent-check-lean.md`) | Story |
|---|---|
| FR018 (`goal`), FR019 (loop) | 3.1 |
| FR020 (gate per item), FR021 (grounding), FR022 (halt), FR023 (audit) | 3.2 |
| FR024 (scripted test), FR025 (live injection) | 3.3 |

## Build Order (≈45 min)

1. **3.1** — field + loop (~15 min). Verify it charges multiple items end-to-end via the mock shim.
2. **3.2** — grounding + halt (~20 min). The espresso-machine catch works here.
3. **3.3** — scripted test (~10 min). Lock the demo so it can't flake.

## Demo Script (folds into the main thread)

```
→ "Set up the new hire's desk: keyboard, mouse, monitor from Acme, under $400."
← 💸 Bought keyboard $40 · mouse $25 · monitor $300 from *Acme*. ($365/$400)
   (injected) espresso machine $250
← 🛑 Skipped — an *espresso machine* isn't part of "desk setup". Didn't charge it.
```
The catch: espresso machine is **in budget and on-allowlist** — only the grounding check stops it.
