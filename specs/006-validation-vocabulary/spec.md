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

## Clarifications

### Session 2026-09-06

- Q: Should a guard test enforce that each of the seven checks is defined in
  only one place, so the duplication cannot grow back? (FR-014, SC-002) → A:
  Yes. A guard scans the source for definitions of the seven checks and fails
  if any is defined outside the vocabulary, following the six existing guards
  that already read source text to hold a standing rule.
- Q: When the two string checks merge, which wording should an absent key
  report? (FR-013) → A: "A non-empty string", everywhere. The two checks were
  found to differ only in that one case, and the more numerous of them
  contradicts itself, calling one rule "a string" when the key is missing and
  "a non-empty string" when the value is present and empty.
- Q: When an optional boolean field is present but holds something other than a
  boolean, what should the check hand back? (FR-005) → A: Report the problem and
  return the declared default, which is what the code does today. The check
  always yields a boolean and never an absent result, so no call site has to
  branch on the rejected case.

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

The same split runs through the required text fields. A career's name left out
is reported as needing "a string", while that same field left empty is reported
as needing "a non-empty string", and a characteristic's label left out is
reported as needing "a non-empty string" again. One requirement, described three
ways, depending on which module and which failure the reader happened to hit.

**Why this priority**: It is the only part of this feature a reader of the
reports can see, and it has to land first regardless: the duplicated checks
cannot be merged into one until they agree on what to say.

**Independent Test**: Put a below-minimum value in each field that requires at
least one, and leave each required text field absent, then run validation and
confirm that each of the two rules is described in the same words wherever it
is broken, with no reference to any other change in this feature.

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
4. **Given** any required text field left absent, **When** it is validated,
   **Then** the reported problem expects "a non-empty string", the same words
   that field already uses when its value is present but empty.
5. **Given** a dice-notation field left absent, **When** it is validated,
   **Then** the reported problem still expects "a string", because that field
   requires notation rather than merely a name with something in it.
6. **Given** the whole packaged data set, **When** it is validated, **Then**
   every reported problem outside the two rules above is worded exactly as it
   was before this change.

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
6. **Given** an optional boolean field, **When** the key is present holding a
   value that is not a boolean, **Then** a problem is reported and the declared
   default is still yielded.

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
- **FR-003**: The vocabulary MUST provide a required non-empty-string check. A
  field guarded by it is called a *required text field* throughout this
  specification. The two names are one rule seen from two sides, the check's and
  the data file's, and no requirement here distinguishes them.
- **FR-004**: The vocabulary MUST provide a required-boolean check.
- **FR-005**: The vocabulary MUST provide an optional-boolean check that takes a
  declared default when the key is absent and reports no problem for it. When
  the key is present holding something other than a boolean, the check MUST
  report a problem and still yield the declared default: it always produces a
  boolean, never an absent result, so no caller has to handle the rejected case.
- **FR-006**: The vocabulary MUST provide a required dice-notation check that
  rejects notation the grammar refuses and rejects the two-digit table die.
- **FR-007**: The vocabulary MUST provide a required-table check that accepts a
  value already in hand and reports it as missing when the value is absent.
- **FR-008**: The vocabulary MUST provide a check reporting every key a table
  carries that its schema does not admit, one problem per key, in sorted order,
  each naming the admitted keys.
- **FR-009**: A value below a required minimum of one MUST be reported as
  expecting "a positive integer", in every data-file kind.
- **FR-009a**: A required text field that is absent MUST be reported as
  expecting "a non-empty string", the same words already used when such a field
  is present but empty. The two string checks being merged differ in this one
  case and in no other, and the more widely used of them describes one rule two
  ways depending on how it was broken.
- **FR-010**: A value below a required minimum other than one MUST keep its
  current phrasing naming that minimum.
- **FR-010a**: A dice-notation field that is absent MUST keep expecting "a
  string". It requires valid dice notation rather than merely text with
  something in it, so it is not the rule FR-009a unifies and MUST NOT be swept
  into it. A dice-notation field is not a required text field.
- **FR-011**: In every required check, an absent key MUST be reported as
  "missing"; a key present holding the wrong type MUST be reported by naming the
  type found, in the vocabulary the data files themselves use. This binds the
  required checks only. The optional-boolean check of FR-005 treats an absent key
  as a success that yields the declared default and reports nothing for it, which
  is an exception to this rule rather than a violation of it.
- **FR-012**: A boolean MUST be rejected wherever an integer is required.
- **FR-013**: Every validation message MUST be unchanged by this feature except
  the two named in FR-009 and FR-009a: the fields whose minimum is one and whose
  current phrasing names that minimum numerically, and the absent-key report for
  required text fields. Any further divergence is a finding to be raised, not a
  message to be quietly rewritten; FR-013b says to whom, and with what effect on
  the work in flight.
- **FR-013a**: The obligation in FR-013 MUST be established by comparing the
  validator's output over the invalid-fixture corpus before and after each
  structural change. It MUST NOT be inferred from the test suite passing, which
  is not evidence for it: the source emits sixty-three distinct expected
  phrasings, and the tests name nine of them in an assertion, or nineteen
  counting comparisons against a whole problem. The fifty-four unnamed ones
  include the phrasing FR-009a makes canonical and every table phrasing the
  required-table check carries, so the messages the suite covers least are the
  ones this feature disturbs most.
