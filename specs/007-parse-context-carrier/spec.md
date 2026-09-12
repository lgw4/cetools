# Feature Specification: Parse Context Carrier

**Feature Branch**: `007-parse-context-carrier`

**Created**: 2026-09-11

**Status**: Draft

**Input**: User description: "The rules-data parsers read TOML files by
descending into them, and at every level they carry three things by hand: which
file is open, where in that file the reader currently sits, and the running list
of problems found. Today that carrying is done by passing arguments. The file
name appears in 53 function signatures, the location is rebuilt by string
concatenation at each level of descent, and the problem list is handed in for
the callee to mutate, or handed back, or smuggled out as a return value
pretending to be a parsed result. All three conventions are in use right now,
sometimes in the same function four lines apart. This feature replaces the
hand-carrying with a single carrier the parsers descend with, and the field
checks that exist today become things that carrier does rather than free
functions the caller must supply context to."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The reports do not move (Priority: P1)

Someone who edits a rules data file runs the tool, gets a list of problems, and
fixes them. They do this the day before this feature lands and the day after.
Nothing they see differs: the same problems, naming the same files, at the same
dotted locations, with the same words for what was found and what was expected,
listed in the same order.

**Why this priority**: This is the whole promise. The feature buys nothing a
data-file author can see, so the only way it can fail them is by changing
something. Every other story in this feature is worthless if this one does not
hold.

**Independent Test**: Run the existing golden and contract suites, unedited,
against each commit in the migration sequence. A commit that changes a report
fails them. The suites are the evidence precisely because they were written
before this feature existed and are not permitted to be adjusted for it.

**Acceptance Scenarios**:

1. **Given** a rules data file with several problems spread across different
   fields, **When** the tool validates it after the migration, **Then** the
   reported problems are byte-identical to what the same file produced before
   the migration, including their order.
2. **Given** a skills registry file whose dependency graph contains a cycle and
   which also has one unrelated bad field, **When** the tool validates it,
   **Then** the cycle is still not reported, because the unrelated bad field
   still suppresses the cross-reference check exactly as it does today.
3. **Given** two career files that declare the same career name, **When** the
   tool validates them, **Then** the problem still names one file in its file
   field and both files in its found text, unchanged by this feature.

---

### User Story 2 - A contributor stops threading context (Priority: P1)

Someone adds a new checked field to a data-file kind. Today they must find the
enclosing function's `file` parameter, build the dotted location by
concatenating the parent's location with the new key, decide which of three
problem-passing conventions the surrounding code uses, and match it. After this
feature they ask the carrier for the check, and the file name, the location, and
the collection are already correct because the carrier descended with them.

**Why this priority**: This is the value the feature actually delivers, and it
is what justifies the churn. It also cannot be delivered halfway: a parser that
still takes a file name is a parser where the old habit still reads as normal.

**Independent Test**: Add a checked field to one data-file kind on a scratch
branch and confirm the diff contains no file name, no string concatenation for
the location, and no choice of problem-passing convention.

**Acceptance Scenarios**:

1. **Given** a parser function that reads a nested table, **When** it descends
   into a child key, **Then** it derives a child carrier rather than building a
   location string.
2. **Given** a field that must hold a non-empty array, **When** the parser
   checks it, **Then** it calls the carrier's array check rather than writing
   the fifteen-times-repeated idiom a sixteenth time.
3. **Given** a problem no named check covers, such as a range that will not
   parse or an amount of zero, **When** the parser reports it, **Then** it
   reports through the carrier and supplies only what is found and what was
   expected.

---

### User Story 3 - A reviewer reads the migration one parser at a time (Priority: P2)

Someone reviewing this work does not face a single commit that rewrites five
parsers. They see the carrier arrive first, delegating to the checks that
already exist so that nothing can have changed. Then they see one parser
converted per commit, each with the full suite green. Then they see the old path
deleted.

**Why this priority**: The change touches roughly a hundred problem sites across
five modules. A review that cannot be done in pieces will not be done carefully,
and "no report changes" is a claim that only survives careful review.

**Independent Test**: Check out each commit in the sequence and run the full
suite; every one passes. Check each commit's diff and confirm it changes either
structure or behavior, never both.

**Acceptance Scenarios**:

1. **Given** the commit that introduces the carrier, **When** the suite runs,
   **Then** it passes, because the carrier delegates to the existing checks and
   no call site has moved yet.
2. **Given** any commit in the per-parser sequence, **When** the suite runs,
   **Then** it passes.
3. **Given** the final commit, **When** the suite runs, **Then** it passes and
   the superseded path no longer exists in the source tree.

---

