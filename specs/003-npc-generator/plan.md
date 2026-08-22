# Implementation Plan: NPC Generator

**Branch**: `003-npc-generator` | **Date**: 2026-08-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-npc-generator/spec.md`

## Summary

Turn a seed into a finished character by walking the source material's lifepath end to
end, and render that character three ways. The engine reads every rule from data through
the loader the previous feature built, the data set grows in three directions (a career
schema at version 2, a directory of per-kind universal chargen tables, two extended
registries, and the project's first non-OGC data files), and `cetools npc` is a thin
consumer of `generate_character`.

Six decisions shape everything else.

**The walk is one fixed-length path per seed.** Nothing is discarded and re-rolled
(FR-023), nothing dies (FR-022), and every failure resolves into a consequence the source
material already prints: qualification failure routes to the draft or to Drifter, survival
failure resolves on the Survival Mishaps table, an aging crisis becomes a debt. That is
what makes reproducibility a property of the design rather than a tendency of the output,
and it is why there is no death branch to build or test.

**Naming draws from a stream of its own.** FR-047b requires that supplying a name change
nothing else about the character a seed produces. Rolling the name from the walk's roller
would shift every draw after it, so the name comes from a roller derived from the walk
seed and the walk's roller never sees it. Supplying a name skips the draw entirely and the
walk is bit-for-bit unaffected.

**A batch is one seed and a derivation, not one stream.** Character *i* runs on
`character_seed(master, i)`, which is `master` itself at position 0 and a blake2b
derivation of `(master, i)` above it. FR-057's prefix property then holds by construction
rather than by the accident of stream order, FR-048a's batch of one is byte-identical to
the single character of that seed, and FR-050a's per-character derived seed regenerates
that one person when quoted back to `--seed`. See research R2 for why position 0 is the
master itself.

**Rendering goes through the existing dispatchers.** `as_text(character)` is the Universal
Character Format, `as_text(character, full=True)` is the fuller sheet, and `as_dict` /
`as_json` carry everything unconditionally. `as_text` grows a keyword-only `full` flag that
the registrations which have no fuller form reject rather than ignore, on the same
reasoning the dispatch fallback already raises: a rendering that silently gives less than
was asked for is the miss this design exists to detect.

**Machine-readable output has one shape whatever the count.** Every run emits a
`CharacterBatch`: master seed, package version, and provenance at the top level, the
characters as a list, a list of one when one was asked for (FR-050a). A consumer writes one
code path. This is what the spec's 2026-08-21 clarification settled, and it is what ships.

**The licensing checks stop being able to read "data file" as "OGC file".** Until this
feature the two named the same set. The name tables split them, and the existing guards
assert `"Open Game Content" in text` of every `.toml` under the data directory, so they
would fail on the first name table and, relaxed to pass it, would stop proving the
designation for the files that need it (FR-042a, SC-015a). Every shipped data file gains a
designation line naming which of the two it is, and the guards assert exactly one, neither
being a failure and both being a failure. See research R9.

## Technical Context

**Language/Version**: Python 3.13+, unchanged.

**Primary Dependencies**: no new runtime dependency. Typer remains the only one. Standard
library reached for here: `hashlib` (the seed derivation, through the fold `seeds.py`
already has), `dataclasses`, `tomllib`, `importlib.resources`, `functools.singledispatch`.

**Storage**: 26 packaged read-only data files under `src/cetools/data/`, up from 5. Six
universal chargen tables, eight name tables, eight careers, four registries and task
parameters. Plus, at the caller's explicit request only, an override location. No search
path, no configuration directory, no environment variable, unchanged from
`002-rules-data-loading` FR-027. (Qualified by feature, because FR-027 of *this* spec is the
material-benefit rule and an unqualified reference lands a reader on the wrong requirement.)

**Testing**: pytest, Typer's `CliRunner`, committed golden files compared as **bytes**
(research R7), the JSON contract suite, Hypothesis, the audit-hook guard, and two sampled
populations: one thousand seeds for the always-living and consistency audits (SC-003 to
SC-008) and ten thousand rolled names for the regional weighting check (SC-019). Both carry
a new `slow` marker so the inner development loop can run `-m "not slow"`, which is what
the project's own test-first discipline asks for after every step.

**Target Platform**: cross-platform CLI and importable library, unchanged.

**Project Type**: single library with a thin CLI, unchanged.

**Performance Goals**: none that constrain design, with one measured floor. SC-003's
thousand-seed sample and SC-019's ten-thousand-name sample must complete inside a test
suite people actually run. A walk is a few hundred draws over an already-loaded data set,
so the sample is expected in single-digit seconds; if it is not, the sample is marked
`slow` and stays in CI rather than being shrunk, because SC-003 fixes the size and forbids
excluding a seed.

**Constraints**:

- **The always-living guarantee is structural.** There is no death path to disable and no
  lethal mode to select (FR-022). A generator that could fail for some seed would fail
  SC-003, which admits no exclusions.
- **No rules constant in engine code** (FR-038, SC-013). The term cap, the years a term
  costs, the ages, the qualification penalty, the benefit-roll thresholds, and the cash
  modifier all live in `chargen-parameters.toml`, and SC-013 demonstrates a behavior change
  from editing five separate files.
- **Locale cannot reach the output** (FR-046, SC-012). The skill ordering is
  `(casefold, codepoint)` and nothing in `src/` imports `locale`, which a guard asserts
  directly because the subprocess locale test can only ever be best-effort (research R8).
- **SC-014 permits no change to any task check result.** The characteristic modifier bands
  move file, and the committed check goldens must not be regenerated in this feature. They
  are the previous feature's evidence, and regenerating them is how a changed number gets
  absorbed.

**Scale/Scope**: FR-001 through FR-058 with lettered insertions, 89 numbered functional
requirements after the readiness review of 2026-08-21 added twelve, 22 success criteria
(SC-001 through SC-020, plus the lettered SC-015a and SC-015b), four
user stories. Four new
library modules, five existing modules changed, three schema versions raised, 21 new data
files. On the order of 1,600 lines of implementation and a substantially larger test suite
than the code. The largest single risk is not the engine but the data: 21 files, each of
which must carry the right designation, keep its basename unique tree-wide, and resolve
every name it uses against a registry.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| **I. Library-First** | All game logic in importable modules; CLI contains none | **PASS**. The walk, the character, the name roll, the seed derivation, and all three renderings live in the library. `cli.py` gains option parsing, two usage-error checks, a stream split, and an exit code. SC-017 requires every capability exercised by a test that never invokes the command line. |
| **II. CLI Text I/O** | Every capability reachable from CLI; both output modes; stdout/stderr split; meaningful exit codes | **PASS**, and this feature sharpens the split rather than merely honoring it. FR-051 puts the seed, version, and provenance on stderr in text mode so a redirected stdout is exactly a character sheet; in JSON mode they sit in the document and stderr is silent, so the stream is not split (spec Assumptions). Exit 0/1/2, no new code. |
| **III. Test-First** | Tests written first, confirmed failing, then implementation | **PASS, and this time in the committed evidence.** The previous feature recorded a deviation here: the work was test-first but the history did not show it. SC-016 requires expected values committed in a change that precedes the implementing change. The build order below is written as test-commit-then-implement pairs for exactly this reason, and it is the one procedural debt this feature is paying off. |
| **IV. Seed-Reproducible** | Seed accepted everywhere; same seed and version give same output; no unseeded randomness | **PASS**, and it is most of what this feature is. FR-056 forbids the clock, the environment, the locale, and unordered-collection traversal order. Three separate guards apply: the existing module-`random` guard (which `generate_character` must be added to), the new no-`locale` guard, and SC-012's cross-locale comparison. |
| **V. Data-Driven Rules** | SRD content in data files, none hard-coded | **PASS**, and FR-038 states the obligation as an enumerated list rather than a principle, which is what makes SC-013 able to fail. The one thing engine code knows is the *shape* of the walk; every number in it is read. |
| **VI. Simplicity** | YAGNI; stdlib preferred; runtime dependencies justified | **PASS with three recorded tensions**; see Complexity Tracking. |
| **Licensing & Distribution** | OGC files designated; distributions bundle the OGL text and Section 15 chain; PI strings absent from OGC data; compatibility claims carry attribution | **PASS with required work**, and the required work is larger than it looks; see below. |

**Licensing work this feature owes.** Twenty-one new data files ship, and for the first
time they are not all Open Game Content. Concretely:

1. Thirteen new OGC files (six chargen tables, seven careers) each carry the existing
   designation line and neither Product Identity string.
2. Eight name tables carry a **new** GPL-3.0 designation line, must not carry the OGC
   designation, and must not be claimed by the Section 15 game-data notice.
3. The Section 15 game-data notice in `LICENSE-OGL.txt`, and the `SECTION_15_NOTICES`
   literal in `tests/conftest.py` that pins it verbatim, must be narrowed from "every
   `.toml` file under `(src/cetools/data/)`" to language that excludes the name tables
   while still deriving machine-readably. The `_NOTICE_PATH` and `_NOTICE_SUFFIX` regexes
   in `conftest.py` parse the notice's parentheses and its "every `.toml` file" phrase, so
   the new wording has to keep a parseable shape. This is the sharpest edge in the
   feature: get it wrong and either a name table travels under a notice that does not
   cover it, or a career table travels under no notice at all. Research R9 settles the
   wording and the parse.
4. `_assert_shipped_rules_data` in `tests/guards/test_packaging.py`, which today asserts
   `"Open Game Content" in text` of every `.toml` in the wheel and the sdist, becomes an
   exactly-one-of-two check (FR-042a).
5. SC-015a requires the checks to be demonstrably fail-able: adding a file of each
   designation in turn, to a copy of the package, must break the suite. The existing
   `test_the_coverage_check_sees_a_designated_file_the_old_scan_missed` is the pattern to
   extend, and it already writes and unlinks real files.
6. `README.md`'s licensing section says every `.toml` under `src/cetools/data/` is OGC.
   That sentence becomes false the moment the first name table lands and must change in
   the same commit; `CONTRIBUTING.md`'s "Licensing, which is not optional" section says the
   same thing twice and must change with it.
7. **All six of the above land before the first name table, not after it.** Items 3, 4, and 5
   change checks that the name tables would otherwise break on arrival, and every one of them
   passes against the data set as it stands with no name table in it. This is the ordering
   `tasks.md` encodes as Phase 2H before Phase 2I, and it is what keeps the suite green
   through the sharpest edge in the feature rather than through none of it.

**Post-Phase-1 re-check**: still **PASS**. The Phase 1 design added no runtime dependency
and no hard-coded rules content. Four new modules is the largest structural addition and is
recorded in Complexity Tracking rather than passing unnoticed.

## Project Structure

### Documentation (this feature)

```text
specs/003-npc-generator/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── data-files.md    # The new and changed file schemas, composition, cross-file rules
│   ├── library-api.md   # Public importable surface, added and changed
│   ├── cli.md           # The npc command and both text renderings
│   └── json-output.md   # The committed npc document shape
├── checklists/
│   └── requirements.md  # Written by /speckit-specify
└── tasks.md             # Phase 2 output (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
src/
└── cetools/
    ├── __init__.py         # + the new public surface
    ├── errors.py           # unchanged: no new error type is needed (research R10)
    ├── seeds.py            # + derive_seed
    ├── notation.py         # unchanged
    ├── registries.py       # + Band, modifier bands, pseudo-hex, characteristic classes
    ├── careers.py          # career schema v2: promotion optional, specialist rename,
    │                       #   advanced-education required, medical tier, career flags
    ├── chargen.py          # NEW: the six universal chargen table kinds and their schemas
    ├── names.py            # NEW: the two name table kinds, their schemas, and the name roll
    ├── character.py        # NEW: Character, CareerService, CharacterSkill, HistoryStep,
    │                       #   StepThrow, StepEffect, CharacterBatch
    ├── generator.py        # NEW: generate_character, generate_batch, the walk
    ├── provenance.py       # unchanged
    ├── rules.py            # + eleven singleton kinds and one new repeatable kind,
    │                       #   table-driven dispatch, the draft-resolves cross-file rule
    ├── tasks.py            # characteristic bands leave TaskParameters
    ├── render.py           # + Character and CharacterBatch registrations; as_text gains full=
    ├── cli.py              # + npc command
    └── data/
        ├── __init__.py
        ├── tasks.toml                      # v2: characteristic-dms removed
        ├── registries/
        │   ├── characteristics.toml        # v2: + modifier bands, + pseudo-hex
        │   ├── skills.toml                 # + background/homeworld skills, + cascade specialties
        │   └── benefits.toml               # + items the seven new careers name
        ├── chargen/                        # NEW directory, one kind per file (FR-037)
        │   ├── draft.toml
        │   ├── aging.toml
        │   ├── mishaps.toml
        │   ├── background-skills.toml
        │   ├── medical-tiers.toml
        │   └── chargen-parameters.toml
        ├── names/                          # NEW directory, GPL-3.0, not OGC (FR-042)
        │   ├── given-names.toml
        │   ├── surnames-africa.toml
        │   ├── surnames-asia.toml
        │   ├── surnames-central-america.toml
        │   ├── surnames-europe.toml
        │   ├── surnames-indigenous.toml
        │   ├── surnames-north-america.toml
        │   └── surnames-south-america.toml
        └── careers/                        # eight careers (FR-032)
            ├── navy.toml                   # brought to schema v2
            └── (seven more, named in research R6)

