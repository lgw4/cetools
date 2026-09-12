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

**Independent Test**: Run the existing suites, unedited, against each commit in
the migration sequence, and alongside them the data-derived comparison of
FR-016b. The suites matter because they were written before this feature existed
and are not permitted to be adjusted for it, but they are not on their own
enough to support the claim: they pin a small minority of the wordings the
parsers emit, and the golden corpus pins none of them (FR-016a). A commit that
changes a report may well leave the suites green, so the comparison is what
actually tests this story and the suites are what stop it being tuned.

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
- **A site that already reports at a location its surroundings would not
  produce.** One unrecognized-key call sits inside a nested table but reports
  its stray keys at the bare top-level location, where every other such call in
  the five modules prefixes with its enclosing location. Converting it on the
  carrier its surroundings suggest would change a reported location, which
  FR-014 forbids. It MUST therefore be converted on the carrier that reproduces
  today's location, with a note in the code saying why, and the question of
  whether the location is right is recorded in the inventory rather than
  settled. FR-002's rule that parsers descend by deriving a child carrier is not
  weakened by this: the site still derives rather than concatenating, it simply
  derives from the carrier that preserves its behavior.
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
  recorded through the carrier, including the one hundred and two bespoke
  problems no named check covers — a range that will not parse, an amount of
  zero, a name absent from a registry, a band set with the wrong number of
  unbounded bands, and the rest. A bespoke site MUST supply only what was found
  and what was expected; the file name and the location come from the carrier.
- **FR-010**: The header-key constant, presently written out identically in five
  modules, MUST collapse to one definition.
- **FR-011**: After the migration, no function in the rules-data parsing layer
  may take the file name as a parameter. The parsing layer is the thirteen
  whole-file entry points and everything beneath them. One counted function is
  excluded and stays as it is: the helper that builds the problem for a file
  that could not be opened at all, which FR-012 places outside the carrier
  because there is no carrier to report through. The guard of FR-022 MUST name
  that one exclusion and state FR-012 as its reason, so the exception is visible
  rather than assumed.

#### What stays outside the carrier

- **FR-012**: Problems that are not about a location inside one file MUST stay
  outside the carrier. This covers the twenty-nine problems the loader and its
  file-reading helpers build: the three that name a glob rather than a real
  file, the two that concern a pair of files at once, the problems raised when a
  file cannot be read, listed, or is not a regular file, and every other
  cross-file rule whose problem does not name a point inside one named file. The
  loader already carries a written explanation of why folding two file names
  into one was rejected; that explanation stands and this feature MUST NOT
  weaken it.
- **FR-012a**: The test is where a problem points, not which rule produced it. A
  cross-file rule that reports at a location inside one named file — the
  class-effect check, which reports at a nested effect's `class` key — is inside
  the carrier's territory, is recorded through a carrier the loader builds for
  that file, and is counted among the problems FR-009 covers rather than among
  the twenty-nine of FR-012. A rule is outside only when the problem it builds
  cannot name one file and one location within it.
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
- **FR-016a**: Those corpora are necessary evidence for FR-014 but come nowhere
  near sufficient, and the feature MUST NOT rest its central claim on them
  alone. The parsers emit **77** distinct `expected` wordings. The frozen
  corpora pin **7** of them as exact strings and a further ten only as
  substrings, leaving **60 unpinned by any test in the tree**. The golden
  corpus, which the user stories and SC-001 name first, pins **none**: it
  captures generator output and contains no validation text at all. The
  unpinned wordings are concentrated in exactly what this migration rewrites —
  the registry parser's wordings are entirely unpinned, and the highest-traffic
  strings are the least covered, with one array wording built at thirteen sites
  and one table wording at eight, none of them pinned anywhere.
