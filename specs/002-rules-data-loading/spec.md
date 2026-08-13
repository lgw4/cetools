# Feature Specification: Validated Rules Data Loading

**Feature Branch**: `002-rules-data-loading`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Decisions brief: rules-data-loading. The second of five MVP
features for cetools. Replaces the minimal, single-purpose data reading the dice/task
engine shipped with a validated loader for all rules content, and delivers the compact
table notation career tables are written in. Owns the shape of every rules data file:
the career schema, and the shared registries that give names meaning (skills,
characteristics, benefits). Ships one complete, SRD-faithful military career as its
reference, chosen because a commission, an officer rank ladder, rank bonuses, and a
characteristic-gated advanced table stress the schema hardest. Meaning in the notation
comes from position: the table an entry appears in fixes how it is read, and each
context validates against its own registry; skills carry an optional parenthetical
specialty parsed into base and specialty. Validation is strict in both directions that
hand-authored files fail: unrecognized names are errors and unrecognized keys are
errors, every problem in a data set is collected and reported together, and any problem
means the whole data set fails to load. House rules enter only by an explicitly supplied
override location that mirrors the packaged layout and may be partial, replacing whole
files; because a data set can then mix sources, the loader reports the provenance of
what it loaded alongside the seed, fingerprinting anything overridden. Every data file
declares its schema version. A validation command validates the packaged data set, or an
override composed over it, in both output modes with meaningful exit codes."

## Clarifications

### Session 2026-08-13

- Q: When a check result is rendered, should the provenance appear even for a plain
  packaged load, given that the previous feature's committed reference outputs pin both
  output modes byte for byte? (FR-037 vs SC-009) → A: Provenance always renders, including
  for a packaged load; the reference outputs committed with the previous feature are
  regenerated in this feature, and SC-009 is narrowed to pin the resolution outcome rather
  than the whole byte stream.
- Q: When the validation command is pointed at a single file rather than a directory, how
  does the system decide which packaged file that file stands in for? (FR-040) → A: From
  the file's basename matched against the packaged layout, ignoring the directory it sits
  in; a matching basename is a replacement, a non-matching one an addition.
- Q: Is a career identified by its filename or by a name declared inside the file, and what
  happens when two careers declare the same name? (FR-019a, FR-032) → A: The filename is
  the composition identity and the declared name is a human label; two careers in force
  declaring the same name is a validation error naming both files.
- Q: Are the numeric tables, mustering-out cash and the throw targets, written in the
  compact notation or as plain values? (FR-004a, FR-017) → A: Plain values typed by their
  position in the schema; the notation covers only tables that mix kinds of thing in one
  cell, and the schema states which fields bear notation.
- Q: Is the declared schema version one number for the whole schema, or one per kind of
  file? (FR-002a) → A: One per kind of file, each checked against the version supported for
  that kind, so a change to one kind does not invalidate untouched files of another.

### Session 2026-08-13 (requirements checklist review)

Raised by `checklists/rules-data.md` after planning, and resolved before task generation.

- Q: FR-029 requires an override to mirror the packaged layout, but the clarified FR-040a
  positions a single file by its basename alone. For a file sitting outside the mirrored
  layout these give opposite outcomes, a replacement under one reading and an addition
  under the other. Which governs? (CHK015) → A: The basename governs, everywhere. Layout
  mirroring becomes a recommendation rather than an obligation, which is the only reading
  under which FR-040's promise that validation reports what a run would do holds in every
  case.
- Q: Provenance rests its packaged case on the package version determining content
  exactly, but nothing requires that version to be reported. Should it be? (CHK022) → A:
  Yes. Provenance carries the package version in both output modes, so that the reported
  provenance is a complete reproducibility key rather than half of one.
- Q: A file in an override location that is not a rules data file currently has no effect
  and is named nowhere. Is that intended? (CHK019) → A: No. It is named as ignored wherever
  provenance is reported, and does not fail the load, for the reason FR-032 gives about a
  misspelled stem: a misspelled extension is the same mistake, and FR-032 answers such a
  mistake with visibility rather than rejection. Rejection was considered first and dropped
  because it fails a load over files the author did not write. Files whose names begin with
  a dot are passed over in silence, being made by tools rather than authored.
- Q: FR-033a puts the package version into rendered output, which would embed a CalVer
  string in every committed reference output and rewrite them all on each release. How is
  that handled? (raised while amending) → A: Reference outputs hold the version as a
  placeholder substituted at comparison time, so a release changes none of them, and the
  reported version is asserted against the installed package version directly instead.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Resolve against trustworthy rules content (Priority: P1)

A referee runs a check, and the numbers behind it come from rules data that was proved
well-formed before any of it was used. Every name in that data was recognized, every key
in it was understood, and every file in it declared a shape the system knows how to
read. If any of that had failed, the run would have refused to start rather than quietly
resolving against a table with a hole in it.

**Why this priority**: Everything else in the MVP resolves against this data. Until the
loader can turn a data set into trustworthy rules content, or refuse to, the character
generator has nothing safe to build on and the existing engine is reading its parameters
through a validator that only understands one file. This story is the reason the feature
exists, and it is the only one that must ship for the feature to be worth anything.

**Independent Test**: Fully tested by loading the shipped data set and confirming every
part of it resolves, then by corrupting a copy of it in each distinct way a hand-authored
file can be wrong and confirming the load refuses. Delivers value on its own: the
existing task check keeps working, now through a loader that would catch a bad edit to
the data instead of absorbing it.

**Acceptance Scenarios**:

1. **Given** the data set as shipped, **When** it is loaded, **Then** every file in it
   resolves without error and the rules content it describes is available in full.
