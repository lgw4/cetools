# Feature Specification: Scout Career & Career Selection Flag

**Feature Branch**: `002-scout-career-character`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "We need to add the Scout career to the character generator. We also need to add an optional flag to specify the requested career when invoking the character generator. In these cases, the character generator should automatically generate a new set of characteristics until the character meets the admission requirements for the requested career. If a career is not specified, the character should enter the draft."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a Scout Character (Priority: P1)

A game referee or player invokes the character generator with the Scout career flag and receives a fully-formed Cepheus Engine Scout character, including generated UPP, career history (terms served, skills gained via two rolls per term), and mustering-out benefits. Characteristics are re-rolled until the Intelligence 6+ qualification threshold is met.

**Why this priority**: The Scout career is the primary deliverable of this feature. Without a working Scout generator, no other scenario in this feature has value.

**Independent Test**: Invoke the generator with `--career scout` and verify a complete Scout character record is returned with a valid UPP, at least one Scout career term, skills consistent with Scout skill tables, and correct benefit results.

**Acceptance Scenarios**:

1. **Given** the generator is invoked with `--career scout`, **When** the initial characteristic rolls do not meet Intelligence 6+, **Then** the system silently re-rolls all six characteristics and repeats the qualification check until it passes, then proceeds with character generation.
2. **Given** a character qualifies for the Scout career, **When** the first term is processed, **Then** the character receives basic training (Pilot-1) and two skill rolls from any combination of the four Scout skill tables.
3. **Given** no commission or advancement system exists for Scouts, **When** each term is processed, **Then** the character receives exactly two skill rolls per term (not one), and no commission or advancement roll is attempted.
4. **Given** a Scout character who fails the survival roll (Endurance 7+), **When** generation is attempted, **Then** the CLI exits with code 1 and prints the cause of death to stderr; no character record is produced.
5. **Given** a Scout character completing at least one term, **When** the mustering-out phase runs, **Then** the character receives one benefit roll per term served, drawn from the Scout material benefits and cash tables, with the cash cap of 3 rolls enforced.
6. **Given** a Scout character completing a term, **When** re-enlistment is rolled (6+ target), **Then** the character continues or mustering-out begins; the 7-term cap and mandatory extra term on a natural 12 apply identically to Navy rules.

---

### User Story 2 - Default to Draft When No Career Specified (Priority: P2)

A player or referee invokes the character generator without specifying a career. Rather than defaulting to Navy enlistment, the character enters the draft, rolling on the draft table to determine their career assignment.

**Why this priority**: This changes the default behavior of the existing command and ensures the two-career system is coherent: the draft produces a deterministic Navy or Scout assignment and serves as the fallback for unspecified invocations.

**Independent Test**: Invoke `cetools character generate` (no `--career` flag) multiple times and verify that the resulting character enters a career determined by the draft table, with no enlistment attempt made.

**Acceptance Scenarios**:

1. **Given** the generator is invoked without `--career`, **When** generation begins, **Then** no enlistment roll is made; instead, a draft roll determines the character's career (Navy or Scout per the draft table for the careers supported at this phase).
2. **Given** a draft roll lands on Scout, **When** the character proceeds, **Then** the Scout career rules apply (no commission, two skill rolls per term, Scout skill tables, Scout mustering-out tables).
3. **Given** a draft roll lands on Navy, **When** the character proceeds, **Then** existing Navy career rules apply unchanged.
4. **Given** a draft outcome, **When** the character output is displayed, **Then** the output identifies the career as draft-assigned and names the career (e.g., "Scout (Drafted)" or "Navy (Drafted)").

---

### User Story 3 - Specify a Career at Invocation (Priority: P3)

A player or referee can request a specific career at invocation using a `--career` flag. The generator re-rolls characteristics as many times as needed until the qualification threshold for the requested career is met, then proceeds with character generation.

**Why this priority**: Career selection by request is a quality-of-life feature that allows targeted character concepts without manual re-rolling. It builds on User Story 1's re-roll mechanism.

**Independent Test**: Invoke the generator with `--career navy` and verify the resulting character always qualifies for Navy enlistment, with correct Navy career progression applied.

**Acceptance Scenarios**:

1. **Given** `--career navy` is specified, **When** characteristics are generated, **Then** the system re-rolls until Intelligence 6+ is met and the character is enrolled in Navy without an enlistment roll.
2. **Given** `--career scout` is specified, **When** characteristics are generated, **Then** the system re-rolls until Intelligence 6+ is met and the character is enrolled in Scout without an enlistment roll.
3. **Given** an unrecognized career name is passed via `--career`, **When** invocation occurs, **Then** the CLI exits with code 1 and prints a list of valid career names to stderr.

---

### Edge Cases

