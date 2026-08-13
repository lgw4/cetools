# Feature Specification: Dice and Task Check Engine

**Feature Branch**: `001-dice-task-engine`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "Decisions brief: dice-task-engine. The first of five MVP features for cetools. Bootstraps the repository (packaging, package skeleton, test harness) and delivers the seeded dice core every later feature builds on: reproducible randomness, dice throws, and task checks resolved against SRD parameters held in a shipped data file, exposed as library API and surfaced through two CLI subcommands (`roll` and `check`). Seed reproducibility is settled first because it constrains everything downstream: seeds are an integer or an arbitrary string, strings folded deterministically across processes; randomness lives in a single explicitly-passed roller; the seed is echoed in every output and round-trips. Task parameters (flat target of 8, the Simple-to-Formidable difficulty ladder, the unskilled penalty, and the characteristic DM range table with an unbounded top band) live in data, not code. Effect, criticals, time frames, multiple actions, Jack of All Trades, law-level difficulty, and a `--target` flag are deliberately excluded."

## Clarifications

### Session 2026-08-12

- Q: When a result is emitted as machine-readable data, should the seed be written as a quoted text value or as a bare number? (FR-005) → A: Quoted text containing only decimal digits and an optional sign, exact for any magnitude in every consumer.
- Q: Must every check be given a characteristic score, or may a referee resolve a check without naming one? (FR-015) → A: Optional; omitting it contributes no characteristic modifier and shows no characteristic line.
- Q: Must every check name a difficulty, or is there a default when the referee omits it? (FR-014) → A: Optional, defaulting to the middle rung; the difficulty line still appears in the output.
- Q: How should someone sharing a result report which package version produced it? (FR-025) → A: A top-level version option that prints the package version and exits successfully; results are unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Throw dice reproducibly (Priority: P1)

A referee preparing a session needs to throw dice and, later, get exactly the same
result again: to re-check a number they wrote down, to share a result with a
player who wants to verify it, or to re-run a prepared encounter identically. They
throw dice by describing them (two six-sided dice plus one, one six-sided die, and
so on), see the individual faces and the total, and see the seed that produced
them. Handing that seed back reproduces the throw exactly.

**Why this priority**: This is the foundation every other capability in the
project is built on. Delivered alone it is already useful (a referee has a
reproducible dice roller) and it establishes the reproducibility guarantee that
cannot be retrofitted later.

**Independent Test**: Throw dice without a seed, note the reported seed, throw
again supplying that seed, and confirm the faces and total are identical. Repeat
in a separate process and on a separate machine and confirm the results still
match.

**Acceptance Scenarios**:

1. **Given** no seed is supplied, **When** the referee throws two six-sided dice,
   **Then** the output reports each die's face, the total, and a seed as a decimal
   integer.
2. **Given** a seed reported by a previous throw, **When** the referee throws the
   same dice supplying that seed, **Then** every die face and the total are
   identical to the previous throw.
3. **Given** a throw description that includes a modifier, **When** the referee
   throws, **Then** the output reports the faces, the modifier, and the total with
   the modifier applied.
4. **Given** a text seed such as a session name, **When** the same throw is made
   from two separate processes started with different process-level hash
   randomization settings, **Then** both produce identical results.
5. **Given** a throw request for zero dice or dice with zero sides, **When** the
   referee submits it, **Then** the tool reports a clear error and exits non-zero
   without producing a result.

---

### User Story 2 - Resolve a task check (Priority: P2)

A referee needs to know whether an action succeeds. They state how hard it is by
name (Simple through Formidable), the acting character's relevant characteristic
score and skill level, and any situation-specific modifiers they have decided on,
each with a short label. The tool throws two six-sided dice, applies every
modifier, compares against the standard target, and reports the dice, an itemized
list of every modifier with its label, the total, and whether the check succeeded.

**Why this priority**: This is the capability referees actually reach for at the
table, but it depends on the seeded throw from Story 1 and on the rules data being
readable. Delivered on top of Story 1 it turns a dice roller into a rules engine.

**Independent Test**: Resolve a check at each named difficulty with a fixed seed
and confirm the total equals the dice plus the expected modifiers, and that the
success verdict matches the standard target. Confirm the itemized modifiers in the
output sum to the difference between the dice total and the final total.

