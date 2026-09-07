# Research: Validation Vocabulary

Phase 0. Every open question from the spec, resolved. Nothing here is marked
NEEDS CLARIFICATION; the three that would have been were settled in
`/speckit-clarify` and are recorded in the spec's Clarifications section.

Most of these decisions were reached in a design interview before the spec was
written, and the spec deliberately carries the obligation without the symbol
names. This document carries the names and the reasoning.

---

## R1. Where the vocabulary lives

**Decision**: a new module, `src/cetools/schema.py`.

**Rationale**: the checks need a home that all five parsers can reach and that
nothing outside the package depends on. `errors.py` is the obvious candidate
and is ruled out by the import graph:

- `require_roll` must call `tasks._check_dice` to decide whether notation is
  acceptable.
- `tasks.py:8` already reads
  `from cetools.errors import DiceError, RulesDataError, TaskError`.
- Putting `require_roll` in `errors.py` would therefore close a cycle
  `errors → tasks → errors`.

A separate module also keeps `errors.py` to what it is: the exception
hierarchy plus the two vocabulary pieces (`ValidationProblem`, `type_name`) the
checks build on. The new module sits one layer above it.

```text
errors.py  ──┐
             ├──> schema.py ──> rules.py, careers.py, registries.py,
tasks.py   ──┘                  names.py, chargen.py
```

**Alternatives considered**:

- *Fold into `errors.py`.* Circular import, as above.
- *A `cetools/schema/` package.* Seven functions in roughly 200 lines do not
  need a package. Principle VI.
- *Leave the checks where they are and only merge the wording.* Fixes the
  symptom named in User Story 1 and leaves the cause named in User Story 2:
  the next data-file kind adds a seventeenth copy.

## R2. What the interface looks like

**Decision**: seven module-level functions, signatures unchanged from the
private helpers they replace. Full specification in
[`contracts/schema-vocabulary.md`](contracts/schema-vocabulary.md).

**Rationale**: the existing signatures already work at seventy-three call
sites. Keeping them makes the structural commit a rename plus an import at
every site, which is the property that lets the existing suite serve as the
proof that nothing changed. Redesigning the signature at the same time would
forfeit that.

**Alternatives considered**:

- *A `Checker` class holding `file` and `problems`.* Would remove two
  arguments from every call, and would rewrite all seventy-three sites in the
  same commit that moves them, so a mistake in either would be invisible. It is
  also most of the path-cursor deepening that FR-020 defers.
- *A fuller declarative schema, generalizing `_CHARGEN_GROUPS` across all five
  modules.* Rejected in the design interview and recorded in FR-017 and FR-020.
  Only `chargen.py` has enough flat scalar fields (~35 across 12 groups) for a
  table to pay for itself; `careers.py` and `registries.py` parse nested,
  irregular structures where a table would need escape hatches for most fields.

## R3. Why `require_dict` may read `None` as "missing"

**Decision**: `require_dict` takes a value rather than a container and key, and
reports `found="missing"` when that value is `None`.

**Rationale**: two things have to hold, and both do.

First, the value-taking shape is what the call sites want. All five existing
`careers._require_dict` sites pass a loop element or a parameter already in
hand; `registries.py:231` and `chargen.py:1207` do the same. Forcing a
container and key on them would mean re-looking-up something they already have.

Second, reading `None` as "missing" is sound rather than a guess, because a
TOML file has no way to write an empty value. A key is either present carrying
something or absent entirely, so for any container and key:

```text
container.get(key) is None   ⟺   key not in container
```

This is what lets one value-taking check preserve the "missing" wording at the
three sites that distinguish absence today, two of which test the value and one
of which tests membership:

| Site | Today |
|---|---|
| `rules.py:175` | `"missing" if task is None else type_name(task)` |
| `registries.py:284` | `"missing" if data is None else type_name(data)` |
| `chargen.py:1264` | `"missing" if group not in data else type_name(table)` |

A naive merge onto `careers._require_dict`, which has no absent branch, would
have downgraded all three to `found="NoneType"`—a silently worse message at
three sites, and exactly the kind of drift this feature exists to stop.

The assumption is recorded in the spec's Assumptions and as an Edge Case.

**Alternatives considered**:

- *Container-and-key, like the other six.* Would have to be `require_dict(
  container, key, …)` with the value re-fetched, and the five careers sites
  have no container to name.
- *A separate `require_dict_value` for the in-hand case.* Two functions where
  one suffices, and the seven-check inventory that FR-014a's guard enforces
  gets an eighth entry for no behavioral gain.

## R4. Naming: bare, not underscore-prefixed

**Decision**: `require_int`, not `_require_int`. Absent from
`cetools/__init__.py`'s `__all__`.

**Rationale**: the package's own precedent. `parse_career`,
`parse_characteristics`, `parse_skills`, `parse_benefits`, `parse_given_names`,
`parse_surnames`, and `parse_task_parameters` are all bare-named, all
cross-module, and none appears in `__all__` (`__init__.py:65-90`). Package-
internal is expressed by absence from `__all__`, not by an underscore.

The underscore carries a stronger, narrower promise here:
`specs/001-dice-task-engine/contracts/library-api.md:124-125` reserves it for
two specific symbols. Extending it to seven functions imported by five modules
would reproduce `_check_dice`'s documented awkwardness—an underscore-prefixed
name imported across module boundaries, which reads as a violation at every
site—thirty-five importer-function pairs over.

FR-016's "package-internal" is satisfied by staying out of `__all__`.

## R5. The order of the two commits

**Decision**: one behavioral commit carrying both wording changes and their
tests and one changelog entry, then the structural commits that remove the
duplicates. Nothing mixed.

**Rationale**: Tidy First, and a hard dependency. The three `require_int`
variants and the two string checks cannot be merged into one definition until
they agree on what to say; choosing the wording *is* the behavioral change. So
the ordering is not a convention being observed, it is the only order that
works.

The changelog entry belongs to the behavioral commit alone. The removals are
invisible to a user of the library, so claiming an entry for them would put
noise in a document that exists to tell a reader what changed for them
(FR-019).

**Wording chosen, and why**: `"a positive integer"` over `"an integer >= 1"`,
and `"a non-empty string"` over `"a string"` for an absent required text field.
Both follow the same rule: where two phrasings compete, the surviving one is
the more accurate, and the reports elsewhere are written in English rather than
notation—`"a non-empty string"`, `"an empty table"`, `"at least one entry"`.
The second change additionally removes a self-contradiction, where one rule was
described one way when the key was missing and another when the value was
present and empty.

Neither is pinned by a test, a golden file, or a documented example; see
`data-model.md`, *Inventory: behavioral blast radius*, for the evidence.

**Alternatives considered**:

- *Structural first, behavioral second.* Impossible: there is no single
  definition to extract until the wording is settled.
- *One commit for everything.* Violates Tidy First and the project's commit
  discipline, and would leave a wording regression and a mechanical rename
  indistinguishable in the diff.
- *Keep `"an integer >= 1"`, changing `careers.py` instead.* Fewer fields
  change (one instead of six), but it picks the less accurate phrasing to
  minimize churn, which the spec's Assumptions reject explicitly.

## R6. How the duplicates were compared

**Decision**: mechanically, with an AST comparison, not by reading.

**Method**: a script parsed all five modules, located each of the sixteen
definitions, stripped docstrings, and hashed each on its signature plus its
normalized body. Groups that hash alike are identical.

**Finding**: every group is identical apart from documentation except two.

- `require_int`, three variants (`careers.py:169`, `chargen.py:80`,
  `rules.py:269`).
- `require_string` versus `require_nonempty_string`, differing on the
  absent-key case alone.

**Why it mattered**: an earlier claim, made by inspection and written into the
first draft of the spec, was that `registries._require_nonempty_string` and
`_require_string` produced identical output in all four cases, making their
merge a zero-behavior-change move. Running the two over the same ten inputs
disproved it: they diverge on the missing key. That correction is what produced
FR-009a and the rewritten FR-013, which now requires any further divergence
found during the work to be raised rather than quietly rewritten.

The general lesson is recorded in the spec's Assumptions: the comparison is
mechanical because inspection got it wrong once already.

## R7. Testing approach

**Decision**: `tests/unit/test_schema.py`, written first and failing, plus the
existing suite unchanged as the regression net, plus one new guard.

