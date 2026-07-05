# Contract: `resolve_survival_mishap` Engine API

`resolve_survival_mishap(roller: DiceRoller, characteristics: dict[str, int]) ->
tuple[MishapOutcome, int]` (new, `src/cetools/engine/mishaps.py`) is the sole new
public entry point this feature adds to the engine. It is called exactly once by
`generate_character` (`src/cetools/engine/generator.py`) whenever a term's survival
check fails, and is importable/callable in isolation per Principle II (Library-First)
— no CLI or generator context required to invoke it directly.

## Signature

```python
def resolve_survival_mishap(
    roller: DiceRoller,
    characteristics: dict[str, int],
) -> tuple[MishapOutcome, int]:
    ...
```

Returns the `MishapOutcome` exactly as `data-model.md` specifies (no `debt` field
on it) plus a second `int`: this mishap's debt (`0`, the fixed `10_000`, or the
random `1D6 * 10_000` crisis amount). `MishapOutcome` itself never carries debt —
see `data-model.md`'s rationale — so the debt figure has to travel back to the
caller some other way; a tuple is the minimal change that makes that literally
possible (see tasks.md's Implementation Note for why this deviates from an
earlier bare-`MishapOutcome` draft of this contract).

## Behavior

1. Roll `roller.roll(6)` against `SURVIVAL_MISHAPS_TABLE` (1-indexed) to select a
   `MishapEntry`.
2. If `entry.injury_rolls > 0`, resolve the Injury table that many times (rolling
   `roller.roll(6)` each time) and apply the reduction(s) from the entry per
   `entry.injury_rolls`:
   - `1` roll: apply that single `INJURY_TABLE` row.
   - `2` rolls: apply only the row corresponding to the **lower** of the two rolls
     (more severe; see `research.md` D1).
   - Applying a row means: pick a primary stat from `candidate_stats` (via an
     additional roll when there is more than one candidate), reduce it by
     `primary_dice` D6 or `primary_fixed`, then reduce every other physical stat by
     `secondary_amount` (if nonzero) — each reduction floored at 0
     (`max(0, current - amount)`).
3. If any physical characteristic was driven to 0 by step 2, charge one injury-crisis
   debt of `roller.roll(6) * 10_000` and restore every zeroed physical characteristic
   to 1.
4. If `entry.debt > 0` (the legal-battle outcome), that fixed amount is this
   mishap's debt instead (steps 3 and 4 are mutually exclusive in practice: an
   entry with `debt > 0` never has `injury_rolls > 0`).
5. Return `(outcome, debt_amount)`, where `outcome` is a `MishapOutcome` built from:
   the table roll, `entry.discharge_type`, `entry.imprisoned`, the map of stat →
   total amount actually reduced in step 2 (`{}` if none), and whether a crisis
   fired in step 3; `debt_amount` is `0`, the step-3 crisis amount, or the step-4
   fixed amount (never both — see step 4).

## Side effects

- **Mutates** `characteristics` in place (reductions and any crisis restoration to
  1), exactly like the existing `_apply_aging` helper it is modeled on.
- Performs **no I/O**, raises no exceptions for normal SRD-defined rolls, and never
  signals character death — every 1D6 roll maps to a defined table entry.
- Does **not** itself update `Character.debt` — the caller (`generate_character`) is
  responsible for adding the returned `debt_amount` to the character's running debt
  total (see `data-model.md`'s "Behavioral contract of the term loop"). The function
  only returns the debt for *this* mishap; accumulating it onto `Character.debt` is
  the caller's job.

## Return type

See `data-model.md` for the full `MishapOutcome` field list. `MishapOutcome` itself
never carries a `debt` field — debt is character-level financial state, not
mishap-table metadata — so the debt this mishap incurred travels back to the caller
as the tuple's second element instead. The caller accumulates it onto
`Character.debt`; there is, at most, one debt-contributing event per character, per
the spec's "at most one mishap" invariant.

## Determinism / testability

Like every other engine function, `resolve_survival_mishap` takes its `DiceRoller` as
a parameter and has no hidden randomness — it is fully drivable by
`ConstantRoller`/`SequenceRoller`/`SmartRoller` from `tests/conftest.py`, enabling
exact per-outcome and per-injury-row unit tests, as well as the large-sample
statistical distribution test required by SC-004.