2. **Given** a data set in which one skill name is misspelled, **When** it is loaded,
   **Then** the load fails, naming the file, the location within it, the unrecognized
   name, and the registry the name was checked against.
3. **Given** a data set in which one key name is misspelled, **When** it is loaded,
   **Then** the load fails rather than silently ignoring the key and leaving the check
   it configures inoperative.
4. **Given** a data set in which one file declares a schema version the system does not
   support, **When** it is loaded, **Then** the load fails with a message naming the
   declared version and the version supported for that kind of file, and no attempt is made
   to interpret the file's contents.
5. **Given** an existing seed and check that resolved to a particular result before this
   feature, **When** the same seed and check are resolved through the new loader,
   **Then** the resolution outcome is identical, and the rendered output differs only by
   the provenance now reported alongside the seed.

---

### User Story 2 - Author rules data with fast, complete feedback (Priority: P2)

Someone writing rules data files by hand runs a single command and is told everything
wrong with what they have written: each problem located in its file, described in terms
of what was expected, and reported together in one pass rather than one at a time.

**Why this priority**: The next feature but one authors roughly two dozen career files
against this schema. Whether that work takes a day or a week is decided almost entirely
by how many edit-run cycles each file costs, and a loader that stops at the first problem
turns a file with six mistakes into six cycles. It is second only because the loader must
exist before there is anything to validate against.

**Independent Test**: Fully tested by running the command against the shipped data set
and seeing it pass, then against a file seeded with several distinct mistakes and
confirming that a single run reports all of them, each located. Delivers value on its
own as the authoring tool for all subsequent rules content.

**Acceptance Scenarios**:

1. **Given** no argument, **When** the validation command runs, **Then** it validates the
   data set as shipped and exits reporting success.
2. **Given** a file containing four distinct problems, **When** the validation command
   runs against it, **Then** all four are reported in that single run, each located in
   the file.
3. **Given** any data set with at least one problem, **When** the validation command
   runs, **Then** it exits with a non-zero status, and requesting machine-readable output
   does not change that status.
4. **Given** a request for machine-readable output, **When** the validation command runs
   against a data set with problems, **Then** each problem is emitted as structured data
   carrying its location and description, consumable without parsing prose.

---

### User Story 3 - Apply house rules without forking code (Priority: P3)

A referee who wants a different survival throw for one career writes that one file, points
the tool at the directory holding it, and everything else continues to come from the data
as shipped. Their file is held to exactly the same standard as a shipped one.

**Why this priority**: The project's data-driven principle promises that house rules
happen by editing or swapping data rather than by changing code, and until an override
path exists that promise is unhonored. It ranks below authoring because the schema and
its validation must be settled before user-supplied files can be judged against them.

**Independent Test**: Fully tested by supplying an override location containing a single
modified file, confirming that the modified content is in force, that every file absent
from the override still comes from the shipped data, and that a mistake in the supplied
file fails the load exactly as it would in a shipped file.

**Acceptance Scenarios**:

1. **Given** an override location containing one career file, **When** the data set is
   loaded, **Then** that file replaces the corresponding shipped file entirely and every
   other file comes from the shipped data.
2. **Given** an override location containing a file with an unrecognized name in it,
   **When** the data set is loaded, **Then** the load fails with the same diagnostics a
   shipped file would produce.
3. **Given** no override location, **When** the data set is loaded, **Then** no location
   outside the package is consulted, read, or searched.
4. **Given** an override file that changes only one value, **When** the data set is
   loaded, **Then** the whole file is taken from the override, so any shipped value the
   override file omits is absent rather than inherited.
5. **Given** an override location containing a career file with no packaged counterpart,
   **When** the data set is loaded, **Then** that career is added to the data set, and it
   is reported as added rather than as replacing anything.

---

### User Story 4 - Tell whether a result is reproducible (Priority: P4)

Someone handed a seed and a result can tell what data produced it: whether it came from
the data as shipped, in which case the seed and the package version reproduce it, or from
modified data, in which case they are told exactly what was modified.

**Why this priority**: Overrides break the guarantee that a seed plus a package version
determines an output, and the project treats reproducibility as both a feature and its
testing strategy. Reporting provenance converts a silent break into a visible one. It is
last because it has value only once overrides exist, but it is not optional: shipping
overrides without it would leave the reproducibility claim quietly false.

**Independent Test**: Fully tested by loading with and without an override and comparing
the reported provenance, then by altering the content of an override file at the same
location and confirming the reported provenance changes.

**Acceptance Scenarios**:

1. **Given** a load with no override, **When** provenance is reported, **Then** it
   identifies the data as the packaged data set, names the package version, and carries no
   per-file detail.
2. **Given** a load in which any file came from an override, **When** provenance is
   reported, **Then** it identifies which files came from the override and carries a
   fingerprint of their content.
3. **Given** two override files whose contents differ, **When** each is loaded from the
   same location in turn, **Then** the reported fingerprints differ.
4. **Given** identical override content presented at two different locations, **When**
   each is loaded, **Then** the reported fingerprints are equal, so the fingerprint
   describes content rather than where it was found.
5. **Given** any command that resolves against rules data, **When** it renders a result,
   **Then** the provenance appears alongside the seed in both output modes.

---

### Edge Cases

- What happens when an override location is supplied but does not exist, or exists and is
  empty? The first is a usage error naming the location; the second loads the shipped
  data set unchanged, and reports its provenance as packaged, because no file was
  overridden.
- What happens when an override file declares a schema version that is supported but the
  file is otherwise identical to the shipped one? It is still recorded as overridden,
  because provenance describes where content came from, not whether it differs.
- What happens when a career file names a specialty for a skill the registry says has no
  specialties, or a specialty the registry does not list for that skill? Both are
  validation errors, distinguishable from an unrecognized skill name.
