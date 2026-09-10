---
title: Put the walk's seam where the tests cross it
strength: Worth exploring
status: open
files: [src/cetools/generator.py, tests/unit/test_generator.py, tests/integration/test_traversal.py, tests/integration/test_npc_sample.py, tests/integration/test_data_driven.py]
---

## Problem

`_Walk`'s docstring says "Not part of the public surface; `generate_character`
is the seam", but four test modules import it fifty-nine times and drive its
methods directly.

## Solution

Decide where the seam actually belongs — either make the walk's per-career
step a named interface tests may cross, or give `generate_character` enough
inspectable output that they need not.

## Wins

- Interface and test surface stop disagreeing
- Roller substitution gets a declared shape
- `_FixedRoller` stops being written three times
- Fixture prologue stops being retyped twenty times

## Diagram

Hand-built boxes-and-arrows. Before: a box labelled `generate_character`
marked "the seam", with a dashed boundary around `_Walk` behind it — and four
test-module boxes whose arrows all pierce the dashed boundary, bypassing the
seam entirely; one arrow (`test_traversal.py`) loops back on itself to show
`run` being re-implemented rather than called. After: the boundary redrawn
around what tests actually need to reach, with arrows landing on it instead
of through it.

## Detail

`_Walk`'s claim is at `generator.py:284-286`. The counts against it:

| File | `_Walk` mentions |
|---|---|
| `tests/unit/test_generator.py` | 56, via 24 separate function-local imports |
| `tests/integration/test_npc_sample.py` | 3 |
| `tests/integration/test_traversal.py` | 2 |
| `tests/integration/test_data_driven.py` | 2 |

Other privates imported by tests: `_eligible_tables`, `_resolve_specialty`
(six times), `_apply_characteristic_delta`, `_Debt`, and
`_Walk._highest_matching_rank_row` as a static helper.

The setup no caller would write appears about twenty times verbatim:

```python
walk = _Walk(Roller(20), RULES)
walk.characteristics = {code: 7 for code in RULES.characteristics.names}
```

followed, where a branch demands it, by direct field writes —
`walk.funds = 100_000`, `walk.debt = …; walk.debts = [debt]`,
`walk.pension_qualified = True`, `walk.total_terms_served = 100`, and at
`tests/unit/test_generator.py:1138` and `:1166`, swapping
`walk.roller` for a `_FixedRoller` mid-object.

The roller seam is real but undeclared. `Roller`
(`src/cetools/dice.py:14`) is a concrete class with no `Protocol`; the test
adapter `_FixedRoller` is defined three separate times inside method bodies
(`test_generator.py:176-183`, `:1114-1122`, `:1148-1156`), identical each
time, never extracted. Because the seam is untyped, `_FixedRoller` implements
only `die` and `dice` and would break on any path reading `roller.seed` —
which `generate_character:1621` does, to derive the name stream. That is two
adapters at one seam, so the seam is real; it simply has no interface.

The precondition it hides is worth naming here too: `generate_character`
requires a *fresh* `Roller`, enforced nowhere in code. A half-consumed roller
still reports its original seed, so its derived name stream no longer
corresponds to its walk. The rule exists only in
`specs/003-npc-generator/contracts/library-api.md:60-64`.

Where behavior is only reachable end-to-end, sampling substitutes for a seam:
`_characters(2000)` sweeps at `test_generator.py:648`, `:834`, `:857`, `:905`,
`:983`, a 1000-seed loop at `:120` hunting the draft-collision branch, and
300-seed sweeps elsewhere — each ending in `assert found`, an explicit
admission the branch is not directly addressable. `_SkillBook`
(`generator.py:116-149`), whose three application rules are documented in
prose at `:117-121`, has no test of its own at all.

This candidate is downstream of
[Name the term loop's carried state](service-record.md): a service record is
the most likely thing for a relocated seam to be shaped around, so grill that
one first.