**Acceptance Scenarios**:

1. **Given** a difficulty named on the ladder, **When** the referee resolves a
   check, **Then** the difficulty contributes its modifier to the roll and the
   target number is unchanged.
2. **Given** a characteristic score, **When** the referee resolves a check, **Then**
   the modifier derived from that score matches the published band for that score,
   including scores above every listed band.
3. **Given** a character with the skill at level 0, **When** the referee resolves a
   check, **Then** no bonus and no penalty is applied for skill.
4. **Given** a character who does not have the skill at all, **When** the referee
   resolves a check, **Then** the unskilled penalty is applied.
5. **Given** one or more situational modifiers with labels, **When** the referee
   resolves a check, **Then** each appears in the output with its label and signed
   value and is included in the total.
6. **Given** a check whose total falls below the target, **When** it is resolved,
   **Then** the output reports failure and the tool exits successfully, because
   reporting a failed check is the tool working correctly.
7. **Given** a difficulty name that is not on the ladder, **When** the referee
   resolves a check, **Then** the tool reports a clear error naming the valid
   difficulties and exits non-zero.
8. **Given** dice showing two natural sixes or two natural ones, **When** the check
   is resolved, **Then** the verdict is decided by the total against the target
   with no automatic success or failure applied.

---

### User Story 3 - Consume results from another program (Priority: P3)

Someone building on top of this (a script, a future web interface, or a later
feature in this project) needs results as structured data rather than prose. Every
command renders the same result either as readable text or as structured
machine-readable output, and the structured shape is stable enough to be relied
upon.

**Why this priority**: Required by the project's CLI contract for every command,
and required by later features that will consume these results, but it adds no new
game capability on its own.

**Independent Test**: Run each command in both output modes with the same seed and
confirm the structured output contains the same dice, modifiers, total, verdict,
and seed as the text output, and that the structured output parses cleanly.

**Acceptance Scenarios**:

1. **Given** any command, **When** run in machine-readable mode, **Then** the
   result parses as valid structured data containing the seed, the individual
   dice, the itemized modifiers, and the total.
2. **Given** any command, **When** run in either output mode, **Then** the seed
   appears in the output and is the same value in both modes.
3. **Given** an error condition, **When** run in either output mode, **Then** the
   error message is written to the error stream and no partial result is written
   to the output stream.

---

### User Story 4 - Throw a two-digit table die (Priority: P4)

A referee consulting a table indexed by two dice read as digits (first die as
tens, second as units) needs that specific form of throw, which cannot be
expressed as a count-and-sides description.

**Why this priority**: Nothing in the MVP consumes it yet. It is included as
deliberate groundwork for post-MVP world and trade generation, and is small enough
to build correctly now rather than bolt on later.

**Independent Test**: Throw it with a fixed seed and confirm the reported value is
composed of the two die faces as tens and units, that no value contains a zero or
a digit above six, and that across a fixed seeded sample of at least one thousand
throws all thirty-six values occur.

**Acceptance Scenarios**:

1. **Given** any seed, **When** the referee makes this throw, **Then** the result
   is a two-digit value whose tens and units digits are each between one and six.
2. **Given** a fixed seed, **When** the throw is repeated, **Then** the same value
   is produced.
3. **Given** the result, **When** the output is rendered, **Then** both individual
   die faces are reported alongside the combined value.

---

### Edge Cases

- **Seed that looks like a number**: a seed value consisting only of an optional
  sign and decimal digits is treated as that integer, so any reported seed pasted
  back reproduces the result. Every other seed value is treated as text.
- **Very large integer seeds**: accepted without truncation or overflow, and
  reported back in a form that round-trips.
- **Characteristic score above the highest listed band**: handled by an unbounded
  top band; a score of any magnitude yields a modifier.
- **Negative characteristic score or negative skill level**: rejected as invalid
  input with a clear error.
- **Modifiers that make the outcome certain**: a total far above or far below the
  target is reported as an ordinary success or failure; there are no automatic
  outcomes.
- **No situational modifiers supplied**: the check resolves normally and the
  itemized modifier list contains only the named modifiers that apply.