- What happens when a bare skill name appears for a skill that does have specialties? It
  is valid, and remains distinguishable from a fully-specified reference so a later
  consumer can tell a choice is owed.
- What happens when the same name appears in two registries, once as a skill and once as
  a benefit item? Nothing: the table an entry appears in fixes which registry applies, so
  the two never compete.
- What happens when a data file is present but unreadable, or is not well-formed at all?
  It is a problem like any other, reported with its file named, and it fails the data set.
- What happens when a house rule needs one additional skill? The whole skills registry
  must be supplied in the override, because replacement is per file and never per key.
- What happens when an override filename is misspelled, so that it replaces nothing and is
  taken as new content? The data set gains it, and it is reported as an addition rather
  than a replacement, which is how the mistake becomes visible. The file the author meant
  to override remains in force as shipped.
- What happens when an added career file declares the same name as a packaged one, which
  is what a misspelled override filename produces? The data set fails to load, naming both
  files, because two careers answering to one name leave a later consumer nothing to choose
  between.
- What happens when an override location holds its files flat rather than mirroring the
  packaged directories? It composes identically, because a file is positioned by its
  basename and not by the directory it sits in. Mirroring the layout is worth doing for
  legibility and is not what makes composition work.
- What happens when a registry filename in an override is misspelled? Unlike a career, a
  registry cannot be added: only one of each registry may be in force. The data set fails
  to load naming the file, rather than admitting it as an addition and leaving the real
  registry silently in force.
- What happens when an override location holds a file that is not rules data, such as a
  house rule saved to the wrong extension or a README beside a rule set? The load succeeds
  and the file is named as ignored in the provenance report. The author who expected it to
  be in force sees it named and learns why it was not, which is the same bargain FR-032
  strikes for a misspelled filename: visibility rather than rejection.
- What happens when the file was made by a tool rather than written by the author, such as
  the metadata a file browser leaves in a directory it has opened? It is passed over in
  silence, because it names no mistake anyone made and a report listing it would be noise
  in every load. The line is drawn at the leading dot such files carry, not at a list of
  the tools that make them.
- What happens when a run would never have drawn on the file that is broken? It still
  fails, because a data set that failed only when the broken part was reached would fail
  differently from seed to seed.
- What happens when the validation command is pointed at a single file rather than a
  directory? It validates that file as though it were the sole member of an override,
  composed over the shipped data set. Its position in that override is taken from its
  basename alone, so the directory it happens to sit in is irrelevant: a basename matching
  a packaged file makes it a replacement for that file, and a basename matching nothing
  makes it an addition, reported as one.

## Requirements *(mandatory)*

### Functional Requirements

#### Data files and schema version

- **FR-001**: Every rules data file, whether shipped or user-supplied, MUST declare the
  schema version it was written against, and the system MUST reject a file that does not.
- **FR-001a**: Every rules data file MUST also declare which kind of file it is, from the
  closed set FR-002a names, and the system MUST reject a file that does not. The declared
  kind selects the schema the file is held to. Nothing outside the file may supply it:
  because a file is positioned by its basename alone (FR-029) and a basename matching
  nothing is admitted as an addition (FR-032), an added file has no directory and no
  matching packaged slot from which a kind could be inferred. Where a file does replace a
  packaged one, its declared kind MUST equal that file's kind, and a mismatch is a problem
  naming both kinds, which catches a file saved under the wrong name.
- **FR-002**: The system MUST refuse a file whose declared schema version it does not
  support, reporting the file, the version it declared, and the version the system
  supports for that file's kind, and MUST NOT attempt to interpret that file's contents.
  The refusal is the point: a file written for another shape must fail as a version
  mismatch and not as a cascade of confusing validation errors about individual keys.
- **FR-002a**: Schema versions MUST be counted per kind of file. There are five kinds, and
  the set is closed: the task parameters, the characteristics registry, the skills
  registry, the benefit items registry, and a career. The three registries are separate
  kinds rather than one, because their shapes differ and a change to one must not
  invalidate the others. Each kind declares and is checked against the version supported
  for that kind, and a change to one kind's shape MUST NOT invalidate a user-supplied file
  of a kind whose shape did not change. Every kind starts at the same version today, so
  this costs nothing now and is the whole of what the version field was justified on: a
  house rule overriding one career must survive a change to the registry schema it never
  touched.
- **FR-003**: The declared schema version MUST describe the shape of the file and MUST
  NOT be tied to, or inferred from, the package's own release version, which changes on
  every release for reasons that have nothing to do with file shape.

#### The compact notation

- **FR-004**: The system MUST read table entries written in a compact notation covering
  four forms: a check against a characteristic with a target ("INT 4+"), an adjustment to
  a characteristic ("STR +1"), a named grant with an explicit level ("Pilot 2"), and a
  bare name.
- **FR-004a**: The notation MUST apply only to entries in tables that mix kinds of thing in
  one cell: the personal, service, and advanced skill tables, the mustering-out benefits
  table, and the characteristic gate on a table. Purely numeric content, the mustering-out
  cash amounts and the target numbers of the throws, MUST be declared as plain values typed
  by their position in the schema and MUST NOT be routed through the notation. The schema
  MUST make plain which fields bear notation and which do not, so that a validation problem
  in a numeric field reports a bad number rather than an unrecognized entry form.
- **FR-005**: The meaning of a bare name MUST be fixed by the table it appears in, so
  that a bare name in a skill table denotes a skill and a bare name in a benefits table
  denotes a benefit item. Each table MUST validate a bare name against the registry
  appropriate to that table and no other, so that a skill name is never accepted because
  it happens to appear in the benefit items registry. A form that carries its own meaning
  rather than taking it from position is validated against the registry that form implies
  wherever it appears: a characteristic adjustment is checked against the characteristics
  registry in every context that admits it, including a benefits table.