- **FR-016b**: Every commit in the sequence MUST therefore also be checked by a
  comparison that derives its inputs from the shipped data files rather than
  from what anyone thought to test: each file broken every way the checks can
  detect, every resulting problem recorded, and the whole set compared before
  and after the commit. An identical result is the pass condition, and it is not
  optional for any commit. The comparison is a verification step, not a
  committed corpus: a corpus that can be adjusted to accommodate a change stops
  being evidence, which is FR-016's own reasoning applied to any new corpus this
  feature might add. Because it is not committed, it is also not enforced by
  anything automatic, and a commit that skips it has no evidence behind its
  claim rather than weak evidence.
- **FR-017**: The cross-reference check in the skills parser MUST keep its
  current gate, which runs the check only when the file has produced no problems
  at all, so that one bad field elsewhere in the file still skips it. Whether
  that gate is correct is recorded for later (FR-021), not decided here.
- **FR-018**: This feature is structural throughout. No commit may carry a
  behavioral change. Adding the eighth check is structural on the same terms:
  it replaces copies of an idiom with one definition that reproduces each
  converted site's current wording exactly (FR-008), so it changes what the
  source says and not what the tool reports.
- **FR-018a**: Because nothing a library user or a data-file author can see
  changes, no commit in this feature carries a `CHANGELOG.md` entry. The
  project's rule that every user-visible change ships an entry is satisfied
  because there is no user-visible change, and an entry claiming one would put
  noise in a document that exists to tell readers what changed for them.

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
  optional and the feature is not complete without it. Closure MUST be
  demonstrated the same way the relaxation was made visible: the guard is back
  to the single-definition rule, the expiry note is gone, and the guard's own
  planted-violation self-test shows it can still fail.
- **FR-021**: An inventory of wording inconsistencies and questionable gates
  found while reading the sites MUST be delivered with this feature. Each entry
  names a concrete site, states the question, and carries a stable identifier,
  because code that deliberately preserves an anomaly cites its entry by name.
  Nothing in the inventory may be acted on in this feature, so that the
  structural argument and the wording argument never share a review. "Acted on"
  means changing what a site reports or which rule it applies. Adding a
  parameter whose only purpose is to let two sites keep saying the different
  things they already say preserves the inconsistency rather than resolving it,
  and is therefore required by FR-014 rather than forbidden by this
  requirement.

#### Guarding the result

- **FR-022**: A guard test MUST hold the four counts after the migration: zero
  parsing-layer functions taking a file name, exactly one definition of the
  header-key constant, one problem-passing convention, and zero remaining copies
  of the non-empty-array idiom. The reasoning is the one the project used the
  first time it added such a guard: the duplication it removed had accumulated
  one locally reasonable copy at a time, and a comment would not have stopped
  the next one.
- **FR-023**: Each of the four counts MUST itself be demonstrably able to fail,
  shown by its own test that plants the shape that count forbids and confirms
  the guard rejects it. One self-test covering the guard as a whole is not
  enough: four rules that can only be shown to fail together can hide a rule
  that never fires. This follows the self-test obligation every existing guard
  in this project carries.

#### Documentation and tests

- **FR-024**: This feature MUST write its own contract document for the carrier:
  what it holds, how a child is derived, how a scope is asked whether it failed,
  what it explicitly does not describe, and every anomaly it deliberately
  preserves rather than normalizes, so that a later reader cannot mistake a
  preserved wart for an oversight and quietly fix it.
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
  through array indices, including the top-of-file case where the parent
  location is empty and a naive join would emit a leading dot; a problem
  collection genuinely shared between a parent and a child rather than copied;
  and per-scope failure reported correctly when a sibling scope has failed and
  this one has not.

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

- **SC-001**: The full test suite passes at every commit in the sequence; the
  golden and contract corpora are byte-identical to their state before the
  feature began; and the data-derived comparison of FR-016b reports no
  difference at any commit. All three are required. The first two alone would be
  satisfied by a commit that silently reworded any of the sixty wordings no test
  pins.