- **Missing, unreadable, or malformed rules data**: reported as a clear error
  identifying the problem, exiting non-zero, rather than falling back to built-in
  values.
- **Rules data missing a required parameter** (for example the target number or a
  difficulty entry): reported as a clear error rather than silently defaulting.
- **Randomness contamination**: performing any operation leaves any ambient,
  process-wide random state untouched, so unrelated code in the same process
  cannot perturb or be perturbed by this feature.
- **Two callers in the same process**: each supplies its own random source, so
  neither can consume the other's sequence and change its results.

## Requirements *(mandatory)*

### Functional Requirements

#### Randomness and reproducibility

- **FR-001**: The system MUST draw every random value from a single random source
  that is supplied explicitly by the caller, and MUST NOT read from or write to any
  process-global or ambient random state.
- **FR-002**: The system MUST accept a seed given either as a decimal integer or as
  an arbitrary text string. An integer seed MAY carry a negative sign and has no
  upper bound on magnitude; it MUST be used exactly as given, without truncation,
  rounding, or reduction into a narrower range.
- **FR-003**: A text seed MUST resolve to the same underlying value in every
  process, on every machine, and under every process-level hash-randomization
  setting. A text seed MUST be folded from its exact character sequence as
  supplied: case, surrounding whitespace, and the choice of composed or decomposed
  form for an accented character are all significant, so two strings that differ in
  any of these are different seeds and are not silently unified.
- **FR-004**: When no seed is supplied, the system MUST generate one drawn from at
  least sixty-four bits of entropy from a source suitable for unpredictable values,
  rather than defaulting to a fixed value or deriving one from readily guessable
  process state such as the clock or the process identifier. Sixty-four bits is a
  floor rather than a preference: a seed of that width routinely exceeds the largest
  integer a consumer's default numeric type holds exactly, which is what makes the
  text carriage required by FR-005 necessary rather than merely cautious.
- **FR-005**: Every result the system renders MUST include the seed in both
  human-readable and machine-readable output, whether or not the caller supplied a
  seed. The seed MUST be written in plain decimal notation: digits with an optional
  sign, never another base and never an exponent form. In machine-readable output
  the seed MUST be carried as a text value rather than as a bare number, so that a
  seed too large for a consumer's numeric type survives the round trip without
  losing digits. The seed reported is always the resolved integer and never the
  text the caller supplied: a referee who seeds with a session name is told the
  integer that name resolved to, and it is that integer which reproduces the
  result.
- **FR-006**: Supplying a previously reported seed back to the same operation with
  the same arguments MUST reproduce an identical result, whether that operation is
  invoked as a command or programmatically.
- **FR-007**: The same seed and the same package version MUST produce identical
  results across every version of the underlying language runtime that the package
  declares itself to support, not merely across repeated runs on a single runtime
  version. The supported set is the one the package declares in its own metadata;
  this requirement binds every version in that set, which is what makes it
  dischargeable rather than open-ended.
- **FR-008**: Two independently seeded operations in the same process MUST NOT
  affect each other's results.

#### Dice throws

- **FR-009**: The system MUST throw a caller-specified number of dice with a
  caller-specified number of sides, with an optional signed modifier, and MUST
  report each individual die face, the modifier, and the total.
- **FR-010**: The system MUST provide a two-digit table throw that reads the first
  die as the tens digit and the second as the units digit, reporting both
  individual faces and the combined value. It MUST be requested by a name that
  cannot collide with any count-and-sides description, so that a genuine
  sixty-six-sided die remains expressible and the two are never confused. Because
  its combined value is composed of digits rather than summed, machine-readable
  output MUST identify which form of throw produced a given result, so a consumer
  can tell a composed value from a sum without out-of-band knowledge.
- **FR-011**: The system MUST reject a dice count or a side count that is not a
  positive whole number, with a clear error, and MUST NOT produce a result.
