# Feature Specification: Validation Vocabulary

**Feature Branch**: `006-validation-vocabulary`

**Created**: 2026-09-06

**Status**: Draft

**Input**: User description: "Five modules that parse rules-data TOML files each
hand-roll the same field-checking logic, and the copies have already drifted:
`_unrecognized_key_problems` is byte-identical in five files, `_require_string`
in three, and `_require_int` exists three times with three different behaviors.
Give the checking layer one home, the way `errors.py` already gives
`ValidationProblem` and `type_name` one home, so a rule about what a data file
may contain is stated once and reported the same way everywhere."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One wording for one rule (Priority: P1)

Someone editing a rules data file writes a term length of `0` where the rules
require at least one year. They read the reported problem, fix it, and move on.
Later they make the same class of mistake in a career file, and the report tells
them the same thing in the same words, because it is the same rule.

Today it does not. A career's throw target below its minimum is reported as
needing "a positive integer"; a term length below its minimum is reported as
needing "an integer >= 1". Both fields require the same thing. The reader has to
notice that two different sentences describe one rule, and cannot tell whether
the difference is meaningful.

**Why this priority**: It is the only part of this feature a reader of the
reports can see, and it has to land first regardless: the duplicated checks
cannot be merged into one until they agree on what to say.

**Independent Test**: Put a below-minimum value in each field that requires at
least one, run validation, and confirm every one of them reports the same
expected phrasing, with no reference to any other change in this feature.

**Acceptance Scenarios**:

1. **Given** a chargen parameters file whose `terms.term-years` is `0`,
   **When** the data set is validated, **Then** the reported problem for that
   field expects "a positive integer".
2. **Given** a career file whose `throws.survival.target` is `0`, **When** the
   data set is validated, **Then** the reported problem expects "a positive
   integer", exactly as it does today.
3. **Given** any field whose minimum is `0` rather than `1`, **When** a value
   below it is validated, **Then** the reported problem expects "an integer >=
   0", unchanged.
4. **Given** the whole packaged data set, **When** it is validated, **Then**
   every reported problem other than those for the six fields whose minimum is
   one is worded exactly as it was before this change.

---

### User Story 2 - One place to state a rule (Priority: P2)

A contributor adds a new kind of rules data file, or a new field to an existing
one. They need a field that must be a non-empty string, and one that must be an
integer of at least zero. They reach for the checks the project already has,
find them in one place, and use them. They do not copy a helper out of a
neighboring module, and they do not have to work out which of three versions of
the same helper is the one to imitate.

**Why this priority**: It is the durable value. The wording drift in Story 1 is
a symptom; the cause is that there was nowhere for a check to live, so each
module grew its own. Until the checks have a home, every new data-file kind
adds another copy.

**Independent Test**: The vocabulary exists and is exercised directly by its own
tests, covering each check's absent-key, wrong-type, boundary, and accepted
paths, without any parser module having been changed yet.

**Acceptance Scenarios**:

1. **Given** the vocabulary module, **When** a required integer field is absent
   from its table, **Then** the reported problem says the value is "missing" and
   names the dotted path of the field.
2. **Given** the vocabulary module, **When** a required integer field holds a
   boolean, **Then** the value is rejected rather than accepted as the integer a
   boolean would otherwise pass for.
3. **Given** the vocabulary module, **When** a required table is checked against
   an absent value, **Then** the reported problem says "missing" rather than
   naming a type.
4. **Given** the vocabulary module, **When** a table carries keys the schema
   does not admit, **Then** one problem is reported per unrecognized key, in
   sorted order, each naming the admitted keys.
5. **Given** an optional boolean field, **When** the key is absent, **Then** the
   declared default is taken and no problem is reported.

---

### User Story 3 - The parsers stop restating the rules (Priority: P3)

Every module that reads a rules data file obtains its field checks from the one
place they live. The sixteen private definitions scattered across five modules
are gone, and so are the hand-inlined checks that expressed the same shapes
without ever being given a name.

**Why this priority**: This is what removes the duplication, but it is the part
with no observable effect of its own: it is finished when everything behaves
exactly as it did before. It depends on both stories above.

**Independent Test**: Run the existing suite unchanged. Every message the
validator produces for the packaged data and for the invalid-fixture corpus is
identical to what it produced before, and no module other than the vocabulary
defines any of the checks.

**Acceptance Scenarios**:

1. **Given** the migrated modules, **When** the full test suite runs, **Then**
   it passes with no changes beyond the wording assertions added by Story 1.
2. **Given** the migrated modules, **When** the source is searched for
   definitions of the seven checks, **Then** each is defined exactly once, in
   the vocabulary module.
3. **Given** a career file that omits `always-available`, **When** it is
   validated, **Then** the career is treated as not always available and no
   problem is reported, exactly as today.
4. **Given** the chargen parameters file, **When** it is validated, **Then** its
   field-by-field declaration still drives its own parsing, now resolving each
   declared kind through the shared checks.

---

### Edge Cases

- A key that is absent and a key that is present holding the wrong type must
  stay distinguishable: the first reports "missing", the second names the type
  found. Collapsing the two would make a typo in a key name indistinguishable
  from a typo in its value.
- A required table checked against an absent value must report "missing" rather
  than naming the absence as a type. This is safe to infer from absence alone
  because a data file has no way to write an empty value: a key is either
  present carrying something or not there at all.
- A minimum of one and a minimum of zero must not collapse into one phrasing.
  Only the former reads as "a positive integer".