- **FR-006**: A skill reference MUST be able to carry a specialty, written parenthetically
  after the skill name, and the system MUST resolve such a reference into a base skill and
  its specialty rather than treating the whole string as an opaque name.
- **FR-007**: The system MUST reject a specialty given for a skill the registry declares
  has none, and MUST reject a specialty the registry does not list for that skill, with
  the two reported distinguishably from an unrecognized skill name.
- **FR-008**: A skill reference naming a skill that has specialties but giving none MUST
  remain distinguishable from one that gives a specialty, so that a consumer can tell that
  a choice is owed. Without this the knowledge of which skills require choosing would have
  to live in engine code, which the data-driven principle forbids.
- **FR-009**: Every entry the notation admits MUST be rejected when malformed, reporting
  the entry as written and the forms that were acceptable in that position.
- **FR-009a**: Each notation-bearing field MUST admit a defined subset of the four forms,
  and a well-formed entry of a form the field does not admit MUST be rejected exactly as a
  malformed one is, per FR-009. There are three such subsets: a skill table entry and a
  rank bonus admit an adjustment, a grant, or a bare name; a mustering-out benefits entry
  admits an adjustment or a bare name; a table's characteristic gate admits a check and
  nothing else. Without a defined subset per field, FR-009's promise to report "the forms
  that were acceptable in that position" has nothing to report, and a check written into a
  skill table would pass unremarked.

#### Registries

- **FR-010**: The system MUST ship a registry of skills, a registry of characteristics,
  and a registry of benefit items, each as data.
- **FR-010a**: Four of the five kinds FR-002a names occur exactly once in a data set: the
  task parameters and the three registries. The system MUST reject a data set in which two
  files in force declare the same one of those kinds, naming both files, and MUST reject
  one in which any of them is absent. This is the registry analogue of FR-019b and exists
  for the same reason: a misspelled registry filename is admitted as an addition under
  FR-032, and without this check it would sit inert in the data set while the file it was
  meant to replace stayed silently in force, which is the failure the strictness elsewhere
  in this feature exists to remove.
- **FR-011**: The skills registry MUST declare, for each skill, whether it has specialties
  and which specialties are permitted.
- **FR-012**: The characteristics MUST be declared in data rather than known to the
  parsing code, because characteristic names are rules content and no rules content may be
  hard-coded in engine code.
- **FR-013**: The system MUST reject any name that its governing registry does not
  contain, reporting the file, the location within it, the name as written, and which
  registry it was checked against. Every name, in every registry, MUST be matched exactly
  and case sensitively: a registry entry is the spelling that data files are required to
  use, and case folding would quietly widen the notation, admitting a characteristic
  written `int` as readily as `INT` and leaving the registries describing less than they
  appear to.

#### Career file schema

- **FR-014**: A career file MUST declare the throws that govern a term of service.
  Qualification, survival, promotion, and re-enlistment are required. Commission is
  optional, absent for a career that offers no commission, and its absence is how such a
  career is expressed. The set of throw names is closed, so that a misspelled throw name is
  caught by FR-020 as an unrecognized key rather than admitted as a new throw. A throw
  declares the characteristic it is checked against and its target number as distinct typed
  fields, per FR-004a, rather than as a notation string. The characteristic is optional,
  absent for a throw that takes no characteristic modifier, which is how re-enlistment is
  thrown. The target is required and MUST be a positive integer, since a throw against a
  target of zero or less is not a throw.
- **FR-015**: A career file MUST declare its skill tables. Personal, service, and advanced
  are required; advanced education is optional, present for a career that offers it. The
  set of table names is closed, so that a misspelled table name is caught by FR-020 as an
  unrecognized key rather than admitted as a new table. Any table MAY be gated on a minimum
  characteristic score, since the source material restricts advanced training that way, and
  the gate is optional on every table rather than fixed to one of them. Every table MUST
  declare at least one entry; no maximum is imposed, because how a table is indexed belongs
  to the generator that rolls on it and fixing a length here would put a rules constant in
  engine code.
- **FR-016**: A career file MUST declare at least one rank ladder and MUST be able to
  declare more than one, so that a career with both an enlisted and an officer progression
  is expressible, with each rank carrying its position, its title, and optionally a bonus
  granted on reaching it. A ladder MUST carry at least one rank. Ladder names MUST be
  distinct within a career, and rank positions MUST be non-negative and distinct within
  their ladder; without both, a reference to a rank on a named ladder would not identify
  one rank, and a later consumer would have nothing defensible to choose between.
- **FR-017**: A career file MUST declare both its mustering-out cash table, whose entries
  are plain amounts, and its mustering-out benefits table, whose entries are written in the
  notation and validated per FR-005 and FR-009a. Both are required, both MUST declare at
  least one entry, and every cash amount MUST be a non-negative integer. As with the skill
  tables, no maximum length is imposed.
- **FR-018**: The system MUST ship one complete career that is faithful to the source
  material and that exercises every element of this schema, including a commission, a
  second rank ladder, at least one rank bonus, and a characteristic-gated table.
- **FR-019**: The system MUST reject a career file that omits any element FR-014 through
  FR-017 and FR-019a mark required, naming what is missing rather than failing later when
  the missing part is reached. Those requirements are the enumeration: the required
  elements are the declared name, the qualification, survival, promotion and re-enlistment
  throws, the personal, service and advanced skill tables, at least one rank ladder, and
  both mustering-out tables. The optional elements are the commission throw, the advanced
  education table, a gate on any table, and a bonus on any rank. SC-004 tests this
  enumeration by removing each required element in turn, so an element absent from it is an
  element nothing proves.
