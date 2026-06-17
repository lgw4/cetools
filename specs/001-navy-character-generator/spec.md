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

- What happens when characteristic rolls produce a value of 0 for any characteristic?
- How does the generator handle a character who fails enlistment and the draft table
  assigns them to the Navy anyway?
- What if a character's skill table roll produces a skill they already have—does
  the level increment correctly?
- What happens when the user requests 0 or a negative number of characters?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The generator MUST roll six characteristics (Strength, Dexterity, Endurance,
  Intelligence, Education, Social Standing) using two six-sided dice per characteristic,
  following Cepheus Engine SRD rules.

- **FR-002**: The generator MUST apply the Navy enlistment check against the character's
  characteristics and, on failure, resolve the draft procedure per SRD rules.

- **FR-003**: The generator MUST simulate each term of Navy service by resolving the
  survival roll, commission roll (if applicable), promotion roll (if applicable), and
  skill acquisition for that term.

- **FR-004**: The generator MUST apply skills gained during each term to the character's
  skill list, combining duplicate skills into a higher skill level.

- **FR-005**: The generator MUST track the character's Navy rank and update it on a
  successful commission or promotion roll.

- **FR-006**: The generator MUST end a character's career when a survival roll is failed
  (applying SRD consequences), when the re-enlistment roll fails, when the character
  chooses to leave (after four terms), or when the maximum service limit is reached.

- **FR-007**: The generator MUST calculate and apply mustering-out benefits (cash and
  material) based on the number of terms served and final rank.

- **FR-008**: The generator MUST display the completed character in human-readable
  format including UPP, age, rank, skills, and benefits.

- **FR-009**: The generator MUST support generating more than one character in a single
  invocation when the user specifies a count.

- **FR-010**: The generator MUST support producing structured (JSON) output alongside
  or instead of human-readable output.

- **FR-011**: All Cepheus Engine SRD dice-roll tables used by the Navy career MUST be
  faithfully implemented per the published SRD.

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

- **SC-001**: A user can generate a complete, rules-legal Navy character in under
  five seconds from invoking the command to viewing the result.

- **SC-002**: Every generated character's characteristics, skills, rank, and benefits
  can be verified by hand against the Cepheus Engine SRD tables with zero discrepancies.

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