- **FR-013b**: A divergence from FR-013 MUST be surfaced to the maintainer as a
  decision about the wording, and MUST NOT be settled by whoever finds it. This
  holds whether the divergence is found while the work is in progress or after
  the change that introduced it has landed. Until it is settled, no further
  structural change ships: the method of this feature is that every step is
  provably message-neutral, and a step taken on top of an unexplained divergence
  cannot be. Where the divergence has already landed, whether to correct it
  forward or to amend the change that caused it is the maintainer's call, but
  the divergence and its resolution MUST appear in the record either way. The
  one outcome ruled out is a message quietly becoming correct with no note that
  it was ever wrong, which is how the drift this feature removes accumulated in
  the first place.
- **FR-014**: No module other than the vocabulary MUST define any of the checks
  in FR-002 through FR-008.
- **FR-014a**: An automated guard MUST fail when any of the checks in FR-002
  through FR-008 is defined outside the vocabulary, so that a later module
  cannot reintroduce a copy unnoticed. The duplication this feature removes
  accumulated one module at a time, each addition defensible on its own, which
  is why the rule needs an enforcer rather than a note.
- **FR-014b**: "Defined" in FR-014a means a named definition at the top level of
  a module in the library's own source tree. The guard therefore does NOT catch
  a check written fresh and inline without a name, which is the very shape
  FR-015 converts. This limit MUST be stated wherever the guard is described, so
  that nobody reads the guard as a stronger promise than it is. Closing it would
  mean recognizing a check by its structure rather than its name, a much larger
  machine aimed at a rarer mistake than the one that actually happened: the
  copies that accumulated were copies of a named helper, five times over.
- **FR-014c**: The guard MUST itself be demonstrably able to fail, shown by a
  test that plants a definition the rule forbids and confirms the guard rejects
  it. A guard that would pass against a reintroduced duplicate reports the rule
  as held while it is being broken, which is worse than having no guard. Every
  existing guard in this project carries such a self-test; this one states the
  obligation rather than relying on the convention being noticed.
- **FR-015**: Every module that parses a rules data file MUST obtain these
  checks from the vocabulary, including at the sites that currently express the
  same checks inline without naming them. A site expresses one of these checks
  inline when it decides the acceptability of a single field named by key within
  a table, and reports the same found and expected phrasings that check reports.
  A decision about a whole array, or about an element identified by position
  rather than by key, is not such a site: it belongs to the array handling
  FR-020 leaves alone, even where its per-element test resembles one of these
  checks. The per-element non-empty-string test inside the name-table array
  reader is the case this distinction settles, and it stays where it is.
- **FR-016**: The vocabulary MUST be package-internal: reachable by the modules
  that parse data files, and absent from the library's declared public surface.
- **FR-017**: The field-by-field declaration that drives chargen parameter
  parsing MUST stay local to that module, resolving each declared kind through
  the shared checks rather than through copies.
- **FR-018**: The vocabulary MUST have its own direct tests, written before it
  exists and failing until it does, covering every outcome each check can
  produce, as enumerated for that check in the interface contract. Most checks
  share four outcomes: the absent key, the wrong type, the boundary, and the
  accepted value. Two do not have that shape, and for them the contract's own
  enumeration governs rather than that list.
- **FR-019**: The wording changes in FR-009 and FR-009a MUST ship separately
  from, and before, the removal of the duplicate definitions, and MUST carry a
  changelog entry. The removal itself is not user-visible and MUST NOT claim a
  changelog entry of its own.
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
  phrasing, and every required text field reports the same expected phrasing
  whether it is absent or empty. The count of distinct phrasings falls from two
  to one for the first rule and from two to one for the second.
- **SC-002**: Each of the seven checks is defined exactly once across the
  library's own source tree, down from sixteen definitions of the seven, and a
  test fails if that stops being true.
- **SC-003**: Validating the packaged data set and the existing invalid-fixture
  corpus produces messages identical to those produced before this feature,
  except for the two rules named in FR-013. This is established by the
  before-and-after comparison FR-013a requires, not inferred from the suite.
- **SC-004**: The full test suite passes, with the only test changes being the
  wording assertions added for the two rules in FR-013, the new tests covering
  the vocabulary directly, and the guard required by FR-014a together with the
  self-test FR-014c requires of it.
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
- No existing test pins either phrasing being changed, for either rule, and no
  golden output or documented example carries a validation problem message at
  all: the one documented run of the validator shows its success path. The
  machine-readable contract corpus does pin validation problem text, in four
  places, but only for a malformed file and for two registry-resolution
  messages: none of these is either rule, and the registry checks are excluded
  outright by FR-020. That corpus is named here because the project's own
  contributor guidance treats a change to machine-readable output as breaking
  it, so an exposure argument that passed over it would have been incomplete
  even though its conclusion holds. So both choices are free, and the changes
  are observable only to someone who breaks one of these fields.
- Where two phrasings compete, the surviving one is the more accurate, not the
  less disruptive. This follows the reports elsewhere, which are written in
  English rather than in notation: they say "a non-empty string", "an empty
  table", "at least one entry".
- The duplicate implementations were compared mechanically rather than by
  inspection. Every group is identical apart from its documentation except the
  integer check, which has three variants, and the two string checks, which
  differ in one case. Those two are the whole of the behavioral change, and
  FR-013 holds the line against a third being absorbed silently.
- The checks stay in the shape they already have, taking the file and the
  field's location as separate values. Giving that pair a carrier of its own is
  a separate change, deliberately not attempted here.
- Bare names are used rather than underscore-prefixed ones, following the
  parsers, which are bare and unexported. The underscore is reserved by an
  earlier contract for a stronger promise about two specific symbols.
- How the migration is divided into commits, beyond the requirement that the
  wording change precedes the removals, is left to task breakdown.