- **FR-019a**: A career file MUST declare a human-readable name for the career. That name
  is a label, not an identity: which packaged file an override file replaces is determined
  by filename alone, per FR-029, and never by the name declared inside. Composition must
  not require parsing a file to learn what it stands in for.
- **FR-019b**: The system MUST reject a data set in which two careers in force declare the
  same name, naming both files. Because a career is composed by filename, a misspelled
  override filename yields two careers rather than one, and without this check both would
  answer to the same name and a later consumer would have no defensible way to choose
  between them.

#### Validation and reporting

- **FR-020**: The system MUST reject any key it does not recognize, in any data file.
  This is the only check that catches a misspelled key name, which no registry can catch
  and which would otherwise leave the throw or table that key configures silently
  inoperative.
- **FR-020a**: The system MUST reject a data file it cannot read, and one that is not a
  well-formed document of its format, as a problem naming the file and locating the
  malformation as precisely as the format allows. Such a file contributes no content, and
  the remaining files in the data set MUST still be checked, so that a single unparseable
  file does not mask every other problem the run would have found.
- **FR-020b**: The system MUST reject a value whose type is not the one its position in
  the schema requires, reporting the type found and the type expected. This is the check
  that FR-004a's typing of plain numeric fields buys: a target written as a string reports
  a bad type at that field rather than being routed to the notation and reported as an
  unrecognized entry form.
- **FR-021**: The system MUST collect every problem it finds across the whole data set and
  report them together, rather than stopping at the first.
- **FR-022**: Every reported problem MUST identify the file it occurred in and its location
  within that file, and MUST state what was expected as well as what was found.
- **FR-023**: Validation performed when loading for use and validation performed on demand
  MUST be the same, so that a data set reported as valid always loads and a data set
  reported as invalid never does.

#### Loading and failure

- **FR-024**: The system MUST validate the entire data set whenever it loads, regardless
  of which parts of it a given operation would go on to use.
- **FR-025**: If any part of a data set is invalid, the system MUST fail to load the data
  set as a whole and MUST NOT make a valid subset of it available. A data set that quietly
  dropped a career would generate different characters for the same seed depending on
  which files happened to parse, which is a reproducibility failure disguised as
  resilience.
- **FR-026**: The system MUST NOT fall back to built-in values when data is missing,
  unreadable, or invalid.
- **FR-027**: The system MUST NOT search any location that the caller did not name. No
  configuration directory, environment location, or working-directory convention may
  contribute to a data set, because an automatically discovered file would silently change
  what a seed produces.

#### Overrides

- **FR-028**: The system MUST accept an explicitly supplied override location, and this
  MUST be the only way content that did not ship with the package enters a data set. An
  override location MAY be either a directory or a single file, and both compose by the
  same rule (FR-029), so that what the library accepts and what the validation command
  accepts are the same thing rather than two similar things.
- **FR-029**: An override location MAY be partial. Every file in it is positioned by its
  basename alone, whatever directory within the override it sits in: a file whose basename
  matches a packaged file replaces that file in its entirety, and a packaged file with no
  counterpart in the override is used as shipped. Mirroring the layout of the packaged data
  is RECOMMENDED for legibility and is not required for composition. Basename positioning
  is the general rule of which FR-040a is a consequence rather than an exception, and it is
  what makes FR-040's promise hold: were a directory keyed by path and a single file by its
  basename, the same file would be reported as a replacement by one and an addition by the
  other, and validation would not report what a run would do.
- **FR-029a**: Because the basename positions a file, basenames MUST be unique across the
  packaged layout, and the system MUST reject an override location containing two files
  that share a basename, naming both. Two files claiming one position leave nothing to
  decide between them.
- **FR-030**: The system MUST NOT merge an override file with the packaged file it
  replaces. Replacement is whole-file, so a value the override file omits is absent rather
  than inherited from the shipped file it stands in for.
- **FR-031**: An overriding file MUST be validated by exactly the same rules as a shipped
  file, including its declared kind, its declared schema version, its keys, and every name
  it contains. The one thing not required of it is the licensing header FR-046 requires of
  a shipped file, for the reason recorded there.
- **FR-032**: A file in the override location that corresponds to no packaged file MUST be
  added to the data set as new content, so that a house rule can introduce a career rather
  than only modify one. Because a misspelled filename is indistinguishable in itself from
  content added on purpose, the system MUST report an added file distinctly from a
  replaced one wherever it reports where data came from, so that an unintended addition is
  visible rather than silent. This is the one place where the strictness applied to
  unrecognized keys and unrecognized names is deliberately not applied to unrecognized
  filenames, and reporting is what pays for the exception.
- **FR-032a**: A file in an override location that is not a rules data file MUST be named
  as ignored wherever provenance is reported, and MUST NOT fail the load. FR-032 answers a
  misspelled filename by admitting it and reporting it rather than by rejecting it,
  reasoning that reporting is what pays for admitting an unrecognized filename at all. A
  misspelled extension is the same mistake and is answered the same way. Without the report
  a house rule written to the wrong extension would have no effect and appear nowhere,
  which is the silent-typo failure this feature exists to remove; with it, the author sees
  the file named and learns why their rule did not take. Rejecting it instead was
  considered and dropped: it would fail a load over a file the author did not write, and
  the visibility that matters is achieved without that cost.
- **FR-032b**: A file whose name begins with a dot MUST be passed over silently, neither
  loaded nor reported as ignored. Such files are made by tools rather than written by
  authors: a directory opened once in a file browser acquires one, as do editors saving
  alongside the file being edited. A file the author did not write is not a mistake the
  author needs told about, and a report full of such files is a report that stops being
  read. This is the only carve-out, and it is drawn at authorship rather than at a list of
  known filenames, which would need extending for every tool anyone uses.

