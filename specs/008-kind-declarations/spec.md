# Feature Specification: Kind Declarations

**Feature Branch**: `008-kind-declarations`

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "The rules loader describes the thirteen kinds of
rules-data file in six separate lists that have to be kept in agreement by hand:
which kinds exist, which version of each is supported, which kinds are one file
each, where each one-file kind lives in the packaged data, the order they're
parsed in, and the final check that all of them are present. This feature
replaces those six lists with one declaration per kind, stating its name,
supported schema version, whether it is one file or many, its canonical packaged
file where it has one, and how it's parsed. Discovery, the version check,
parsing of one-file kinds and the presence check all read from that single
declaration, and the lists that could drift out of agreement disappear. Building
the rules data set at the end stays explicit, field by field. The change is
purely structural. [...] Three boundaries were deliberately settled: many-file
kinds keep their own parsing loops; background skills keeps its single explicit
parse step after the empty substitutes; declaration order is for readers and is
not a behavioral contract. Acceptance rests on the existing suite passing
unchanged, with two exceptions: the test that pins two lists against each other
becomes a test that each declared canonical file really is the packaged file
declaring that kind, without a hard-coded count; and tests that fake a
schema-version bump patch the declaration instead of the old list."

## Clarifications

### Session 2026-09-30

- Q: Besides the test edits FR-012 permits, may or must this feature add new
  tests that check the declarations themselves? → A: Require a few new tests of
  declaration invariants; existing tests change only as FR-012 permits.
- Q: Which kind declarations should state a parser? → A: Only the ten kinds
  the general one-file loop parses; background skills, careers, and surname
  tables carry none, and their explicit steps call their parsers directly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nothing a user sees moves (Priority: P1)

Someone generates characters, rolls tasks, or validates a directory of edited
rules-data files. They do this the day before this feature lands and the day
after, and nothing they see differs: the same human-readable output, the same
JSON, the same validation report, the same problems in the same words and the
same order. A library user importing `cetools` finds the same names with the
same behavior.

**Why this priority**: The feature buys nothing a user can see, so the only way
it can fail a user is by changing something. Everything else here is worthless
if this does not hold.

**Independent Test**: Run the full existing suite, including the golden and
contract corpora, with existing tests changed only as FR-012 permits. Every
test passes and neither corpus has been touched.

**Acceptance Scenarios**:

1. **Given** the packaged data with no override, **When** any CLI command runs
   in either output mode, **Then** its output is byte-identical to the output
   before the feature.
2. **Given** an override directory with a file declaring an unknown kind,
   **When** it is validated, **Then** the problem lists the recognized kinds in
   the same words and the same order as today.
3. **Given** an override directory with a file declaring a known kind at an
   unsupported schema version, **When** it is validated, **Then** the version
   problem is reported exactly as today and no further problem is reported for
   that file's slot.
4. **Given** an override that removes, duplicates, or replaces a one-file kind,
   **When** it is validated, **Then** the missing-kind and duplicate-kind
   problems name the same files, in the same words, as today.

---

### User Story 2 - A kind is described in one place (Priority: P1)

A contributor needs to know everything the loader believes about a kind: whether
it exists, which schema version is supported, whether it is one file or many,
which packaged file carries it, and how it is parsed. Today they read six places
and trust that the six agree. After this feature they read one declaration, and
there is no second place that could disagree with it.

**Why this priority**: This is the value the feature delivers. Drift between the
lists is a defect nothing in the code prevents today; one test exists only to
catch two of them disagreeing.

**Independent Test**: For any kind, search the loader for its name. Apart from
the one declaration, it appears only where the code does something specific to
that kind (the background-skills parse step, the many-file loops, and building
the rules data set), never in a list whose job is to enumerate kinds.

**Acceptance Scenarios**:

1. **Given** the loader after the feature, **When** a reader looks for the
   supported schema version of a kind, **Then** it is stated in exactly one
   place, alongside every other fact about that kind.
2. **Given** discovery, the version check, the one-file parse, and the presence
   check, **When** each needs the set of kinds or a fact about one, **Then**
   each reads it from the declarations rather than from its own list.
