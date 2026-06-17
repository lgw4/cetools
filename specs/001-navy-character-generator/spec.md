# Feature Specification: Navy Character Generator

**Feature Branch**: `001-navy-character-generator`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "We are making tools for use with the Cepheus Engine SRD. Initially, this will be a CLI tool, but it may expand to be accessible as an HTTP API. As an MVP, we will be making a character generator with the Navy career only; however, the goal is that we will build generators for all the entities used in Cepheus Engine. We will use Typer to provide the CLI functions."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Complete Navy Character (Priority: P1)

A user invokes the character generator from the command line and receives a fully
resolved Cepheus Engine character who has served in the Navy. The generator
follows all Navy career rules from the Cepheus Engine SRD: it rolls characteristics,
applies the Navy enlistment check, resolves each term of service (survival, commission,
promotion, skills), and applies mustering-out benefits when the character leaves service.

**Why this priority**: This is the entire MVP. Without a fully generated character
there is no deliverable product.

**Independent Test**: Running the generator produces a complete character record
including characteristics, rank, skills with levels, and mustering-out benefits.
The output can be verified by hand against the Cepheus Engine SRD tables.

**Acceptance Scenarios**:

1. **Given** no arguments, **When** the user runs the character generator command,
   **Then** a complete Navy character is generated using random dice rolls, and
   all characteristics, career history, skills, rank, and mustering-out benefits
   are displayed.

2. **Given** the Navy enlistment roll fails, **When** the generator resolves the
   career, **Then** the character is drafted into an appropriate alternative branch
   (per SRD rules) and the output reflects that branch, or the generator re-attempts
   enlistment per SRD draft procedures.

3. **Given** a character fails a survival roll during a term, **When** the generator
   processes that term, **Then** the character's career ends at that point and
   mustering-out benefits are calculated for the terms already served.

4. **Given** a character completes the maximum allowable terms, **When** the
   generator processes mustering-out, **Then** all cash and material benefits are
   applied and the final character record is complete.

5. **Given** the user requests multiple characters, **When** the command is run
   with a count argument, **Then** the specified number of independent characters
   are generated and displayed.

---

### User Story 2 - Display Formatted Character Sheet (Priority: P2)

A user reads the generated character's details in a clear, human-readable format
that mirrors the conventions of Cepheus Engine character sheets: UPP notation for
characteristics, skill list with levels, rank title, and mustering-out benefits.

**Why this priority**: A generated character is only useful if it is readable.
The formatted display is the primary output artifact.

**Independent Test**: The output for any generated character matches the UPP
format (e.g., `777777`) and lists skills in standard notation (e.g., `Gun Combat-1`).
A human familiar with Cepheus Engine can immediately use the output to play a game.

**Acceptance Scenarios**:

1. **Given** a generated character, **When** the character sheet is displayed,
   **Then** characteristics are shown as a six-digit Universal Personality Profile
   (UPP) using hexadecimal notation for values above 9.

2. **Given** a generated character with multiple skills, **When** the character
   sheet is displayed, **Then** each skill appears with its name and numeric level
   (e.g., `Pilot-2`), and skills gained multiple times are combined into a single
   higher-level entry.

3. **Given** a generated character with a Navy commission, **When** the character
   sheet is displayed, **Then** the character's final Navy rank title is shown
   (e.g., `Lieutenant`, `Commander`).

---

### User Story 3 - Export Character as Structured Data (Priority: P3)

A user exports the generated character in a machine-readable format so the data
can be consumed by other tools, stored, or used in future features such as an HTTP API.

**Why this priority**: Structured output future-proofs the tool for API integration
and downstream processing without requiring UI changes.

**Independent Test**: The structured output for a generated character can be parsed
by a standard JSON consumer and contains all fields (characteristics, skills, rank,
benefits, career history).

**Acceptance Scenarios**:

1. **Given** a user runs the generator with a structured-output flag, **When** the
   character is generated, **Then** the output is valid JSON containing all character
   fields.

2. **Given** a user generates multiple characters with the structured-output flag,
   **When** the command completes, **Then** the output is a valid JSON array of
   character objects.

---

### Edge Cases

- Characteristic rolls use 2d6 and produce values in the range 2–12; a raw value of 0
  is impossible at generation time and requires no special handling.
- A character drafted to a non-Navy service triggers a full retry (re-roll, re-enlist).
  A character drafted directly to Navy follows the same career path as an enlistee.
