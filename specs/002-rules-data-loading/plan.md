# Implementation Plan: Validated Rules Data Loading

**Branch**: `002-rules-data-loading` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-rules-data-loading/spec.md`

## Summary

Replace the single-purpose `tasks.toml` reader with a validating loader for all rules
content: a schema for career files, three shipped registries that give names meaning,
the compact notation career tables are written in, an explicit override mechanism,
and a `cetools validate` command. One SRD-faithful career, the Navy, ships as the
reference that proves the schema.

Three decisions shape everything else.

**Validation is a function, not a control flow.** Nothing on the validation path
raises on a data problem. Composition produces a set of files, one implementation
turns that set into a `ValidationReport`, and the two entry points differ only in
what they do with the report: `validate_rules` returns it, `load_rules` raises when
it is not clean. That is what makes FR-021's collect-everything and FR-023's
same-check-both-ways structural rather than a matter of discipline, and it is why a
file with four mistakes costs one run instead of four.

**A file is positioned by its basename and classified by its own declaration.** Both are
now requirements rather than design inferences: FR-029 states basename positioning
directly, with layout mirroring reduced to a recommendation, and FR-001a requires each
file to declare its kind. That pairing is what makes `cetools validate override/navy.toml`
and a real load of `override/` agree in every case, which FR-040 demands, and what lets a
house rule introduce a career (FR-032) while a replacement is still checked against the
kind it claims to replace.

**Provenance rides on the result.** `CheckResult` gains a `provenance` field and
`check` takes `rules=` in place of `parameters=`. `cetools roll` resolves against no
rules data and is untouched, so its three golden files stay byte-for-byte identical,
which is itself part of the evidence for SC-009. The fingerprint is a plain SHA-256
over the file's raw bytes so that anyone handed a result can reproduce it with
`shasum -a 256`. Provenance also carries the package version (FR-033a), which with the
seed is the whole reproduction key; committed goldens and fixtures hold that version as a
placeholder so a release rewrites none of them.

## Technical Context

**Language/Version**: Python 3.13+, unchanged. The open-ended `requires-python` and
the guard that keeps the CI matrix honest are inherited from `001-dice-task-engine`
and are not revisited here.

**Primary Dependencies**: no new runtime dependency. Typer remains the only one.
Standard library additions used by this feature: `hashlib` (already used by
`seeds.py`), `enum.StrEnum`, `dataclasses`, `tomllib`, `importlib.resources`, `re`.

**Storage**: five packaged read-only data files under `src/cetools/data/`, up from
one. Plus, at the caller's explicit request only, files under an override location
the caller names. No filesystem search path, no configuration directory, no
environment variable (FR-027).

**Testing**: pytest, Typer's `CliRunner`, committed golden files, a frozen copy of
the previous feature's golden files under `tests/golden/pre-loader/` that is never
regenerated, and a new audit-hook guard that proves no location outside the installed
package is opened. Hypothesis is available and applies to the notation parser
(round-tripping a rendered entry through `parse_entry`).

**Target Platform**: cross-platform CLI and importable library, unchanged.

**Project Type**: single library with a thin CLI, unchanged.

**Performance Goals**: none that constrain design. A packaged load reads five small
TOML files once per process and is cached. The full career set that a later feature
authors is on the order of two dozen files, still trivial. An override load is not
cached, because the authoring loop edits a file and reloads in the same process.

**Constraints**: three, and each is a hard edge rather than a preference.

- **Whole-set, whole-file, all-or-nothing.** The entire data set validates on every
  load regardless of what a run would use (FR-024), a valid subset is never exposed
  (FR-025), and an override replaces a file entirely rather than merging into it
  (FR-030). All three exist to keep a seed's meaning from depending on which files
  happened to parse.
- **Nothing implicit is ever read.** SC-007 requires this proved automatically, not
  asserted, which is what the audit-hook guard is for.
- **FR-045 permits exactly one difference in rendered output.** The provenance block,
  and nothing else. The regeneration of the reference outputs is itself checked
  against the frozen pre-loader copies, so a changed number cannot be absorbed into a
  regeneration.

**Scale/Scope**: 61 functional requirements, 16 success criteria, after the requirements
checklist review added ten requirements and two criteria and amended fifteen more. Four
new library modules plus a rewritten `rules.py`; four new data files plus two header lines
added to `tasks.toml`; one new command and one new option on an existing command. On the
order of 800 lines of implementation and a substantially larger test suite. The review
added no new module and no new dependency: the added requirements state rules the design
had already settled, plus three behaviors it had not (the package version in provenance,
ignored files named in the report, and the notice-chain check deriving its coverage).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| **I. Library-First** | All game logic in importable modules; CLI contains none | **PASS** - loading, composition, validation, notation parsing, and provenance all live in the library. `cli.py` gains argument parsing and two exit-code decisions and nothing else. Rendering of the validation report is a `render.py` registration, not CLI code. |
| **II. CLI Text I/O** | Every capability reachable from CLI; both output modes; stdout/stderr split; meaningful exit codes | **PASS** - `cetools validate` covers the new capability, `--rules-data` covers overrides on `check`; both modes on both; validation problems are the requested report and go to stdout, usage errors to stderr; exit 0/1/2, no new code introduced. |
| **III. Test-First** | Tests written first, confirmed failing, then implementation | **PASS in the work, NOT in the committed evidence**; see Recorded Deviation below. SC-012 asks for expected values landing in a change that precedes the implementing change, and the branch history does not carry that separation. |
| **IV. Seed-Reproducible** | Seed accepted everywhere; same seed and version give same output; no unseeded randomness | **PASS**, and strengthened. Overrides break "seed plus package version determines output", and provenance is what converts that silent break into a visible one (User Story 4). Nothing in this feature draws randomness. FR-045 and SC-009 pin that resolution is unchanged. |
| **V. Data-Driven Rules** | SRD content in data files, none hard-coded | **PASS**, and this feature is largely the discharge of the principle. Characteristics are data rather than parser constants (FR-012), the registries are what make a misspelling detectable, and SC-011 requires a demonstrated behavior change from a data edit for a throw, a table entry, a rank bonus, and a registry entry. |
| **VI. Simplicity** | YAGNI; stdlib preferred; runtime dependencies justified | **PASS with two recorded tensions**; see Complexity Tracking. |
| **Licensing & Distribution** | OGC files designated; every distribution bundles the OGL text and Section 15 chain; PI strings absent from OGC data; compatibility claims carry attribution | **PASS with required work**; see below. |

## Recorded Deviation: the test-first evidence Principle III and SC-012 ask for

Stated here rather than left for a reviewer to discover, because the whole point of
SC-012 is that test-first be evidenced instead of asserted, and on this branch it is
asserted.

Every test in this feature was in fact written before the code it covers and observed
failing. What is missing is the *committed* separation. `22bcbb2` lands `notation.py`,
`registries.py`, `careers.py` and `provenance.py` together with `test_notation.py`,
`test_registries.py`, `test_careers.py` and `test_provenance.py`; `8ffc9a0`, `a7ed647`
and `11cb32b` do the same for `rules.py`, `tasks.py`, `render.py`, `cli.py` and the data
files. No test commit precedes its implementing commit, so the history proves nothing
about the order the work was done in, which is exactly what SC-012 asked the history to
prove.

Splitting each of those commits in two was considered and declined: reconstructing the
red state after the fact produces a history that asserts test-first just as much as the
present one does, at the cost of rewriting a branch. The honest record is this note.

**What this costs, concretely**: SC-012 is not satisfied on this branch. Treat it as
open. The remedy is procedural and belongs to the next feature: commit the test file,
run it, commit the failure's absence of a fix, then implement. Nothing about the code in
this feature depends on it, and the suite is unaffected either way.

**Licensing work this feature owes.** Four new Open Game Content files ship. Each
needs its designation comment and neither Product Identity string (FR-046), verified
against the built wheel and sdist rather than the working tree (SC-014), which means
the existing packaging guard must iterate over every `.toml` under `cetools/data/`
instead of naming `tasks.toml`. Separately, the Section 15 chain in `LICENSE-OGL.txt`
ends with this project's own game-data copyright line, which currently names
`src/cetools/data/tasks.toml` specifically. That line must be widened to cover the
whole data directory, and `tests/conftest.py`'s `SECTION_15_NOTICES` literal, which
pins the chain verbatim, must be updated in the same change.

This was recorded here as a thing easy to miss, and the requirements checklist found it
was worse than that: nothing in the spec required it, and the existing guard could not
catch it, because comparing the chain against a fixed expected text passes unchanged while
the copyright line beneath it goes stale. FR-047 now requires the coverage and SC-016
requires the check to derive what must be covered from the data files actually present, so
adding a data file without widening the notice fails the suite rather than depending on a
reviewer's memory. FR-046 was also amended to say outright that it binds shipped files
only: a house rule needs no licensing header, which FR-031's "exactly the same rules" had
left arguable.

**Post-Phase-1 re-check**: still **PASS**. The Phase 1 design added no dependency and
no hard-coded rules content. The closed sets of throw names and table names are a
strictness choice, not hard-coded content: they name the schema's own slots, and the
values in every slot stay in data. Both are now stated in the spec (FR-014, FR-015)
rather than being design choices about it.

**Post-checklist re-check**: still **PASS**, and one row left Complexity Tracking. The
kind declaration each file carries was recorded there as a field beyond what the
requirements named; FR-001a now names it, so it implements a requirement rather than
exceeding one. The three behaviors the review added (the package version in provenance,
ignored files named rather than rejected, a notice check that derives its coverage) each
introduce a field or a report line and no new module, dependency, or abstraction.

## Project Structure

### Documentation (this feature)

```text
specs/002-rules-data-loading/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── data-files.md    # Every file's schema, composition, cross-file rules
│   ├── notation.md      # The compact notation grammar and contexts
│   ├── library-api.md   # Public importable surface, added and removed
│   ├── cli.md           # Command surface and text rendering
│   └── json-output.md   # Committed JSON shapes
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
src/
└── cetools/
    ├── __init__.py         # public re-exports: added and removed surface
    ├── errors.py           # + ValidationProblem; RulesDataError gains .problems
    ├── notation.py         # NEW: the compact notation, parse_entry, entry types
    ├── registries.py       # NEW: characteristic, skill, benefit registries + their file schemas
    ├── careers.py          # NEW: CareerDefinition and friends + the career file schema
    ├── provenance.py       # NEW: Provenance, FileProvenance, Disposition, fingerprint
    ├── rules.py            # REWRITTEN: discovery, composition, task-parameters schema,
    │                       #   validation driver, RulesData, ValidationReport,
    │                       #   load_rules, validate_rules
    ├── tasks.py            # CheckResult gains provenance; check takes rules= not parameters=
    ├── render.py           # + ValidationReport registrations; + provenance in CheckResult
    ├── cli.py              # + validate command; + --rules-data on check
    └── data/
        ├── __init__.py
        ├── tasks.toml              # + schema / schema-version header
        ├── registries/
        │   ├── characteristics.toml   # NEW
        │   ├── skills.toml            # NEW
        │   └── benefits.toml          # NEW
        └── careers/
            └── navy.toml              # NEW: the reference career