- A boolean must be rejected wherever an integer is required, even though the
  underlying representation treats booleans as a kind of integer.
- A dice-notation field must keep rejecting the two-digit table die, which
  describes a table value rather than a count and a side count.
- An unrecognized key must be reported once per key and in a stable order, so
  that a report of the same file reads the same way on every run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A single module MUST own the checks that decide whether one field
  of a rules data file holds an acceptable value.
- **FR-002**: The vocabulary MUST provide a required-integer check accepting an
  optional lower bound.
- **FR-003**: The vocabulary MUST provide a required non-empty-string check.
- **FR-004**: The vocabulary MUST provide a required-boolean check.
- **FR-005**: The vocabulary MUST provide an optional-boolean check that takes a
  declared default when the key is absent and reports no problem for it.
- **FR-006**: The vocabulary MUST provide a required dice-notation check that
  rejects notation the grammar refuses and rejects the two-digit table die.
- **FR-007**: The vocabulary MUST provide a required-table check that accepts a
  value already in hand and reports it as missing when the value is absent.
- **FR-008**: The vocabulary MUST provide a check reporting every key a table
  carries that its schema does not admit, one problem per key, in sorted order,
  each naming the admitted keys.
- **FR-009**: A value below a required minimum of one MUST be reported as
  expecting "a positive integer", in every data-file kind.
- **FR-010**: A value below a required minimum other than one MUST keep its
  current phrasing naming that minimum.
- **FR-011**: An absent key MUST be reported as "missing"; a key present holding
  the wrong type MUST be reported by naming the type found, in the vocabulary
  the data files themselves use.
- **FR-012**: A boolean MUST be rejected wherever an integer is required.
- **FR-013**: Every validation message MUST be unchanged by this feature except
  those for the six fields whose minimum is one and whose current phrasing names
  the minimum numerically.
- **FR-014**: No module other than the vocabulary MUST define any of the checks
  in FR-002 through FR-008.
- **FR-015**: Every module that parses a rules data file MUST obtain these
  checks from the vocabulary, including at the sites that currently express the
  same checks inline without naming them.
- **FR-016**: The vocabulary MUST be package-internal: reachable by the modules
  that parse data files, and absent from the library's declared public surface.
- **FR-017**: The field-by-field declaration that drives chargen parameter
  parsing MUST stay local to that module, resolving each declared kind through
  the shared checks rather than through copies.
- **FR-018**: The vocabulary MUST have its own direct tests, written before it
  exists and failing until it does, covering each check's absent-key,
  wrong-type, boundary, and accepted paths.
- **FR-019**: The wording change in FR-009 MUST ship separately from, and before,
  the removal of the duplicate definitions, and MUST carry a changelog entry.
  The removal itself is not user-visible and MUST NOT claim a changelog entry of
  its own.
- **FR-020**: This feature MUST NOT introduce a carrier for the file-and-path
  pair, MUST NOT introduce a shared check for arrays of parsed elements, MUST
  NOT extend the field-by-field declaration pattern to any other module, and
  MUST NOT alter the checks that resolve a skill, benefit, or characteristic
  name against its registry.

### Key Entities

- **Field check**: A decision about whether one field of one data file holds an
  acceptable value. Reports what it found and what it expected, names the
  field's location, and yields the accepted value or nothing.
- **Validation problem**: One thing wrong with one data file, naming the file,
  the field's dotted location, what was found, and what was expected. Already
  modeled; unchanged by this feature.
- **Dotted location**: The path identifying a field inside its file, built up
  segment by segment as parsing descends. Unchanged in form by this feature.
- **Data-file kind**: One category of rules data, each with its own schema and
  its own parser. Five modules parse the kinds between them.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every field requiring a minimum of one reports the same expected
  phrasing. The count of distinct phrasings for that one rule falls from two to
  one.
- **SC-002**: Each of the seven checks is defined exactly once across the whole
  source tree, down from sixteen definitions of the seven.
- **SC-003**: Validating the packaged data set and the existing invalid-fixture
  corpus produces messages identical to those produced before this feature,
  except for the six fields named in FR-013.
- **SC-004**: The full test suite passes, with the only test changes being the
  wording assertions added for the six fields and the new tests covering the
  vocabulary directly.
- **SC-005**: A contributor adding a checked field to any data-file kind can do
  so without writing a type check, a missing-key check, or a problem message,
  and without copying anything from another module.
- **SC-006**: Changing how any one of the seven checks reports requires editing
  one place, and the change reaches every data-file kind.

## Assumptions

- A rules data file cannot express an empty value: a key is either present
  carrying something or absent. This is what makes it safe for the required-table
  check to read an absent value as a missing key rather than as a value of some
  empty type, and it is why that check needs no separate way to be told which of
  the two it is looking at.
- No existing test pins either phrasing of the below-minimum message, so the
  choice between them is free. The six fields whose messages change are the only
  places the change is observable.
- The wording that survives is the one already used by career throw targets, on
  the grounds that the reports elsewhere are written in English rather than in
  notation: they say "a non-empty string", "an empty table", "at least one
  entry".
- The checks stay in the shape they already have, taking the file and the
  field's location as separate values. Giving that pair a carrier of its own is
  a separate change, deliberately not attempted here.
- Bare names are used rather than underscore-prefixed ones, following the
  parsers, which are bare and unexported. The underscore is reserved by an
  earlier contract for a stronger promise about two specific symbols.
- How the migration is divided into commits, beyond the requirement that the
  wording change precedes the removals, is left to task breakdown.
