# Contract: Rules Data Files

**Feature**: `002-rules-data-loading`

This is the shape of every rules data file, shipped or user-supplied. It is a
contract in the strict sense: an override file is held to it exactly as a packaged
file is (FR-031), and every key not named here is rejected (FR-020).

## Packaged layout

```text
src/cetools/data/
├── __init__.py                     # makes the directory importable; not a data file
├── tasks.toml                      # kind: task-parameters
├── registries/
│   ├── characteristics.toml        # kind: characteristics
│   ├── skills.toml                 # kind: skills
│   └── benefits.toml               # kind: benefits
└── careers/
    └── navy.toml                   # kind: career
```

Every `.toml` file under `data/`, at any depth, is a data file. Basenames are unique
across the whole layout, because the basename is the composition key; a test enforces
that (see `plan.md`).

## Every file: the header

```toml
# Open Game Content per OGL 1.0a; see LICENSE-OGL.txt

schema = "career"
schema-version = 1
```

| Key | Type | Required | Meaning |
|---|---|---|---|
| `schema` | string | yes | The kind of file, from the fixed set below. Selects the schema that validates it. |
| `schema-version` | integer | yes | The version of that kind's shape this file was written against. |

Kinds: `task-parameters`, `characteristics`, `skills`, `benefits`, `career`. The
supported version for every kind is currently `1`.

Rules:

1. A file declaring no `schema`, or no `schema-version`, is rejected (FR-001).
2. A file declaring an unsupported version for its kind is rejected naming the
   declared version and the supported version for that kind, and its contents are not
   interpreted, so no further problem is reported from that file (FR-002).
3. A file whose basename matches a packaged file must declare that file's kind. A
   mismatch is a problem naming both kinds.
4. `schema-version` counts per kind (FR-002a). It is never derived from, compared to,
   or displayed alongside the package's release version (FR-003).
5. The Open Game Content designation comment is required in every shipped data file
   and neither Product Identity string may appear (FR-046).

## `task-parameters` (`tasks.toml`)

Unchanged from `001-dice-task-engine` except for the two header keys. Reproduced here
because this file is now an ordinary member of the validated set (FR-044).

```toml
schema = "task-parameters"
schema-version = 1

[task]
roll = "2d6"
target = 8
unskilled-dm = -3

[difficulty-dms]
"Average" = 0
# ... one rung per difficulty name

[characteristic-dms]
"0-2" = -2
"33+" = 9
# ... one row per band
```

| Location | Type | Required | Notes |
|---|---|---|---|
| `task.roll` | string | yes | Dice notation describing a count and a side count. `d66` is rejected. |
| `task.target` | integer | yes | |
| `task.unskilled-dm` | integer | yes | |
| `difficulty-dms.*` | integer | yes, at least one | Exactly one rung must be `0`. |
| `characteristic-dms.*` | integer | yes, at least one | Keys are `N-M` or `N+`. Exactly one band must be unbounded. |

Every rule the previous feature's loader enforced is preserved, restated as collected
problems rather than as the first raise.

## `characteristics` (`registries/characteristics.toml`)

```toml
schema = "characteristics"
schema-version = 1

[characteristics]
STR = "Strength"
DEX = "Dexterity"
END = "Endurance"
INT = "Intellect"
EDU = "Education"
SOC = "Social Standing"
```

| Location | Type | Notes |
|---|---|---|
| `characteristics.*` | string | Key is the code used in the notation, value is the human label. At least one entry. Codes are matched case sensitively. |

Characteristics are data rather than a constant in the parser (FR-012), so the
notation's `STR +1` resolves through this file and nothing else.

## `skills` (`registries/skills.toml`)

```toml
schema = "skills"
schema-version = 1

[skills]
"Admin" = []
"Blade" = ["Cutlass", "Dagger", "Sword"]
"Vacc Suit" = []
```

| Location | Type | Notes |
|---|---|---|
| `skills.*` | array of string | Key is the skill name, value is its permitted specialties. At least one entry. |

The specialty list is required for every skill, empty when the skill has none. Absence
is not accepted as a way of saying "no specialties": FR-011 requires each skill to
declare whether it has them, and a missing key is indistinguishable from a forgotten
one.

## `benefits` (`registries/benefits.toml`)

```toml
schema = "benefits"
schema-version = 1

benefits = ["Low Passage", "Middle Passage", "High Passage", "Blade", "Gun", "Ship Share"]
```

| Location | Type | Notes |
|---|---|---|
| `benefits` | array of string | Benefit item names. At least one entry. |

A name may also exist in the skills registry with no interaction; the table an entry
appears in fixes which registry applies (FR-005).

## `career` (`careers/navy.toml`)

Values below are illustrative of the shape. The shipped reference career is authored
from the source material during implementation (FR-018).