tests/
├── conftest.py          # + read_golden_bytes, + npc fixtures, + the designation constants
│                        #   hoisted out of test_licensing and test_packaging,
│                        #   SECTION_15_NOTICES updated
├── unit/                # + chargen, names, character, generator, render;
│                        #   test_licensing extended for the two designations
├── contract/            # + the npc document payload
├── integration/         # + npc CLI, streams, batch, overrides, goldens
├── guards/              # + no-locale guard; packaging designation check split;
│                        #   seed-contract library list extended; data layout unchanged
├── property/            # + walk invariants over seeds
└── golden/
    ├── npc_*.txt        # NEW: compared as bytes, literal tabs, LF (research R7)
    └── (existing files unchanged, and deliberately not regenerated)
```

**Structure Decision**: the flat module layout is kept and four modules are added to it,
each owning the schema of the files it produces types for, which is the rule research R11
of the previous feature set. `chargen.py` owns the six universal table kinds; `names.py`
owns the two name kinds *and* the region-first roll, because the roll is what FR-043f
constrains and it belongs beside the tables it weights; `character.py` owns the produced
value; `generator.py` owns the walk. `rules.py` keeps discovery, composition, provenance,
the task-parameters schema, and dispatch.

Splitting `character.py` from `generator.py` is the one place this departs from the
existing precedent, where `dice.py` and `tasks.py` each hold their parameters, their result
type, and their function together. It is recorded in Complexity Tracking. The short reason
is that `render.py` and every consumer read the character while only the walk writes it,
and the walk is by a wide margin the largest single body of code in the package.

The data directory gains two subdirectories. `importlib.resources` traverses them without
`__init__.py`, verified for the previous feature's two and unchanged here.

## Implementation Notes

Guidance to carry into `/speckit-tasks` and `/speckit-implement`.

### Tidy First: what is structural, and what has to go first

Six changes rearrange code without changing any output. Per the project's Tidy First rule
they are separate commits, they come before the behavioral work, and each says so in its
message. The suite runs green before and after each.

1. **`render._provenance_lines` gains an `indent` parameter.** The npc command writes the
   block to stderr with no surrounding result, so it needs it unindented.
2. **`as_text` gains a keyword-only `full: bool = False`.** Every existing registration
   accepts it and raises `CetoolsError` when it is true, so a caller asking for a fuller
   rendering of a throw is told rather than quietly handed the plain one.
3. **`rules._validate`'s per-kind blocks become a table.** Four repeated blocks become a
   `kind -> parse function` mapping and one loop. Doing this before the count goes from
   four to eleven is the whole point.
4. **`Band` and the characteristic modifier bands move from `tasks.py` to
   `registries.py`.** `TaskParameters` loses `characteristic_bands` and
   `characteristic_dm`; `CharacteristicRegistry` gains them; `check` calls
   `rules.characteristics.characteristic_dm(...)`. Both affected schema versions rise to 2
   and both data files change. **No golden file and no JSON fixture may change**, which is
   SC-014, and the committed check goldens are the evidence: they are the previous
   feature's output and regenerating them in this feature would destroy exactly what
   SC-014 asks to compare against. This is a breaking library change and gets a
   **Breaking changes** changelog heading.
5. **`tables.advanced` is renamed `tables.specialist`** in the career schema and in
   `navy.toml`. No behavior reads it yet.
6. **`DESIGNATION` and `_uncovered` are hoisted into `tests/conftest.py`.** They are
   duplicated verbatim in `test_licensing.py` and `test_packaging.py` today, a second
   designation is about to be added beside them, and a constant that has to be edited in
   two places is one that will be edited in one.

### Build order

Each step's tests are written, committed, and observed failing before the implementation,
per Principle III and SC-016. This is the feature that pays off the previous one's recorded
deviation, so the commit separation is the deliverable, not a nicety.

Structural work above, then: `seeds` (`derive_seed`) → `registries` (bands, pseudo-hex) →
`chargen` → `names` → `careers` (v2) → `rules` (new kinds, the draft cross-file rule) →
the Open Game Content data files → **the licensing checks, widened** → the name tables →
`character` → `generator` → `render` → `cli` → goldens → guards → the sampled
audits → property tests → README, CHANGELOG.

The data files come after the schemas that validate them and before the walk that reads
them, because a walk written against data that does not exist yet is a walk written against
what its author remembers of the source material.

**The licensing checks widen between the two groups of data files, and the order is not a
preference.** `_assert_shipped_rules_data` asserts `"Open Game Content" in text` of every
`.toml` in the wheel and the sdist. Every file in the first group satisfies it; the first
file in the second group does not, and would not until the check is widened. Authoring the
name tables first therefore puts the whole of that work on the wrong side of the rule that a
commit lands only with the suite green. Widening first costs nothing: an exactly-one-of-two
check over files that all carry the first designation passes, and the GPL mirror passes
vacuously. `README.md` and `CONTRIBUTING.md` change in this group too, before the sentence
they carry becomes false rather than after.

### Per the project's global instruction, the `fluent-python:*` skills that apply

- `choosing-a-data-class-builder` — frozen slotted dataclasses throughout, as everywhere
  else in the package
- `using-pattern-matching` — dispatching on notation entry types inside the walk, and on
  history step effects inside the renderer
- `choosing-mapping-types` — the character's characteristics and the surname tables in
  force, as read-only mappings
- `writing-sequence-idioms` — accumulating history steps and skills without intermediate
  lists per term
- `using-functools-and-operator` — the `singledispatch` registrations, and the sort key
- `designing-function-signatures` — keyword-only `name=`, `count=`, and `full=`
- `writing-generators-and-iterators` — the term loop reads naturally as a generator of
  history steps
- `handling-text-encoding` — the golden files are compared as bytes and the sort key is
  `casefold`, never `locale.strxfrm`

### Traps worth naming now

Each is already resolved in research or the contracts; they are collected here because each
one is a place where the obvious implementation is wrong.

- **The name roller is derived, never drawn from the walk's roller.** This is FR-047b and
  FR-056a, and the natural implementation violates both. Write the test that generates the
  same seed with and without a supplied name and compares field by field *first*.
- **`character_seed(master, 0)` is `master` itself.** Not a derivation. Without that,
  `--seed X` and `--seed X --count 1` produce different people, and a quoted derived seed
  does not round-trip. Research R2.
- **Do not regenerate `tests/golden/check_*.txt`.** They are SC-014's evidence.
- **`tests/unit/test_library_api.py` derives `__all__` from the spec contracts.** Its
  parser reads `## Public surface added` and `## Public surface removed` out of
  `specs/002-rules-data-loading/contracts/library-api.md`. Adding an export requires both
  writing `specs/003-npc-generator/contracts/library-api.md` with those headings **and**
  extending the parser to a third contract. The test will fail with a set difference that
  does not obviously say so.