- What happens when re-rolling for qualification produces the same failing results many times? (The system loops indefinitely until qualification is met; no maximum re-roll limit is imposed, consistent with the SRD intent of guaranteed enrollment when a career is chosen.)
- What happens when the draft table assigns a career that is not yet implemented? (Out of scope for this phase; the draft table is restricted to Navy and Scout only. If future phases add careers, the draft table expands accordingly.)
- What happens when a Scout character has Education below 8? (The Advanced Education skill table is not available; skill rolls are limited to the other three tables.)
- What happens when a Scout exhausts re-enlistment on the first term? (The character mustering out with only basic training and two skill rolls is a valid outcome.)
- What happens if a Scout has no valid skill table to roll on? (Cannot occur: Personal Development, Service Skills, and Specialist Skills are always available regardless of Education.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST implement the Scout career as a data structure conforming to the existing career data interface, requiring zero changes to the core generation engine.
- **FR-002**: The Scout career data MUST specify: qualification stat Intelligence, qualification target 6; survival stat Endurance, survival target 7; no commission or advancement; re-enlistment target 6; basic training skill Pilot-1.
- **FR-003**: The Scout career data MUST include all four skill tables exactly as specified in the SRD: Personal Development (Jack o' Trades, +1 Dex, +1 Edu, +1 Int, +1 Edu, Melee Combat), Service Skills (Comms, Electronics, Gun Combat, Gunnery, Recon, Piloting), Specialist Skills (Engineering, Gunnery, Demolitions, Navigation, Medicine, Vehicle), and Advanced Education (Advocate, Computer, Linguistics, Medicine, Navigation, Tactics; available only if Education 8+).
- **FR-004**: The Scout career data MUST include the material benefits mustering-out table: 1. Low Passage, 2. +1 Edu, 3. Weapon, 4. Mid Passage, 5. Explorers' Society, 6. Courier Vessel.
- **FR-005**: The Scout career data MUST include the cash benefits mustering-out table: 1. Cr1,000, 2. Cr5,000, 3. Cr10,000, 4. Cr10,000, 5. Cr20,000, 6. Cr50,000, 7. Cr50,000.
- **FR-006**: The generation engine MUST award exactly two skill rolls per Scout term, because Scouts have no commission or advancement track. The engine MUST derive the number of skill rolls from the career data structure (commission-enabled: up to 2 if no advancement; no-commission career: always 2) rather than hardcoding 2 for Scout.
- **FR-007**: The CLI MUST accept an optional `--career <name>` flag on the `cetools character generate` subcommand. Valid values for this phase are `navy` and `scout` (case-insensitive).
- **FR-008**: When `--career <name>` is supplied, the system MUST generate characteristics and re-roll them as a complete set until the qualification target for the requested career is met, then proceed directly to the first term without an enlistment roll.
- **FR-009**: When `--career` is not supplied, the system MUST determine the character's career by rolling on the draft table rather than attempting enlistment.
- **FR-010**: The draft table for this phase MUST cover only the two implemented careers. Scouts (draft result 5 per SRD) and Navy (all other results per the subset table) are the valid outcomes.
- **FR-011**: The character output MUST indicate how career assignment occurred: "Drafted" when assigned via draft, or the career name alone when assigned via `--career`.
- **FR-012**: When an unrecognized career name is passed to `--career`, the CLI MUST exit with code 1 and print the list of valid career names to stderr.
- **FR-013**: The system MUST NOT implement a retirement pension for Scouts, as the SRD awards retirement only to careers with a commission/advancement track.
- **FR-014**: All existing Navy character generation behavior MUST be preserved unchanged, including enlistment rolls when no `--career` flag triggers a direct Navy draft result.

### Key Entities

- **Scout Career**: A career data structure conforming to the existing career interface. Has no commission or advancement tracks; specifies Pilot-1 as basic training; awards two skill rolls per term; has unique mustering-out tables.
- **Draft Table**: A mapping from a 1D6 roll to a career assignment. For this phase, covers Navy and Scout only. Expands when additional careers are implemented.
- **Career Flag**: The `--career` CLI argument. Selects a specific career for guaranteed enrollment via characteristic re-rolling. Absence triggers the draft.
- **Qualification Re-roll Loop**: The process of re-rolling all six characteristics until the requested career's qualification threshold is met. Does not alter any other generation step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can invoke `cetools character generate --career scout` and always receive a complete, valid Scout character record with Intelligence 6+ and correct Scout career output.
- **SC-002**: A user can invoke `cetools character generate` (no flag) and always receive a character whose career was assigned via the draft, with the draft origin indicated in the output.
- **SC-003**: The Scout career data structure can be defined and the generation engine processes it without any modification to engine logic, validated by a test that generates a Scout character using only the data structure.
- **SC-004**: All Scout-specific rules (two skill rolls per term, no commission/advancement, correct skill tables, correct mustering-out tables) are covered by automated tests, with 100% of Scout SRD rules verified.
- **SC-005**: Passing an unrecognized career name to `--career` exits with code 1 and produces a human-readable error on stderr in all cases.

## Assumptions

- The SRD at `https://evolvedexperiment.github.io/cepheus-srd/character-creation.html` is authoritative; the Scout career details (qualification, survival, skill tables, mustering-out) match those sourced during specification.
- No retirement pension applies to Scouts; this is consistent with the SRD's restriction of pensions to commissioned careers.
- The qualification check for `--career` re-rolls is identical for both Navy and Scout (Intelligence 6+); no DM for prior careers is applied, as this generator creates new characters with no prior career history.
- The draft table is restricted to Navy and Scout for this phase. Expanding the draft table to all twelve SRD careers is deferred until those careers are implemented.
- The `--career` flag accepts career names as lowercase strings; the implementation may normalise input case.
- The Explorers' Society benefit (Scout material table, result 5) is recorded as a named benefit in the output; its in-game mechanical effect (free passage bookings, etc.) is noted but not mechanically simulated in this phase.
- The Courier Vessel benefit (Scout material table, result 6) is recorded as a named benefit; ownership and maintenance rules are noted but not mechanically simulated in this phase.
- Characteristic DM penalties from multiple prior careers (SRD rule: −2 per prior career to qualification) do not apply here, as the generator always creates a character with no prior career history.
- Output format remains plain text to standard output; no structured format changes are introduced in this phase.
