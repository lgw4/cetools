# Phase 1 Data Model: Validated Rules Data Loading

**Feature**: `002-rules-data-loading` | **Date**: 2026-08-13

Every type below is a frozen dataclass with `slots=True`, following the convention
`001-dice-task-engine` established: these are value objects that are built once by
the loader, then read, rendered, and compared, never mutated. Sequence fields are
tuples and mapping fields are read-only mappings, so a caller holding a reference
cannot edit the loaded data set underneath another caller.

**Vocabulary.** The spec says "data set", "provenance", "validation problem" and
"table entry". The code says `RulesData`, `Provenance`, `ValidationProblem` and the
notation entry types. The mapping is one-to-one; no third term is introduced.

## Overview

```text
RulesData
├── task_parameters : TaskParameters        (existing type, unchanged shape)
├── characteristics : CharacteristicRegistry
├── skills          : SkillRegistry
├── benefits        : BenefitRegistry
├── careers         : Mapping[str, CareerDefinition]   keyed by file stem
└── provenance      : Provenance
```

## The notation entry types (`cetools/notation.py`)

One entry of a table that mixes kinds of thing in one cell. The parse function
returns exactly one of four types; the caller's context decides which are admissible
and which registry validates the name (research R10).

### `SkillReference`

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Base skill name, trimmed. Validated against the skills registry. |
| `specialty` | `str \| None` | `None` when the entry gave none. |

`specialty is None` for a skill that has specialties means a choice is owed, and stays
distinguishable from a specialty that was given (FR-008). The type carries no
knowledge of which skills owe a choice; that is the registry's (FR-011).

### `CharacteristicCheck`

| Field | Type | Notes |
|---|---|---|
| `characteristic` | `str` | Validated against the characteristics registry. |
| `target` | `int` | The number the throw must equal or exceed. |

Written `INT 4+`. Legal only in a table gate.

### `CharacteristicAdjustment`

| Field | Type | Notes |
|---|---|---|
| `characteristic` | `str` | Validated against the characteristics registry. |
| `amount` | `int` | Signed; the sign is required in the written form. |

Written `STR +1` or `SOC -1`.

### `SkillGrant`

| Field | Type | Notes |
|---|---|---|
| `skill` | `SkillReference` | Carries its own optional specialty. |
| `level` | `int` | Non-negative. |

Written `Pilot 2` or `Blade (Cutlass) 1`.

### `BenefitItem`

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Validated against the benefit items registry. |

The bare form in a benefits table. A bare form in a skill table yields a
`SkillReference` instead: same written text, different type, decided by position
(FR-005).

## The registries (`cetools/registries.py`)

### `CharacteristicRegistry`

| Field | Type | Notes |
|---|---|---|
| `names` | `Mapping[str, str]` | Code (`"INT"`) to label (`"Intellect"`). Insertion order is the file's order. |

`__contains__` delegates to `names`. Characteristic codes are matched exactly, case
sensitively: a registry entry is the spelling that data files must use, and
case-folding here would make `int 4+` valid and quietly widen the notation.

### `SkillRegistry`

| Field | Type | Notes |
|---|---|---|
| `skills` | `Mapping[str, tuple[str, ...]]` | Skill name to its permitted specialties. An empty tuple means the skill has none. |

Four distinguishable outcomes when resolving a `SkillReference`, which is what FR-007
and FR-008 together require — the table below has four rows, `SkillResolution` has four
members, and contracts/notation.md says four:

| Condition | Outcome |
|---|---|
| name absent from `skills` | unrecognized skill name |
| specialty given, skill's tuple empty | specialty given for a skill that has none |
| specialty given, not in the skill's tuple | unrecognized specialty for that skill |
| specialty given and listed, or no specialty given | valid |

### `BenefitRegistry`

| Field | Type | Notes |
|---|---|---|
| `items` | `tuple[str, ...]` | Benefit item names, in file order. |

A name may appear in more than one registry with no interaction, because the table an
entry sits in fixes which registry applies (spec Edge Cases).

## The career types (`cetools/careers.py`)