- What if a character's skill table roll produces a skill they already have—does
  the level increment correctly?
- When the user requests 0 or a negative count, the CLI MUST emit a validation error
  (e.g., `Error: count must be a positive integer`) and exit with a non-zero status code.

## Clarifications

### Session 2026-06-17

- Q: Are aging characteristic effects in scope for MVP, and what is the maximum service limit? → A: Aging effects are OUT OF SCOPE; hard cap at 7 terms (28 years). Age is tracked and displayed only; it does not modify characteristics.
- Q: When the user passes a count of 0 or a negative number, what should the CLI do? → A: Emit a validation error message and exit with a non-zero status code.
- Q: For an automated generator, how is the "character chooses to leave after four terms" rule handled? → A: The generator always attempts re-enlistment beyond term 4, continuing until re-enlistment fails, survival fails, or the 7-term cap is reached.
- Q: What is the JSON output schema (field names and structure)? → A: Flat top-level object: `upp` (string), `age` (int), `rank` (string), `terms` (int), `skills` (object mapping name→level), `benefits` (array of `{type, value}` objects).
- Q: When a character fails Navy enlistment and the SRD draft assigns them to a non-Navy service, what should the generator do? → A: Retry from scratch (re-roll characteristics, re-attempt enlistment) until the character enlists or is drafted into the Navy — every invocation is guaranteed to produce a Navy character.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The generator MUST roll six characteristics (Strength, Dexterity, Endurance,
  Intelligence, Education, Social Standing) using two six-sided dice per characteristic,
  following Cepheus Engine SRD rules.

- **FR-002**: The generator MUST apply the Navy enlistment check against the character's
  characteristics and, on failure, resolve the draft procedure per SRD rules. If the
  draft assigns the character to a non-Navy service, the generator MUST retry from
  scratch (re-rolling characteristics and re-attempting enlistment) until the character
  enters the Navy by enlistment or Navy draft. Every invocation is guaranteed to
  produce a Navy character. The retry loop MUST terminate with an error after 1,000
  consecutive non-Navy outcomes to guarantee termination under any implementation
  defect; in practice, 1,000 consecutive non-Navy outcomes are statistically impossible.

- **FR-003**: The generator MUST simulate each term of Navy service by resolving the
  survival roll, commission roll (if applicable), promotion roll (if applicable), and
  skill acquisition for that term.

- **FR-004**: The generator MUST apply skills gained during each term to the character's
  skill list, combining duplicate skills into a higher skill level.

- **FR-005**: The generator MUST track the character's Navy rank and update it on a
  successful commission or promotion roll. A promotion roll that succeeds when the
  character is already at the maximum Navy rank has no effect; the rank does not change.

- **FR-006**: The generator MUST end a character's career when a survival roll is failed
  (applying SRD consequences), when the re-enlistment roll fails, or when the 7-term
  maximum (28 years of service) is reached. Terms 1 through 4 are served automatically
  without a re-enlistment check; the character cannot voluntarily leave before term 4.
  Beginning with term 5, the generator MUST attempt a re-enlistment roll after each
  term; if the roll fails, the career ends and mustering-out benefits are calculated.
  The career continues until a dice-driven stopping condition or the 7-term cap.
  A survival failure ends the character's career immediately; for this MVP, survival
  failure is career-ending only and does not kill the character or modify characteristics.
  Aging characteristic effects are not simulated; age is tracked and displayed only.

- **FR-007**: The generator MUST calculate and apply mustering-out benefits (cash and
  material) based on the number of terms served and final rank.

- **FR-008**: The generator MUST display the completed character in human-readable
  format including UPP, age, rank, skills, and benefits. The CLI command MUST be
  `cetools navy`. UPP values use hexadecimal notation for values 10–15 (A–F); since
  initial characteristic rolls use 2d6 (range 2–12) and no characteristic modification
  occurs during generation, the maximum displayable UPP digit is C (12). When multiple
  characters are generated, each character block MUST be separated by a line containing
  only `---`.

- **FR-009**: The generator MUST support generating more than one character in a single
  invocation via a `--count INTEGER` flag (default: 1). If the count is 0 or negative,
  the CLI MUST emit the message `Error: count must be a positive integer` and exit with
  status code 1. A successful invocation MUST exit with status code 0. Any unexpected
  runtime error MUST exit with a non-zero status code.