### User Story 4 - Wording problems are written down, not fixed (Priority: P3)

While converting roughly a hundred hand-built problem sites, whoever does the
work will notice wordings that disagree with each other, and at least one gate
that looks wrong. None of it is changed here. All of it is written into an
inventory delivered with the feature, so the next reviewer inherits a list
rather than a memory.

**Why this priority**: It costs little and protects the central claim. A feature
that promises "nothing the tool reports changes" cannot also quietly improve a
message. Separating the two keeps the structural argument reviewable on its own
terms, which is the same reason the project already forbids mixing structural
and behavioral changes in one commit.

**Independent Test**: The inventory exists as a delivered document, every entry
names a concrete site, and no entry has been acted on in this feature's diff.

**Acceptance Scenarios**:

1. **Given** two sites that state the same rule in different words, **When** the
   migration converts them, **Then** both keep their current words and both are
   recorded in the inventory.
2. **Given** the cross-reference gate that skips on any unrelated problem in the
   file, **When** the migration converts its parser, **Then** the gate behaves
   exactly as it does today and the question of whether it should is recorded in
   the inventory.

---

### Edge Cases

- **A sibling's failure must not be mistaken for this scope's failure.** Once
  problems accumulate into one shared collection, the seventeen places that
  today test their own local list for emptiness would instead be testing the
  whole run. Three of these sit below file level, at one table or one array
  element, and are the likeliest to be missed: a mishap effect, a surname entry,
  and a band list. A fourth — the cross-reference gate in the skills parser —
  must keep asking about the whole file, because that is what it asks today.
- **Insertion order changes and must not matter.** A shared collection appends
  in descent order rather than in each fragment's local order. The loader sorts
  every problem once before reporting, which is what makes the change
  unobservable. Nothing in the migration may move that sort, bypass it, or add a
  reporting path that skips it.
- **A problem about a file that is not one file.** Three problems name a glob
  (`careers/*.toml`, `names/surnames-*.toml`) rather than a real file, and two
  concern a pair of files at once, naming one in the file field and both in the
  found text. A carrier whose meaning is "somewhere inside one file" cannot
  describe these, so they stay outside it.
- **A problem about a file that could not be opened at all.** An unreadable
  file, an unlistable directory, and a path that is not a regular file are
  reported before any parse begins, so there is no carrier to report through.
- **The duplication guard during the transition.** For the duration of the
  migration, each check exists both as a free function and as a carrier
  behavior. The existing guard that forbids a check being defined more than once
  must be made to tolerate this deliberately, with an expiry, and the final
  commit must restore it to the single-definition rule.

## Requirements *(mandatory)*

### Functional Requirements

#### The carrier

- **FR-001**: A single carrier MUST hold the three things the parsers carry by
  hand today: the name of the file being parsed, the dotted location of the
  point currently being read, and the collection of problems found so far.
- **FR-002**: The carrier MUST be able to produce a child carrier for a nested
  key and for an indexed array element, sharing the parent's file name and
  problem collection and extending the parent's location. Parsers MUST descend
  by deriving a child carrier, never by concatenating location strings at the
  call site.
- **FR-003**: The locations a derived carrier produces MUST be identical to the
  strings the current concatenation produces, including the dot separator for a
  nested key, the bracketed index for an array element, and the empty parent
  location at the top of a file (so that a top-level key's location is the bare
  key, not a leading dot).
- **FR-004**: The problem collection MUST be genuinely shared between a parent
  carrier and every carrier derived from it, so that a problem recorded at any
  depth reaches the one collection the loader reports from.
- **FR-005**: The carrier MUST be able to report whether any problem has been
  recorded **within a named scope**, independently of problems recorded
  elsewhere in the run. The seventeen sites that today test a local list for
  emptiness MUST each be converted to the scope that preserves its current
  meaning, which is the file for fourteen of them and a smaller fragment for
  three.

#### What goes through the carrier

- **FR-006**: The carrier MUST cover the thirteen entry points that parse a
  whole rules-data file and every function beneath them. Those entry points are
  the task-parameters parser, the characteristics, skills, and benefits registry
  parsers, the given-names and surnames parsers, the career parser, and the six
  chargen parsers (draft table, aging table, mishap table, background skills,
  medical tiers, chargen parameters).
- **FR-007**: The seven named field checks that exist today MUST become
  behaviors of the carrier: the integer check with an optional minimum, the
  non-empty-string check, the required-boolean check, the dice-notation check,
  the table check, the optional-boolean check, and the unrecognized-key check.
