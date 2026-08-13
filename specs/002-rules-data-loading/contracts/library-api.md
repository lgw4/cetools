# Contract: Library API

**Feature**: `002-rules-data-loading`

Every capability in this feature is reachable from `import cetools` without invoking
the command line (FR-043, SC-013). The CLI adds argument parsing, printing, and exit
codes, and nothing else.

## Public surface added

```python
from cetools import (
    # loading and validation
    load_rules, validate_rules, RulesData, ValidationReport,
    # problems
    ValidationProblem,
    # provenance
    Provenance, FileProvenance, Disposition,
    # registries
    CharacteristicRegistry, SkillRegistry, BenefitRegistry,
    # notation
    parse_entry, SkillReference, SkillGrant,
    CharacteristicCheck, CharacteristicAdjustment, BenefitItem,
    # careers
    CareerDefinition, Throw, SkillTable, RankLadder, Rank, MusteringOut,
)
```

## Public surface removed

```python
load_task_parameters   # replaced by load_rules(...).task_parameters
```

`TaskParameters` and `Band` remain exported: the type survives, only its reader is
replaced (FR-044).

## Loading

```python
def load_rules(override: Path | str | None = None) -> RulesData: ...
```

Composes the packaged data set with `override` if one is given, validates all of it,
and returns the loaded set. Raises `RulesDataError` carrying `.problems` if anything
is wrong; the exception's message summarizes and the tuple carries the detail.

`override` may name a directory or a single file (FR-040a). A path that does not
exist raises `RulesDataError` naming it. `None` opens nothing outside the installed
package (FR-027).

The no-override call is cached, because the installed files cannot change within a
process. Tests that write data files and reload must call
`load_rules.cache_clear()`; the suite's autouse fixture does it for them.

```python
def validate_rules(override: Path | str | None = None) -> ValidationReport: ...
```

The same composition and the same validation, returning the report instead of
raising (FR-023). A data set `validate_rules` reports as valid always loads, and one
it reports as invalid never does, because both entry points call one implementation
and differ only in what they do with its result.

## Types

```python
@dataclass(frozen=True, slots=True)
class RulesData:
    task_parameters: TaskParameters
    characteristics: CharacteristicRegistry
    skills: SkillRegistry
    benefits: BenefitRegistry
    careers: Mapping[str, CareerDefinition]   # keyed by file stem
    provenance: Provenance

@dataclass(frozen=True, slots=True)
class ValidationReport:
    provenance: Provenance
    file_count: int
    problems: tuple[ValidationProblem, ...]
    @property
    def valid(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class ValidationProblem:
    file: str
    location: str
    found: str
    expected: str

@dataclass(frozen=True, slots=True)
class Provenance:
    files: tuple[FileProvenance, ...]
    @property
    def is_packaged(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class FileProvenance:
    file: str
    disposition: Disposition      # StrEnum: REPLACED | ADDED
    fingerprint: str              # "sha256:<64 hex chars>"
```

Field-by-field detail for the registry, career, and notation types is in
`data-model.md`; their file-level schema is in `contracts/data-files.md`.

## Notation

```python
def parse_entry(text: str, context: EntryContext) -> TableEntry: ...
```

`EntryContext` is a `StrEnum` with `SKILL_TABLE`, `BENEFIT_TABLE`, and `GATE`.
`TableEntry` is the union of the five notation types. Raises `RulesDataError` for a
malformed entry or a form the context does not admit; the loader catches it and
records a `ValidationProblem` rather than letting it escape.

Registry validation is separate from parsing: `parse_entry` produces a
`SkillReference` for `Vac Suit` and the registry is what rejects it, so a caller
can parse an entry without a data set in hand.

## Changed: `check`

```python
def check(
    roller: Roller,
    *,
    difficulty: str | None = None,
    characteristic: int | None = None,
    skill: int | None = None,
    modifiers: Sequence[Modifier] = (),
    rules: RulesData | None = None,          # was: parameters: TaskParameters | None
) -> CheckResult: ...
```

`rules=None` loads the packaged data set. The returned `CheckResult` carries a
`provenance` field copied from `rules.provenance` (FR-037).

**Breaking change.** The `parameters=` keyword is removed rather than kept beside
`rules=`, per FR-044. Package version `2026.08.1` is unreleased, so no published
consumer is affected; the changelog records it under **Breaking changes** anyway.
Tests needing a check against synthetic parameters build a `RulesData` through the
suite's fixture rather than passing a bare `TaskParameters`.

## Rendering

`as_text`, `as_dict`, and `as_json` gain registrations for `ValidationReport`. Their
`CheckResult` registrations gain the provenance block. `ThrowResult` rendering is
untouched, because `roll` resolves against no rules data.

## Errors

```python
class RulesDataError(CetoolsError):
    def __init__(self, message: str, problems: Sequence[ValidationProblem] = ()) -> None: ...
    problems: tuple[ValidationProblem, ...]
```

One `except CetoolsError` still catches everything the library raises. `.problems` is
empty for the runtime invariant failures `tasks.py` raises and non-empty for a failed
load.
