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
   identifies the data as the packaged data set and carries no per-file detail.
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
- **FR-002**: The system MUST refuse a file whose declared schema version it does not
  support, reporting the file, the version it declared, and the version the system
  supports for that file's kind, and MUST NOT attempt to interpret that file's contents.
  The refusal is the point: a file written for another shape must fail as a version
  mismatch and not as a cascade of confusing validation errors about individual keys.
- **FR-002a**: Schema versions MUST be counted per kind of file, so that a career file, a
  registry, and the task parameters each declare and are checked against the version
  supported for their own kind. A change to one kind's shape MUST NOT invalidate a
  user-supplied file of a kind whose shape did not change. Every kind starts at the same
  version today, so this costs nothing now and is the whole of what the version field was
  justified on: a house rule overriding one career must survive a change to the registry
  schema it never touched.
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
  denotes a benefit item. Each table MUST validate its names against the registry
  appropriate to that table and no other.
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

#### Registries

- **FR-010**: The system MUST ship a registry of skills, a registry of characteristics,
  and a registry of benefit items, each as data.
- **FR-011**: The skills registry MUST declare, for each skill, whether it has specialties
  and which specialties are permitted.
- **FR-012**: The characteristics MUST be declared in data rather than known to the
  parsing code, because characteristic names are rules content and no rules content may be
  hard-coded in engine code.
- **FR-013**: The system MUST reject any name that its governing registry does not
  contain, reporting the file, the location within it, the name as written, and which
  registry it was checked against.

#### Career file schema

- **FR-014**: A career file MUST be able to declare the throws that govern a term of
  service: qualification, survival, commission, promotion, and re-enlistment. A throw
  declares the characteristic it is checked against and its target number as distinct
  typed fields, per FR-004a, rather than as a notation string.
- **FR-015**: A career file MUST be able to declare its personal, service, and advanced
  skill tables, and MUST be able to gate a table on a minimum characteristic score, since
  the source material restricts advanced training that way.
- **FR-016**: A career file MUST be able to declare more than one rank ladder, so that a
  career with both an enlisted and an officer progression is expressible, with each rank
  carrying its position, its title, and optionally a bonus granted on reaching it.
- **FR-017**: A career file MUST be able to declare its mustering-out cash table, whose
  entries are plain amounts, and its mustering-out benefits table, whose entries are
  written in the notation and validated against the benefit items registry.
- **FR-018**: The system MUST ship one complete career that is faithful to the source
  material and that exercises every element of this schema, including a commission, a
  second rank ladder, at least one rank bonus, and a characteristic-gated table.
- **FR-019**: The system MUST reject a career file that omits any element the schema
  requires, naming what is missing rather than failing later when the missing part is
  reached.
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
  MUST be the only way content that did not ship with the package enters a data set.
- **FR-029**: An override location MUST mirror the layout of the packaged data, and MAY
  be partial: a file present in the override replaces the corresponding packaged file in
  its entirety, and a packaged file with no counterpart in the override is used as
  shipped.
- **FR-030**: The system MUST NOT merge an override file with the packaged file it
  replaces. Replacement is whole-file, so a value the override file omits is absent rather
  than inherited from the shipped file it stands in for.
- **FR-031**: An overriding file MUST be validated by exactly the same rules as a shipped
  file, including its declared schema version, its keys, and every name it contains.
- **FR-032**: A file in the override location that corresponds to no packaged file MUST be
  added to the data set as new content, so that a house rule can introduce a career rather
  than only modify one. Because a misspelled filename is indistinguishable in itself from
  content added on purpose, the system MUST report an added file distinctly from a
  replaced one wherever it reports where data came from, so that an unintended addition is
  visible rather than silent. This is the one place where the strictness applied to
  unrecognized keys and unrecognized names is deliberately not applied to unrecognized
  filenames, and reporting is what pays for the exception.

#### Provenance

- **FR-033**: The system MUST report the provenance of the data set it actually loaded.
- **FR-034**: When no file came from an override, provenance MUST identify the data as
  the packaged data set and need carry no further detail, because the package version
  already determines that content exactly.