- **`options_in_help` asserts whole-set equality.** The new command needs its own
  assertion, and any option added later breaks it deliberately.
- **The seed-contract guard's library list is manual.** `generate_character` and
  `generate_batch` must be added to it or a stray `random` call is unguarded.
- **The npc goldens are rendered from hand-constructed `Character` values, not captured from
  a seed.** Which character a given seed produces is unknowable until the walk exists, so a
  golden captured from a finished implementation is not an expected value written before it,
  which is what SC-016 asks for. The six SC-009 references, the fuller sheet, and the batch
  reference are each a constructed character plus a hand-authored byte string with the
  renderer in between. What the command owes them is a derivation, not a second expectation:
  its stdout equals `as_text(...)` of the character it generated.
- **`read_golden` reads text, which silently normalizes CRLF.** The Universal Character
  Format is tab separated, and a golden that pins tabs and line endings has to be compared
  as bytes. New fixture, and `.gitattributes` marks the npc goldens so no tool touches
  them. Research R7.
- **The property suite computes `_PARAMETERS = load_rules().task_parameters` at import
  time**, before the autouse cache-clearing fixture can run. Moving the characteristic
  bands must not reach into that line; it reads `difficulty_dms` only, so it does not, but
  check it rather than assume it.
- **`ValidationProblem` is `order=True` over all four fields.** Adding a field to it would
  silently join the sort key and break the pinned JSON key order. Nothing here needs to,
  and nothing here may.