tests/
├── conftest.py          # + rules fixtures; SECTION_15_NOTICES updated
├── unit/                # + notation, registries, careers, rules, composition, provenance
├── contract/            # + validation payload; check payload gains provenance
├── integration/         # + validate CLI, override composition, golden files
├── guards/              # + no-outside-reads audit hook; packaging guard widened
├── property/            # + notation round-trip invariants
└── golden/
    ├── *.txt            # regenerated: check goldens gain one line, roll goldens unchanged
    └── pre-loader/      # NEW: frozen copies of the previous feature's outputs, never regenerated
```

**Structure Decision**: the flat module layout is kept. `rules.py` is rewritten
wholesale, which is exactly what the previous plan isolated it for, and the domain
types it produces live beside `dice.py` and `tasks.py` rather than inside a loader
package. Each new module owns the schema of the files it produces types for
(research R11): `careers.py` validates career files, `registries.py` validates the
three registry files, and `rules.py` keeps discovery, composition, provenance
assembly, the task-parameters schema, and dispatch. A `rules/` package with a shared
`schema.py` was considered and rejected as more structure than the code needs.

The data directory gains two subdirectories. `importlib.resources` traverses them
without `__init__.py` files, verified on this machine (research R5), so no package
scaffolding is added for its own sake.

## Implementation Notes

Guidance to carry into `/speckit-tasks` and `/speckit-implement`.

**Do this first, before touching any code**: copy `tests/golden/*.txt` verbatim into
`tests/golden/pre-loader/` and commit them. SC-009 requires comparison against the
outputs committed with the previous feature rather than regenerated ones, and the
evidence is destroyed the moment the renderer changes. This is the one task with a
hard ordering constraint outside the usual test-first rule.

**Build order** (each step's tests written and failing first, per Principle III):
`errors` (ValidationProblem) → `notation` → `registries` → `careers` → `provenance` →
`rules` (discovery, composition, task-parameters schema, driver) → data files →
`tasks` (CheckResult, check signature) → `render` → `cli` → goldens → guards →
property tests. The notation comes before the schemas that use it, and the registries
before the careers that validate against them.

**Author the reference career from the source material**, not from the illustrative
values in `contracts/data-files.md`. Those exist to show the shape. FR-018 requires
the shipped career to exercise every schema element, including a commission, a second
rank ladder, at least one rank bonus, and a characteristic-gated table, and SC-004
tests that by removing each required element in turn and expecting a specific
rejection.

**Per the project's global instruction**, consult the matching `fluent-python:*`
skills when writing the code. The ones that apply here:

- `choosing-a-data-class-builder` - frozen slotted dataclasses throughout
- `using-pattern-matching` - dispatching on notation entry types, which is where an
  `isinstance` chain would otherwise grow
- `choosing-mapping-types` - the registries and the careers mapping; read-only
  mappings, not dicts handed out by reference
- `writing-sequence-idioms` - accumulating problems without building intermediate
  lists per file
- `using-functools-and-operator` - `cache` on the packaged load, `singledispatch`
  registrations in `render.py`
- `designing-function-signatures` - keyword-only on the changed `check`
- `handling-text-encoding` - every data file read is explicitly UTF-8; the
  fingerprint hashes raw bytes and must not decode first

**Traps worth naming now**, each already resolved in the contracts or research:

- Basenames must be unique across the packaged layout or the composition key stops
  identifying a slot. Write that test early; it is one assertion and it guards the
  whole composition model.
- The fingerprint hashes bytes, not decoded text. Decoding first would make the value
  irreproducible with `shasum` and would silently normalize line endings.
- A version mismatch must suppress every other problem from that file (FR-002),
  otherwise a file written for another shape reports a cascade of key errors.
- The audit-hook guard captures import machinery reads too. Import everything before
  arming, and filter `__pycache__`.
- `load_rules` is cached only for the no-override call. The autouse fixture that
  currently clears `load_task_parameters` must be repointed, or every override test
  will see a stale packaged set.
- `Rules:` is no longer than `Total:`, so the check text block's label column width
  does not change. If it did, every line of every check golden would change and
  SC-009's "one difference" claim would be false.
- Do not delete `tests/golden/pre-loader/` when regenerating goldens.
- The package version must be a placeholder in every committed golden and JSON fixture,
  substituted at comparison time. Writing the literal makes every release rewrite every
  check golden, and each rewrite is another chance to absorb a changed number, which is
  what SC-009 exists to prevent. Assert the real value once, directly, per SC-008.
- The dot-prefixed filter runs before the extension filter, not after. A `.DS_Store` must
  disappear entirely (FR-032b); only a non-dot file with the wrong extension becomes an
  ignored entry (FR-032a). Reversing the order puts every tool artifact in the report.
- An ignored file does not fail the load and carries no fingerprint. It is a separate
  tuple on `Provenance`, not a third `Disposition` member, so `is_packaged` stays an
  emptiness check and `fingerprint` stays non-optional.
- An override containing only ignored files still reports `packaged`, because nothing took
  effect, and still lists them. That combination is the whole point of FR-032a, so it needs
  its own test rather than falling out of the packaged case.

**Deliberately not built**, so review does not read these as gaps: per-key merging,
any implicitly searched location, warnings-instead-of-errors, partial or lazy
loading, benefit item semantics, the remaining careers, house-rule onboarding
documentation, schema migration, and grouping or bounding a cascade of related problems.
Each is recorded with its reason in the spec's Out of Scope. Research R13 adds three more
at implementation grain: no table length constraints, no override caching, and no schema
migration machinery behind the version field.

## Complexity Tracking

One row remains. It is not a constitutional violation; it is a place where this feature
is deliberately less simple than the minimum, and Principle VI says such a choice must
survive review rather than pass unnoticed.

| Choice | Why needed | Simpler alternative rejected because |
|---|---|---|
| `schema-version` in every file | Recorded in the spec's Assumptions as a conscious departure: overrides mean user-authored files outlive package upgrades, CalVer carries no compatibility signal, and by the time two dozen career files exist outside anyone's control the schema is fixed. One line per file buys an upgrade story that cannot be recovered afterwards. | Omitting the field entirely, rejected because a user file written against an old shape would fail as a scatter of key errors with no way to say what actually went wrong. |

**Removed after the requirements checklist review**: the `schema` kind declaration. It sat
here because research R2 showed FR-032 and FR-040a together forced a field no requirement
asked for. The review treated that as a gap in the requirements rather than a liberty taken
by the design, and FR-001a now requires the declaration outright. Worth naming the
circularity plainly: the spec was amended to require what the design had found it needed.
That is legitimate here because the need was demonstrable from requirements that already
existed, and the alternative was to leave a load-bearing field permanently unaccounted for.
It would not be legitimate as a general habit.

No new runtime dependency is introduced, so the dependency clause of Principle VI is
not engaged.