#### Provenance

- **FR-033**: The system MUST report the provenance of the data set it actually loaded.
- **FR-033a**: Provenance MUST carry the package version, whether or not anything was
  overridden. The version is what determines the packaged content, so a provenance report
  that omits it identifies that content only to a reader who already knows which version
  produced it. Since provenance is the report that travels with a seed, and the
  reproducibility guarantee is that a seed and a package version together determine an
  output, a provenance carrying only the seed's other half is half a key.
- **FR-034**: When no file came from an override, provenance MUST identify the data as
  the packaged data set and, beyond the version FR-033a requires, need carry no further
  detail, because that version determines the content exactly.
- **FR-035**: When any file came from an override, provenance MUST identify which files
  did, MUST distinguish a file that replaced a packaged one from a file that was added
  where none shipped, and MUST carry a fingerprint of the content of each. The package
  version is still reported, because the files that did not come from the override are
  still the packaged ones and the version is what determines them. Any file FR-032a marks
  ignored MUST be named too, distinctly from both a replacement and an addition, since the
  point of naming it is that the author expected it to be one of those.
- **FR-036**: A provenance fingerprint MUST change when the content it describes changes,
  and MUST NOT vary with the location the content was read from, the time it was read, or
  anything else outside the content itself.
- **FR-037**: Every command that resolves against rules data MUST report provenance
  alongside the seed, in both human-readable and machine-readable output, including when
  the data set is the packaged one and nothing was overridden. Provenance is reported
  unconditionally rather than only when an override contributed, so that a reader never has
  to infer "packaged" from the absence of a line, and so that the presence of the report is
  not itself a signal that can be missed.

#### Command-line surface

- **FR-038**: The system MUST provide a command that validates rules data and reports
  every problem found.
- **FR-039**: Given no argument, that command MUST validate the packaged data set.
- **FR-040**: Given a location, that command MUST validate it composed over the packaged
  data exactly as a load would compose it, so that a single career file is still checked
  against the real registries and what is reported is what a run would do.
- **FR-040a**: Given a single file rather than a directory, that command MUST determine
  the file's position in the composed data set from its basename alone, ignoring the
  directory the file was found in, and MUST then treat it exactly as FR-029 and FR-032
  treat a file at that position in an override: a replacement when the basename matches a
  packaged file, an addition otherwise, reported distinctly. This now follows from FR-029
  rather than standing beside it, since basename positioning is the general rule; it is
  retained as a requirement of its own because it is the case an author meets most often.
  An author checking a file they have just edited must not have to reconstruct the packaged
  directory layout around it to get the answer a real load would give.
- **FR-041**: That command MUST support both human-readable and machine-readable output,
  MUST exit zero when no problem is found, and MUST exit non-zero when any problem is
  found, with the choice of output mode affecting neither outcome.
- **FR-042**: Every command that resolves against rules data MUST accept the override
  location, since data that is overridable through the library but not from the command
  line is overridable only in principle.
- **FR-043**: Every capability in this feature MUST be reachable programmatically without
  invoking the command line.

#### Replacing the existing reader

- **FR-044**: The parameter reading that the dice and task engine shipped MUST be replaced
  by this loader rather than kept alongside it, and the parameters it read MUST become an
  ordinary member of the validated data set.
- **FR-045**: Replacing it MUST NOT change any result: an existing seed and check MUST
  resolve identically before and after. "Result" here means the resolution outcome, the
  dice, the modifiers and their labels, the total, the target, the success or failure, and
  the seed. The rendered output surrounding it changes by exactly one addition, the
  provenance FR-037 requires, and that addition is the only permitted difference.

#### Licensing

- **FR-046**: Every data file this feature ships MUST carry its Open Game Content
  designation, and MUST NOT contain either Product Identity string, in keeping with the
  obligations that attach to redistributed rules content. This binds shipped files only. An
  override file supplied by the person running the tool is not redistributed by this
  project and MUST NOT be required to carry a designation, so FR-031's requirement that an
  overriding file be validated by exactly the same rules covers its declared version, its
  kind, its keys and its names, and not its licensing header.
- **FR-047**: The copyright notice chain that travels with the shipped Open Game Content
  MUST cover every data file this feature adds. This feature takes the number of shipped
  data files from one to five, and the project's own line in that chain currently names the
  single file that shipped before. Widening it is part of shipping the new files, not a
  later tidying: four files would otherwise travel outside the notice that grants the right
  to redistribute them. The obligation is invisible to the existing verification, which
  compares the chain against a fixed expected text and therefore passes unchanged while the
  line beneath it goes stale, so this requirement exists to make the widening something a
  check can fail on rather than something a reviewer must remember.

### Key Entities

- **Data set**: The complete, validated collection of rules content in force for a run.
  Composed from the packaged data and, if one was supplied, an override location. Either
  loads whole or does not load.
- **Data file**: One file of rules content. Declares its kind and the schema version it
  was written against, is positioned in a data set by its basename, and belongs to exactly
  one source, packaged or overridden.
- **Kind**: What a data file is, declared in the file and drawn from a closed set of five:
  task parameters, characteristics, skills, benefit items, and career. Selects the schema
  the file is held to. Career is the only kind a data set may hold more than one of.
- **Schema version**: The declared shape of a data file, counted per kind, independent of
  the package's release version, and the basis on which a file is accepted or refused
  before its contents are examined.
- **Registry**: A shipped declaration of the names legal in a given context. Three exist:
  skills, characteristics, and benefit items. A registry is what makes a misspelling
  detectable.
