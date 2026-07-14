# ADR 0001 — The term loop stays in the generator

**Date:** 2026-07-13
**Status:** Accepted

## Context

An architecture review proposed lifting a **Term** module out of `generate()`'s
term loop: `serve(career, state, rolls, rules) -> TermResult`, with the loop
becoming a fold. The rationale was that one term of service is a real domain
concept with no module of its own, that the loop mutated `characteristics` and
`skills` in place, and that a term could not be tested on its own.

The review deliberately parked it behind two other changes and said to reassess
afterwards. Those changes landed:

- The **Rolls** seam (`engine/rolls.py`) — tests script rolls by name, so any
  scenario a term can be in is expressible from outside.
- The named steps (`background`, `training`, `aging`, `benefits`, `ranks`) — each
  returns what changed rather than mutating.

## Decision

**Do not extract a Term module.** The term loop stays in `generate()`.

## Rationale

- **The testability argument is spent.** `tests/test_generator.py` has 77 tests,
  all through `generate()`, none reaching past its interface. `ScriptedRolls`
  expresses survival failing in a chosen term, a natural 12 at the cap, and every
  rung of the ageing ladder. There is nothing a Term module would make testable
  that is not already tested.
- **It would have exactly one caller.** Depth is leverage per unit of interface;
  one call site is no leverage. Apply the deletion test to the proposed module:
  deleting it would push the loop straight back into `generate()`. Complexity
  would *move*, not *concentrate* — which is the signal not to build it.
- **Sequencing the steps and deciding when to stop is the coordinator's job.**
  `generate()` reads as assign → qualify → background → terms → muster out. A
  Term module would still have to hand the loop back its exits (survived? another
  term?), so `generate()` would keep the control flow anyway.

## What was done instead

The reassessment surfaced two real problems, and those were fixed:

1. **The advancement rule was written twice** — once on the post-commission path
   and once for a standing rank. Extracted to `engine/ranks.py` (`progress`), so
   the rule exists once. Two call sites became one, which is leverage a Term
   module would not have provided.
2. **`resolve_survival_mishap` still mutated `characteristics` in place**, and the
   rank-bonus grant mutated `skills`. Both now return what changed, so every step
   in the engine is consistent.

## Consequences

- `generate()` remains the one place that knows the order of a career.
- A future review that proposes a Term module should read this first. Reopen it
  only if a **second caller** appears — a term simulator, a "what if" tool, an
  incremental character builder. That would give the interface leverage it does
  not have today.