- **Basenames are unique tree-wide and 21 files are landing at once.** `skills.toml`
  already exists, so the background skills file cannot be `skills.toml`;
  `characteristics.toml` exists, so nothing else may be. `tests/guards/test_data_layout.py`
  catches it, but catching it after authoring seven careers is a slow way to find out.
- **`d66` reads two faces as tens and units.** A table indexed 11 to 66 is not a table
  indexed 1 to 36, and the Draft table's row order is significant because the die that
  reads it is positional (FR-005).
- **A gate excludes rather than fails.** A table the character does not qualify for is not
  among the tables the skill roll may select, so the selection is over the eligible set,
  not over all tables with a retry.
- **The commission is entered once per career**, and a successful commission or
  advancement is always taken (FR-012). Declining is not modeled.
- **A mishap-ended term still counts** toward the term cap and the aging modifier, costs
  the shorter number of years, and forfeits that term's benefit roll (FR-020). Three
  separate consequences; the natural implementation gets one or two of them.
- **The characteristics registry has to declare each characteristic's class.** The aging
  table reduces "three physical characteristics" and "one mental characteristic", and
  neither can be read from data without it. FR-039 does not name the field, and it is
  load-bearing; research R12 records why it is added under the same reasoning FR-039 gives
  for the bands and the letters, rather than being a liberty the design took.