- **FR-012**: Each die face MUST be equally probable across its range by
  construction, with no face unreachable and none favored by the derivation,
  rather than merely appearing uniform under sampling; the same holds for all
  thirty-six values of the two-digit table throw. For the six-sided die and for the
  two-digit throw this MUST additionally be evidenced by exhaustive coverage over a
  fixed seeded sample of at least one thousand throws, in which every possible
  outcome occurs at least once. A distributional test against a tolerance is
  deliberately not the criterion: it would be flaky and would test something weaker
  than the property being claimed.

#### Task checks

- **FR-013**: The system MUST resolve a check by throwing the dice described in the
  rules data, which ship as two six-sided dice, adding every applicable modifier,
  and comparing the total against a fixed target number also taken from the rules
  data; a total that reaches or exceeds the target is a success. The check's own
  dice are rules content and are held in data for the same reason the target is
  (FR-021), so a referee can house-rule the core throw.
- **FR-014**: The system MUST accept difficulty by name across the full ladder held
  in the rules data, which ships spanning a positive modifier of six at the easiest
  rung to a negative modifier of six at the hardest, and MUST apply difficulty as a
  modifier to the roll rather than as a change to the target number. A difficulty
  name MUST be matched exactly, character for character, with no case folding, no
  abbreviation, and no whitespace tolerance, so that a near miss is reported under
  FR-019 rather than silently resolved to a neighbouring rung. Difficulty is
  optional: when none is named the check MUST use the ladder entry whose modifier
  is zero, and MUST still name that difficulty in the itemized output so the
  assumption is visible rather than silent. That entry is identified by its
  modifier being zero, not by its position in the ladder and not by a particular
  name, because a ladder edited under FR-022 need have neither a middle nor any
  given name; rules data whose ladder does not hold exactly one zero-modifier entry
  is rejected under FR-024.
- **FR-015**: The system MUST derive a characteristic modifier from a characteristic
  score using the range table held in the rules data, which ships with an unbounded
  top band so that every non-negative score yields a modifier. A characteristic
  score is optional: when none is supplied the check MUST resolve normally,
  contributing no characteristic modifier and showing no characteristic entry in
  the itemized output. A negative characteristic score MUST be rejected with a
  clear error. Because the table is editable under FR-022, coverage of every score
  is a property of the shipped data rather than of the engine: a score falling
  outside every band in the data then in force MUST be reported as a rules-data
  error rather than silently contributing zero.
- **FR-016**: The system MUST distinguish three skill states: a trained skill at
  level zero (contributing nothing), a trained skill at level one or higher
  (contributing its level), and no training at all (contributing the unskilled
  penalty from the rules data). Omitting a skill level entirely and supplying a
  level of zero MUST be distinct inputs producing distinct results: the first is
  untrained, the second is trained at level zero. A negative skill level MUST be
  rejected with a clear error.
- **FR-017**: The system MUST accept zero or more caller-supplied situational
  modifiers, each carrying a caller-supplied label and a signed value, and MUST
  include all of them in the total. A situational modifier whose label is empty,
  whose value is absent, or whose value is not a signed whole number MUST be
  rejected as a usage error under FR-031, because it is a malformed input to the
  invocation rather than a condition the engine detected while resolving a check.
- **FR-018**: A check result MUST report the individual die faces, every applied
  modifier itemized with its label and signed value, the total, the target number,
  and whether the check succeeded.
- **FR-019**: The system MUST reject a difficulty name that is not on the ladder
  with a clear error that names the valid difficulties.
- **FR-020**: The system MUST NOT apply any automatic success or automatic failure
  based on the natural dice showing their highest or lowest possible values.

#### Rules content

- **FR-021**: The target number, the difficulty ladder, the unskilled penalty, the
  characteristic modifier range table, and the description of the dice a check
  throws MUST live in a data file shipped with the package; no engine code may
  contain these values. The file MUST carry the Open Game Content designation
  required by the project's licensing constraints, since the file is created by
  this feature even though the wider licensing work is not.
- **FR-035**: Because this feature is the one that first produces a distributable
  package containing Open Game Content, that distribution MUST satisfy the
  project's licensing constraints as they apply to a distribution: it MUST bundle
  the full text of the license the rules data is released under together with the
  complete verbatim copyright-notice chain that license requires, and the
  repository MUST state plainly which files are Open Game Content and which are
  under the source-code license. This is not the whole of the licensing work.
  Publishing, the compatibility statement, and the package description belong to
  the packaging and release feature; what belongs here is only what an installable
  artifact containing Open Game Content cannot be built without. Where any text
  this feature writes claims compatibility with the source rules, it MUST carry
  the trademark attribution and non-affiliation statement the project's licensing
  constraints require, or else make no such claim.
