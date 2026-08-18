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
    CharacteristicRegistry, SkillRegistry, BenefitRegistry, SkillResolution,
    # notation
    parse_entry, EntryContext, NotationProblem, SkillReference, SkillGrant,
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

`override` may name a directory or a single file (FR-028, FR-029). A path that does not
exist raises `RulesDataError` naming it. `None` opens nothing outside the installed
package (FR-027).

A file in an override that is not a `.toml` file does not raise: its path within the
override lands in `provenance.ignored` and the load proceeds (FR-032a). The path rather
than the basename, so two `notes.md` in different directories are both named. A file or
directory *found by walking an override directory* whose name begins with a dot is
passed over without appearing anywhere (FR-032b), so a `.DS_Store` beside a house rule
neither fails the load nor clutters the report, and pointing the loader at a git
checkout reports nothing from `.git/`. The carve-out does not apply to `override` itself:
a dot-prefixed path the caller names composes by its basename if it is a `.toml` file,
or is ignored and named in `provenance.ignored` otherwise — the same treatment any other
named path gets, because a path typed on the command line was written by the author.

A directory within the override that cannot be listed is a collected `ValidationProblem`
naming it, not a subtree passed over in silence; symlinked directories are followed.

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
    version: str                  # installed package version (FR-033a)
    files: tuple[FileProvenance, ...]     # took effect; sorted by file
    ignored: tuple[str, ...]              # not rules data (FR-032a); paths within the
                                          # override, sorted
    @property
    def is_packaged(self) -> bool: ...    # not self.files

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
def parse_entry(text: str, context: EntryContext) -> Entry | NotationProblem: ...

@dataclass(frozen=True, slots=True)
class NotationProblem:
    found: str
    expected: str
```

`EntryContext` is a plain `Enum` of `auto()` members with `SKILL_TABLE`,
`BENEFIT_TABLE`, and `GATE`. `Entry` is the union of the five notation types.

`parse_entry` **returns** a `NotationProblem` for a malformed entry or a form the
context does not admit; it raises nothing. That is the "validation is a function,
not a control flow" decision in plan.md's Summary applied one level down: the
caller, which knows the field the text came from, turns the problem into a located
`ValidationProblem`, and a parser that raised would make collecting every problem
in one run (FR-021) a matter of discipline instead of structure. `NotationProblem`
carries no file or location for the same reason: the parser does not know them.

`EntryContext` is deliberately not a `StrEnum`, unlike `Disposition`. Nothing reads
or writes an `EntryContext` value as text: it is a dict key and an identity
comparison inside the library, never rendered, never serialized, and never read
from a data file. `Disposition` earns its `StrEnum` base because `"replaced"` and
`"added"` are the strings both output modes emit. Adding string behavior to
`EntryContext` would be surface with no caller, which Principle VI rejects.
`SkillResolution` is a plain `Enum` for the same reason.

Registry validation is separate from parsing: `parse_entry` produces a
`SkillReference` for `Vac Suit` and the registry is what rejects it, so a caller
can parse an entry without a data set in hand. `SkillRegistry.resolve` returns a
`SkillResolution` — `VALID`, `UNRECOGNIZED_SKILL`, `SPECIALTY_NOT_ALLOWED`, or
`UNRECOGNIZED_SPECIALTY` (FR-007) — rather than raising, on the same reasoning.

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

### Package-internal seam: `render._problem_line`

```python
def _problem_line(problem: ValidationProblem) -> str: ...
```

`cli.py` imports this to print the problems of a failed `check` load. It is
package-internal — the leading underscore is the convention, as it is for
`tasks._check_dice`, and callers outside the package must not use it — but it is
named here because it crosses a module boundary and because a seam no contract
records is a seam a later change can break without noticing.

It exists so that the two surfaces which render a problem as one line, `validate`'s
report and `check`'s failure output, cannot disagree about the form. Duplicating the
formatting in `cli.py` was the alternative, and contracts/cli.md fixes that form for
both, so one of the two copies would eventually have drifted from it. A public
spelling was considered and rejected: nothing outside the package renders a single
problem, and `__all__` is the contract, so adding a name with no caller is the
speculative surface Principle VI rejects.

## Errors

```python
class RulesDataError(CetoolsError):
    def __init__(self, message: str, problems: Sequence[ValidationProblem] = ()) -> None: ...
    problems: tuple[ValidationProblem, ...]
```

One `except CetoolsError` still catches everything the library raises. `.problems` is
empty for the runtime invariant failures `tasks.py` raises and non-empty for a failed
load.