- **SC-002**: Functions in the rules-data parsing layer that take the file name
  as a parameter go from **53 to 1**, a removal of 52. The 53 are: 20 in the
  chargen parser, 12 in the career parser, 7 in the registry parser, 7 in the
  field-check vocabulary, 4 in the names parser, and 3 in the rules module. The
  one that remains is the unopenable-file helper, which FR-011 excludes and
  FR-012 explains: it builds a problem that names no location inside any file,
  so there is no carrier for it to report through. Reporting 53 → 0 would
  require either dragging that problem into a carrier that cannot describe it or
  quietly not counting it, and the spec does neither. (A generator helper
  outside the parsing layer also takes a file name for a runtime table lookup;
  it is not in scope and is not among the 53.)
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
  array" guards are converted to the same check alongside them, giving nineteen
  call sites in total, but they are **not** part of the count of 15 and the
  guard of FR-022 does not measure them: they do not contain the idiom, and
  three of the four accept an empty array today where every one of the 15
  rejects it. Those three MUST keep accepting it — converting them to a
  non-empty check would start reporting a file that validates clean today, which
  FR-014 forbids. The eighth check therefore has to be able to express both
  rules, and the disagreement is recorded in the inventory rather than settled.
- **SC-006**: All **102** problems constructed by hand inside the per-file
  parsers (40 chargen, 37 career, 16 registry, 7 names, 2 task parameters) are
  recorded through the carrier, and **0** of the **29** cross-file problems are.
  The figure is exact, not approximate: an approximate target cannot be held by
  a guard or checked by a reviewer. The class-effect check is counted in the 102
  and not in the 29, per FR-012a.
- **SC-007**: All **17** local emptiness questions across **16** functions are
  converted to an explicit scope, and each preserves its current meaning. An
  "emptiness question" is a test of the problem accumulator a function threads
  through its own parsing, asked to decide what that function does next. A local
  list built for one loop and inspected immediately — such as the per-specialty
  list the skills parser collects and reports in one go — is not one of the 17
  and does not become a scope; it is an ordinary collection whose contents reach
  the accumulator by the same path they do today. Under the looser reading that
  counts any list of problems tested for truth, the number would be 18, and
  naming which reading applies is the difference between a count a reviewer can
  check and one they can only re-argue.
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
  of problems in different insertion orders produce the same report. The
  assumption carries less weight than it first appears to, and deliberately so:
  problems are collected per file and folded into the run's list a file at a
  time, exactly as they are today, so no migration step can make two files
  interleave. The sort therefore does no more work after this feature than
  before it, and the assumption has to hold only for pairs of problems within
  one file. Where it is load-bearing at all, a failure surfaces as a difference
  in the comparison FR-016a requires, which reaches the orderings the frozen
  corpora never exercise. Either way the signal is to stop and reconsider, never
  to adjust the tests or to move the sort.
- The three deeper-than-file scopes are the mishap-effect parser, the
  surname-entry parser, and the band-list parser. The rule for choosing any
  site's scope is the one FR-005 states — the scope that preserves the site's
  current meaning, which is decided by reading which list the site tests today,
  not by where the site happens to sit. A count found wrong while reading the
  code is corrected in the commit that finds it, in either direction: if a
  fourth deeper-than-file scope turns up it is converted the same way and
  SC-007's count rises, and if one of the three turns out on reading to be a
  file-level question it is converted as one and the count falls. Neither case
  is a licence to change what a site means; both are a licence to correct a
  number the spec got wrong.
- "One problem-passing convention" means the carrier's shared collection. A
  function may still return the parsed value or `None`, and `None` remains the
  caller's failure signal; what goes away is the problem list travelling
  separately.
- The inventory is a document in this feature's directory, not a tracked issue
  list, matching how this project has recorded deferred questions before.
- No third-party dependency is added. The carrier is ordinary library code, in
  keeping with the constitution's preference for the standard library.
- No performance requirement is stated, and that is deliberate rather than an
  oversight. Validation runs once over the packaged files at load or on an
  explicit validate command, and a carrier per descent step is a small object
  where the code today builds a string. Neither the absence of a budget nor the
  change in allocation shape is expected to be observable, and if that turns out
  to be wrong it is a new problem to specify, not one this feature silently
  accepted.
