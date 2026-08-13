# Phase 1 Data Model: Dice and Task Check Engine

**Feature**: `001-dice-task-engine` | **Date**: 2026-08-11

All result types are frozen dataclasses with `slots=True`: they are value objects
that are compared, rendered, and serialized but never mutated after construction.
Sequence fields are tuples so instances stay hashable and cannot be edited in place
by a caller holding a reference.

**A note on vocabulary.** The spec says "modifier", "unskilled penalty", and
"characteristic modifier"; the data file and the API say `dm`, `unskilled-dm`, and
`characteristic_dm`. These name the same things. "DM" is the source rules' own
abbreviation for a dice modifier and is the right register for a field name; the
spec's longer forms are the right register for prose. The mapping is one-to-one and
no third term is introduced anywhere.

## Roller

The only source of randomness in the feature. Constructed from a seed and passed
explicitly to every function that needs a die.

| Field | Type | Notes |
|-------|------|-------|
| `seed` | `int` | Resolved seed, always a non-negative integer below 2^64 unless the caller supplied a larger one deliberately. Public, because every result echoes it. |
| `_rng` | `random.Random` | Private. Never shared, never reseeded after construction. |

**Construction**: `Roller(seed: int | str | None = None)`

Seed resolution, in one place, used identically by library and CLI:

| Input | Resolution |
|-------|-----------|
| `None` | `secrets.randbits(64)` |
| `int` | used as given |
| `str` matching `^[+-]?[0-9]+$` | `int(value)` |
| any other `str` | blake2b-64 fold of the UTF-8 bytes |

**Methods**:

- `die(sides: int) -> int` - one uniform face in `1..sides` via rejection sampling
  on `getrandbits`.
- `dice(count: int, sides: int) -> tuple[int, ...]` - `count` faces in draw order.

**Validation**: `count` and `sides` must each be integers of at least 1; otherwise
`DiceError`.

**Invariant**: a `Roller` touches no module-level random state. Two `Roller`
instances in one process are fully independent.

## ThrowResult

Produced by `throw`, `throw_dice`, and `d66`. One type serves all three so the
`roll` command has a single output shape.

| Field | Type | Notes |
|-------|------|-------|
| `notation` | `str` | Canonical form of what was thrown: `"2d6+1"`, `"1d6"`, `"d66"`. |
| `faces` | `tuple[int, ...]` | Individual die faces in draw order. |
| `modifier` | `int` | Flat modifier; always `0` for `d66`. |
| `total` | `int` | See below. |
| `seed` | `int` | Copied from the `Roller` that produced it. |

**`total` semantics**: for a dice throw, `sum(faces) + modifier`. For `d66`, the
composed two-digit value `faces[0] * 10 + faces[1]`, which is deliberately not a
sum. `notation` is what tells a consumer which rule applies; this is stated in the
JSON contract because the field is part of a committed interface.

**Invariants**:

- `len(faces) == count` and every face is within `1..sides`.
- For `d66`: `len(faces) == 2`, both faces within `1..6`, `total` within `11..66`
  with no digit `0` and no digit above `6`.

## Modifier

A single labeled adjustment to a check. The four kinds (difficulty,
characteristic, skill, situational) are all represented by this one type and are
itemized identically in output, so a reader sees a flat, auditable list.

| Field | Type | Notes |
|-------|------|-------|
| `label` | `str` | Human-facing. Non-empty; whitespace-trimmed. |
| `value` | `int` | Signed. May be `0` (a skill at level 0 still appears, so the reader can see it was considered). |

**Label conventions**, fixed because golden files pin them:

| Kind | Label | Example |
|------|-------|---------|
| Difficulty | `Difficulty (<name>)` | `Difficulty (Difficult)` |
| Characteristic | `Characteristic <score>` | `Characteristic 9` |
| Skill, trained | `Skill <level>` | `Skill 2` |
| Skill, untrained | `Unskilled` | `Unskilled` |
| Situational | caller's own text, verbatim | `cover` |

Characteristics are labeled generically because this feature has no notion of
characteristic names; `DEX` and friends arrive with the NPC generator.

## CheckResult

