# Contract: Library API

**Feature**: `003-npc-generator`

Every capability in this feature is reachable from `import cetools` without invoking the
command line (FR-055, SC-017). The CLI adds option parsing, two usage-error checks, a stream
split, and an exit code, and nothing else.

## Public surface added

```python
from cetools import (
    # generation
    generate_character, generate_batch,
    # the produced value
    Character, CharacterBatch, CharacterSkill, CareerService,
    HistoryStep, StepThrow, StepEffect,
    # universal chargen tables
    DraftTable, AgingTable, AgingRow, ClassEffect,
    MishapTable, MishapRow, InjuryRow, MishapEffect,
    BackgroundSkills, MedicalTiers, MedicalThreshold, ChargenParameters,
    # name tables
    GivenNameTable, SurnameTable, SurnameEntry,
)
```

## Public surface removed

```python
# nothing
```

`Band` stays exported. It moves from `cetools.tasks` to `cetools.registries` with the
modifier bands (FR-039), and `__init__.py` re-exports it from its new home, so the name and
the contract are unchanged.

**`tests/unit/test_library_api.py` derives the expected `__all__` from these two headings.**
Its parser reads `## Public surface added` and `## Public surface removed` out of
`specs/002-rules-data-loading/contracts/library-api.md` today and must be extended to read
this file as a third contract. Without that, adding any export fails the suite with a set
difference that does not say why.

## Generation

```python
def generate_character(
    roller: Roller,
    rules: RulesData,
    *,
    name: str | None = None,
) -> Character: ...
```

Runs the source material's lifepath end to end and returns the finished character. The
walk consumes `roller` from the first characteristic throw to the last mustering-out roll,
and the character records `roller.seed`.

`name=None` rolls a name from the shipped tables and records the parts it was composed
from. A supplied name is used verbatim, and `given_name`, `surname`, and `surname_region`
are empty (FR-047d). A supplied name is never split, reordered, or decomposed.

**The name never draws from `roller`.** It comes from a roller derived from `roller.seed`,
which is what makes FR-047b hold: the same seed generated with and without a supplied name
produces characters differing in the name and its recorded parts and in nothing else. Pass
a fresh `Roller`; one whose stream is partly consumed still reports its original seed, so
its derived name stream would no longer correspond to its walk.

The character is always alive, always named, and always internally consistent. There is no
seed for which this raises, and no argument that makes it produce a dead or partial
character (FR-022, FR-023, SC-003).

It raises `RulesDataError` only for a rules-data problem a load could not have caught,
which is a characteristic score outside the range the pseudo-hex symbols cover, or a table
row a declared die can reach and the table does not have. Both are unreachable from the
shipped data.

```python
def generate_batch(
    seed: int | str | None,
    rules: RulesData,
    *,
    count: int = 1,
    name: str | None = None,
) -> CharacterBatch: ...
```

Generates `count` characters from one master seed and returns them in a `CharacterBatch`.

Character *i* runs on `master` itself at position 0 and on a derivation of `(master, i)`
above it, so the first characters of a larger batch equal a smaller batch from the same
seed (FR-057), a batch of one is the single character of that seed (FR-048a), and each
character's recorded seed regenerates that character alone (FR-050a). See research R2.

`count` below one raises `CetoolsError`. `name` with `count` above one raises
`CetoolsError` naming both, because a name names one character and applying it to all of
them or to the first alone would each silently discard part of what was asked for
(FR-053a). The CLI turns both into usage errors rather than restating the rule.

It takes a seed rather than a `Roller`, unlike `generate_character`, because it owns the
derivation: a partly consumed `Roller` would still report its original seed and would
silently produce a batch whose positions did not correspond to that seed.

## Types

Field-by-field detail is in `data-model.md`. The shapes:

```python
@dataclass(frozen=True, slots=True)
class Character:
    seed: int
    name: str
    given_name: str
    surname: str
    surname_region: str
    title: str
    characteristics: Mapping[str, int]
    skills: tuple[CharacterSkill, ...]
    careers: tuple[CareerService, ...]
    age: int
    funds: int
    debt: int
    pension: int
    benefits: tuple[str, ...]
    history: tuple[HistoryStep, ...]

@dataclass(frozen=True, slots=True)
class CharacterBatch:
    seed: int
    provenance: Provenance
    characters: tuple[Character, ...]

@dataclass(frozen=True, slots=True)
class CharacterSkill:
    name: str
    specialty: str | None
    level: int

@dataclass(frozen=True, slots=True)
class CareerService:
    career: str
    terms: int
    ladder: str
    rank: int
    title: str
    commissioned: bool
    entered_by: str      # "selected" | "drafted" | "fallback"
    ended: str           # "mishap" | "re-enlistment" | "chose to leave" | "term cap"
    benefit_rolls: int

@dataclass(frozen=True, slots=True)
class HistoryStep:
    kind: str
    career: str
    term: int
    throw: StepThrow | None
    selected: str
    effects: tuple[StepEffect, ...]

@dataclass(frozen=True, slots=True)
class StepThrow:
    faces: tuple[int, ...]
    modifiers: tuple[Modifier, ...]
    total: int
    target: int
    success: bool

@dataclass(frozen=True, slots=True)
class StepEffect:
    kind: str
    subject: str
    amount: int
```

`HistoryStep.kind` and `StepEffect.kind` are closed sets of strings, enumerated in
`data-model.md`. Strings rather than enums because they are what the machine-readable
output emits and what an audit groups by, and an enum would add a conversion at the one
boundary that matters while adding no check the closed set does not already give.

## Changed: `CharacteristicRegistry`