- **FR-035**: When any file came from an override, provenance MUST identify which files
  did, MUST distinguish a file that replaced a packaged one from a file that was added
  where none shipped, and MUST carry a fingerprint of the content of each.
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
  packaged file, an addition otherwise, reported distinctly. An author checking a file they
  have just edited must not have to reconstruct the packaged directory layout around it to
  get the answer a real load would give.
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
  obligations that attach to redistributed rules content.

### Key Entities

- **Data set**: The complete, validated collection of rules content in force for a run.
  Composed from the packaged data and, if one was supplied, an override location. Either
  loads whole or does not load.
- **Data file**: One file of rules content. Declares the schema version it was written
  against, and belongs to exactly one source, packaged or overridden.
- **Schema version**: The declared shape of a data file, counted per kind of file,
  independent of the package's release version, and the basis on which a file is accepted
  or refused before its contents are examined.
- **Registry**: A shipped declaration of the names legal in a given context. Three exist:
  skills, characteristics, and benefit items. A registry is what makes a misspelling
  detectable.
- **Skill reference**: A named skill with an optional specialty. Knows whether the skill
  admits specialties and whether one was given, so that an owed choice is visible without
  code knowing which skills owe one.
- **Career definition**: The rules content for one career: its declared name, its
  qualification, survival, commission, promotion and re-enlistment throws, its personal, service and advanced skill
  tables with any characteristic gate, one or more rank ladders with titles and bonuses,
  and its mustering-out cash and benefits tables.
- **Table entry**: One element of a table that mixes kinds of thing in one cell, written in
  the compact notation. Resolves, according to the table it sits in, to a check, a
  characteristic adjustment, a skill grant, or a benefit item. Purely numeric content, cash
  amounts and throw targets, is not a table entry and never reaches the notation.
- **Validation problem**: One thing wrong with a data set. Carries the file, the location
  within it, what was found, and what was expected. Problems are reported as a collection,
  never one at a time.
- **Provenance**: The description of where the loaded data set came from. Either the
  packaged data set, or a mixture identifying each overridden file and fingerprinting its
  content. Travels with the seed into rendered output, and is reported whether or not
  anything was overridden.
- **Task parameters**: The target number, difficulty ladder, unskilled penalty, and
  characteristic modifier bands the existing engine resolves against. Previously read by a
  reader of their own; now an ordinary member of the data set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every data file the package ships, including the registries and the
  reference career, validates without a single problem, verified as an automated check
  that runs against the files as read from the installed package rather than from the
  source tree.
- **SC-002**: For each distinct way a hand-authored file can be wrong, an unrecognized
  name, an unrecognized key, a malformed entry, a missing required element, an
  unsupported schema version, and a file that is not well-formed at all, a deliberately
  corrupted copy of shipped data is rejected, and the report names the file and the
  location within it. Every category is covered by at least one case, so no category can
  regress into silent acceptance.
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
  produce two careers answering to one name.
- **SC-006**: A value present in a packaged file and absent from the override file that
  replaces it is absent from the loaded data set, confirming that replacement is whole-file
  rather than a merge.
- **SC-007**: With no override supplied, no filesystem location outside the installed
  package is opened during a load, verified as an automated check rather than by
  inspection.
- **SC-008**: Provenance distinguishes a packaged load from an overridden one in one
  hundred percent of cases, identical override content at two different locations
  fingerprints identically, and differing content fingerprints differently.
- **SC-009**: Every seed and check that produced a given resolution outcome before the
  loader was replaced produces an identical one after, compared field by field against the
  reference outputs committed with the previous feature rather than against regenerated
  ones. The comparison covers the dice, the modifiers and their labels, the total, the
  target, the success or failure, and the seed. Because FR-037 adds provenance to rendered
  output, the reference outputs are regenerated in this feature, and that regeneration is
  itself checked: the only difference between the old and new reference outputs is the
  added provenance, so a regeneration that quietly absorbed a changed number fails.
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
- **The validation command accepts either a directory or a single file**, treating a
  single file as an override containing only that file, positioned by its basename.
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