- **A pension is earned in one career, not over a life** (FR-018). `pension.minimum-terms`
  is compared against the terms of a single `CareerService`, never against the total. Summing
  the character's terms is the natural implementation and it pays the wrong people.
- **A commission moves the character to another ladder** (FR-007b), at the lowest rank that
  ladder declares, and the rank bonus there is granted on arrival. `CareerService.ladder` is
  the ladder they ended on, which for a commissioned character is not the one they entered on.
- **The aging crisis debt buys something.** Settling it lifts every characteristic the crisis
  covered to `medical.crisis-restores-to` (FR-021). An implementation that records the debt and
  settles it without restoring anything passes every test that only checks the arithmetic.
- **Debts settle in the order they arose** (FR-025a), and a partly covered medical bill
  restores points one at a time in an order the walk decides and records. Iterating a mapping
  of reductions is the traversal-order dependency FR-056 forbids.
- **A characteristic reduction floors at the bottom of the declared pseudo-hex range.**
  Two statements in the spec pull against each other here, and research R13 settles them.
  The history records the reduction called for *and* the amount applied when they differ,
  because SC-005 reads both.

### Deliberately not built

So review does not read these as gaps. Each is recorded with its reason in the spec's Out
of Scope: the remaining sixteen careers, a lethal mode, psionics and anagathics, world and
homeworld generation, culturally coherent names, any correlation between a name and the
rest of the character, gender in any form, non-human species, noble titles, starting
equipment, modeling material benefits, forcing a career or a term count, and editing or
re-rolling a generated character. Research R10 adds three at implementation grain: no new
error type, no schema migration machinery behind the raised versions, and no floor or
ceiling imposed on an override's name tables.