**Rationale**: Principle III is non-negotiable, and the two kinds of test here
do different jobs.

- **`tests/unit/test_schema.py`** is the Red step for the vocabulary itself:
  roughly 25-30 direct cases covering each check's absent-key, wrong-type,
  empty-string, `minimum` boundary, and accepted paths, plus
  `unrecognized_key_problems`' sort order and its `expected` list. It is
  written before `schema.py` exists and must fail on import (FR-018). Its cases
  come from the tables in `contracts/schema-vocabulary.md`, which are written
  as exact strings for that purpose.
- **The existing suite**: `test_careers.py`, `test_chargen.py`,
  `test_registries.py`, `test_names.py`, `test_rules.py`, and the forty-three
  tests in `tests/integration/test_validation_categories.py`—is the proof
  that the extraction changed nothing. It must pass unchanged apart from the
  wording assertions added in the behavioral commit (SC-003, SC-004).

The order within the behavioral commit is the same discipline one level down:
assert the new wording, watch it fail, change the two source lines, watch it
pass.

## R8. The guard against regrowth

**Decision**: `tests/guards/test_no_duplicate_checks.py`, joining the ten guards
already in that directory, reading the source of `src/cetools/*.py` with `ast`
and failing if any of the seven checks is defined outside `schema.py`.

**Rationale**: the duplication this feature removes accumulated one module at a
time, and every single addition was defensible in isolation—the helper was
five lines, the neighboring module already had one, and copying it was faster
than finding a home for it. A rule that depends on nobody ever making that
locally reasonable choice again will not hold. FR-014a and SC-002 both require
an enforcer rather than a note.

The project already treats this as a category. CONTRIBUTING.md's test-layout
table names `tests/guards/` as the home for "whole-repository invariants
nothing else can check", and ten guards live there today.

**Template**: `tests/guards/test_no_locale.py`, which enforces "no module under
`src/` imports `locale`". It is the closest existing guard in both rule shape
and mechanism, and the new one follows it directly:

- `ast.parse(path.read_text(...), filename=str(path))`, walking the tree.
- `sorted((repo_root / "src").rglob("*.py"))` for the file set.
- The `repo_root` fixture from `tests/conftest.py`
  (`Path(__file__).resolve().parent.parent`) rather than a locally re-derived
  `parents[2]`. Several guards re-derive it; `test_no_locale.py` and
  `test_data_layout.py` use the fixture, and the fixture exists for this.

**Shape**: collect every top-level `ast.FunctionDef` whose name matches one of
the seven checks, with or without a leading underscore, and assert that the
only file defining any of them is `schema.py`.

`ast` rather than a regex over source text, for two reasons. A regex would
match the name in a docstring, a comment, or a call site, so it could not tell
a definition from a mention. And "defined at the top level of a module" is not
expressible as a regex at all, but falls straight out of walking the tree.

**Self-test, per repository convention**: every guard module here carries a
test proving its detector is not vacuous—`test_the_guard_can_fail`,
`test_the_guard_has_something_to_check`, `test_the_coverage_check_can_fail`.
The pattern in `test_no_locale.py` is to plant an offending file under `src/`,
assert the detector catches it, and `unlink()` it. The new guard carries the
same, since a guard that would pass against a reintroduced duplicate is worse
than none: it would report the rule as held while the duplication grew back.

**Known limit, accepted**: the guard catches a *named* definition reappearing.
It does not catch a fresh hand-inlined equivalent check—precisely the shape
of the eleven inline sites this feature converts. Catching that would mean
recognizing a check by its structure rather than its name, which is a
substantially larger piece of machinery aimed at a much rarer mistake: the
copies that actually accumulated here were copies of a *named* helper, five
times over. Recorded as a limit rather than solved (Principle VI).

**Alternatives considered**:

- *A comment in each module.* Is what the codebase effectively had, in
  `type_name`'s docstring, and it did not hold.
- *A lint rule.* `flake8` is optional in this project and gates nothing
  (`pyproject.toml`, `[tool.mypy]` comment and CONTRIBUTING.md's Style and
  tooling section). A rule that does not run is not a guard.
- *Structural detection of inline duplicates.* See the known limit above.