- **Skill reference**: A named skill with an optional specialty. Knows whether the skill
  admits specialties and whether one was given, so that an owed choice is visible without
  code knowing which skills owe one.
- **Career definition**: The rules content for one career: its declared name; its
  qualification, survival, promotion and re-enlistment throws, and its commission throw if
  it offers one; its personal, service and advanced skill tables, and its advanced
  education table if it has one, any of them optionally gated on a characteristic; one or
  more rank ladders with distinct names, each carrying ranks at distinct positions with
  titles and optional bonuses; and its mustering-out cash and benefits tables.
- **Table entry**: One element of a table that mixes kinds of thing in one cell, written in
  the compact notation. Resolves, according to the table it sits in, to a check, a
  characteristic adjustment, a skill grant, or a benefit item. Purely numeric content, cash
  amounts and throw targets, is not a table entry and never reaches the notation.
- **Validation problem**: One thing wrong with a data set. Carries the file, the location
  within it, what was found, and what was expected. Problems are reported as a collection,
  never one at a time.
- **Provenance**: The description of where the loaded data set came from. Always carries
  the package version; beyond that, either identifies the data as the packaged set or
  identifies each overridden file, says whether it replaced, was added, or was ignored as
  not rules data, and fingerprints the content of the ones that took effect. Travels with
  the seed into rendered output, and is reported whether or not anything was overridden.
  With the seed, it is the whole of what is needed to reproduce a result.
- **Task parameters**: The target number, difficulty ladder, unskilled penalty, and
  characteristic modifier bands the existing engine resolves against. Previously read by a
  reader of their own; now an ordinary member of the data set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every data file the package ships, including the registries and the
  reference career, validates without a single problem, verified as an automated check
  that runs against the files as read from the installed package rather than from the
  source tree.
- **SC-002**: For each distinct way a hand-authored data set can be wrong, a deliberately
  corrupted copy of shipped data is rejected, and the report names the file and, where the
  problem is not about the file as a whole, the location within it. The categories are
  these, and the list is closed: an unrecognized name (FR-013); an unrecognized key
  (FR-020); a malformed entry (FR-009); a well-formed entry of a form its field does not
  admit (FR-009a); a missing required element (FR-019); a value of the wrong type
  (FR-020b); an unsupported schema version (FR-002); a missing or unrecognized kind
  declaration, and a replacement whose declared kind is not the kind it replaces (FR-001a);
  a file that is not well-formed at all, or cannot be read (FR-020a); two careers in force
  declaring one name (FR-019b); two files in force declaring one single-instance kind, or
  such a kind absent (FR-010a); and two files in an override sharing a basename (FR-029a).
  Every category is covered by at least one case, so no category can regress into silent
  acceptance, and a category added to the schema later is added here in the same change. A
  file in an override that is not rules data is deliberately absent from this list: FR-032a
  reports it rather than rejecting it, and SC-005 covers that.
- **SC-003**: A data set containing several distinct problems reports all of them from a
  single run, demonstrated with a file carrying at least four, so that the number of
  runs needed to find every problem in a file is always one.
- **SC-004**: The reference career exercises every element of the career schema, evidenced
  by removing any single required element from a copy of it and observing a specific
  rejection naming what is missing. A schema element the reference career does not
  exercise is a schema element nothing proves.
- **SC-005**: An override location supplying one file puts that file's content in force
  while every other file continues to come from the packaged data, verified by observing
  both an effect from the overridden file and unchanged behavior from a file the override
  does not contain. An override file matching no packaged file enters the data set and is
  reported as an addition, so that the misspelled-filename case is distinguishable from
  the replacement case by report alone. An added career declaring a name a packaged career
  already uses is rejected, naming both files, so the misspelled-filename case cannot
  produce two careers answering to one name. An override file that is not rules data leaves
  the load succeeding and is named as ignored in the report, and a dot-prefixed file
  alongside it is named nowhere, so the three ways a file can fail to take effect, wrong
  stem, wrong extension, and not authored at all, are distinguishable by report alone.
- **SC-006**: A value present in a packaged file and absent from the override file that
  replaces it is absent from the loaded data set, confirming that replacement is whole-file
  rather than a merge.
- **SC-007**: With no override supplied, no filesystem location outside the installed
  package is opened during a load, verified as an automated check rather than by
  inspection.
- **SC-008**: Provenance distinguishes a packaged load from an overridden one in one
  hundred percent of cases, identical override content at two different locations
  fingerprints identically, and differing content fingerprints differently. The package
  version is present in the reported provenance in both cases and in both output modes, so
  that a result carries a complete reproduction key rather than one that has to be
  completed from elsewhere, and the version it reports equals the version of the installed
  package, asserted directly rather than inferred from a reference output that holds it as
  a placeholder.
- **SC-009**: Every seed and check that produced a given resolution outcome before the
  loader was replaced produces an identical one after, compared field by field against the
  reference outputs committed with the previous feature rather than against regenerated
  ones. The comparison covers the dice, the modifiers and their labels, the total, the
  target, the success or failure, and the seed. Because FR-037 adds provenance to rendered
  output, the reference outputs are regenerated in this feature, and that regeneration is
  itself checked: the only difference between the old and new reference outputs is the
  added provenance, so a regeneration that quietly absorbed a changed number fails. The
  package version FR-033a puts in that provenance is held in the reference outputs as a
  placeholder and substituted at comparison time, so that a release changes no reference
  output. Reference outputs carrying a literal version would be rewritten on every release,
  and each rewrite is another occasion for an unrelated change to be absorbed, which is the
  failure this criterion exists to prevent. SC-008 covers the version itself.
- **SC-010**: Exit status is zero for a validation run that finds nothing, non-zero for
  one that finds anything, and unchanged by the choice of output mode, with no case
  producing a status outside the set the project already uses.