3. **Given** the loader after the feature, **When** a reader looks for a
   comment claiming that parse order is load-bearing, **Then** there is none.

---

### User Story 3 - The loader gets smaller (Priority: P2)

A reviewer compares the loader before and after. The replaced lists and the
eleven separate one-file parse calls are gone, and what replaced them is shorter
than what it replaced.

**Why this priority**: The Simplicity principle is the justification the feature
rests on. It passes because it removes enumerations that already exist rather
than adding a layer, and that claim is only true if the result is smaller.

**Independent Test**: Count the lines of the loader module before and after the
feature.

**Acceptance Scenarios**:

1. **Given** the loader module before and after, **When** their lengths are
   compared, **Then** the after is shorter.

---

### Edge Cases

- **The list of recognized kinds in a problem.** The unknown-kind problem names
  every recognized kind. Its wording must come out identical, which depends on
  it being sorted before joining, as it is today, rather than following
  declaration order.
- **A rejected file still occupies its slot.** A one-file kind whose file is
  rejected on its header (unreadable, bad version, unknown or missing kind) is
  not also reported missing. That slot bookkeeping reads which kinds are one
  file and which basename each lives at; after this feature it reads both from
  the declarations, with the same result for every input.
- **Background skills depends on another kind.** Its parse needs the skills
  registry, or the empty substitute when that registry is absent or invalid. It
  is declared like every other one-file kind but states no parser, so the
  general one-file parse passes over it, and it is parsed in one explicit step
  after the substitutes exist.
  This is the only such kind; no general dependency mechanism is introduced.
- **Many-file kinds have no canonical file.** Careers and surname tables are
  declared, with their supported versions, but have no canonical packaged file,
  are not part of the one-file parse, and keep their own loops with their own
  duplicate-name checks.
- **Presence differs between the two many-file kinds.** Today the final
  presence check requires every one-file kind and at least one surname table,
  but not at least one career. That exact rule is preserved; the feature does
  not make the two many-file kinds uniform.
- **Parse order changes and must not matter.** The one-file kinds may be parsed
  in declaration order rather than today's hand-written order. Each file's
  problems are collected separately and the loader sorts all problems once
  before reporting, so the report cannot change. The sort stays exactly where
  it is.

## Requirements *(mandatory)*

### Functional Requirements

#### The declaration

- **FR-001**: Each of the thirteen kinds of rules-data file MUST be declared
  exactly once, stating its name, its supported schema version, whether it is
  one file or many, and its canonical packaged file if it is one file. A
  declaration MUST state a parser if and only if the general one-file loop
  (FR-007) parses its kind; background skills, careers, and surname tables
  state none, and their explicit steps call their parsers directly, so no
  parser is named in two places.
- **FR-002**: The declarations MUST be internal to the loader and MUST NOT be
  exported or added to the public library interface.
- **FR-003**: Declarations MUST be ordered for readers, grouped by the module
  that owns each kind's parser. The order MUST NOT carry behavior.

#### What reads from it

- **FR-004**: Discovery of which packaged file declares which kind MUST read the
  set of recognized kinds from the declarations.
- **FR-005**: The schema-version check and the unknown-kind check MUST read the
  supported version and the set of recognized kinds from the declarations.
- **FR-006**: The missing-kind and duplicate-kind checks for one-file kinds, and
  the bookkeeping of which one-file slot a rejected file occupies, MUST read
  which kinds are one file and each one's canonical file from the declarations.
- **FR-007**: Every one-file kind except background skills MUST be parsed by
  one loop over the declarations that state a parser; the loop MUST NOT name
  any kind. Background skills MUST be parsed in one explicit step after the
  empty registry substitutes are built, as today.
- **FR-008**: The final check that every required kind is present MUST read
  the one-file kinds from the declarations. The existing requirement that at
  least one surname table is present MUST be kept as it is.
- **FR-009**: Careers and surname tables MUST keep their own parsing loops and
  their kind-specific duplicate checks, unchanged.
- **FR-010**: Building the rules data set MUST remain explicit, naming each of
  its fields individually.