## Complexity Tracking

Three rows. None is a constitutional violation; each is a place where this feature is
deliberately less simple than the minimum, and Principle VI says such a choice must survive
review rather than pass unnoticed.

| Choice | Why needed | Simpler alternative rejected because |
|---|---|---|
| Four new modules, in particular splitting `character.py` from `generator.py` | The package's precedent (`dice.py`, `tasks.py`) is to keep a result type beside the function that builds it, and this departs from it. The walk is the largest body of code in the package and is written by one caller; the character is read by the renderer, the CLI, both audit suites, and every library consumer. Keeping them together would make the module that every consumer imports the module that holds the engine. | One `chargen.py` holding schemas, model, and walk together, rejected at roughly 1,200 lines in one file. Folding the model into `render.py`, rejected because the model is not a rendering concern. |
| A second licensing designation, and the guards that tell the two apart | FR-042a requires it, and SC-015a requires it to be demonstrably fail-able. The cost is real: two designation constants, a narrowed Section 15 notice that still parses machine-readably, and the exactly-one-of-two check duplicated across the working tree, the wheel, and the sdist. | Designating the name tables OGC, rejected because they are not derived from the source material and the OGL cannot be claimed over content it does not cover. Leaving them undesignated, rejected because SC-015 requires no file to carry neither. |
| `as_text` grows a `full=` flag that most registrations reject | A second public function (`as_full_text`) would be the simpler surface. The flag was chosen because the fuller sheet is the same rendering of the same value at a different depth, and because two entry points would each need their own dispatch fallback and their own contract row. | Two functions, rejected for the reason above. Silently ignoring `full=True` on registrations that have no fuller form, rejected because it is the dispatch-miss failure the existing fallback exists to detect, one level down. |

No new runtime dependency is introduced, so the dependency clause of Principle VI is not
engaged.