```toml
schema = "career"
schema-version = 1

name = "Navy"

[throws.qualification]
characteristic = "INT"
target = 8

[throws.survival]
characteristic = "INT"
target = 5

[throws.commission]
characteristic = "SOC"
target = 10

[throws.promotion]
characteristic = "EDU"
target = 8

[throws.re-enlistment]
target = 6

[tables.personal]
entries = ["STR +1", "DEX +1", "END +1", "INT +1", "EDU +1", "SOC +1"]

[tables.service]
entries = ["Ship's Boat", "Vacc Suit", "Gunnery", "Mechanical", "Gun Combat", "Blade"]

[tables.advanced]
entries = ["Vacc Suit", "Mechanical", "Electronic", "Engineering", "Gunnery", "Jack-of-all-Trades"]

[tables.advanced-education]
requires = "EDU 8+"
entries = ["Medical", "Navigation", "Engineering", "Computer", "Pilot", "Admin"]

[[ladders]]
name = "enlisted"
ranks = [
  { rank = 1, title = "Able Spacehand" },
  { rank = 5, title = "Petty Officer", bonus = "Mechanical 1" },
]

[[ladders]]
name = "officer"
ranks = [
  { rank = 1, title = "Ensign", bonus = "SOC +1" },
  { rank = 2, title = "Lieutenant" },
]

[mustering-out]
cash = [1000, 5000, 5000, 10000, 20000, 50000, 50000]
benefits = ["Low Passage", "INT +1", "EDU +2", "Blade", "High Passage", "Ship Share"]
```

### Keys

| Location | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Human label, not the composition identity (FR-019a). |
| `throws.qualification` | throw | yes | |
| `throws.survival` | throw | yes | |
| `throws.commission` | throw | no | Absent for a career with no commission. |
| `throws.promotion` | throw | yes | |
| `throws.re-enlistment` | throw | yes | |
| `tables.personal` | table | yes | |
| `tables.service` | table | yes | |
| `tables.advanced` | table | yes | |
| `tables.advanced-education` | table | no | |
| `ladders` | array of ladder | yes | At least one. |
| `mustering-out.cash` | array of integer | yes | Non-empty, each non-negative. Plain values, never notation (FR-004a). |
| `mustering-out.benefits` | array of notation | yes | Non-empty. Benefit-table context. |

A **throw** is a table with:

| Key | Type | Required | Notes |
|---|---|---|---|
| `characteristic` | string | no | A characteristics registry code. Absent means the throw takes no characteristic modifier. |
| `target` | integer | yes | Plain value, never notation (FR-014, FR-004a). |

A **table** is a table with:

| Key | Type | Required | Notes |
|---|---|---|---|
| `requires` | notation | no | Gate context: a characteristic check such as `EDU 8+` (FR-015). |
| `entries` | array of notation | yes | Non-empty. Skill-table context. |

A **ladder** is a table with:

| Key | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Distinct within the career. |
| `ranks` | array of rank | yes | Non-empty. |

A **rank** is a table with:

| Key | Type | Required | Notes |
|---|---|---|---|
| `rank` | integer | yes | Non-negative, distinct within its ladder. |
| `title` | string | yes | |
| `bonus` | notation | no | Skill-table context (FR-016). |

The table names and the throw names are closed sets. `[tables.sevice]` is an
unrecognized key, not a new table.

## Composition

1. The packaged data set is every `.toml` under `cetools/data/`, keyed by basename.
2. If an override location was named and is a directory, every `.toml` under it, at
   any depth, is collected and keyed by basename. If it is a single file, that file
   alone is collected, keyed by its basename (FR-040a).
3. A key present in both is a **replacement**: the override file is used whole, and
   nothing from the packaged file survives (FR-029, FR-030).
4. A key present only in the override is an **addition** (FR-032).
5. Two override files sharing a basename is a problem naming both.
6. Nothing outside the package is opened when no override was named (FR-027).

Composition never reads a file's contents to decide its position. Validation happens
afterwards, over the composed set, all of it, every time (FR-024).

## Cross-file rules

Checked after every file has been read, because they cannot be judged one file at a
time:

| Rule | Requirement |
|---|---|
| No two careers in force declare the same `name` | FR-019b. The problem names both files. |
| No two files in force declare the same singleton kind | Registry analogue of FR-019b (see `data-model.md`). The problem names both files. |
| Every singleton kind is present | A data set missing its skills registry cannot validate careers. |
| Every name resolves against its registry | FR-013. |

## Failure

Any problem anywhere fails the whole data set (FR-025). No valid subset is exposed,
no built-in value is substituted (FR-026), and the outcome does not depend on which
part of the data set a later operation would have read (FR-024).