- **FR-022**: Editing the shipped data file MUST change the engine's arithmetic
  correspondingly, with no code change required, so a referee's house rule is a
  data edit. The edits that MUST be honored are: changing any value; adding,
  removing, or renaming a difficulty ladder entry; and adding, removing, or
  altering the bounds of a characteristic band. Two constraints survive every edit,
  because the engine has no defined behavior without them: the ladder MUST retain
  exactly one entry whose modifier is zero (FR-014), and the characteristic table
  MUST retain exactly one unbounded top band. Data violating either is rejected
  under FR-024 rather than accepted and worked around.
- **FR-023**: The system MUST read exactly one rules data file, the one shipped
  inside the package, and MUST NOT automatically search user or system
  configuration locations for alternatives.
- **FR-024**: Rules data that is missing, unreadable, or missing a required
  parameter MUST produce a clear error rather than a silent fallback to built-in
  values. The required parameters are exactly these, so that "required" names a
  decidable set: the target number; the unskilled penalty; the description of the
  dice a check throws; a difficulty ladder holding at least one entry, of which
  exactly one has a modifier of zero; and a characteristic range table holding at
  least one band, of which exactly one is unbounded at the top.

#### Command-line surface

- **FR-025**: The system MUST provide two subcommands, one that throws dice and one
  that resolves a check, each accepting only the options meaningful to it. Each
  subcommand's help text MUST list exactly the options that subcommand accepts and
  no others, which states the requirement as something checkable rather than as a
  matter of taste. Alongside those
  two subcommands the command MUST offer a top-level option that reports the
  installed package version and exits successfully, because the reproducibility
  promise is stated as a seed together with a package version and someone sharing a
  seed needs a supported way to report the version with it. Rendered results are
  unchanged by this option; they carry the seed, not the version.
- **FR-026**: Every subcommand MUST support both human-readable and
  machine-readable output, rendered from the same library result rather than
  assembled separately. Observably, this means that for the same operation and the
  same seed, every value the two modes have in common MUST be identical. The
  human-readable rendering MUST be stable within a package version and is pinned by
  the reference files of SC-008; unlike the machine-readable shape it is not a
  committed interface across versions, because it exists to be read by a person
  rather than parsed.
- **FR-027**: The system MUST write results to the standard output stream and
  errors and diagnostics to the standard error stream. Errors MUST be written as
  plain text on the error stream in both output modes: requesting machine-readable
  output does not make errors structured, and no structured error envelope is
  provided. On any error nothing at all is written to the output stream, so a
  consumer never sees a partial result.
- **FR-028**: The machine-readable output shape MUST be treated as a committed
  public interface; any change to a field's name, its value's type, or its meaning
  is a breaking change. Because the project's version scheme cannot signal it, such
  a change MUST be recorded in the package's changelog under a heading identifying
  it as breaking, which is what "flagged prominently" means here. This feature
  establishes the shape and so changes nothing: the obligation binds from the first
  change onward, and the changelog itself is created by the packaging and release
  feature rather than this one.

#### Errors and exit behavior

- **FR-029**: The library MUST signal every error condition it detects by raising a
  typed error descending from a single project-wide base error type, and MUST NOT
  print to any stream or terminate the process.
- **FR-030**: The command-line layer MUST be the only place that catches those
  errors; on catching one it MUST write the message to the error stream and exit
  with status one.
- **FR-031**: Usage errors (unknown options, missing required arguments, malformed
  option values including a malformed situational modifier) MUST exit with status
  two, distinct from the status used for errors raised by the library. The two
  classes are told apart by where the fault is detected, which makes the boundary
  decidable for any input: a malformed invocation, detected before the library is
  called, is a usage error; anything the library raises once it has been called
  falls under FR-030 regardless of how it looks to the user.
- **FR-032**: A check that resolves to failure MUST exit with status zero, because
  a reported failure is correct operation, not an error.