- **FR-010**: The generator MUST support producing structured (JSON) output via a
  `--json` boolean flag (default: false). The JSON schema for a single character MUST
  contain these top-level fields: `upp` (string, hexadecimal UPP notation), `age`
  (integer), `rank` (string, Navy rank title or enlisted rating; empty string `""` for
  a character who never received a commission and has no enlisted rating title), `terms`
  (integer, terms served), `skills` (object mapping skill name to integer level; MUST be
  an empty object `{}` if the character has no skills), and `benefits` (array of objects
  each with `type` ("cash" or "material") and `value` (integer credits for cash benefits;
  string benefit name for material benefits)). Multiple characters MUST be output as a
  JSON array of such objects. The `career_history` field is intentionally excluded from
  the JSON output schema.

- **FR-011**: All Cepheus Engine SRD dice-roll tables and constants used by the Navy
  career MUST be faithfully implemented per the published SRD
  (https://cepheus-srd.opengamingnetwork.com). Before implementation begins, the
  implementation plan MUST enumerate every SRD-derived constant required by FR-001
  through FR-007, including: the Navy enlistment target number and all characteristic
  DMs; survival, commission, promotion, and re-enlistment target numbers and all DMs
  for each; the number of skill rolls acquired per term; all Navy skill tables
  (Personal Development, Service Skills, Advanced Education, Officer Skills) with their
  full skill lists; the number of mustering-out benefit rolls per term and any rank
  bonuses; the cash and material benefit tables with all valid material benefit names;
  the characteristic modifier table (mapping raw values to DMs); and all Navy enlisted
  ratings and officer rank titles.

- **FR-012**: All character generation logic MUST reside in library modules under
  `src/cetools/` that are fully independent of the CLI layer. The CLI entry point
  (Typer command) MUST act as a thin binding that calls into library functions only;
  no business logic is permitted in the CLI handler. SRD table data MUST be
  importable and exercisable in tests without invoking the CLI. This requirement
  enforces Constitution Principle I (CLI First, Logic Decoupled).

### Key Entities

- **Character**: The generated person. Holds six characteristics, age, a list of
  skills (each with a level), a career history, final rank, and mustering-out benefits.

- **Characteristic**: One of the six core attributes (STR, DEX, END, INT, EDU, SOC),
  each with a numeric value and a derived modifier.

- **Career Term**: A four-year period of Navy service. Records the term number,
  survival outcome, commission/promotion outcome, and skills acquired.

- **Skill**: A named ability with a numeric proficiency level (0+). Duplicate skill
  gains during character generation increase the level rather than creating a duplicate
  entry.

- **Rank**: The character's military grade within the Navy (enlisted rating or officer
  rank), with an associated title per SRD tables.

- **Benefit**: A mustering-out reward, either a cash amount or a named material item
  (e.g., weapon, passage, ship shares).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can generate a single complete, rules-legal Navy character in under
  five seconds from invoking the command to viewing the result. No time constraint is
  placed on batch invocations (SC-003).

- **SC-002**: Every generated character's characteristics, skills, rank, and benefits
  can be verified by hand against the Cepheus Engine SRD tables with zero discrepancies.
  Acceptance procedure: generate 10 sample characters and verify each field against the
  CE SRD tables manually; all 10 must pass without discrepancy.

- **SC-003**: The generator can produce 100 characters in a single invocation without
  error.

- **SC-004**: The structured (JSON) output for any generated character can be parsed
  by a standard JSON tool without errors.

- **SC-005**: A user familiar with Cepheus Engine can read the human-readable output
  and use the character in a game session without consulting any additional documentation.

## Assumptions

- Characters are generated for the Navy career only; other careers are out of scope
  for this MVP.
- All dice are simulated via a cryptographically unbiased random number generator;
  there is no support for manual dice input in this version.
- The Cepheus Engine SRD is the authoritative source for all tables and rules;
  house rules and variant rules are out of scope.
- The tool is designed for single-player or game-master use, not for multi-user
  concurrent sessions.
- Character data is not persisted between invocations unless the user redirects
  output; no database or file storage is built into the MVP.
- The future HTTP API expansion is out of scope for this feature but the character
  generation logic must be structured to support it without major rework.
- Aging characteristic effects (CE SRD aging tables, characteristic degradation) are
  out of scope for this MVP. Age is computed as 18 + (4 × terms served) and displayed
  only; it does not modify characteristics.