| Field | Type | Notes |
|-------|------|-------|
| `faces` | `tuple[int, ...]` | Faces of the check throw, from `task.roll` in the data. |
| `dice_total` | `int` | `sum(faces)`, before modifiers. |
| `modifiers` | `tuple[Modifier, ...]` | Every applied modifier, in fixed order (below). |
| `total` | `int` | `dice_total + sum(m.value for m in modifiers)`. |
| `target` | `int` | From the data file. Echoed so output is self-explaining. |
| `success` | `bool` | `total >= target`. |
| `seed` | `int` | Copied from the `Roller`. |

**Modifier order** is fixed and deterministic: difficulty, then characteristic (if
given), then skill, then the caller's situational modifiers in the order supplied.
Golden files depend on this, so it is a contract, not an incidental detail.

**Invariants**:

- `total == dice_total + sum(m.value for m in modifiers)` always holds.
- `success == (total >= target)` always holds, with no special case for a natural
  high or low roll (FR-020).

## Band

One row of the characteristic table. Internal to the rules data, but part of the
data file contract.

| Field | Type | Notes |
|-------|------|-------|
| `minimum` | `int` | Inclusive lower bound. |
| `maximum` | `int \| None` | Inclusive upper bound; `None` means unbounded. |
| `dm` | `int` | Modifier for scores in the band. |

Exactly one band in the table has `maximum is None`, and it sorts last.

## TaskParameters

The parsed contents of `tasks.toml`. Loaded once and cached.

| Field | Type | Notes |
|-------|------|-------|
| `roll` | `str` | Dice notation for a check, e.g. `"2d6"`. Parsed by the same grammar `cetools roll` uses. |
| `target` | `int` | Flat target. Success is `total >= target`. |
| `unskilled_dm` | `int` | Applied when no skill level is given. |
| `difficulty_dms` | `Mapping[str, int]` | Ladder, in data-file order. |
| `characteristic_bands` | `tuple[Band, ...]` | Sorted by `minimum`. |

**Methods**:

- `difficulty_dm(name: str) -> int` - exact match, character for character. Unknown
  name raises `TaskError` whose message lists the valid names, per FR-019.
- `default_difficulty() -> str` - the name of the sole entry whose modifier is `0`,
  used when the caller names no difficulty (FR-014). Derived from the data rather
  than being a constant in the CLI, so no rung name lives in code.
- `characteristic_dm(score: int) -> int` - first band containing the score.
  Negative score raises `TaskError`. A score matching no band raises `RulesDataError`,
  since that means the shipped table has a gap.

**Loading validation** (minimal by design; feature 2 replaces this wholesale):
required tables present, values are integers of the right sign-free types, band
keys parse as `N-M` or `N+`, exactly one unbounded band exists, and exactly one
difficulty rung has a modifier of `0`. Any failure raises `RulesDataError`. There
is no fallback to built-in values.

**FR-024 is the normative statement** of what "required" means, and the table in
[contracts/tasks-toml.md](contracts/tasks-toml.md) is its check-by-check
expansion. The two invariants that survive every house-rule edit — exactly one
zero-modifier rung, exactly one unbounded band — are restated in FR-014 and FR-022
for local readability, but FR-024 is where they are decided. If the three ever
disagree, FR-024 wins.

Validation lives in `_task_parameters_from_toml`, not in `load_task_parameters`, so
every failure path is reachable from a test without a file on disk. See
[contracts/library-api.md](contracts/library-api.md).

## Error hierarchy

```text
CetoolsError        rendering dispatch miss (no leaf describes it)
├── DiceError        invalid notation, non-positive count or sides,
│                    unsupported notation or seed type
├── RulesDataError   data file missing, unreadable, malformed, or incomplete
└── TaskError        unknown difficulty, negative characteristic, negative skill
```

Raised by the library, never caught by it. Only `cli.py` catches `CetoolsError`.
The base is raised directly for one condition, an `as_text`/`as_dict` call on an
unregistered result type: FR-029 admits no exception, and a fourth public leaf for
a path no supported caller reaches is the speculative surface Principle VI rejects.

## Relationships

```text
Roller ──produces──> ThrowResult
   │
   └──produces──> CheckResult ──contains──> Modifier (ordered)
                       ▲
                       │ reads target, unskilled_dm, roll,
                       │ difficulty ladder, characteristic bands
                       │
              TaskParameters ──contains──> Band (ordered)
                       ▲
                       │ parsed from
                  tasks.toml
```

Every result carries its own `seed`, so no result depends on ambient context to be
reproducible.