- **FR-008**: An eighth check MUST be added for "this field must hold a
  non-empty array", replacing the fifteen hand-written copies of that idiom. It
  MUST reproduce each converted site's current wording for what was found
  (`missing`, `an empty array`, or the data file's own word for the wrong type)
  and for what was expected.
- **FR-009**: Every problem stated about something inside a single file MUST be
  recorded through the carrier, including the roughly one hundred bespoke
  problems no named check covers — a range that will not parse, an amount of
  zero, a name absent from a registry, a band set with the wrong number of
  unbounded bands, and the rest. A bespoke site MUST supply only what was found
  and what was expected; the file name and the location come from the carrier.
- **FR-010**: The header-key constant, presently written out identically in five
  modules, MUST collapse to one definition.
- **FR-011**: After the migration, no function in the rules-data parsing layer
  may take the file name as a parameter.

#### What stays outside the carrier

- **FR-012**: Problems that are not about a location inside one file MUST stay
  outside the carrier. This covers the twenty-nine problems the loader and its
  file-reading helpers build: the three that name a glob rather than a real
  file, the two that concern a pair of files at once, the problems raised when a
  file cannot be read, listed, or is not a regular file, and every other
  cross-file rule. The loader already carries a written explanation of why
  folding two file names into one was rejected; that explanation stands and this
  feature MUST NOT weaken it.
- **FR-013**: The carrier's meaning MUST remain "a point inside one named file".
  It MUST NOT be extended to describe a glob, a pair of files, or an absent file.

#### Preserving behavior

- **FR-014**: Nothing the tool reports may change: the same file, the same
  location, the same wording of what was found and what was expected, in the
  same order, for every input.
- **FR-015**: The single sort the loader performs over all problems before
  reporting MUST remain exactly where it is. It is load-bearing for this
  feature: it is what erases the change in insertion order that a shared
  collection introduces. No commit in this feature may move it, bypass it, or
  introduce a reporting path that does not pass through it.
- **FR-016**: The existing golden and contract test corpora MUST NOT be edited
  to accommodate this work. A change that requires editing them is a change this
  feature forbids.
- **FR-017**: The cross-reference check in the skills parser MUST keep its
  current gate, which runs the check only when the file has produced no problems
  at all, so that one bad field elsewhere in the file still skips it. Whether
  that gate is correct is recorded for later (FR-021), not decided here.
- **FR-018**: This feature is structural throughout. No commit may carry a
  behavioral change.

#### Delivery shape

- **FR-019**: The work MUST land as a sequence of commits that are each green
  and each independently reviewable: first the carrier, delegating to the checks
  that exist so that nothing can have changed; then one parser at a time; then a
  final commit deleting the superseded path.
- **FR-020**: The guard that forbids a field check being defined more than once
  MUST be relaxed deliberately and visibly for the duration of the migration,
  during which each check exists in two forms, and MUST be restored to the
  single-definition rule by the final commit. The relaxation MUST state in the
  guard itself that it is temporary and what closes it. The final commit is not
  optional and the feature is not complete without it.
- **FR-021**: An inventory of wording inconsistencies and questionable gates
  found while reading the sites MUST be delivered with this feature. Each entry
  names a concrete site and states the question. Nothing in the inventory may be
  acted on in this feature, so that the structural argument and the wording
  argument never share a review.

#### Guarding the result

- **FR-022**: A guard test MUST hold the four counts after the migration: zero
  parsing-layer functions taking a file name, exactly one definition of the
  header-key constant, one problem-passing convention, and zero remaining copies
  of the non-empty-array idiom. The reasoning is the one the project used the
  first time it added such a guard: the duplication it removed had accumulated
  one locally reasonable copy at a time, and a comment would not have stopped
  the next one.
- **FR-023**: The guard MUST itself be demonstrably able to fail, shown by a
  test that plants the shape the rule forbids and confirms the guard rejects it,
  following the self-test obligation every existing guard in this project
  carries.

#### Documentation and tests

- **FR-024**: This feature MUST write its own contract document for the carrier:
  what it holds, how a child is derived, how a scope is asked whether it failed,
  and what it explicitly does not describe.
- **FR-025**: The existing validation-vocabulary contract MUST keep authority
  over the wording of the original seven checks, because that wording is exactly
  what this feature promises not to change. It MUST receive a single added line
  noting that its signatures are superseded by the carrier contract, and no
  other edit.
- **FR-026**: The direct tests of the seven checks MUST keep transcribing the
  vocabulary contract row by row, adapted to the new call shape. They MUST NOT
  be thinned out because a carrier now supplies the context.
- **FR-027**: A new test suite MUST cover what only a carrier can get wrong: a
  location built correctly across nested descent through several levels and
  through array indices, a problem collection genuinely shared between a parent
  and a child rather than copied, and per-scope failure reported correctly when a
  sibling scope has failed and this one has not.

### Out of Scope

- **FR-028**: This feature MUST NOT change any reported wording, MUST NOT change
  any reported order, MUST NOT change the cross-file rules or the shape of the
  problems they produce, MUST NOT alter which fields are checked or what they
  are checked against, MUST NOT change the public library surface or the CLI,
  and MUST NOT act on any entry in the inventory it delivers.

### Key Entities

- **Parse context (the carrier)**: The thing a parser descends with. Holds one
  file name, one dotted location, and one shared problem collection; can derive
  a child for a key or an index; can perform each field check; can record a
  bespoke problem; can say whether a named scope has failed.
- **Problem**: One statement that something in the data is wrong, naming a file,
  a location, what was found, and what was expected. Unchanged by this feature.
- **Scope**: A region of a file over which the question "did anything here fail"
  is asked. Fourteen of the seventeen existing questions scope to the whole
  file; three scope to a single table or a single array element.
- **Field check**: A named decision about whether one field holds what the rules
  require. Seven exist; an eighth is added here. After this feature they are
  reached through the carrier rather than called as free functions with context
  passed in.
- **Inventory**: A delivered list of wording inconsistencies and questionable
  gates observed during the migration and deliberately not fixed by it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full test suite passes at every commit in the sequence, and
  the golden and contract corpora are byte-identical to their state before the
  feature began.
- **SC-002**: Functions in the rules-data parsing layer that take the file name
  as a parameter go from **53 to 0**. The 53 are: 20 in the chargen parser, 12
  in the career parser, 7 in the registry parser, 7 in the field-check
  vocabulary, 4 in the names parser, and 3 in the rules module. (A generator
  helper outside the parsing layer also takes a file name for a runtime table
  lookup; it is not in scope and is not counted.)
- **SC-003**: Definitions of the header-key constant go from **5 to 1**. The 5
  are in the career, chargen, names, registry, and rules modules.
- **SC-004**: Conventions for moving problems from callee to caller go from **3
  to 1**. The 3 in use today are: a caller-owned list passed in as a parameter
  and appended to; a list returned as the function's entire result; and a list
  returned alongside the parsed value in a pair. The draft-table parser uses two
  of the three four lines apart.
- **SC-005**: Hand-written copies of the non-empty-array idiom go from **15 to
  0**. The 15 are: 7 in the chargen parser, 5 in the career parser, 2 in the
  names parser, and 1 in the registry parser. Four further bare "must be an
  array" guards are converted alongside them.
- **SC-006**: All **~102** problems constructed by hand inside the per-file
  parsers (40 chargen, 37 career, 16 registry, 7 names, 2 task parameters) are
  recorded through the carrier, and **0** of the **29** cross-file problems are.
- **SC-007**: All **17** local emptiness questions across **16** functions are
  converted to an explicit scope, and each preserves its current meaning.
- **SC-008**: A contributor adding a checked field to any data-file kind writes
  no file name, no location string, and makes no choice of problem-passing
  convention.
- **SC-009**: The guard holding SC-002 through SC-005 fails when the shape it
  forbids is planted, demonstrated by its own self-test.

## Assumptions

- The thirteen whole-file entry points and everything beneath them are the
  carrier's territory. The loader that composes files, resolves overrides, and
  applies cross-file rules is not, and keeps building its problems as it does
  today.
- Feature 006 explicitly deferred this work: its FR-020 states that giving the
  file-and-path pair a carrier of its own was out of scope, and its contract
  repeats that the vocabulary "never builds a path; it receives the finished
  one". This feature reverses that deferral on purpose, which is why the older
  contract is annotated rather than rewritten.
- The loader's single sort over all problems is assumed to be a total order over
  everything a report can contain, so that two runs which produce the same set
  of problems in different insertion orders produce the same report. If that
  assumption fails for any pair of problems, the failure surfaces as a golden or
  contract test failure during the migration, which is the signal to stop and
  reconsider rather than to adjust the tests.
- The three deeper-than-file scopes are the mishap-effect parser, the
  surname-entry parser, and the band-list parser. If reading the code during
  implementation turns up a fourth, it is converted the same way and the count
  in SC-007 is corrected in the same commit.
- "One problem-passing convention" means the carrier's shared collection. A
  function may still return the parsed value or `None`, and `None` remains the
  caller's failure signal; what goes away is the problem list travelling
  separately.
- The inventory is a document in this feature's directory, not a tracked issue
  list, matching how this project has recorded deferred questions before.
- No third-party dependency is added. The carrier is ordinary library code, in
  keeping with the constitution's preference for the standard library.