#### What goes away

- **FR-011**: After the feature, the loader MUST contain no hand-kept list of
  kinds other than the declarations: no separate table of supported versions,
  no separate list of one-file kinds, no separate table of canonical files, no
  hand-written sequence of one-file parse calls, and no hand-written presence
  check naming each one-file kind. The comment stating that parse order is
  load-bearing MUST be removed.

#### Preserving behavior

- **FR-012**: Nothing a user can see may change: human-readable output, JSON
  output, the validation report, and the wording, location, and order of every
  problem, for every input. The golden and contract corpora MUST NOT be edited.
  The existing suite MUST pass, with only these edits to existing tests
  permitted (new tests are governed by FR-015):
  - The test that pins the canonical-file table against the one-file kind list
    MUST become a test that each declared canonical file is the packaged file
    that declares that kind, and MUST lose its hard-coded count of one-file
    kinds.
  - Tests that reach into the supported-version table MUST reach into the
    declarations instead. This covers the two tests that fake a schema-version
    bump by patching it, and the test that checks supported versions are
    integer literals unrelated to the package version, which iterates it.
- **FR-013**: The loader's single sort of all problems before reporting MUST
  stay where it is.
- **FR-014**: This feature is structural throughout. No commit may carry a
  behavioral change, and because nothing a user or library consumer can see
  changes, no commit adds a `CHANGELOG.md` entry.
- **FR-015**: New tests MUST pin what only the declarations can get wrong,
  written before the declarations exist so they fail first: every declared
  name is unique; every one-file kind declares a canonical file and no
  many-file kind does; and every one-file kind is parsed exactly once, by the
  general loop or by the background-skills step. No new
  test may assert a count of kinds (SC-005).

### Key Entities

- **Kind**: One sort of rules-data file, named by the `kind` a file declares in
  its header. Thirteen exist: eleven are one file each (task parameters,
  characteristics, skills, benefits, draft table, aging table, mishap table,
  background skills, medical tiers, chargen parameters, given names) and two
  are many files each (careers, surname tables).
- **Kind declaration**: The one internal statement of everything the loader
  knows about a kind: name, supported schema version, one file or many,
  canonical packaged file where it has one, and parser where the general
  one-file loop parses it.
- **Canonical file**: The packaged file a one-file kind lives at, and the name
  an override replaces it under.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full suite passes, with the golden and contract corpora
  byte-identical to their state before the feature, with existing tests
  changed only as FR-012 permits, and with the new tests FR-015 requires
  passing.
- **SC-002**: Hand-kept enumerations of kinds in the loader go from five to
  one. The five are the supported-version table (whose keys also serve as the
  set of kinds, so it covers two of the input's six lists), the one-file kind
  list, the canonical-file table, the sequence of one-file parse calls, and the
  presence check. The one is the declarations. The explicit construction of the
  rules data set is not counted: FR-010 keeps it on purpose.
- **SC-003**: Adding a kind means writing one declaration plus the code that is
  genuinely specific to that kind (its parser, its rules data field). No list
  exists that must also be edited to keep the loader consistent.
- **SC-004**: The loader module is shorter after the feature than before.
- **SC-005**: No test asserts a count of kinds.

## Assumptions

- "Which kinds exist" and "which version each supports" are one table today,
  whose keys serve as the first and values as the second. The six lists the
  input names are therefore five hand-kept structures in the loader, which is
  the count SC-002 uses.
- The derived reverse lookup from canonical file to kind goes with the table it
  is derived from, and is replaced by a lookup derived from the declarations.
- The problem sort is a total order over problems within one file, as feature
  007 assumed. Since each file's problems are still collected separately and
  folded in whole, a change of parse order cannot interleave two files, so a
  report cannot move. If it ever did, the signal is to stop and reconsider,
  never to adjust the tests or move the sort.
- A docstring or comment that names a renamed test or a removed table is
  updated in the same commit, so the source never points at something that no
  longer exists.
- No third-party dependency is added and no performance requirement is stated:
  the loader runs once per load and the declarations are a handful of small
  records.