#### Project foundation

- **FR-033**: The repository MUST provide an installable package with a runnable
  command-line entry point and an executable test suite, established as part of
  this feature.
- **FR-034**: All library capabilities in this feature MUST be reachable
  programmatically by an importing caller, independently of the command-line layer.

### Key Entities

- **Seed**: The reproducibility handle. Accepted as an integer or arbitrary text,
  always reported as a single decimal integer that can be supplied back verbatim,
  and carried as a text value in machine-readable output so no consumer rounds it.
- **Random source**: The single object that holds seeded randomness and produces
  every die face. Created from a seed and passed explicitly to whatever needs it,
  so ownership of a random sequence is always visible in the call.
- **Dice throw result**: The outcome of throwing dice. Carries the individual
  faces, any flat modifier, the total, and the seed.
- **Modifier**: A single labeled signed adjustment to a check. Comes from a named
  difficulty, a characteristic score, a skill state, or the caller directly; all
  four kinds are itemized identically in output.
- **Check result**: The outcome of resolving a task. Carries the dice faces, the
  ordered itemized modifiers, the total, the target number, the success verdict,
  and the seed.
- **Task parameters**: The shipped rules content: the target number, the difficulty
  ladder mapping each name to its modifier, the unskilled penalty, and the
  characteristic modifier range table with its unbounded top band.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any given seed and package version, one hundred percent of
  repeated runs of the same command produce byte-identical output, including runs
  in separate processes, verified as an automated check. Identity across different
  machines follows from FR-003 and FR-007 and is established by running that same
  automated check on each supported platform, rather than by inspection or by
  assertion.
- **SC-002**: A text seed produces identical results when the same command is run
  in two processes started with different process-level hash randomization
  settings, verified as an automated check rather than by inspection.
- **SC-003**: Check arithmetic matches the rules data in force for every difficulty
  entry and every characteristic band that data contains, including its unbounded
  top band, verified case by case. The criterion is stated against the data rather
  than against fixed counts, because SC-010 requires those counts to be editable;
  the file as shipped holds seven difficulties and twelve bands, so that is the
  case count for the shipped suite.
- **SC-004**: Every rendered result, in both output modes and for every command,
  includes a seed that reproduces that result when supplied back, with no
  exceptions and no flag required to make it appear.
- **SC-005**: Running any operation leaves any ambient process-wide random state
  bit-for-bit unchanged, verified as an automated check.
- **SC-006**: Exit status is zero for every successful run, including a check that
  reports failure and including the version option; one for every error the library
  raises; and two for every usage error, with no case producing a status outside
  that set. Requesting machine-readable output changes none of these.
- **SC-007**: A referee can obtain a resolved check, with every modifier itemized
  and explained, in a single command invocation without consulting the rulebook for
  any modifier value.
- **SC-008**: Every behavior in the functional requirements has a test whose
  expected values were written before the implementation existed, evidenced by
  those values being committed in a change that precedes the implementing change
  and by the test being observed to fail before it passes. Rendered command output
  is additionally pinned by committed reference files. A change to a reference file
  is acceptable only when it accompanies an intended change of behavior described
  in that same commit; regenerating the files wholesale to make a failing suite
  pass is not, and that is the difference the phrase "reviewed as differences"
  names.
- **SC-009**: The two-digit table throw has its own dedicated tests rather than
  being covered incidentally by tests of other throws.
- **SC-010**: Changing a value in the shipped rules data file changes the engine's
  results accordingly with no code edit, demonstrated for the target number, a
  difficulty entry, the unskilled penalty, and a characteristic band.
- **SC-011**: Every capability in this feature is exercised by at least one test
  that imports the library directly without invoking the command line, so that
  FR-034's programmatic reachability is verified rather than assumed to follow from
  the command-line tests passing.
- **SC-012**: The licensing obligations that attach to the shipped rules data are
  verified by automated check rather than by inspection: the data file as read
  from the installed package carries its Open Game Content designation and
  contains neither Product Identity string, and the license text and its
  copyright-notice chain are present in the built distribution. A later edit that
  drops any of these fails the suite instead of shipping quietly.