```python
@dataclass(frozen=True, slots=True)
class CharacteristicRegistry:
    names: Mapping[str, str]                # unchanged
    classes: Mapping[str, str]              # NEW
    bands: tuple[Band, ...]                 # moved from TaskParameters
    pseudo_hex_minimum: int                 # NEW
    pseudo_hex: tuple[str, ...]             # NEW

    def __contains__(self, code: object) -> bool: ...
    def characteristic_dm(self, score: int) -> int: ...   # moved from TaskParameters
    def symbol(self, score: int) -> str: ...              # NEW
    def floor(self) -> int: ...                           # NEW
```

`symbol` raises `RulesDataError` naming the score and the declared range for a score
outside it. `floor` returns the value a characteristic reduction clamps at, which is
`pseudo_hex_minimum` (research R13).

## Changed: `TaskParameters`

```python
@dataclass(frozen=True, slots=True)
class TaskParameters:
    roll: str
    target: int
    unskilled_dm: int
    difficulty_dms: Mapping[str, int]
    # characteristic_bands: REMOVED
    # characteristic_dm(): REMOVED
```

**Breaking change**, recorded under a **Breaking changes** changelog heading. `check`'s
signature is unchanged; it now reads `rules.characteristics.characteristic_dm(...)`. No task
check result changes as a consequence, which is SC-014 and which the committed check
goldens are the evidence for. Those goldens must not be regenerated in this feature.

## Changed: `CareerDefinition`

```python
@dataclass(frozen=True, slots=True)
class CareerDefinition:
    name: str
    medical_tier: str            # NEW, required
    always_available: bool       # NEW, default False
    re_enterable: bool           # NEW, default False
    throws: Mapping[str, Throw]  # "promotion" now optional
    tables: Mapping[str, SkillTable]   # "advanced" renamed "specialist";
                                       # "advanced-education" now required
    ladders: tuple[RankLadder, ...]
    mustering_out: MusteringOut
```

## Changed: `RulesData`

Eight fields added; every existing field keeps its name, type, and meaning.

```python
@dataclass(frozen=True, slots=True)
class RulesData:
    task_parameters: TaskParameters
    characteristics: CharacteristicRegistry
    skills: SkillRegistry
    benefits: BenefitRegistry
    careers: Mapping[str, CareerDefinition]
    draft: DraftTable                          # NEW
    aging: AgingTable                          # NEW
    mishaps: MishapTable                       # NEW
    background_skills: BackgroundSkills        # NEW
    medical_tiers: MedicalTiers                # NEW
    chargen: ChargenParameters                 # NEW
    given_names: GivenNameTable                # NEW
    surnames: Mapping[str, SurnameTable]       # NEW, keyed by file stem
    provenance: Provenance
```

`load_rules` and `validate_rules` keep their signatures and their contract exactly. A data
set `validate_rules` reports as valid always loads and one it reports as invalid never
does, unchanged, because both still call one implementation.

## Rendering

```python
def as_text(result, *, full: bool = False) -> str: ...
def as_dict(result) -> dict: ...
def as_json(result) -> str: ...
```

`as_text` gains a keyword-only `full`. Registrations:

| Value | `as_text` | `as_text(full=True)` | `as_dict` |
|---|---|---|---|
| `Character` | the Universal Character Format | the fuller sheet: the format, plus debt, pension, and the history | every field |
| `CharacterBatch` | the sheets, one blank line between consecutive ones | the fuller sheets, same separation | the batch document |
| `ThrowResult`, `CheckResult`, `ValidationReport` | unchanged | raises `CetoolsError` | unchanged |

`full=True` on a value with no fuller form **raises** rather than being ignored. That is
the dispatch-miss failure the existing `as_text` fallback exists to detect, one level down:
a rendering that silently gives less than was asked for is worse than one that says it
cannot. The alternative considered was a second public function, `as_full_text`, rejected
because the fuller sheet is the same rendering of the same value at a different depth and
two entry points would each need their own fallback and their own contract row.

`as_dict(batch)["characters"][i] == as_dict(batch.characters[i])`, so a consumer that
already handles one character handles a batch.

## Package-internal seams

Named here because each crosses a module boundary, and a seam no contract records is one a
later change can break without noticing. This follows the convention
`002-rules-data-loading/contracts/library-api.md` set for `render._problem_line`.

```python
# cetools/seeds.py
def derive_seed(seed: int, *parts: int | str) -> int: ...
```

Folds a seed and one or more parts through the blake2b digest `seeds.py` already uses,
returning a value in the space `resolve_seed` accepts, so a reported decimal string
round-trips. Used by `generator.py` for batch positions and for the name stream. Not
exported, for the same reason `resolve_seed` and `rng_seed` are not: nothing outside the
package computes a seed, and a name with no caller is the speculative surface Principle VI
rejects.

```python
# cetools/names.py
def roll_name(roller: Roller, given: GivenNameTable,
              surnames: Mapping[str, SurnameTable]) -> Name: ...
```

Selects a region uniformly over the surname tables in force, then a surname within it, then
a given name (FR-043f, FR-043g). Not exported, because naming a character is reached through
`generate_character` and no requirement asks for a standalone name capability.

## Errors

No new error type. A draft table naming a career that is not in force is a cross-file
validation problem and fails the load, exactly like two careers declaring one name. A
characteristic outside the pseudo-hex range is a `RulesDataError`, for the same reason
`characteristic_dm` already raises one for a score no band covers. A count below one, or a
name beside a count above one, is a `CetoolsError` from the library and a usage error from
the CLI. One `except CetoolsError` still catches everything the library raises.