- **SC-011**: Changing a value in any shipped data file changes the system's behavior
  accordingly with no code edit, demonstrated for a career throw, a skill table entry, a
  rank bonus, and a registry entry.
- **SC-012**: Every behavior in the functional requirements has a test whose expected
  values were written before the implementation existed, evidenced by those values being
  committed in a change that precedes the implementing change and by the test being
  observed to fail before it passes.
- **SC-013**: Every capability in this feature is exercised by at least one test that uses
  the library directly without invoking the command line, so that programmatic
  reachability is verified rather than assumed to follow from the command-line tests
  passing.
- **SC-014**: Every data file this feature adds carries its Open Game Content designation
  and contains neither Product Identity string, verified by automated check against the
  files as read from the installed package, so that a later edit dropping either fails the
  suite instead of shipping quietly.
- **SC-015**: Validation on demand and validation on load agree on every data set they are
  both given, valid and invalid alike, demonstrated by asserting the two against the same
  inputs rather than by inspecting that they share an implementation. FR-023 is the claim
  that a data set reported valid always loads and one reported invalid never does, and it
  is the one behavior in this feature that a structural argument alone would leave untested.
- **SC-016**: The copyright notice chain that ships with the package covers every data
  file the package contains, verified by an automated check that derives what the chain
  must cover from the data files actually present rather than comparing it against a fixed
  expected text. A check written the latter way passes unchanged when a file is added, which
  is exactly the failure FR-047 exists to prevent, so adding a data file without widening
  the notice must fail the suite.

## Out of Scope

Each exclusion below is deliberate. The reasons are recorded because they determine what
later features must add.

- **Per-key merging of override files**: excluded. Replacement is whole-file, which means
  a house rule changing one throw supplies that whole file and a house rule adding one
  skill supplies the whole skills registry. Merging was rejected because a partial file is
  harder to reason about and because the merged result would exist in no file anyone could
  read.
- **Any implicitly searched location**: excluded, and this exclusion is inherited from the
  previous feature rather than introduced here. A discovered file would change what a seed
  produces without anyone asking it to.
- **Treating unknown names or keys as warnings**: excluded. A warning raised by a library
  has nowhere to go, and a warning that does not fail is a warning that is ignored, which
  returns the silent-typo failure mode the strictness exists to remove.
- **Partial or lazy loading**: excluded. Both would let a run proceed past a broken file,
  and lazy loading additionally makes whether a data set works depend on the seed.
- **Semantics for benefit items**: excluded. A benefit item's name is validated against the
  registry and nothing more; what a passage or a ship means to a character belongs to the
  generator.
- **All remaining career content**: excluded. One reference career ships here to prove the
  schema; the generator's seed careers and the full set of careers belong to the two
  features that follow.
- **The house-rule authoring workflow**: excluded. Discovering that overrides exist,
  learning the schema, sharing a rule set, and carrying one across an upgrade are a
  documentation and tooling concern that may warrant its own effort; this feature delivers
  the mechanism, not the onboarding.
- **Migration between schema versions**: excluded. The version field is declared and
  checked per kind of file, but with one version per kind in existence there is nothing to
  migrate; what the field buys is that a future migration is possible at all.
- **Grouping or bounding a cascade of related problems**: excluded, deliberately and with
  a known cost. One truncated skills registry makes every skill reference in every career
  an unrecognized name, so a single mistake can produce a report far longer than the
  mistake deserves. FR-021 requires every problem, and suppressing or folding some would
  put the loader in the business of guessing which mistake caused which, which is how a
  real second problem gets hidden behind a guess. The cost is bounded while one career
  ships. It is the feature that authors the full career set, where a cascade spans two
  dozen files, that should decide whether grouping is worth its risk, and it will have the
  evidence this feature does not.

## Assumptions

- **The reference career is the Navy**: either of the two military careers satisfies the
  criteria that selected one, and the Navy is taken as the reference. If the other proves
  to express the schema more completely while the data is being authored, substituting it
  changes nothing else in this specification.
- **Schema version acceptance is exact**: a file is accepted when its declared version is
  the one the system supports for that file's kind, and refused otherwise. With exactly one
  version per kind in existence there is no compatibility range to define, and defining one
  now would be inventing a policy with no case to test it against.
- **Requiring the version field is a conscious departure from the simplicity principle**,
  and is recorded here so that review does not have to rediscover it. By that principle's
  standard the field is speculative: there is one version today and nothing yet reads it
  for any purpose but equality. It is accepted because overrides mean user-authored files
  now outlive package upgrades, because the project's release versioning deliberately
  carries no signal about breaking changes, and because by the time the full career set is
  authored the schema is fixed in roughly two dozen files outside anyone's control. One
  declared line per file buys an unambiguous upgrade story that cannot be recovered
  afterwards.
- **Provenance fingerprints are reported per overridden file** rather than as a single
  value for the data set, because a data set can mix sources and a single value could not
  say which file was responsible for the difference.
- **An override location may be a directory or a single file**, a single file being an
  override containing only that file. This was recorded here as an assumption when it bound
  only the validation command; it now binds every override location, and is stated as
  FR-028 and FR-029 rather than assumed.
- **The reference career is loaded and validated but otherwise unused** by this feature,
  since no command generates characters yet. It exists to prove the schema against real
  content rather than against a fixture whose author could unconsciously avoid the hard
  parts.
- **The existing dice-throwing command gains nothing from this feature**, because it
  resolves against no rules data; the requirement that commands accept an override
  location binds the check command and any later command that reads the data set.
- **Rules data is trusted input**: an override location is named deliberately by the person
  running the tool, so validation exists to catch mistakes rather than to defend against a
  hostile file.