## Out of Scope

Each exclusion below is deliberate. The reasons are recorded because they
determine what later features must add.

- **Margin of success and its degrees ladder**: not computed. Consequently opposed
  checks, aiding another, combat damage, and initiative bonuses are all unreachable
  until it is added. Nothing in the MVP needs it, since character-generation throws
  are pass or fail.
- **Critical success and critical failure rules**: none, because the source rules
  state outright that the highest natural roll is not an automatic success and the
  lowest is not an automatic failure. The only natural-roll rules are local to
  survival and re-enlistment and belong to the NPC generator feature.
- **Time frames**: excluded. They are a separate mechanic rather than a check, and
  their trade-off of one point of modifier per row moved on the time frames table
  is genuine design work deserving its own feature.
- **Multiple-actions penalty and Jack of All Trades**: excluded, because both are
  labeled numbers a caller can already pass as situational modifiers.
- **Law-level base difficulty**: excluded; it belongs to a legal-affairs feature
  that does not exist yet.
- **A target-number override option**: excluded. With opposed checks out of scope
  nothing needs it, and offering it would invite modeling difficulty as a shift in
  the target, which produces wrong numbers while looking reasonable.
- **Rules data override and search precedence**: excluded. The validated data
  loader owns loading and should design search precedence once, in the next
  feature. A configuration directory searched automatically was specifically
  rejected: it would silently change results for a given seed and quietly break the
  reproducibility guarantee.
- **Schema validation of the rules data and the compact-string grammar**: excluded;
  both belong to the next feature. This feature's data reading is minimal and
  intended to be replaced rather than extended.

## Assumptions

- **Seed parsing**: a supplied seed consisting only of an optional sign and decimal
  digits is interpreted as that integer; anything else is interpreted as text. This
  is required for the round-trip guarantee, since reported seeds are always decimal
  integers.
- **Absent skill means untrained**: if no skill level is given for a check, the
  unskilled penalty applies. Supplying a level of zero explicitly is a distinct
  input meaning trained at level zero, contributing nothing. This matches the
  source rules, where lacking a skill entirely is worse than having it at level
  zero.
- **Characteristic is given as a score**: when a characteristic is involved at all,
  checks take the score and derive the modifier from the shipped table. Passing a
  pre-computed characteristic modifier directly is not offered, since a caller
  wanting that can use a labeled situational modifier. Omitting the characteristic
  entirely is a valid check, not an error, because not every roll at the table hangs
  off a characteristic.
- **Situational modifiers are labeled pairs**: each is supplied as a label and a
  signed value together, repeatable within one invocation. The exact command-line
  syntax for expressing the pair is a design detail for the planning phase; the
  requirement is that the label survives into both output modes.
- **Dice descriptions**: throws are described by a count, a side count, and an
  optional signed flat modifier. Whether the count may be omitted to mean one, and
  the exact accepted spelling, are planning-phase details; the two-digit table
  throw is requested by name because it cannot be expressed this way.
- **Characteristic modifier table content**: twelve bands covering scores from zero
  upward in steps of three, from a penalty of two at the bottom to a bonus of nine
  in the unbounded top band. This is equivalent to the formula in the source rules
  but is expressed as data so a referee can house-rule a flatter or steeper curve,
  which is the substitution that keeping rules content in data exists to enable.
- **Difficulty ladder content**: seven entries from a bonus of six at the easiest
  through zero at the middle to a penalty of six at the hardest. The prototype
  sketch in the project's decision notes is missing the easiest entry and truncates
  the characteristic table; both are corrected here.
- **Prior decisions inherited**: this feature depends on no other feature. The
  package skeleton, packaging configuration, and test harness it establishes are
  consumed by all four remaining MVP features.
- **Licensing**: the shipped rules data file is Open Game Content and carries the
  designation required by the project's licensing constraints. Because this
  feature also builds the first installable artifact containing that content, the
  license text, its copyright-notice chain, and the repository-level statement of
  which files are Open Game Content travel with it (FR-035) rather than waiting
  for the packaging and release feature. What still waits for that feature is
  everything to do with publishing: the package description, the compatibility
  statement as it appears on the index, and the release process itself.