### `CareerDefinition`

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Human label (FR-019a). Not the composition identity. |
| `throws` | `Mapping[str, Throw]` | Keys from the fixed set below. |
| `tables` | `Mapping[str, SkillTable]` | Keys from the fixed set below. |
| `ladders` | `tuple[RankLadder, ...]` | At least one. |
| `mustering_out` | `MusteringOut` | |

Throw keys, fixed: `qualification`, `survival`, `commission`, `promotion`,
`re-enlistment`. All required except `commission`, which not every career has.

Table keys, fixed: `personal`, `service`, `advanced`, `advanced-education`. All
required except `advanced-education`. The set is closed rather than open so that a
misspelled table name is caught by the unrecognized-key rule (FR-020); an open set
would make `[tables.sevice]` a new table rather than a typo.

### `Throw`

| Field | Type | Notes |
|---|---|---|
| `characteristic` | `str \| None` | `None` means the throw takes no characteristic modifier, which is how re-enlistment is thrown. |
| `target` | `int` | Plain typed value, never notation (FR-004a). Positive; a throw against a target of zero or less is not a throw (FR-014). |

### `SkillTable`

| Field | Type | Notes |
|---|---|---|
| `requires` | `CharacteristicCheck \| None` | The gate (FR-015). `None` for an ungated table. |
| `entries` | `tuple[SkillTableEntry, ...]` | Non-empty. Each is a `SkillReference`, `SkillGrant`, or `CharacteristicAdjustment`. |

`SkillTableEntry` is a type alias for that union, not a class.

### `RankLadder` and `Rank`

| `RankLadder` field | Type | Notes |
|---|---|---|
| `name` | `str` | For example `enlisted`, `officer`. Distinct within a career. |
| `ranks` | `tuple[Rank, ...]` | Non-empty, sorted by `rank`, no duplicate positions. |

| `Rank` field | Type | Notes |
|---|---|---|
| `rank` | `int` | Position on the ladder, non-negative (FR-016). |
| `title` | `str` | |
| `bonus` | `SkillTableEntry \| None` | Granted on reaching the rank. Same admissible forms as a skill table entry. |

### `MusteringOut`

| Field | Type | Notes |
|---|---|---|
| `cash` | `tuple[int, ...]` | Plain amounts, non-empty, non-negative (FR-017, FR-004a). |
| `benefits` | `tuple[BenefitItem \| CharacteristicAdjustment, ...]` | Non-empty. Notation-bearing. |

No length constraint is imposed on any table; see research R13.

## Provenance (`cetools/provenance.py`)

### `Disposition`

A `StrEnum` with members `REPLACED` and `ADDED`, so the value serializes to
`"replaced"` and `"added"` in JSON without a conversion step (FR-032, FR-035).

A file ignored under FR-032a is **not** a third member here. It carries no fingerprint,
because nothing was made of its content, and it contributed nothing to the data set. It
is held in a separate `ignored` tuple instead, which keeps `fingerprint` non-optional and
keeps `is_packaged` an emptiness check rather than a filter.

### `FileProvenance`

| Field | Type | Notes |
|---|---|---|
| `file` | `str` | The composition key, which is the basename (research R3). |
| `disposition` | `Disposition` | |
| `fingerprint` | `str` | `"sha256:"` plus the 64-character lowercase hex digest of the file's raw bytes (research R4). |

### `Provenance`

| Field | Type | Notes |
|---|---|---|
| `version` | `str` | The installed package version, from `importlib.metadata` (FR-033a). Present whether or not anything was overridden. |
| `files` | `tuple[FileProvenance, ...]` | Files that took effect. Sorted by `file`. Empty exactly when nothing was overridden. |
| `ignored` | `tuple[str, ...]` | Basenames of files in an override location that are not rules data (FR-032a). Sorted. Dot-prefixed files never appear here (FR-032b). |

| Property | Returns |
|---|---|
| `is_packaged` | `not self.files` |

An empty `files` is the packaged data set, which FR-034 says needs no detail beyond the
version because that version determines the content exactly. Provenance is still reported
in that case, as a value saying "packaged" rather than as an absent line (FR-037).

`ignored` is independent of `is_packaged`: an override location holding only a README
leaves the data packaged and the README named. That combination is the point of FR-032a,
so the two fields must not be collapsed into one.

The version is read once from installed package metadata rather than threaded in by the
caller, so that a result cannot report a version other than the one that produced it.

## Validation reporting (`cetools/errors.py`)

### `ValidationProblem`

| Field | Type | Notes |
|---|---|---|
| `file` | `str` | Composition key of the file the problem is in. |
| `location` | `str` | Dotted key path with array indices, for example `tables.service.entries[2]`. `""` for a problem about the file as a whole, such as an unreadable file. |
| `found` | `str` | What was there. |
| `expected` | `str` | What would have been acceptable. |

`found` and `expected` are separate fields rather than one message because FR-022
requires both and because the machine-readable output must carry them without a
consumer parsing prose (Acceptance Scenario 2.4).

Problems sort by `(file, location)` so a report is stable run to run.

### `RulesDataError`

Unchanged in name and place in the hierarchy, extended with a `problems` field:

```python
class RulesDataError(CetoolsError):
    def __init__(self, message: str, problems: Sequence[ValidationProblem] = ()) -> None
    problems: tuple[ValidationProblem, ...]
```

The message-only construction is retained because `tasks.py` raises this type for
runtime invariant failures (a characteristic score no band covers) that are not data
file problems and carry no location.

## The loaded data set (`cetools/rules.py`)

### `RulesData`

| Field | Type | Notes |
|---|---|---|
| `task_parameters` | `TaskParameters` | The existing type, now an ordinary member of the set (FR-044). |
| `characteristics` | `CharacteristicRegistry` | |
| `skills` | `SkillRegistry` | |
| `benefits` | `BenefitRegistry` | |
| `careers` | `Mapping[str, CareerDefinition]` | Keyed by the file stem, so `careers/navy.toml` is `careers["navy"]` (FR-019a). |
| `provenance` | `Provenance` | |

A `RulesData` exists only if the whole data set validated. There is no partially
loaded instance and no way to build one from a subset (FR-025).

### `ValidationReport`

| Field | Type | Notes |
|---|---|---|
| `provenance` | `Provenance` | Known even when validation fails, because composition precedes validation. |
| `file_count` | `int` | Files composed and checked. |
| `problems` | `tuple[ValidationProblem, ...]` | Sorted. Empty means valid. |

| Property | Returns |
|---|---|
| `valid` | `not self.problems` |

## Changes to existing types

### `CheckResult` gains one field

| Field | Type | Notes |
|---|---|---|
| `provenance` | `Provenance` | Appended after `seed`, so positional construction of the existing fields is unaffected. |

No other field changes; FR-045 permits no change to the dice, the modifiers, the
total, the target, the success, or the seed.

### `TaskParameters` is unchanged

Its fields, its methods, and its arithmetic are untouched. Only where it comes from
changes: it is built by the loader as one member of `RulesData` rather than by a
reader of its own.

## Schema versions

| Kind | `schema` value | Supported version | File |
|---|---|---|---|
| Task parameters | `task-parameters` | 1 | `tasks.toml` |
| Characteristics | `characteristics` | 1 | `registries/characteristics.toml` |
| Skills | `skills` | 1 | `registries/skills.toml` |
| Benefit items | `benefits` | 1 | `registries/benefits.toml` |
| Career | `career` | 1 | `careers/navy.toml` |

Versions are counted per kind (FR-002a, which now names this closed set of five in the
spec): the supported version is looked up by the file's declared kind, so bumping one kind
leaves user files of every other kind valid. Each file declares its kind (FR-001a), and a
file replacing a packaged one must declare that file's kind.

`career` is the only repeatable kind. The other four occur exactly once, and FR-010a
requires each to be present and forbids two files in force from declaring the same one,
naming both when they do. That rule catches a misspelled registry filename, which would
otherwise be admitted as an addition and leave the real registry silently in force. It
began as the registry analogue of FR-019b's duplicate career name rule and is now a
requirement in its own right.
